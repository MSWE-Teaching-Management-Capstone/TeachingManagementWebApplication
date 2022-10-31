from flask import Blueprint, render_template

from management_app.views.auth import login_required

settings = Blueprint('settings', __name__, url_prefix='/settings')

@settings.route('/admins')
@login_required
def admins():
    # TODO get data from database
    admins = [
        {'name': 'Admin A', 'email': 'profA@uci.edu'},
        {'name': 'Staff B', 'email': 'staffB@uci.edu'},
        {'name': 'Staff C', 'email': 'staffC@uci.edu'}
    ]
    users = [
        {'name': 'User A'},
        {'name': 'User B'},
        {'name': 'User C'}
    ]
    return render_template(
        'settings/admins.html',
        admins=admins,
        current_user=admins[0],
        users=users
    )

@settings.route('/point-policy')
@login_required
def point_policy():
    # TODO get data from database
    rules = [
        {'name': 'Rule 1', 'point_value': 1},
        {'name': 'Rule 2', 'point_value': 0.5},
        {'name': 'Rule 3', 'point_value': 1.5}
    ]
    return render_template('settings/point-policy.html', rules=rules)