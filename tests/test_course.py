from management_app.db import get_db
from management_app.views.course import update_scheduled_teaching, calculate_combined_classes_and_update_scheduled_teaching
from management_app.models import *

# Avoid overriding the real template file, just test part of the download_template()
def test_download_template(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')

    with app.app_context():
        db = get_db()
        # db.execute("DELETE FROM scheduled_teaching")
        # db.session.execute(db.delete(ScheduledTeaching))
        # db.session.commit()

        response = client.get('/courses/data-templates/scheduled_teaching.xlsx')
        assert response.status_code == 200

def test_upload_user_file(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    file = 'tests/resource/scheduled_teaching.xlsx'
    data = {'courseTemplate': (open(file, 'rb'), file)}
    
    with app.app_context():
        db = get_db()
        # response1 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
        response1 = db.session.execute(db.select(ScheduledTeaching)).fetchall()

        client.post('/courses/upload', data=data)
        # response2 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
        response2 = db.session.execute(db.select(ScheduledTeaching)).fetchall()

        assert len(response2) - len(response1) == 2

def test_offerings(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/offerings')
    assert response.status_code == 200

def test_catalog(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/catalog')
    assert response.status_code == 200

def test_create_offering(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/create_offering')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        # response1 = db.execute("SELECT * FROM scheduled_teaching").fetchall()
        response1 = db.session.execute(db.select(ScheduledTeaching)).fetchall()

        client.post('/courses/create_offering', data={'year': 2023, 'quarter': 3, 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})        
        
        # response2 = db.execute("SELECT * FROM scheduled_teaching").fetchall()
        response2 = db.session.execute(db.select(ScheduledTeaching)).fetchall()

        assert len(response2) - len(response1) == 2     
                
        # create invalid offering
        # wrong "quarter"
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': "Fal", 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})        
        # wrong "ucinetid"
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': 3, 'multi_ucinetid': "", 'ucinetid': 'wrongUserID', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})
        # wrong "course_title_id"
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': 3, 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'wrongCourse', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})
        # wrong "year"
        client.post('/courses/create_offering', data={'year': 202, 'quarter': 3, 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})
        # wrong "course_sec"
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': 3, 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': '@', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})
        # wrong "num_of_enrollment"
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': 3, 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "ABC", 'offload_or_recall_flag': 0})
        # wrong "offload_or_recall_flag"
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': 3, 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 2})
        # response3 = db.execute("SELECT * FROM scheduled_teaching").fetchall()
        response3 = db.session.execute(db.select(ScheduledTeaching)).fetchall()

        assert len(response3) == len(response2)



def test_update_offering(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/update/2/2023/3/CS12222A/A1')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        client.post('/courses/update/2/2023/3/CS234/A', data={'enrollment': 85})
        # response = db.execute("SELECT enrollment FROM scheduled_teaching WHERE course_title_id = 'CS234'").fetchone()
        stmt = db.select(ScheduledTeaching.enrollment).where(ScheduledTeaching.course_title_id == 'CS234')
        response = db.session.execute(stmt).scalar()

        assert response == 85

def test_delete_offering(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')

    with app.app_context():
        db = get_db()
        # response1 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
        response1 = db.session.execute(db.select(ScheduledTeaching)).fetchall()

        client.get('/courses/delete/2/2023/3/CS234/A')

        # response2 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
        response2 = db.session.execute(db.select(ScheduledTeaching)).fetchall()

        assert len(response1) - len(response2) == 1



def test_add_course(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/catalog/add')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        client.post('/courses/catalog/add', data={'title-id': 'CS1234A', 'title': 'INTRODUCTION TO ML', 'level': 'Undergrad', 'units': 4, 'combine-with': ""})
        # response = db.execute("SELECT course_title_id FROM courses WHERE course_title = 'INTRODUCTION TO ML'").fetchone()
        response = db.session.execute(db.select(Courses.course_title_id).where(Courses.course_title == 'INTRODUCTION TO ML')).scalar_one()

        assert response == 'CS1234A'      
        
        # response1 = db.execute('SELECT COUNT(*) AS cnt FROM courses').fetchone()
        response1 = db.session.execute(db.select(db.func.count()).select_from(Courses)).scalar_one()


        # add invalid courses
        # check "Course Title ID is already taken"
        client.post('/courses/catalog/add', data={'title-id': 'CS12222A', 'title': 'INTRODUCTION TO ML', 'level': 'Undergrad', 'units': 4, 'combine-with': ""})

        # response2 = db.execute('SELECT COUNT(*) AS cnt FROM courses').fetchone()
        response2 = db.session.execute(db.select(db.func.count()).select_from(Courses)).scalar_one()
        
        assert response1 == response2


def test_edit_course(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/catalog/course/9999/edit')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        client.post('/courses/catalog/course/9999/edit', data={'title': 'INTRO TO ML', 'level': 'Undergrad', 'units': 2, 'combine-with': ""})
        # response = db.execute("SELECT course_title, units FROM courses WHERE course_id = 9999").fetchone()
        response = db.session.execute(db.select(Courses.course_title, Courses.units).where(Courses.course_id == 9999)).fetchone()

        
        assert response.course_title == 'INTRO TO ML'
        assert response.units == 2

        # response = db.execute("SELECT course_id FROM courses WHERE course_title_id = 'CS234'").fetchone()
        response = db.session.execute(db.select(Courses.course_id).where(Courses.course_title_id == 'CS234')).scalar_one()

        client.post(f"/courses/catalog/course/{response}/edit", data={'title': 'AN', 'level': 'Undergrad', 'units': 2, 'combine-with': ""})

        # response = db.execute(f"SELECT course_title, course_level, units FROM courses WHERE course_id = {response['course_id']}").fetchone()
        stmt = db.select(Courses.course_title, Courses.course_level, Courses.units).\
            where(Courses.course_id == response)
        response = db.session.execute(stmt).fetchone()
        
        assert response[0] == 'AN'
        assert response[1] == 'Undergrad'
        assert response[2] == 2


# def test_update_scheduled_teaching(auth, app):
#     auth.login(email='tpadmin@uci.edu', net_id='tpadmin')    

#     with app.app_context():
#         update_scheduled_teaching(888, 0, 6, 2, 2023, 3, 'CS234', 'A')
#         db = get_db()
#         # response = db.execute("SELECT enrollment FROM scheduled_teaching WHERE course_title_id = 'CS234'").fetchone()
#         stmt = db.select(ScheduledTeaching.enrollment).where(ScheduledTeaching.course_title_id == 'CS234')
#         response = db.session.execute(stmt).scalar()

#         assert response == 888

def test_calculate_combined_classes_and_update_scheduled_teaching(auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')    

    with app.app_context():
        rows_dict = {}
        rows_dict["ICS193"] = {'user_id': 1, 'year': 2023, 'quarter': 3, 'course_sec': 'A', 'num_of_enrollment': 1000, 'offload_or_recall_flag': 0, 'num_of_co_taught': 2, 'combine_with': "ICS80"}
        rows_dict["ICS80"] = {'user_id': 2, 'year': 2022, 'quarter': 1, 'course_sec': 'A', 'num_of_enrollment': 1500, 'offload_or_recall_flag': 0, 'num_of_co_taught': 2, 'combine_with': "ICS193"}
        calculate_combined_classes_and_update_scheduled_teaching(rows_dict)

        db = get_db() 
        # response = db.execute("SELECT teaching_point_val FROM scheduled_teaching WHERE course_title_id = 'ICS193'").fetchone()
        stmt = db.select(ScheduledTeaching.teaching_point_val).where(ScheduledTeaching.course_title_id == 'ICS193')
        response = db.session.execute(stmt).scalar()

        assert response == 0.25

        # response = db.execute("SELECT teaching_point_val FROM scheduled_teaching WHERE course_title_id = 'ICS80'").fetchone()
        stmt = db.select(ScheduledTeaching.teaching_point_val).where(ScheduledTeaching.course_title_id == 'ICS80')
        response = db.session.execute(stmt).scalar()

        assert response == 0.1875

        