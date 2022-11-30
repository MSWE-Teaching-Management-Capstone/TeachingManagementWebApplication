import pandas as pd
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from datetime import datetime

from management_app.db import get_db
from management_app.views.auth import login_required
from management_app.views.utils import download_file, upload_file, remove_upload_file, get_upload_filepath, insert_log
from management_app.views.points import calculate_yearly_ending_balance, get_faculty_roles_credit_due, update_yearly_ending_balance, get_yearly_teaching_points, get_grad_mentoring_points, get_yearly_exception_points

faculty = Blueprint('faculty', __name__, url_prefix='/faculty')

# Regular faculty user login URL endpoint
@faculty.route('/', methods=['GET'])
@login_required
def faculty_index():
    user_id = g.user['user_id']
    faculty_name = g.user['user_name']
    res = get_faculty_point_breakdown(user_id)
    year_options = get_professor_point_year_ranges()
    point_info = res[0]
    exceptions = res[1]
    offerings = res[2]
    return render_template(
        'faculty/faculty-dashboard.html',
        faculty_name=faculty_name,
        year_options=year_options,
        point_info=point_info,
        exceptions=exceptions,
        offerings=offerings
    )

@faculty.route('/points', methods=['GET'])
@login_required
def index():
    if request.method == 'GET':
        year_options = get_professor_point_year_ranges()
        if ((len(year_options)) == 0):
            faculties = []
        else:
            year_select = request.args.get('year') or year_options[len(year_options)-1]
            year = int(year_select.split('-')[0])
            faculties = get_all_faculty_point_info(year)
        return render_template('faculty/index.html', faculties=faculties, year_options=year_options)

@faculty.route('/members', methods=['GET'])
@login_required
def members():
    members = get_all_faculty_members()
    return render_template('faculty/members.html', members=members)

@faculty.route('/points/<int:id>', methods=['GET'])
@login_required
def point_breakdown(id):
    db = get_db()
    faculty_name = db.execute('SELECT * FROM users WHERE user_id = ?', (id,)).fetchone()['user_name']
    res = get_faculty_point_breakdown(id)
    year_options = get_professor_point_year_ranges()
    point_info = res[0]
    exceptions = res[1]
    offerings = res[2]
    return render_template(
        'faculty/faculty-dashboard.html',
        faculty_name=faculty_name,
        year_options=year_options,
        point_info=point_info,
        exceptions=exceptions,
        offerings=offerings
    )

@faculty.route('/data-templates/<filename>', methods=['GET'])
@login_required
def download_template(filename):
    if request.method == 'GET':
        # TODO: pre-populate data for the 2nd download
        return download_file(filename)

@faculty.route('/upload/<template>', methods=['POST'])
@login_required
def upload(template):
    if request.method == 'POST':
        file = request.files['facultyTemplate']
        filename = secure_filename(file.filename)
        file_path = get_upload_filepath(filename)

        upload_file(file)

        if template == 'addUsers':
            process_user_file(file_path, 1, 'Users')
        elif template == 'addProfessors':
            process_professors_point_file(file_path, 1, 'Professors_point_info')

        remove_upload_file(file)
        if template == 'addUsers':
            return redirect(url_for('faculty.members'))
        elif template == 'addProfessors':
            return redirect(url_for('faculty.index'))

