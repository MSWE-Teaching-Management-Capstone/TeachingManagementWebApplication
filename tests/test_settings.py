from tests.conftest import captured_templates
from management_app.db import get_db
from flask import g

def test_index(app, client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
    with captured_templates(app) as templates:
        response = client.get('/settings/admins')
        assert response.status_code == 200
        assert len(templates) == 1

        template, context = templates[0]
        assert template.name == 'settings/index.html'

        assert len(context['admins']) == 2
        assert context['admins'][0]['user_name'] == 'Test Professor Admin'
        assert context['admins'][1]['user_name'] == 'Test Staff'

        assert context['current_user']['user_name'] == 'Test Professor Admin'

        assert len(context['users']) == 1
        assert context['users'][0]['user_name'] == 'Test Professor'

def test_remove_admin_post(app, client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
        response = client.post('/settings/admins/1')
        assert response.status_code == 200
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user is not None and user['admin'] == 0

def test_remove_admin_delete(app, client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
        assert g.user['admin'] == 1

        response = client.delete('/settings/admins/4')
        assert response.status_code == 200
    with app.app_context():
        db = get_db()
        admin = db.execute('SELECT * FROM users WHERE user_id = 4').fetchone()
        assert admin is None

def test_remove_admin_last_admin(app, client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
    with app.app_context():
        db = get_db()
        db.execute('UPDATE users SET admin = 0 WHERE user_id = 4')
        db.commit()
        response = client.post('settings/admins/1')
        assert response.status_code == 400
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user is not None and user['admin'] == 1

def test_point_policy(app, client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
    with captured_templates(app) as templates:
        response = client.get('/settings/point-policy')
        assert response.status_code == 200
        assert len(templates) == 1

        template, context = templates[0]
        assert template.name == 'settings/point-policy.html'

        with app.app_context():
            db = get_db()
            rules = db.execute('SELECT * FROM rules').fetchall()
            assert context['rules'] == rules

def test_edit_rule_point_value_role(app, client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
    # test using "Role-assistant professor (2nd+ year)""
    response = client.post('/settings/point-policy/rules/4', data={'point-value': '3.5'})
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        rule = db.execute('SELECT * FROM rules WHERE rule_id = 4').fetchone()
        assert rule['value'] == 3.5
        
        # once a role constant changes the ending balance of faculty with the affected role should be updated as well
        prof = db.execute('SELECT ending_balance, credit_due FROM faculty_point_info WHERE user_id = 2 and year = 2022').fetchone()
        assert prof['ending_balance'] == -1.625
        assert prof['credit_due'] == 3.5

def test_edit_rule_point_value_category(app, client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    with client:
        client.get('/auth/login')
    # test using category 2 (only ICS 53 classes should be affected)
    response = client.post('/settings/point-policy/rules/11', data={'point-value': '1.5'})
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        rule = db.execute('SELECT * FROM rules WHERE rule_id = 11').fetchone()
        assert rule['value'] == 1.5

        # once a category constant changes the teaching point val of the course offerings should be updated
        offerings = db.execute("SELECT teaching_point_val FROM scheduled_teaching WHERE course_title_id = 'ICS53'").fetchall()
        assert len(offerings) == 2
        assert offerings[0]['teaching_point_val'] == 1.5
        assert offerings[1]['teaching_point_val'] == 1.5

        # the affected faculty's ending balance should be updated as well
        prof = db.execute('SELECT ending_balance FROM faculty_point_info WHERE user_id = 1 and year = 2022').fetchone()
        assert prof['ending_balance'] == 2.5