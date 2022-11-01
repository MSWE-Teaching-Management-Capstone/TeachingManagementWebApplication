from flask import (Blueprint, render_template, redirect, url_for)

from management_app.views.auth import login_required

logs = Blueprint('logs', __name__, url_prefix='/logs')


@logs.route('/')
@login_required
def index():
    return redirect(url_for('logs.get_exception_logs'))


@logs.route('/exception')
@login_required
def get_exception_logs():
    # TODO: Retrieve data from database in the future tasks
    logs_lst = [
        {'timeStamp': '10/22/2023', 'owner': 'Admin A', 'affected': 'Professor A',
         'exception': 'Buyout', 'reason': 'This is a comment of the buyout.'},
        {'timeStamp': '10/21/2023', 'owner': 'Admin A', 'affected': 'Professor B',
         'exception': 'Leave of absence',
         'reason': 'This is a comment of the leave of absence.'},
        {'timeStamp': '10/20/2023', 'owner': 'Admin B', 'affected': 'Professor C',
         'exception': 'Sabbatical',
         'reason': 'This is a comment of the sabbatical.'}
    ]

    logs_lst = logs_lst * 10  # extend to verify functionality of scrolling down

    return render_template('logs/index.html', exception_logs=logs_lst)


@logs.route('/general')
@login_required
def get_general_logs():
    # TODO: Retrieve data from database in the future tasks
    logs_lst = [
        {'timeStamp': '10/22/2023', 'owner': 'Admin A',
         'description': 'Add faculty(Professor A)'},
        {'timeStamp': '10/21/2023', 'owner': 'Admin A',
         'description': 'Upload enrollment sheet'},
        # `affected faculty` field is `null` in the database for the action above
        {'timeStamp': '10/19/2023', 'owner': 'Admin B',
         'description': 'Edit professor(Professor C)'}
    ]

    return render_template('logs/general_logs.html', general_logs=logs_lst)
