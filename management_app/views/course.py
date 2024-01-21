from flask import Blueprint, redirect, render_template, url_for, request, flash, g
from werkzeug.utils import secure_filename
import pandas as pd
import re, os

from management_app.views.auth import login_required
from management_app.db import get_db
from management_app.views.utils import download_file, upload_file, remove_upload_file, get_upload_filepath, insert_log, convert_local_timezone, BASE_DIR, DOWNLOAD_FOLDER
from management_app.views.points import calculate_teaching_point_val, update_yearly_ending_balance, get_latest_academic_year
from management_app.models import *
from sqlalchemy.orm.exc import NoResultFound

courses = Blueprint('courses', __name__, url_prefix='/courses')


@courses.route('/offerings', methods=['GET'])
@login_required
def offerings():
    if request.method == 'GET':
        upload_time = get_latest_scheduled_teaching_upload_time()
        db = get_db()
        courses = []       
        # rows = db.execute(
        #     'SELECT DISTINCT year FROM scheduled_teaching ORDER BY year ASC'
        # ).fetchall()
        stmt = db.select(db.distinct(ScheduledTeaching.year)).order_by(ScheduledTeaching.year.asc())
        res = db.session.execute(stmt).scalars()

        rows = []
        for year in res:
            rows.append(year)

        if rows != []:
            year_options = generate_year_options(rows)            

            # todays_date = date.today()  # creating the date object of today's date        
            # y_start, y_end = todays_date.year, todays_date.year + 1
            year_selected = request.args.get('year')  # 2020-2021 (including: 2020 Fall(1) - 2021 Winter(2) & Spring(3))
            y_start, y_end = get_displayed_year_period(year_options, year_selected)
            courses = get_displayed_courses(y_start, y_end)

        return render_template('courses/offerings.html', courses=courses, year_options=year_options, upload_time=upload_time)


@courses.route('/catalog', methods=['GET'])
@login_required
def catalog():
    db = get_db()    
    # courses = db.execute('SELECT * FROM courses').fetchall()
    rows = db.session.execute(db.select(Courses)).scalars()
    courses = []
    for row in rows:
        courses.append({"course_id": row.course_id, "course_title_id": row.course_title_id, "course_title": row.course_title, "units": row.units, "course_level": row.course_level, "combine_with": row.combine_with})

    return render_template('courses/catalog.html', courses=courses)


@courses.route('/data-templates/<filename>', methods=['GET'])
@login_required
def download_template(filename):
    if request.method == 'GET':
        db = get_db()
        # res = db.execute('SELECT COUNT(*) AS cnt FROM scheduled_teaching').fetchone()
        stmt = db.select(db.func.count()).select_from(ScheduledTeaching)
        res = db.session.execute(stmt).scalar()

        # Prepopulate schedule_teaching template after the first time upload        
        if res != 0:
            prepopulate_schedule_teaching_template()
            
        return download_file(filename)


@courses.route('/upload', methods=['POST'])
@login_required
def upload_user_file():
    if (request.method == 'POST'):
        file = request.files['courseTemplate']
        filename = secure_filename(file.filename)
        file_path = get_upload_filepath(filename)
        upload_file(file)

        rows_dict = {}
        user_id_and_academic_year_set = set()
        offering_tmp = get_offering_from_excel(file_path, file, rows_dict, user_id_and_academic_year_set)

        if offering_tmp == []:
            return redirect(url_for('courses.offerings'))

        for row_dict in offering_tmp:
            insert_or_update_scheduled_teaching_for_each_user(row_dict["user_UCINetID_list"], row_dict["num_of_enrollment"], row_dict["user_id_and_academic_year_set"], row_dict["academic_year"], row_dict["combine_with"], row_dict["rows_dict"], row_dict["course_title_id"], row_dict["year"], row_dict["quarter"], row_dict["course_sec"], row_dict["offload_or_recall_flag"], row_dict["num_of_co_taught"])

        insert_log('Admin: ' + g.user.user_name, None, None, "Upload scheduled teaching file")
        flash('Upload scheduled teaching file successfully!', 'success')

        # rules #5: Combined grad/undergraduate classes
        calculate_combined_classes_and_update_scheduled_teaching(rows_dict)

        for pair in user_id_and_academic_year_set:
            update_yearly_ending_balance(pair[0], pair[1])
        
        remove_upload_file(file)

        return redirect(url_for('courses.offerings'))


