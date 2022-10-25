import os
from flask import Flask, redirect
from dotenv import load_dotenv

from . import db
from .views.auth import auth
from .views.faculty import faculty

load_dotenv('.flaskenv')
load_dotenv('.env')

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'management_app.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(faculty) # temporarily render faculty views under url_prefix='/faculty'

    @app.route('/')
    def redirect_to_auth_login():
        return redirect('/auth')

    return app