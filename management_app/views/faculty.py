import pandas as pd
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from management_app.db import get_db
from management_app.views.auth import login_required
from management_app.views.utils import download_file, upload_file, remove_upload_file, get_upload_filepath
from management_app.views.points import get_faculty_credit_due_by_role, get_yearly_ending_balance

faculty = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty.route('/', methods=['GET'])
@login_required
def index():
    if request.method == 'GET':
        year_options = get_professor_point_year_ranges()
        if ((len(year_options)) == 0):
            faculties = []
        else:
            year_select = request.args.get('year') or year_options[len(year_options)-1]
            year = year_select.split('-')[0]
            faculties = get_professor_point_info(year)
        return render_template('faculty/index.html', faculties=faculties, year_options=year_options)

@faculty.route('/data-templates/<filename>', methods=['GET'])
@login_required
def download_template(filename):
    if request.method == 'GET':
        # TODO: pre-populate data for the 2nd download
        return download_file(filename)

@faculty.route('/upload', methods=['POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['facultyTemplate']
        filename = secure_filename(file.filename)
        file_path = get_upload_filepath(filename)
        action_type = request.form['templateUploadOptions']

        upload_file(file)

        if action_type == 'addUsers':
            process_user_file(file_path, 1, 'Users', action_type)
        elif action_type == 'addProfessors':
            process_professors_point_file(file_path, 1, 'Professors_point_info', action_type)

        remove_upload_file(file)
        return redirect(url_for('faculty.index'))

def process_user_file(file_path, sheet__index, sheet__index_name, action_type):
    error = None
    try:
        df = pd.read_excel(file_path, sheet_name=sheet__index or sheet__index_name)
        #Check if NaN in the sheet
        df.loc[df['admin'].isnull(),'admin'] = 0
        df['admin'] = df['admin'].astype(int)
        df.loc[df['active_status'].isnull(),'active_status'] = 1
        df['active_status'] = df['active_status'].astype(int)
        users_rows = df.values.tolist()

        if len(users_rows) == 0:
            error = 'No data source found. Please refresh and upload again.'
        else:
            # We need initial year data as start_year to determine the range of role and active status
            for row in users_rows:
                start_year = row[0]
                user_name = row[1]
                user_email = row[2]
                user_ucinetid = row[3]
                user_role = row[4]
                is_active = row[5]
                is_admin = row[6]

                db = get_db()
                row = get_exist_user(user_ucinetid) # Check exist user by ucinetid

                if row is None and action_type == 'addUsers':
                    try:
                        insert_users(user_name, user_email, user_ucinetid, is_admin)
                        insert_users_status(user_ucinetid, start_year, user_role, is_active)
                    except db.IntegrityError:
                        error = 'Database insert error. Please refresh and upload correct file with new user data.'
                        print('INTEGRITY ERROR\n', traceback.print_exc())
                elif row is not None:
                    error = 'Database insert error. User is already existed. Please refresh and upload correct file with new user data.'
    except:
        error = 'Failed to upload. Please refresh and upload the correct data format again.'

    if error is not None:
        flash(error, 'error')
        return

    flash('Upload users data succesfully!', 'success')
    return

def process_professors_point_file(file_path, sheet__index, sheet__index_name, action_type):
    error = None
    try:
        df = pd.read_excel(file_path, sheet_name=sheet__index or sheet__index_name)
        #Check if NaN in the sheet
        df.loc[df['grad_students (students name)'].isnull(),'grad_students (students name)'] = ''
        df['grad_students (students name)'] = df['grad_students (students name)'].astype(str)
        professors_point_rows = df.values.tolist()

        if len(professors_point_rows) == 0:
            error = 'No data source found. Please refresh and upload again.'

        # Note: year represents the start of academic year quarter
        # e.g., year 2019 for 2019-2020 (2019 Fall, 2020 Winter, 2020 Spring)
        for row in professors_point_rows:
            year = row[0]
            user_ucinetid = row[2]
            grad_count = row[3]
            grad_students = row[4]

            db = get_db()
            user = get_exist_user(user_ucinetid)

            if user is None:
                error = 'User is not existed in the system'
            else:
                user_id = user['user_id']

                # TODO: Need to remove this later and use the last year
                previous_balance = get_yearly_previous_balance(user_id, year)
                if previous_balance is None:
                    previous_balance = row[5]

                if action_type == 'addProfessors':
                    try:
                        insert_professors_point_info(user_id, year, previous_balance, grad_count, grad_students)
                    except db.IntegrityError:
                        print('INTEGRITY ERROR\n', traceback.print_exc())
                        error = 'Database insert error. Please refresh and upload correct file with data of a new academic year.'
    except:
        error = 'Failed to upload. Please refresh and upload the correct data format again.'

    if error is not None:
        flash(error, 'error')
        return
    
    flash('Upload professors point info data succesfully!', 'success')
    return

def get_exist_user(user_ucinetid):
    db = get_db()
    return db.execute(
        'SELECT * FROM users WHERE user_ucinetid = ?', (user_ucinetid,)
    ).fetchone()

def get_user_current_profile(user_id):
    # TODO: need to update as yearly range user_role and active_status
    db = get_db()
    profile = db.execute(
        'SELECT * FROM users_status WHERE user_id = ? AND end_year is NULL', (user_id,)
    ).fetchone()
    return profile['user_role']

def get_professor_point_year_ranges():
    year_options = []
    db = get_db()
    rows = db.execute(
        'SELECT DISTINCT year FROM professors_point_info'
    ).fetchall()
    for row in rows:
        year = row['year']
        option = str(year) + '-' + str(year+1)
        year_options.append(option)
    return year_options

def get_yearly_previous_balance(user_id, year):
    db = get_db()
    row = db.execute(
        'SELECT ending_balance FROM professors_point_info WHERE user_id = ? AND year = ?',
        (user_id, year-1)
    ).fetchone()
    if row is None:
        return None
    return row['ending_balance']

def get_professor_point_info(year):
    faculties = []
    db = get_db()
    data = db.execute(
        'SELECT users.user_id, users.user_name, users.user_email,'
        ' users_status.user_role, users_status.active_status,'
        ' prof.year, prof.credit_due, prof.previous_balance, prof.ending_balance'
        ' FROM users'
        ' JOIN users_status ON users.user_id = users_status.user_id'
        ' JOIN professors_point_info AS prof ON users.user_id = prof.user_id'
        ' WHERE prof.year = ?',
        (year,)
    ).fetchall()

    for row in data:
        faculties.append({
            'name': row['user_name'],
            'email': row['user_email'],
            'role': row['user_role'],
            'required_point': row['credit_due'],
            'prev_balance': row['previous_balance'],
            'ending_balance': row['ending_balance']
        })
    return faculties

def insert_users(user_name, user_email, user_ucinetid, is_admin):
    db = get_db()
    db.execute(
        'INSERT INTO users (user_name, user_email, user_ucinetid, admin)'
        ' VALUES (?, ?, ?, ?)',
        (user_name, user_email, user_ucinetid, is_admin)
    )
    db.commit()
    return

def insert_users_status(user_ucinetid, start_year, user_role, active_status):
    db = get_db()
    user = get_exist_user(user_ucinetid)
    user_id = user['user_id']
    db.execute(
        'INSERT INTO users_status (user_id, start_year, user_role, active_status)'
        ' VALUES (?, ?, ?, ?)',
        (user_id, start_year, user_role, active_status)
    )
    db.commit()
    return

def insert_professors_point_info(user_id, year, previous_balance, grad_count, grad_students):
    user_role = get_user_current_profile(user_id)
    credit_due = get_faculty_credit_due_by_role(user_role)
    ending_balance = round(get_yearly_ending_balance(user_id, year, grad_count, grad_students, previous_balance, credit_due), 4)

    db = get_db()
    db.execute(
        'INSERT INTO professors_point_info (user_id, year, previous_balance, ending_balance, credit_due, grad_count, grad_students)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?)',
        (user_id, year, previous_balance, ending_balance, credit_due, grad_count, grad_students)
    )
    db.commit()
    return

def update_users(user_name, is_admin, user_ucinetid):
    db = get_db()
    db.execute(
        'UPDATE users SET user_name = ?, admin = ?'
        ' WHERE user_ucinetid = ?',
        (user_name, is_admin, user_ucinetid)
    )
    db.commit()
    return

def update_user_status_by_users_template(user_id, year, user_role):
    db = get_db()
    db.execute(
        'UPDATE users_status SET year = ?, user_role = ?'
        ' WHERE user_id = ?',
        (year, user_role, user_id)
    )
    db.commit()
    return

def update_professors_point_info(user_id, year, previous_balance, grad_count, grad_students):
    db = get_db()
    db.execute(
        'UPDATE professors_point_info SET year = ?, previous_balance = ?, grad_count = ?, grad_students = ?'
        ' WHERE user_id = ?',
        (year, previous_balance, grad_count, grad_students, user_id)
    )
    return