@faculty.route('/create-member', methods=['GET', 'POST'])
@login_required
def create_member():
    role_options = get_faculty_roles_credit_due()

    if request.method == 'POST':
        error = None
        name = request.form['name']
        ucinetid = request.form['ucinetid']
        email = request.form['email']
        role = request.form['role']

        if not name:
            error = 'Name is required. '
        if not ucinetid:
            error = 'UCI NetID is required. '
        if not email:
            error = 'Email is required. '
        if not role:
            error = 'User Role is required. '

        if error is not None:
            flash(error, 'error')
        else:
            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute(
                    'INSERT INTO users (user_name, user_email, user_ucinetid, admin)'
                    ' VALUES (?, ?, ?, ?)',
                    (name, email, ucinetid, 0)
                )

                user_id = cursor.lastrowid
                start_year = datetime.now().year
                cursor.execute(
                    'INSERT INTO faculty_status (user_id, start_year, role, active_status)'
                    ' VALUES (?, ?, ?, ?)',
                    (user_id, start_year, role, 1)
                )
                db.commit()
                insert_log('Admin', user_id, None, 'Add new faculty member')
            except:
                error = 'Database insert error. User is already existed.'

            if error is None:
                flash('Add faculty member successfully! You can upload faculty point for new academic year data.', 'success')
            else:
                flash(error, 'error')
        return redirect(url_for('faculty.create_member', role_options=role_options))

    if request.method == 'GET':
        return render_template('faculty/create-member.html', role_options=role_options)

@faculty.route('/<int:id>/update/<int:year>', methods=['GET', 'POST'])
@login_required
def update_points(id, year):
    error = None
    exception_options = ['buyout', 'sabbatical', 'leave', 'other']
    faculty = {}
    exceptions = []

    try:
        profile = get_user_yearly_status(id, year)
        faculty = {
            'academic_year': year,
            'member': get_faculty_member_info(id),
            'point': get_faculty_yearly_point_info(id, year),
            'role': profile['role']
        }
        exceptions = get_faculty_yearly_exceptions(id, year)
    except Exception as e:
        print(e)
        error = 'User is not found'

    if request.method == 'POST':
        try:
            grad_count = request.form['grad_count']
            grad_students = request.form['grad_students']
            grad_students = grad_students if len(grad_students) > 0 else None

            if 'exception_adjust' in request.form:
                exception_adjust = request.form['exception_adjust']
                exception_point = request.form['exception_point']
                exception_category = request.form['exception_category']
                exception_message = request.form['exception_message']

                if exception_point is None or len(exception_point) <= 0:
                    error = 'Exception point is required.'
                elif exception_category is None or exception_category == 'None':
                    error = 'Exception category is required.'

                if error is None:
                    points = 0
                    if exception_adjust == 'exception_add':
                        points = float(exception_point) * 1
                    elif exception_adjust == 'exception_subtract':
                        points = float(exception_point) * -1
                    insert_exception(id, year, exception_category, exception_message, points)

            # Update grad_count, grad_students firstly
            update_faculty_grad_info(id, year, grad_count, grad_students)

            # Update total ending_point finally
            update_yearly_ending_balance(id, year)

            insert_log('Admin', id, None, 'Update faculty member points')
        except Exception as e:
            error = 'Failed to update. Please refresh and fill the correct info again.'

        if error is not None:
            flash(error, 'error')
        else:
            flash('Update successfully!', 'success')
        return redirect(url_for('faculty.update_points', id=id, year=year))

    if error is not None:
        flash(error, 'error')

    return render_template(
        'faculty/edit-points.html',
        exception_options=exception_options,
        faculty=faculty,
        exceptions=exceptions
    )

