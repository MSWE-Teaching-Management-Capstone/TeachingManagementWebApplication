import os
import pytest
from flask import session

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
      session['google_id'] = 'TEST_ID_NUM'

# TODO Add more test cases in the future and verify the values from database
def test_request_exception_logs(client):
    mock_login(client)
    response = client.get('/logs/exception')
    assert response.status_code == 200

def test_request_general_logs(client):
    mock_login(client)
    response = client.get('/logs/general')
    assert response.status_code == 200
