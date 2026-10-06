from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session

from app.core.db.database import get_db
from app.core.security.security import get_current_user
from app.controllers.chat.dto.chat import (
    ChatRequest,
    ChatResponse,
    ChatCreate,
    ChatUpdate,
    MessageResponse,
    StartChatResponse,
    SendMessageResponse,
)
from app.models.message import Message
from app.services.chat_service import ChatService
from app.core.langgraph.langgraph import AppLangGraph


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


# ============================================================
# START NEW CHAT
# ============================================================

@router.post(
    "",
    response_model=StartChatResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def start_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ChatService(db)

    # 1. Create chat with optional project
    chat = service.create_chat(
        current_user=current_user,
        request=ChatCreate(
            project_id=request.project_id,
        ),
    )

    if chat is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # 2. Run AI + generate title
    app_lang_graph = AppLangGraph()

    title = app_lang_graph.generate_title(
        request.message
    )

    chat.title = title

    db.commit()
    db.refresh(chat)

    # 3. Save user message
    user_message = Message(
        chat_id=chat.id,
        role="user",
        content={
            "type": "text",
            "content": request.message,
        },
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # 4. Run Vixi
    response = app_lang_graph.chat(
        user_id=current_user["sub"],
        username=current_user.get(
            "preferred_username"
        ),
        roles=current_user.get(
            "realm_access",
            {},
        ).get(
            "roles",
            [],
        ),
        chat_id=str(chat.id),
        message=request.message,
        project_id=(
            str(chat.project_id)
            if chat.project_id
            else None
        ),
    )

    # 5. Save assistant message
    assistant_message = Message(
        chat_id=chat.id,
        role="assistant",
        content=response["message"],
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # 6. Return persisted assistant message
    return {
        "chat_id": chat.id,
        "title": chat.title,
        "message": assistant_message,
    }


# ============================================================
# CONTINUE EXISTING CHAT
# ============================================================

@router.post(
    "/{chat_id}/messages",
    response_model=SendMessageResponse,
)
def send_message(
    chat_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ChatService(db)

    # 1. Verify chat belongs to current user
    chat = service.get_chat(
        current_user=current_user,
        chat_id=chat_id,
    )

    if chat is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    # 2. Save user message
    user_message = Message(
        chat_id=chat.id,
        role="user",
        content={
            "type": "text",
            "content": request.message,
        },
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # 3. Run Vixi
    app_lang_graph = AppLangGraph()

    response = app_lang_graph.chat(
        user_id=current_user["sub"],
        username=current_user.get(
            "preferred_username"
        ),
        roles=current_user.get(
            "realm_access",
            {},
        ).get(
            "roles",
            [],
        ),
        chat_id=str(chat.id),
        message=request.message,
        project_id=(
            str(chat.project_id)
            if chat.project_id
            else None
        ),
    )

    # 4. Save assistant message
    assistant_message = Message(
        chat_id=chat.id,
        role="assistant",
        content=response["message"],
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # 5. Return persisted assistant message
    return {
        "chat_id": chat.id,
        "message": assistant_message,
    }


# ============================================================
# GET CHATS
# ============================================================

@router.get(
    "",
    response_model=list[ChatResponse],
)
def get_chats(
    project_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ChatService(db)

    return service.get_chats(
        current_user=current_user,
        project_id=project_id,
    )


# ============================================================
# GET SINGLE CHAT
# ============================================================

@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
)
def get_chat(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ChatService(db)

    chat = service.get_chat(
        current_user=current_user,
        chat_id=chat_id,
    )

    if chat is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return chat


# ============================================================
# UPDATE CHAT
# ============================================================

@router.patch(
    "/{chat_id}",
    response_model=ChatResponse,
)
def update_chat(
    chat_id: UUID,
    request: ChatUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ChatService(db)

    chat = service.update_chat(
        current_user=current_user,
        chat_id=chat_id,
        request=request,
    )

    if chat is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Chat or project not found",
        )

    return chat


# ============================================================
# DELETE CHAT
# ============================================================

@router.delete(
    "/{chat_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
def delete_chat(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ChatService(db)

    deleted = service.delete_chat(
        current_user=current_user,
        chat_id=chat_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )


# ============================================================
# GET LAST 20 MESSAGES
# ============================================================

@router.get(
    "/{chat_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ChatService(db)

    # 1. Verify chat ownership
    chat = service.get_chat(
        current_user=current_user,
        chat_id=chat_id,
    )

    if chat is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    # 2. Get latest 20 messages
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(20)
        .all()
    )

    # 3. Return chronological order
    messages.reverse()

    return messages