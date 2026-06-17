from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.state import AgentState
from app.config import MODEL
from app.prompts import ANSWER_SYSTEM


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

    llm = ChatAnthropic(model=MODEL, temperature=0)
    response = llm.invoke([
        SystemMessage(content=ANSWER_SYSTEM),
        HumanMessage(
            content=(
                f"Question: {state['question']}\n\n"
                f"SQL:\n{state['sql']}\n\n"
                f"Results ({len(rows)} rows):\n{rows_text}"
            )
        ),
    ])

    return {"answer": response.content.strip()}
