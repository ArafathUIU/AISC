# AISC — Hierarchical Project Plan

**Author**: Lead Systems Architect  
**Date**: 2026-06-18  
**Status**: Draft — Ready for Review

---

# Phase 1: Core Infrastructure

> **Goal**: Establish the foundational platform — agent framework, authentication, memory system, and event bus. No agents ship yet, but the skeleton must be production-ready.

---

## Milestone 1.1: Monorepo & DevOps Foundation

### Epic 1.1.1: Repository & Project Scaffold

**Task 1.1.1.1 — Initialize Monorepo Structure**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create the full directory tree under `aisc/` per the folder structure blueprint. Initialize git, `.gitignore`, `pyproject.toml`, `Makefile`, `.env.example`, root `docker-compose.yml`. |
| **Dependencies** | None |
| **Difficulty** | Easy |
| **Estimated Effort** | 2 hours |
| **Required Technologies** | Git, Python 3.12+, Docker |
| **Success Criteria** | `tree aisc/` matches blueprint structure; `git init` succeeds; `docker compose config` validates; `make help` lists available targets. |

**Task 1.1.1.2 — Shared Libraries Package Setup**

| Attribute | Detail |
|-----------|--------|
| **Description** | Scaffold all 4 shared libraries: `aisc-proto` (Protobuf with buf.build), `aisc-models` (Pydantic v2), `aisc-events` (Kafka producer/consumer abstraction), `aisc-utils` (logging, tracing, config). Set up editable pip installs. |
| **Dependencies** | 1.1.1.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | Protobuf, buf, Pydantic v2, kafka-python, structlog, OpenTelemetry SDK |
| **Success Criteria** | All 4 libs installable via `pip install -e .`; `aisc-models` imports without errors; `aisc-proto` compiles via `buf generate`; `aisc-events` can produce/consume against a local Kafka via docker-compose. |

**Task 1.1.1.3 — CI Pipeline (Lint, Typecheck, Test)**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `.github/workflows/ci.yml` that runs ruff, mypy, and pytest on every PR. Configure branch protection for `main`. |
| **Dependencies** | 1.1.1.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | GitHub Actions, ruff, mypy, pytest |
| **Success Criteria** | PR to `main` triggers CI; ruff passes with zero errors; mypy passes with strict mode; pytest collects 0 tests (initially) without errors. |

**Task 1.1.1.4 — Local Development Environment**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `docker-compose.yml` with PostgreSQL, Redis, Kafka (single broker), Qdrant, Neo4j. Create `scripts/dev-setup.sh` that spins up infra, runs migrations, seeds test data. |
| **Dependencies** | 1.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Docker, Docker Compose, bash/powershell |
| **Success Criteria** | `docker compose up -d` starts all 5 databases; `make dev-setup` completes without errors; health checks pass for all containers. |

---

### Epic 1.1.2: Docker Images & Container Registry

**Task 1.1.2.1 — Base Service Dockerfile Template**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create a multi-stage `Dockerfile` template for FastAPI services. Include dev stage with hot-reload, prod stage with gunicorn + uvicorn workers. Create a cookiecutter-style generator script. |
| **Dependencies** | 1.1.1.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | Docker, FastAPI, gunicorn, uvicorn |
| **Success Criteria** | Template builds successfully; dev stage supports hot-reload; prod stage runs with 4 uvicorn workers; image size < 300MB. |

**Task 1.1.2.2 — Docker Compose Override Files**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `docker-compose.override.yml` (dev — mounts volumes, enables debug) and `docker-compose.prod.yml` (production — resource limits, restart policies, secrets). |
| **Dependencies** | 1.1.1.4, 1.1.2.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 2 hours |
| **Required Technologies** | Docker Compose |
| **Success Criteria** | Dev override mounts source code volumes; prod override sets CPU/memory limits; secrets injected via env_file. |

---

## Milestone 1.2: Event Bus & Messaging

### Epic 1.2.1: Kafka Infrastructure

**Task 1.2.1.1 — Kafka Cluster Setup**

| Attribute | Detail |
|-----------|--------|
| **Description** | Configure Kafka with 3 brokers, Zookeeper ensemble, schema registry. Create topics for all 40+ event types with appropriate partitions and retention. |
| **Dependencies** | 1.1.1.4 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | Kafka, Zookeeper, Confluent Schema Registry, docker-compose |
| **Success Criteria** | 3 Kafka brokers form a cluster; schema registry is healthy; all topics auto-created on first publish; retention set to 7 days. |

**Task 1.2.1.2 — Protobuf Event Definitions**

| Attribute | Detail |
|-----------|--------|
| **Description** | Define Protobuf schemas for all 40+ event types in `libs/aisc-proto/events.proto`. Include the standard event envelope and type-specific payloads. |
| **Dependencies** | 1.1.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Protobuf v3, buf |
| **Success Criteria** | All 40+ events defined as protobuf messages; `buf lint` passes; `buf breaking` enabled; generated Python stubs importable. |

**Task 1.2.1.3 — Event Publisher & Consumer Library**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `aisc-events` library: `EventPublisher` with async publish, batching, idempotency keys, and `EventConsumer` with at-least-once semantics, dead-letter queue support, and retry with backoff. |
| **Dependencies** | 1.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | aiokafka, Protobuf, asyncio |
| **Success Criteria** | Publisher delivers message to Kafka with correlation_id; consumer reads, deserializes, and acks; DLQ catches unprocessable messages; retry with exponential backoff works. |

**Task 1.2.1.4 — Event Bus Integration Tests**

| Attribute | Detail |
|-----------|--------|
| **Description** | Write integration tests using `testcontainers-python` to spin up Kafka in CI and test publish/consume for every event type. Test failure modes (broker down, schema mismatch, consumer lag). |
| **Dependencies** | 1.2.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | testcontainers-python, pytest-asyncio |
| **Success Criteria** | All event types round-trip; broker failure triggers retry; schema mismatch sends to DLQ; tests run in CI. |

---

## Milestone 1.3: Authentication & Authorization

### Epic 1.3.1: Auth Service Core

**Task 1.3.1.1 — Auth Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `auth-service` FastAPI app with health check, config loading, DB connection, and Alembic migrations. |
| **Dependencies** | 1.1.1.4 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | FastAPI, SQLAlchemy 2.0, Alembic, asyncpg |
| **Success Criteria** | `GET /health` returns 200; Alembic creates initial migration; service connects to PostgreSQL. |

**Task 1.3.1.2 — User Model & Registration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `users` table with bcrypt password hashing. Create `POST /api/v1/auth/register` and `POST /api/v1/auth/login` endpoints returning JWT access + refresh tokens. |
| **Dependencies** | 1.3.1.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | bcrypt, python-jose (JWT), pydantic |
| **Success Criteria** | User registers -> stored with hashed password; login -> returns valid JWT; invalid password -> 401; duplicate email -> 409. |

**Task 1.3.1.3 — JWT Refresh & Token Blacklist**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `POST /api/v1/auth/refresh` with rotating refresh tokens. Store token family in Redis with blacklist support on logout. |
| **Dependencies** | 1.3.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | Redis, python-jose |
| **Success Criteria** | Refresh token returns new access + refresh pair; used refresh token is invalidated (rotation); logout blacklists all tokens in family. |

**Task 1.3.1.4 — RBAC & ABAC Authorization**

| Attribute | Detail |
|-----------|--------|
| **Description** | Define roles (`admin`, `developer`, `viewer`) in `roles` table with permissions. Implement ABAC (Attribute-Based Access Control) for fine-grained project-level access. Create FastAPI dependency `require_permission`. |
| **Dependencies** | 1.3.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | FastAPI dependencies, SQLAlchemy |
| **Success Criteria** | RBAC: admin can manage users, viewer cannot; ABAC: user can access assigned projects only; `require_permission("projects:write")` gates endpoints. |

**Task 1.3.1.5 — Auth Middleware for API Gateway**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create a FastAPI middleware that validates JWT on every request. Extract user context, attach to request scope. Emit `UserAuthenticated` event. |
| **Dependencies** | 1.3.1.2 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | FastAPI middleware, aisc-events |
| **Success Criteria** | All routes behind middleware require valid JWT; expired token -> 401; user context available via `request.state.user`. |

## Milestone 1.4: Memory System Foundation

### Epic 1.4.1: Short-Term Memory (Redis)

**Task 1.4.1.1 — Redis Client & Connection Pool**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `stores/redis.py` in `memory-service` with async connection pool, key prefixing, TTL management, and JSON serialization. |
| **Dependencies** | 1.1.1.4 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | redis-py (async), orjson |
| **Success Criteria** | Connection pool reuses connections; keys are namespaced by service; TTL auto-expires; read/write round-trips JSON. |

**Task 1.4.1.2 — Agent Session State Store**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement CRUD operations for agent session state: active task context, conversation history, intermediate artifact versions, loop iteration counters. |
| **Dependencies** | 1.4.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | Redis, aisc-models |
| **Success Criteria** | Agent state written/read atomically; state TTL matches agent timeout; concurrent agent access handled via optimistic locking. |

