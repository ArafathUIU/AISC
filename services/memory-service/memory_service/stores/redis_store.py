"""Redis store — short-term memory and agent state management."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
from aisc_utils import get_logger, settings

logger = get_logger(__name__)


class RedisStore:
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._redis = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password or None,
            decode_responses=True,
            max_connections=20,
        )
        await self._redis.ping()
        logger.info("redis_connected", host=settings.redis_host)

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None

    @property
    def is_connected(self) -> bool:
        return self._redis is not None

    async def get(self, key: str) -> dict[str, Any] | None:
        if not self._redis:
            return None
        value = await self._redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: dict[str, Any], ttl: int | None = None) -> None:
        if not self._redis:
            return
        data = json.dumps(value, default=str)
        if ttl:
            await self._redis.setex(key, ttl, data)
        else:
            await self._redis.set(key, data)

    async def publish(self, channel: str, message: str) -> None:
        if self._redis:
            await self._redis.publish(channel, message)

    async def scan_keys(self, pattern: str, count: int = 100) -> list[str]:
        if not self._redis:
            return []
        keys: list[str] = []
        cursor = 0
        while True:
            cursor, batch = await self._redis.scan(cursor, match=pattern, count=count)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys


redis_store = RedisStore()
