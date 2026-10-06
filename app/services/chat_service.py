from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db.database import get_db
from app.core.langgraph.langgraph import AppLangGraph
from app.controllers.chat.dto.chat import (
    ChatRequest,
    ChatResponse,
    ChatCreate,
    ChatUpdate,
)

from app.models.chat import Chat
from app.models.project import Project


class ChatService:

    def __init__(
        self,
        db: Session,
        app_lang_graph: AppLangGraph | None = None,
    ):
        self.db = db
        self.app_lang_graph = app_lang_graph or AppLangGraph()

    # ============================================================
    # CREATE CHAT
    # ============================================================

    def create_chat(
        self,
        current_user: dict,
        request: ChatCreate,
    ) -> Chat:

        user_id = current_user["sub"]

        # If a project is provided,
        # make sure it belongs to the current user.
        if request.project_id is not None:

            project = (
                self.db.query(Project)
                .filter(
                    Project.id == request.project_id,
                    Project.user_id == user_id,
                )
                .first()
            )

            if project is None:
                return None

        chat = Chat(
            user_id=user_id,
            project_id=request.project_id,
            title=request.title,
        )

        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)

        return chat

    # ============================================================
    # GET CHATS
    # ============================================================

    def get_chats(
        self,
        current_user: dict,
        project_id: UUID | None = None,
    ) -> list[Chat]:

        user_id = current_user["sub"]

        query = (
            self.db.query(Chat)
            .filter(Chat.user_id == user_id)
        )

        if project_id is not None:
            query = query.filter(
                Chat.project_id == project_id
            )

        return (
            query
            .order_by(Chat.updated_at.desc())
            .all()
        )

    # ============================================================
    # GET SINGLE CHAT
    # ============================================================

    def get_chat(
        self,
        current_user: dict,
        chat_id: UUID,
    ) -> Chat | None:

        user_id = current_user["sub"]

        return (
            self.db.query(Chat)
            .filter(
                Chat.id == chat_id,
                Chat.user_id == user_id,
            )
            .first()
        )

    # ============================================================
    # UPDATE CHAT
    # ============================================================

    def update_chat(
        self,
        current_user: dict,
        chat_id: UUID,
        request: ChatUpdate,
    ) -> Chat | None:

        user_id = current_user["sub"]

        chat = (
            self.db.query(Chat)
            .filter(
                Chat.id == chat_id,
                Chat.user_id == user_id,
            )
            .first()
        )

        if chat is None:
            return None

        if request.title is not None:
            chat.title = request.title

        if request.project_id is not None:

            project = (
                self.db.query(Project)
                .filter(
                    Project.id == request.project_id,
                    Project.user_id == user_id,
                )
                .first()
            )

            if project is None:
                return None

            chat.project_id = request.project_id

        self.db.commit()
        self.db.refresh(chat)

        return chat

    # ============================================================
    # DELETE CHAT
    # ============================================================

    def delete_chat(
        self,
        current_user: dict,
        chat_id: UUID,
    ) -> bool:

        user_id = current_user["sub"]

        chat = (
            self.db.query(Chat)
            .filter(
                Chat.id == chat_id,
                Chat.user_id == user_id,
            )
            .first()
        )

        if chat is None:
            return False

        self.db.delete(chat)
        self.db.commit()

        return True

    # ============================================================
    # CHAT
    # ============================================================

    def chat(
        self,
        request: ChatRequest,
        current_user: dict,
    ) -> ChatResponse:

        user_id = current_user["sub"]

        # Extract username from authenticated Keycloak token
        username = current_user.get(
            "preferred_username"
        )

        # Extract all realm roles from authenticated Keycloak token
        roles = current_user.get(
            "realm_access",
            {},
        ).get(
            "roles",
            [],
        )

        return self.app_lang_graph.chat(
            user_id=user_id,
            username=username,
            roles=roles,
            chat_id=request.chat_id,
            message=request.message,
            project_id=request.project_id,
        )

    # ============================================================
    # START CHAT
    # ============================================================

    def start_chat(
        self,
        current_user: dict,
        request: ChatRequest,
    ):
        user_id = current_user["sub"]

        chat = Chat(
            user_id=user_id,
        )

        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)

        return chat


# ============================================================
# LANGGRAPH DEPENDENCY
# ============================================================

app_lang_graph = AppLangGraph()


def get_app_lang_graph() -> AppLangGraph:
    return app_lang_graph


# ============================================================
# CHAT SERVICE DEPENDENCY
# ============================================================

def get_chat_service(
    db: Session = Depends(get_db),
    app_lang_graph: AppLangGraph = Depends(get_app_lang_graph),
) -> ChatService:

    return ChatService(
        db=db,
        app_lang_graph=app_lang_graph,
    )