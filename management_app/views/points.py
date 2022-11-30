from management_app.db import get_db

def calculate_teaching_point_val(course_title_id, num_of_enrollment, offload_or_recall_flag, year, quarter, user_id, num_of_co_taught):
    # rules: 
    # #1: if P course (e.g. "CS297P") -> if offload_or_recall_flag is 0 then get 1 point; if offload_or_recall_flag is 1 then get 0 point
    # #2: if num_of_enrollment < 8: get 0 pt
    # #3: if not P course -> give points according to the category 0-4 (3 input: num_of_enrollment, units, course_level)
    # #4: if not P course -> Points are divided equally between the instructors for a co-taught course.
    # #5: if not P course -> Combined grad/undergraduate classes that are offered simultaneously will be given credit according to the class which would have yielded the most points (typically the undergraduate one) plus .25 points. (a 2 credit course can not be combined with a 4 unit course)

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
    # Cat 0 applies to 6 unit courses
    elif units == 6:
        return point_c0 / num_of_co_taught
    # Cat 4 applies to 2 unit courses
    # a two unit undergraduate course can also be a co-taught course
    # elif course_level == "Undergrad" and units == 2:
    elif units == 2:
        # 2020-2021 (including: 2020 Fall(1) - 2021 Winter(2) & Spring(3))
        earned_pnt = point_c4 / num_of_co_taught

        res = None
        if quarter == 1:
            return earned_pnt
        elif quarter == 2:
            res = db.execute("""
                SELECT SUM(st.teaching_point_val) AS total
                FROM scheduled_teaching AS st JOIN courses AS c ON st.course_title_id = c.course_title_id
                WHERE user_id = ? AND c.units = ? AND year = ? AND quarter = ?
            """, (user_id, 2, year - 1, 1)).fetchone()
        else:
            res = db.execute("""
                SELECT SUM(st.teaching_point_val) AS total
                FROM scheduled_teaching AS st JOIN courses AS c ON st.course_title_id = c.course_title_id
                WHERE user_id = ? AND c.units = ? AND ((year = ? AND quarter = ?) OR (year = ? AND quarter = ?))
            """, (user_id, 2, year - 1, 1, year, 2)).fetchone()

        # a faculty member can only have a max of 0.5 points per year for category 4
        total = res['total']
        if total is not None:
            sum_of_Cat4_pnt = res['total']
            if sum_of_Cat4_pnt >= 0.5:
                return 0
            elif sum_of_Cat4_pnt + earned_pnt > 0.5:
                return 0.5 - sum_of_Cat4_pnt
        
        return earned_pnt
    # Cat 1-3 applies to 4 unit courses
    elif units == 4:
        if (course_level == "Undergrad" and num_of_enrollment >= 200) or (course_level == "Grad" and num_of_enrollment >= 100):
            return point_c1 / num_of_co_taught
        elif (course_level == "Undergrad" and num_of_enrollment > 20 and num_of_enrollment <= 199) or (course_level == "Grad" and num_of_enrollment > 20 and num_of_enrollment <= 99):
            return point_c2 / num_of_co_taught      
        else:  # (course_level == "Undergrad" and num_of_enrollment <= 20) or (course_level == "Grad" and num_of_enrollment <= 20)
            return point_c3 / num_of_co_taught
    else:
        # e.g. 1 unit course
        return 0  

def get_faculty_roles_credit_due():
    # Get credit_due by faculty_role from the database
    # { Role1: point1, Role2: point2... }
    faculty_roles = {}
    db = get_db()
    rows = db.execute('SELECT * FROM rules').fetchall()
    for row in rows:
        if row is not None:
            if 'role' in row['rule_name'].lower():
                key = row['rule_name'].split('-')[1].lower()
                faculty_roles[key] = row['value']
    return faculty_roles

def get_yearly_teaching_points(user_id, start_year):
    # Note: year comes from faculty_point_info table, it represents the start of an an academic year
    # This year should convert to the range of academic year
    # e.g., year 2020 should be 2020-2021 (including 2020 Fall(1) - 2021 Winter(2) & Spring(3))
    end_year = start_year + 1
    db = get_db()
    res = db.execute("""
        SELECT SUM(teaching_point_val) AS total
        FROM scheduled_teaching
        WHERE user_id = ? AND ((year = ? AND quarter = 1) OR (year = ? AND quarter = 2) OR (year = ? AND quarter = 3))
    """, (user_id, start_year, end_year, end_year)).fetchone()
    return 0 if res['total'] is None else res['total']

def get_grad_mentoring_points(grad_count):
    # TODO/Note: point per grad student and extra points are temporarily hard-coded
    grad_points = grad_count * 0.125
    if grad_points >= 0.5:
        grad_points = 0.5
    if grad_count >= 6:
        grad_points += 0.5 # max = 0.5 for grad_count credits
    return grad_points

def get_yearly_exception_points(user_id, year):
    exception_points = 0
    db = get_db()
    rows = db.execute(
        'SELECT points FROM exceptions WHERE user_id = ? AND year = ?', (user_id, year)
    ).fetchall()
    for row in rows:
        exception_points += row['points']
    return exception_points

def calculate_yearly_ending_balance(user_id, year, grad_count, previous_balance, credit_due):
    teaching_points = get_yearly_teaching_points(user_id, year)
    grad_points = get_grad_mentoring_points(grad_count)
    exception_points = get_yearly_exception_points(user_id, year)
    total = previous_balance + teaching_points + grad_points + exception_points - credit_due
    total = round(total, 4)
    return total

def get_latest_academic_year():
    db = get_db()
    res = db.execute(
        'SELECT DISTINCT year FROM faculty_point_info ORDER BY year DESC LIMIT 1'
    ).fetchone()
    return res['year'] if res is not None else None

def update_yearly_ending_balance(user_id, year):
    # Note that year parameter represents the start of an an academic year
    # e.g., year 2020 should be 2020-2021 (including 2020 Fall(1) - 2021 Winter(2) & Spring(3))
    db = get_db()
    latest_year = get_latest_academic_year()
    # no point record, no need to update
    if latest_year is None:
        return

    diff = 0
    for y in range(year, latest_year+1):
        row = db.execute(
            'SELECT * FROM faculty_point_info WHERE user_id = ? AND year = ?',
            (user_id, y)
        ).fetchone()

        # Use stored credit_due in faculty_point_info table to re-calculate
        # instead of rule_name stored in rule table due to rules of point policy may change
        if row is not None:
            grad_count = row['grad_count']
            credit_due = row['credit_due']
            previous_balance = row['previous_balance']
            ending_balance = row['ending_balance']

            if y == year:
                new_ending_balance = calculate_yearly_ending_balance(user_id, y, grad_count, previous_balance, credit_due)
                diff = new_ending_balance - ending_balance
                ending_balance += diff
            else:
                previous_balance += diff
                ending_balance += diff

            previous_balance = round(previous_balance, 4)
            ending_balance = round(ending_balance, 4)
            db.execute(
                'UPDATE faculty_point_info SET previous_balance = ?, ending_balance = ?'
                ' WHERE user_id = ? AND year = ?',
                (previous_balance, ending_balance, user_id, y)
            )
            db.commit()
    return