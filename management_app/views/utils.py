import os
from flask import send_from_directory
from werkzeug.utils import secure_filename
import datetime as dt
from management_app.db import get_db
from management_app.models import Users, Logs

BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_FOLDER = 'static/upload_files'
DOWNLOAD_FOLDER = 'static/data_templates'
ALLOWED_EXTENSIONS = set(['xlsx', 'xls'])


def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_filepath(filename):
    return os.path.realpath(os.path.join(BASE_DIR, UPLOAD_FOLDER, filename))


def upload_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_location = get_upload_filepath(filename)
        if (save_location.startswith(BASE_DIR)):
            file.save(save_location)
            print('Upload {} successfully'.format(filename))
    return


def remove_upload_file(file):
    filename = secure_filename(file.filename)
    save_location = get_upload_filepath(filename)
    os.remove(save_location)
    print('Remove {} successfully'.format(filename))
    return

def get_exist_user(user_ucinetid):
    db = get_db()
    user = db.session.execute(db.select(Users).filter_by(user_ucinetid=user_ucinetid)).scalar_one()

    return user

def insert_log(owner: str, user_id: int = None, exception_id: int = None, log_category: str = None):
    db = get_db()
    log = Logs(owner=owner, user_id=user_id, exception_id=exception_id, log_category=log_category)
    db.session.add(log)
    db.session.commit()
    return

def convert_local_timezone(utc_timestamp):
    return utc_timestamp.replace(tzinfo=dt.timezone.utc).astimezone(tz=None).strftime('%m/%d/%Y %H:%M:%S')