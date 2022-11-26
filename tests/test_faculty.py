def test_request_get_faculty_response(client, auth):
  auth.login()
  response = client.get('/faculty/')
  assert response.status_code == 200

def test_download_correct_file(client, auth):
  auth.login()
  response = client.get('/faculty/data-templates/users.xlsx')
  assert response.status_code == 200

def test_download_incorrect_file(client, auth):
  auth.login()
  response = client.get('/faculty/data-templates/123.xlsx')
  assert response.status_code == 404
