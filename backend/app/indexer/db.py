from pathlib import Path
import sqlite3
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent.parent / "index.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    # SQLite does not enforce foreign keys by default; enable it
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    return conn

def init_db():
    """Creates a DB as per the ER diagram in docs/db.xml."""
    conn = connect()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            package TEXT NOT NULL,
            version TEXT NOT NULL,
            base_url TEXT NOT NULL,
            checksum TEXT,
            UNIQUE(package, version)
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            path TEXT,               -- relative path on site if you want
            title TEXT,
            text TEXT,               -- full page text (pre-chunk)
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_id, url),
            FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE
        );

        -- FTS5 over CHUNKS (not full docs) for better ranking/precision
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL,
            pos INTEGER NOT NULL,    -- chunk order within a document
            text TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        DROP TABLE IF EXISTS docs_fts;
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            text, title, url, package, version, document_id UNINDEXED, chunk_id UNINDEXED,
            tokenize='porter'
        );
        """
    )
    conn.commit()
    return conn
