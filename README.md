# AI Doc Helper

A VS Code extension + backend system for intelligent documentation lookup.

## Current Milestone
- ✅ Working VS Code extension (`AI: Lookup Docs`)
- ✅ Webview panel ("Hello AI Docs")
- 🚧 Next: Connect to FastAPI backend

## Run Locally
```bash
cd extension
npm install
npm run compile
# Press F5 in VS Code → open "AI: Lookup Docs"

### Current Status (v0.1)
The VS Code extension successfully launches via `AI: Lookup Docs`, opens a working webview panel, and connects to a local FastAPI backend (built with uv) through a live `/health` ping.
