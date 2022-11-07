import os
from flask import send_from_directory
from werkzeug.utils import secure_filename

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
            # TODO: Call logs API later
            print('Upload {} successfully'.format(filename))
    return

def remove_upload_file(file):
    filename = secure_filename(file.filename)
    save_location = get_upload_filepath(filename)
    os.remove(save_location)
    # TODO: Call logs API later
    print('Remove {} successfully'.format(filename))
    return