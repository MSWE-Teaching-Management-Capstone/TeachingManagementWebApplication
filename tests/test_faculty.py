from datetime import datetime
from flask import g
from management_app.db import get_db

def test_download_correct_file(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/faculty/data-templates/users.xlsx')
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

def test_update_member(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update').status_code == 200
    client.post('/faculty/1/update', data={'name': 'Updated', 'ucinetid': 'tpadmin', 'email': 'tpadmin@uci.edu', 'role': 'tenured pot', 'status': 1})

    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user['user_name'] == 'Updated'

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

def test_update_points_by_execptions(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    assert client.get('/faculty/1/update/2022').status_code == 200
    client.post('/faculty/1/update/2022', data={
        'grad_count': '2.0',
        'grad_students': 'Student 1, Student 2',
        'exception_adjust': 'exception_add',
        'exception_point': '1',
        'exception_category': 'buyout',
        'exception_message': ''
    })

    with app.app_context():
        db = get_db()
        exceptions = db.execute('SELECT SUM(points) AS p FROM exceptions WHERE user_id = 1 AND year = 2022').fetchone()
        assert exceptions['p'] == 3.0
        points = db.execute('SELECT * FROM faculty_point_info WHERE user_id = 1 AND year = 2022').fetchone()
        assert points['ending_balance'] == 2.75
        log = db.execute("SELECT * FROM logs WHERE owner = 'Admin: Test Professor Admin'").fetchone()
        assert log['log_category'] == 'buyout'

def test_regular_faculty_login_dashboard(client, auth):
    auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
    with client:
        client.get('/auth/login')
        assert g.user['admin'] == 0
        assert client.get('/faculty', follow_redirects=True).status_code == 200
