from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    message: str
    project_id: UUID | None = None


class ChatCreate(BaseModel):
    project_id: UUID | None = None
    title: str | None = None


class ChatUpdate(BaseModel):
    title: str | None = None
    project_id: UUID | None = None


class ChatResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    role: str
    content: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StartChatResponse(BaseModel):
    chat_id: UUID
    title: str
    message: MessageResponse


class SendMessageResponse(BaseModel):
    chat_id: UUID
    message: MessageResponse