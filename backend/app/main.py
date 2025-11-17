from app.api import indexer
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict, Optional
from app.project_detect import detect_multi
from app.env_python import env_python_packages
from app.project_resolve import resolve_all
from app.validate_python import discover_declared_requirements, diff_declared_installed

app = FastAPI(title="AI Doc Helper Backend")
app.include_router(indexer.router, prefix="/search", tags=["search"])


ROOT = Path(__file__).resolve().parents[2]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

class ResolveRequest(BaseModel):
    folder_python_paths: Optional[Dict[str, str]] = None  # map of folder -> python path

class ValidateResponse(BaseModel):
    workdir: str
    interpreter: str
    missing: list
    incompatible: list



@app.get("/project/detect-multi")
def project_detect_multi():
    """Detects Python and Node in repo root and first-level subfolders (e.g., backend/, extension/)."""
    det = detect_multi(ROOT, scan_depth=1)
    # dataclasses to plain dict
    return {
        "roots": [
            {
                "path": r.path,
                "ecosystems": [
                    {
                        "name": e.name,
                        "score": e.score,
                        "files": e.files,
                        "packages": e.packages,
                    } for e in r.ecosystems
                ],
            } for r in det.roots
        ]
    }

@app.get("/env/python")
def env_python(workdir: str | None = Query(None), python_path: str | None = Query(None)):
    """
    Return installed Python packages for a given interpreter or workdir.
    """
    return env_python_packages(workdir=workdir, python_path=python_path)


@app.get("/env/validate-python", response_model=ValidateResponse)
def validate_python(workdir: str = Query(...), python_path: str | None = Query(None)):
    """
    Compare project's declared Python deps (requirements.txt / pyproject.toml)
    vs packages installed in the provided interpreter (or guessed).
    """
    declared = discover_declared_requirements(Path(workdir))
    env = env_python_packages(workdir=workdir, python_path=python_path)
    missing, incompatible = diff_declared_installed(declared, env["packages"])
    return {
        "workdir": workdir,
        "interpreter": env["interpreter"],
        "missing": missing,
        "incompatible": incompatible,
    }


@app.get("/health")
def health():
    return {"ok": True, "service": "ai-doc-helper-backend"}


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

@app.get("/__probe")
def __probe():
    import inspect
    return {"main_file": __file__, "app_id": id(app)}


@app.post("/project/resolve")
def project_resolve(body: ResolveRequest):
    return resolve_all(ROOT, folder_python_paths=body.folder_python_paths or {})