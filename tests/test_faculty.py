import os
import pytest

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

def mock_login_session(client):
  # Enable login auth
  with client.session_transaction() as session:
      session['google_id'] = ''

def test_request_get_faculty_response(client):
  mock_login_session(client)
  response = client.get('/faculty/')
  assert response.status_code == 200

def test_download_correct_file(client):
  mock_login_session(client)
  response = client.get('/faculty/data-templates/users_template.xlsx')
  assert response.status_code == 200

def test_download_incorrect_file(client):
  mock_login_session(client)
  response = client.get('/faculty/data-templates/123.xlsx')
  assert response.status_code == 404
