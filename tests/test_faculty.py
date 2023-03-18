from datetime import datetime
from flask import g
from management_app.db import get_db
from management_app.views.faculty import insert_faculty_point_info, insert_faculty_status, insert_users

def test_download_user_file(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/faculty/data-templates/users.xlsx')
    assert response.status_code == 200

# To avoid overriding the real template file, only test part of the download_faculty_point_file
def test_download_faculty_point_file(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM faculty_point_info")
        response = client.get('/faculty/data-templates/professors_point_info.xlsx')
        assert response.status_code == 200

def test_download_incorrect_file(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/faculty/data-templates/123.xlsx')
    assert response.status_code == 404

def test_get_all_members(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
        assert g.user['admin'] == 1
        assert client.get('/faculty/members').status_code == 200

def test_get_all_faculty_points(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/points').status_code == 200
    assert client.get('/faculty/points?year=2022-2023').status_code == 200

def test_empty_year_options(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM faculty_point_info")
        assert client.get('/faculty/points').status_code == 200

def test_get_faculty_dashboard(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/points/1').status_code == 200

def test_create_member(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/create-member').status_code == 200
    client.post('/faculty/create-member', data={'name': 'New Created', 'ucinetid': 'newuser', 'email': 'newuser@uci.edu', 'role': 'assistant POT (1st year)', 'status': 1})

    with app.app_context():
        db = get_db()
        cur_year = datetime.now().year

        user = db.execute("SELECT * FROM users WHERE user_ucinetid = 'newuser'").fetchone()
        assert user['user_name'] == 'New Created'

        faculty = db.execute("SELECT * FROM faculty_status WHERE user_id = 5 AND start_year = ?", (cur_year,)).fetchone()
        assert faculty['role'] == 'assistant POT (1st year)'
        assert faculty['active_status'] == 1

        log = db.execute("SELECT * FROM logs WHERE owner = 'Admin: Test Professor Admin'").fetchone()
        assert log['log_category'] == 'Add new faculty member'

def test_invalid_input_for_create_member(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/create-member').status_code == 200

    # name is required
    client.post('/faculty/create-member', data={'name': '', 'ucinetid': 'newuser', 'email': 'newuser@uci.edu', 'role': 'assistant POT (1st year)', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE user_ucinetid = 'newuser'").fetchone()
        assert user == None

    # ucinetid is required
    client.post('/faculty/create-member', data={'name': 'New User', 'ucinetid': '', 'email': 'newuser@uci.edu', 'role': 'assistant POT (1st year)', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE user_ucinetid = 'newuser'").fetchone()
        assert user == None

    # email is required
    client.post('/faculty/create-member', data={'name': 'New User', 'ucinetid': 'newuser', 'email': '', 'role': 'assistant POT (1st year)', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE user_ucinetid = 'newuser'").fetchone()
        assert user == None

    # role is required
    client.post('/faculty/create-member', data={'name': 'New User', 'ucinetid': 'newuser', 'email': 'newuser@uci.edu', 'role': '', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE user_ucinetid = 'newuser'").fetchone()
        assert user == None

def test_create_duplicated_member(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    client.get('/faculty/create-member')
    client.post('/faculty/create-member', data={'name': 'New Created', 'ucinetid': 'newuser', 'email': 'newuser@uci.edu', 'role': 'assistant POT (1st year)', 'status': 1})
    response = client.post('/faculty/create-member', data={'name': 'New Created', 'ucinetid': 'newuser', 'email': 'newuser@uci.edu', 'role': 'assistant POT (1st year)', 'status': 1})
    assert response.status_code != 200
    with app.app_context():
        db = get_db()
        users = db.execute("SELECT * FROM users").fetchall()
        assert len(users) == 5

def test_update_member(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update').status_code == 200
    client.post('/faculty/1/update', data={'name': 'Updated', 'ucinetid': 'tpadmin', 'email': 'tpadmin@uci.edu', 'role': 'tenured pot', 'status': 1})

    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user['user_name'] == 'Updated'

def test_invalid_update_member(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update').status_code == 200

    # name is required
    client.post('/faculty/1/update', data={'name': '', 'ucinetid': 'tpadmin', 'email': 'tpadmin@uci.edu', 'role': 'tenured pot', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user['user_name'] == 'Test Professor Admin'

    # ucinetid is required
    client.post('/faculty/1/update', data={'name': 'Updated', 'ucinetid': '', 'email': 'tpadmin@uci.edu', 'role': 'tenured pot', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user['user_name'] == 'Test Professor Admin'

    # email is required
    client.post('/faculty/1/update', data={'name': 'Updated', 'ucinetid': 'tpadmin', 'email': '', 'role': 'tenured pot', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user['user_name'] == 'Test Professor Admin'

    # role is required
    client.post('/faculty/1/update', data={'name': 'Updated', 'ucinetid': 'tpadmin', 'email': 'tpadmin@uci.edu', 'role': '', 'status': 1})
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user['user_name'] == 'Test Professor Admin'

def test_update_member_status(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update').status_code == 200
    client.post('/faculty/1/update', data={'name': 'Test Professor Admin', 'ucinetid': 'tpadmin', 'email': 'tpadmin@uci.edu', 'role': 'tenured pot', 'status': 0})

    with app.app_context():
        db = get_db()
        cur_year = datetime.now().year

        prev_status = db.execute('SELECT * FROM faculty_status WHERE user_id = 1 AND start_year = 2020').fetchone()
        assert prev_status['active_status'] == 1
        assert prev_status['end_year'] == cur_year

        new_status = db.execute('SELECT * FROM faculty_status WHERE user_id = 1 AND start_year = ?', (cur_year,)).fetchone()
        assert new_status['active_status'] == 0
        assert new_status['end_year'] == None

def test_update_member_role(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update').status_code == 200
    client.post('/faculty/1/update', data={'name': 'Test Professor Admin', 'ucinetid': 'tpadmin', 'email': 'tpadmin@uci.edu', 'role': 'tenured pot change', 'status': 1})

    with app.app_context():
        db = get_db()
        cur_year = datetime.now().year

        prev_status = db.execute('SELECT * FROM faculty_status WHERE user_id = 1 AND start_year = 2020').fetchone()
        assert prev_status['role'] == 'tenured pot'
        assert prev_status['end_year'] == cur_year

        new_status = db.execute('SELECT * FROM faculty_status WHERE user_id = 1 AND start_year = ?', (cur_year,)).fetchone()
        assert new_status['role'] == 'tenured pot change'
        assert new_status['end_year'] == None

        log = db.execute("SELECT * FROM logs WHERE owner = 'Admin: Test Professor Admin'").fetchone()
        assert log['log_category'] == 'Update faculty member information'

def test_update_points_by_grad(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update/2022').status_code == 200
    client.post('/faculty/1/update/2022', data={
        'grad_count':'2.0',
        'grad_students': 'Student 1, Student 2',
        'exception_point': '',
        'exception_category': 'None',
        'exception_message': ''
    })

    with app.app_context():
        db = get_db()
        points = db.execute('SELECT * FROM faculty_point_info WHERE user_id = 1 AND year = 2022').fetchone()
        assert points['grad_count'] == 2.0
        assert points['grad_students'] == 'Student 1, Student 2'
        assert points['ending_balance'] == 1.75
        log = db.execute("SELECT * FROM logs WHERE owner = 'Admin: Test Professor Admin'").fetchone()
        assert log['log_category'] == 'Update faculty member points'

def test_update_points_by_execptions_add(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update/2022').status_code == 200
    client.post('/faculty/1/update/2022', data={
        'grad_count': '2.0',
        'grad_students': 'Student 1, Student 2',
        'exception_adjust': 'exception_add',
        'exception_point': '1',
        'exception_category': 'buyout',
        'exception_message': 'test_message'
    })
    with app.app_context():
        db = get_db()
        exceptions = db.execute('SELECT SUM(points) AS p FROM exceptions WHERE user_id = 1 AND year = 2022').fetchone()
        assert exceptions['p'] == 3.0
        points = db.execute('SELECT * FROM faculty_point_info WHERE user_id = 1 AND year = 2022').fetchone()
        assert points['ending_balance'] == 2.75
        log = db.execute("SELECT * FROM logs WHERE owner = 'Admin: Test Professor Admin'").fetchone()
        assert log['log_category'] == 'buyout_test_message'

def test_update_points_by_execptions_substract(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update/2022').status_code == 200
    client.post('/faculty/1/update/2022', data={
        'grad_count': '2.0',
        'grad_students': 'Student 1, Student 2',
        'exception_adjust': 'exception_subtract',
        'exception_point': '1',
        'exception_category': 'buyout',
        'exception_message': ''
    })
    with app.app_context():
        db = get_db()
        exceptions = db.execute('SELECT SUM(points) AS p FROM exceptions WHERE user_id = 1 AND year = 2022').fetchone()
        assert exceptions['p'] == 1.0

def test_invalid_update_points(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update/2022').status_code == 200

    # with exception_adjust, need to fill exception_point 
    client.post('/faculty/1/update/2022', data={
        'grad_count': '2.0',
        'grad_students': '',
        'exception_adjust': 'exception_add',
        'exception_point': '',
        'exception_category': 'buyout',
        'exception_message': ''
    })
    with app.app_context():
        db = get_db()
        exceptions = db.execute('SELECT SUM(points) AS p FROM exceptions WHERE user_id = 1 AND year = 2022').fetchone()
        assert exceptions['p'] == 2

    # with exception_adjust, need to fill exception_category 
    client.post('/faculty/1/update/2022', data={
        'grad_count': '2.0',
        'grad_students': '',
        'exception_adjust': 'exception_add',
        'exception_point': '1.0',
        'exception_category': 'None',
        'exception_message': ''
    })
    with app.app_context():
        db = get_db()
        exceptions = db.execute('SELECT SUM(points) AS p FROM exceptions WHERE user_id = 1 AND year = 2022').fetchone()
        assert exceptions['p'] == 2

def test_regular_faculty_login_dashboard(client, auth):
    auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
    with client:
        client.get('/auth/login')
        assert g.user['admin'] == 0
        assert client.get('/faculty', follow_redirects=True).status_code == 200

def test_update_faculty_status(client, auth, app):
    auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
    with client:
        client.get('/auth/login')
        insert_faculty_point_info(1, 2023, 1.5, 0, "", 2.5)
    with app.app_context():
        db = get_db()
        res = db.execute('SELECT * FROM faculty_point_info WHERE user_id = 1 AND year = 2023').fetchone()
        assert res['year'] == 2023
        assert res['previous_balance'] == 1.5

def test_insert_faculty_status(client, auth, app):
    auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
    with client:
        client.get('/auth/login')
        insert_faculty_status('tdprof', 2023, 'tenured research professor', 1)
    with app.app_context():
        db = get_db()
        res1 = db.execute('SELECT * FROM faculty_status WHERE user_id = 3 AND start_year = 2023').fetchone()
        assert res1['active_status'] == 1
        assert res1['start_year'] == 2023

        res2 = db.execute('SELECT * FROM faculty_status WHERE user_id = 3 AND start_year = 2020').fetchone()
        assert res2['active_status'] == 0
        assert res2['start_year'] == 2020
        assert res2['end_year'] == 2021

def test_insert_users(client, auth, app):
    auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
    with client:
        client.get('/auth/login')
        insert_users('New User', 'new@uci.edu', 'new1', 0)
    with app.app_context():
        db = get_db()
        res = db.execute('SELECT * FROM users WHERE user_ucinetid = "new1"').fetchone()
        assert res['user_id'] == 5
        assert res['user_name'] == 'New User'
        assert res['admin'] == 0

def test_upload_user(client, auth, app):
    auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
    file = 'tests/resource/2023 Users Data.xlsx'
    data = { 'facultyTemplate': (open(file, 'rb'), file) }
    client.post('/faculty/upload/addUsers', data=data)
    with app.app_context():
        db = get_db()
        res = db.execute('SELECT * FROM users').fetchall()
        assert len(res) == 6

def test_upload_faculty_point(client, auth, app):
    auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
    file = 'tests/resource/2023 Professor Point Data.xlsx'
    data = { 'facultyTemplate': (open(file, 'rb'), file) }
    client.post('/faculty/upload/addProfessors', data=data)
    with app.app_context():
        db = get_db()
        res = db.execute('SELECT * FROM faculty_point_info WHERE year = 2023').fetchall()
        assert len(res) == 2