**Task 1.4.1.3 — Redis Pub/Sub for WebSocket Gateway**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement Redis Pub/Sub channels per project, per agent, and per event type. The WebSocket gateway subscribes and forwards messages to connected clients. |
| **Dependencies** | 1.4.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | Redis Pub/Sub, FastAPI WebSockets |
| **Success Criteria** | Event published to `project:{id}:events` channel -> WS gateway receives -> client receives JSON; multiple clients on same channel all receive. |

---

### Epic 1.4.2: Long-Term Memory (PostgreSQL)

**Task 1.4.2.1 — Memory Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `memory-service` FastAPI app. Connect to PostgreSQL, Redis, Qdrant, Neo4j. Define ORM models for `projects`, `tasks`, `artifacts`, `evaluations`, `workflows`, `learning_records`, `agent_runs`, `incidents`. |
| **Dependencies** | 1.1.1.4 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | FastAPI, SQLAlchemy 2.0 async, Alembic |
| **Success Criteria** | All 8 tables created via Alembic migration; ORM models match schema from Blueprint; async session factory works. |

**Task 1.4.2.2 — Project & Task CRUD API**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement REST endpoints for project and task CRUD: create, list, get, update, delete (soft). Include filtering, pagination, and sorting. |
| **Dependencies** | 1.4.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | FastAPI, SQLAlchemy, pydantic |
| **Success Criteria** | Full CRUD for projects and tasks; list supports `?status=active&page=2&limit=20`; soft delete archives; foreign key constraints enforced. |

**Task 1.4.2.3 — Artifact Storage & Versioning**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement artifact storage with version tracking. Each update creates a new version row. Support `GET /artifacts/{id}/versions` and `GET /artifacts/{id}/versions/{v}`. Parent-child relationship for derived artifacts. |
| **Dependencies** | 1.4.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | SQLAlchemy, pydantic |
| **Success Criteria** | Artifact update -> version counter increments; version history retrievable; parent artifact links to child; content stored as JSONB. |

**Task 1.4.2.4 — Evaluation & Score Storage**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement evaluation storage with full iteration history. Each evaluation includes gate type, all metric scores, pass/fail status, iteration number, and feedback text. |
| **Dependencies** | 1.4.2.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | SQLAlchemy, JSONB |
| **Success Criteria** | Evaluation stored with all scores; queriable by artifact and gate type; iteration history shows score progression over loops. |

---

### Epic 1.4.3: Semantic Memory (Vector DB)

**Task 1.4.3.1 — Qdrant Setup & Collection Management**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement Qdrant client in `memory-service/stores/qdrant.py`. Create collections for: code embeddings (768d), document embeddings (768d), agent memory (1536d for GPT-4o). Set up cosine similarity. |
| **Dependencies** | 1.1.1.4 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | qdrant-client, sentence-transformers |
| **Success Criteria** | Collections created with correct dimensionality; cosine similarity configured; HNSW index built; collection info queryable. |

**Task 1.4.3.2 — Embedding Generation Pipeline**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement embedding generation using `sentence-transformers/all-MiniLM-L6-v2` (768d) for code/docs and OpenAI `text-embedding-3-large` (3072d) for agent context. Support batching. |
| **Dependencies** | 1.4.3.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | sentence-transformers, openai, asyncio |
| **Success Criteria** | Document -> embedding vector; batch of 100 -> 100 vectors; local and API embeddings produce correct dimensions. |

**Task 1.4.3.3 — Vector Search API**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `POST /api/v1/memory/search` with query text, collection filter, and top-k. Returns ranked results with similarity scores. |
| **Dependencies** | 1.4.3.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | qdrant-client, FastAPI |
| **Success Criteria** | Query "user authentication" returns auth-related documents first; scores decrease with relevance; filter by collection works; top-k limits results. |

---

### Epic 1.4.4: Knowledge Graph (Neo4j)

**Task 1.4.4.1 — Neo4j Client & Schema Setup**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement Neo4j driver in `memory-service/stores/neo4j.py`. Create constraints and indexes. Define node types and relationship types per Blueprint. |
| **Dependencies** | 1.1.1.4 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | neo4j-driver (async), Cypher |
| **Success Criteria** | Driver connects with connection pool; unique constraints on all node IDs; indexes on relationship properties; Cypher query executes successfully. |

**Task 1.4.4.2 — Core Relationship Operations**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement CRUD for all 12 relationship types (HAS_REQUIREMENT, IMPLEMENTS, REQUIRES, DEPENDS_ON, HAS_COLUMN, EXPOSES, DEPLOYS_TO, AFFECTS, FIXES, JUSTIFIES, USES, COVERS). |
| **Dependencies** | 1.4.4.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Neo4j, Cypher |
| **Success Criteria** | Each relationship type tested with create, read, delete; graph traversal across 3-hop path returns correct entities; no orphaned relationships. |

**Task 1.4.4.3 — Graph Query API**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `GET /api/v1/knowledge-graph/query?cypher=` for raw Cypher (read-only, with query validation) and `GET /api/v1/knowledge-graph/entity/{type}/{id}/relations` for entity-centric traversal. |
| **Dependencies** | 1.4.4.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | FastAPI, Neo4j |
| **Success Criteria** | Read-only Cypher queries return results; write queries blocked; entity relations return all connected nodes with relationship types. |

---

## Milestone 1.5: API Gateway & Service Mesh

### Epic 1.5.1: API Gateway Setup

**Task 1.5.1.1 — Kong Declarative Configuration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Configure Kong as API gateway with route definitions for all 12 microservices. Enable JWT plugin, rate limiting (100 req/s per user), CORS, and request logging. |
| **Dependencies** | 1.3.1.5 (auth middleware) |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Kong, Lua |
| **Success Criteria** | `GET /api/v1/projects` routed to orchestrator-service:8002; JWT validation on all `/api/v1/*`; rate limit triggers 429; CORS headers present. |

**Task 1.5.1.2 — Service Discovery**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement DNS-based service discovery with Docker Compose (dev) and Kubernetes DNS (prod). Services discover each other via `http://{service-name}:{port}`. |
| **Dependencies** | 1.1.1.4 |
| **Difficulty** | Easy |
| **Estimated Effort** | 2 hours |
| **Required Technologies** | Docker Compose networking, Kubernetes Services |
| **Success Criteria** | `auth-service` reaches `memory-service:8007` via HTTP; inter-service latency < 5ms on same host. |

**Task 1.5.1.3 — WebSocket Gateway**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `ws-gateway` service with FastAPI WebSocket support. Authenticate via JWT in query param. Subscribe client to project and agent channels. Forward events from Redis Pub/Sub to WS clients. |
| **Dependencies** | 1.4.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | FastAPI WebSockets, Redis, python-jose |
| **Success Criteria** | Client connects with JWT -> authenticated; subscribes to `project:{id}:*` -> receives events; disconnect -> channels unsubscribed; 1000 concurrent connections handled. |

---

## Milestone 1.6: Observability Foundation

### Epic 1.6.1: Logging & Tracing

**Task 1.6.1.1 — Structured Logging Library**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `aisc-utils/logging.py` with structlog. Every log entry includes: timestamp, service_name, correlation_id, log_level, message, and context dict. JSON format for prod, console for dev. |
| **Dependencies** | 1.1.1.2 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | structlog, orjson |
| **Success Criteria** | `logger.info("task_started", task_id="x")` -> `{"service": "orchestrator", "correlation_id": "abc", "event": "task_started", "task_id": "x"}`. |

**Task 1.6.1.2 — OpenTelemetry Tracing**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `aisc-utils/tracing.py` with OpenTelemetry SDK. Auto-instrument FastAPI, SQLAlchemy, Redis, Kafka. Propagate trace context across services via W3C TraceContext headers. |
| **Dependencies** | 1.6.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | opentelemetry-python, Jaeger (exporter) |
| **Success Criteria** | Span created per HTTP request; trace_id propagated across service calls; Jaeger UI shows full trace waterfall; DB queries appear as child spans. |

**Task 1.6.1.3 — ELK Stack Setup**

| Attribute | Detail |
|-----------|--------|
| **Description** | Add Elasticsearch, Logstash, and Kibana to docker-compose. Configure Logstash to ingest JSON logs from all services. Create Kibana index pattern and basic dashboard. |
| **Dependencies** | 1.6.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | Elasticsearch, Logstash, Kibana, Docker |
| **Success Criteria** | Logs from all services visible in Kibana Discover; correlation_id searchable; dashboard shows error rate and request count. |

---

### Epic 1.6.2: Metrics & Monitoring

**Task 1.6.2.1 — Prometheus Metrics Endpoint**

| Attribute | Detail |
|-----------|--------|
| **Description** | Add `prometheus-client` to all services. Expose `GET /metrics` with: request count, latency histogram, error count, active agents, queue depth, and DB pool usage. |
| **Dependencies** | 1.1.1.2 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | prometheus-client, FastAPI |
| **Success Criteria** | Each service exposes `/metrics`; Prometheus scrapes successfully; custom metrics appear: `aisc_active_agents`, `aisc_task_queue_depth`, etc. |

