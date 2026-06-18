"""AISC shared Pydantic data models."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentType(StrEnum):
    ORCHESTRATOR = "orchestrator"
    PRODUCT_MANAGER = "product_manager"
    RESEARCH = "research"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    QA = "qa"
    SECURITY = "security"
    DEVOPS = "devops"
    MONITORING = "monitoring"
    SELF_HEALING = "self_healing"
    KNOWLEDGE = "knowledge"
    LEARNING = "learning"
    CONSENSUS = "consensus"
    IMPROVEMENT = "improvement"
    REVIEWER = "reviewer"


class AgentStatus(StrEnum):
    CREATED = "created"
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class TaskStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ArtifactType(StrEnum):
    PRD = "prd"
    USER_STORY = "user_story"
    FEATURE_SPEC = "feature_spec"
    ARCHITECTURE_DOC = "architecture_doc"
    API_SPEC = "api_spec"
    ERD = "erd"
    SOURCE_CODE = "source_code"
    TEST_FILE = "test_file"
    SECURITY_REPORT = "security_report"
    DEPLOYMENT_CONFIG = "deployment_config"
    RESEARCH_REPORT = "research_report"
    ADR = "adr"


class ArtifactStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class GateType(StrEnum):
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    CODE = "code"
    TESTING = "testing"
    SECURITY = "security"
    DEPLOYMENT = "deployment"


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class EventEnvelope(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_service: str
    source_agent: str | None = None
    correlation_id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    task_id: UUID | None = None
    payload: dict = Field(default_factory=dict)
    version: str = "1.0"


class AgentContext(BaseModel):
    agent_id: UUID
    agent_type: AgentType
    status: AgentStatus
    current_task_id: UUID | None = None
    tools: list[str] = Field(default_factory=list)


class TaskContext(BaseModel):
    task_id: UUID
    task_type: str
    project_id: UUID
    agent_type: AgentType
    priority: Priority = Priority.MEDIUM
    input: dict = Field(default_factory=dict)
    dependencies: list[UUID] = Field(default_factory=list)


class Artifact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    task_id: UUID | None = None
    type: ArtifactType
    name: str
    content: str
    version: int = 1
    status: ArtifactStatus = ArtifactStatus.DRAFT
    parent_artifact_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)


class MetricScore(BaseModel):
    metric_name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    justification: str
    passed: bool


class EvaluationResult(BaseModel):
    artifact_id: UUID
    gate_type: GateType
    aggregate_score: float = Field(ge=0, le=100)
    metric_scores: list[MetricScore]
    passed: bool
    iteration: int
    feedback: str | None = None


class Critique(BaseModel):
    artifact_id: UUID
    reviewer_id: UUID
    overall_score: float = Field(ge=0, le=100)
    metric_scores: dict[str, float] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class LoopState(BaseModel):
    artifact_id: UUID
    gate_type: GateType
    current_iteration: int = 1
    max_iterations: int = 5
    threshold: float
    score_history: list[float] = Field(default_factory=list)
    stuck_count: int = 0
