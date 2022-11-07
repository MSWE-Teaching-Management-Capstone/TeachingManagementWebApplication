import pandas as pd
import traceback
from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from management_app.db import get_db
from management_app.views.auth import login_required
from management_app.views.utils import download_file, upload_file, remove_upload_file, get_upload_filepath

faculty = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty.route('/', methods=['GET'])
@login_required
def index():
    if request.method == 'GET':
        years = get_professor_point_year_ranges()
        if ((len(years)) == 0):
            faculties = []
        else:
            yearSelect = years[0] or request.args.get('year')
            year = yearSelect.split('-')[0]
            faculties = get_professor_point_by_year(year)
        return render_template('faculty/index.html', faculties=faculties, years=years)

@faculty.route('/data-templates/<filename>', methods=['GET'])
@login_required
def download_template(filename):
    if request.method == 'GET':
        return download_file(filename)

@faculty.route('/upload', methods=['POST'])
@login_required
def upload():
    # TODO: catch and display reuqest error message
    if request.method == 'POST':
        file = request.files['facultyTemplate']
        filename = secure_filename(file.filename)
        file_path = get_upload_filepath(filename)
        action_type = request.form['templateUploadOptions']

        upload_file(file)

        if action_type == 'addUsers':
            process_user_file(file_path, 1, 'Users', action_type)
        elif action_type == 'editUsers':
            process_user_file(file_path, 1, 'Users', action_type)
        elif action_type == 'addProfessors':
            process_professors_point_file(file_path, 1, 'Professors_point_info', action_type)
        elif action_type == 'editProfessors':
            process_professors_point_file(file_path, 1, 'Professors_point_info', action_type)

        remove_upload_file(file)
        return redirect(url_for('faculty.index'))

def process_user_file(file_path, sheet__index, sheet__index_name, action_type):
    df = pd.read_excel(file_path, sheet_name=sheet__index or sheet__index_name)
    df.loc[df['admin'].isnull(),'admin'] = 0 #Check if NaN in the sheet
    df['admin'] = df['admin'].astype(int)
    users_data = df.values.tolist()

    for user in users_data:
        user_name = user[0]
        user_email = user[1]
        user_ucinetid = user[2]
        user_role = user[3]
        is_admin = user[4]

        db = get_db()
        db.execute("PRAGMA foreign_keys = ON")
        user = get_exist_user(user_ucinetid) # Check exist user by ucinetid

        if user is None and action_type == 'addUsers':
            try:
                insert_users(user_name, user_email, user_ucinetid, is_admin)
                insert_users_status(user_ucinetid, 2020, user_role, 1) # TODO: confirm if we can have active_status in template (temporarily set current year 2020)
            except db.IntegrityError:
                print('INTEGRITY ERROR\n', traceback.print_exc())
        elif action_type == 'editUsers':
            user_id = user['user_id']
            try:
                update_users(user_name, is_admin, user_ucinetid)
                update_user_status_by_users_template(user_id, 2020, user_role) # TODO: confirm if we can have active_status in template (temporarily set current year 2020)
            except db.IntegrityError:
                print('INTEGRITY ERROR\n', traceback.print_exc())
    return

def process_professors_point_file(file_path, sheet__index, sheet__index_name, action_type):
    df = pd.read_excel(file_path, sheet_name=sheet__index or sheet__index_name)
    data = df.values.tolist()

    for d in data:
        year = d[0]
        user_ucinetid = d[2]
        grad_count = d[3]
        grad_students = d[4]
        previous_balance = d[5]

        db = get_db()
        db.execute("PRAGMA foreign_keys = ON")
        user = get_exist_user(user_ucinetid)

        if user is None:
            print('User is not existed in the system') # TODO: display error to front-end
            return

        # TODO: Automatically calculate point after insert/update
        user_id = user['user_id']
        if action_type == 'addProfessors':
            try:
                insert_professors_point_info(user_id, year, previous_balance, grad_count, grad_students)
            except db.IntegrityError:
                print('INTEGRITY ERROR\n', traceback.print_exc())
        elif action_type == 'editProfessors':
            try:
                update_professors_point_info(user_id, year, previous_balance, grad_count, grad_students)
            except db.IntegrityError:
                print('INTEGRITY ERROR\n', traceback.print_exc())
    return

def get_exist_user(user_ucinetid):
    db = get_db()
    return db.execute(
        'SELECT * FROM users WHERE user_ucinetid = ?', (user_ucinetid,)
    ).fetchone()

def get_exist_professor_point_info(user_id):
    db = get_db()
    return db.execute(
        'SELECT * FROM professors_point_info WHERE user_id = ?', (user_id,)
    ).fetchone()

def get_professor_point_year_ranges():
    year_options = []
    db = get_db()
    rows = db.execute(
        'SELECT DISTINCT year FROM professors_point_info'
        ' ORDER BY year DESC'
    ).fetchall()
    for row in rows:
        year = row['year']
        option = str(year) + '-' + str(year+1)
        year_options.append(option)
    return year_options

def get_professor_point_by_year(year):
    faculties = []
    db = get_db()
    data = db.execute(
        'SELECT users.user_id, users.user_name, users.user_email,'
        ' users_status.user_role, users_status.active_status,'
        ' prof.year, prof.previous_balance, prof.ending_balance'
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
            'required_point': '6.50 (To-DO: auto-calc)',
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

def insert_users_status(user_ucinetid, year, user_role, active_status):
    db = get_db()
    user = get_exist_user(user_ucinetid)
    user_id = user['user_id']
    db.execute(
        'INSERT INTO users_status (user_id, year, user_role, active_status)'
        ' VALUES (?, ?, ?, ?)',
        (user_id, year, user_role, active_status)
    )
    db.commit()
    return

def insert_professors_point_info(user_id, year, previous_balance, grad_count, grad_students):
    db = get_db()
    db.execute(
        'INSERT INTO professors_point_info (user_id, year, previous_balance, grad_count, grad_students)'
        ' VALUES (?, ?, ?, ?, ?)',
        (user_id, year, previous_balance, grad_count, grad_students)
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

# TODO: if we have year in user template, probably no need this
def update_user_status_by_professor_template(user_id, year):
    db = get_db()
    db.execute(
        'UPDATE users_status SET year = ?'
        ' WHERE user_id = ?',
        (year, user_id)
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