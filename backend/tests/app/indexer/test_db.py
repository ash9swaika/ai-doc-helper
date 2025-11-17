# tests/app/indexer/test_db.py

import pytest
import sqlite3
from pathlib import Path
import app.indexer.db as db

def test_init_db_creates_tables(tmp_path: Path):
    """Test that init_db creates the necessary tables in a new database."""
    # point DB_PATH to a temp file
    db.DB_PATH = tmp_path / "test_index.db"

    conn = db.init_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = {row[0] for row in cur.fetchall()}

    # docs_fts is a virtual table; sqlite_master type='table' vs 'virtual'
    cur.execute("SELECT name, type FROM sqlite_master")
    entries = {(row[0], row[1]) for row in cur.fetchall()}

    assert "sources" in table_names
    assert "documents" in table_names
    assert "chunks" in table_names

    # ensure FTS table exists (type can be 'table' or 'virtual table' depending on sqlite version)
    assert any(name == "docs_fts" for name, _type in entries)


def test_sources_unique_package_version(tmp_path: Path):
    """Test that the sources table enforces unique (package, version) constraint."""
    db.DB_PATH = tmp_path / "test_index.db"
    conn = db.init_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO sources(package, version, base_url) VALUES(?,?,?)",
        ("pandas", "2.2.2", "https://example.com/docs1"),
    )
    conn.commit()

    # Attempt to insert duplicate (package, version)
    # Second insert with same (package, version) should violate uniqueness
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute(
            "INSERT INTO sources(package, version, base_url) VALUES (?, ?, ?)",
            ("pandas", "2.2.2", "https://example.com/docs2"),
        )
        conn.commit()


def test_documents_unique_source_url(tmp_path: Path):
    """Test that the documents table enforces unique (source_id, url) constraint."""
    db.DB_PATH = tmp_path / "test_index.db"
    conn = db.init_db()
    cur = conn.cursor()

    # Insert a source first
    cur.execute(
        "INSERT INTO sources(package, version, base_url) VALUES(?,?,?)",
        ("numpy", "1.24.0", "https://example.com/numpy"),
    )
    source_id = cur.lastrowid
    conn.commit()

    cur.execute(
        "INSERT INTO documents(source_id, url, title, text) VALUES(?,?,?,?)",
        (source_id, "https://example.com/numpy/doc1", "Doc 1", "Some text"),
    )
    conn.commit()

    # Attempt to insert duplicate (source_id, url)
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute(
            "INSERT INTO documents(source_id, url, title, text) VALUES(?,?,?,?)",
            (source_id, "https://example.com/numpy/doc1", "Doc 1 Duplicate", "Some other text"),
        )
        conn.commit()

def test_documents_cascade_on_delete(tmp_path: Path):
    """Test that deleting a source cascades to delete its documents."""
    db.DB_PATH = tmp_path / "test_index.db"
    conn = db.init_db()
    cur = conn.cursor()

    # Insert a source
    cur.execute(
        "INSERT INTO sources(package, version, base_url) VALUES(?,?,?)",
        ("scipy", "1.10.0", "https://example.com/scipy"),
    )
    source_id = cur.lastrowid
    conn.commit()

    # Insert a documents for that source
    cur.execute(
        "INSERT INTO documents(source_id, url, title, text) VALUES(?,?,?,?)",
        (source_id, "https://example.com/scipy/doc1", "SciPy Doc 1", "SciPy text"),
    )
    cur.execute(
        "INSERT INTO documents(source_id, url, title, text) VALUES(?,?,?,?)",
        (source_id, "https://example.com/scipy/doc2", "SciPy Doc 2", "SciPy text"),
    )
    conn.commit()

    # Delete the source
    cur.execute("DELETE FROM sources WHERE id=?", (source_id,))
    conn.commit()

    # Check that the document is also deleted
    cur.execute("SELECT COUNT(*) FROM documents WHERE source_id=?", (source_id,))
    count = cur.fetchone()[0]
    assert count == 0