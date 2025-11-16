from typing import Dict, Optional
import sqlite3
from app.indexer.db import init_db
from app.indexer.extract import html_to_text_and_title, chunk_text_heading_aware

def upsert_source(conn: sqlite3.Connection, package: str, version: str, base_url: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sources(package, version, base_url) VALUES(?,?,?) "
        "ON CONFLICT(package,version) DO UPDATE SET base_url=excluded.base_url "
        "RETURNING id",
        (package, version, base_url),
    )
    source_id = cur.fetchone()[0]
    conn.commit()
    return source_id

def upsert_document(conn: sqlite3.Connection, source_id: int, url: str, html: str):
    text, title = html_to_text_and_title(html)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents(source_id, url, title, text) VALUES (?,?,?,?) "
        "ON CONFLICT(source_id, url) DO UPDATE SET title=excluded.title, text=excluded.text "
        "RETURNING id",
        (source_id, url, title, text),
    )
    doc_id = cur.fetchone()[0]
    conn.commit()
    return doc_id, title, text

def index_chunks(conn: sqlite3.Connection, package: str, version: str, doc_id: int, url: str, text: str, title: str):
    """
    Given a document's plain text, split it into chunks and index them:

    - Deletes any existing chunks for this document (so re-indexing is clean).
    - Inserts new rows into `chunks`.
    - Inserts corresponding rows into `docs_fts` (FTS5) with metadata:  
        package, version, url, document_id, chunk_id.
    """
    chunks = chunk_text_heading_aware(text)
    cur = conn.cursor()
    # wipe old chunks for this doc
    cur.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
    cur.execute("DELETE FROM docs_fts WHERE document_id=?", (doc_id,))
    # insert chunks and into FTS
    for i, ch in enumerate(chunks):
        cur.execute("INSERT INTO chunks(document_id, pos, text) VALUES (?,?,?)", (doc_id, i, ch))
        chunk_id = cur.lastrowid
        print(ch, title, url, package, version, doc_id, chunk_id)
        cur.execute(
            "INSERT INTO docs_fts(text, title, url, package, version, document_id, chunk_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ch, title, url, package, version, doc_id, chunk_id),
        )
        cur.execute("SELECT url, package, version, document_id, chunk_id FROM docs_fts")
        print("docs_fts rows:", cur.fetchall())
    conn.commit()

def build_index(
    package: str,
    version: str,
    base_url: str,
    url_to_html: Dict[str, str],
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """
    Index all provided URLs for a given (package, version).

    - Ensures the `sources` row exists.
    - Upserts each document row.
    - Indexes each document's text into chunks + FTS.
    If `conn` is provided, use it and DO NOT close it.
    If `conn` is None, create a new connection via init_db() and close it.
    """
    own_conn = False
    if conn is None:
        conn = init_db()
        own_conn = True

    source_id = upsert_source(conn, package=package, version=version, base_url=base_url)

    for url, html in url_to_html.items():
        doc_id, title, text = upsert_document(conn, source_id=source_id, url=url, html=html)
        index_chunks(
            conn=conn,
            package=package,
            version=version,
            doc_id=doc_id,
            url=url,
            text=text,
            title=title,
        )

    if own_conn:
        conn.close()