@faculty.route('/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update_member(id):
    error = None
    faculty = {}
    role_options = get_faculty_roles_credit_due()
    role_history = get_faculty_roles_history(id)
    cur_year = datetime.now().year
    cur_profile = get_user_yearly_status(id, cur_year)

    try:
        faculty = {
            'member': get_faculty_member_info(id),
            'role_history': role_history,
            'cur_role': cur_profile['role'],
            'cur_status': cur_profile['active_status']
        }
    except Exception as e:
        print(e)
        error = 'Failed to update. Please refresh and fill the correct info again.'
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            ucinetid = request.form['ucinetid']
            email = request.form['email']
            role = request.form['role']
            status = int(request.form['status'])

            if not name:
                error = 'Name is required. '
            if not ucinetid:
                error = 'UCI NetID is required. '
            if not email:
                error = 'Email is required. '
            if not role:
                error = 'User Role is required. '

            if error is None:
                # Update faculty user info
                update_users(name, email, ucinetid, id)

                # Update faculty profile status and role when changing a new role
                role_start_year = cur_profile['start_year']
                role_end_year = cur_profile['end_year']
                cur_role = cur_profile['role']
                cur_status = cur_profile['active_status']
                cur_year = datetime.now().year
                # Note: only allow to update the latest user_role
                if cur_role != role and role_end_year is None:
                    # credit_due = role_options[role]
                    update_faculty_role(id, role_start_year, cur_year, role)
                    update_yearly_ending_balance(id, role_start_year)

                if cur_status != status and role_end_year is None:
                    update_faculty_status(id, role_start_year, cur_year, role, status)

                insert_log('Admin', id, None, 'Update faculty member information')
        except Exception as e:
            print(e)
            error = 'Failed to update. Please refresh and fill the correct info again.'

        if error is not None:
            flash(error, 'error')
        else:
            flash('Update successfully!', 'success')
        return redirect(url_for('faculty.update_member', id=id))

    if error is not None:
        flash(error, 'error')

    return render_template(
        'faculty/edit-member.html',
        faculty=faculty,
        role_options=role_options
    )

def process_user_file(file_path, sheet__index, sheet__index_name):
    error = None
    try:
        df = pd.read_excel(file_path, sheet_name=sheet__index or sheet__index_name)
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
                role = row[4].lower()
                is_active = 1 if pd.isna(row[5]) else row[5]
                is_admin = 0 if pd.isna(row[6]) else row[6]

                db = get_db()
                user = get_exist_user(user_ucinetid) # Check exist user by ucinetid

                if user is None:
                    try:
                        # If role is staff, just keep admin flag in users table and no need to know staff's active role range
                        insert_users(user_name, user_email, user_ucinetid, is_admin)
                        if role != 'staff':
                            insert_faculty_status(user_ucinetid, start_year, role, is_active)
                    except db.IntegrityError:
                        error = 'Database insert error. Please refresh and upload correct file with new user data.'
                        print('INTEGRITY ERROR\n', traceback.print_exc())
                elif row is not None:
                    error = 'Database insert error. User is already existed. Please refresh and upload correct file with new user data.'
    except Exception as e:
        print(e)
        error = 'Failed to upload. Please refresh and upload the correct data format again.'

    if error is not None:
        flash(error, 'error')
        return

    insert_log('System', None, None, 'Upload users spreadsheet')
    flash('Upload users data succesfully!', 'success')
    return

def process_professors_point_file(file_path, sheet__index, sheet__index_name):
    error = None
    faculty_roles = get_faculty_roles_credit_due()

    try:
        df = pd.read_excel(file_path, sheet_name=sheet__index or sheet__index_name)
        professors_point_rows = df.values.tolist()
        if len(professors_point_rows) == 0:
            error = 'No data source found. Please refresh and upload again.'

        # Note: year represents the start of academic year quarter
        # e.g., year 2019 for 2019-2020 (2019 Fall, 2020 Winter, 2020 Spring)
        for row in professors_point_rows:
            year = row[0]
            user_ucinetid = row[2]
            grad_count = float(row[3])
            grad_students = None if pd.isna(row[4]) else str(row[4])

            user = get_exist_user(user_ucinetid)
            if user is None:
                error = 'User is not existed in the system'
            else:
                user_id = user['user_id']
                profile_status = get_user_yearly_status(user_id, year)

                # If user is not active, display ending_balance with 0 for front-end
                # Only when user is active, insert new ending_balance point record
                if profile_status and profile_status['active_status'] != 1:
                    error = 'Failed to upload the inactive faculty point data. If you would like to assign point to inactive faculty, please activate the faculty through UI first.'
                else:
                    role = profile_status['role'].lower()
                    credit_due = faculty_roles[role]

                    # TODO: Need to remove this later and use the last year
                    previous_balance = get_yearly_previous_balance(user_id, year)
                    if previous_balance is None:
                        previous_balance = float(row[5])

                    db = get_db()
                    try:
                        insert_faculty_point_info(user_id, year, previous_balance, grad_count, grad_students, credit_due)
                    except db.IntegrityError:
                        print('INTEGRITY ERROR\n', traceback.print_exc())
                        error = 'Database insert error. Please refresh and upload correct file with data of a new academic year.'
    except Exception as e:
        print(e)
        error = 'Failed to upload. Please refresh and upload the correct format with new academic year and active users data again.'

    if error is not None:
        flash(error, 'error')
        return

    insert_log('System', None, None, 'Upload professors point spreadsheet')
    flash('Upload professors point info data succesfully!', 'success')
    return

def get_exist_user(user_ucinetid):
    db = get_db()
    return db.execute(
        'SELECT * FROM users WHERE user_ucinetid = ?', (user_ucinetid,)
    ).fetchone()

def get_user_yearly_status(user_id, year):
    # Note: year comes from professor_point_info table, it represents the start of an an academic year
    # e.g., year 2020 should be 2020-2021 (including 2020 Fall(1) - 2021 Winter(2) & Spring(3))
    db = get_db()
    rows = db.execute(
        'SELECT * FROM faculty_status WHERE user_id = ? ORDER BY start_year ASC', (user_id,)
    ).fetchall()

    profile = {}
    return_row = None
    for row in rows:
        if row is not None:
            start_year = row['start_year']
            end_year = row['end_year']

            # If end_year is Null, it's the latest result
            # If end_year is no Null, continue to find result
            if end_year is None and start_year <= year:
                return_row = row
            elif start_year <= year and end_year != year:
                return_row = row
            elif start_year <= year and end_year == year:
                return_row = row

    if return_row is not None:
        profile['start_year'] = return_row['start_year']
        profile['end_year'] = return_row['end_year']
        profile['active_status'] = return_row['active_status']
        profile['role'] = return_row['role']
    return profile

def get_professor_point_year_ranges():
    year_options = []
    db = get_db()
    rows = db.execute(
        'SELECT DISTINCT year FROM faculty_point_info'
    ).fetchall()
    for row in rows:
        year = row['year']
        option = str(year) + '-' + str(year+1)
        year_options.append(option)
    return year_options

def get_yearly_previous_balance(user_id, year):
    db = get_db()
    row = db.execute(
        'SELECT * FROM faculty_point_info WHERE user_id = ? AND year = ?',
        (user_id, year-1,)
    ).fetchone()
    return None if row is None else row['ending_balance']

def get_all_faculty_point_info(year):
    faculties = []
    db = get_db()
    data = db.execute(
        'SELECT users.user_id, users.user_name, users.user_email, faculty.credit_due,faculty.previous_balance, faculty.ending_balance'
        ' FROM users'
        ' JOIN faculty_point_info AS faculty ON users.user_id = faculty.user_id'
        ' WHERE faculty.year = ?'
        ' ORDER BY users.user_name',
        (year,)
    ).fetchall()

    for row in data:
        if row is not None:
            # get user yearly profile_status first
            user_id = row['user_id']
            profile_status = get_user_yearly_status(user_id, year)

            faculties.append({
                'user_id': user_id,
                'academic_year': year,
                'name': row['user_name'],
                'email': row['user_email'],
                'required_point': row['credit_due'],
                'prev_balance': row['previous_balance'],
                'ending_balance': row['ending_balance'],
                'profile_status': profile_status # { start_year, end_year, active_status, role }
            })
    return faculties

def get_all_faculty_members():
    members = []
    db = get_db()
    rows = db.execute(
        'SELECT u.user_id, u.user_name, u.user_email, u.user_ucinetid, f.role, f.active_status'
        ' FROM users AS u'
        ' LEFT JOIN faculty_status AS f ON u.user_id = f.user_id'
        " WHERE f.end_year IS NULL AND f.role != 'staff'"
        ' ORDER BY u.user_name'
    ).fetchall()
    for row in rows:
        members.append({
            'id': row['user_id'],
            'name': row['user_name'],
            'email': row['user_email'],
            'net_id': row['user_ucinetid'],
            'cur_role': row['role'],
            'cur_status': row['active_status']
        })
    return members

def get_faculty_member_info(user_id):
    info = {}
    db = get_db()
    row = db.execute(
        'SELECT * FROM users WHERE user_id = ?', (user_id,)
    ).fetchone()
    if row is not None:
        info = {
            'name': row['user_name'],
            'email': row['user_email'],
            'ucinetid': row['user_ucinetid']
        }
    return info

def get_faculty_yearly_point_info(user_id, year):
    point = {}
    db = get_db()
    row = db.execute(
        'SELECT * FROM faculty_point_info WHERE user_id = ? AND year = ?',
        (user_id, year)
    ).fetchone()
    if row is not None:
        point = {
            'previous_balance': row['previous_balance'],
            'ending_balance': row['ending_balance'],
            'credit_due': row['credit_due'],
            'grad_count': row['grad_count'],
            'grad_students': row['grad_students']
        }
    return point

def get_faculty_yearly_exceptions(user_id, year):
    exceptions = []
    db = get_db()
    rows = db.execute(
        'SELECT * FROM exceptions WHERE user_id = ? AND year = ?', (user_id, year)
    ).fetchall()
    for row in rows:
        exceptions.append({
            'exception_category': row['exception_category'],
            'message': row['message'],
            'points': row['points']
        })
    return exceptions

def get_faculty_roles_history(user_id):
    roles_status = []
    db = get_db()
    rows = db.execute(
        'SELECT * FROM faculty_status WHERE user_id = ? ORDER BY start_year', (user_id,)
    ).fetchall()

    if rows is None:
        return roles_status

    for row in rows:
        roles_status.append({
            'start_year': row['start_year'],
            'end_year': row['end_year'],
            'role': row['role'],
            'active_status': row['active_status']
        })

        if len(roles_status) > 1:
            last_profile = roles_status[len(roles_status)-2]
            last_status = last_profile['active_status']
            last_role = last_profile['role']
            if last_status == row['active_status'] and last_role == row['role']:
                roles_status.pop()
                roles_status[len(roles_status)-1]['end_year'] = row['end_year']
    return roles_status

def get_faculty_point_breakdown(id):
    year_options = get_professor_point_year_ranges()
    point_info = {}
    exceptions = []
    offerings = []
    if len(year_options) > 0:
        user_id = id
        year_select = request.args.get('year') or year_options[len(year_options)-1]
        year = int(year_select.split('-')[0])
        db = get_db()
        points = db.execute(
            'SELECT * from faculty_point_info WHERE user_id = ? AND year = ?', (user_id, year)
        ).fetchone()

        if points is not None:
            offerings = []
            rows = db.execute(
                ' SELECT * FROM scheduled_teaching AS st'
                ' INNER JOIN courses AS c'
                ' ON st.course_title_id = c.course_title_id'
                ' WHERE user_id = ? AND ((year = ? AND quarter = 1) OR (year = ? AND quarter = 2) OR (year = ? AND quarter = 3))',
                (user_id, year, year+1, year+1)
            ).fetchall()

            for row in rows:
                offerings.append(row)

            point_info = {
                **points,
                'teaching_point': get_yearly_teaching_points(user_id, year),
                'grad_point': get_grad_mentoring_points(points['grad_count']),
                'exception_point': get_yearly_exception_points(user_id, year)
            }
        exceptions = get_faculty_yearly_exceptions(user_id, year)
    return [point_info, exceptions, offerings]

def insert_users(user_name, user_email, user_ucinetid, is_admin):
    db = get_db()
    db.execute(
        'INSERT INTO users (user_name, user_email, user_ucinetid, admin)'
        ' VALUES (?, ?, ?, ?)',
        (user_name, user_email, user_ucinetid, is_admin)
    )
    db.commit()
    return

def insert_faculty_status(user_ucinetid, start_year, role, active_status):
    db = get_db()
    user = get_exist_user(user_ucinetid)
    user_id = user['user_id']
    db.execute(
        'INSERT INTO faculty_status (user_id, start_year, role, active_status)'
        ' VALUES (?, ?, ?, ?)',
        (user_id, start_year, role, active_status)
    )
    db.commit()
    return

def insert_faculty_point_info(user_id, year, previous_balance, grad_count, grad_students, credit_due):
    ending_balance = calculate_yearly_ending_balance(user_id, year, grad_count, previous_balance, credit_due)

    db = get_db()
    db.execute(
        'INSERT INTO faculty_point_info (user_id, year, previous_balance, ending_balance, credit_due, grad_count, grad_students)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?)',
        (user_id, year, previous_balance, ending_balance, credit_due, grad_count, grad_students)
    )
    db.commit()
    return

def insert_exception(user_id, year, exception_category, exception_message, points):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO exceptions (user_id, year, exception_category, message, points)'
        ' VALUES (?, ?, ?, ?, ?)',
        (user_id, year, exception_category, exception_message, points)
    )

    exception_id = cursor.lastrowid
    log_category = exception_category
    if len(exception_message) > 0:
        log_category += '_' + exception_message
    insert_log('Admin', user_id, exception_id, log_category)
    db.commit()
    return

