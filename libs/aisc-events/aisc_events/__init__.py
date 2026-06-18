"""AISC Kafka event publisher and consumer library."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

import orjson
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from aisc_models import EventEnvelope


class EventPublisher:
    def __init__(self, bootstrap_servers: str, client_id: str = "aisc") -> None:
        self._bootstrap_servers = bootstrap_servers
        self._client_id = client_id
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            client_id=self._client_id,
            value_serializer=lambda v: orjson.dumps(v),
            compression_type="snappy",
            acks="all",
            retries=3,
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def publish(self, event: EventEnvelope, topic: str | None = None) -> None:
        if self._producer is None:
            raise RuntimeError("Publisher not started")
        topic_name = topic or f"aisc.{event.event_type.lower()}"
        payload = event.model_dump(mode="json")
        await self._producer.send_and_wait(topic_name, payload)

    async def publish_batch(self, events: list[tuple[EventEnvelope, str]]) -> None:
        if self._producer is None:
            raise RuntimeError("Publisher not started")
        batch = self._producer.create_batch()
        for event, topic in events:
            payload = event.model_dump(mode="json")
            metadata = batch.append(
                key=bytes(str(event.correlation_id), "utf-8"),
                value=orjson.dumps(payload),
                timestamp=int(event.timestamp.timestamp() * 1000),
            )
            if metadata is None:
                await self._producer.send_batch(batch, [topic])
                batch = self._producer.create_batch()
        await self._producer.send_batch(batch, [events[-1][1]])


class EventConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        topics: list[str],
        group_id: str,
        client_id: str = "aisc",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topics = topics
        self._group_id = group_id
        self._client_id = client_id
        self._consumer: AIOKafkaConsumer | None = None
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event_type: str) -> Callable:
        def decorator(handler: Callable) -> Callable:
            self._handlers.setdefault(event_type, []).append(handler)
            return handler
        return decorator

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            client_id=self._client_id,
            value_deserializer=lambda v: orjson.loads(v),
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_records=100,
        )
        await self._consumer.start()

    async def stop(self) -> None:
        if self._consumer:
            await self._consumer.stop()

    async def consume(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Consumer not started")
        try:
            async for msg in self._consumer:
                try:
                    event_data = msg.value
                    event_type = event_data.get("event_type", "")
                    handlers = self._handlers.get(event_type, [])
                    for handler in handlers:
                        await handler(event_data)
                    await self._consumer.commit()
                except Exception:
                    import structlog
                    logger = structlog.get_logger(__name__)
                    logger.exception("Failed to process event", topic=msg.topic)
        except asyncio.CancelledError:
            pass
