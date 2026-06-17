import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.graph import graph
from app.state import AgentState

app = FastAPI(title="BigQuery SQL Agent", version="0.1.0")

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "https://sanchitk.dev").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sql: str
    attempts: int


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    initial: AgentState = {
        "question": req.question,
        "schema": "",
        "sql": "",
        "error": None,
        "attempts": 0,
        "result": None,
        "answer": "",
    }
    result = await graph.ainvoke(initial)
    return QueryResponse(
        answer=result["answer"],
        sql=result.get("sql", ""),
        attempts=result.get("attempts", 0),
    )


# Serve the React frontend — mount after API routes so /health and /query win.
_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(_dist / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        candidate = _dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {"service": "BigQuery SQL Agent", "status": "ok"}
