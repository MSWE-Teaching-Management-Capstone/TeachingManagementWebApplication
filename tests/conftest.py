import os
import tempfile
import pytest
from contextlib import contextmanager
from flask import template_rendered

from management_app import create_app
from management_app.db import get_db
from management_app.__init__ import init_rules, init_courses
from management_app.models import Users, FacultyStatus, FacultyPointInfo, Courses, ScheduledTeaching, Exceptions, Rules, Logs, db

# with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
#     _data_sql = f.read().decode('utf8')

@pytest.fixture(scope='module')
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        # init_db()

        # init_rules()
        # init_courses()
        
        # db.executescript(_data_sql)
        stmt = db.insert(Users).values([
            {'user_name': 'Test Professor Admin', 'user_email': 'tpadmin@uci.edu', 'user_ucinetid': 'tpadmin', 'admin': 1},
            {'user_name': 'Test Professor', 'user_email': 'tprofessor@uci.edu', 'user_ucinetid': 'tprofessor', 'admin': 0},
            {'user_name': 'Test Deactivated Professor', 'user_email': 'tdprof@uci.edu', 'user_ucinetid': 'tdprof', 'admin': 0},
            {'user_name': 'Test Staff', 'user_email': 'tstaff@ics.uci.edu', 'user_ucinetid': 'tstaff', 'admin': 1},
        ])
        try:
            db.session.execute(stmt)
            db.session.commit()
        except:
            pass

        stmt = db.insert(FacultyStatus).values([
            {'user_id': 1, 'start_year': 2020, 'end_year': None, 'active_status': 1, 'role': 'tenured pot'},
            {'user_id': 2, 'start_year': 2022, 'end_year': None, 'active_status': 1, 'role': 'assistant professor (2nd+ year)'},
            {'user_id': 3, 'start_year': 2020, 'end_year': 2021, 'active_status': 0, 'role': 'tenured research professor'},
        ])
        try:
            db.session.execute(stmt)
            db.session.commit()
        except:
            pass

        stmt = db.insert(FacultyPointInfo).values([
            {'user_id': 1, 'year': 2022, 'previous_balance': 2, 'ending_balance': 1.5, 'credit_due': 6.5, 'grad_count': 0, 'grad_students': None},
            {'user_id': 2, 'year': 2022, 'previous_balance': 0.125, 'ending_balance': -0.625, 'credit_due': 2.5, 'grad_count': 2, 'grad_students': 'Grad Student 1,Grad Student 2'},
        ])
        try:
            db.session.execute(stmt)
            db.session.commit()
        except:
            pass

        stmt = db.insert(ScheduledTeaching).values([
            {'user_id': 1, 'year': 2022, 'quarter': 1, 'course_title_id': 'ICS51', 'course_sec': 'A', 'enrollment': 250, 'offload_or_recall_flag': 0, 'teaching_point_val': 1.5},
            {'user_id': 1, 'year': 2022, 'quarter': 1, 'course_title_id': 'ICS193', 'course_sec': 'A', 'enrollment': 10, 'offload_or_recall_flag': 0, 'teaching_point_val': 0.25},
            {'user_id': 1, 'year': 2023, 'quarter': 2, 'course_title_id': 'ICS53', 'course_sec': 'A', 'enrollment': 150, 'offload_or_recall_flag': 0, 'teaching_point_val': 1},
            {'user_id': 1, 'year': 2023, 'quarter': 2, 'course_title_id': 'ICS193', 'course_sec': 'A', 'enrollment': 11, 'offload_or_recall_flag': 0, 'teaching_point_val': 0.25},
            {'user_id': 1, 'year': 2023, 'quarter': 3, 'course_title_id': 'ICS53', 'course_sec': 'A', 'enrollment': 150, 'offload_or_recall_flag': 0, 'teaching_point_val': 1},
            {'user_id': 1, 'year': 2023, 'quarter': 3, 'course_title_id': 'ICS193', 'course_sec': 'A', 'enrollment': 12, 'offload_or_recall_flag': 0, 'teaching_point_val': 0},
            {'user_id': 2, 'year': 2022, 'quarter': 1, 'course_title_id': 'ICS80', 'course_sec': 'A', 'enrollment': 50, 'offload_or_recall_flag': 0, 'teaching_point_val': 0.25},
            {'user_id': 2, 'year': 2023, 'quarter': 3, 'course_title_id': 'CS234', 'course_sec': 'A', 'enrollment': 100, 'offload_or_recall_flag': 0, 'teaching_point_val': 1.25},
        ])
        try:
            db.session.execute(stmt)
            db.session.commit()
        except:
            pass

        try:
            db.session.add(Exceptions(user_id=1, year=2022, exception_category='other', message='VC of Undergraduate Studies - 2 points', points=2))
            db.session.commit()
        except:
            pass

        try:
            db.session.add(Logs(owner='Test Professor Admin', user_id=1, exception_id=1, log_category='exception'))
            db.session.commit()
        except:
            pass

        try:
            db.session.add(Courses(course_id=9999, course_title_id='CS12222A', course_title='INTRODUCTION TO DATA MANAGEMENT', units=4, course_level='Undergrad', combine_with=None))
            db.session.commit()
        except:
            pass

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, **kwargs):
        with self._client.session_transaction() as session:
            session['google_id'] = 'google_id'
            session['domain'] = 'uci.edu'
            for key in kwargs:
                session[key] = kwargs[key]

    def logout(self):
        return self._client.get('/auth/logout')

@pytest.fixture
def auth(client):
    return AuthActions(client)

@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)