**Task 1.6.2.2 — Grafana Dashboards**

| Attribute | Detail |
|-----------|--------|
| **Description** | Add Grafana to docker-compose. Create dashboards: "System Overview" (all services health), "Agent Performance" (LLM tokens, latency), "Quality Gates" (pass/fail rates by gate), "Event Bus" (throughput, lag). |
| **Dependencies** | 1.6.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Grafana, Prometheus |
| **Success Criteria** | All 4 dashboards load with real-time data; Prometheus data source configured; dashboards exported as JSON for version control. |

**Task 1.6.2.3 — Health Check Endpoint**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `GET /health` on every service returning: service status, uptime, DB connection status, event bus connection status, and dependency health (cascading). |
| **Dependencies** | 1.6.2.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | FastAPI |
| **Success Criteria** | `GET /health` returns 200 with all dependencies healthy; DB down -> health returns degraded status; used by Kubernetes liveness/readiness probes. |

---

# Phase 2: Core Agents

> **Goal**: Ship the Product Manager, Research Agent, and Architect Agent. Validate the recursive quality loop end-to-end with these agents.

---

## Milestone 2.1: Agent Runtime Engine

### Epic 2.1.1: Agent Runtime Core

**Task 2.1.1.1 — Agent Runtime Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `agent-runtime` FastAPI app. Connect to Redis (agent state), Kafka (events), and memory-service (context). Define agent lifecycle states: CREATED -> INITIALIZING -> IDLE -> BUSY -> ERROR -> TERMINATED. |
| **Dependencies** | 1.4.1.2, 1.2.1.3, Milestone 1.4 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | FastAPI, Redis, Kafka |
| **Success Criteria** | Agent Runtime starts and connects to all dependencies; agent lifecycle state machine defined as enum; state transitions validated. |

**Task 2.1.1.2 — Agent Base Class**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/base.py` with abstract `BaseAgent` class. Defines: `async def run(task: TaskContext) -> AgentResult`, `async def critique(artifact: Artifact) -> Critique`, `async def improve(artifact: Artifact, critique: Critique) -> Artifact`. Lifecycle hooks: `on_start`, `on_complete`, `on_error`. |
| **Dependencies** | 2.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Python ABC, asyncio, pydantic |
| **Success Criteria** | Concrete agent inherits `BaseAgent`; `run()` called -> `on_start` fires -> executes -> `on_complete` fires; `on_error` catches exceptions; all three core methods defined. |

**Task 2.1.1.3 — LLM Provider Abstraction**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `llm/` module with `LLMProvider` base class and concrete implementations for OpenAI (GPT-4o, GPT-4o-mini), Anthropic (Claude 3.5 Sonnet, Claude 3 Haiku), DeepSeek (DeepSeek-V3), and a local Llama 3.2 (via Ollama). |
| **Dependencies** | None (standalone lib) |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | openai, anthropic, httpx, ollama |
| **Success Criteria** | All 4 providers implement `async chat(messages, **kwargs) -> LLMResponse`; streaming supported; token usage returned; provider switchable via config. |

**Task 2.1.1.4 — LLM Router (Cost-Aware)**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `llm/router.py`. Routes tasks to cheapest capable model: simple tasks -> DeepSeek/Haiku/GPT-4o-mini, complex architecture -> Claude Sonnet/GPT-4o. Supports provider failover (OpenAI down -> Anthropic). Tracks per-task token costs. |
| **Dependencies** | 2.1.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Python, asyncio |
| **Success Criteria** | Router selects cheaper model for simple prompt; cost logged per task; provider failover works; budget exceeded -> task paused. |

**Task 2.1.1.5 — Tool Execution Framework**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `tools/` module with `BaseTool` class. Tools receive input, execute, return result. Implement: `RAGQueryTool`, `WebSearchTool`, `GitOpsTool`, `DockerOpsTool`, `CodeGenerationTool`, `StaticAnalysisTool`, `TestRunnerTool`, and `SecurityScannerTool`. |
| **Dependencies** | 2.1.1.2 |
| **Difficulty** | Large |
| **Estimated Effort** | 16 hours |
| **Required Technologies** | subprocess, docker-py, gitpython, httpx |
| **Success Criteria** | Each tool: executable, result returned, error handled; tools registered in agent config; agent can invoke tool by name. |

---

## Milestone 2.2: Orchestrator Agent

### Epic 2.2.1: Orchestrator Service Core

**Task 2.2.1.1 — Orchestrator Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `orchestrator-service` FastAPI app. Connect to PostgreSQL, Redis, Kafka. Define workflow engine skeleton. |
| **Dependencies** | 1.4.2.1, 1.2.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | FastAPI, SQLAlchemy, Redis, Kafka |
| **Success Criteria** | Service starts and connects to all dependencies; workflow CRUD endpoints respond. |

**Task 2.2.1.2 — Workflow DAG Engine**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `engine/workflow.py` using `networkx`. Define workflow as DAG of tasks with dependencies. Support: topological sort, parallel execution of independent nodes, circular dependency detection, node status tracking. |
| **Dependencies** | 2.2.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | networkx, asyncio |
| **Success Criteria** | DAG created with 5 nodes; topological sort returns valid order; parallel nodes execute concurrently; circular dependency raises error; node status transitions: pending -> running -> completed/failed. |

**Task 2.2.1.3 — Agent Scheduler**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `engine/scheduler.py`. Matches tasks to agents by capability. Queues tasks when no agent available. Implements priority-based scheduling with aging. Tracks agent availability in Redis. |
| **Dependencies** | 2.2.1.2, 2.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Redis, asyncio |
| **Success Criteria** | Task created -> assigned to correct agent type; all agents busy -> task queued; high-priority task preempts queue; idle agent picks next task from queue. |

**Task 2.2.1.4 — Dependency Resolution**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `engine/dependency.py`. A task's dependencies must be COMPLETED before it can be ASSIGNED. Supports artifact-level dependencies (code depends on architecture). Resolves and emits `TaskReady` when satisfied. |
| **Dependencies** | 2.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | networkx, SQLAlchemy |
| **Success Criteria** | Task A depends on Task B -> A stays PENDING until B completes; multi-level dependency chain resolves in order; failed dependency -> dependent tasks marked BLOCKED. |

**Task 2.2.1.5 — Escalation Handler**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement escalation logic for: quality gate failed at max iterations, agent error unhandled, deadline exceeded, consensus deadlock. Escalation creates a human-review task and notifies via WebSocket. |
| **Dependencies** | 2.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | Kafka, WebSocket |
| **Success Criteria** | Quality gate fails 5 times -> escalation task created; escalation appears in UI; human can accept/reject/override; escalation has timeout. |

---

### Epic 2.2.2: Product Manager Agent

**Task 2.2.2.1 — PM Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/product_manager.py`. Input: business idea / problem statement. Output: structured PRD with problem statement, target users, success metrics, and feature list. Uses RAG for market context and competitor analysis. |
| **Dependencies** | 2.1.1.2, 2.1.1.4, RAG (2.4.1) |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider, RAG |
| **Success Criteria** | Input "build a todo app" -> output structured PRD with 5+ features; each feature has success metrics; PRD passes requirements gate at >=90. |

**Task 2.2.2.2 — PM Agent System Prompt**

| Attribute | Detail |
|-----------|--------|
| **Description** | Design and version the PM agent system prompt in `prompts/product_manager.md`. Include role, output format, quality criteria, chain-of-thought instructions, and few-shot examples. |
| **Dependencies** | 2.2.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | Prompt engineering |
| **Success Criteria** | Prompt produces consistently structured PRDs; edge case handling tested; prompt versioned in git. |

**Task 2.2.2.3 — User Story Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Extend PM agent to generate user stories from PRD features. Each story: "As a {role}, I want {action} so that {benefit}". Acceptance criteria in Gherkin format. |
| **Dependencies** | 2.2.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | LLM Provider |
| **Success Criteria** | 10 features -> 10+ stories; each story has 3+ acceptance criteria in Gherkin; stories linked to features; stories pass review. |

**Task 2.2.2.4 — Roadmap Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Extend PM agent to generate development roadmap from features. Prioritize using MoSCoW method. Assign features to milestones with estimated effort. |
| **Dependencies** | 2.2.2.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | LLM Provider |
| **Success Criteria** | Roadmap has 3+ milestones; features classified as Must/Should/Could/Won't; effort estimates present; roadmap is logically ordered. |

---

### Epic 2.2.3: Research Agent

