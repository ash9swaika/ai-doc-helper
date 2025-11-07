## 🗺️ Roadmap

### v0.1 – ✅ Completed
- VS Code command **AI: Lookup Docs** launches successfully.
- Webview panel renders ("Hello AI Docs 👋").
- FastAPI backend (via `uv`) runs locally with `/health` route.
- Webview connects to backend and confirms live connection.

### v0.2 – 🚧 In Progress
- Add `/search` endpoint to FastAPI that accepts `query` and returns mock results.
- Extend webview with a search input + "Fetch Docs" button.
- Display fetched search results dynamically in the panel.

### v0.3 – 🔜 Planned
- Create `indexer/` module to crawl or cache documentation pages.
- Connect backend `/search` to indexer for real retrieval.
- Refine UI: better styling, loading state, and result formatting.