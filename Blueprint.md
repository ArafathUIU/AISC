# AISC — Technical Blueprint

**Author**: Lead Systems Architect  
**Date**: 2026-06-18  
**Status**: Draft — Ready for Review

---

## 1. System Architecture Document

### 1.1 System Overview

AISC is an event-driven, multi-agent, recursive quality-gated software engineering platform. It is organized into 13 major subsystems, each operating as an independent microservice communicating over a central event bus.

### 1.2 Major Systems Identified

| # | System | Description |
|---|--------|-------------|
| 1 | **Orchestrator Engine** | CEO-level coordination; schedules agents, manages workflows, tracks dependencies, handles escalations |
| 2 | **Agent Runtime** | Hosts and executes all AI agents, manages their lifecycle, tools, and memory access |
| 3 | **Recursive Quality Engine** | The core loop engine — manages generate→review→critique→improve→evaluate→score cycles per artifact |
| 4 | **Scoring Engine** | Evaluates artifacts against predefined metrics; produces numeric scores; determines gate pass/fail |
| 5 | **Quality Gate Service** | Defines and enforces quality thresholds per artifact type; decides whether to loop or advance |
| 6 | **RAG System** | Retrieval-Augmented Generation pipeline — embedding, vector search, reranking, context assembly |
| 7 | **Memory System** | Multi-tier memory: short-term (Redis), long-term (PostgreSQL), semantic (Vector DB), relational (Neo4j) |
| 8 | **Event Bus** | Central nervous system — Kafka/RabbitMQ/NATS — all actions emit events; decouples all services |
| 9 | **Self-Learning Engine** | Records every iteration (prompt→output→critique→score→result); extracts knowledge for future improvement |
| 10 | **Self-Healing System** | Failure detection → root cause analysis → patch generation → validation → autonomous recovery |
| 11 | **Multi-Agent Debate System** | Consensus mechanism — multiple reviewers critique, consensus agent resolves, improvement agent refines |
| 12 | **Security System** | AuthN (OAuth2/JWT), AuthZ (RBAC/ABAC), encryption (AES-256/TLS 1.3), secret management (Vault) |
| 13 | **Observability System** | Metrics (Prometheus), dashboards (Grafana), structured logging (ELK), tracing (OpenTelemetry) |

---

## 2. Service Architecture (Microservices)

```
                          ┌──────────────────┐
                          │   API Gateway     │  (FastAPI + Kong/NGINX)
                          └────────┬─────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
     ┌────▼─────┐           ┌──────▼──────┐          ┌──────▼──────┐
     │  Auth    │           │ Orchestrator │          │  WebSocket  │
     │ Service  │           │   Service    │          │   Gateway   │
     └────┬─────┘           └──────┬───────┘          └──────┬──────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │    Event Bus      │
                         │ (Kafka/NATS)      │
                         └─────────┬─────────┘
                                   │
     ┌────────┬────────┬───────────┼───────────┬──────────┬────────┬────────┐
     │        │        │           │           │          │        │        │
  ┌──▼──┐ ┌──▼──┐ ┌───▼──┐  ┌────▼────┐  ┌───▼───┐  ┌───▼──┐ ┌───▼──┐ ┌───▼───┐
  │Agent│ │Quality│ │Scoring│  │  RAG    │  │Memory │  │Self- │ │Self- │ │Obser- │
  │ Run-│ │ Gate  │ │Engine │  │ Service │  │Service│  │Learn │ │Heal  │ │vabil- │
  │time │ │Service│ │       │  │         │  │       │  │Engine │ │Engine│ │ity    │
  └─────┘ └──────┘ └───────┘  └─────────┘  └───────┘  └──────┘ └─────┘ └───────┘
```

### 2.1 Microservice Inventory

| Service | Port | Responsibility | Internal DB Access |
|---------|------|----------------|-------------------|
| `api-gateway` | 80/443 | Route external requests, rate limiting, auth middleware | None |
| `auth-service` | 8001 | User auth, JWT issuance, RBAC/ABAC enforcement | PostgreSQL |
| `orchestrator-service` | 8002 | Workflow orchestration, agent scheduling, dependency resolution | PostgreSQL, Redis |
| `agent-runtime` | 8003 | Agent lifecycle, LLM API calls, tool execution | Redis (state) |
| `quality-gate-service` | 8004 | Gate definitions, threshold evaluation, loop control | PostgreSQL |
| `scoring-engine` | 8005 | Metric computation, artifact evaluation, score aggregation | PostgreSQL |
| `rag-service` | 8006 | Embedding, vector search, reranking, context assembly | Vector DB |
| `memory-service` | 8007 | Unified CRUD across all memory tiers | PostgreSQL, Redis, Vector DB, Neo4j |
| `self-learning-service` | 8008 | Iteration recording, knowledge extraction, prompt optimization | PostgreSQL |
| `self-healing-service` | 8009 | Failure detection, RCA, patch generation, validation | PostgreSQL |
| `debate-service` | 8010 | Multi-agent consensus, review coordination, resolution | Redis (state) |
| `observability-service` | 8011 | Metrics aggregation, alert evaluation, log ingestion | None (sinks to external) |
| `ws-gateway` | 8012 | Real-time WebSocket connections for UI updates | Redis (pub/sub) |

