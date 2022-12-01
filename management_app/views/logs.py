from flask import (Blueprint, render_template, redirect, url_for, request)

from management_app.db import get_db
from management_app.views.auth import login_required
from management_app.views.utils import convert_local_timezone

logs = Blueprint('logs', __name__, url_prefix='/logs')


@logs.route('/')
@login_required
def index():
    return redirect(url_for('logs.get_exception_logs'))


@logs.route('/exception')
@login_required
def get_exception_logs():
    return render_template('logs/index.html', exception_logs=get_admin_exception_logs())


@logs.route('/general')
@login_required
def get_general_logs():
    return render_template('logs/general_logs.html', general_logs=get_admin_general_logs())


@logs.route('/exception-with-dates', methods=['POST'])
@login_required
def get_admin_exceptions_with_daterange():
    admin_exceptions_with_dates = []

    if request.method == 'POST':
        start_date = request.form['start-date']
        end_date = request.form['end-date']

        db = get_db()

        raw = db.execute(
            'SELECT logs.created, logs.owner, users.user_name, exceptions.exception_category, exceptions.message'
            ' FROM logs'
            ' JOIN users ON users.user_id = logs.user_id'
            ' JOIN exceptions ON logs.exception_id = exceptions.exception_id'
            ' WHERE logs.exception_id IS NOT NULL AND logs.user_id IS NOT NULL'
            ' AND logs.created < ? AND logs.created > ?',
            (end_date, start_date),
        ).fetchall()

        for record in raw:
            admin_exceptions_with_dates.append(
                {
                    'timeStamp': convert_local_timezone(record['created']),
                    'owner': record['owner'],
                    'affected': record['user_name'],
                    'exception': record['exception_category'],
                    'reason': record['message']
                }
            )

    return render_template('logs/index.html', exception_logs=admin_exceptions_with_dates)


def get_admin_exception_logs():
    admin_exceptions = []
    db = get_db()

    raw = db.execute(
        'SELECT logs.created, logs.owner, users.user_name, exceptions.exception_category, exceptions.message'
        ' FROM logs'
        ' JOIN users ON users.user_id = logs.user_id'
        ' JOIN exceptions ON logs.exception_id = exceptions.exception_id'
        ' WHERE logs.exception_id IS NOT NULL AND logs.user_id IS NOT NULL'
    ).fetchall()

    for record in raw:
        admin_exceptions.append(
            {
                'timeStamp': convert_local_timezone(record['created']),
                'owner': record['owner'],
                'affected': record['user_name'],
                'exception': record['exception_category'],
                'reason': record['message']
            }
        )

    return admin_exceptions


def get_admin_general_logs():
    admin_general = []
    db = get_db()

    raw = db.execute(
        'SELECT logs.created, logs.owner, logs.log_category, logs.user_id, logs.exception_id'
        ' FROM logs'
        ' WHERE logs.exception_id IS NULL',
    ).fetchall()

    for record in raw:
        admin_general.append(
            {
                'timeStamp': convert_local_timezone(record['created']),  # This is a `datetime.datetime` object
                'owner': record['owner'],
                'description': convert_description(record['log_category'],
                                                   record['user_id'] if 'user_id' in record.keys() else None)
            }
        )

    return admin_general


def convert_description(category, affected_user_id):
    if not affected_user_id:
        return category
    user_name = get_username_from_id(affected_user_id)
    description = f'{category}({user_name})'

    return description


def get_username_from_id(user_id):
    db = get_db()
    res = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)
    ).fetchone()
    return res['user_name'] if res is not None else ''