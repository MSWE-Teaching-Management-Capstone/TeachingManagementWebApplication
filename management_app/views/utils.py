import os
from flask import send_from_directory
from werkzeug.utils import secure_filename
from management_app.db import get_db

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


# Duplicate here to avoid circular import error
def get_exist_user(user_ucinetid):
    db = get_db()
    return db.execute(
        'SELECT * FROM users WHERE user_ucinetid = ?', (user_ucinetid,)
    ).fetchone()


def check_admin(net_id):
    db = get_db()

    res = db.execute(
        'SELECT admin FROM users WHERE user_ucinetid = ?', (net_id,)
    ).fetchone()[0]

    return True if res == 1 else False


def insert_log(owner: str, user_id: int = None, exception_id: int = None, log_category: str = None):
    db = get_db()
    db.execute("INSERT INTO logs (owner, created, user_id, exception_id, log_category)"
               " VALUES(?, CURRENT_TIMESTAMP, ?, ?, ?)",
               (owner, user_id, exception_id, log_category))
    db.commit()
    return
