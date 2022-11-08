from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for
from flask import request
from werkzeug.utils import secure_filename
import pandas as pd

from management_app.views.auth import login_required
from management_app.db import get_db
from management_app.views.utils import download_file, upload_file, remove_upload_file, get_upload_filepath

courses = Blueprint('courses', __name__, url_prefix='/courses')

@courses.route('/offerings')
@login_required
def offerings():
    db = get_db()
    # TODO: should filter by the year selected from the frontend
    courses = db.execute(
            'SELECT year, quarter, user_name, course_title_id, course_sec, enrollment'
            ' FROM scheduled_teaching st JOIN courses ON st.course_id = courses.course_id JOIN users ON st.user_id = users.user_id'
            ' WHERE year = 2022'#, (,)
    ).fetchall()

    return render_template('courses/offerings.html', courses=courses)


# @courses.route('/catalog')



@courses.route('/data-templates/<filename>')
@login_required
def download_template(filename):

    # TODO: do template Prefill: 
    # Schedule_teaching table prepopulate: year, quarter, usename, ucinetid, 
    # course_type： Lec, course_sec: A (each prodessor 3 rows: fall, winter, spring)

    return download_file(filename)

@courses.route('/upload', methods=['POST'])
@login_required
def upload_user_file():
    if (request.method == 'POST'):
        file = request.files['courseTemplate']        
        upload_file(file)

        
        df = pd.read_excel(get_upload_filepath('scheduled_teaching111.xlsx'), sheet_name=1)
        
        # TODO: 
        # notice: template is different from the table
        
        
        db = get_db()
        # store to database
        df.to_sql(name='scheduled_teaching', con=db, if_exists='append', index=False)         
        
        # TODO: should filter by the year selected from the frontend
        courses = db.execute(
                'SELECT year, quarter, user_name, course_title_id, course_sec, enrollment'
                ' FROM scheduled_teaching st JOIN courses ON st.course_id = courses.course_id JOIN users ON st.user_id = users.user_id'
                ' WHERE year = 2022'#, (,)
        ).fetchall()

        # remove_upload_file(file)

        # notice the url before and after file uploaded
        # return redirect(url_for('faculty.index'))
        return render_template('courses/offerings.html', courses=courses)