**Task 2.2.3.1 — Research Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/research.py`. Input: research question / technology area. Output: structured research report with findings, recommendations, pros/cons, and risk assessment. Uses RAG for internal docs and WebSearch for external. |
| **Dependencies** | 2.1.1.2, 2.1.1.4, RAG (2.4.1) |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider, RAG, Web Search Tool |
| **Success Criteria** | Input "compare React vs Vue for dashboard" -> report with feature comparison, performance benchmarks, ecosystem size, recommendation with reasoning. |

**Task 2.2.3.2 — Technology Evaluation Framework**

| Attribute | Detail |
|-----------|--------|
| **Description** | Define a structured evaluation framework: technology scored on maturity, community, performance, learning curve, ecosystem, licensing. Weighted scoring produces recommendation. |
| **Dependencies** | 2.2.3.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | Pydantic |
| **Success Criteria** | Any technology comparison produces consistent scoring rubric; scores justified with citations; recommendation clear. |

**Task 2.2.3.3 — Competitor Analysis**

| Attribute | Detail |
|-----------|--------|
| **Description** | Extend Research Agent to search for competitors, analyze their features, pricing, strengths/weaknesses, and market position. Output competitive matrix. |
| **Dependencies** | 2.2.3.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Web Search Tool, LLM |
| **Success Criteria** | Input "Slack competitors" -> matrix with 5+ competitors; each has features, pricing tier, SWOT analysis; sources cited. |

---

### Epic 2.2.4: Architect Agent

**Task 2.2.4.1 — Architect Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/architect.py`. Input: PRD + user stories. Output: system architecture document, component diagram (Mermaid), API contracts (OpenAPI), and ER diagram (Mermaid). |
| **Dependencies** | 2.1.1.2, 2.1.1.4, PM Agent output |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | LLM Provider, RAG |
| **Success Criteria** | Input PRD for "todo app" -> architecture doc with 3+ services, Mermaid component diagram, 5+ API endpoints in OpenAPI, ER diagram with 3+ tables. |

**Task 2.2.4.2 — Service Decomposition Engine**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement logic to decompose requirements into microservices. Apply bounded context from DDD. Each service has: name, responsibility, API surface, data ownership. |
| **Dependencies** | 2.2.4.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider |
| **Success Criteria** | Requirements for e-commerce -> 5+ microservices (catalog, cart, orders, payments, users); each service has clear responsibility boundary; no circular dependencies. |

**Task 2.2.4.3 — API Contract Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate OpenAPI 3.1 specs for each service. Include endpoints, request/response schemas, error codes, and authentication requirements. |
| **Dependencies** | 2.2.4.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Pydantic, openapi-schema-pydantic |
| **Success Criteria** | Generated OpenAPI spec validates against schema; all endpoints have request/response examples; spec importable into Postman/Swagger UI. |

**Task 2.2.4.4 — Database Schema Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate ER diagrams and DDL SQL from requirements. Identify entities, relationships, cardinalities, and indexes. Output Mermaid ER diagram + SQLAlchemy model definitions. |
| **Dependencies** | 2.2.4.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | LLM Provider, SQLAlchemy |
| **Success Criteria** | Generated DDL executes without errors; ER diagram matches DDL; all foreign keys defined; indexes on frequently queried columns. |

**Task 2.2.4.5 — Architecture Decision Records (ADR)**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate ADRs for each architectural decision. Format: Title, Status, Context, Decision, Consequences. Store in `docs/architecture/adr/`. |
| **Dependencies** | 2.2.4.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 3 hours |
| **Required Technologies** | LLM Provider |
| **Success Criteria** | Each major architectural decision has an ADR; ADRs are versioned; pros/cons of alternatives documented. |

---

## Milestone 2.3: Recursive Quality Framework (Core)

### Epic 2.3.1: Scoring Engine

**Task 2.3.1.1 — Scoring Engine Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `scoring-engine` FastAPI app. Define metric interface with `async score(artifact) -> float` returning 0-100. |
| **Dependencies** | 1.4.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | FastAPI, pydantic |
| **Success Criteria** | Scoring engine starts; metric interface defined; new metrics pluggable via registration. |

**Task 2.3.1.2 — Requirements Metrics**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement 5 metrics for requirements: `completeness` (are all sections filled?), `clarity` (is language unambiguous?), `consistency` (are there contradictions?), `feasibility` (is it technically achievable?), `business_alignment` (does it solve the stated problem?). |
| **Dependencies** | 2.3.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider, pydantic |
| **Success Criteria** | PRD scored on all 5 metrics; each metric returns 0-100 with justification; combined score is weighted average. |

**Task 2.3.1.3 — Architecture Metrics**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement 5 metrics for architecture: `scalability`, `reliability`, `security`, `maintainability`, `cost_efficiency`. Each evaluated by LLM against best practices. |
| **Dependencies** | 2.3.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider, pydantic |
| **Success Criteria** | Architecture doc scored on all 5 metrics; scores reflect actual quality (good arch >= 85, bad arch < 60); each score has textual justification. |

**Task 2.3.1.4 — Code Metrics**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement 5 code metrics: `complexity` (cyclomatic via radon), `maintainability` (via radon), `testability` (LLM-evaluated), `performance` (LLM-evaluated), `security` (static analysis + LLM). |
| **Dependencies** | 2.3.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | radon, bandit, LLM Provider |
| **Success Criteria** | Python code scored on all 5 metrics; radon integration produces actual numbers; LLM evaluation consistent across runs. |

**Task 2.3.1.5 — Testing Metrics**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement 4 testing metrics: `coverage` (parse coverage reports), `mutation_score` (run mutmut), `reliability` (flakiness detection), `edge_cases` (LLM-evaluated). |
| **Dependencies** | 2.3.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | coverage.py, mutmut, LLM Provider |
| **Success Criteria** | Test suite scored on all 4 metrics; coverage % extracted from coverage.xml; mutation score from mutmut output; edge case evaluation detects missing test scenarios. |

**Task 2.3.1.6 — Deployment Metrics**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement 3 deployment metrics: `stability` (error rate, uptime), `availability` (health check success rate), `performance` (p95 latency, throughput). Query from Prometheus. |
| **Dependencies** | 2.3.1.1, 1.6.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | prometheus-client, httpx |
| **Success Criteria** | Deployment scored on all 3 metrics; data sourced from Prometheus; scores reflect actual production behavior. |

---

### Epic 2.3.2: Quality Gate Service

**Task 2.3.2.1 — Quality Gate Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `quality-gate-service` FastAPI app. Define gate types: requirements, architecture, code, testing, deployment. Each gate has a threshold (0-100) and max iterations. |
| **Dependencies** | 2.3.1.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | FastAPI, pydantic |
| **Success Criteria** | Quality gate service starts; gate definitions loadable from YAML config; gate evaluation endpoint responds. |

**Task 2.3.2.2 — Gate Evaluation Engine**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `evaluate(artifact, gate_type)` -> calls scoring engine for all metrics of that gate type, computes weighted aggregate score, compares against threshold, returns pass/fail + all scores. |
| **Dependencies** | 2.3.2.1, 2.3.1.2-2.3.1.6 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | FastAPI, httpx (async) |
| **Success Criteria** | Requirements artifact scored against 5 metrics -> aggregate score computed -> compared to threshold (90) -> pass/fail determined; miss one metric -> gate fails. |

**Task 2.3.2.3 — Loop Controller**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `loop_controller.py`. Core recursive loop algorithm: generate/improve -> evaluate -> if fail -> critique -> improve -> evaluate -> repeat until pass or max iterations. Emits events at each step. |
| **Dependencies** | 2.3.2.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | asyncio, Kafka (events) |
| **Success Criteria** | Artifact fails gate -> critique generated -> agent improves -> re-evaluated; score improves over iterations; passes after N iterations; max iterations reached -> escalation. |

**Task 2.3.2.4 — Quality Gate Integration Tests**

| Attribute | Detail |
|-----------|--------|
| **Description** | Integration test: Feed PM Agent a prompt -> PRD generated -> evaluated against requirements gate -> if fail, loop -> if pass, advance. Validate full end-to-end recursive loop. |
| **Dependencies** | 2.3.2.3, 2.2.2.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | pytest, testcontainers, Docker |
| **Success Criteria** | Mock PM agent produces PRD; gate evaluates; if < 90, critique + improve loop runs; loop converges or escalates; entire flow traced via events. |

---

## Milestone 2.4: RAG System

### Epic 2.4.1: RAG Service

**Task 2.4.1.1 — RAG Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `rag-service` FastAPI app. Connect to Qdrant (vector DB) and embedding models. Define ingestion and query pipelines. |
| **Dependencies** | 1.4.3.1, 1.4.3.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | FastAPI, qdrant-client, sentence-transformers |
| **Success Criteria** | RAG service starts; `POST /api/v1/rag/query` and `POST /api/v1/rag/ingest` endpoints respond. |

**Task 2.4.1.2 — Document Ingestion Pipeline**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement document ingestion: chunk documents (256-512 token chunks with overlap), generate embeddings, store in Qdrant with metadata (source, type, timestamp). Support markdown, code, and JSON formats. |
| **Dependencies** | 2.4.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | langchain text splitters, sentence-transformers |
| **Success Criteria** | Markdown document ingested -> chunked -> embedded -> stored in Qdrant; chunk overlap configurable; metadata preserved; duplicate detection prevents re-ingestion. |

**Task 2.4.1.3 — Query Pipeline**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement query pipeline: embed query -> vector search (top-k) -> rerank results (cross-encoder) -> assemble context -> return ranked passages with scores. |
| **Dependencies** | 2.4.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | qdrant-client, sentence-transformers, cross-encoder |
| **Success Criteria** | Query "how to authenticate users" -> returns relevant code/docs passages; reranker improves ranking over raw vector search; context limited to fit LLM context window. |

