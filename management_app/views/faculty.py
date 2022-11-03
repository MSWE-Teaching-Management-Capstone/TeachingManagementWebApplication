from flask import Flask, Blueprint, send_from_directory, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from management_app.views.auth import login_required
from management_app.views.utils import download_file, upload_file, remove_upload_file

faculty = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty.route('/')
@login_required
def index():
    # TODO: Get data from database
    faculties = [
        {'name': 'Professor Mark', 'email': 'mark@uci.edu', 'role': 'Tenured Faculty', 'required_point': 3.5,
         'prev_balance': 0.1250, 'estimated_balance': 0.2500},
        {'name': 'Professor 2', 'email': 'mark1@uci.edu', 'role': 'Pre Tenured Faculty 1 st', 'required_point': 2.5,
         'prev_balance': 0.1000, 'estimated_balance': 0.1250},
        {'name': 'Professor 3', 'email': 'mark3@uci.edu', 'role': 'PoT Tenured Faculty', 'required_point': 6.5,
         'prev_balance': 1.4375, 'estimated_balance': 0.9375}
    ]
    return render_template('faculty/index.html', faculties=faculties)


@faculty.route('/data-templates/<filename>')
@login_required
def download_template(filename):
    return download_file(filename)


@faculty.route('/upload', methods=['POST'])
@login_required
def upload_user_template():
    if (request.method == 'POST'):
        file = request.files['facultyTemplate']
        filename = secure_filename(file.filename)
        upload_file(file)

        # TODO: process spreadsheet and store in database

        remove_upload_file(file)

        return redirect(url_for('faculty.index'))