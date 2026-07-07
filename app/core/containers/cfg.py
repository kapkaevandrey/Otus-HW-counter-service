from app.config import AppSettings, KafkaSettings, RedisSettings


class Config:
    def __init__(self, app: AppSettings, kafka: KafkaSettings, redis: RedisSettings):
        self._app = app
        self._kafka = kafka
        self._redis = redis

    @property
    def app(self) -> AppSettings:
        return self._app

    @property
    def kafka(self) -> KafkaSettings:
        return self._kafka

    @property
    def redis(self) -> RedisSettings:
        return self._redis