**Task 2.4.1.4 — RAG Integration with Agents**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `RAGQueryTool` that agents invoke. Tool accepts query string, calls RAG service, returns top-k context passages. Agents include retrieved context in their prompts. |
| **Dependencies** | 2.4.1.3, 2.1.1.5 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | httpx, FastAPI |
| **Success Criteria** | Agent invokes RAG tool -> receives context passages -> includes in LLM prompt; RAG-grounded responses are factually accurate; context source cited in agent output. |

---

## Milestone 2.5: Multi-Agent Debate System

### Epic 2.5.1: Debate Service

**Task 2.5.1.1 — Debate Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `debate-service` FastAPI app. Manage debate lifecycle: OPEN -> IN_REVIEW -> CONSENSUS -> RESOLVED / DEADLOCKED. Coordinate reviewer agents (3 instances) and consensus agent. |
| **Dependencies** | 2.1.1.1, 1.2.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | FastAPI, Redis (debate state), Kafka |
| **Success Criteria** | Debate service starts; debate lifecycle state machine defined; debate can be created and tracked. |

**Task 2.5.1.2 — Reviewer Agent Coordination**

| Attribute | Detail |
|-----------|--------|
| **Description** | When an artifact is submitted for review, spawn 3 reviewer agents in parallel. Each independently critiques the artifact and produces a score. Collect all critiques. |
| **Dependencies** | 2.5.1.1, 2.1.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | asyncio, Kafka |
| **Success Criteria** | Artifact submitted -> 3 reviewers run in parallel -> 3 independent critiques returned; each critique has score + detailed feedback; reviewers complete within timeout. |

**Task 2.5.1.3 — Consensus Agent**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/consensus.py`. Aggregates reviewer critiques, checks agreement level. If 2+ reviewers pass, majority rules. If split, identifies conflict areas, asks reviewers to re-evaluate specific points. After 3 rounds, escalates to human. |
| **Dependencies** | 2.5.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider |
| **Success Criteria** | 3 reviewers return scores [92, 88, 94] -> consensus reached (pass); scores [95, 60, 50] -> conflict identified -> reviewers re-focus on disputed areas; 3 rounds no consensus -> escalation. |

**Task 2.5.1.4 — Improvement Agent**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/improvement.py`. Receives artifact + all critiques + score. Synthesizes feedback into concrete improvements. Outputs improved artifact version. Used in both debate loop and recursive quality loop. |
| **Dependencies** | 2.5.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider |
| **Success Criteria** | Artifact + 3 critiques -> improved artifact; all critique points addressed; new version has higher score; improvement is incremental (not rewriting from scratch). |

**Task 2.5.1.5 — Debate Integration Tests**

| Attribute | Detail |
|-----------|--------|
| **Description** | End-to-end test: submit artifact -> 3 reviewers critique -> consensus agent resolves -> improvement agent refines -> re-submit for review. Validate full debate loop. |
| **Dependencies** | 2.5.1.1-2.5.1.4 |
| **Difficulty** | Large |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | pytest, testcontainers, Docker |
| **Success Criteria** | Full debate loop executes; consensus reached or deadlock handled; improvement produces measurably better artifact; all events emitted. |

---

# Phase 3: Development Agents

> **Goal**: Ship the Developer Agent, QA Agent, and Security Agent. Enable end-to-end code generation with quality gates.

---

## Milestone 3.1: Developer Agent

### Epic 3.1.1: Code Generation Engine

**Task 3.1.1.1 — Developer Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/developer.py`. Input: API contracts + ER diagrams + architecture docs. Output: working source code (Python/FastAPI backend as MVP). Supports code generation, refactoring, and documentation generation. |
| **Dependencies** | 2.1.1.2, 2.1.1.4, Architect Agent output |
| **Difficulty** | Large |
| **Estimated Effort** | 16 hours |
| **Required Technologies** | LLM Provider, RAG, GitOps tool |
| **Success Criteria** | API contract for "GET /todos" -> generates working FastAPI endpoint; code compiles; imports resolve; basic CRUD endpoints generated for each API contract. |

**Task 3.1.1.2 — Code Generation Prompt Engineering**

| Attribute | Detail |
|-----------|--------|
| **Description** | Design system prompts for code generation. Include: language best practices (PEP 8, type hints, async), framework patterns (FastAPI dependency injection), error handling patterns, and security defaults (input validation, SQL injection prevention). |
| **Dependencies** | 3.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Prompt engineering, Python/FastAPI expertise |
| **Success Criteria** | Generated code passes ruff with zero errors; uses type hints throughout; follows FastAPI best practices; includes proper error handling. |

**Task 3.1.1.3 — Multi-File Project Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Extend Developer Agent to generate multi-file projects: models, schemas, routes, services, config. Organize code per microservice conventions. Create `__init__.py`, `requirements.txt`, `Dockerfile`. |
| **Dependencies** | 3.1.1.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | LLM Provider, GitOps tool |
| **Success Criteria** | Architecture with 3 services -> 3 service directories generated; each has models/routes/services/__init__.py; imports cross-resolve; project structure follows blueprint conventions. |

**Task 3.1.1.4 — Code Refactoring**

| Attribute | Detail |
|-----------|--------|
| **Description** | Extend Developer Agent to refactor existing code based on critique feedback. Preserve functionality while improving: readability, performance, security, or architecture. |
| **Dependencies** | 3.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider, StaticAnalysis tool |
| **Success Criteria** | Critique identifies N+1 query -> refactored code uses eager loading; tests still pass; diff is minimal and targeted. |

**Task 3.1.1.5 — Frontend Generation (React/Next.js)**

| Attribute | Detail |
|-----------|--------|
| **Description** | Extend Developer Agent to generate React/Next.js frontend from API contracts. Generate: components, pages, API client, hooks, and basic styling (Tailwind). |
| **Dependencies** | 3.1.1.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | LLM Provider, React, Next.js |
| **Success Criteria** | Backend with 5 API endpoints -> working React app generated; pages for list/detail/create; API client with proper error handling; basic Tailwind styling. |

---

### Epic 3.1.2: Code Quality Gates

**Task 3.1.2.1 — Static Analysis Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `StaticAnalysisTool` that runs ruff (linting), mypy (type checking), and radon (complexity) against generated code. Parse output into structured scores. |
| **Dependencies** | 2.1.1.5 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | ruff, mypy, radon, subprocess |
| **Success Criteria** | Tool runs on directory -> returns structured report with errors/warnings/complexity scores; report parsed into scoring metrics; tool integrated into code gate evaluation. |

**Task 3.1.2.2 — Code Gate Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Integrate code quality gate with Developer Agent loop. Generated code -> static analysis -> security scan -> performance analysis -> review -> score -> loop or advance. |
| **Dependencies** | 3.1.2.1, 2.3.2.3, 3.3.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | FastAPI, Kafka |
| **Success Criteria** | Code generation triggers code gate; gate evaluates all 5 metrics; score >= 92 -> advance; score < 92 -> loop with critique. |

---

## Milestone 3.2: QA Agent

### Epic 3.2.1: Test Generation

**Task 3.2.1.1 — QA Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/qa.py`. Input: source code + requirements. Output: pytest test files with unit tests, integration tests, and E2E tests. Uses coverage analysis to identify gaps. |
| **Dependencies** | 2.1.1.2, 3.1.1.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | LLM Provider, pytest |
| **Success Criteria** | FastAPI endpoint generated -> pytest file with valid tests generated; tests use fixtures, parametrize, and mocks; tests actually test behavior (not just pass). |

**Task 3.2.1.2 — Unit Test Generation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate unit tests for each function/method. Cover: happy path, edge cases, error cases, boundary conditions. Use pytest conventions (fixtures, parametrize). Mock external dependencies. |
| **Dependencies** | 3.2.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | pytest, unittest.mock, LLM Provider |
| **Success Criteria** | Function with 3 branches -> tests for all 3 paths; edge cases tested (None, empty list, max int); mocks used for DB/external calls; tests run and pass. |

**Task 3.2.1.3 — Integration Test Generation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate integration tests using pytest + httpx (TestClient). Test full request/response cycle. Set up test database with fixtures. Test authentication flow. |
| **Dependencies** | 3.2.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | pytest, httpx, FastAPI TestClient |
| **Success Criteria** | Integration tests cover all API endpoints; test DB created/teardown per test; auth headers included; response status and body validated. |

**Task 3.2.1.4 — E2E Test Generation (Playwright)**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate Playwright E2E tests for critical user flows. Test: login, create resource, view resource, update resource, delete resource. |
| **Dependencies** | 3.1.1.5 |
| **Difficulty** | Large |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | Playwright, LLM Provider |
| **Success Criteria** | E2E test navigates full user flow; assertions on UI elements; screenshots on failure; tests run headless in CI. |

