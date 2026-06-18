"""PostgreSQL store — long-term persistent memory."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from aisc_utils import get_logger, settings

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    input: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    assigned_agent_type: Mapped[str | None] = mapped_column(String(50))
    assigned_agent_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    dependencies: Mapped[list | None] = mapped_column(JSONB, default=list)
    artifact_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    task_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(20), default="markdown")
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    parent_artifact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_by_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    artifact_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PgStore:
    def __init__(self) -> None:
        self._engine = None
        self._session_factory = None

    async def connect(self) -> None:
        self._engine = create_async_engine(
            settings.postgres_dsn,
            echo=False,
            pool_size=20,
            max_overflow=10,
        )
        self._session_factory = sessionmaker(  # type: ignore[assignment]
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("postgres_connected")

    async def create_tables(self) -> None:
        if self._engine is None:
            await self.connect()
        async with self._engine.begin() as conn:  # type: ignore[union-attr]
            await conn.run_sync(Base.metadata.create_all)
        logger.info("postgres_tables_created")

    async def session(self) -> AsyncSession:
        if self._session_factory is None:
            await self.connect()
        return self._session_factory()  # type: ignore[misc]


pg_store = PgStore()
