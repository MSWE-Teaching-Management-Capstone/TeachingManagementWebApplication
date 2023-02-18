from datetime import datetime
from management_app.views.utils import insert_log
from management_app.views.logs import convert_description

def test_request_exception_logs(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/logs/exception')
    assert response.status_code == 200

def test_request_general_logs(client, auth):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    response = client.get('/logs/general')
    assert response.status_code == 200

def test_exceptions_with_date(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    client.get('/logs/exception')
    with app.app_context():
        insert_log('Admin', 1, None, 'Add new faculty member')
        year = datetime.now().year + 1
        end_date = str(year) + '-01-01 00:00:00'
        data = {
            'start-date': '2020-01-01 00:00:00',
            'end-date': end_date
        }
        response = client.post('/logs/exception-with-dates', data=data)
        assert response.status_code == 200

def test_convert_description(client, auth, app):
    auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
    client.get('/logs/exception')
    with app.app_context():
        assert convert_description('Exception', 1) == 'Exception(Test Professor Admin)'
        assert convert_description('Exception', None) == 'Exception'