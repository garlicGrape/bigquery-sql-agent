from google.oauth2 import service_account
from google import genai
from google.genai import types

from app.state import AgentState
from app.config import MODEL, VERTEX_LOCATION, BQ_BILLING_PROJECT
from app.prompts import DRAFT_SYSTEM

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


def draft_node(state: AgentState) -> dict:
    attempts = state.get("attempts", 0) + 1

    system_content = DRAFT_SYSTEM.format(schema_description=state["schema"])

    human_parts = [f"Question: {state['question']}"]
    if state.get("error"):
        human_parts.append(
            f"\nThe previous SQL attempt failed with this error — fix it:\n{state['error']}"
        )
    if state.get("sql"):
        human_parts.append(f"\nPrevious SQL:\n{state['sql']}")

    client = _get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents="\n".join(human_parts),
        config=types.GenerateContentConfig(
            system_instruction=system_content,
            temperature=0,
        ),
    )

    sql = response.text.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    return {"sql": sql, "error": None, "attempts": attempts}
