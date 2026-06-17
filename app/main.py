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
  <style>
    body { margin: 0; min-height: 100vh; background: #f8fafc; font-family: system-ui, sans-serif; display: flex; align-items: flex-start; justify-content: center; padding: 40px 16px; box-sizing: border-box; }
    #widget-wrap { width: 100%; max-width: 680px; }
    #status { padding: 12px; font-size: 13px; color: #718096; }
  </style>
</head>
<body>
  <div id="widget-wrap">
    <div id="status">Loading widget…</div>
    <div id="bq-agent-widget"></div>
  </div>
  <script>
    window.onerror = function(msg, src, line, col, err) {
      document.getElementById('status').style.display = 'block';
      document.getElementById('status').textContent = 'JS Error: ' + msg + ' (' + src + ':' + line + ')';
    };
    window.onunhandledrejection = function(e) {
      document.getElementById('status').style.display = 'block';
      document.getElementById('status').textContent = 'Promise Error: ' + e.reason;
    };
    var el = document.getElementById('bq-agent-widget');
    el.dataset.apiUrl = window.location.origin;
  </script>
  <script src="/dist/bq-sql-agent.iife.js"
    onload="document.getElementById('status').style.display='none'; setTimeout(function(){ if(!document.getElementById('bq-agent-widget').children.length){ document.getElementById('status').style.display='block'; document.getElementById('status').textContent='Widget loaded but rendered nothing — check console'; } }, 500);"
    onerror="document.getElementById('status').textContent='Error: could not load /dist/bq-sql-agent.iife.js (404?)'">
  </script>
</body>
</html>"""


@app.get("/")
async def root():
    return {"service": "BigQuery SQL Agent", "status": "ok"}