**Task 3.2.1.5 — Coverage Analysis Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Integrate coverage.py into test runner. Parse coverage report. Identify uncovered lines/functions/branches. Generate new tests to fill gaps. |
| **Dependencies** | 3.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | coverage.py, LLM Provider |
| **Success Criteria** | Coverage report parsed; uncovered lines identified; QA agent generates tests targeting uncovered code; coverage increases after each iteration. |

**Task 3.2.1.6 — Mutation Testing Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Integrate mutmut for mutation testing. Run mutations, identify killed/survived mutants. Surviving mutants indicate weak tests. Generate improved tests. |
| **Dependencies** | 3.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | mutmut, LLM Provider |
| **Success Criteria** | Mutation score computed; surviving mutants identified; QA agent generates tests to kill surviving mutants; mutation score > 80%. |

---

### Epic 3.2.2: Testing Gate

**Task 3.2.2.1 — Testing Gate Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Integrate testing quality gate. Generated tests -> run tests -> coverage analysis -> mutation testing -> score -> loop or advance. Threshold: >= 95. |
| **Dependencies** | 3.2.1.5, 3.2.1.6, 2.3.2.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | FastAPI, Kafka, pytest |
| **Success Criteria** | Test suite evaluated against 4 metrics; score >= 95 -> advance; score < 95 -> loop; all 4 metrics considered in aggregate. |

---

## Milestone 3.3: Security Agent

### Epic 3.3.1: Security Scanning

**Task 3.3.1.1 — Security Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/security.py`. Scans source code for: SQL injection, XSS, CSRF, SSRF, authentication flaws, insecure dependencies, hardcoded secrets. Uses SAST tools + LLM review. |
| **Dependencies** | 2.1.1.2, 3.1.1.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | bandit, safety, LLM Provider |
| **Success Criteria** | Code with SQL injection vulnerable pattern -> detected and reported; hardcoded API key -> flagged; dependency with known CVE -> reported. |

**Task 3.3.1.2 — SAST Tool Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Integrate bandit (Python security scanner) and safety (dependency vulnerability checker). Parse their JSON output into structured vulnerability reports. |
| **Dependencies** | 3.3.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | bandit, safety, subprocess |
| **Success Criteria** | bandit scan -> parsed into structured report; safety check -> CVE list with severity; both integrated into `SecurityScannerTool`. |

**Task 3.3.1.3 — LLM-Powered Security Review**

| Attribute | Detail |
|-----------|--------|
| **Description** | Use LLM to review code for security patterns that static tools miss: logic flaws, race conditions, insecure defaults, missing rate limiting, improper session management. |
| **Dependencies** | 3.3.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider |
| **Success Criteria** | Code with missing input validation -> LLM flags it; race condition in concurrent code -> LLM identifies; review produces actionable fix suggestions. |

**Task 3.3.1.4 — Secret Scanning**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement secret scanning using regex patterns + entropy detection. Scan all files in repo for: API keys, tokens, passwords, private keys, connection strings. |
| **Dependencies** | 3.3.1.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | Python re, detect-secrets |
| **Success Criteria** | AWS key pattern detected; high-entropy string flagged; false positive rate < 10%; scan runs as pre-commit hook and in security gate. |

**Task 3.3.1.5 — Security Gate Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Mandatory security gate: no code deploys without passing. SAST + dependency check + LLM review + secret scan. Threshold: must pass ALL checks (score = min across all). |
| **Dependencies** | 3.3.1.2-3.3.1.4, 2.3.2.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | FastAPI, Kafka |
| **Success Criteria** | Any critical vulnerability -> gate fails immediately; all checks pass -> gate passes; security gate is non-bypassable in deployment pipeline. |

---

# Phase 4: Operations

> **Goal**: Ship the DevOps Agent and Monitoring Agent. Enable autonomous deployment and production observability.

---

## Milestone 4.1: DevOps Agent

### Epic 4.1.1: Infrastructure Automation

**Task 4.1.1.1 — DevOps Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/devops.py`. Generates: Dockerfiles, K8s manifests, Terraform plans, CI/CD pipeline configs (GitHub Actions). Reads architecture docs to understand deployment topology. |
| **Dependencies** | 2.1.1.2, Architect Agent output |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | LLM Provider, Docker, Kubernetes, Terraform |
| **Success Criteria** | Architecture with 3 services -> Dockerfiles for each; K8s deployment + service manifests; Terraform for DB provisioning; GitHub Actions CI/CD file. |

**Task 4.1.1.2 — Dockerfile Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate optimized multi-stage Dockerfiles per service. Include: base image selection, dependency caching, build stage, runtime stage, health checks, non-root user. |
| **Dependencies** | 4.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Docker, LLM Provider |
| **Success Criteria** | Dockerfile builds successfully; image size < 200MB; layers are cached efficiently; runs as non-root; healthcheck configured. |

**Task 4.1.1.3 — Kubernetes Manifest Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate K8s manifests: Deployment, Service, ConfigMap, Secret, HPA, PDB, Ingress. Include resource requests/limits, liveness/readiness probes, anti-affinity rules. |
| **Dependencies** | 4.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Kubernetes, LLM Provider |
| **Success Criteria** | Manifests validate with `kubectl --dry-run`; resource limits set; probes configured; HPA scales 2-10 replicas; anti-affinity spreads across nodes. |

**Task 4.1.1.4 — Terraform Plan Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate Terraform HCL for cloud infrastructure: VPC, subnets, RDS/Aurora, ElastiCache, EKS cluster, IAM roles. Use modules where possible. |
| **Dependencies** | 4.1.1.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | Terraform, AWS/GCP/Azure, LLM Provider |
| **Success Criteria** | `terraform validate` passes; `terraform plan` produces sensible diff; resources tagged correctly; state stored in S3/GCS backend. |

**Task 4.1.1.5 — CI/CD Pipeline Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate GitHub Actions workflows: CI (lint, typecheck, test), CD-staging (build, push, deploy to staging, integration tests), CD-production (deploy, smoke tests, rollback on failure). |
| **Dependencies** | 4.1.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | GitHub Actions, LLM Provider |
| **Success Criteria** | CI workflow runs on PR; CD-staging deploys to staging; CD-production includes approval gate and rollback step; all workflows have timeout and concurrency limits. |

---

### Epic 4.1.2: Deployment Automation

**Task 4.1.2.1 — Container Build & Push**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `DockerOpsTool` that builds images per service, tags with git SHA, pushes to container registry. Validates image before push. |
| **Dependencies** | 4.1.1.2, 2.1.1.5 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | docker-py, subprocess |
| **Success Criteria** | Tool builds image -> tags with sha and latest -> pushes to registry -> verifies by pulling; build logs captured; build failure -> error with context. |

**Task 4.1.2.2 — Deployment Execution**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement deployment execution: apply K8s manifests via kubectl/helm, wait for rollout, verify health checks, run smoke tests. Support canary and blue-green strategies. |
| **Dependencies** | 4.1.1.3, 4.1.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | kubectl, helm, httpx |
| **Success Criteria** | Deployment applied -> rollout watches until ready -> health check passes -> smoke tests pass; canary: 10% traffic for 5 min -> promote; failure -> automatic rollback. |

**Task 4.1.2.3 — Deployment Gate Integration**

| Attribute | Detail |
|-----------|--------|
| **Description** | Integrate deployment quality gate. Post-deployment: stability (error rate, uptime), availability, performance. Score from Prometheus metrics. Threshold >= 95. Loop if fail. |
| **Dependencies** | 4.1.2.2, 2.3.2.3, 4.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | prometheus-client, Kafka |
| **Success Criteria** | Deployment completes -> deployment gate evaluates metrics; error rate > 1% -> gate fails -> rollback; all metrics green -> gate passes. |

---

## Milestone 4.2: Monitoring Agent

### Epic 4.2.1: Production Monitoring

