from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.core.memory.mem0_memory import Mem0Memory

memory = Mem0Memory()


@tool
def memory_search(
    query: str,
    user_id: Annotated[str, InjectedState("user_id")],
    project_id: Annotated[str | None, InjectedState("project_id")]
) -> str:
    """
    Search long-term memory for information relevant to the
    current user or project.
    """

    print("\n========== MEMORY SEARCH ==========")
    print("USER:", user_id)
    print("PROJECT:", project_id)
    print("QUERY:", query)

    result = memory.search(
        query=query,
        user_id=user_id,
        project_id=project_id
    )

    print("RESULT:", result)
    print("===================================\n")

    return str(result)


@tool
def memory_save(
    content: str,
    user_id: Annotated[str, InjectedState("user_id")],
    project_id: Annotated[str | None, InjectedState("project_id")]
) -> str:
    """
    Save important information to long-term memory when it may be
    useful in future conversations.
    """

    print("\n=========== MEMORY SAVE ===========")
    print("USER:", user_id)
    print("PROJECT:", project_id)
    print("CONTENT:", content)

    result = memory.save(
        content=content,
        user_id=user_id,
        project_id=project_id
    )

    print("RESULT:", result)
    print("===================================\n")

    return str(result)


MEMORY_TOOLS = [
    memory_search,
    memory_save
]