from flask import Blueprint, Response, render_template, flash, make_response, redirect, url_for, session, request

from management_app.db import get_db
from management_app.views.auth import login_required
from management_app.views.utils import insert_log

settings = Blueprint('settings', __name__, url_prefix='/settings')

@settings.route('/admins', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        add_admin_status(request.form['user-select'])

    users, admins = get_users_and_admins()
    current_user = next(admin for admin in admins if admin['user_email'] == session['email'])

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
    insert_log(session['name'], id, None, 'Add new admin')

def remove_admin_status(id):
    db = get_db()
    db.execute('UPDATE users SET admin = 0 WHERE user_id = ?', (id,))
    db.commit()
    insert_log(session['name'], id, None, 'Remove admin status')

def delete_admin(id):
    db = get_db()
    db.execute('DELETE FROM users WHERE user_id = ?', (id,))
    db.commit()
    insert_log(session['name'], id, None, 'Delete admin')

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
    insert_log(session['name'], None, None, f'Update point policy - Rule Name: {new["rule_name"]} | Value: {old["value"]} -> {new["value"]}')