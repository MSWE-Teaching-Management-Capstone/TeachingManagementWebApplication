from management_app.db import get_db

def calculate_teaching_point_val(course_title_id, num_of_enrollment, offload_or_recall_flag, year, quarter):
    # TODO: check policy and mental model

    # rules: 
    # #1: if P course (e.g. "CS297P") -> if offload_or_recall_flag is 0 then get 1 point; if offload_or_recall_flag is 1 then get 0 point
    # #2: if num_of_enrollment < 8: get 0 pt
    # #3: if not P course -> give points according to the category (3 input: num_of_enrollment, units, course_level)
    
    # initial db:
    # Category 0: 1.5 points
    # Category 1: 1.25 points
    # Category 2: 1 point
    # Category 3: 0.75 points
    # Category 4: 0.25 points (max 0.5 points per year)

    db = get_db()
    rows = db.execute(
        'SELECT * FROM rules'
    ).fetchall()

    for row in rows:
        if row['rule_name'] == "Category 0":
            point_c0 = row['value']
        if row['rule_name'] == "Category 1":
            point_c1 = row['value']
        if row['rule_name'] == "Category 2":
            point_c2 = row['value']
        if row['rule_name'] == "Category 3":
            point_c3 = row['value']
        if row['rule_name'] == "Category 4":
            point_c4 = row['value']

    row = db.execute(
        'SELECT units, course_level FROM courses '
        ' WHERE course_title_id = ?', (course_title_id,)
    ).fetchone()
    
    units = row['units']
    course_level = row['course_level']    

    # rules #1
    if course_title_id[-1] == "P":
        if offload_or_recall_flag == 0 or offload_or_recall_flag is None:
            return point_c2
        # TODO: if previous_yearly_balance >= 0   (generate warning if this happens, don't stop this)
        return 0
    # rules #2
    elif num_of_enrollment < 8:
        return 0
    # rules #3
    elif units == 6:
        return point_c0
    elif (course_level == "Undergrad" and num_of_enrollment >= 200) or (course_level == "Grad" and num_of_enrollment >= 100):
        return point_c1
    elif (course_level == "Undergrad" and num_of_enrollment > 20 and num_of_enrollment <= 199) or (course_level == "Grad" and num_of_enrollment > 20 and num_of_enrollment <= 99):
        return point_c2
    elif (course_level == "Undergrad" and num_of_enrollment <= 20) or (course_level == "Grad" and num_of_enrollment <= 20):
        return point_c3
    elif course_level == "Undergrad" and units == 2:
        # 2020-2021 (including: 2020 Fall(1) - 2021 Winter(2) & Spring(3))
        if quarter == 1:
            y1 = year
            y2 = year+1
            y3 = year+1
        if quarter == 2 or quarter == 3:
            y1 = year-1
            y2 = year
            y3 = year

        sql_statement = f"SELECT COUNT(*) FROM scheduled_teaching WHERE ((year = {y1} AND quarter = 1) OR (year = {y2} AND quarter = 2) OR (year = {y3} AND quarter = 3)) AND teaching_point_val = {point_c4}"
        num_of_row = db.execute(sql_statement).fetchone()         
        
        if num_of_row[0] < 2:
            return point_c4
    return 0

def get_faculty_credit_due_by_role(user_role):
    required_point = 0
    if user_role == 'tenured research faculty':
        required_point = 3.5
    elif user_role == 'assistant professor (1st year)':
        required_point = 1
    elif user_role == 'assistant professor (2nd+ year)':
        required_point = 2.5
    elif user_role == 'tenured POT':
        required_point = 6.5
    elif user_role == 'assistant POT (1st year)':
        required_point = 5
    elif user_role == 'assistant POT (2nd+ year)':
        required_point = 5.5
    elif user_role == 'staff':
        required_point = 0
    return required_point

def get_yearly_teaching_points(user_id, year):
    # Note: year comes from professor_point_info table, it represents the start of an an academic year
    # This year should convert to the range of academic year
    # e.g., year 2020 should be 2020-2021 (including 2020 Fall(1) - 2021 Winter(2) & Spring(3))
    year_range_start = year
    year_range_end = year + 1
    yearly_teaching_points = 0
    db = get_db()
    rows = db.execute(
        'SELECT st.teaching_point_val'
        ' FROM scheduled_teaching AS st'
        ' JOIN users ON users.user_id = st.user_id'
        ' WHERE st.user_id = ? AND ((st.year = ? AND st.quarter = 1) OR (st.year = ? AND st.quarter = 2) OR (st.year = ? AND st.quarter = 3))',
        (user_id, year_range_start, year_range_end, year_range_end)
    ).fetchall()

    for row in rows:
        yearly_teaching_points += row['teaching_point_val']
    return yearly_teaching_points

def get_yearly_grad_mentoring_points(grad_count, grad_students):
    # TODO/Note: point per grad student and extra points are temporarily hard-coded
    grad_points = grad_count * 0.125

    total_grad_students = 0
    if len(grad_students) > 0:
        total_grad_students = len(grad_students.split(','))

    if grad_points >= 0.5:
        grad_points = 0.5 # max = 0.5 for grad_count credits
    if total_grad_students >= 6:
        grad_points += 0.5
    return grad_points

def get_yearly_exception_points(user_id, year):
    exception_points = 0
    db = get_db()
    rows = db.execute(
        'SELECT points FROM exceptions WHERE user_id = ? AND year = ?', (user_id, year)
    )
    for row in rows:
        exception_points += row['points']
    return exception_points

def get_yearly_ending_balance(user_id, year, grad_count, grad_students, previous_balance, credit_due):
    # TODO: confirm previous_balance rule
    # if previous_balance > 2:
    #     previous_balance = 2

    teaching_points = get_yearly_teaching_points(user_id, year)
    grad_points = get_yearly_grad_mentoring_points(grad_count, grad_students)
    exception_points = get_yearly_exception_points(user_id, year)
    return previous_balance + teaching_points + grad_points + exception_points - credit_due

def update_yearly_ending_balance():
    # TODO: this function will be re-called in course.py after enrollment get updated after week 2
    # TODO: If past enrollment changes -> update previous balance & ending balance recursively
    return