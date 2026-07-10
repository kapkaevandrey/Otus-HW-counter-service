import logging
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import app_settings, kafka_settings, redis_settings
from app.core.clients import RedisClient
from app.core.containers.cfg import Config as AppConfig
from app.core.containers.context import Context, get_context
from app.server import app


@pytest.fixture(autouse=True, scope="session")
def enable_log_propagation_for_tests():
    """
    Временно включает propagate=True для всех логгеров, чтобы caplog их ловил.
    Работает для всех логгеров в тестах.
    """
    loggers = logging.root.manager.loggerDict
    old_values = {}
    for name, logger in loggers.items():
        if not isinstance(logger, logging.Logger):
            continue
        old_values[name] = logger.propagate
        logger.propagate = True
    try:
        yield
    finally:
        for name, logger in loggers.items():
            if isinstance(logger, logging.Logger) and name in old_values:
                logger.propagate = old_values[name]


@pytest.fixture(scope="session", autouse=True)
async def load_redis_scripts():
    from app.config import REDIS_SCRIPTS_PATH

    client = RedisClient.from_settings(redis_settings)
    for script_path in REDIS_SCRIPTS_PATH.glob("*.lua"):
        await client.script_load(script_path.read_text(encoding="utf-8"))
    await client.aclose()


@pytest.fixture
async def redis_client() -> AsyncGenerator[RedisClient, Any]:
    client = RedisClient.from_settings(redis_settings)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest.fixture()
async def context(redis_client) -> Context:
    return Context(
        redis_client=redis_client,
        cfg=AppConfig(app=app_settings, kafka=kafka_settings, redis=redis_settings),
    )


@pytest.fixture
async def client(context):
    def _get_context():
        return context

    app.dependency_overrides[get_context] = _get_context

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
