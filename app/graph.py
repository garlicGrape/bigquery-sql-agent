import sys
from langgraph.graph import StateGraph, START, END

from app.state import AgentState
from app.config import MAX_RETRIES
from app.nodes.schema import schema_node
from app.nodes.draft import draft_node
from app.nodes.validate import validate_node
from app.nodes.execute import execute_node
from app.nodes.answer import answer_node


def _route_after_validate(state: AgentState) -> str:
    if state.get("error"):
        return "draft" if state["attempts"] < MAX_RETRIES else "answer"
    return "execute"


def _route_after_execute(state: AgentState) -> str:
    if state.get("error"):
        return "draft" if state["attempts"] < MAX_RETRIES else "answer"
    return "answer"


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("schema", schema_node)
    workflow.add_node("draft", draft_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("answer", answer_node)

    workflow.add_edge(START, "schema")
    workflow.add_edge("schema", "draft")
    workflow.add_edge("draft", "validate")
    workflow.add_conditional_edges(
        "validate",
        _route_after_validate,
        {"execute": "execute", "draft": "draft", "answer": "answer"},
    )
    workflow.add_conditional_edges(
        "execute",
        _route_after_execute,
        {"answer": "answer", "draft": "draft"},
    )
    workflow.add_edge("answer", END)

    return workflow.compile()


graph = build_graph()


if __name__ == "__main__":
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Which Citibike stations were busiest in July 2018?"
    )
    initial: AgentState = {
        "question": question,
        "schema": "",
        "sql": "",
        "error": None,
        "attempts": 0,
        "result": None,
        "answer": "",
    }
    result = graph.invoke(initial)
    print(result["answer"])
    print(f"\nSQL:\n{result['sql']}")
