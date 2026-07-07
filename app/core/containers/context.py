from logging import Logger, getLogger

from app.config import app_settings, kafka_settings, redis_settings
from app.core.clients import RedisClient

from .cfg import Config


class Context:
    def __init__(
        self,
        redis_client: RedisClient,
        cfg: Config,
        logger: Logger | None = None,
    ) -> None:
        self._redis_client = redis_client
        self._cfg = cfg
        self._logger = logger or getLogger(__name__)

    @property
    def redis_client(self) -> RedisClient:
        return self._redis_client

    @property
    def cfg(self) -> Config:
        return self._cfg

    @property
    def logger(self) -> Logger:
        return self._logger

    async def start_clients(self):
        """Start all clients if that need"""
        pass

    async def stop_clients(self):
        """Stop all clients if that need"""
        pass


context = Context(
    redis_client=RedisClient.from_settings(redis_settings),
    cfg=Config(app=app_settings, kafka=kafka_settings, redis=redis_settings),
    logger=getLogger(__name__),
)


def get_context() -> Context:
    return context
