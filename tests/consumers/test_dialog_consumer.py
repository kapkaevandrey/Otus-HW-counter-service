import json
from uuid import uuid4

from app.apps.consumers.dialog import DialogConsumer
from app.core.enums import DialogEventType
from app.schemas.services import DialogReadEventSchema, MessageSentEventSchema


def _get_consumer() -> DialogConsumer:
    return DialogConsumer(
        consumer_class=object,
        consumer_args=(),
        consumer_kwargs={},
        context=object(),
    )


def test_try_get_message_schema_parses_message_sent_from_dict_string_and_bytes():
    consumer = _get_consumer()
    raw = {
        "event_id": str(uuid4()),
        "type": DialogEventType.MESSAGE_SENT,
        "recipient_id": str(uuid4()),
        "sender_id": str(uuid4()),
        "conversation_id": str(uuid4()),
        "message_id": str(uuid4()),
        "sent_at": "2026-07-08T10:00:00Z",
    }

    parsed_from_dict = consumer.try_get_message_schema(raw)
    parsed_from_string = consumer.try_get_message_schema(json.dumps(raw))
    parsed_from_bytes = consumer.try_get_message_schema(json.dumps(raw).encode())

    assert isinstance(parsed_from_dict, MessageSentEventSchema)
    assert isinstance(parsed_from_string, MessageSentEventSchema)
    assert isinstance(parsed_from_bytes, MessageSentEventSchema)


def test_try_get_message_schema_parses_dialog_read():
    consumer = _get_consumer()
    raw = {
        "event_id": str(uuid4()),
        "type": DialogEventType.DIALOG_READ,
        "user_id": str(uuid4()),
        "peer_id": str(uuid4()),
        "conversation_id": str(uuid4()),
        "read_at": "2026-07-08T10:00:00Z",
    }

    parsed = consumer.try_get_message_schema(raw)

    assert isinstance(parsed, DialogReadEventSchema)


def test_try_get_message_schema_returns_none_for_invalid_payload():
    consumer = _get_consumer()

    assert consumer.try_get_message_schema(b"invalid-json") is None
    assert consumer.try_get_message_schema({"type": "unknown.event"}) is None
