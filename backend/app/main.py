from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

@app.get("/search")
def search(query: str):
    # placeholder for doc retrieval logic
    return {"query": query, "results": []}