### 2.2 Technology Choices per Service

| Service | Language | Framework | Key Libraries |
|---------|----------|-----------|---------------|
| `api-gateway` | — | Kong / NGINX + Lua | rate-limiting, jwt, cors |
| `auth-service` | Python | FastAPI | python-jose, passlib, itsdangerous |
| `orchestrator-service` | Python | FastAPI | celery, networkx (DAG), celery |
| `agent-runtime` | Python | FastAPI | langchain, openai, anthropic, httpx |
| `quality-gate-service` | Python | FastAPI | pydantic |
| `scoring-engine` | Python | FastAPI | numpy, radon (code metrics) |
| `rag-service` | Python | FastAPI | sentence-transformers, qdrant-client, langchain |
| `memory-service` | Python | FastAPI | sqlalchemy, redis-py, neo4j-driver, qdrant-client |
| `self-learning-service` | Python | FastAPI | sqlalchemy, numpy |
| `self-healing-service` | Python | FastAPI | docker-py, gitpython |
| `debate-service` | Python | FastAPI | redis-py |
| `observability-service` | Python | FastAPI | prometheus-client, opentelemetry |
| `ws-gateway` | Python | FastAPI + websockets | redis-py |

---

## 3. Agent Architecture

### 3.1 Agent Inventory (15 agents identified)

| # | Agent | Role | Inputs | Outputs |
|---|-------|------|--------|---------|
| 1 | **Orchestrator Agent** | CEO / Coordinator | Project definition, human input | Task assignments, workflow DAGs |
| 2 | **Product Manager Agent** | Requirements & planning | Business ideas, market context | PRDs, User Stories, Feature Specs |
| 3 | **Research Agent** | Technology & competitor research | Research questions, tech landscape | Research Reports, Tech Recommendations, Risk Assessments |
| 4 | **Architect Agent** | System design | Requirements, constraints | Architecture Docs, API Contracts, ER Diagrams |
| 5 | **Developer Agent** | Code generation | Architecture specs, API contracts | Source code (backend/frontend/mobile) |
| 6 | **QA Agent** | Testing | Source code, requirements | Unit tests, Integration tests, E2E tests, Coverage reports |
| 7 | **Security Agent** | Security auditing | Source code, configurations | Vulnerability reports, Secret scan results, Penetration test results |
| 8 | **DevOps Agent** | Infrastructure & deployment | Application code, architecture | Dockerfiles, K8s manifests, Terraform plans, CI/CD pipelines |
| 9 | **Monitoring Agent** | Production observability | Metrics, logs, traces | Alerts, Performance reports, Anomaly flags |
| 10 | **Self-Healing Agent** | Autonomous recovery | Failure alerts, error logs | Root cause analyses, Patches, Rollback plans |
| 11 | **Knowledge Agent** | Knowledge management | All artifacts, iteration history | Structured knowledge, Updated embeddings |
| 12 | **Learning Agent** | Continuous improvement | Historical data, evaluation results | Optimized prompts, Architecture patterns, Better defaults |
| 13 | **Consensus Agent** | Debate resolution | Reviewer critiques | Final decision, Resolution rationale |
| 14 | **Improvement Agent** | Artifact refinement | Critiques, artifact, score | Improved artifact |
| 15 | **Reviewer Agents (x3)** | Peer review | Artifact to review | Critiques, scores |

### 3.2 Agent Interface (Shared Contract)

```yaml
Agent:
  id: uuid
  type: enum[orchestrator|product_manager|research|architect|developer|qa|security|devops|monitoring|self_healing|knowledge|learning|consensus|improvement|reviewer]
  status: enum[idle|busy|error|offline]
  capabilities: list[str]
  tools: list[str]
  memory_context: dict
  config:
    llm_model: str
    temperature: float
    max_tokens: int
  run(input: ArtifactContext) -> AgentResult
```

### 3.3 Agent Tools Matrix

| Tool | PM | Research | Architect | Developer | QA | Security | DevOps | Monitor | Healer |
|-----|:--:|:--------:|:---------:|:---------:|:--:|:--------:|:------:|:-------:|:------:|
| RAG Query | x | x | x | x | x | x | x | | x |
| Vector Search | x | x | x | x | | x | | | |
| Code Generation | | | | x | x | | | | |
| Static Analysis | | | | x | | x | | | |
| Test Runner | | | x | | x | | | | |
| Security Scanner | | | | | | x | | | x |
| Git Operations | | | | x | | | x | | x |
| Docker Build | | | | | | | x | | |
| K8s Deploy | | | | | | | x | | |
| DB Migration | | | x | x | | | x | | |
| Web Search | | x | | | | | | | |
| API Test | | | | | x | x | | x | |

