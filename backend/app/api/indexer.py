from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
import asyncio

from app.indexer.db import init_db
from app.indexer.fetch import fetch_many
from app.indexer.index import build_index
from app.indexer.query import search

router = APIRouter()

class SourceSpec(BaseModel):
    package: str
    version: str
    base_url: str
    urls: List[str]  # list of documentation pages to fetch & index (MVP)

@router.post("/index/init")
def index_init():
    init_db()
    return {"status": "ok"}

@router.post("/index/build")
async def index_build(spec: SourceSpec):
    pages = await fetch_many(spec.urls)
    build_index(spec.package, spec.version, spec.base_url, pages)
    return {"status": "indexed", "pages": len(pages)}

class Query(BaseModel):
    q: str
    package: str | None = None
    version: str | None = None
    limit: int = 10

@router.post("/query")
def query(q: Query):
    results = search(q.q, q.package, q.version, q.limit)
    return {"results": results}