**Task 4.2.1.1 — Monitoring Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/monitoring.py`. Continuously monitors production: queries Prometheus for metrics, analyzes logs via ELK, detects anomalies, generates alerts. |
| **Dependencies** | 1.6.2.1, 1.6.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | prometheus-client, elasticsearch-py, LLM Provider |
| **Success Criteria** | Agent polls Prometheus every 30s; detects latency spike -> alert; detects error rate increase -> alert; alerts include context and suggested actions. |

**Task 4.2.1.2 — Anomaly Detection**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement statistical anomaly detection: moving average + standard deviation on key metrics (latency, error rate, throughput, resource usage). Detect outliers that deviate > 3 sigma. |
| **Dependencies** | 4.2.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | numpy, scipy, Prometheus |
| **Success Criteria** | Steady state established over 1 hour baseline; metric spikes 5x -> anomaly detected; seasonal patterns learned; false positive rate < 5%. |

**Task 4.2.1.3 — Alert Generation & Routing**

| Attribute | Detail |
|-----------|--------|
| **Description** | Generate alerts with: severity (critical/warning/info), affected service, metric data, suggested root causes. Route critical alerts to Self-Healing agent automatically. |
| **Dependencies** | 4.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Kafka, WebSocket |
| **Success Criteria** | Anomaly detected -> alert generated -> emitted as `AlertTriggered` event; critical alerts -> Self-Healing subscription; alert appears in Grafana and WebSocket feed. |

**Task 4.2.1.4 — Log Analysis**

| Attribute | Detail |
|-----------|--------|
| **Description** | Query ELK for error patterns, correlate with metrics anomalies, identify recurring issues. Use LLM to summarize log patterns and suggest fixes. |
| **Dependencies** | 4.2.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | elasticsearch-py, LLM Provider |
| **Success Criteria** | Error cluster identified in logs -> correlated with latency spike -> LLM summarizes "5xx errors from payment service due to DB timeout" -> suggested fix generated. |

---

# Phase 5: Autonomous Recovery

> **Goal**: Ship the Self-Healing Engine. Enable the system to detect failures, diagnose root causes, generate fixes, validate them, and deploy autonomously.

---

## Milestone 5.1: Self-Healing Engine

### Epic 5.1.1: Failure Detection & Diagnosis

**Task 5.1.1.1 — Self-Healing Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `self-healing-service` FastAPI app. Subscribe to `AlertTriggered` and `FailureDetected` events. Manage incident lifecycle: DETECTED -> ANALYZING -> PATCHING -> VALIDATING -> RESOLVED / ESCALATED. |
| **Dependencies** | 4.2.1.3, 1.2.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | FastAPI, Kafka, SQLAlchemy |
| **Success Criteria** | Service subscribes to alert events; incident created in DB on alert; lifecycle transitions tracked; incident history queryable. |

**Task 5.1.1.2 — Root Cause Analysis (RCA) Engine**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `analyzer.py`. On incident: gather logs, metrics, traces around failure time; query knowledge graph for similar past incidents; use LLM to hypothesize root cause with confidence score; validate hypothesis against data. |
| **Dependencies** | 5.1.1.1, 1.4.4.3, 4.2.1.4 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | elasticsearch-py, Neo4j, LLM Provider |
| **Success Criteria** | DB timeout incident -> logs show "connection pool exhausted" -> RCA identifies "missing connection leak in /users endpoint" -> confidence 85%; similar incident in graph -> reinforces hypothesis. |

**Task 5.1.1.3 — Failure Pattern Recognition**

| Attribute | Detail |
|-----------|--------|
| **Description** | Analyze historical incidents stored in knowledge graph. Identify recurring patterns: "same bug class", "same root cause type", "same service affected". Use patterns to preemptively flag risks in new deployments. |
| **Dependencies** | 5.1.1.2, 1.4.4.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Neo4j, LLM Provider |
| **Success Criteria** | 3 incidents with "connection leak" -> pattern identified; new deployment with similar DB access pattern -> preemptive warning; pattern database grows over time. |

---

### Epic 5.1.2: Autonomous Patch Generation

**Task 5.1.2.1 — Patch Generator**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `patcher.py`. Given root cause + affected code + incident context, use LLM to generate a fix. Generate: code patch (diff), test for the fix, rollback plan. |
| **Dependencies** | 5.1.1.2, 3.1.1.4 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | LLM Provider, gitpython |
| **Success Criteria** | RCA "connection leak in /users" -> patch adds connection.close() in finally block; test verifies connections returned to pool; rollback plan is git revert. |

**Task 5.1.2.2 — Patch Validation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `validator.py`. Before deploying patch: run unit tests, run integration tests, run security scan, run the specific regression test for the bug. All must pass. |
| **Dependencies** | 5.1.2.1, 3.2.1, 3.3.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | pytest, bandit, subprocess |
| **Success Criteria** | Patch passes all existing tests; new regression test passes; security scan clean; validation failure -> patch rejected -> back to generator. |

**Task 5.1.2.3 — Autonomous Deployment of Patches**

| Attribute | Detail |
|-----------|--------|
| **Description** | If patch validated: create PR with diff + explanation, get auto-approval if confidence > 90%, deploy via canary, monitor for 10 min, promote if healthy, rollback if degraded. |
| **Dependencies** | 5.1.2.2, 4.1.2 |
| **Difficulty** | Large |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | GitHub API, kubectl, Prometheus |
| **Success Criteria** | Validated patch -> PR created with RCA summary; auto-merged if high confidence; canary deployment at 10%; metrics stable for 10 min -> full promotion; metrics degrade -> automatic rollback. |

**Task 5.1.2.4 — Self-Healing End-to-End Test**

| Attribute | Detail |
|-----------|--------|
| **Description** | Deliberately inject a failure (connection leak). Verify: detection -> RCA -> patch generation -> validation -> deployment -> recovery. Full autonomous loop. |
| **Dependencies** | 5.1.2.3 |
| **Difficulty** | Large |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Chaos engineering tools, Docker |
| **Success Criteria** | Injected leak causes errors; Monitoring detects; Self-Healing triggers; Patch validated; Canary deployed; Metrics recover; Incident resolved. Total time < 15 min. |

---

# Phase 6: Self-Learning

> **Goal**: Ship the Self-Learning Engine and Knowledge Agent. Close the loop — the system learns from every iteration and improves over time.

---

## Milestone 6.1: Self-Learning Engine

### Epic 6.1.1: Iteration Recording & Knowledge Extraction

**Task 6.1.1.1 — Self-Learning Service Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Create `self-learning-service` FastAPI app. Subscribe to `IterationRecorded` events. Implement recording, extraction, and optimization pipelines. |
| **Dependencies** | 1.2.1.3, 1.4.2.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 5 hours |
| **Required Technologies** | FastAPI, Kafka, SQLAlchemy |
| **Success Criteria** | Service starts; subscribes to iteration events; records stored in `learning_records` table; extraction pipeline triggered on batch. |

**Task 6.1.1.2 — Iteration Recorder**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `recorder.py`. Every recursive loop iteration: capture prompt, output, critique, score, final result. Store with metadata (agent, task, artifact type, duration, tokens used). |
| **Dependencies** | 6.1.1.1 |
| **Difficulty** | Easy |
| **Estimated Effort** | 4 hours |
| **Required Technologies** | SQLAlchemy, Kafka |
| **Success Criteria** | All iterations from all agents recorded; queriable by agent, artifact type, date range; no data loss on service restart. |

**Task 6.1.1.3 — Knowledge Extractor**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `extractor.py`. Analyze recorded iterations to extract: successful prompt patterns, common failure causes, effective improvement strategies, architecture patterns that pass gates on first try. |
| **Dependencies** | 6.1.1.2 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | LLM Provider, numpy, Neo4j |
| **Success Criteria** | 100 PRD iterations -> extractor identifies "PRDs with quantified success metrics pass gate faster"; pattern stored in knowledge graph; knowledge linked to source iterations for provenance. |

**Task 6.1.1.4 — Prompt Optimizer**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `optimizer.py`. Based on extracted knowledge: update agent system prompts with proven patterns, add few-shot examples from successful iterations, add anti-patterns from failures. Version prompts in git. |
| **Dependencies** | 6.1.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | LLM Provider, git |
| **Success Criteria** | Extracted pattern "use quantified success metrics" -> added to PM agent prompt; next PM run includes pattern in system prompt; prompt versioned; rollback possible. |

**Task 6.1.1.5 — Knowledge Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/knowledge.py`. Manages the knowledge graph. On new artifact: extract entities, create relationships, update embeddings. On query: search graph for related concepts. |
| **Dependencies** | 2.1.1.2, 1.4.4.2, 1.4.3.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | Neo4j, Qdrant, LLM Provider |
| **Success Criteria** | New architecture doc -> entities extracted -> relationships created in Neo4j; embeddings updated in Qdrant; query "what APIs does user service expose?" -> traverses graph -> returns endpoints. |

---

### Epic 6.1.2: Continuous Improvement Pipeline

**Task 6.1.2.1 — Learning Agent Implementation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement `agents/learning.py`. Periodically analyzes accumulated knowledge. Identifies: most effective agent configurations, optimal iteration counts, cost-efficient LLM routing strategies. |
| **Dependencies** | 6.1.1.3, 2.1.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | LLM Provider, numpy |
| **Success Criteria** | Analysis of 1000 tasks -> recommends "architecture tasks use Claude, simple tasks use DeepSeek"; recommendation implemented in LLM router; measurable cost reduction. |

**Task 6.1.2.2 — Pattern Application Engine**

| Attribute | Detail |
|-----------|--------|
| **Description** | Automatically apply learned patterns to new tasks. Before agent runs: query knowledge graph for similar past tasks, retrieve successful patterns, inject into agent context. |
| **Dependencies** | 6.1.1.5 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Neo4j, LLM Provider |
| **Success Criteria** | New task "build user auth" -> graph query finds 3 similar past auth tasks -> patterns injected into context -> agent outputs based on proven patterns; first-pass gate success rate improves. |

**Task 6.1.2.3 — Learning Loop Validation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Run 10 identical tasks over time. Verify: iteration count decreases, first-pass gate success rate increases, output quality score trends upward, cost per task decreases. |
| **Dependencies** | 6.1.2.1, 6.1.2.2 |
| **Difficulty** | Large |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | pytest, metrics comparison |
| **Success Criteria** | Task 1: 5 iterations to pass -> Task 10: 2 iterations to pass; cost reduced 40%; quality score increased; learning effect is measurable and sustained. |

---

