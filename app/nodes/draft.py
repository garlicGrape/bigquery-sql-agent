from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.state import AgentState
from app.config import MODEL
from app.prompts import DRAFT_SYSTEM


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

    llm = ChatAnthropic(model=MODEL, temperature=0)
    response = llm.invoke([
        SystemMessage(content=system_content),
        HumanMessage(content="\n".join(human_parts)),
    ])

    sql = response.content.strip()
    # Strip markdown fences if the model adds them anyway
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    return {"sql": sql, "error": None, "attempts": attempts}
