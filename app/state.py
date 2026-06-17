from typing import Optional, Any
from typing_extensions import TypedDict


class AgentState(TypedDict):
    question: str
    schema: str
    sql: str
    error: Optional[str]
    attempts: int
    result: Optional[list[dict[str, Any]]]
    answer: str
