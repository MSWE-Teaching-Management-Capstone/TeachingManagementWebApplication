# TODO Add more test cases in the future and verify the values from database
def test_request_exception_logs(client, auth):
    auth.login()
    response = client.get('/logs/exception')
    assert response.status_code == 200

def test_request_general_logs(client, auth):
    auth.login()
    response = client.get('/logs/general')
    assert response.status_code == 200