@courses.route('/create_offering', methods=['GET', 'POST'])
@login_required
def create_offering():
    ucinetid_options = get_ucinetid()
    if request.method == 'POST':
        year = request.form['year']
        quarter = request.form['quarter']
        academic_year = get_academic_year(year, quarter)
        
        user_UCINetID_list = []        
        if request.form['multi_ucinetid'] != "":
            user_UCINetID_list = get_ucinetid_list(request.form['multi_ucinetid'])
        user_UCINetID_list.append(request.form['ucinetid'])
        
        user_id = get_user_id(request.form['ucinetid'])

        num_of_co_taught = len(user_UCINetID_list)
        course_title_id = request.form['course_title_id'].strip().replace(' ', '')
        combine_with = get_combine_with(course_title_id)
        course_sec = request.form['course_sec'].strip()
        num_of_enrollment = get_num_of_enrollment(request.form['num_of_enrollment'])
        offload_or_recall_flag = get_offload_or_recall_flag(request.form['offload_or_recall_flag'])

        # Input validation: if not valid input, show error message with the incorrect column
        if not is_valid_input(year, quarter, user_UCINetID_list, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag):
            return redirect(url_for('courses.offerings'))
        
        user_id_and_academic_year_set = set()
        rows_dict = {}
        insert_or_update_scheduled_teaching_for_each_user(user_UCINetID_list, num_of_enrollment, user_id_and_academic_year_set, academic_year, combine_with, rows_dict, course_title_id, year, quarter, course_sec, offload_or_recall_flag, num_of_co_taught)

        insert_log('Admin: ' + g.user.user_name, user_id, None, "Add scheduled teaching")
        flash('Add scheduled teaching data successfully!', 'success')

        # rules #5: Combined grad/undergraduate classes
        calculate_combined_classes_and_update_scheduled_teaching(rows_dict)        

        for pair in user_id_and_academic_year_set:
            update_yearly_ending_balance(pair[0], pair[1])

        return redirect(url_for('courses.offerings'))
    return render_template('courses/create-offering.html', ucinetid_options=ucinetid_options)


@courses.route('/update/<int:user_id>/<int:year>/<int:quarter>/<course_title_id>/<course_sec>', methods=['GET', 'POST'])
@login_required
def update_offering(user_id, year, quarter, course_title_id, course_sec):
    course = {
        'year': year,
        'quarter': quarter,
        'user_name': get_user_name(user_id),
        'course_title_id': course_title_id,
        'course_sec': course_sec
    }
    
    if request.method == 'POST':
        num_of_enrollment = request.form['enrollment']
        db = get_db()
        # db.execute(
        #     'UPDATE scheduled_teaching SET enrollment = ?'
        #     ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
        #     (num_of_enrollment, user_id, year, quarter, course_title_id, course_sec)
        # )
        # db.commit()
        stmt = db.update(ScheduledTeaching).\
                values(enrollment=num_of_enrollment).\
                where(
                    (ScheduledTeaching.user_id == user_id) &
                    (ScheduledTeaching.year == year) &
                    (ScheduledTeaching.quarter == quarter) &
                    (ScheduledTeaching.course_title_id == course_title_id) &
                    (ScheduledTeaching.course_sec == course_sec)
                )

        db.session.execute(stmt)
        db.session.commit()

        insert_log('Admin: ' + g.user.user_name, user_id, None, "Edit scheduled teaching")
        flash('Edit scheduled teaching data successfully!', 'success')

        academic_year = get_academic_year(year, quarter)
        update_yearly_ending_balance(user_id, academic_year)

        return redirect(url_for('courses.offerings'))
    return render_template('courses/edit-offering.html', course=course)


