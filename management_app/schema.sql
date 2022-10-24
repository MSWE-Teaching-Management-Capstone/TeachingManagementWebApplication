DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS professors_point_info;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS scheduled_teaching;
DROP TABLE IF EXISTS exceptions;
DROP TABLE IF EXISTS points_constant;
DROP TABLE IF EXISTS logs;


CREATE TABLE users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_name TEXT NOT NULL,
  user_email TEXT UNIQUE NOT NULL,
  user_ucinetid TEXT UNIQUE NOT NULL,
  user_role TEXT NOT NULL,
  admin INTEGER NOT NULL -- SQLite does not have a separate Boolean storage class. Instead, Boolean values are stored as integers 0 (false) and 1 (true).
);

CREATE TABLE professors_point_info (
  user_id INTEGER PRIMARY KEY,
  year INTEGER PRIMARY KEY,
  previous_balance REAL,
  ending_balance REAL,
  credit_due REAL,
  grad_count REAL,
  grad_students TEXT,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE courses (
  course_id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_title_id TEXT NOT NULL,
  course_title TEXT NOT NULL,
  units INTEGER NOT NULL,
  teaching_point_val REAL,
  course_level TEXT
);

CREATE TABLE scheduled_teaching (
  user_id INTEGER PRIMARY KEY,
  course_id INTEGER PRIMARY KEY,
  year INTEGER PRIMARY KEY,
  quarter INTEGER PRIMARY KEY,
  course_code INTEGER NOT NULL,
  course_type TEXT NOT NULL,
  course_sec TEXT NOT NULL,
  enrollment INTEGER,
  FOREIGN KEY (user_id) REFERENCES users (user_id),
  FOREIGN KEY (course_id) REFERENCES courses (course_id)
);

CREATE TABLE exceptions (
  exception_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER PRIMARY KEY,
  year INTEGER PRIMARY KEY,
  reason TEXT NOT NULL,
  points REAL,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE points_constant (
  rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_name TEXT NOT NULL,
  points REAL
);

CREATE TABLE logs (
  transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_id INTEGER,
  message TEXT,
  exception_category TEXT,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);



