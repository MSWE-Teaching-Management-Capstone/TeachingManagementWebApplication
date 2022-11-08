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

courses = Blueprint('courses', __name__, url_prefix='/courses')

@courses.route('/offerings', methods=['GET'])
@login_required
def offerings():
    if request.method == 'GET':
        # generate year options
        todays_date = date.today()  # creating the date object of today's date
        years = list(range(2019, todays_date.year+1))  # [2019, 2020, 2021, 2022]
        year_options = [str(y) + '-' + str(y+1) for y in years]  # ['2019-2020', '2020-2021', '2021-2022', '2022-2023']

        db = get_db() 
        y_start, y_end = todays_date.year, todays_date.year+1
        year_selected = request.args.get('year')  # 2020-2021 (including: 2020 Fall - 2021 Winter & Spring)
        if year_selected != None:
            y_start = year_selected.split('-')[0]
            y_end = year_selected.split('-')[1]

        courses = db.execute(
                'SELECT year, quarter, user_name, course_title_id, course_sec, enrollment'
                ' FROM scheduled_teaching st JOIN courses ON st.course_id = courses.course_id JOIN users ON st.user_id = users.user_id'
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
        #     teaching_point_val = -1

        #     db.execute(
        #         'INSERT INTO courses (course_title_id, course_title, units, teaching_point_val, course_level)'
        #         ' VALUES (?, ?, ?, ?, ?)',
        #         (course_title_id, course_title, units, teaching_point_val, course_level)
        #     )
        #     db.commit()

        # TODO: haven't calculate "teaching_point_val" column

        return render_template('courses/catalog.html')


@courses.route('/data-templates/<filename>', methods=['GET'])
@login_required
def download_template(filename):

    # TODO: do template Prefill: 
    # Schedule_teaching table prepopulate: year, quarter, usename, ucinetid, 
    # course_type： Lec, course_sec: A (each prodessor 3 rows: fall, winter, spring)

    if request.method == 'GET':
        return download_file(filename)

@courses.route('/upload', methods=['POST'])
@login_required
def upload_user_file():
    if (request.method == 'POST'):
        file = request.files['courseTemplate'] 
        upload_file(file)        
        quarterDict = {"Fall": 1, "Winter": 2, "Spring": 3, "Summer": 4}
        db = get_db()

        df = pd.read_excel(get_upload_filepath(file.filename), sheet_name=1)
        rows = df.values.tolist()   
        for row in rows:
            year = row[0]
            quarter = row[1]
            if quarter in quarterDict.keys():
                quarter = quarterDict[quarter]
            user_UCINetID = row[2].strip()
            course_code = row[3]

            # course_title_id column may be like "CS 143B" or "CS143B" -> all convert to "CS143B"
            course_title_id = row[4].strip().replace(' ', '')

            course_type = row[5].strip()
            # course_type = "Lec"
            course_sec = row[6].strip()
            # course_sec = 'A'
            num_of_enrollment = row[7]
            offload_or_recall_flag = row[8]
            
            user_id = None
            # use "user_UCINetID" in s_t file to get user_id in users table
            # take ucinetid: alfchen, emj to test
            row = db.execute(
                'SELECT user_id FROM users'
                ' WHERE user_ucinetid = ?', (user_UCINetID,)
            ).fetchone()
            if row != None:
                user_id = row[0]
            
            course_id = None
            # use "course_title_id" in s_t file to get course_id in courses table
            row = db.execute(
                'SELECT course_id FROM courses'
                ' WHERE course_title_id = ?', (course_title_id,)
            ).fetchone()
            if row != None:
                course_id = row[0]

            db.execute(
                'INSERT INTO scheduled_teaching (user_id, course_code, year, quarter, course_id, course_type, course_sec, enrollment, offload_or_recall_flag)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (user_id, course_code, year, quarter, course_id, course_type, course_sec, num_of_enrollment, offload_or_recall_flag)
            )
            db.commit()      
        
        remove_upload_file(file)
        
        # TODO: call recaculation API (written by Ying-ru) (files may or may not contain numbers of enrollment)        

        return redirect(url_for('courses.offerings'))