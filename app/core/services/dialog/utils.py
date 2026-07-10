from uuid import UUID

from app.config import redis_settings
from app.core.clients import RedisClient
from app.core.services.utils import ServiceUtils
from app.schemas.services import MessageSentEventSchema


class DialogUtils(ServiceUtils):
    UNREAD_KEY_PREFIX = redis_settings.REDIS_UNREAD_KEY_PREFIX
    PROCESSED_EVENT_KEY_PREFIX = redis_settings.REDIS_PROCESSED_EVENT_KEY_PREFIX
    PROCESSED_EVENT_TTL_SEC = redis_settings.REDIS_PROCESSED_EVENT_TTL_SEC

    def unread_key(self, user_id: UUID) -> str:
        return f"{self.UNREAD_KEY_PREFIX}:{user_id}"

    def processed_event_key(self, event_id: UUID) -> str:
        return f"{self.PROCESSED_EVENT_KEY_PREFIX}:{event_id}"

    async def increment_unread_on_message_sent(
        self,
        event: MessageSentEventSchema,
        redis_client: RedisClient,
    ) -> int | None:
        return await redis_client.increment_unread_on_message_sent(
            processed_event_key=self.processed_event_key(event.event_id),
            unread_key=self.unread_key(event.recipient_id),
            sender_id=str(event.sender_id),
            processed_ttl_sec=self.PROCESSED_EVENT_TTL_SEC,
        )
