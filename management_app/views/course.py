from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for

from management_app.views.auth import login_required
from management_app.db import get_db

courses = Blueprint('courses', __name__, url_prefix='/courses')

@courses.route('/')
@login_required
def index():
    db = get_db()
    # TODO: should filter by the year selected from the frontend
    courses = db.execute(
            'SELECT year, quarter, user_name, course_title_id, course_sec, enrollment'
            ' FROM scheduled_teaching st JOIN courses ON st.course_id = courses.course_id JOIN users ON st.user_id = users.user_id'
            ' WHERE year = 2022'#, (,)
    ).fetchall()

    return render_template('courses/index.html', courses=courses)