@courses.route('/delete/<int:user_id>/<int:year>/<int:quarter>/<course_title_id>/<course_sec>', methods=['GET', 'POST'])
@login_required
def delete_offering(user_id, year, quarter, course_title_id, course_sec):
    db = get_db()
    # db.execute(
    #     'DELETE FROM scheduled_teaching '
    #     ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
    #     (user_id, year, quarter, course_title_id, course_sec)
    # )
    # db.commit()
    stmt = db.delete(ScheduledTeaching).\
        where(
            (ScheduledTeaching.user_id == user_id) &
            (ScheduledTeaching.year == year) &
            (ScheduledTeaching.quarter == quarter) &
            (ScheduledTeaching.course_title_id == course_title_id) &
            (ScheduledTeaching.course_sec == course_sec)
        )
    db.session.execute(stmt)
    db.session.commit()

    insert_log('Admin: ' + g.user.user_name, user_id, None, "Delete scheduled teaching")
    flash('Delete scheduled teaching data successfully!', 'success')

    academic_year = get_academic_year(year, quarter)
    update_yearly_ending_balance(user_id, academic_year)

    return redirect(url_for('courses.offerings'))

@courses.route('/catalog/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':        
        title_id = request.form['title-id'].strip().replace(' ', '')
        title = request.form['title']
        level = request.form['level']
        units = request.form['units']
        combine_with = request.form['combine-with'].strip().replace(' ', '')

        error = None
        if is_course_title_id_taken(title_id):
            error = 'Course Title ID is already taken.'

        if error is not None:
            flash(error, 'error')
        else:
            db = get_db()
            # db.execute("""
            #     INSERT INTO courses (course_title_id, course_title, units, course_level, combine_with)
            #     VALUES (?, ?, ?, ?, ?)
            # """, (title_id, title, units, level, combine_with))
            # db.commit()
            stmt = db.insert(Courses).values(
                course_title_id=title_id,
                course_title=title,
                units=units,
                course_level=level,
                combine_with=combine_with
            )

            db.session.execute(stmt)
            db.session.commit()

            insert_log('Admin: ' + g.user.user_name, None, None, f"Added new course ({title_id})")
            flash('Course added successfully!', 'success')
   
    return render_template('courses/add-course.html')

@courses.route('/catalog/course/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(id):
    db = get_db()

    # course = db.execute('SELECT * FROM courses WHERE course_id = ?', (id,)).fetchone()
    course = db.session.execute(db.select(Courses).where(Courses.course_id == id)).scalar_one()

    if request.method == 'POST':
        title = request.form['title']
        level = request.form['level']
        units = request.form['units']
        combine_with = request.form['combine-with']

        # db.execute("""
        #     UPDATE courses
        #     SET course_title = ?, course_level = ?, units = ?, combine_with = ?
        #     WHERE course_id = ?
        # """, (title, level, units, combine_with, id))
        # db.commit()
        stmt = db.update(Courses).\
            values(course_title=title, course_level=level, units=units, combine_with=combine_with).\
            where(Courses.course_id == id)            

        db.session.execute(stmt)
        db.session.commit()


        update_teaching_point_balances(course.course_title_id)
        insert_log('Admin: ' + g.user.user_name, None, None, f"Edited course ({course.course_title_id})")
        flash('Update successfully!', 'success')

    return render_template('courses/edit-course.html', course=course)


def is_course_title_id_taken(title_id):
    db = get_db()
    # res = db.execute('SELECT COUNT(*) AS count FROM courses WHERE course_title_id = ?', (title_id,)).fetchone()
    res = db.session.execute(db.select(db.func.count()).where(Courses.course_title_id == title_id)).scalar()

    return res > 0

def update_teaching_point_balances(title_id):
    db = get_db()
    start_year = get_latest_academic_year()
    end_year = start_year + 1
    updated_users = set()
    # offerings = db.execute("""
    #     SELECT *
    #     FROM scheduled_teaching
    #     WHERE ((year = ? AND quarter = 1) OR (year = ? AND (quarter = 2 OR quarter = 3))) AND course_title_id = ?
    # """, (start_year, end_year, title_id)).fetchall()
    stmt = db.select(ScheduledTeaching).\
        where(
            (((ScheduledTeaching.year == start_year) & (ScheduledTeaching.quarter == 1)) | ((ScheduledTeaching.year == end_year) & ((ScheduledTeaching.quarter == 2) | (ScheduledTeaching.quarter == 3)))) & (ScheduledTeaching.course_title_id == title_id))
    offerings = db.session.execute(stmt).scalars()

    for offering in offerings:
        # co_taught = db.execute("""
        #     SELECT COUNT(DISTINCT user_id) AS num
        #     FROM scheduled_teaching
        #     GROUP BY year, quarter, course_title_id
        #     HAVING year = ? AND quarter = ? AND course_title_id = ?
        # """, (offering.year, offering.quarter, offering.course_title_id)).fetchone()
        stmt = db.select(
            db.func.count(db.func.DISTINCT(ScheduledTeaching.user_id))
        ).where(
            (ScheduledTeaching.year == offering.year) &
            (ScheduledTeaching.quarter == offering.quarter) &
            (ScheduledTeaching.course_title_id == offering.course_title_id)
        ).group_by(
            ScheduledTeaching.year,
            ScheduledTeaching.quarter,
            ScheduledTeaching.course_title_id
        )

        co_taught = db.session.execute(stmt).scalar()


        value = calculate_teaching_point_val(
            offering.course_title_id,
            offering.enrollment,
            offering.offload_or_recall_flag,
            offering.year,
            offering.quarter,
            offering.user_id,
            co_taught
        )
        if value != offering.teaching_point_val:
            # db.execute("""
            #     UPDATE scheduled_teaching
            #     SET teaching_point_val = ?
            #     WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?
            # """, (value, offering.user_id, offering.year, offering.quarter, offering.course_title_id, offering.course_sec))
            stmt = db.update(ScheduledTeaching).\
                values(teaching_point_val=value).\
                where(
                    (ScheduledTeaching.user_id == offering.user_id) &
                    (ScheduledTeaching.year == offering.year) &
                    (ScheduledTeaching.quarter == offering.quarter) &
                    (ScheduledTeaching.course_title_id == offering.course_title_id) &
                    (ScheduledTeaching.course_sec == offering.course_sec)
                )

            db.session.execute(stmt)

            updated_users.add(offering.user_id)
    
    # db.commit()
    db.session.commit()

    for id in updated_users:
        update_yearly_ending_balance(id, start_year)

def is_valid_input(year, quarter, user_UCINetID_list, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag):   
    db = get_db()

    # check the existence of an user    
    for ucinetid in user_UCINetID_list:
        # user = db.execute(
        #     'SELECT * FROM users WHERE user_ucinetid = ?', (ucinetid,)
        # ).fetchone()
        stmt = db.select(Users).where(Users.user_ucinetid == ucinetid)
        try:
            user = db.session.execute(stmt).scalar()
        except NoResultFound:
            user = None

        if user is None:
            err_msg = f"Operation failed: User {ucinetid} not exists in the system."
            flash(err_msg, 'error')
            return False

    # check the existence of a course
    # course = db.execute(
    #     'SELECT * FROM courses WHERE course_title_id = ?', (course_title_id,)
    # ).fetchone()
    stmt = db.select(Courses).where(Courses.course_title_id == course_title_id)
    try:
        course = db.session.execute(stmt).scalar()
    except NoResultFound:
        course = None

    if course is None:
        err_msg = f"Operation failed: Course {course_title_id} not exists in the system."
        flash(err_msg, 'error')
        return False
    
    # data examples:
    # year	
    # quarter: 1, 2, 3, 4
    # user_UCINetID_list: [XXX] or [XXX,XXX,XXX]
    # course_title_id: CS143B
    # course_sec: A, A1, 1, 15
    # num_of_enrollment: None or 0 or positvie integer	
    # offload_or_recall_flag: 1 or 0

    col_name = None
    if re.match(r'\d{4}', str(year)) is None:
        col_name = "year"
    elif re.match(r'[1-4]', str(quarter)) is None:
        col_name = "quarter"
    elif None in [re.match(r'[a-z]+', ucinetid) for ucinetid in user_UCINetID_list]:
        col_name = "user_UCINetID"
    elif re.match(r'[0-9A-Z]+', course_title_id) is None:
        col_name = "course_title_id"  
    elif re.match(r'[0-9A-Z]+', course_sec) is None:
        col_name = "course_sec"  
    elif num_of_enrollment != -1 and re.match(r'[0-9]+', str(num_of_enrollment)) is None:
        col_name = "num_of_enrollment"
    elif re.match(r'[01]', str(offload_or_recall_flag)) is None:
        col_name = "offload_or_recall_flag"  
    else:        
        return True
    
    err_msg = f"Operation failed: Incorrect data format on {col_name} column."
    flash(err_msg, 'error')
    return False

def check_existence_of_row(user_id, year, quarter, course_title_id, course_sec):
    db = get_db()
    # row = db.execute(
    #     'SELECT * FROM scheduled_teaching '
    #     ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
    #     (user_id, year, quarter, course_title_id, course_sec)
    # ).fetchone()
    stmt = db.select(ScheduledTeaching).\
        where(
            (ScheduledTeaching.user_id == user_id) &
            (ScheduledTeaching.year == year) &
            (ScheduledTeaching.quarter == quarter) &
            (ScheduledTeaching.course_title_id == course_title_id) &
            (ScheduledTeaching.course_sec == course_sec)
        )
    try:
        row = db.session.execute(stmt).scalar()
    except NoResultFound:
        row = None

    return row

def insert_scheduled_teaching(user_id, year, quarter, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag, teaching_point_val):
    db = get_db()
    # db.execute(
    #     'INSERT INTO scheduled_teaching (user_id, year, quarter, course_title_id, course_sec, enrollment, offload_or_recall_flag, teaching_point_val)'
    #     ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    #     (user_id, year, quarter, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag, teaching_point_val)
    # )
    # db.commit()
    db.session.add(ScheduledTeaching(
        user_id=user_id,
        year=year,
        quarter=quarter,
        course_title_id=course_title_id,
        course_sec=course_sec,
        enrollment=num_of_enrollment,
        offload_or_recall_flag=offload_or_recall_flag,
        teaching_point_val=teaching_point_val))
    db.session.commit()

def update_scheduled_teaching(num_of_enrollment, offload_or_recall_flag, teaching_point_val, user_id, year, quarter, course_title_id, course_sec):
    db = get_db()
    # db.execute(
    #     'UPDATE scheduled_teaching SET enrollment = ?, offload_or_recall_flag = ?, teaching_point_val = ?'
    #     ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
    #     (num_of_enrollment, offload_or_recall_flag, teaching_point_val, user_id, year, quarter, course_title_id, course_sec)
    # )
    # db.commit()
    stmt = db.update(ScheduledTeaching).\
        values(
            enrollment=num_of_enrollment,
            offload_or_recall_flag=offload_or_recall_flag,
            teaching_point_val=teaching_point_val
        ).\
        where(
            ScheduledTeaching.user_id == user_id,
            ScheduledTeaching.year == year,
            ScheduledTeaching.quarter == quarter,
            ScheduledTeaching.course_title_id == course_title_id,
            ScheduledTeaching.course_sec == course_sec
        )

    db.session.execute(stmt)
    db.session.commit()

def get_ucinetid():
    ucinetids = []
    db = get_db()
    # rows = db.execute('SELECT DISTINCT user_ucinetid FROM users ORDER BY user_ucinetid ASC').fetchall()
    stmt = db.select(db.distinct(Users.user_ucinetid)).order_by(Users.user_ucinetid.asc())
    user_ucinetids = db.session.execute(stmt).scalars()
        
    for user_ucinetid in user_ucinetids:
        ucinetids.append(user_ucinetid)
    return ucinetids

def get_academic_year(year, quarter):
    if quarter == 1:
        return year
    if quarter == 2 or quarter == 3:
        return year-1

def get_ucinetid_list(ucinetids):
    return [ucinetid.strip() for ucinetid in ucinetids.split(',')]

def get_combine_with(course_title_id):
    db = get_db()
    # combine_with = db.execute(
    #     'SELECT combine_with FROM courses'
    #     ' WHERE course_title_id = ?', (course_title_id,)
    # ).fetchone()
    stmt = db.select(Courses).where(Courses.course_title_id == course_title_id)
    try:
        res = db.session.execute(stmt).scalar_one()
    except NoResultFound:
        res = None

    return res if res is None else res.combine_with

def get_num_of_enrollment(num):
    return -1 if pd.isna(num) or num == "" else num

def get_offload_or_recall_flag(flag):
    return 0 if pd.isna(flag) else flag

def get_user_id(user_UCINetID):
    db = get_db()
    user_id = None
    # use "user_UCINetID" in s_t file to get user_id in users table
    # insert these 2 rows into users table to test
        # value: Alfred Chen, alfchen@uci.edu, alfchen
        # value: Eric Mjolsness, emj@uci.edu, emj
    # row = db.execute(
    #     'SELECT user_id FROM users'
    #     ' WHERE user_ucinetid = ?', (user_UCINetID,)
    # ).fetchone()
    stmt = db.select(Users.user_id).where(Users.user_ucinetid == user_UCINetID)
    try:
        row = db.session.execute(stmt).scalar()
    except NoResultFound:
        row = None

    if row != None:
        user_id = row

    return user_id

def get_user_name(user_id):
    db = get_db()
    user_name = None
    # row = db.execute(
    #     'SELECT user_name FROM users'
    #     ' WHERE user_id = ?', (user_id,)
    # ).fetchone()
    stmt = db.select(Users.user_name).where(Users.user_id == user_id)
    try:
        row = db.session.execute(stmt).scalar()
    except NoResultFound:
        row = None

    if row != None:
        user_name = row

    return user_name

def get_teaching_point_val(num_of_enrollment, user_id_and_academic_year_set, user_id, academic_year, combine_with, rows_dict, course_title_id, year, quarter, course_sec, offload_or_recall_flag, num_of_co_taught): 
    if num_of_enrollment == -1:
        teaching_point_val = 1  # default value is 1 for each course
    else:                    
        user_id_and_academic_year_set.add((user_id, academic_year))
        if combine_with != None: 
            rows_dict[course_title_id] = {'user_id': user_id, 'year': year, 'quarter': quarter, 'course_sec': course_sec, 'num_of_enrollment': num_of_enrollment, 'offload_or_recall_flag': offload_or_recall_flag, 'num_of_co_taught': num_of_co_taught, 'combine_with': combine_with}

            teaching_point_val = 1
        else:
            teaching_point_val = calculate_teaching_point_val(course_title_id, num_of_enrollment, offload_or_recall_flag, year, quarter, user_id, num_of_co_taught)

    return teaching_point_val, user_id_and_academic_year_set, rows_dict

def calculate_combined_classes_and_update_scheduled_teaching(rows_dict):
    keys = list(rows_dict.keys())
    for i in range(len(keys)):
        if keys[i] in rows_dict:
            row1_dict = rows_dict[keys[i]]
            row2_dict = rows_dict[row1_dict['combine_with']]
            val1 = calculate_teaching_point_val(keys[i], row1_dict['num_of_enrollment'], row1_dict['offload_or_recall_flag'], row1_dict['year'], row1_dict['quarter'], row1_dict['user_id'], row1_dict['num_of_co_taught'])
            val2 = calculate_teaching_point_val(row1_dict['combine_with'], row2_dict['num_of_enrollment'], row2_dict['offload_or_recall_flag'], row2_dict['year'], row2_dict['quarter'], row2_dict['user_id'], row2_dict['num_of_co_taught'])
            
            teaching_point_val = val1+0.25 if val1 > val2 else val2+0.25
            # Points are divided equally between the combined grad/undergraduate classes
            teaching_point_val_avg = teaching_point_val / 2
            
            update_scheduled_teaching(row1_dict['num_of_enrollment'], row1_dict['offload_or_recall_flag'], teaching_point_val_avg, row1_dict['user_id'], row1_dict['year'], row1_dict['quarter'], keys[i], row1_dict['course_sec'])
            update_scheduled_teaching(row2_dict['num_of_enrollment'], row2_dict['offload_or_recall_flag'], teaching_point_val_avg, row2_dict['user_id'], row2_dict['year'], row2_dict['quarter'], row1_dict['combine_with'], row2_dict['course_sec'])

            rows_dict.pop(row1_dict['combine_with'])
            rows_dict.pop(keys[i])

def insert_or_update_scheduled_teaching_for_each_user(user_UCINetID_list, num_of_enrollment, user_id_and_academic_year_set, academic_year, combine_with, rows_dict, course_title_id, year, quarter, course_sec, offload_or_recall_flag, num_of_co_taught):

    for user_UCINetID in user_UCINetID_list:
        user_id = get_user_id(user_UCINetID)

        teaching_point_val, user_id_and_academic_year_set, rows_dict = get_teaching_point_val(num_of_enrollment, user_id_and_academic_year_set, user_id, academic_year, combine_with, rows_dict, course_title_id, year, quarter, course_sec, offload_or_recall_flag, num_of_co_taught)

        row = check_existence_of_row(user_id, year, quarter, course_title_id, course_sec)               
        
        if row is None:
            insert_scheduled_teaching(user_id, year, quarter, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag, teaching_point_val)
        else:
            update_scheduled_teaching(num_of_enrollment, offload_or_recall_flag, teaching_point_val, user_id, year, quarter, course_title_id, course_sec)


def get_latest_scheduled_teaching_upload_time():
    db = get_db()
    # res = db.execute(
    #     """SELECT * FROM logs
    #      WHERE log_category LIKE '%Upload scheduled teaching file%'
    #      ORDER BY created DESC LIMIT 1"""
    # ).fetchone()
    stmt = db.select(Logs).\
        where(Logs.log_category.like('%Upload scheduled teaching file%')).\
        order_by(Logs.created.desc()).limit(1)
    try:
        res = db.session.execute(stmt).scalar()
    except NoResultFound:
        res = None

    if res is None:
        return ""
    return convert_local_timezone(res.created)

def prepopulate_schedule_teaching_template():
    db = get_db()
    # get the latest academic year from scheduled_teaching
    # year = db.execute(
    #     'SELECT DISTINCT year FROM scheduled_teaching ORDER BY year DESC LIMIT 1'
    # ).fetchone()['year']
    stmt = db.select(db.distinct(ScheduledTeaching.year)).order_by(db.desc(ScheduledTeaching.year)).limit(1)
    year = db.session.execute(stmt).scalar_one()

    # Should include: year, quarter, ucinetid, course_sec
    # Each prodessor has 3 rows: fall, winter, spring
    ucinetids = get_ucinetid()
    rows_data = []
    for ucinetid in ucinetids:
        rows_data.append([year, "Fall", ucinetid, "", "A", "", ""])
        rows_data.append([year+1, "Winter", ucinetid, "", "A", "", ""])
        rows_data.append([year+1, "Spring", ucinetid, "", "A", "", ""])

    df1 = pd.DataFrame([["Scheduled_teaching", "quarter", "1 (Fall), 2 (Winter), 3 (Spring), 4 (Summer)"], ["", "course_title_id", "CS143B"], ["", "course_sec", "A"], ["", "num_of_enrollment", "180"], ["", "offload_or_recall_flag", "1 for \"offload / recall\" or 0"]], 
        columns=[" ", "column name", "column values"])

    df2 = pd.DataFrame(rows_data,
        columns=["year", "quarter", "user_UCINetID",	"course_title_id", "course_sec", "num_of_enrollment", "offload_or_recall_flag"])    

    with pd.ExcelWriter(os.path.join(BASE_DIR, DOWNLOAD_FOLDER, 'scheduled_teaching.xlsx'), mode='w') as writer:  
        df1.to_excel(writer, sheet_name='Examples for column value', index=False)
        df2.to_excel(writer, sheet_name='Scheduled_teaching', index=False)


def generate_year_options(rows):
    db = get_db()
    # min_quarter = db.execute(
    #     'SELECT DISTINCT quarter FROM scheduled_teaching WHERE year = ? ORDER BY quarter ASC', (rows[-1],)
    # ).fetchone()['quarter']
    stmt = db.select(db.distinct(ScheduledTeaching.quarter)).where(ScheduledTeaching.year == rows[-1]).order_by(db.asc(ScheduledTeaching.quarter)).limit(1)
    min_quarter = db.session.execute(stmt).scalar_one()

    year_options = []
    # generate year options
    for year in rows:
        year_options.append(str(year) + '-' + str(year+1))

    # if the biggest year don't have quarter 1, then this biggest year can't be the start of the year period
    if min_quarter != '1':
        year_options.pop()
    return year_options


def get_displayed_year_period(year_options, year_selected):
    if year_selected != None:
        y_start = year_selected.split('-')[0]
        y_end = year_selected.split('-')[1]
    else:
        y_start = year_options[-1].split('-')[0]
        y_end = year_options[-1].split('-')[1]
    return y_start, y_end


def get_displayed_courses(y_start, y_end):
    db = get_db()
    # courses = db.execute(
    #     'SELECT year, quarter, user_name, st.course_title_id, course_sec, enrollment, st.user_id'
    #     ' FROM scheduled_teaching st JOIN courses ON st.course_title_id = courses.course_title_id JOIN users ON st.user_id = users.user_id'
    #     ' WHERE (year = ? AND quarter = 1) OR (year = ? AND quarter = 2) OR (year = ? AND quarter = 3)'
    #     ' ORDER BY year DESC, quarter DESC, st.course_title_id', (y_start, y_end, y_end)
    # ).fetchall()
    stmt = db.select(
        ScheduledTeaching.year,
        ScheduledTeaching.quarter,
        Users.user_name,
        ScheduledTeaching.course_title_id,
        ScheduledTeaching.course_sec,
        ScheduledTeaching.enrollment,
        ScheduledTeaching.user_id
        ).join(Courses, ScheduledTeaching.course_title_id == Courses.course_title_id)\
        .join(Users, ScheduledTeaching.user_id == Users.user_id)\
        .where(
            ((ScheduledTeaching.year == y_start) & (ScheduledTeaching.quarter == 1)) |
            ((ScheduledTeaching.year == y_end) & (ScheduledTeaching.quarter == 2)) |
            ((ScheduledTeaching.year == y_end) & (ScheduledTeaching.quarter == 3))
        ).order_by(
            ScheduledTeaching.year.desc(),
            ScheduledTeaching.quarter.desc(),
            ScheduledTeaching.course_title_id
        )

    rows = db.session.execute(stmt).fetchall()
    courses = []
    for row in rows:
        courses.append({"year": row[0], "quarter": row[1], "user_name": row[2], "course_title_id": row[3], "course_sec": row[4], "enrollment": row[5], "user_id": row[6]})

    return courses


def get_offering_from_excel(file_path, file, rows_dict, user_id_and_academic_year_set):
    quarterDict = {"fall": 1, "winter": 2, "spring": 3, "summer": 4}
    df = pd.read_excel(file_path, sheet_name=1)
    rows = df.values.tolist()    
    offering_tmp = []
    for row in rows:
        year = row[0]
        quarter = row[1]
        if type(quarter) == str:
            quarter = quarter.lower()
            if quarter in quarterDict.keys():
                quarter = quarterDict[quarter]
        
        academic_year = get_academic_year(year, quarter)            
        
        # if it's a co-taught course, the UCINetID column will have multiple users seperated by comma
        # row[2] looks like: " emj, alfchen"
        user_UCINetID_list = get_ucinetid_list(row[2])
        num_of_co_taught = len(user_UCINetID_list)

        # course_title_id column may be like "CS 143B" or "CS143B" -> all convert to "CS143B"
        course_title_id = row[3].strip().replace(' ', '')
        combine_with = get_combine_with(course_title_id)
        
        course_sec = row[4].strip()
        
        num_of_enrollment = get_num_of_enrollment(row[5])
        offload_or_recall_flag = get_offload_or_recall_flag(row[6])

        # Input validation: if not valid input, reject the whole file and show error message with the incorrect column (insert or update only when the file is all correct)        
        if not is_valid_input(year, quarter, user_UCINetID_list, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag):
            remove_upload_file(file)                
            return []

        offering_tmp.append({"user_UCINetID_list": user_UCINetID_list, "num_of_enrollment": num_of_enrollment, "user_id_and_academic_year_set": user_id_and_academic_year_set, "academic_year": academic_year, "combine_with": combine_with, "rows_dict": rows_dict, "course_title_id": course_title_id, "year": year, "quarter": quarter, "course_sec": course_sec, "offload_or_recall_flag": offload_or_recall_flag, "num_of_co_taught": num_of_co_taught})

    return offering_tmp