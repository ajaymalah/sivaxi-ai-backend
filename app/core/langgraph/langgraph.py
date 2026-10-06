from dataclasses import dataclass
from typing import TypedDict, Annotated

from langgraph.graph import (
    StateGraph,
    START,
    END,
    add_messages,
)
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres import PostgresSaver

from app.core.tools.terminal import terminal
from app.core.tools.memory import MEMORY_TOOLS
from app.core.tools.search_web import search_web
from app.core.tools.block_user import block_user

from app.core.llms.gemini_llm import GeminiLLM
from app.core.constants.constants import ADMIN_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT, PORTFOLIO_SYSTEM_PROMPT

DB_URI = "postgresql://postgres:postgres@localhost:5432/data_intellijence"


@dataclass
class GraphContext:
    user_id: str
    username: str | None
    roles: list[str]
    chat_id: str
    project_id: str | None = None


class LangGraphState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    chat_id: str
    project_id: str | None
    iterations: int


class AppLangGraph:

    def __init__(self):

        gemini = GeminiLLM()

        self.llm = gemini.bind_tools([
            terminal,
            block_user,
            search_web,
            *MEMORY_TOOLS,
        ])

        self.title_llm = GeminiLLM()

        self.lang_graph = StateGraph(
            LangGraphState
        )

        self.add_nodes()
        self.add_edges()

        self.checkpointer_context = (
            PostgresSaver.from_conn_string(
                DB_URI
            )
        )

        self.checkpointer = (
            self.checkpointer_context.__enter__()
        )

        self.checkpointer.setup()

        self.graph = self.lang_graph.compile(
            checkpointer=self.checkpointer
        )

    # ============================================================
    # NODES
    # ============================================================

    def add_nodes(self):

        self.lang_graph.add_node(
            "agent",
            self.agent,
        )

        self.lang_graph.add_node(
            "tools",
            ToolNode([
                terminal,
                block_user,
                search_web,
                *MEMORY_TOOLS,
            ]),
        )

    # ============================================================
    # EDGES
    # ============================================================

    def add_edges(self):

        self.lang_graph.add_edge(
            START,
            "agent",
        )

        self.lang_graph.add_conditional_edges(
            "agent",
            self.route_after_agent,
            {
                "tools": "tools",
                "end": END,
            },
        )

        self.lang_graph.add_edge(
            "tools",
            "agent",
        )

    # ============================================================
    # AGENT
    # ============================================================

    def agent(
            self,
            state: LangGraphState,
            runtime
    ):
        iterations = state.get(
            "iterations",
            0
        )

        context = self.build_context(state)

        system_prompt = self.get_system_prompt(
            runtime.context.roles
        )

        response = self.llm.invoke(
            context,
            system_prompt=system_prompt
        )

        return {
            "messages": [response],
            "iterations": iterations + 1
        }

    # ============================================================
    # BUILD CONTEXT
    # ============================================================

    def build_context(
        self,
        state: LangGraphState,
    ):

        messages = state["messages"]

        max_messages = 20

        if len(messages) <= max_messages:

            recent_messages = messages

        else:

            candidate_messages = messages[
                -max_messages:
            ]

            first_human_index = next(
                (
                    index
                    for index, message
                    in enumerate(candidate_messages)
                    if message.type == "human"
                ),
                0,
            )

            recent_messages = candidate_messages[
                first_human_index:
            ]

        print("\n========== CONTEXT ==========")

        print(
            "TOTAL MESSAGES:",
            len(messages),
        )

        print(
            "MESSAGES SENT TO GEMINI:",
            len(recent_messages),
        )

        for i, message in enumerate(
            recent_messages
        ):

            content = message.content

            if not isinstance(
                content,
                str,
            ):
                content = str(content)

            print(
                i,
                message.type,
                content[:100],
                "TOOL_CALLS:",
                getattr(
                    message,
                    "tool_calls",
                    None,
                ),
            )

        print("=============================\n")

        return recent_messages

    # ============================================================
    # ROUTING
    # ============================================================

    def route_after_agent(
        self,
        state: LangGraphState,
    ):

        iterations = state.get(
            "iterations",
            0,
        )

        # Safety limit
        if iterations >= 10:
            return "end"

        last_message = state["messages"][-1]

        # Agent requested a tool
        if last_message.tool_calls:
            return "tools"

        # Normal answer → finish
        return "end"

    # ============================================================
    # CHAT
    # ============================================================

    def chat(
        self,
        user_id: str,
        username: str | None,
        roles: list[str],
        chat_id: str,
        message: str,
        project_id: str | None = None,
    ):

        config = {
            "configurable": {
                "thread_id": chat_id,
            }
        }

        print("\n==============================")
        print("CHAT")
        print(
            "GRAPH INSTANCE:",
            id(self),
        )
        print(
            "THREAD ID:",
            chat_id,
        )
        print(
            "USERNAME:",
            username,
        )
        print(
            "ROLES:",
            roles,
        )

        before = self.graph.get_state(
            config
        )

        print("BEFORE STATE:")
        print(before.values)

        result = self.graph.invoke(
            {
                "messages": [
                    ("user", message),
                ],
                "user_id": user_id,
                "chat_id": chat_id,
                "project_id": project_id,
                "iterations": 0,
            },
            config=config,
            context=GraphContext(
                user_id=user_id,
                username=username,
                roles=roles,
                chat_id=chat_id,
                project_id=project_id,
            ),
        )

        after = self.graph.get_state(
            config
        )

        print("AFTER STATE:")
        print(after.values)

        print("==============================\n")

        last_message = result["messages"][-1]

        return {
            "message": {
                "type": "text",
                "content": last_message.content,
            },
            "chat_id": chat_id,
        }

    # ============================================================
    # GENERATE TITLE
    # ============================================================

    def generate_title(
        self,
        message: str,
    ) -> str:

        prompt = f"""
Generate a short title for a conversation based on
the user's first message.

Rules:
- Maximum 6 words
- Clear and meaningful
- No quotes
- No emojis
- Return only the title

User message:
{message}
"""

        response = self.title_llm.invoke(
            [("user", prompt)]
        )

        content = response.content

        if isinstance(
            content,
            list,
        ):

            text = ""

            for item in content:

                if (
                    isinstance(item, dict)
                    and "text" in item
                ):
                    text += item["text"]

            return text.strip()

        return content.strip()

    def get_system_prompt(
            self,
            roles: list[str]
    ) -> str:

        if "admin" in roles:
            return ADMIN_SYSTEM_PROMPT

        if "portfolio" in roles:
            return PORTFOLIO_SYSTEM_PROMPT

        return DEFAULT_SYSTEM_PROMPT