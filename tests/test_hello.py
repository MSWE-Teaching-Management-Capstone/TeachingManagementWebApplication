# We will use module `pytest` and `unittest` for the unit testing

def plus_one(x):
    return x + 1


def test_plus_one():
    num = 3
    assert plus_one(num) == 4


def test_plus_two():
    num = 3
    assert plus_one(num) == 5  # this will fail
