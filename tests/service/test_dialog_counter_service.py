from uuid import uuid4

from app.core.services import DialogCounterService, DialogUtils
from app.core.utils import utcnow
from app.schemas.services import MessageSentEventSchema


def _message_sent_event() -> MessageSentEventSchema:
    return MessageSentEventSchema(
        recipient_id=uuid4(),
        sender_id=uuid4(),
        conversation_id=uuid4(),
        message_id=uuid4(),
        sent_at=utcnow(),
    )


async def test_increment_unread_on_message_sent_increments_counter(context):
    utils = DialogUtils()
    redis = context.redis_client
    event = _message_sent_event()

    unread_count = await utils.increment_unread_on_message_sent(event, redis)

    assert unread_count == 1
    assert await redis.hget(utils.unread_key(event.recipient_id), str(event.sender_id)) == b"1"
    assert await redis.exists(utils.processed_event_key(event.event_id)) == 1


async def test_increment_unread_on_message_sent_is_idempotent(context):
    utils = DialogUtils()
    redis = context.redis_client
    event = _message_sent_event()

    first = await utils.increment_unread_on_message_sent(event, redis)
    second = await utils.increment_unread_on_message_sent(event, redis)

    assert first == 1
    assert second is None
    assert await redis.hget(utils.unread_key(event.recipient_id), str(event.sender_id)) == b"1"


async def test_processing_dialog_message_handles_message_sent(context):
    service = DialogCounterService(context)
    event = _message_sent_event()

    response = await service.processing_dialog_message(schema=event)

    assert response.is_success is True
    assert (
        await context.redis_client.hget(
            DialogUtils().unread_key(event.recipient_id),
            str(event.sender_id),
        )
        == b"1"
    )


async def test_processing_dialog_message_skips_duplicate_message_sent(context):
    service = DialogCounterService(context)
    event = _message_sent_event()

    await service.processing_dialog_message(schema=event)
    response = await service.processing_dialog_message(schema=event)

    assert response.is_success is True
    assert (
        await context.redis_client.hget(
            DialogUtils().unread_key(event.recipient_id),
            str(event.sender_id),
        )
        == b"1"
    )
