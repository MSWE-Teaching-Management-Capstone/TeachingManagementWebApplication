from datetime import datetime
from flask import g
from management_app.db import get_db
#from management_app.views.course import insert_faculty_point_info, insert_faculty_status, insert_users


def test_download_template(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/data-templates/scheduled_teaching.xlsx')
    assert response.status_code == 200

def test_upload_user_file(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    file = 'tests/resource/scheduled_teaching.xlsx'
    data = {'courseTemplate': (open(file, 'rb'), file)}
    
    with app.app_context():
        db = get_db()
        response1 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
        client.post('/courses/upload', data=data)
        response2 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
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
        response1 = db.execute("SELECT * FROM scheduled_teaching").fetchall()
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': 3, 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})
        response2 = db.execute("SELECT * FROM scheduled_teaching").fetchall()
        assert len(response2) - len(response1) == 2

        # response4 = db.execute("SELECT * FROM scheduled_teaching WHERE course_title_id = 'CS12222A'").fetchall()
        # assert len(response4) == 2        
                
        response3 = db.execute("SELECT * FROM scheduled_teaching").fetchall()
        # create invalid offering
        client.post('/courses/create_offering', data={'year': 2023, 'quarter': "Fal", 'multi_ucinetid': "tpadmin", 'ucinetid': 'tprofessor', 'course_title_id': 'CS12222A', 'course_sec': 'A1', 'num_of_enrollment': "", 'offload_or_recall_flag': 0})
        assert len(response3) == len(response2)

def test_update_offering(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/courses/update/2/2023/3/CS12222A/A1')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        client.post('/courses/update/2/2023/3/CS234/A', data={'enrollment': 85})
        response = db.execute("SELECT enrollment FROM scheduled_teaching WHERE course_title_id = 'CS234'").fetchone()
        assert response['enrollment'] == 85

def test_delete_offering(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')

    with app.app_context():
        db = get_db()
        response1 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
        client.get('/courses/delete/2/2023/3/CS234/A')
        response2 = db.execute('SELECT * FROM scheduled_teaching').fetchall()
        assert len(response1) - len(response2) == 1