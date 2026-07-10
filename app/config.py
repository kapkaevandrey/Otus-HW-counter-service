from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_PATH = BASE_DIR / "scripts"
REDIS_SCRIPTS_PATH = SCRIPTS_PATH / "redis"


class EmptyBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow", env_file=".env")


class AppSettings(EmptyBaseSettings):
    SERVICE_NAME: str = "otus-social"
    ROOT_PATH: str = ""
    SERVICE_DESCRIPTION: str = "Otus Homework for social network"
    STAND: str = "dev"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOW_ORIGINS: str | None = None
    ENABLE_JSON_LOG: bool = True
    LOG_DEV: bool = False

    @property
    def allow_origins_list(self) -> list[str]:
        return self.ALLOW_ORIGINS.split(",") if self.ALLOW_ORIGINS else []


class RedisSettings(EmptyBaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_SSL: bool = False
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: str = ""
    REDIS_POOL_MAX_SIZE: int = 50
    REDIS_TIMEOUT_SEC: int = 30
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_DEFAULT_SETTINGS_TTL: int = 24 * 60 * 60
    REDIS_UNREAD_KEY_PREFIX: str = "unread"
    REDIS_PROCESSED_EVENT_KEY_PREFIX: str = "processed"
    REDIS_PROCESSED_EVENT_TTL_SEC: int = 24 * 60 * 60


class KafkaSettings(EmptyBaseSettings):
    KAFKA_BROKERS: str = "kafka:9093"
    KAFKA_GROUP_ID: str = "otus"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = "PLAIN"
    KAFKA_SASL_PLAIN_USERNAME: str | None = None
    KAFKA_SASL_PLAIN_PASSWORD: str | None = None
    KAFKA_MAX_REQUEST_SIZE_BYTES: int = 1 * 1024 * 1024
    KAFKA_MAX_POOL_INTERVAL: int = 30000  # 0.5 min

    UNREAD_MESSAGES_TOPIC: str = "social.dialog.messages"


app_settings = AppSettings()
redis_settings = RedisSettings()
kafka_settings = KafkaSettings()
