from flask import Blueprint, Response, render_template, flash, make_response, redirect, url_for, request, g

from management_app.db import get_db
from management_app.views.auth import login_required
from management_app.views.points import get_latest_academic_year, calculate_teaching_point_val, update_yearly_ending_balance
from management_app.views.utils import insert_log

settings = Blueprint('settings', __name__, url_prefix='/settings')

@settings.route('/admins', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        add_admin_status(request.form['user-select'])

    users, admins = get_users_and_admins()
    current_user = next(admin for admin in admins if admin['user_email'] == g.user['user_email'])

    return render_template(
        'settings/index.html',
        admins=admins,
        current_user=current_user,
        users=users
    )

@settings.route('/admins/<id>', methods=['POST', 'DELETE'])
@login_required
def remove_admin(id):
    if is_only_admin():
        flash('Cannot remove admin when only one is left.', 'error')
        return make_response('Cannot remove admin when only one is left.', 400)
    if request.method == 'POST':
        remove_admin_status(id)
    if request.method == 'DELETE':
        delete_admin(id)
    return Response(status=200)
    

@settings.route('/point-policy')
@login_required
def point_policy():
    db = get_db()
    rules = db.execute('SELECT * FROM rules').fetchall()
    return render_template('settings/point-policy.html', rules=rules)

@settings.route('/point-policy/rules/<id>', methods=['POST'])
@login_required
def edit_rule_point_value(id):
    update_rule_point_value(id, request.form['point-value'])
    return redirect(url_for('settings.point_policy'))

def get_users_and_admins():
    db = get_db()
    admins = []
    users = []
    res = db.execute("""
            SELECT u.user_id, u.user_name, u.user_email, u.user_ucinetid, u.admin, fs.role
            FROM users AS u LEFT JOIN faculty_status AS fs ON u.user_id = fs.user_id
            WHERE (fs.end_year IS NULL AND fs.active_status IS TRUE) OR fs.role IS NULL
        """)
    for user in res.fetchall():
        if user['admin']:
            admins.append(user)
        else:
            users.append(user)

    return (users, admins)

def add_admin_status(id):
    db = get_db()
    db.execute('UPDATE users SET admin = 1 WHERE user_id = ?', (id,))
    db.commit()
    insert_log("Admin: " + g.user['user_name'], id, None, 'Add new admin')

def remove_admin_status(id):
    db = get_db()
    db.execute('UPDATE users SET admin = 0 WHERE user_id = ?', (id,))
    db.commit()
    insert_log("Admin: " + g.user['user_name'], id, None, 'Remove admin status')

def delete_admin(id):
    db = get_db()
    db.execute('DELETE FROM users WHERE user_id = ?', (id,))
    db.commit()
    insert_log("Admin: " + g.user['user_name'], id, None, 'Delete admin')

def is_only_admin():
    db = get_db()
    res = db.execute('SELECT COUNT(admin) AS count FROM users WHERE admin IS TRUE').fetchone()
    return res['count'] == 1

def update_rule_point_value(id, value):
    db = get_db()
    old = db.execute('SELECT value FROM rules WHERE rule_id = ?', (id,)).fetchone()
    db.execute('UPDATE rules SET value = ? WHERE rule_id = ?', (value, id))
    db.commit()
    new = db.execute('SELECT * FROM rules WHERE rule_id = ?', (id,)).fetchone()
    insert_log("Admin: " + g.user['user_name'], None, None, f'Update point policy - Rule Name: {new["rule_name"]} | Value: {old["value"]} -> {new["value"]}')
    update_teaching_point_balances(new['rule_id'])

def update_teaching_point_balances(rule_id):
    db = get_db()
    rule = db.execute('SELECT * FROM rules WHERE rule_id = ?', (rule_id,)).fetchone()
    rule_name = rule['rule_name']
    start_year = get_latest_academic_year()

    if rule_name.startswith('Role-'):
        role = rule_name[5:].lower()
        faculty = db.execute('SELECT user_id FROM faculty_status WHERE active_status IS TRUE AND role = ?', (role,)).fetchall()

        for user in faculty:
            db.execute('UPDATE faculty_point_info SET credit_due = ? WHERE user_id = ? AND year = ?', (rule['value'], user['user_id'], start_year))
        
        db.commit()
        
        for user in faculty:
            update_yearly_ending_balance(user['user_id'], start_year)
    elif rule_name.startswith('Category'):
        end_year = start_year + 1
        offerings = db.execute("""
            SELECT *
            FROM scheduled_teaching
            WHERE (year = ? AND quarter = 1) OR (year = ? AND (quarter = 2 OR quarter = 3))
        """, (start_year, end_year)).fetchall()

        for offering in offerings:
            co_taught = db.execute("""
                SELECT COUNT(DISTINCT user_id) AS num
                FROM scheduled_teaching
                GROUP BY year, quarter, course_title_id
                HAVING year = ? AND quarter = ? AND course_title_id = ?
            """, (offering['year'], offering['quarter'], offering['course_title_id'])).fetchone()
            value = calculate_teaching_point_val(
                offering['course_title_id'],
                offering['enrollment'],
                offering['offload_or_recall_flag'],
                offering['year'],
                offering['quarter'],
                offering['user_id'],
                co_taught['num']
            )
            if value != offering['teaching_point_val']:
                db.execute("""
                    UPDATE scheduled_teaching
                    SET teaching_point_val = ?
                    WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?
                """, (value, offering['user_id'], offering['year'], offering['quarter'], offering['course_title_id'], offering['course_sec']))
        
        db.commit()

        faculty = db.execute('SELECT user_id FROM faculty_status WHERE active_status IS TRUE').fetchall()
        for user in faculty:
            update_yearly_ending_balance(user['user_id'], start_year)