### 3.4 Multi-Agent Debate Flow

```
Artifact Ready for Review
        │
        ▼
┌───────────────────┐
│ Orchestrator      │
│ assigns reviewers  │
└───────┬───────────┘
        │
   ┌────┼────┐
   ▼    ▼    ▼
  RevA RevB RevC     (independent review + scoring)
   │    │    │
   └────┼────┘
        ▼
┌───────────────────┐
│ Consensus Agent   │ ← aggregates critiques, checks agreement
└───────┬───────────┘
        │
   ┌────▼────┐
   │Consensus?│
   └────┬────┘
   Yes  │  No
   ▼    │    ▼
Pass   │ ┌──────────────┐
       │ │ Improvement   │
       │ │ Agent refines │
       │ └──────┬────────┘
       │        │
       │   Resubmit for review
       │
       ▼
   Advance to next phase
```

---

## 4. Database Architecture

### 4.1 Database Inventory

| Database | Technology | Purpose | Schema Type |
|----------|-----------|---------|-------------|
| **Primary DB** | PostgreSQL 15+ | Users, Projects, Tasks, Artifacts, Agent states (persistent), Evaluation history, Learning records | Relational |
| **Cache / Short-Term Memory** | Redis 7+ | Active task states, agent session state, rate limiting, Pub/Sub for WebSockets | Key-Value |
| **Vector DB** | Qdrant (primary) / FAISS (fallback) | Document embeddings, semantic search, RAG context | Vector |
| **Graph DB** | Neo4j 5+ | Project-Requirement-API-Database-Bug-Solution relationships | Property Graph |

### 4.2 PostgreSQL Schema (Core Tables)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   users      │     │   projects   │     │    tasks     │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (PK)      │◄───┐│ id (PK)      │◄───┐│ id (PK)      │
│ email        │    ││ name         │    ││ project_id(FK)│
│ password_hash│    ││ description  │    ││ type         │
│ role         │    ││ owner_id (FK)│──┐ ││ status       │
│ created_at   │    ││ status       │  │ ││ assigned_agent│
└──────────────┘    ││ created_at   │  │ ││ priority     │
                    │└──────────────┘  │ ││ input        │
                    │                  │ ││ created_at   │
┌──────────────┐    │                  │ └──────────────┘
│  artifacts   │    │                  │
├──────────────┤    │                  │ ┌──────────────┐
│ id (PK)      │    │                  │ │ evaluations  │
│ project_id   │    │                  │ ├──────────────┤
│ task_id      │    │                  │ │ id (PK)      │
│ type         │    │                  │ │ artifact_id  │
│ content      │    │                  │ │ gate_type    │
│ version      │    │                  │ │ scores (JSON)│
│ status       │    │                  │ │ passed       │
│ created_by   │────┼──────────────────┘ │ iteration    │
│ parent_id    │    │                    │ feedback     │
│ created_at   │    │                    │ created_at   │
└──────────────┘    │                    └──────────────┘
                    │
┌──────────────┐    │     ┌──────────────┐     ┌──────────────┐
│  workflows   │    │     │learning_recs │     │  agent_runs  │
├──────────────┤    │     ├──────────────┤     ├──────────────┤
│ id (PK)      │    │     │ id (PK)      │     │ id (PK)      │
│ project_id   │    │     │ artifact_type│     │ agent_id     │
│ dag (JSON)   │    │     │ prompt       │     │ task_id      │
│ current_node │    │     │ output       │     │ input        │
│ status       │    │     │ critique     │     │ output       │
└──────────────┘    │     │ score        │     │ tokens_used  │
                    │     │ final_result │     │ duration_ms  │
┌──────────────┐    │     │ extracted_knowledge│ created_at   │
│  debaters    │    │     └──────────────┘     └──────────────┘
├──────────────┤    │
│ id (PK)      │    │     ┌──────────────┐
│ artifact_id  │    │     │  incidents   │
│ consensus    │    │     ├──────────────┤
│ status       │    │     │ id (PK)      │
│ resolved_by  │    │     │ project_id   │
└──────────────┘    │     │ severity     │
                    │     │ root_cause   │
                    │     │ patch_id     │
                    │     │ status       │
                    │     └──────────────┘
                    │
                    └──────────────────────┘
```

### 4.3 Knowledge Graph (Neo4j) Node Types & Relationships

```
Nodes:
  Project, Requirement, UserStory, Feature,
  APIEndpoint, DatabaseTable, Column,
  Microservice, Deployment, Bug, Solution,
  TestCase, ArchitectureDecision, Technology

