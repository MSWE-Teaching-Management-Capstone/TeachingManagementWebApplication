INSERT INTO users (user_name, user_email, user_ucinetid, admin)
VALUES
  ('Test Professor Admin', 'tpadmin@uci.edu', 'tpadmin', 1),
  ('Test Professor', 'tprofessor@uci.edu', 'tprofessor', 0),
  ('Test Deactivated Professor', 'tdprof@uci.edu', 'tdprof', 0),
  ('Test Staff', 'tstaff@ics.uci.edu', 'tstaff', 1);

INSERT INTO faculty_status (user_id, start_year, end_year, active_status, role)
VALUES
  (1, 2020, null, 1, 'tenured pot'),
  (2, 2022, null, 1, 'assistant professor (2nd+ year)'),
  (3, 2020, 2021, 0, 'tenured research professor');

INSERT INTO faculty_point_info (user_id, year, previous_balance, ending_balance, credit_due, grad_count, grad_students)
VALUES
  (1, 2022, 2, 1.5, 6.5, 0, null),
  (2, 2022, 0.125, -0.625, 2.5, 2, 'Grad Student 1,Grad Student 2');

INSERT INTO scheduled_teaching (user_id, year, quarter, course_title_id, course_sec, enrollment, offload_or_recall_flag, teaching_point_val)
VALUES
  (1, 2022, 1, 'ICS51', 'A', 250, 0, 1.5),
  (1, 2022, 1, 'ICS193', 'A', 10, 0, 0.25),
  (1, 2023, 2, 'ICS53', 'A', 150, 0, 1),
  (1, 2023, 2, 'ICS193', 'A', 11, 0, 0.25),
  (1, 2023, 3, 'ICS53', 'A', 150, 0, 1),
  (1, 2023, 3, 'ICS193', 'A', 12, 0, 0),
  (2, 2022, 1, 'ICS80', 'A', 50, 0, 0.25),
  (2, 2023, 3, 'CS234', 'A', 100, 0, 1.25);

INSERT INTO exceptions (user_id, year, exception_category, message, points)
VALUES
  (1, 2022, 'other', 'VC of Undergraduate Studies - 2 points', 2);

INSERT INTO logs (owner, user_id, exception_id, log_category)
VALUES
  ('Test Professor Admin', 1, 1, 'exception');

INSERT INTO courses (course_id, course_title_id, course_title, units, course_level, combine_with)
VALUES
  (9999, 'CS12222A', 'INTRODUCTION TO DATA MANAGEMENT', 4, 'Undergrad', null);