from flask import Blueprint, Response, render_template, flash, make_response, session, request

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
    rules = db.execute('SELECT rule_name, points FROM points_constant').fetchall()
    return render_template('settings/point-policy.html', rules=rules)


def get_users_and_admins(db):
    admins = []
    users = []
    res = db.execute("""
            SELECT users.user_id, user_name, user_email, user_ucinetid, admin, role
            FROM users LEFT JOIN faculty_status ON users.user_id = faculty_status.user_id
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