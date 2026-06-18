"""AISC shared utilities: logging, tracing, configuration."""

from __future__ import annotations

import os

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict


def configure_logging(service_name: str = "aisc", log_level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()
            if os.getenv("LOG_FORMAT") == "console"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name or __name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "aisc"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "aisc"
    postgres_user: str = "aisc"
    postgres_password: str = "aisc_dev"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_schema_registry_url: str = "http://localhost:8081"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "aisc_dev"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""

    jwt_private_key_path: str = ""
    jwt_public_key_path: str = ""
    jwt_access_token_ttl_minutes: int = 15
    jwt_refresh_token_ttl_days: int = 7

    log_level: str = "INFO"
    log_format: str = "console"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"


settings = Settings()
