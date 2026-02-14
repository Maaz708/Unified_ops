# app/api/routers/inbox.py
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from app.api.dependencies.db import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.message import StaffSendMessageRequest, MessageOut
from app.services.inbox_service import InboxService
from app.models.conversation import Conversation
from app.models.contact import Contact
from app.models.message import Message, MessageDirection

router = APIRouter(prefix="/inbox", tags=["inbox"])


class ConversationListItem(BaseModel):
    id: UUID
    contact_name: str | None
    contact_id: UUID
    last_message_at: datetime | None

    class Config:
        from_attributes = True


class MessageListItem(BaseModel):
    id: UUID
    direction: MessageDirection
    body_text: str
    subject: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ReplyRequest(BaseModel):
    body: str


def _workspace_from_user(current_user: dict) -> UUID:
    wid = current_user.get("workspace_id")
    if not wid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace")
    return UUID(wid) if isinstance(wid, str) else wid


@router.get("/conversations", response_model=list[ConversationListItem])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    workspace_id = _workspace_from_user(current_user)
    convs = db.execute(
        select(Conversation, Contact)
        .join(Contact, Conversation.contact_id == Contact.id)
        .where(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted.is_(False),
        )
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.updated_at.desc())
    ).all()
    return [
        ConversationListItem(
            id=c.id,
            contact_name=contact.full_name,
            contact_id=contact.id,
            last_message_at=c.last_message_at,
        )
        for c, contact in convs
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageListItem])
def list_conversation_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    workspace_id = _workspace_from_user(current_user)
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    messages = list(
        db.scalars(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.workspace_id == workspace_id,
            )
            .order_by(Message.created_at.asc())
        ).all()
    )
    return [MessageListItem(
        id=m.id,
        direction=m.direction,
        body_text=m.body_text,
        subject=m.subject,
        created_at=m.created_at,
    ) for m in messages]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_reply(
    conversation_id: UUID,
    payload: ReplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    workspace_id = _workspace_from_user(current_user)
    service = InboxService(db)
    staff_id = UUID("00000000-0000-0000-0000-000000000000")
    return service.send_reply_by_conversation(
        workspace_id, staff_id, conversation_id, payload.body, background_tasks
    )


@router.post(
    "/workspaces/{workspace_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_staff_message(
    workspace_id: UUID,
    payload: StaffSendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = InboxService(db)
    staff_id = UUID("00000000-0000-0000-0000-000000000000")
    return service.send_message(workspace_id, staff_id, payload, background_tasks)