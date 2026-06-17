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
    *, *::before, *::after { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #f8fafc; font-family: system-ui, -apple-system, sans-serif; display: flex; align-items: flex-start; justify-content: center; padding: 40px 16px; }
    #app { width: 100%; max-width: 680px; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px; box-shadow: 0 1px 4px rgba(0,0,0,.06); display: flex; flex-direction: column; gap: 20px; }
    h2 { margin: 0; font-size: 18px; font-weight: 600; color: #1a202c; letter-spacing: -0.01em; }
    p.sub { margin: 0; font-size: 13px; color: #718096; }
    #history { display: flex; flex-direction: column; gap: 16px; max-height: 420px; overflow-y: auto; }
    .q { align-self: flex-end; background: #2b6cb0; color: #fff; padding: 9px 14px; border-radius: 14px 14px 4px 14px; font-size: 14px; line-height: 1.5; max-width: 85%; }
    .a { align-self: flex-start; background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 14px 14px 14px 4px; padding: 12px 14px; font-size: 14px; line-height: 1.6; color: #2d3748; max-width: 95%; }
    .a p { margin: 0 0 10px; }
    details { border-radius: 8px; overflow: hidden; border: 1px solid #2d3748; margin-top: 4px; }
    summary { display: flex; align-items: center; justify-content: space-between; padding: 7px 12px; background: #2d3748; cursor: pointer; list-style: none; }
    summary span { color: #e2e8f0; font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
    .copy-btn { background: transparent; border: 1px solid #4a5568; border-radius: 5px; color: #a0aec0; font-size: 11px; padding: 2px 8px; cursor: pointer; }
    pre { margin: 0; padding: 14px 16px; background: #1a202c; color: #e2e8f0; font-size: 12.5px; font-family: "JetBrains Mono", Menlo, monospace; line-height: 1.65; overflow-x: auto; white-space: pre; }
    .err { align-self: flex-start; background: #fff5f5; border: 1px solid #fc8181; border-radius: 14px 14px 14px 4px; padding: 10px 14px; color: #c53030; font-size: 13px; max-width: 90%; }
    .loading { align-self: flex-start; display: flex; align-items: center; gap: 8px; background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 14px 14px 14px 4px; padding: 10px 14px; font-size: 13px; color: #718096; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner { display: inline-block; width: 13px; height: 13px; border: 2px solid #cbd5e0; border-top-color: #2b6cb0; border-radius: 50%; animation: spin .7s linear infinite; flex-shrink: 0; }
    #input-row { display: flex; gap: 8px; }
    input { flex: 1; padding: 10px 14px; font-size: 14px; border: 1px solid #cbd5e0; border-radius: 8px; outline: none; color: #1a202c; }
    input:focus { border-color: #2b6cb0; }
    button#ask { padding: 10px 20px; font-size: 14px; font-weight: 600; background: #2b6cb0; color: #fff; border: none; border-radius: 8px; cursor: pointer; white-space: nowrap; }
    button#ask:disabled { background: #a0aec0; cursor: not-allowed; }
  </style>
</head>
<body>
  <div id="app">
    <div>
      <h2>Ask the Citibike Data</h2>
      <p class="sub">Powered by Gemini · LangGraph · BigQuery</p>
    </div>
    <div id="history" style="display:none"></div>
    <div id="input-row">
      <input id="q" type="text" placeholder="e.g. Which stations were busiest in July 2018?" autocomplete="off" />
      <button id="ask">Ask</button>
    </div>
  </div>

  <script>
    const API = window.location.origin;
    const history = document.getElementById('history');
    const input = document.getElementById('q');
    const btn = document.getElementById('ask');
    const STEPS = ['Fetching schema…','Drafting query…','Validating SQL…','Running on BigQuery…'];

    function addEl(tag, cls, parent) {
      const el = document.createElement(tag);
      if (cls) el.className = cls;
      if (parent) parent.appendChild(el);
      return el;
    }

    async function ask() {
      const q = input.value.trim();
      if (!q) return;
      input.value = '';
      btn.disabled = true;
      history.style.display = 'flex';
      history.style.flexDirection = 'column';
      history.style.gap = '16px';

      const qDiv = addEl('div', 'q', history);
      qDiv.textContent = q;

      const loadDiv = addEl('div', 'loading', history);
      const spinner = addEl('span', 'spinner', loadDiv);
      const stepTxt = addEl('span', '', loadDiv);
      stepTxt.textContent = STEPS[0];
      let si = 0;
      const timer = setInterval(() => { si = Math.min(si+1, STEPS.length-1); stepTxt.textContent = STEPS[si]; }, 1800);

      history.scrollTop = history.scrollHeight;

      try {
        const res = await fetch(API + '/query', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({question: q})
        });
        const data = await res.json();
        clearInterval(timer);
        loadDiv.remove();

        if (!res.ok) throw new Error(data.detail || 'HTTP ' + res.status);

        const aDiv = addEl('div', 'a', history);
        const p = addEl('p', '', aDiv);
        p.textContent = data.answer;

        if (data.sql) {
          const det = addEl('details', '', aDiv);
          const sum = addEl('summary', '', det);
          const label = addEl('span', '', sum);
          label.textContent = 'SQL';
          const copyBtn = addEl('button', 'copy-btn', sum);
          copyBtn.textContent = 'Copy';
          copyBtn.onclick = (e) => { e.preventDefault(); navigator.clipboard.writeText(data.sql).then(() => { copyBtn.textContent='Copied!'; setTimeout(()=>copyBtn.textContent='Copy',1800); }); };
          const pre = addEl('pre', '', det);
          pre.textContent = data.sql;
        }
      } catch(e) {
        clearInterval(timer);
        loadDiv.remove();
        const errDiv = addEl('div', 'err', history);
        errDiv.textContent = e.message || 'Request failed';
      }

      btn.disabled = false;
      input.focus();
      history.scrollTop = history.scrollHeight;
    }

    btn.onclick = ask;
    input.onkeydown = (e) => { if (e.key === 'Enter') ask(); };
  </script>
</body>
</html>"""


@app.get("/")
async def root():
    return {"service": "BigQuery SQL Agent", "status": "ok"}
