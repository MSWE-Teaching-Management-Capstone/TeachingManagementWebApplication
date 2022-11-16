from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for
from flask import request
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import date

from management_app.views.auth import login_required
from management_app.db import get_db
from management_app.views.utils import download_file, upload_file, remove_upload_file, get_upload_filepath
from management_app.views.points import calculate_teaching_point_val



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
            y_start = rows[0]['year']
            y_end = y_start + 1
        
            # generate year options
            for row in rows:
                year = row['year']
                year_options.append(str(year) + '-' + str(year+1))

            # todays_date = date.today()  # creating the date object of today's date        
            # y_start, y_end = todays_date.year, todays_date.year + 1
            year_selected = request.args.get('year')  # 2020-2021 (including: 2020 Fall(1) - 2021 Winter(2) & Spring(3))
            if year_selected != None:
                y_start = year_selected.split('-')[0]
                y_end = year_selected.split('-')[1]

            courses = db.execute(
                'SELECT year, quarter, user_name, st.course_title_id, course_sec, enrollment'
                ' FROM scheduled_teaching st JOIN courses ON st.course_title_id = courses.course_title_id JOIN users ON st.user_id = users.user_id'
                ' WHERE (year = ? AND quarter = 1) OR (year = ? AND quarter = 2) OR (year = ? AND quarter = 3)', (y_start, y_end, y_end)
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

        #     db.execute(
        #         'INSERT INTO courses (course_title_id, course_title, units, course_level)'
        #         ' VALUES (?, ?, ?, ?)',
        #         (course_title_id, course_title, units, course_level)
        #     )
        #     db.commit()        


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
        for row in rows:
            year = row[0]
            quarter = row[1]
            if quarter in quarterDict.keys():
                quarter = quarterDict[quarter]
            user_UCINetID = row[2].strip()            

            # course_title_id column may be like "CS 143B" or "CS143B" -> all convert to "CS143B"
            course_title_id = row[3].strip().replace(' ', '')
            
            course_sec = row[4].strip()
            num_of_enrollment = row[5]
            offload_or_recall_flag = row[6]
            if offload_or_recall_flag is None:
                offload_or_recall_flag = 0
            
            
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
            
            # TODO:
            if num_of_enrollment is None:
                teaching_point_val = 1  # default value is 1 for each course
            else:
                teaching_point_val = calculate_teaching_point_val(course_title_id, num_of_enrollment, offload_or_recall_flag, year, quarter)

            # check existence
            row = db.execute(
                'SELECT * FROM scheduled_teaching '
                ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
                (user_id, year, quarter, course_title_id, course_sec)
            ).fetchone()
            if row is None:
                db.execute(
                    'INSERT INTO scheduled_teaching (user_id, year, quarter, course_title_id, course_sec, enrollment, offload_or_recall_flag, teaching_point_val)'
                    ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (user_id, year, quarter, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag, teaching_point_val)
                )
            else:
                db.execute(
                    'UPDATE scheduled_teaching SET enrollment = ?, offload_or_recall_flag = ?, teaching_point_val = ?'
                    ' WHERE user_id = ? AND year = ? AND quarter = ? AND course_title_id = ? AND course_sec = ?', 
                    (num_of_enrollment, offload_or_recall_flag, teaching_point_val, user_id, year, quarter, course_title_id, course_sec)
                )
            db.commit()


        # TODO: call "adjust_co_taught_course_pt": before checking if it's a co-taught course, 
        #   I need to insert all data in the scheduled_teaching beforhand  
        #   (rule: Points are divided equally between the instructors for a co-taught course.)

        # TODO: call calculate professor's point API (written by ying-ru): update_yearly_ending_balance(user_id, year, is_recursive) ??   (send academic year to ying-ru)
                    
        
        remove_upload_file(file)

        return redirect(url_for('courses.offerings'))