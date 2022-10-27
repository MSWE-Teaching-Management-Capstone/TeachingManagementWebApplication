from flask import (Blueprint, render_template)

from management_app.views.auth import login_required

faculty = Blueprint('faculty', __name__, url_prefix='/faculty')

# TODO: Update login redirect to faculty page later
@faculty.route('/')
@login_required
def index():
  faculties = [
    { 'name': 'Professor Mark',  'email': 'mark@uci.edu', 'role': 'Tenured Faculty', 'required_point': 3.5, 'prev_balance': 0.1250, 'estimated_balance': 0.2500 },
    { 'name': 'Professor 2',  'email': 'mark1@uci.edu', 'role': 'Pre Tenured Faculty 1 st', 'required_point': 2.5, 'prev_balance': 0.1000, 'estimated_balance': 0.1250 },
    { 'name': 'Professor 3',  'email': 'mark3@uci.edu', 'role': 'PoT Tenured Faculty', 'required_point': 6.5, 'prev_balance': 1.4375, 'estimated_balance': 0.9375 }
  ]
  return render_template('faculty/index.html', faculties=faculties)
