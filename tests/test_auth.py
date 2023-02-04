from flask import session, g

def test_login(client, auth):
  auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
  with client:
        client.get('/auth/login')
        assert session['domain'] == 'uci.edu'
        assert session['email'] == 'tpadmin@uci.edu'
        assert session['net_id'] == 'tpadmin'

def test_logout(client, auth):
    auth.login()
    with client:
        auth.logout()
        assert 'google_id' not in session
        assert 'domain' not in session

def test_logged_in_admin_user(client, auth):
  auth.login(email='tpadmin@uci.edu', net_id='tpadmin')
  with client:
        client.get('/faculty/members')
        assert g.user['user_email'] == 'tpadmin@uci.edu'
        assert g.user['user_name'] == 'Test Professor Admin'
        assert g.user['user_ucinetid'] == 'tpadmin'
        assert g.user['admin'] == 1

def test_logged_in_non_admin_user(client, auth):
  auth.login(email='tprofessor@uci.edu', net_id='tprofessor')
  with client:
        client.get('/auth/login')
        assert g.user['user_email'] == 'tprofessor@uci.edu'
        assert g.user['admin'] == 0