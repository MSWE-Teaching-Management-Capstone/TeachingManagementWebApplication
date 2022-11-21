from flask import Blueprint, redirect, render_template, url_for, request, flash
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import date
import re

from management_app.views.auth import login_required
from management_app.db import get_db
from management_app.views.utils import download_file, upload_file, remove_upload_file, get_upload_filepath
from management_app.views.points import calculate_teaching_point_val, update_yearly_ending_balance



courses = Blueprint('courses', __name__, url_prefix='/courses')

@courses.route('/offerings', methods=['GET'])
@login_required
def offerings():
    if request.method == 'GET':
        db = get_db()        
        year_options = []
        courses = []       
        rows = db.execute(
            'SELECT DISTINCT year FROM scheduled_teaching ORDER BY year ASC'
        ).fetchall()          

        if rows != []:
            min_quarter = db.execute(
            'SELECT DISTINCT quarter FROM scheduled_teaching WHERE year = ? ORDER BY quarter ASC', (rows[-1]['year'],)
            ).fetchone()['quarter']           
        
            # generate year options
            for row in rows:
                year = row['year']
                year_options.append(str(year) + '-' + str(year+1))

            # if the biggest year don't have quarter 1, then this biggest year can't be the start of the year period
            if min_quarter != '1':
                year_options.pop()

            # todays_date = date.today()  # creating the date object of today's date        
            # y_start, y_end = todays_date.year, todays_date.year + 1
            year_selected = request.args.get('year')  # 2020-2021 (including: 2020 Fall(1) - 2021 Winter(2) & Spring(3))
            if year_selected != None:
                y_start = year_selected.split('-')[0]
                y_end = year_selected.split('-')[1]
            else:
                y_start = year_options[-1].split('-')[0]
                y_end = year_options[-1].split('-')[1]

            courses = db.execute(
                'SELECT year, quarter, user_name, st.course_title_id, course_sec, enrollment'
                ' FROM scheduled_teaching st JOIN courses ON st.course_title_id = courses.course_title_id JOIN users ON st.user_id = users.user_id'
                ' WHERE (year = ? AND quarter = 1) OR (year = ? AND quarter = 2) OR (year = ? AND quarter = 3)'
                ' ORDER BY year DESC, quarter DESC, st.course_title_id', (y_start, y_end, y_end)
            ).fetchall()
            
        return render_template('courses/offerings.html', courses=courses, year_options=year_options)





@courses.route('/catalog', methods=['GET'])
@login_required
def catalog():
    if request.method == 'GET':
        # # Initial courses table: parse input file and insert data into db only for the first time
        # db = get_db()

        # df = pd.read_excel(get_upload_filepath("courses.xlsx"), sheet_name=1)
        # rows = df.values.tolist()
        # for row in rows:
        #     # course_title_id column may be like "CS 143B" or "CS143B" -> all convert to "CS143B"
        #     course_title_id = row[0].strip().replace(' ', '')

        #     course_title = row[1].strip()
        #     units = row[2]            
        #     course_level = row[3].strip()

        #     # combine_with column may be like "CS 143B" or "CS143B" -> all convert to "CS143B"
        #     if pd.isna(row[4]):
        #         combine_with = None
        #     else:            
        #         combine_with = str(row[4]).strip().replace(' ', '')
            

        #     db.execute(
        #         'INSERT INTO courses (course_title_id, course_title, units, course_level, combine_with)'
        #         ' VALUES (?, ?, ?, ?, ?)',
        #         (course_title_id, course_title, units, course_level, combine_with)
        #     )
        #     db.commit()


        # TODO: show "combine_with" column in the front end so that admin will remember to edit it if he needs to
        # TODO: check: the "unit" column of the courses file only has single values (in the unit column, I won’t get values like 2-4 or 4+2), if not: generate warning and reject add/edit

        return render_template('courses/catalog.html')


@courses.route('/data-templates/<filename>', methods=['GET'])
@login_required
def download_template(filename):

    # TODO: do template Prefill: 
    # Schedule_teaching template prepopulate: year, quarter, usename, ucinetid, 
        # course_type： Lec, course_sec: A (each prodessor 3 rows: fall, winter, spring)
    # courses template: no need to prepopulate

    if request.method == 'GET':
        return download_file(filename)

