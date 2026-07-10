from uuid import uuid4

from app.core.services import DialogCounterService, DialogUtils


async def test_get_unread_counters_returns_total_and_breakdown(context):
    service = DialogCounterService(context)
    user_id = uuid4()
    peer_one = uuid4()
    peer_two = uuid4()
    unread_key = DialogUtils().unread_key(user_id)
    await context.redis_client.hset(unread_key, str(peer_one), 3)
    await context.redis_client.hset(unread_key, str(peer_two), 2)

    response = await service.get_unread_counters(user_id=user_id)

    assert response.is_success is True
    assert response.result.user_id == user_id
    assert response.result.total == 5
    by_peer = {item.peer_id: item.count for item in response.result.by_peer}
    assert by_peer == {peer_one: 3, peer_two: 2}


async def test_get_unread_counters_skips_zero_counters(context):
    service = DialogCounterService(context)
    user_id = uuid4()
    peer_one = uuid4()
    peer_two = uuid4()
    unread_key = DialogUtils().unread_key(user_id)
    await context.redis_client.hset(unread_key, str(peer_one), 4)
    await context.redis_client.hset(unread_key, str(peer_two), 0)

    response = await service.get_unread_counters(user_id=user_id)

    assert response.result.total == 4
    assert [item.peer_id for item in response.result.by_peer] == [peer_one]


async def test_get_unread_counters_empty_returns_zero(context):
    service = DialogCounterService(context)

    response = await service.get_unread_counters(user_id=uuid4())

    assert response.result.total == 0
    assert response.result.by_peer == []


async def test_get_unread_counters_endpoint(client, context):
    user_id = uuid4()
    peer_id = uuid4()
    await context.redis_client.hset(DialogUtils().unread_key(user_id), str(peer_id), 7)

    response = await client.get(f"/api/v1/counters/{user_id}/unread")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7
    assert body["by_peer"] == [{"peer_id": str(peer_id), "count": 7}]


async def test_get_unread_total_endpoint(client, context):
    user_id = uuid4()
    await context.redis_client.hset(DialogUtils().unread_key(user_id), str(uuid4()), 2)
    await context.redis_client.hset(DialogUtils().unread_key(user_id), str(uuid4()), 5)

    response = await client.get(f"/api/v1/counters/{user_id}/unread/total")

    assert response.status_code == 200
    assert response.json() == 7
