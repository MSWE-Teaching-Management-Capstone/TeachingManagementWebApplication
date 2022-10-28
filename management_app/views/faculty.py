from flask import (Blueprint, render_template, send_from_directory)

from management_app.views.auth import login_required

faculty = Blueprint('faculty', __name__, url_prefix='/faculty')

# TODO: Update login redirect to faculty page later
@faculty.route('/')
@login_required
def index():
  # TODO: Get data from database
  faculties = [
    { 'name': 'Professor Mark',  'email': 'mark@uci.edu', 'role': 'Tenured Faculty', 'required_point': 3.5, 'prev_balance': 0.1250, 'estimated_balance': 0.2500 },
    { 'name': 'Professor 2',  'email': 'mark1@uci.edu', 'role': 'Pre Tenured Faculty 1 st', 'required_point': 2.5, 'prev_balance': 0.1000, 'estimated_balance': 0.1250 },
    { 'name': 'Professor 3',  'email': 'mark3@uci.edu', 'role': 'PoT Tenured Faculty', 'required_point': 6.5, 'prev_balance': 1.4375, 'estimated_balance': 0.9375 }
  ]
  return render_template('faculty/index.html', faculties=faculties)

@faculty.route('/download_file/<filename>')
@login_required
def download_file(filename):
  path = 'static/data_templates'
  return send_from_directory(path, filename, as_attachment=True)