Relationships:
  (Project)-[:HAS_REQUIREMENT]->(Requirement)
  (Requirement)-[:IMPLEMENTS]->(UserStory)
  (UserStory)-[:REQUIRES]->(APIEndpoint)
  (APIEndpoint)-[:DEPENDS_ON]->(DatabaseTable)
  (Table)-[:HAS_COLUMN]->(Column)
  (Microservice)-[:EXPOSES]->(APIEndpoint)
  (Project)-[:DEPLOYS_TO]->(Deployment)
  (Bug)-[:AFFECTS]->(APIEndpoint)
  (Solution)-[:FIXES]->(Bug)
  (ArchitectureDecision)-[:JUSTIFIES]->(Technology)
  (Project)-[:USES]->(Technology)
  (TestCase)-[:COVERS]->(APIEndpoint)
```

---

## 5. Event Architecture

### 5.1 Event Types (40+ identified)

#### Project & Workflow Events
| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `ProjectCreated` | Orchestrator | All agents, Memory, Observability |
| `ProjectUpdated` | Orchestrator | Memory |
| `ProjectArchived` | Orchestrator | Memory, Learning |
| `WorkflowStarted` | Orchestrator | All involved agents |
| `WorkflowNodeCompleted` | Orchestrator | Orchestrator (self) |
| `WorkflowCompleted` | Orchestrator | Learning, Memory |
| `WorkflowFailed` | Orchestrator | Self-Healing, Observability |

#### Task & Assignment Events
| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `TaskCreated` | Orchestrator | Target Agent, Memory |
| `TaskAssigned` | Orchestrator | Target Agent, Memory, Observability |
| `TaskStarted` | Agent Runtime | Orchestrator, Memory |
| `TaskCompleted` | Agent Runtime | Orchestrator, Quality Gate, Memory |
| `TaskFailed` | Agent Runtime | Orchestrator, Self-Healing |

#### Artifact Lifecycle Events
| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `ArtifactDraftCreated` | Agent Runtime | Quality Gate, Memory |
| `ArtifactSubmittedForReview` | Agent Runtime | Debate Service, Quality Gate |
| `ArtifactReviewStarted` | Debate Service | Observability |
| `ArtifactCritiqueGenerated` | Reviewer Agents | Consensus Agent |
| `ArtifactConsensusReached` | Consensus Agent | Improvement Agent, Orchestrator |
| `ArtifactImproved` | Improvement Agent | Quality Gate |
| `ArtifactScored` | Scoring Engine | Quality Gate, Memory |
| `ArtifactApproved` | Quality Gate | Orchestrator, Memory, Learning |
| `ArtifactRejected` | Quality Gate | Orchestrator, Agent Runtime (loop back) |
| `ArtifactFinalized` | Quality Gate | Memory, Learning |

#### Quality & Loop Events
| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `QualityGateEvaluated` | Quality Gate | Observability |
| `QualityGatePassed` | Quality Gate | Orchestrator |
| `QualityGateFailed` | Quality Gate | Orchestrator, Agent Runtime |
| `RecursiveLoopStarted` | Quality Gate | Observability |
| `RecursiveLoopIteration` | Quality Gate | Learning |
| `RecursiveLoopCompleted` | Quality Gate | Learning |

#### Deployment Events
| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `DeploymentRequested` | Orchestrator | DevOps Agent |
| `BuildStarted` | DevOps Agent | Observability |
| `BuildCompleted` | DevOps Agent | Monitoring Agent |
| `BuildFailed` | DevOps Agent | Self-Healing |
| `DeploymentStarted` | DevOps Agent | Monitoring Agent, Observability |
| `DeploymentCompleted` | DevOps Agent | Orchestrator, Monitoring Agent |
| `DeploymentFailed` | DevOps Agent | Self-Healing |
| `RollbackInitiated` | Self-Healing Agent | DevOps Agent |
| `RollbackCompleted` | DevOps Agent | Orchestrator |

#### Production Events
| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `MetricAnomalyDetected` | Monitoring Agent | Self-Healing, Observability |
| `AlertTriggered` | Monitoring Agent | Self-Healing, Orchestrator |
| `FailureDetected` | Monitoring Agent | Self-Healing |
| `RootCauseIdentified` | Self-Healing Agent | Memory, Learning |
| `PatchGenerated` | Self-Healing Agent | QA Agent (for validation) |
| `PatchValidated` | QA Agent | DevOps Agent |
| `PatchDeployed` | DevOps Agent | Orchestrator, Monitoring Agent |

#### Learning Events
| Event | Publisher | Consumers |
|-------|-----------|-----------|
| `IterationRecorded` | Any agent | Self-Learning Engine |
| `KnowledgeExtracted` | Self-Learning | Knowledge Agent, Memory |
| `PromptOptimized` | Self-Learning | Agent Runtime |
| `PatternIdentified` | Self-Learning | Knowledge Graph |

### 5.2 Event Schema (Standard Envelope)

```json
{
  "event_id": "uuid",
  "event_type": "ArtifactScored",
  "timestamp": "ISO8601",
  "source_service": "scoring-engine",
  "source_agent": "qa_agent",
  "correlation_id": "uuid (traces entire workflow)",
  "project_id": "uuid",
  "task_id": "uuid",
  "payload": {}
}
```

### 5.3 Message Broker Selection

| Criteria | Kafka | RabbitMQ | NATS |
|----------|-------|----------|------|
| Throughput | Very High | Medium | High |
| Persistence | Yes (log) | Yes | Optional |
| Complexity | High | Medium | Low |
| Recommended | Production | — | — |

**Decision**: Kafka for production (event sourcing, replay capability). NATS as lightweight option for development.

---

## 6. Communication Protocol

### 6.1 API Architecture

| Layer | Protocol | Format | Description |
|-------|----------|--------|-------------|
| External (Frontend → API) | HTTPS/2 | REST + JSON | User-facing API |
| Internal (Service → Service) | HTTPS/2 | gRPC (primary) / REST (fallback) | Inter-service sync calls |
| Async (Service → Service) | Kafka | Protobuf | Event-driven communication |
| Real-time (Server → Client) | WSS | JSON | WebSocket for UI updates |
| Agent Messages | Kafka + Redis | JSON | Agent-to-agent coordination |

### 6.2 Agent Communication Protocol (ACP)

```json
{
  "message_id": "uuid",
  "correlation_id": "uuid",
  "conversation_id": "uuid",
  "sender": {
    "agent_id": "uuid",
    "agent_type": "architect_agent",
    "service": "agent-runtime"
  },
  "receiver": {
    "agent_id": "uuid",
    "agent_type": "developer_agent"
  },
  "message_type": "task_handoff | review_request | critique | query | response",
  "priority": "low | medium | high | critical",
  "task_ref": {
    "task_id": "uuid",
    "artifact_id": "uuid"
  },
  "payload": {},
  "created_at": "ISO8601",
  "ttl": 3600
}
```

### 6.3 REST API Endpoints (Key Resources)

```
/api/v1
├── /auth
│   ├── POST   /login
│   ├── POST   /register
│   ├── POST   /refresh
│   └── GET    /me
├── /projects
│   ├── POST   /                          — Create project
│   ├── GET    /                          — List projects
│   ├── GET    /{project_id}              — Get project
│   ├── PUT    /{project_id}              — Update project
│   ├── DELETE /{project_id}              — Archive project
│   ├── GET    /{project_id}/workflow     — Get current workflow state
│   └── POST   /{project_id}/start        — Start autonomous development
├── /tasks
│   ├── GET    /                          — List tasks (filtered)
│   ├── GET    /{task_id}                 — Get task detail
│   ├── GET    /{task_id}/artifacts       — Get task artifacts
│   └── GET    /{task_id}/iterations      — Get recursive loop history
├── /agents
│   ├── GET    /                          — List agents & status
│   ├── GET    /{agent_id}                — Get agent detail
│   ├── GET    /{agent_id}/runs           — Get agent execution history
│   └── POST   /{agent_id}/assign         — Manually assign task
├── /artifacts
│   ├── GET    /{artifact_id}             — Get artifact
│   ├── GET    /{artifact_id}/versions    — Get version history
│   ├── GET    /{artifact_id}/scores      — Get evaluation history
│   └── GET    /{artifact_id}/critiques   — Get critique history
├── /quality-gates
│   ├── GET    /                          — List gate definitions
│   ├── GET    /{gate_id}                 — Get gate detail
│   └── GET    /{gate_id}/history         — Get gate evaluation history
├── /rag
│   ├── POST   /query                     — Query RAG pipeline
│   └── POST   /ingest                    — Ingest documents
├── /memory
│   ├── POST   /store                     — Store in memory
│   ├── GET    /search?q=&type=           — Search across memory
│   └── GET    /context/{agent_id}        — Get agent memory context
├── /knowledge-graph
│   ├── GET    /query?cypher=             — Run Cypher query
│   └── GET    /entity/{type}/{id}/relations — Get entity relationships
├── /debates
│   ├── GET    /{debate_id}               — Get debate state
│   ├── GET    /{debate_id}/critiques     — Get all critiques
│   └── GET    /{debate_id}/resolution    — Get resolution
├── /deployments
│   ├── POST   /                          — Trigger deployment
│   ├── GET    /{deployment_id}           — Get deployment status
│   └── GET    /{deployment_id}/logs      — Get deployment logs
├── /monitoring
│   ├── GET    /metrics                   — Get aggregated metrics
│   ├── GET    /alerts                    — Get active alerts
│   └── GET    /health                    — System health check
├── /incidents
│   ├── GET    /                          — List incidents
│   ├── GET    /{incident_id}             — Get incident detail
│   ├── GET    /{incident_id}/rca         — Get root cause analysis
│   └── GET    /{incident_id}/patch       — Get generated patch
└── /learning
    ├── GET    /insights                  — Get learned improvements
    └── GET    /patterns                  — Get identified patterns