def update_users(name, email, ucinetid, user_id):
    db = get_db()
    db.execute(
        'UPDATE users'
        ' SET user_name = ?, user_email = ?, user_ucinetid = ?'
        ' WHERE user_id = ?',
        (name, email, ucinetid, user_id)
    )
    db.commit()
    return

def update_faculty_role(user_id, start_year, cur_year, role):
    db = get_db()
    if cur_year == start_year:
        db.execute(
            'UPDATE faculty_status SET role = ?'
            ' WHERE user_id = ? AND start_year = ?',
            (role, user_id, start_year)
        )
    else:
        db.execute(
            'UPDATE faculty_status SET end_year = ?'
            ' WHERE user_id = ? AND start_year = ?',
            (cur_year, user_id, start_year)
        )
        db.execute(
            'INSERT INTO faculty_status (user_id, start_year, active_status, role)'
            ' VALUES (?, ?, ?, ?)',
            (user_id, cur_year, 1, role)
        )
    db.commit()
    return

def update_faculty_status(user_id, start_year, cur_year, role, status):
    db = get_db()
    if cur_year == start_year:
        db.execute(
            'UPDATE faculty_status SET active_status = ?'
            ' WHERE user_id = ? AND start_year = ?',
            (status, user_id, start_year)
        )
    else:
        db.execute(
            'UPDATE faculty_status SET end_year = ?'
            ' WHERE user_id = ? AND start_year = ?',
            (cur_year, user_id, start_year)
        )
        db.execute(
            'INSERT INTO faculty_status (user_id, start_year, active_status, role)'
            ' VALUES (?, ?, ?, ?)',
            (user_id, cur_year, status, role)
        )
    db.commit()

    status_msg = 'Active' if status == 1 else 'Inactive'
    insert_log('Admin', user_id, None, 'Update faculty member status to "{}"'.format(status_msg))
    return

def update_faculty_grad_info(user_id, year, grad_count, grad_students):
    db = get_db()
    db.execute(
        'UPDATE faculty_point_info SET grad_count = ?, grad_students = ?'
        ' WHERE user_id = ? AND year = ?',
        (grad_count, grad_students, user_id, year)
    )
    db.commit()
    return