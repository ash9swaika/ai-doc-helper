from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="AI Doc Helper Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "service": "ai-doc-helper-backend"}

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

@app.get("/search", response_model=SearchResponse)
def search(query: str = Query(..., min_length=1, max_length=200)):
    # TODO: replace with actual search logic
    mock = [
        SearchResult(
            title="Getting Started FastAPI", 
            snippet="FastAPI is easy to learn and fast to code...", 
            url="https://fastapi.tiangolo.com/"
        ),
        SearchResult(
            title="VS Code Extensions API", 
            snippet="Discover the best VS Code extensions to boost your productivity.", 
            url="https://code.visualstudio.com/docs/editor/extension-gallery"
        )
    ]
    
    # tiny heuristic: filter by token presence
    q = query.lower()
    results = [r for r in mock if q in r.title.lower() or q in r.snippet.lower()] or mock
    return SearchResponse(query=query, results=results)