```

---

## 7. Deployment Architecture

### 7.1 Containerization Strategy

```
┌─────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                  │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────┐     │
│  │   Ingress (Nginx)  │  │  Certificate Mgr    │     │
│  └────────┬───────────┘  └────────────────────┘     │
│           │                                          │
│  ┌────────▼──────────────────────────────────────┐  │
│  │              API Gateway (Kong)                │  │
│  └────────┬──────────────────────────────────────┘  │
│           │                                          │
│  ┌────────▼──────────────────────────────────────┐  │
│  │            Service Mesh (Istio/Linkerd)        │  │
│  │         mTLS, Traffic split, Retry             │  │
│  └────────┬──────────────────────────────────────┘  │
│           │                                          │
│  ┌────────┼────────┬────────┬────────┬────────┐     │
│  │        │        │        │        │        │     │
│  ▼        ▼        ▼        ▼        ▼        ▼     │
│ ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐   │
│ │Auth  ││Orch  ││Agent ││Gate  ││Score ││RAG   │   │
│ │Svc   ││Svc   ││RT    ││Svc   ││Svc   ││Svc   │   │
│ └──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘   │
│    │       │       │       │       │       │         │
│ ┌──▼───┐┌──▼───┐┌──▼───┐┌──▼───┐┌──▼───┐┌──▼───┐   │
│ │Mem   ││Learn ││Heal  ││Debate││Obser ││WS    │   │
│ │Svc   ││Svc   ││Svc   ││Svc   ││Svc   ││GW    │   │
│ └──┬───┘└──────┘└──┬───┘└──────┘└──────┘└──────┘   │
│    │               │                                 │
└────┼───────────────┼─────────────────────────────────┘
     │               │
