from functools import cached_property

from app.core.enums import DialogEventType
from app.core.services.base import BaseService, async_use_case
from app.schemas.services import BaseServiceResponse, DialogCounterEvent, DialogReadEventSchema, MessageSentEventSchema

from .utils import DialogUtils


class DialogCounterService(BaseService):
    @cached_property
    def utils(self) -> DialogUtils:
        return DialogUtils()

    @async_use_case()
    async def processing_dialog_message(self, schema: DialogCounterEvent) -> BaseServiceResponse[None]:
        if schema.type == DialogEventType.MESSAGE_SENT:
            await self._handle_message_sent(schema)
        elif schema.type == DialogEventType.DIALOG_READ:
            await self._handle_dialog_read(schema)
        return BaseServiceResponse[None]()

    async def _handle_message_sent(self, schema: MessageSentEventSchema) -> None:
        unread_count = await self.utils.increment_unread_on_message_sent(schema, self.context.redis_client)
        message = "Incremented unread counter"
        extra = {
            "event_id": str(schema.event_id),
            "recipient_id": str(schema.recipient_id),
            "sender_id": str(schema.sender_id),
            "unread_count": unread_count,
        }
        if unread_count is None:
            message = "Skip duplicate message.sent event"
            extra = {"event_id": str(schema.event_id), "recipient_id": str(schema.recipient_id)}
        self.logger.info(message, extra=extra)

    async def _handle_dialog_read(self, schema: DialogReadEventSchema) -> None:
        reset_result = await self.utils.reset_unread_on_dialog_read(schema, self.context.redis_client)
        message = "Reset unread counter"
        extra = {
            "event_id": str(schema.event_id),
            "user_id": str(schema.user_id),
            "peer_id": str(schema.peer_id),
            "unread_count": reset_result,
        }
        if reset_result is None:
            message = "Skip duplicate dialog.read event"
            extra = {"event_id": str(schema.event_id), "user_id": str(schema.user_id)}
        self.logger.info(message, extra=extra)
