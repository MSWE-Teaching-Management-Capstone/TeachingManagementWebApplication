import sqlite3

import pytest
from management_app.db import get_db
import subprocess


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()

    # with pytest.raises(sqlite3.ProgrammingError) as e:
    #     db.execute('SELECT 1')

    # assert 'closed' in str(e.value)

def test_init_db_command(runner, monkeypatch):
    # class Recorder(object):
    #     called = False

    # def fake_init_db():
    #     Recorder.called = True

    # monkeypatch.setattr('management_app.db.init_db', fake_init_db)
    # result = runner.invoke(args=['init-db'])
    # assert 'Initialized' in result.output
    # assert Recorder.called

    # Execute the terminal command 'flask init-db'
    result = subprocess.run(['flask', 'init-db'], capture_output=True, text=True)
    # Check if the command succeeded (exit code 0) and contains expected output
    assert result.returncode == 0
    assert "Initialized the database." in result.stdout