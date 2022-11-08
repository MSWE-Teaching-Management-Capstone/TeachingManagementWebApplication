from flask import Blueprint, render_template, session

from management_app.views.auth import login_required
from management_app.db import get_db

settings = Blueprint('settings', __name__, url_prefix='/settings')

@settings.route('/admins')
@login_required
def admins():
    db = get_db()
    admins = []
    users = []

    for user in db.execute('SELECT * FROM users').fetchall():
        if user['admin']:
            admins.append(user)
        else:
            users.append(user)
    
    user_email = session['email']
    current_user = next(admin for admin in admins if admin['user_email'] == user_email)

    return render_template(
        'settings/index.html',
        admins=admins,
        current_user=current_user,
        users=users
    )

@settings.route('/point-policy')
@login_required
def point_policy():
    db = get_db()
    rules = db.execute('SELECT rule_name, points FROM points_constant').fetchall()
    return render_template('settings/point-policy.html', rules=rules)