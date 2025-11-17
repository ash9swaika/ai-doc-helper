# backend/app/docs_resolver.py
import json, urllib.request

def pypi_project_urls(pkg_name: str) -> dict:
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    with urllib.request.urlopen(url, timeout=6) as r:
        data = json.load(r)
    return data.get("info", {}).get("project_urls", {}) or {}

def resolve_docs_url(pkg_name: str, version: str | None):
    urls = {}
    try:
        urls = pypi_project_urls(pkg_name)
    except Exception:
        pass

    # Priority: Documentation → Homepage → ReadTheDocs convention
    doc_url = urls.get("Documentation") or urls.get("Homepage") or urls.get("Home") or ""
    # ReadTheDocs versioning heuristic
    if "readthedocs.io" in doc_url and version:
        # common patterns: /en/stable/, /en/latest/, /en/<version>/
        # verify existence with a HEAD if you want; else optimistic:
        return doc_url.rstrip("/") + f"/en/{version}/"
    return doc_url or ""
