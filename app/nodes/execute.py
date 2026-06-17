from app.state import AgentState
from app.bigquery import execute_query


def execute_node(state: AgentState) -> dict:
    rows, error = execute_query(state["sql"])
    if error:
        return {"error": f"Query execution failed: {error}", "result": None}
    return {"result": rows, "error": None}