┌────▼───────────────▼─────────────────────────────────┐
│              Data Plane (StatefulSets)                │
│                                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │PostgreSQL│ │  Redis   │ │  Qdrant  │ │  Neo4j   ││
│  │ Cluster  │ │ Cluster  │ │ Cluster  │ │ Cluster  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                       │
│  ┌──────────┐ ┌──────────┐                           │
│  │  Kafka   │ │  Vault   │                           │
│  │ Brokers  │ │ (Secrets)│                           │
│  └──────────┘ └──────────┘                           │
└───────────────────────────────────────────────────────┘
```

### 7.2 Infrastructure as Code

| Component | Tool | Configuration |
|-----------|------|---------------|
| K8s Cluster | Terraform (EKS/GKE/AKS) | `infra/terraform/k8s/` |
| Networking | Terraform | VPC, Subnets, Security Groups |
| Databases | Terraform + Helm | Managed (RDS/Cloud SQL) or self-hosted |
| CI/CD | GitHub Actions | `.github/workflows/` |
| Container Registry | ECR/GCR/ACR | Per-service repos |
| Secret Mgmt | HashiCorp Vault | Dynamic secrets, auto-rotation |

### 7.3 CI/CD Pipeline

```
Git Push
  │
  ▼
┌─────────────┐
│ Lint & Type │
│ Check       │
└──────┬──────┘
       ▼
┌─────────────┐
│ Unit Tests  │
└──────┬──────┘
       ▼
┌─────────────┐
│ Build Image │
└──────┬──────┘
       ▼
┌─────────────┐
│ Security    │
│ Scan        │
└──────┬──────┘
       ▼
┌─────────────┐
│ Push to     │
│ Registry    │
└──────┬──────┘
       ▼
┌─────────────┐
│ Deploy to   │
│ Staging     │
└──────┬──────┘
       ▼
┌─────────────┐
│ Integration │
│ Tests       │
└──────┬──────┘
       ▼
┌─────────────┐
│ Quality Gate│── Fail ──► Rollback
│ (score≥95)  │
└──────┬──────┘
       ▼  Pass
