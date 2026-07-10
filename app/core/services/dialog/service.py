from functools import cached_property

from app.core.enums import DialogEventType
from app.core.services.base import BaseService, async_use_case
from app.schemas.services import BaseServiceResponse, DialogCounterEvent, MessageSentEventSchema

from .utils import DialogUtils


class DialogCounterService(BaseService):
    @cached_property
    def utils(self) -> DialogUtils:
        return DialogUtils()

    @async_use_case()
    async def processing_dialog_message(self, schema: DialogCounterEvent) -> BaseServiceResponse[None]:
        if schema.type == DialogEventType.MESSAGE_SENT:
            await self._handle_message_sent(schema)

        return BaseServiceResponse[None]()

    async def _handle_message_sent(self, schema: MessageSentEventSchema) -> None:
        unread_count = await self.utils.increment_unread_on_message_sent(
            schema,
            self.context.redis_client,
        )
        if unread_count is None:
            self.logger.info(
                "Skip duplicate message.sent event",
                extra={"event_id": str(schema.event_id), "recipient_id": str(schema.recipient_id)},
            )
            return

        self.logger.info(
            "Incremented unread counter",
            extra={
                "event_id": str(schema.event_id),
                "recipient_id": str(schema.recipient_id),
                "sender_id": str(schema.sender_id),
                "unread_count": unread_count,
            },
        )
