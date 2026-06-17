from google.oauth2 import service_account
from google import genai
from google.genai import types

from app.state import AgentState
from app.config import MODEL, VERTEX_LOCATION, BQ_BILLING_PROJECT
from app.prompts import ANSWER_SYSTEM

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def _get_client() -> genai.Client:
    import os
    key_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_file:
        creds = service_account.Credentials.from_service_account_file(key_file, scopes=_SCOPES)
    else:
        import google.auth
        creds, _ = google.auth.default(scopes=_SCOPES)
    return genai.Client(vertexai=True, project=BQ_BILLING_PROJECT, location=VERTEX_LOCATION, credentials=creds)


def answer_node(state: AgentState) -> dict:
    if state.get("error"):
        answer = (
            f"I was unable to answer your question after {state.get('attempts', 1)} attempt(s).\n"
            f"Last error: {state['error']}"
        )
        if state.get("sql"):
            answer += f"\nLast SQL attempted:\n{state['sql']}"
        return {"answer": answer}

    rows = state.get("result") or []
    rows_text = "\n".join(str(row) for row in rows[:20])
    if len(rows) > 20:
        rows_text += f"\n... ({len(rows) - 20} more rows)"

    client = _get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=(
            f"Question: {state['question']}\n\n"
            f"SQL:\n{state['sql']}\n\n"
            f"Results ({len(rows)} rows):\n{rows_text}"
        ),
        config=types.GenerateContentConfig(
            system_instruction=ANSWER_SYSTEM,
            temperature=0,
        ),
    )

    return {"answer": response.text.strip()}
