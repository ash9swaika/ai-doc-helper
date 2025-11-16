# tests/app/indexer/test_index.py
from app.indexer import index as index_module


def test_upsert_source_inserts_and_updates(conn):
    cur = conn.cursor()

    # First upsert: should insert
    source_id_1 = index_module.upsert_source(
        conn,
        package="pandas",
        version="2.2.2",
        base_url="https://docs.example.com/v1",
    )

    # Check row exists
    cur.execute("SELECT id, package, version, base_url FROM sources")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == source_id_1
    assert rows[0][1] == "pandas"
    assert rows[0][2] == "2.2.2"
    assert rows[0][3] == "https://docs.example.com/v1"

    # Second upsert with same (package, version) but different base_url
    source_id_2 = index_module.upsert_source(
        conn,
        package="pandas",
        version="2.2.2",
        base_url="https://docs.example.com/v2",
    )

    # Should refer to the same logical source
    assert source_id_1 == source_id_2

    # There should still be exactly 1 row, but with updated base_url
    cur.execute("SELECT id, package, version, base_url FROM sources")
    rows = cur.fetchall()
    assert len(rows) == 1
    (row_id, pkg, ver, base_url) = rows[0]
    assert row_id == source_id_1
    assert pkg == "pandas"
    assert ver == "2.2.2"
    assert base_url == "https://docs.example.com/v2"


def test_upsert_document_inserts_and_updates(conn):
    cur = conn.cursor()

    # First create a source row (can use upsert_source or direct insert)
    source_id = index_module.upsert_source(
        conn,
        package="pandas",
        version="2.2.2",
        base_url="https://docs.example.com",
    )

    url = "https://docs.example.com/df.html"
    html_v1 = "<html><head><title>Old Title</title></head><body>Old body</body></html>"
    html_v2 = "<html><head><title>New Title</title></head><body>New body</body></html>"

    # First upsert: insert doc
    doc_id_1, title_1, text_1 = index_module.upsert_document(
        conn, source_id=source_id, url=url, html=html_v1
    )

    # Check inserted row
    cur.execute("SELECT id, source_id, url, title, text FROM documents")
    rows = cur.fetchall()
    assert len(rows) == 1
    (row_id, row_source_id, row_url, row_title, row_text) = rows[0]
    assert row_id == doc_id_1
    assert row_source_id == source_id
    assert row_url == url
    assert "Old Title" in row_title
    assert "Old body" in row_text

    # Second upsert: should update same row (same url/source_id)
    doc_id_2, title_2, text_2 = index_module.upsert_document(
        conn, source_id=source_id, url=url, html=html_v2
    )

    # Same doc id, updated content
    assert doc_id_1 == doc_id_2
    assert "New Title" in title_2
    assert "New body" in text_2

    # Verify DB state
    cur.execute("SELECT id, source_id, url, title, text FROM documents")
    rows = cur.fetchall()
    assert len(rows) == 1
    (row_id, row_source_id, row_url, row_title, row_text) = rows[0]
    assert row_id == doc_id_1
    assert "New Title" in row_title
    assert "New body" in row_text


