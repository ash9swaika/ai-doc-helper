## 🗺️ Roadmap



### v0.3 – 🔜 Planned
- Create `indexer/` module to crawl or cache documentation pages.
- Connect backend `/search` to indexer for real retrieval.
- Refine UI: better styling, loading state, and result formatting.

# AI Doc Helper — Phase 1–6 Checkpoint

*Last updated: 11 Nov 2025 (Asia/Kolkata)*

## 🧭 Project Overview

AI Doc Helper is a VS Code extension + FastAPI backend + (upcoming) indexer that lets developers query documentation for their **installed** libraries directly inside the editor.

**Repository layout** (agreed structure):

```
ai-doc-helper/
  backend/     ← FastAPI backend (APIs, env + project detection)
  extension/   ← VS Code extension (webview UI, commands)
  indexer/     ← upcoming BM25 / scraper / ranking pipeline
  docs/        ← README, roadmap, design notes
```

## 🎯 Goals (MVP)

* Detect project ecosystems (Python, Node) and the **active** environment per workspace folder
* Validate environment vs declared deps; highlight **missing/incompatible** packages
* Provide an in-editor panel to query docs (health check done; doc retrieval pipeline coming next)

---

## 🧩 Milestones & Reasoning

### ✅ Phase 1 — Extension Bootstrap

**Why:** Prove activation → command → webview loop end-to-end.

**What:**

* `activate()` / `deactivate()` implemented
* Registered command: **“AI: Lookup Docs”**
* Debugged via **F5** → Command Palette → *AI: Lookup Docs*
* VS Code command **AI: Lookup Docs** launches successfully.
* CORS enabled
* Webview button **Ping Backend** → fetches `/health`
* FastAPI backend (via `uv`) runs locally with `/health` route.
* Webview connects to backend and confirms live connection.

**Outcome:** Live JSON `{ "status": "ok" }` in panel.
**Outcome:** Webview opens and shows *“Hello AI Docs 👋”*.

---

### ✅ Phase 2 — Add search in background that accepts query

**Why:** Verify front-to-back communication early.

**What:**

* Add `/search` endpoint to FastAPI that accepts `query` and returns mock results.
* Extend webview with a search input + "Fetch Docs" button.
* Display fetched search results dynamically in the panel.

**Outcome:** Display mock results in the panel.

---

### ✅ Phase 3 — Multi-Ecosystem Project Detection

**Why:** Repo is polyglot; we need correct docs per ecosystem.

**What:**

* `project_detect.py` scans for sentinels: `pyproject.toml`, `requirements.txt`, `package.json`, etc.
* Supports nested folders like `backend/`, `extension/`
* Endpoint: `GET /project/detect-multi`

**Outcome:** Structured list of all detected ecosystems + candidates.

---

### ✅ Phase 4 — Python Environment Discovery

**Why:** Declared vs **installed** versions often differ.

**What:**

* `env_python.py` → `GET /env/python`
* Uses `importlib.metadata` to enumerate installed distributions
* Interpreter resolution: configured path or guess `.venv/venv` under each folder

**Outcome:** Accurate, runtime list of installed packages.

---

### ✅ Phase 5 — Environment Validation (Python)

**Why:** Early surfacing of environment drift prevents wasted queries.

**What:**

* `validate_python.py` → `POST /env/validate-python`

  * Parses `requirements.txt` / `pyproject.toml`
  * Compares against installed set
  * Returns `{missing:[], incompatible:[]}`
* VS Code function `validatePythonEnvForFolder()` shows popup:

  * ✅ OK
  * ⚠️ Mismatch with actions: **Pick Interpreter**, **Show Details**, **Index Anyway**

**Outcome:** Clear guidance and actionable next steps inside VS Code.

---

### ✅ Phase 6 — Project + Environment Merge

**Why:** Single source of truth for indexing and retrieval.

**What:**

* `GET /project/resolve` (planned/implemented) integrates detection + env inventory per folder

**Outcome:** Foundation for the indexer to target the right docs with the right versions.

---

## 🪲 Current Issue — “Missing Routes” in FastAPI Docs

**Symptom:** `/docs` only shows older endpoints (e.g., `/health`); new ones (e.g., `/env/validate-python`, `/project/resolve`) are **absent**. Extension calls return **404**.

**What we already verified:**

