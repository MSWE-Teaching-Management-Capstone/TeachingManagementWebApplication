from management_app.db import get_db
from management_app.views.points import calculate_teaching_point_val, get_faculty_roles_credit_due, calculate_yearly_ending_balance

def test_calculate_teaching_point_val(app):
    with app.app_context():
        db = get_db()
        res = db.execute('SELECT user_id, year, quarter, course_title_id, enrollment, offload_or_recall_flag, teaching_point_val FROM scheduled_teaching').fetchall()
        for offering in res:
            assert calculate_teaching_point_val(
                offering['course_title_id'],
                offering['enrollment'],
                offering['offload_or_recall_flag'],
                offering['year'],
                offering['quarter'],
                offering['user_id'],
                1
            ) == offering['teaching_point_val']

def test_get_faculty_roles_credit_due(app):
    expected = {
        'tenured research faculty': 3.5,
        'faculty up for tenure': 3.5,
        'assistant professor (1st year)': 1,
        'assistant professor (2nd+ year)': 2.5,
        'tenured pot': 6.5,
        'pot up for tenure': 6.5,
        'assistant pot (1st year)': 5,
        'assistant pot (2nd+ year)': 5.5
    }
    with app.app_context():
        assert get_faculty_roles_credit_due() == expected

def test_calculate_yearly_ending_balance(app):
    with app.app_context():
        db = get_db()
        res = db.execute('SELECT user_id, year, previous_balance, ending_balance, credit_due, grad_count FROM faculty_point_info').fetchall()
        for point_info in res:
            ending_balance = calculate_yearly_ending_balance(
                point_info['user_id'],
                point_info['year'],
                point_info['grad_count'],
                point_info['previous_balance'],
                point_info['credit_due']
            )
            assert ending_balance == point_info['ending_balance'], f"Test failed for - user_id: {point_info['user_id']}, year: {point_info['year']}"
