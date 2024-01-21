from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String, nullable=False)
    user_email = db.Column(db.String, nullable=False, unique=True)
    user_ucinetid = db.Column(db.String, nullable=False, unique=True)
    admin = db.Column(db.Integer, nullable=False)

class FacultyStatus(db.Model):
    __tablename__ = 'faculty_status'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    start_year = db.Column(db.Integer, primary_key=True)
    end_year = db.Column(db.Integer)
    active_status = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String, nullable=False)

class FacultyPointInfo(db.Model):
    __tablename__ = 'faculty_point_info'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    previous_balance = db.Column(db.Float)
    ending_balance = db.Column(db.Float)
    credit_due = db.Column(db.Float)
    grad_count = db.Column(db.Float)
    grad_students = db.Column(db.String)

class Courses(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_title_id = db.Column(db.String, unique=True, nullable=False)
    course_title = db.Column(db.String, nullable=False)
    units = db.Column(db.Integer, nullable=False)
    course_level = db.Column(db.String)
    combine_with = db.Column(db.String)

class ScheduledTeaching(db.Model):
    __tablename__ = 'scheduled_teaching'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    quarter = db.Column(db.Integer, primary_key=True)
    course_title_id = db.Column(db.String, db.ForeignKey('courses.course_title_id'), primary_key=True)
    course_sec = db.Column(db.String, primary_key=True)
    enrollment = db.Column(db.Integer)
    offload_or_recall_flag = db.Column(db.Integer)
    teaching_point_val = db.Column(db.Float)

class Exceptions(db.Model):
    __tablename__ = 'exceptions'
    exception_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    exception_category = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    points = db.Column(db.Float)

class Rules(db.Model):
    __tablename__ = 'rules'
    rule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_name = db.Column(db.String, nullable=False)
    value = db.Column(db.Float)

class Logs(db.Model):
    __tablename__ = 'logs'
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner = db.Column(db.String, nullable=False)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    exception_id = db.Column(db.Integer, db.ForeignKey('exceptions.exception_id'))
    log_category = db.Column(db.String)