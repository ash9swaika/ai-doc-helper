from app.indexer import index as index_module
from app.indexer import query as search_module

def test_search_returns_matching_results(conn):
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
        """
    }

    # Build index into this DB file
    index_module.build_index(
        package=package,
        version=version,
        base_url=base_url,
        url_to_html=url_to_html,
    )

    # search.search(q, package=None, version=None, limit=10)
    results = search_module.search("DataFrame", package="pandas", limit=5)

    assert len(results) >= 1
    top = results[0]
    assert top["package"] == "pandas"
    assert "DataFrame" in top["title"]
    # snippet uses highlight([...]) – depending on case it might be [DataFrame]
    assert "DataFrame" in top["snippet"] or "[DataFrame]" in top["snippet"]


def test_search_respects_package_filter(conn):
    base_url = "https://docs.example.com"

    # pandas docs mentioning "DataFrame"
    index_module.build_index(
        package="pandas",
        version="2.2.2",
        base_url=base_url,
        url_to_html={
            "https://docs.example.com/pandas_df.html": """
                <html>
                  <head><title>DataFrame</title></head>
                  <body>
                    <p>A DataFrame is a 2D labeled data structure.</p>
                  </body>
                </html>
            """
        },
    )

    # numpy docs mentioning "array"
    index_module.build_index(
        package="numpy",
        version="1.26.0",
        base_url=base_url,
        url_to_html={
            "https://docs.example.com/numpy_array.html": """
                <html>
                  <head><title>ndarray</title></head>
                  <body>
                    <p>An ndarray is a multidimensional array object.</p>
                  </body>
                </html>
            """
        },
    )

    # search for "array" but restrict to pandas – should return nothing or only pandas hits
    results_pandas = search_module.search("array", package="pandas", limit=10)
    # It's acceptable for this to be empty, but it must NOT include numpy
    assert all(r["package"] == "pandas" for r in results_pandas)

    # Now search with package="numpy" – should give us numpy docs
    results_numpy = search_module.search("array", package="numpy", limit=10)
    assert len(results_numpy) >= 1
    assert all(r["package"] == "numpy" for r in results_numpy)


def test_search_respects_version_filter(conn):
    base_url = "https://docs.example.com"

    # Two versions of same package
    index_module.build_index(
        package="pandas",
        version="1.0.0",
        base_url=base_url,
        url_to_html={
            "https://docs.example.com/pandas_v1.html": """
                <html>
                  <head><title>DataFrame v1</title></head>
                  <body>
                    <p>DataFrame API - version 1.0.0</p>
                  </body>
                </html>
            """
        },
        conn=conn
    )

    index_module.build_index(
        package="pandas",
        version="2.0.0",
        base_url=base_url,
        url_to_html={
            "https://docs.example.com/pandas_v2.html": """
                <html>
                  <head><title>DataFrame v2</title></head>
                  <body>
                    <p>DataFrame API - version 2.0.0</p>
                  </body>
                </html>
            """
        },
        conn=conn
    )

    results_v1 = search_module.search("DataFrame", package="pandas", version="1.0.0", limit=10)
    assert len(results_v1) >= 1
    assert all(r["version"] == "1.0.0" for r in results_v1)

    results_v2 = search_module.search("DataFrame", package="pandas", version="2.0.0", limit=10)
    assert len(results_v2) >= 1
    assert all(r["version"] == "2.0.0" for r in results_v2)


def test_search_respects_limit(conn):
    package = "pandas"
    version = "2.2.2"
    base_url = "https://docs.example.com"

    # Make multiple chunks match "DataFrame" by repeating it a lot
    url_to_html = {
        "https://docs.example.com/df.html": """
            <html>
              <head><title>DataFrame</title></head>
              <body>
                <p>DataFrame one.</p>
                <p>DataFrame two.</p>
                <p>DataFrame three.</p>
                <p>DataFrame four.</p>
              </body>
            </html>
        """
    }

    index_module.build_index(
        package=package,
        version=version,
        base_url=base_url,
        url_to_html=url_to_html,
    )

    results = search_module.search("DataFrame", package="pandas", limit=2)
    assert len(results) <= 2


def test_search_snippet_uses_highlight(conn):
    package = "pandas"
    version = "2.2.2"
    base_url = "https://docs.example.com"

    url_to_html = {
        "https://docs.example.com/df.html": """
            <html>
              <head><title>DataFrame</title></head>
              <body>
                <p>A DataFrame is a 2D labeled data structure.</p>
              </body>
            </html>
        """
    }

    index_module.build_index(
        package=package,
        version=version,
        base_url=base_url,
        url_to_html=url_to_html,
        conn=conn
    )

    results = search_module.search("DataFrame", package="pandas", limit=1)
    assert len(results) == 1
    snippet = results[0]["snippet"]
    # highlight(docs_fts, 0, '[', ']') → '[DataFrame]' or '[DataFrame] ...'
    assert "[" in snippet and "]" in snippet
