from app.state import AgentState
from app.bigquery import get_schema
from app.prompts import build_schema_description


def schema_node(state: AgentState) -> dict:
    raw = get_schema()
    return {"schema": build_schema_description(raw)}
