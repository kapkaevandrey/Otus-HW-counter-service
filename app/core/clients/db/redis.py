from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ConnectionError, ResponseError

from app.config import REDIS_SCRIPTS_PATH, RedisSettings


class RedisClient(Redis):
    _scripts_sha_cache: dict[str, str]
    _lua_scripts: dict[str, str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scripts_sha_cache = {}
        self._lua_scripts = {
            "increment_unread_on_message_sent": (REDIS_SCRIPTS_PATH / "increment_unread_on_message_sent.lua").read_text(
                encoding="utf-8"
            ),
            "reset_unread_on_dialog_read": (REDIS_SCRIPTS_PATH / "reset_unread_on_dialog_read.lua").read_text(
                encoding="utf-8"
            ),
        }

    @classmethod
    def from_settings(cls, settings: RedisSettings) -> RedisClient:
        return cls(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_POOL_MAX_SIZE,
            retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
            retry_on_error=[ConnectionError],
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
            ssl=settings.REDIS_SSL,
            socket_connect_timeout=settings.REDIS_TIMEOUT_SEC,
            socket_timeout=settings.REDIS_TIMEOUT_SEC,
        )

    async def increment_unread_on_message_sent(
        self,
        *,
        processed_event_key: str,
        unread_key: str,
        sender_id: str,
        processed_ttl_sec: int,
    ) -> int | None:
        return await self._eval_counter_script(
            name="increment_unread_on_message_sent",
            keys=[processed_event_key, unread_key],
            args=[sender_id, str(processed_ttl_sec)],
        )

    async def reset_unread_on_dialog_read(
        self,
        *,
        processed_event_key: str,
        unread_key: str,
        peer_id: str,
        processed_ttl_sec: int,
    ) -> int | None:
        return await self._eval_counter_script(
            name="reset_unread_on_dialog_read",
            keys=[processed_event_key, unread_key],
            args=[peer_id, str(processed_ttl_sec)],
        )

    async def _eval_counter_script(self, *, name: str, keys: list[str], args: list[str]) -> int | None:
        raw = await self._run_evalsha(name, keys, args)
        if raw is None:
            return None
        return int(raw)

    async def _run_evalsha(self, name: str, keys: list[str], args: list[str]) -> Any:
        sha = self._scripts_sha_cache.get(name)
        if sha:
            try:
                return await self.evalsha(sha, len(keys), *keys, *args)
            except ResponseError as exc:
                if "NOSCRIPT" not in str(exc):
                    raise

        loaded_sha = await self.script_load(self._lua_scripts[name])
        self._scripts_sha_cache[name] = loaded_sha
        return await self.evalsha(loaded_sha, len(keys), *keys, *args)
