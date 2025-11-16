# tests/app/indexer/test_fetch.py

import asyncio
import pytest

from app.indexer import fetch as fetch_module

class FakeResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            # We don't need a real httpx.HTTPStatusError type; any exception is fine
            raise Exception(f"HTTP {self.status_code}")

class FakeAsyncClient:
    """
    Simple async fake to stand in for httpx.AsyncClient.

    mapping: url -> (status_code, text)
    """
    def __init__(self, mapping, *args, **kwargs):
        self.mapping = mapping
        self.calls = []
        self.closed = False

    async def get(self, url):
        self.calls.append(url)
        status_code, text = self.mapping.get(url, (404, "not found"))
        return FakeResponse(status_code=status_code, text=text)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.closed = True

def test_fetch_many_cache_miss_uses_network_and_writes_cache(tmp_path, monkeypatch):
    # Override CACHE_DIR for the test
    monkeypatch.setattr(fetch_module, "CACHE_DIR", tmp_path / ".cache")
    fetch_module.CACHE_DIR.mkdir(exist_ok=True)

    urls = ["https://example.com/page1"]

    fake_client = FakeAsyncClient({
        "https://example.com/page1": (200, "<html>OK</html>"),
    })

    # Patch httpx.AsyncClient to return our fake client
    def fake_async_client_ctor(*args, **kwargs):
        return fake_client

    monkeypatch.setattr(fetch_module.httpx, "AsyncClient", fake_async_client_ctor)

    # Run the async function from a sync test
    result = asyncio.run(fetch_module.fetch_many(urls, timeout=5.0))

    # It should return the body
    assert result["https://example.com/page1"] == "<html>OK</html>"

    # It should have made exactly one network call
    assert fake_client.calls == ["https://example.com/page1"]

    # And the cache file should exist with the same content
    cache_files = list(fetch_module.CACHE_DIR.glob("*.html"))
    assert len(cache_files) == 1
    assert cache_files[0].read_text(encoding="utf-8") == "<html>OK</html>"


def test_fetch_many_cache_hit_skips_network(tmp_path, monkeypatch):
    # Override CACHE_DIR for the test
    monkeypatch.setattr(fetch_module, "CACHE_DIR", tmp_path / ".cache")
    fetch_module.CACHE_DIR.mkdir(exist_ok=True)

    url = "https://example.com/page1"

    # Pre-populate cache file
    from app.indexer.fetch import _cache_key
    cache_file = _cache_key(url)
    cache_file.write_text("<html>FROM CACHE</html>", encoding="utf-8")

    fake_client = FakeAsyncClient({
        url: (200, "<html>SHOULD NOT BE USED</html>"),
    })

    def fake_async_client_ctor(*args, **kwargs):
        return fake_client

    monkeypatch.setattr(fetch_module.httpx, "AsyncClient", fake_async_client_ctor)

    result = asyncio.run(fetch_module.fetch_many([url], timeout=5.0))

    # Should return cached content, not network result
    assert result[url] == "<html>FROM CACHE</html>"

    # No network requests should have been made
    assert fake_client.calls == []