┌─────────────┐
│ Deploy to   │
│ Production  │
└─────────────┘
```

---

## 8. Folder Structure (Monorepo)

```
aisc/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd-staging.yml
│       └── cd-production.yml
├── services/
│   ├── api-gateway/
│   │   ├── kong/                    # Kong declarative config
│   │   └── Dockerfile
│   ├── auth-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   └── middleware/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── orchestrator-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── engine/
│   │   │   │   ├── workflow.py
│   │   │   │   ├── scheduler.py
│   │   │   │   └── dependency.py
│   │   │   ├── routes/
│   │   │   └── events/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── agent-runtime/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── agents/
│   │   │   │   ├── base.py
│   │   │   │   ├── orchestrator.py
│   │   │   │   ├── product_manager.py
│   │   │   │   ├── research.py
│   │   │   │   ├── architect.py
│   │   │   │   ├── developer.py
│   │   │   │   ├── qa.py
│   │   │   │   ├── security.py
│   │   │   │   ├── devops.py
│   │   │   │   ├── monitoring.py
│   │   │   │   ├── self_healing.py
│   │   │   │   ├── knowledge.py
│   │   │   │   ├── learning.py
│   │   │   │   ├── consensus.py
│   │   │   │   ├── improvement.py
│   │   │   │   └── reviewer.py
│   │   │   ├── tools/
│   │   │   │   ├── code_generation.py
│   │   │   │   ├── static_analysis.py
│   │   │   │   ├── test_runner.py
│   │   │   │   ├── security_scanner.py
│   │   │   │   ├── rag_client.py
│   │   │   │   ├── git_ops.py
│   │   │   │   ├── docker_ops.py
│   │   │   │   └── web_search.py
│   │   │   ├── llm/
│   │   │   │   ├── base.py
│   │   │   │   ├── openai.py
│   │   │   │   ├── anthropic.py
│   │   │   │   ├── deepseek.py
│   │   │   │   └── router.py      # Routes to cheapest/best model
│   │   │   └── events/
│   │   ├── prompts/                # Agent system prompts
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── quality-gate-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── gates/
│   │   │   │   ├── requirements.py
│   │   │   │   ├── architecture.py
│   │   │   │   ├── code.py
│   │   │   │   ├── testing.py
│   │   │   │   └── deployment.py
│   │   │   ├── loop_controller.py
│   │   │   └── routes/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── scoring-engine/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── metrics/
│   │   │   │   ├── completeness.py
│   │   │   │   ├── clarity.py
│   │   │   │   ├── complexity.py
│   │   │   │   ├── security.py
│   │   │   │   ├── performance.py
│   │   │   │   └── test_coverage.py
│   │   │   ├── evaluator.py
│   │   │   └── routes/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── rag-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── embedding/
│   │   │   ├── retrieval/
│   │   │   ├── reranking/
│   │   │   ├── ingestion/
│   │   │   └── routes/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── memory-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── stores/
│   │   │   │   ├── postgres.py
│   │   │   │   ├── redis.py
│   │   │   │   ├── qdrant.py
│   │   │   │   └── neo4j.py
│   │   │   ├── routes/
│   │   │   └── models/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── self-learning-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── recorder.py
│   │   │   ├── extractor.py
│   │   │   ├── optimizer.py
│   │   │   └── routes/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── self-healing-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── detector.py
│   │   │   ├── analyzer.py       # RCA
│   │   │   ├── patcher.py
│   │   │   ├── validator.py
│   │   │   └── routes/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── debate-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── coordinator.py
│   │   │   ├── consensus.py
│   │   │   └── routes/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── observability-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── metrics/
│   │   │   ├── alerts/
│   │   │   └── routes/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── ws-gateway/
│       ├── src/
│       │   ├── main.py
│       │   ├── handlers/
│       │   └── pubsub.py
│       ├── requirements.txt
│       └── Dockerfile
├── libs/                           # Shared libraries
│   ├── aisc-proto/                 # Protobuf definitions
│   │   ├── events.proto
│   │   ├── agent.proto
│   │   └── artifact.proto
│   ├── aisc-models/                # Shared Pydantic models
│   │   ├── artifact.py
│   │   ├── event.py
│   │   ├── agent.py
│   │   └── quality.py
│   ├── aisc-events/                # Event publishing/consuming utils
│   │   ├── publisher.py
│   │   ├── consumer.py
│   │   └── types.py
│   └── aisc-utils/                 # Common utilities
│       ├── logging.py
│       ├── tracing.py
│       └── config.py
├── infra/
│   ├── terraform/
│   │   ├── k8s/
│   │   ├── databases/
│   │   └── networking/
│   ├── helm/
│   │   ├── aisc-platform/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   ├── values-staging.yaml
│   │   │   ├── values-production.yaml
│   │   │   └── templates/
│   │   │       ├── auth-service.yaml
│   │   │       ├── orchestrator-service.yaml
│   │   │       ├── agent-runtime.yaml
│   │   │       └── ...
│   └── docker-compose/
│       ├── docker-compose.yml      # Local dev
│       ├── docker-compose.override.yml
│       └── docker-compose.prod.yml
├── docs/
│   ├── architecture/
│   ├── agents/
│   ├── apis/
│   └── operations/
├── scripts/
│   ├── dev-setup.sh
│   ├── db-migrate.sh
│   └── seed-data.sh
├── frontend/                       # Optional: admin dashboard
│   ├── src/
│   ├── package.json
│   └── ...
├── docker-compose.yml              # Root dev compose
├── Makefile
├── pyproject.toml
├── .env.example
├── .gitignore
└── project.MD
```

---

## 9. All Recursive Quality Loops

| Loop | Triggered By | Artifacts | Gate Metrics | Threshold | Max Iterations |
|------|-------------|-----------|-------------|-----------|----------------|
| **Requirements Loop** | PM Agent output | PRD, User Stories | Completeness, Clarity, Consistency, Feasibility, Business Alignment | ≥90 | 5 |
| **Architecture Loop** | Architect Agent output | Architecture docs, API contracts, ERDs | Scalability, Reliability, Security, Maintainability, Cost Efficiency | ≥90 | 5 |
| **Development Loop** | Developer Agent output | Source code | Complexity, Maintainability, Testability, Performance, Security | ≥92 | 7 |
| **Testing Loop** | QA Agent output | Test suites, coverage reports | Coverage %, Mutation Score, Reliability, Edge Cases | ≥95 | 5 |
| **Deployment Loop** | DevOps Agent output | Running deployment | Stability, Availability, Performance | ≥95 | 3 |
| **Debate Loop** (nested) | Any review | Critiques, improved artifact | Reviewer agreement %, Critique resolution | ≥80% consensus | 3 |

### Loop Controller Algorithm

```
loop_control(artifact, gate_type, max_iterations):
    iteration = 1
    while iteration <= max_iterations:
        event = emit(LoopIteration, {artifact, iteration})
        agent.generate_or_improve(artifact)
        score = scoring_engine.evaluate(artifact, gate_type)
        event = emit(ArtifactScored, {artifact, score})
        if score >= gate.threshold:
            emit(QualityGatePassed, {artifact, score, iteration})
            return ACCEPT
        critiqued = review_agent.critique(artifact, score)
        artifact = improvement_agent.refine(artifact, critiqued)
        iteration += 1
    emit(QualityGateFailed, {artifact, score, iteration})
    return REJECT | ESCALATE