@courses.route('/upload', methods=['POST'])
@login_required
def upload_user_file():
    if (request.method == 'POST'):
        file = request.files['courseTemplate']
        filename = secure_filename(file.filename)
        file_path = get_upload_filepath(filename)
        upload_file(file)

        quarterDict = {"Fall": 1, "Winter": 2, "Spring": 3, "Summer": 4}
        db = get_db()

        df = pd.read_excel(file_path, sheet_name=1)
        rows = df.values.tolist()
        rows_dict = {}
        user_id_and_academic_year_set = set()
        for row in rows:
            year = row[0]
            quarter = row[1]
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

            # Input validation: if not valid input, reject the whole file and show error message with the incorrect column
            if not is_valid_input(year, quarter, user_UCINetID_list, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag):
                remove_upload_file(file)                    
                return redirect(url_for('courses.offerings'))

            insert_or_update_scheduled_teaching_for_each_user(user_UCINetID_list, num_of_enrollment, user_id_and_academic_year_set, academic_year, combine_with, rows_dict, course_title_id, year, quarter, course_sec, offload_or_recall_flag, num_of_co_taught)            

        flash('Upload scheduled teaching file successfully!', 'success')

        # rules #5: Combined grad/undergraduate classes
        calculate_combined_classes_and_update_scheduled_teaching(rows_dict)        

        for pair in user_id_and_academic_year_set:
            update_yearly_ending_balance(pair[0], pair[1])
        
        remove_upload_file(file)

        return redirect(url_for('courses.offerings'))


@courses.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    ucinetid_options = get_ucinetid()
    if request.method == 'POST':
        year = request.form['year']
        quarter = request.form['quarter']
        academic_year = get_academic_year(year, quarter)
        
        user_UCINetID_list = []        
        if request.form['multi_ucinetid'] != "":
            user_UCINetID_list = get_ucinetid_list(request.form['multi_ucinetid'])
        user_UCINetID_list.append(request.form['ucinetid'])
        
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

        flash('Add scheduled teaching data successfully!', 'success')

        # rules #5: Combined grad/undergraduate classes
        calculate_combined_classes_and_update_scheduled_teaching(rows_dict)        

        # for pair in user_id_and_academic_year_set:
        #     update_yearly_ending_balance(pair[0], pair[1])

        return redirect(url_for('courses.offerings'))
    return render_template('courses/create.html', ucinetid_options=ucinetid_options)

def is_valid_input(year, quarter, user_UCINetID_list, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag):
    # data examples:
    # year	
    # quarter: 1, 2, 3, 4
    # user_UCINetID_list: [XXX] or [XXX,XXX,XXX]
    # course_title_id: CS143B
    # course_sec: A, A1, 1, 15
    # num_of_enrollment: None or 0 or positvie integer	
    # offload_or_recall_flag: 1 or 0

    print('='*50)
    print(offload_or_recall_flag)

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
    
    err_msg = f"Incorrect data format on {col_name} column."
    flash(err_msg, 'error')
    return False

def check_existence_of_row(user_id, year, quarter, course_title_id, course_sec):
    db = get_db()
    row = db.execute(
        'SELECT * FROM scheduled_teaching '
        ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
        (user_id, year, quarter, course_title_id, course_sec)
    ).fetchone()

    return row

def insert_scheduled_teaching(user_id, year, quarter, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag, teaching_point_val):
    db = get_db()
    db.execute(
        'INSERT INTO scheduled_teaching (user_id, year, quarter, course_title_id, course_sec, enrollment, offload_or_recall_flag, teaching_point_val)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, year, quarter, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag, teaching_point_val)
    )
    db.commit()

def update_scheduled_teaching(num_of_enrollment, offload_or_recall_flag, teaching_point_val, user_id, year, quarter, course_title_id, course_sec):
    db = get_db()
    db.execute(
        'UPDATE scheduled_teaching SET enrollment = ?, offload_or_recall_flag = ?, teaching_point_val = ?'
        ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
        (num_of_enrollment, offload_or_recall_flag, teaching_point_val, user_id, year, quarter, course_title_id, course_sec)
    )
    db.commit()

def get_ucinetid():
    ucinetids = []
    db = get_db()
    rows = db.execute('SELECT DISTINCT user_ucinetid FROM users').fetchall()
    for row in rows:
        ucinetids.append(row["user_ucinetid"])
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
    combine_with = db.execute(
        'SELECT combine_with FROM courses'
        ' WHERE course_title_id = ?', (course_title_id,)
    ).fetchone()    
    return combine_with if combine_with is None else combine_with[0]

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
    row = db.execute(
        'SELECT user_id FROM users'
        ' WHERE user_ucinetid = ?', (user_UCINetID,)
    ).fetchone()
    if row != None:
        user_id = row[0]

    return user_id

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
    keys = rows_dict.keys()
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