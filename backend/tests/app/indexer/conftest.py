import pytest
import sqlite3

from app.indexer import db as db_module

@pytest.fixture
def conn(tmp_path):
    """
    Create a fresh SQLite DB for each test and initialize the schema.
    """
    # Override DB_PATH to a temp file for this test run
    db_module.DB_PATH = tmp_path / "test_index.db"
    conn = db_module.init_db()
    yield conn
    conn.close()