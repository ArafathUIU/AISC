# AISC — System Architecture

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Executive Summary

AISC (Autonomous AI Software Company) is an event-driven, multi-agent, recursive quality-gated software engineering platform. It emulates an entire software organization using 15 specialized AI agents orchestrated through a central event bus, producing and continuously refining software artifacts until predefined quality thresholds are met.

---

## 2. System Overview

```
                              Human (UI / API)
                                    |
                    ┌───────────────┼───────────────┐
                    |               |               |
              ┌─────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
              │ Kong API   │  │ WebSocket  │  │ Auth       │
              │ Gateway    │  │ Gateway    │  │ Service    │
              └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                    |               |               |
                    └───────────────┼───────────────┘
                                    |
                          ┌─────────▼─────────┐
                          │    Event Bus      │
                          │  (Kafka / NATS)   │
                          └─────────┬─────────┘
                                    |
     ┌──────────┬──────────┬───────┼───────┬──────────┬──────────┬──────────┐
     |          |          |       |       |          |          |          |
┌────▼────┐┌────▼────┐┌────▼────┐┌─▼──────┐┌▼──────┐┌──▼────┐┌───▼───┐┌───▼──────┐
│Orches-  ││Agent    ││Quality  ││Scoring ││RAG    ││Memory ││Self-  ││Self-     │
│trator   ││Runtime  ││Gate Svc ││Engine  ││Service││Service││Learn  ││Heal      │
│Service  ││         ││         ││        ││       ││       ││Engine ││Engine    │
└────┬────┘└────┬────┘└────┬────┘└─┬──────┘└┬──────┘└──┬────┘└───┬───┘└───┬──────┘
     |          |          |       |       |          |          |          |
     └──────────┴──────────┴───────┼───────┴──────────┴──────────┴──────────┘
                                   |
                          ┌────────▼────────┐
                          │  Data Plane     │
                          │  PostgreSQL     │
                          │  Redis          │
                          │  Qdrant         │
                          │  Neo4j          │
                          │  Kafka Brokers  │
                          │  Vault          │
                          └─────────────────┘
```

---

## 3. The 13 Major Systems

| # | System | Service Name | Port | Description |
|---|--------|-------------|------|-------------|
| 1 | **Orchestrator Engine** | `orchestrator-service` | 8002 | CEO-level coordination; DAG workflow engine; agent scheduling; dependency resolution; escalation routing |
| 2 | **Agent Runtime** | `agent-runtime` | 8003 | Hosts all AI agents; manages lifecycle (CREATED->IDLE->BUSY->ERROR->TERMINATED); LLM provider abstraction; tool execution framework |
| 3 | **Recursive Quality Engine** | `quality-gate-service` | 8004 | Core loop engine; manages generate->review->critique->improve->evaluate->score cycles; loop controller |
| 4 | **Scoring Engine** | `scoring-engine` | 8005 | 27 metrics across 6 gates; evaluates artifacts 0-100; produces structured scoring results |
| 5 | **RAG System** | `rag-service` | 8006 | Embedding generation; vector search; cross-encoder reranking; context assembly; document ingestion |
| 6 | **Memory System** | `memory-service` | 8007 | 4-tier unified memory: PostgreSQL (long-term), Redis (short-term), Qdrant (semantic), Neo4j (graph) |
| 7 | **Event Bus** | Kafka Cluster | 9092 | 40+ event types; Protobuf serialization; at-least-once delivery; dead-letter queues; schema registry |
| 8 | **Self-Learning Engine** | `self-learning-service` | 8008 | Iteration recording; knowledge extraction; prompt optimization; pattern identification |
| 9 | **Self-Healing System** | `self-healing-service` | 8009 | Failure detection->RCA->patch generation->validation->autonomous canary deployment |
| 10 | **Multi-Agent Debate System** | `debate-service` | 8010 | 3 reviewer agents + consensus agent + improvement agent; resolves disagreements |
| 11 | **Security System** | `auth-service` | 8001 | OAuth2/JWT; RBAC/ABAC; AES-256/TLS 1.3; Vault secret management; audit logging |
| 12 | **Observability System** | `observability-service` | 8011 | Prometheus metrics; Grafana dashboards; ELK logging; OpenTelemetry tracing; structured logging |
| 13 | **API Gateway** | Kong + `ws-gateway` | 80/443 + 8012 | Route external traffic; JWT validation; rate limiting; CORS; WebSocket connections |

