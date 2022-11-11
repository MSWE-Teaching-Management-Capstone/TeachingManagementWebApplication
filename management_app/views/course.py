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
        db = get_db()
        
        # generate year options
        year_options = []        
        rows = db.execute(
            'SELECT DISTINCT year FROM scheduled_teaching ORDER BY year DESC'
        ).fetchall()
        y_start = rows[0]['year']
        y_end = y_start + 1
        for row in rows:
            year = row['year']
            year_options.append(str(year) + '-' + str(year+1))

        # todays_date = date.today()  # creating the date object of today's date        
        # y_start, y_end = todays_date.year, todays_date.year + 1
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


        # TODO: should give the default teaching_point_val = 1 for each course
        


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

            # course_title_id column may be like "CS 143B" or "CS143B" -> all convert to "CS143B"
            course_title_id = row[3].strip().replace(' ', '')
            
            course_sec = row[4].strip()
            # course_sec = 'A'
            # TODO: if no num_of_enrollment -> show “-” or “?” in the frontend
            num_of_enrollment = row[5]
            offload_or_recall_flag = row[6]
            
            user_id = None
            # use "user_UCINetID" in s_t file to get user_id in users table
            # take ucinetid: alfchen, emj to test
            row = db.execute(
                'SELECT user_id FROM users'
                ' WHERE user_ucinetid = ?', (user_UCINetID,)
            ).fetchone()
            if row != None:
                user_id = row[0]           
            

            # TODO: if not exist-> add; if exist-> update


            db.execute(
                'INSERT INTO scheduled_teaching (user_id, year, quarter, course_title_id, course_sec, enrollment, offload_or_recall_flag)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, year, quarter, course_title_id, course_sec, num_of_enrollment, offload_or_recall_flag)
            )
            db.commit()      
        
        remove_upload_file(file)
        
        # TODO: if enrollment got updated -> update related courses' "teaching_point_val" column
        # TODO: haven't calculate "teaching_point_val" column
            # calculate teaching_point_val according to category (3 input) (write this function in the point.py and call it here)
                # calculate rules: 
                    # * category 0: 4+2 credit ? Ans: 6 units
                    # * category 2: onload ?
                        # note: "CS297P" -> this is P course
                        #     if P course -> if offload_or_recall_flag is 0 then get 1 point; if offload_or_recall_flag is 1 then get 0 point
                        #     if not P course -> give points according to category

        # TODO: after upload enrollment -> call calculate teaching_point_val -> call calculate professor's point (ying-ru)  (write it in the point.py)
        # TODO: call recaculation API (written by Ying-ru) (files may or may not contain numbers of enrollment)        

        return redirect(url_for('courses.offerings'))