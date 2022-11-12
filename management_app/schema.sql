DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS users_status;
DROP TABLE IF EXISTS professors_point_info;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS scheduled_teaching;
DROP TABLE IF EXISTS exceptions;
DROP TABLE IF EXISTS points_constant;
DROP TABLE IF EXISTS logs;

CREATE TABLE users (
  user_id INTEGER PRIMARY KEY, -- AUTOINCREMENT
  user_name TEXT NOT NULL,
  user_email TEXT UNIQUE NOT NULL,
  user_ucinetid TEXT UNIQUE NOT NULL,
  admin INTEGER NOT NULL -- SQLite does not have a separate Boolean storage class. Instead, Boolean values are stored as integers 0 (false) and 1 (true).
);

CREATE TABLE users_status (
  start_year INTEGER,
  user_id INTEGER,
  end_year INTEGER,  
  active_status INTEGER NOT NULL,
  user_role TEXT NOT NULL,
  PRIMARY KEY (start_year, user_id),
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE professors_point_info (
  user_id INTEGER,
  year INTEGER,
  previous_balance REAL,
  ending_balance REAL,
  credit_due REAL,
  grad_count REAL,
  grad_students TEXT,
  PRIMARY KEY (user_id, year),
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE courses (
  course_id INTEGER PRIMARY KEY,  -- AUTOINCREMENT
  course_title_id TEXT NOT NULL,
  course_title TEXT NOT NULL,
  units INTEGER NOT NULL,
  course_level TEXT
);

CREATE TABLE scheduled_teaching (
  user_id INTEGER,
  year INTEGER,
  quarter INTEGER,
  course_title_id TEXT,
  course_sec TEXT,
  enrollment INTEGER,
  offload_or_recall_flag INTEGER,
  teaching_point_val REAL,
  PRIMARY KEY (user_id, year, quarter, course_title_id, course_sec),
  FOREIGN KEY (user_id) REFERENCES users (user_id),
  FOREIGN KEY (course_title_id) REFERENCES courses (course_title_id)
);

CREATE TABLE exceptions (
  exception_id INTEGER PRIMARY KEY,  -- AUTOINCREMENT
  user_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  exception_category TEXT NOT NULL,
  message TEXT NOT NULL,
  points REAL,  
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE points_constant (
  rule_id INTEGER PRIMARY KEY, -- AUTOINCREMENT
  rule_name TEXT NOT NULL,
  points REAL
);

CREATE TABLE logs (
  log_id INTEGER PRIMARY KEY,  -- AUTOINCREMENT
  owner TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_id INTEGER,
  exception_id INTEGER,
  log_category TEXT,
  FOREIGN KEY (user_id) REFERENCES users (user_id),
  FOREIGN KEY (exception_id) REFERENCES exceptions (exception_id)
);
