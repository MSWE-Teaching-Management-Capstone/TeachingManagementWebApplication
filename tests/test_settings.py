from management_app.db import get_db
from tests.conftest import captured_templates

def test_index(app, client, auth):
    auth.login(email='tpadmin@uci.edu')
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
    auth.login()
    response = client.post('/settings/admins/1')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user is not None and user['admin'] == 0

def test_remove_admin_delete(app, client, auth):
    auth.login()
    response = client.delete('/settings/admins/4')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        admin = db.execute('SELECT * FROM users WHERE user_id = 4').fetchone()
        assert admin is None

def test_remove_admin_last_admin(app, client, auth):
    auth.login()
    with app.app_context():
        db = get_db()
        db.execute('UPDATE users SET admin = 0 WHERE user_id = 4')
        db.commit()
        response = client.post('settings/admins/1')
        assert response.status_code == 400
        user = db.execute('SELECT * FROM users WHERE user_id = 1').fetchone()
        assert user is not None and user['admin'] == 1

def test_point_policy(app, client, auth):
    auth.login()
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

def test_edit_rule_point_value(app, client, auth):
    auth.login()
    response = client.post('/settings/point-policy/rules/1', data={'point-value': '2.5'})
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        rule = db.execute('SELECT * FROM rules WHERE rule_id = 1').fetchone()
        assert rule['value'] == 2.5
