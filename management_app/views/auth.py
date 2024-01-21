import os
import pathlib
import functools
import requests
import google.auth.transport.requests
from werkzeug.exceptions import abort
from flask import flash, session, redirect, request, render_template, Blueprint, url_for, g
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol

from management_app.views.utils import get_exist_user

auth = Blueprint('auth', __name__, url_prefix='/auth')

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

client_secrets_file = os.path.join(pathlib.Path(__file__).parent.parent, "client_secret.json")

# Create the session flow
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/auth/login_callback"
)

# Wrapper for login session checkup
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "google_id" not in session:
            return redirect(url_for('auth.index'))
        else:
            return view(**kwargs)

    return wrapped_view

@auth.route("/")
def index():
    return render_template("login.html")

@auth.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.index'))

@auth.route("/login_callback")
def login_callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=os.getenv("GOOGLE_CLIENT_ID")
    )

    session["google_id"] = id_info.get("sub")
    session["domain"] = id_info.get("hd", "-1")
    session['net_id'] = id_info.get('email').split(sep='@')[0]

    # verify the domain of email comes from UCI
    if session["domain"] != os.getenv("DOMAIN", ""):
        session.clear()
        flash("Alert: You have to log in with your UCI email (e.g. abc123@uci.edu)")
        return redirect(url_for('auth.index'))

    # verify if the user has the permission to access the system
    if not get_exist_user(session['net_id']):
        session.clear()
        flash("Alert: You do not have the permission to access the system.")
        return redirect(url_for('auth.index'))

    return redirect(url_for('auth.redirect_to_homepage'))

@auth.route("/redirect_to_homepage")
@login_required
def redirect_to_homepage():
    if g.user.admin:
        return redirect('/faculty/points')
    else:
        return redirect('/faculty')

@auth.before_app_request
def load_logged_in_user():
    user_net_id = session.get('net_id')

    if user_net_id is None:
        g.user = None
    elif get_exist_user(user_net_id):
        g.user = get_exist_user(user_net_id)
    return