from typing import List, Dict, Optional
import sqlite3
from app.indexer.db import connect

def search(q: str, package: Optional[str]=None, version: Optional[str]=None, limit: int = 10) -> List[Dict]:
    conn = connect()
    cur = conn.cursor()

    filters = []
    params = []

    if package:
        filters.append("package = ?")
        params.append(package)
    if version:
        filters.append("version = ?")
        params.append(version)

    where = "WHERE 1=1"
    if filters:
        where += " AND " + " AND ".join(filters)

    # FTS5 rank: bm25(doc)
    sql = f"""
      SELECT
        docs_fts.rowid,
        highlight(docs_fts, 0, '[', ']') AS snippet, -- on text field
        title, url, package, version, document_id, chunk_id,
        bm25(docs_fts) AS score
      FROM docs_fts
      WHERE docs_fts MATCH ?
      {('AND ' + ' AND '.join(filters)) if filters else ''}
      ORDER BY score
      LIMIT ?
    """
    # FTS5 expects a MATCH query; simple words work, add quotes for phrases
    cur.execute(sql, [q, *params, limit])
    rows = cur.fetchall()
    results = []
    for row in rows:
        _, snippet, title, url, pkg, ver, doc_id, chunk_id, score = row
        results.append({
            "title": title,
            "url": url,
            "package": pkg,
            "version": ver,
            "snippet": snippet,
            "score": score,
            "document_id": doc_id,
            "chunk_id": chunk_id
        })
    return results
