import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.graph import graph
from app.state import AgentState

app = FastAPI(title="BigQuery SQL Agent", version="0.1.0")

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "https://sanchitk.dev,https://bq-sql-agent-uysui4e3nq-uc.a.run.app").split(",")]
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


# Serve the widget JS bundle and any other static dist files.
# The frontend builds as an IIFE (bq-sql-agent.iife.js), not a full SPA.
_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/dist", StaticFiles(directory=_dist), name="dist")


@app.get("/demo", response_class=HTMLResponse)
async def demo():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BigQuery SQL Agent — Demo</title>
</head>
<body style="margin:0;background:#f8fafc;font-family:sans-serif;">
  <div id="bq-agent-widget" data-api-url=""></div>
  <script>
    // Point the widget at this same origin so it works on any deployment
    document.getElementById('bq-agent-widget').dataset.apiUrl = window.location.origin;
  </script>
  <script src="/dist/bq-sql-agent.iife.js"></script>
</body>
</html>"""


@app.get("/")
async def root():
    return {"service": "BigQuery SQL Agent", "status": "ok"}
