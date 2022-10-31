import pytest
from flask import template_rendered

from management_app import create_app

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def mock_login(client):
  # Enable login auth
  with client.session_transaction() as session:
      session['google_id'] = ''

def captured_templates(app, recorded, **extra):
    def record(sender, template, context):
        recorded.append((template, context))
    return template_rendered.connected_to(record, app)

def test_get_admins_template(app, client):
    mock_login(client)
    templates = []
    with captured_templates(app, templates):
        response = client.get('/settings/admins')
        assert response.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'settings/admins.html'
        # TODO use data from test database for expected context values
        assert len(context['admins']) == 3
        assert context['current_user'] == context['admins'][0]
        assert len(context['users']) == 3

def test_get_point_policy_template(app, client):
    mock_login(client)
    templates = []
    with captured_templates(app, templates):
        response = client.get('/settings/point-policy')
        assert response.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'settings/point-policy.html'
        # TODO use data from test database for expected context values
        assert len(context['rules']) == 3
