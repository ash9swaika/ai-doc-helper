import hashlib
from pathlib import Path
from typing import Iterable, Dict
import httpx

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

def _cache_key(url: str) -> Path:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.html"

async def fetch_many(urls: Iterable[str], timeout=20.0) -> Dict[str, str]:
    """Fetch URLs with simple file cache (no etag for MVP)."""
    out = {}
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for url in urls:
            fp = _cache_key(url)
            if fp.exists():
                out[url] = fp.read_text(encoding="utf-8", errors="ignore")
                continue
            r = await client.get(url)
            r.raise_for_status()
            fp.write_text(r.text, encoding="utf-8", errors="ignore")
            out[url] = r.text
    return out