---

## 4. Core Innovation: Recursive Quality-Gated Engineering

```
Generate -> Review -> Critique -> Improve -> Evaluate -> Score
                                                          |
                                              ┌───────────▼───────────┐
                                              │ Score >= Threshold?    │
                                              └───────────┬───────────┘
                                     No (Loop)            | Yes (Advance)
                                              |           |
                                              └───────────┘
```

Every artifact (PRD, architecture, code, tests, security report, deployment) must pass through this cycle. The system does not merely generate software — it continuously engineers better software through recursive refinement.

---

## 5. Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.12+ | All backend services |
| **API Framework** | FastAPI | 0.111+ | Async REST APIs |
| **LLM Providers** | OpenAI, Anthropic, DeepSeek, Ollama | Latest | AI agent intelligence |
| **Event Bus** | Apache Kafka | 3.7+ | Async service communication |
| **Primary Database** | PostgreSQL | 15+ | Long-term persistent storage |
| **Cache** | Redis | 7.2+ | Short-term memory, pub/sub, queues |
| **Vector DB** | Qdrant | 1.9+ | Semantic search, embeddings |
| **Graph DB** | Neo4j | 5.x | Knowledge graph, relationships |
| **API Gateway** | Kong | 3.x | External request routing |
| **Service Mesh** | Istio | 1.22+ | mTLS, traffic management |
| **Container** | Docker | 26+ | Application packaging |
| **Orchestration** | Kubernetes | 1.30+ | Container orchestration |
| **IaC** | Terraform | 1.9+ | Cloud infrastructure |
| **CI/CD** | GitHub Actions | — | Automated pipelines |
| **Secret Mgmt** | HashiCorp Vault | 1.17+ | Secrets management |
| **Monitoring** | Prometheus + Grafana | Latest | Metrics + dashboards |
| **Logging** | ELK Stack | 8.x | Centralized logging |
| **Tracing** | OpenTelemetry + Jaeger | Latest | Distributed tracing |
| **Frontend** | Next.js / React | 14+ | Admin dashboard |
| **Serialization** | Protobuf | v3 | Event schemas |
| **Type Checking** | mypy | 1.10+ | Static type checking |
| **Linting** | ruff | 0.5+ | Fast Python linting |

---

## 6. 15 AI Agents

| # | Agent | Phase | Function |
|---|-------|-------|----------|
| 1 | Orchestrator | P2 | CEO — coordinates all agents, manages workflows |
| 2 | Product Manager | P2 | Requirements, PRDs, user stories, roadmaps |
| 3 | Research | P2 | Technology evaluation, competitor analysis |
| 4 | Architect | P2 | System design, API contracts, DB schemas |
| 5 | Developer | P3 | Code generation (backend + frontend) |
| 6 | QA | P3 | Test generation, coverage, mutation testing |
| 7 | Security | P3 | Vulnerability scanning, secret detection, pen-testing |
| 8 | DevOps | P4 | Docker, K8s, Terraform, CI/CD, deployment |
| 9 | Monitoring | P4 | Anomaly detection, alerting, log analysis |
| 10 | Self-Healing | P5 | Failure detection, RCA, patch generation, auto-recovery |
| 11 | Knowledge | P6 | Knowledge graph management, embedding updates |
| 12 | Learning | P6 | Pattern extraction, prompt optimization |
| 13 | Consensus | P2 | Debate resolution |
| 14 | Improvement | P2 | Artifact refinement from critiques |
| 15 | Reviewer (x3) | P2 | Independent artifact review |

---

## 7. 6 Recursive Quality Loops

