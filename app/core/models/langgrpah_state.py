from typing import TypedDict, Annotated, Literal
from langgraph.graph import add_messages


class LangGraphState(TypedDict):

    messages: Annotated[list, add_messages]

    goal: str

    plan: list[str]

    current_step: int

    next_action: Literal[
        "tool",
        "agent",
        "exit"
    ]

    iterations: int