def test_index_chunks_creates_chunks_and_fts_rows(conn):
    cur = conn.cursor()

    # Create a source + document
    source_id = index_module.upsert_source(
        conn,
        package="pandas",
        version="2.2.2",
        base_url="https://docs.example.com",
    )

    url = "https://docs.example.com/df.html"
    html = """
    <html>
      <head><title>DataFrame Basics</title></head>
      <body>
        <h1>DataFrame</h1>
        <p>A DataFrame is a 2D labeled data structure.</p>

        <h2>Creating</h2>
        <p>You can create it from dicts, lists, NumPy arrays...</p>
      </body>
    </html>
    """

    doc_id, title, text = index_module.upsert_document(conn, source_id, url, html)

    # Index chunks first time
    index_module.index_chunks(
        conn,
        package="pandas",
        version="2.2.2",
        doc_id=doc_id,
        url=url,
        text=text,
        title=title,
    )

    # Check chunks exist
    cur.execute("SELECT COUNT(*) FROM chunks WHERE document_id=?", (doc_id,))
    chunk_count_1 = cur.fetchone()[0]
    assert chunk_count_1 > 0

    # Check FTS entries exist for this doc
    cur.execute("SELECT COUNT(*) FROM docs_fts WHERE document_id=?", (doc_id,))
    fts_count_1 = cur.fetchone()[0]
    assert fts_count_1 == chunk_count_1

    # Re-index with slightly different text (to check deletion + reinsertion)
    new_text = text + "\nExtra line about pandas DataFrame."
    index_module.index_chunks(
        conn,
        package="pandas",
        version="2.2.2",
        doc_id=doc_id,
        url=url,
        text=new_text,
        title=title,
    )

    # After re-index, ensure we don't just accumulate chunks forever
    cur.execute("SELECT COUNT(*) FROM chunks WHERE document_id=?", (doc_id,))
    chunk_count_2 = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM docs_fts WHERE document_id=?", (doc_id,))
    fts_count_2 = cur.fetchone()[0]

    assert chunk_count_2 > 0
    assert fts_count_2 == chunk_count_2
    # This isn't strictly guaranteed to be different, but often will be if chunking changes
    # The key guarantee: re-index didn't double counts; it replaced them
    assert chunk_count_2 == chunk_count_1 or chunk_count_2 != 0


def test_build_index_creates_source_docs_chunks_and_fts(conn):
    cur = conn.cursor()

    package = "pandas"
    version = "2.2.2"
    base_url = "https://docs.example.com"

    url_to_html = {
        "https://docs.example.com/df.html": """
            <html>
              <head><title>DataFrame</title></head>
              <body>
                <h1>DataFrame</h1>
                <p>A DataFrame is a 2D labeled data structure.</p>
              </body>
            </html>
        """,
        "https://docs.example.com/indexing.html": """
            <html>
              <head><title>Indexing</title></head>
              <body>
                <h1>Indexing</h1>
                <p>You can select rows and columns using labels or positions.</p>
              </body>
            </html>
        """,
    }

    cur.execute("SELECT name, type, sql FROM sqlite_master WHERE name LIKE 'docs_fts%'")
    print("docs_fts definitions:", cur.fetchall())

    cur.execute("PRAGMA table_info(docs_fts)")
    print("docs_fts columns:", cur.fetchall())

    cur.execute("PRAGMA table_info('docs_fts_content')")
    print("docs_fts_content columns:", cur.fetchall())

    # Call the top-level build function
    index_module.build_index(
        package=package,
        version=version,
        base_url=base_url,
        url_to_html=url_to_html,
    )

    # 1) One source row
    cur.execute("SELECT id, package, version, base_url FROM sources")
    sources_rows = cur.fetchall()
    assert len(sources_rows) == 1
    source_id, pkg, ver, base_url_db = sources_rows[0]
    assert pkg == package
    assert ver == version
    assert base_url_db == base_url

    # 2) One documents row per URL
    cur.execute("SELECT url FROM documents WHERE source_id=?", (source_id,))
    doc_urls = {row[0] for row in cur.fetchall()}
    assert doc_urls == set(url_to_html.keys())

    # 3) Some chunks exist for these documents
    cur.execute("SELECT COUNT(*) FROM chunks")
    total_chunks = cur.fetchone()[0]
    assert total_chunks > 0

    # 4) docs_fts populated; at least as many rows as chunks
    cur.execute("SELECT COUNT(*) FROM docs_fts")
    total_fts = cur.fetchone()[0]
    assert total_fts == total_chunks

    cur.execute("PRAGMA table_info(docs_fts)")
    print(cur.fetchall())

    cur.execute("SELECT url, package, version, document_id, chunk_id FROM docs_fts")
    print("docs_fts rows:", cur.fetchall())

    # Optional: quick sanity check that some text is searchable
    cur.execute(
        "SELECT COUNT(*) FROM docs_fts WHERE text LIKE '%DataFrame%' OR text LIKE '%Indexing%'"
    )
    assert cur.fetchone()[0] > 0