## Milestone 6.2: Production Hardening

### Epic 6.2.1: Kubernetes Production Deployment

**Task 6.2.1.1 — Helm Chart Finalization**

| Attribute | Detail |
|-----------|--------|
| **Description** | Finalize Helm chart for all 12 services. Include: resource limits, HPA, PDB, anti-affinity, configmaps, secrets (via Vault), ingress, service mesh (Istio). |
| **Dependencies** | 4.1.1.3, 1.5.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | Helm, Kubernetes, Istio |
| **Success Criteria** | `helm install aisc-platform` deploys all services; all pods healthy; Istio sidecar injected; mTLS working; ingress routes traffic. |

**Task 6.2.1.2 — Terraform Production Environment**

| Attribute | Detail |
|-----------|--------|
| **Description** | Finalize Terraform for production: multi-AZ, autoscaling, managed databases (RDS PostgreSQL, ElastiCache Redis, Managed Kafka), Vault for secrets, ACM for TLS. |
| **Dependencies** | 4.1.1.4 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | Terraform, AWS/GCP/Azure |
| **Success Criteria** | `terraform apply` creates full production environment; all resources tagged; state in remote backend; plan shows no unexpected changes. |

**Task 6.2.1.3 — Disaster Recovery Plan**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement: database backups (automated, cross-region), Kafka log replication, state reconstruction from event sourcing, documented recovery runbook. |
| **Dependencies** | 6.2.1.1, 6.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | PostgreSQL WAL, Kafka MirrorMaker, Terraform |
| **Success Criteria** | DB restored from backup in < 1 hour; Kafka logs replayed -> state reconstructed; DR runbook tested; RPO < 1 hour, RTO < 4 hours. |

**Task 6.2.1.4 — Load Testing & Performance Tuning**

| Attribute | Detail |
|-----------|--------|
| **Description** | Run locust/k6 load tests against all services. Identify bottlenecks. Tune: DB connection pools, Kafka partitions, service replicas, cache hit rates. |
| **Dependencies** | 6.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | k6/locust, Prometheus, Grafana |
| **Success Criteria** | System handles 1000 req/s sustained; p95 latency < 500ms; no OOM kills; no connection pool exhaustion; load test results documented. |

---

### Epic 6.2.2: Security Hardening

**Task 6.2.2.1 — Vault Secret Management**

| Attribute | Detail |
|-----------|--------|
| **Description** | Migrate all secrets (DB passwords, API keys, JWT secrets) to HashiCorp Vault. Implement dynamic secrets for DB. Auto-rotation for all credentials. |
| **Dependencies** | 6.2.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Vault, Kubernetes Secrets CSI |
| **Success Criteria** | No secrets in config files or env vars; Vault dynamic DB credentials auto-rotate; secret access audited; Vault HA cluster. |

**Task 6.2.2.2 — Penetration Testing Automation**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement automated pen-testing in CI/CD: OWASP ZAP baseline scan, API fuzzing, SQL injection test suite. Run against staging environment before production deploy. |
| **Dependencies** | 6.2.1.1, 3.3.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | OWASP ZAP, API fuzzing tools |
| **Success Criteria** | ZAP scan runs in CI against staging; critical/medium findings block deploy; fuzzing covers all API endpoints; report generated. |

**Task 6.2.2.3 — Compliance & Audit Logging**

| Attribute | Detail |
|-----------|--------|
| **Description** | Implement audit logging for: user actions, agent decisions, deployment changes, data access. Store immutable logs. Generate compliance reports. |
| **Dependencies** | 6.1.1.2 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | ELK, immudb (immutable log) |
| **Success Criteria** | All user actions logged with actor + timestamp; agent decisions (accept/reject/escalate) logged; audit trail immutable; compliance report exportable. |

---

## Milestone 6.3: Admin Dashboard (Frontend)

### Epic 6.3.1: Dashboard Core

**Task 6.3.1.1 — React/Next.js App Scaffold**

| Attribute | Detail |
|-----------|--------|
| **Description** | Scaffold Next.js app with TypeScript, Tailwind CSS, and shadcn/ui components. Set up API client for all AISC endpoints. Connect to WebSocket gateway for real-time updates. |
| **Dependencies** | 1.5.1.1, 1.5.1.3 |
| **Difficulty** | Medium |
| **Estimated Effort** | 6 hours |
| **Required Technologies** | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| **Success Criteria** | Next.js app builds; API client auto-generates from OpenAPI spec; WebSocket connects; shadcn/ui components render. |

**Task 6.3.1.2 — Project Management UI**

| Attribute | Detail |
|-----------|--------|
| **Description** | Pages: Project list, Project detail (workflow DAG visualization), Create project (input business idea), Project settings. DAG visualization using React Flow. |
| **Dependencies** | 6.3.1.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 12 hours |
| **Required Technologies** | React Flow, Next.js |
| **Success Criteria** | Create project with idea -> submit; project list shows all projects with status; project detail shows workflow DAG with node statuses; DAG nodes color-coded by status. |

**Task 6.3.1.3 — Agent Monitoring UI**

| Attribute | Detail |
|-----------|--------|
| **Description** | Pages: Agent list (status, current task, execution history), Agent detail (live conversation view, tool invocations, token usage). Real-time updates via WebSocket. |
| **Dependencies** | 6.3.1.1 |
| **Difficulty** | Large |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | Next.js, WebSocket |
| **Success Criteria** | Agent list shows real-time status; agent detail shows live conversation stream; tool invocations displayed with results; token usage chart. |

**Task 6.3.1.4 — Artifact & Quality Gate UI**

| Attribute | Detail |
|-----------|--------|
| **Description** | Pages: Artifact viewer (rendered markdown, code, Mermaid diagrams), Version history diff, Score history (chart showing improvement over iterations), Quality gate status. |
| **Dependencies** | 6.3.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 10 hours |
| **Required Technologies** | mermaid.js, diff viewer, recharts |
| **Success Criteria** | Artifact renders markdown/Mermaid/code with syntax highlighting; version diff shows changes; score chart shows upward trend over iterations; gate status clearly displayed. |

**Task 6.3.1.5 — Operations Dashboard**

| Attribute | Detail |
|-----------|--------|
| **Description** | Pages: Deployment history, Incident list with RCA/patch details, Metrics dashboard (Grafana embed), Alert feed, System health overview. |
| **Dependencies** | 6.3.1.1, 6.2.1.1 |
| **Difficulty** | Medium |
| **Estimated Effort** | 8 hours |
| **Required Technologies** | Next.js, Grafana embed, WebSocket |
| **Success Criteria** | Deployment timeline with status; incident cards with RCA and patch links; Grafana dashboard embedded; alert feed real-time; health overview shows all services green/red. |

---

# Summary

## Effort Estimates by Phase

| Phase | Tasks | Total Hours | Calendar Weeks (2 devs) |
|-------|-------|-------------|--------------------------|
| Phase 1: Core Infrastructure | 27 | 150 | 10 |
| Phase 2: Core Agents | 30 | 222 | 14 |
| Phase 3: Development Agents | 18 | 138 | 9 |
| Phase 4: Operations | 12 | 86 | 6 |
| Phase 5: Autonomous Recovery | 8 | 69 | 5 |
| Phase 6: Self-Learning & Hardening | 19 | 176 | 11 |
| **Total** | **114** | **841** | **55 weeks** |

## Difficulty Distribution

| Difficulty | Count | Percentage |
|------------|-------|------------|
| Easy | 20 | 17.5% |
| Medium | 68 | 59.6% |
| Large | 26 | 22.8% |

## Dependency Graph (Phase Level)

```
Phase 1 (Foundation)
   |
   v
Phase 2 (Core Agents + Quality Framework)
   |
   v
Phase 3 (Development Agents)
   |
   v
Phase 4 (Operations)
   |
   v
Phase 5 (Autonomous Recovery)
   |
   v
Phase 6 (Self-Learning + Hardening)
```

## Critical Path

```
1.1.1.1 (Monorepo)
  -> 1.1.1.4 (Dev Env)
    -> 1.2.1.3 (Event Bus)
      -> 1.4.2.1 (Memory Service)
        -> 2.1.1.2 (Agent Base)
          -> 2.2.2.1 (PM Agent)
            -> 2.3.2.3 (Loop Controller) [KEY MILESTONE: First loop works]
              -> 2.4.1.3 (RAG Query)
                -> 3.1.1.1 (Developer Agent)
                  -> 5.1.2.3 (Autonomous Patch Deploy)
                    -> 6.1.1.4 (Prompt Optimizer)
```

## MVP Scope (Phase 1 + 2)

Minimum viable system: one agent (PM) goes through one recursive loop. 

- **Deliverable**: Given a business idea, system produces a PRD >= 90 quality score, looping if needed.
- **Effort**: ~372 hours (~23 weeks with 2 devs)
- **Services**: Auth, Orchestrator, Agent Runtime, Memory, Scoring, Quality Gate, WebSocket GW, Observability
- **Agents**: Product Manager, Reviewer (x3), Consensus, Improvement

---

*This project plan is ready for sprint planning and task assignment.*
