from flask import Blueprint, Response, render_template, flash, make_response, redirect, url_for, session, request

from management_app.views.auth import login_required
from management_app.db import get_db

settings = Blueprint('settings', __name__, url_prefix='/settings')

@settings.route('/admins', methods=['GET', 'POST'])
@login_required
def index():
    db = get_db()
    if request.method == 'POST':
        add_admin_status(db, request.form['user-select'])

    users, admins = get_users_and_admins(db)
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
    db = get_db()
    if is_only_admin(db):
        flash('Cannot remove admin when only one is left.', 'error')
        return make_response('Cannot remove admin when only one is left.', 400)
    if request.method == 'POST':
        remove_admin_status(db, id)
    if request.method == 'DELETE':
        delete_admin(db, id)
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
    db = get_db()
    update_rule_point_value(db, id, request.form['point-value'])
    return redirect(url_for('settings.point_policy'))

def get_users_and_admins(db):
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

def add_admin_status(db, id):
    db.execute('UPDATE users SET admin = 1 WHERE user_id = ?', (id))
    db.commit()

def remove_admin_status(db, id):
    db.execute('UPDATE users SET admin = 0 WHERE user_id = ?', (id))
    db.commit()

def delete_admin(db, id):
    db.execute('DELETE FROM users WHERE user_id = ?', (id))
    db.commit()

def is_only_admin(db):
    res = db.execute('SELECT COUNT(admin) AS count FROM users WHERE admin IS TRUE').fetchone()
    return res['count'] == 1

def update_rule_point_value(db, id, value):
    db.execute('UPDATE rules SET value = ? WHERE rule_id = ?', (value, id))
    db.commit()