* Import path OK: `E:\dev\ai-code-doc-helper\backend\app\__init__.py`
* Clean import OK: `python -X dev -c "import app.main; print('OK imported')"`
* Uvicorn starts clean; no startup errors

**Likely root causes:**

1. Routes live under `if __name__ == "__main__":` (not executed when imported)
2. A **second** `app = FastAPI()` re-declared later, wiping routes
3. Silent import error (e.g., `from app.validate_python import ...` fails), preventing route registration

**Fixes applied / guidance:**

* Ensure a **single** `app = FastAPI()` near the top-level
* Define **all** `@app.get`/`@app.post` routes at import time (not inside `__main__` or functions)
* Start from project root of `backend/` so `import app.main` resolves correctly
* Add a probe route `GET /__probe` to verify the correct file instance
* Run uvicorn with explicit module + reload dir:

```bash
uv run uvicorn app.main:app \
  --reload \
  --port 8000 \
  --reload-dir .
```

**Bug resolution**
An older instance of the server process was still running which disallowed the newer versions access to the port due to port-binding. But we could not see the instance of this process because the process
exited between two commands

```bash 
Get-Process uvicorn, python, uv -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, StartTime, Path
```
Looked at this command and timestamp of when the processes started to figure out the stale process. Then killed that process and re-run the uvicorn command. It fixed the issue.

**Success criteria:** New endpoints appear in **/docs**; VS Code popups stop seeing 404.

---

## 🔍 Verification Checklist

* [ ] `grep -n "app = FastAPI" -n backend/app/*.py` → only one authoritative instance
* [ ] No route decorators below `if __name__ == "__main__"`
* [ ] `uvicorn app.main:app --reload` shows probe route `/__probe`
* [ ] `/docs` lists `/env/validate-python`, `/project/resolve`, `/project/detect-multi`, `/env/python`
* [ ] Extension command **Validate Python Env** returns 200 OK

---

## 🚀 Next Implementation Steps (Post-Fix)

1. **Indexer skeleton (indexer/):**

   * Define corpus format per ecosystem (package → version → docs base URL)
   * Add BM25 baseline with on-disk store (whoosh/lucene-like or elastic-ready JSON)
2. **Doc source adapters:**

   * Python: `docs.python.org` stubs + package docs (readthedocs, pdoc, mkdocs)
   * Node: `npmjs` metadata + `typedoc`/docs sites
3. **Query API (backend):**

   * `POST /query` with `{symbol, package, version, language, context}`
   * Return ranked passages with source URLs
4. **Extension UI:**

   * Search box + results list + “Open in Browser” / “Copy snippet”
   * Sticky banner showing **interpreter** and **workspace folder** in focus
5. **Quality loop:**

   * Capture clicked result → relevance feedback (MVP: local histogram)
   * Log latency + success rate

---

## 🗺️ Roadmap Snapshot

* [x] Phase 1: Bootstrap extension
* [x] Phase 2: Webview ↔ backend health check
* [x] Phase 3: Multi-ecosystem detection
* [x] Phase 4: Python env inventory
* [x] Phase 5: Env validation + VS Code UX
* [x] Phase 6: Project–Env resolution
* [ ] Phase 7: Indexer baseline (BM25)
* [ ] Phase 8: Query API + ranking
* [ ] Phase 9: Webview search UX + telemetry

---

## 🧪 Handy Commands

```bash
# From ai-doc-helper/backend
uv run uvicorn app.main:app --reload --port 8000 --reload-dir .

# Probe import
python -X dev -c "import app.main; print('OK imported')"

# List endpoints (requires httpie)
http :8000/openapi.json | jq '.paths | keys'
```

---

## 📝 Notes for Contributors (future)

* Keep all route registrations at module top-level; avoid side effects in `__main__`
* Prefer dependency-injected helpers for testing (`def make_app(...):` optional, but return **one** app)
* Add types + pydantic models for request/response stability

---

## 📌 Appendix — Data Structures

**/env/validate-python response (example):**

```json
{
  "folder": "backend/",
  "interpreter": "E:/dev/ai-code-doc-helper/backend/.venv/Scripts/python.exe",
  "missing": ["numpy>=2.1"],
  "incompatible": [{"name": "pydantic", "declared": ">=2", "installed": "1.10.13"}]
}
```
