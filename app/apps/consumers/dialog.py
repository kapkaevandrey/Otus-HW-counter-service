from functools import cached_property
from typing import Any

from aiokafka import ConsumerRecord
from pydantic import TypeAdapter, ValidationError

from app.core.clients import BaseKafkaConsumer
from app.core.containers import Context
from app.core.services import DialogCounterService
from app.schemas.services import DialogCounterEvent


_dialog_event_adapter: TypeAdapter[DialogCounterEvent] = TypeAdapter(DialogCounterEvent)


class DialogConsumer(BaseKafkaConsumer):
    def __init__(self, *args: Any, context: Context, **kwargs: Any) -> None:
        self._context = context
        super().__init__(*args, **kwargs)

    @property
    def context(self) -> Context:
        return self._context

    @cached_property
    def dialog_counter_service(self) -> DialogCounterService:
        return DialogCounterService(self.context)

    async def process_message(self, message: ConsumerRecord, context: Any = None) -> None:
        schema = self.try_get_message_schema(message.value)
        if schema is None:
            return

        service_response = await self.dialog_counter_service.processing_dialog_message(schema=schema)
        if service_response.is_success:
            self.logger.info("Successfully processing dialog counter message")
        else:
            self.logger.error(
                "Failed to processing dialog counter message",
                extra={
                    "error_message": service_response.error_message,
                    "error_details": service_response.error_details,
                },
            )

    def try_get_message_schema(self, data: bytes | str | dict) -> DialogCounterEvent | None:
        try:
            if isinstance(data, dict):
                return _dialog_event_adapter.validate_python(data)
            if isinstance(data, bytes):
                return _dialog_event_adapter.validate_json(data)
            return _dialog_event_adapter.validate_json(data)
        except ValidationError as error:
            self.logger.error(
                "Failed to validate dialog counter message. Data - %s",
                data.decode() if isinstance(data, bytes) else data,
                exc_info=error,
            )
        return None