```

---

## 10. Risk Analysis

### 10.1 Critical Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| R1 | **AI Hallucination** — agents generate plausible but incorrect implementations | Critical | High | Multi-agent cross-validation, RAG grounding, factuality scoring metric, human-in-the-loop for architecture decisions |
| R2 | **Infinite Recursive Loops** — quality threshold never met, system loops indefinitely | Critical | Medium | Hard max iterations per loop type, escalation to Orchestrator after threshold, progressive threshold relaxation |
| R3 | **Token Cost Explosion** — recursive refinement consumes massive LLM tokens | High | High | Token budgets per task, cost-aware LLM router (route simple tasks to cheaper models), caching of stable artifacts |
| R4 | **Agent Coordination Deadlocks** — agents wait indefinitely for each other | High | Medium | Timeouts on all inter-agent messages, deadlock detection in Orchestrator, priority-based preemption |
| R5 | **External LLM API Dependency** — OpenAI/Anthropic outage blocks entire system | High | Medium | Multi-provider failover (OpenAI → Anthropic → DeepSeek → local Llama), offline fallback mode |
| R6 | **Generated Code Security** — AI-generated code contains vulnerabilities | Critical | High | Mandatory Security Agent gate before deployment, SAST/DAST in pipeline, no code deploys without passing security gate |
| R7 | **Test Reliability** — AI-written tests passing AI-written code (circular validation) | High | High | Mutation testing, property-based testing, human-reviewed test templates, adversarial test generation |
| R8 | **Knowledge Drift** — Self-learning engine reinforces bad patterns over time | Medium | Medium | Periodic human audit of learned patterns, provenance tracking, rollback of harmful knowledge |
| R9 | **Consensus Deadlock** — Reviewers cannot agree, debate never resolves | Medium | Low | Escalation to human after 3 rounds, tiebreaker by Orchestrator, weighted voting by agent credibility |
| R10 | **Database Overload** — Recursive loops generate massive iteration history | Medium | Medium | Retention policies, aggregation of old iterations, tiered storage |

### 10.2 Operational Risks

| Risk | Mitigation |
|------|------------|
| Production deployment of AI-generated code causes outage | Canary deployments, automated rollback on anomaly detection, gradual traffic shifting |
| Event bus failure loses critical messages | At-least-once delivery, event sourcing with replay, dead letter queues |
| Vector DB index corruption degrades RAG quality | Regular re-indexing, quality monitoring on retrieval precision |
| Configuration drift between environments | GitOps, Terraform state locking, automated drift detection |

### 10.3 Strategic Risks

| Risk | Mitigation |
|------|------------|
| Over-engineering — building too much before validating core loops | Phase 1 MVP: Orchestrator + 1 Agent + 1 Quality Gate; validate recursive loop works end-to-end |
| LLM model deprecation — providers retire models | Abstraction layer over LLM APIs, prompt templates versioned, model migration testing |
| Scope creep — trying to support too many frameworks | Start with Python/FastAPI only; add frameworks based on validated demand |

---

## Summary

| Dimension | Count |
|-----------|-------|
| Major Systems | 13 |
| Microservices | 12 (+ API Gateway) |
| AI Agents | 15 |
| Databases | 4 (PostgreSQL, Redis, Qdrant, Neo4j) |
| External Dependencies | 12+ |
| REST API Resource Groups | 13 |
| Event Types | 40+ |
| Recursive Quality Loops | 6 |
| Identified Risks | 13 |

---

*This blueprint is ready for technical review.*