| Loop | Artifacts | Metrics | Threshold | Max Iterations |
|------|-----------|---------|-----------|:--------------:|
| Requirements | PRD, User Stories, Feature Specs | Completeness, Clarity, Consistency, Feasibility, Business Alignment | 90 | 5 |
| Architecture | Architecture Docs, API Contracts, ERDs | Scalability, Reliability, Security, Maintainability, Cost Efficiency | 90 | 5 |
| Code | Source Code | Complexity, Maintainability, Testability, Performance, Security | 92 | 7 |
| Testing | Tests, Coverage Reports | Coverage, Mutation Score, Reliability, Edge Cases | 95 | 5 |
| Security | Security Reports | Vulnerability Scan, LLM Review, Secrets, Dependencies, Compliance | 98 | 3 |
| Deployment | Running Deployments | Stability, Availability, Performance | 95 | 3 |

---

## 8. Communication Patterns

```
Synchronous (REST/gRPC): Service-to-service direct calls for CRUD operations
Asynchronous (Kafka):    Event-driven for workflow state changes, agent coordination
Real-time (WebSocket):   UI updates, live agent conversation streaming
Pub/Sub (Redis):         WebSocket gateway broadcasting to connected clients
```

---

## 9. Deployment Topology

```
┌─────────────────────────────────────────────────┐
│              Kubernetes Cluster                  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Ingress  │  │ Cert Mgr │  │ Istio    │      │
│  │ (Nginx)  │  │          │  │ (mTLS)   │      │
│  └────┬─────┘  └──────────┘  └──────────┘      │
│       │                                          │
│  ┌────▼─────────────────────────────────────┐   │
│  │         Kong API Gateway                  │   │
│  └────┬─────────────────────────────────────┘   │
│       │                                          │
│  ┌────▼─────────────────────────────────────┐   │
│  │         12 Microservices (Stateless)      │   │
│  │  Auth | Orch | Agent | Gate | Score |    │   │
│  │  RAG | Memory | Learn | Heal | Debate |  │   │
│  │  Observability | WS Gateway              │   │
│  └────┬─────────────────────────────────────┘   │
│       │                                          │
│  ┌────▼─────────────────────────────────────┐   │
│  │         Data Plane (StatefulSets)         │   │
│  │  PostgreSQL | Redis | Qdrant | Neo4j     │   │
│  │  Kafka | Vault                            │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 10. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Event-driven architecture** | Decouples services; enables replay; scales independently; fits agent coordination model |
| **4-tier memory** | Different access patterns require different storage: sub-ms (Redis), relational (PG), semantic (Qdrant), graph (Neo4j) |
| **Recursive loops over single-pass** | Quality is emergent; single-pass generation produces unreliable output |
| **Multi-agent debate** | Single-agent bias is real; consensus across 3 reviewers produces more robust decisions |
| **Security gate is highest threshold (98)** | Security is non-negotiable; critical findings halt immediately |
| **Polyglot LLM with cost-aware routing** | Different tasks need different intelligence levels; routing simple tasks to cheaper models saves cost |
| **PostgreSQL as source of truth** | ACID guarantees; all other tiers are eventually consistent views |

---

## 11. System Boundaries & External Dependencies

```
INTERNAL:
  All 12 microservices
  All 4 databases
  Kafka cluster
  Vault

EXTERNAL (required):
  OpenAI API          — LLM provider (primary)
  Anthropic API       — LLM provider (fallback)
  DeepSeek API        — LLM provider (cost-optimized)
  Ollama (local)      — LLM provider (offline fallback)
  GitHub API          — Code storage, PRs, CI/CD
  Container Registry  — Docker image storage (ECR/GCR/ACR)
  Cloud Provider      — AWS/GCP/Azure for K8s, managed DBs

EXTERNAL (optional):
  Slack/Teams Webhook — Human notifications
  PagerDuty           — On-call escalation
  Jira                — External task tracking
  Sentry              — Error tracking
```

---

*End of System Architecture*
