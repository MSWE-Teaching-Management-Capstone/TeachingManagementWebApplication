import pytest

from management_app.db import get_db
from management_app.views.points import calculate_teaching_point_val, get_faculty_roles_credit_due, calculate_yearly_ending_balance

@pytest.mark.parametrize(('course_title_id', 'num_of_enrollment', 'offload_or_recall_flag', 'year', 'quarter', 'user_id', 'num_of_co_taught', 'expected_value'), (
    ('ICS51', 250, 0, 2022, 1, 1, 1, 1.5),
    ('ICS193', 7, 0, 2022, 1, 1, 1, 0),
    ('ICS53', 150, 0, 2022, 2, 1, 1, 1),
    ('ICS193', 6, 0, 2022, 2, 1, 1, 0),
    ('ICS53', 150, 0, 2022, 3, 1, 1, 1),
    ('ICS193', 5, 0, 2022, 3, 1, 1, 0),
    ('ICS80', 50, 0, 2022, 1, 2, 1, 0.25),
    ('CS234', 100, 0, 2022, 3, 2, 1, 1.25)
))
def test_calculate_teaching_point_val(app, course_title_id, num_of_enrollment, offload_or_recall_flag, year, quarter, user_id, num_of_co_taught, expected_value):
    with app.app_context():
        assert calculate_teaching_point_val(course_title_id, num_of_enrollment, offload_or_recall_flag, year, quarter, user_id, num_of_co_taught) == expected_value

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
