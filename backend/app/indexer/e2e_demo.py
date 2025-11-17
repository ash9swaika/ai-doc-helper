# app/indexer/e2e_demo.py

import asyncio

from app.indexer.fetch import fetch_many
from app.indexer.index import build_index
from app.indexer import query as query_module  # or `search` if that's your module name


async def main():
    # 1) Define what we want to index
    package = "pandas"
    version = "test-1.0.0"
    base_url = "https://pandas.pydata.org"

    # Keep this small for first test
    urls = [
        "https://pandas.pydata.org/docs/reference/frame.html",
        "https://pandas.pydata.org/docs/reference/index.html",
    ]

    print("🔎 Fetching docs...")
    url_to_html = await fetch_many(urls, timeout=20.0)

    # You can inspect how many actually succeeded
    for url, html in url_to_html.items():
        print(f"- {url}: {'OK' if html else 'EMPTY'}")

    # 2) Build the index in your normal DB (db.DB_PATH)
    print("📚 Building index...")
    build_index(
        package=package,
        version=version,
        base_url=base_url,
        url_to_html=url_to_html,
    )

    # 3) Run a couple of search queries
    print("\n🔍 Running sample search queries:\n")

    def run_query(q: str):
        results = query_module.search(q, package=package, version=version, limit=5)
        print(f"Query: {q!r}  -> {len(results)} hits")
        for r in results:
            print("  -", r["title"], "→", r["url"])
            print("    snippet:", r["snippet"])
        print()

    run_query("DataFrame")
    run_query("indexing")
    run_query("groupby")


if __name__ == "__main__":
    asyncio.run(main())
