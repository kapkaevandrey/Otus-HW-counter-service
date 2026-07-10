from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import Field

from app.core.enums import DialogEventType
from app.schemas.base import EmptyBaseSchema


class MessageSentEventSchema(EmptyBaseSchema):
    event_id: UUID = Field(default_factory=uuid4)
    type: Literal[DialogEventType.MESSAGE_SENT] = DialogEventType.MESSAGE_SENT
    recipient_id: UUID
    sender_id: UUID
    conversation_id: UUID
    message_id: UUID
    sent_at: dt.datetime


class DialogReadEventSchema(EmptyBaseSchema):
    event_id: UUID = Field(default_factory=uuid4)
    type: Literal[DialogEventType.DIALOG_READ] = DialogEventType.DIALOG_READ
    user_id: UUID
    peer_id: UUID
    conversation_id: UUID
    read_at: dt.datetime


DialogCounterEvent = Annotated[
    MessageSentEventSchema | DialogReadEventSchema,
    Field(discriminator="type"),
]
