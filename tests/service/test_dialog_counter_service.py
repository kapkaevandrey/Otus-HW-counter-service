from uuid import uuid4

from app.core.services import DialogCounterService, DialogUtils
from app.core.utils import utcnow
from app.schemas.services import DialogReadEventSchema, MessageSentEventSchema


def _message_sent_event() -> MessageSentEventSchema:
    return MessageSentEventSchema(
        recipient_id=uuid4(),
        sender_id=uuid4(),
        conversation_id=uuid4(),
        message_id=uuid4(),
        sent_at=utcnow(),
    )


def _dialog_read_event(*, user_id, peer_id) -> DialogReadEventSchema:
    return DialogReadEventSchema(
        user_id=user_id,
        peer_id=peer_id,
        conversation_id=uuid4(),
        read_at=utcnow(),
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


async def test_reset_unread_on_dialog_read_sets_counter_to_zero(context):
    utils = DialogUtils()
    redis = context.redis_client
    user_id = uuid4()
    peer_id = uuid4()
    unread_key = utils.unread_key(user_id)
    await redis.hset(unread_key, str(peer_id), 5)
    event = _dialog_read_event(user_id=user_id, peer_id=peer_id)

    reset_result = await utils.reset_unread_on_dialog_read(event, redis)

    assert reset_result == 0
    assert await redis.hget(unread_key, str(peer_id)) == b"0"
    assert await redis.exists(utils.processed_event_key(event.event_id)) == 1


async def test_reset_unread_on_dialog_read_is_idempotent(context):
    utils = DialogUtils()
    redis = context.redis_client
    user_id = uuid4()
    peer_id = uuid4()
    unread_key = utils.unread_key(user_id)
    await redis.hset(unread_key, str(peer_id), 3)
    event = _dialog_read_event(user_id=user_id, peer_id=peer_id)

    first = await utils.reset_unread_on_dialog_read(event, redis)
    second = await utils.reset_unread_on_dialog_read(event, redis)

    assert first == 0
    assert second is None
    assert await redis.hget(unread_key, str(peer_id)) == b"0"


async def test_processing_dialog_message_handles_dialog_read(context):
    service = DialogCounterService(context)
    user_id = uuid4()
    peer_id = uuid4()
    unread_key = DialogUtils().unread_key(user_id)
    await context.redis_client.hset(unread_key, str(peer_id), 2)
    event = _dialog_read_event(user_id=user_id, peer_id=peer_id)

    response = await service.processing_dialog_message(schema=event)

    assert response.is_success is True
    assert await context.redis_client.hget(unread_key, str(peer_id)) == b"0"


async def test_sequential_read_after_sent_resets_counter(context):
    service = DialogCounterService(context)
    user_id = uuid4()
    peer_id = uuid4()
    sent_event = MessageSentEventSchema(
        recipient_id=user_id,
        sender_id=peer_id,
        conversation_id=uuid4(),
        message_id=uuid4(),
        sent_at=utcnow(),
    )
    read_event = _dialog_read_event(user_id=user_id, peer_id=peer_id)
    unread_key = DialogUtils().unread_key(user_id)

    await service.processing_dialog_message(schema=sent_event)
    await service.processing_dialog_message(schema=read_event)

    assert await context.redis_client.hget(unread_key, str(peer_id)) == b"0"


async def test_sequential_sent_after_read_increments_counter(context):
    service = DialogCounterService(context)
    user_id = uuid4()
    peer_id = uuid4()
    sent_event = MessageSentEventSchema(
        recipient_id=user_id,
        sender_id=peer_id,
        conversation_id=uuid4(),
        message_id=uuid4(),
        sent_at=utcnow(),
    )
    read_event = _dialog_read_event(user_id=user_id, peer_id=peer_id)
    unread_key = DialogUtils().unread_key(user_id)

    await service.processing_dialog_message(schema=read_event)
    await service.processing_dialog_message(schema=sent_event)

    assert await context.redis_client.hget(unread_key, str(peer_id)) == b"1"
