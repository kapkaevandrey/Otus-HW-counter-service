from uuid import UUID

from app.schemas.base import EmptyBaseSchema


class UnreadPeerCounter(EmptyBaseSchema):
    peer_id: UUID
    count: int


class UnreadCountersResult(EmptyBaseSchema):
    user_id: UUID
    total: int
    by_peer: list[UnreadPeerCounter]
