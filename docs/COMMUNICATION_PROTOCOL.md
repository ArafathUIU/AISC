# AISC — Communication Protocol

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Protocol Architecture

AISC uses a layered communication model:

```
Layer 1 (External):    HTTPS/2 REST + JSON — User-facing API
Layer 2 (Internal):    gRPC (primary) / REST (fallback) — Inter-service sync calls
Layer 3 (Async):       Kafka + Protobuf — Event-driven communication
Layer 4 (Real-time):   WSS + JSON — WebSocket for UI updates
Layer 5 (Agent):       Kafka + Redis Pub/Sub — Agent-to-agent messaging
```

---

## 2. Agent Communication Protocol (ACP)

### 2.1 Message Envelope

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "660e8400-e29b-41d4-a716-446655440001",
  "conversation_id": "770e8400-e29b-41d4-a716-446655440002",
  "sender": {
    "agent_id": "architect-001",
    "agent_type": "architect",
    "service": "agent-runtime"
  },
  "receiver": {
    "agent_id": "developer-001",
    "agent_type": "developer"
  },
  "message_type": "task_handoff",
  "priority": "high",
  "task_ref": {
    "task_id": "880e8400-e29b-41d4-a716-446655440003",
    "artifact_id": "990e8400-e29b-41d4-a716-446655440004"
  },
  "payload": {},
  "created_at": "2026-06-18T09:15:00Z",
  "ttl": 3600
}
```

### 2.2 Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `task_handoff` | Agent -> Agent | Pass task context and artifact to next agent |
| `review_request` | Agent -> Reviewer | Request artifact critique |
| `critique` | Reviewer -> Consensus | Structured critique with scores |
| `query` | Agent -> Agent | Request information |
| `response` | Agent -> Agent | Response to query |
| `broadcast` | Agent -> All | System-wide announcement |
| `status_update` | Agent -> Orchestrator | Agent progress report |
| `escalation` | Agent -> Orchestrator | Escalate issue |

### 2.3 Priority Levels

| Priority | Description | Max Queue Time |
|----------|-------------|:-------------:|
| `critical` | Security incident, production outage | 30s |
| `high` | Quality gate failure, task dependency | 2min |
| `medium` | Standard task execution | 10min |
| `low` | Background analysis, learning extraction | 1hr |

### 2.4 Delivery Guarantees

| Scenario | Guarantee |
|----------|-----------|
| Agent online | At-least-once delivery within TTL |
| Agent offline | Message queued; delivered on reconnection |
| Agent ERROR | Message routed to dead-letter queue; Orchestrator notified |
| TTL expired | Message dropped; sender notified |
| Duplicate message | Idempotency via `message_id` deduplication |

---

## 3. REST API Specification

### 3.1 Base URL & Versioning

```
Production:  https://api.aisc.dev/api/v1
Staging:     https://staging-api.aisc.dev/api/v1
Development: http://localhost:8000/api/v1
```

### 3.2 Common Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Correlation-ID: uuid
X-Request-ID: uuid
Accept: application/json
Accept-Language: en
```

### 3.3 Common Response Codes

| Code | Meaning | Body |
|------|---------|------|
| 200 | Success | Response data |
| 201 | Created | Created resource with Location header |
| 204 | No Content (delete) | Empty |
| 400 | Bad Request | `{ "error": "validation_error", "details": [...] }` |
| 401 | Unauthorized | `{ "error": "unauthorized" }` |
| 403 | Forbidden | `{ "error": "forbidden", "required_permission": "..." }` |
| 404 | Not Found | `{ "error": "not_found", "resource": "..." }` |
| 409 | Conflict | `{ "error": "conflict", "reason": "..." }` |
| 422 | Unprocessable | `{ "error": "validation_error", "fields": {...} }` |
| 429 | Rate Limited | `{ "error": "rate_limited", "retry_after": 30 }` |
| 500 | Server Error | `{ "error": "internal_error", "request_id": "..." }` |
| 503 | Service Unavailable | `{ "error": "service_unavailable" }` |

### 3.4 Pagination

```
GET /api/v1/projects?page=2&limit=20&sort=created_at&order=desc

Response:
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 156,
    "pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

### 3.5 Complete Endpoint Reference

```
/api/v1

├── /auth
│   ├── POST   /register                  # Create account
│   ├── POST   /login                     # Login, get JWT tokens
│   ├── POST   /refresh                   # Refresh access token
│   ├── POST   /logout                    # Invalidate tokens
│   └── GET    /me                        # Current user profile
│
├── /projects
│   ├── GET    /                          # List projects (filter: ?status=active)
│   ├── POST   /                          # Create project
│   ├── GET    /{project_id}              # Get project details
│   ├── PUT    /{project_id}              # Update project
│   ├── DELETE /{project_id}              # Archive project
│   ├── GET    /{project_id}/workflow     # Get workflow DAG state
│   ├── POST   /{project_id}/start        # Start autonomous development
│   ├── POST   /{project_id}/pause        # Pause project
│   └── GET    /{project_id}/members      # List project members
│
├── /tasks
│   ├── GET    /                          # List tasks (?project_id=&status=&agent_type=)
│   ├── GET    /{task_id}                 # Get task details
│   ├── GET    /{task_id}/artifacts       # Get artifacts produced by task
│   ├── GET    /{task_id}/iterations      # Get recursive loop history
│   ├── GET    /{task_id}/agent-runs      # Get agent execution history
│   └── POST   /{task_id}/retry           # Retry failed task
│
├── /agents
│   ├── GET    /                          # List all agents & status
│   ├── GET    /{agent_id}                # Get agent details
│   ├── GET    /{agent_id}/runs           # Get agent execution history
│   ├── POST   /{agent_id}/assign         # Manually assign task to agent
│   └── POST   /{agent_id}/pause          # Pause agent
│
├── /artifacts
│   ├── GET    /{artifact_id}             # Get artifact
│   ├── PUT    /{artifact_id}             # Update artifact (human override)
│   ├── GET    /{artifact_id}/versions    # Get version history
│   ├── GET    /{artifact_id}/versions/{v} # Get specific version
│   ├── GET    /{artifact_id}/scores      # Get evaluation score history
│   ├── GET    /{artifact_id}/critiques   # Get critique history
│   ├── GET    /{artifact_id}/children    # Get derived artifacts
│   └── GET    /{artifact_id}/diff?v1=1&v2=3  # Diff between versions
│
├── /quality-gates
│   ├── GET    /                          # List gate definitions
│   ├── GET    /{gate_type}               # Get gate configuration
│   ├── GET    /{gate_type}/history       # Get evaluation history for gate
│   └── POST   /evaluate                  # Evaluate an artifact against a gate
│
├── /rag
│   ├── POST   /query                     # Semantic search
│   │         Body: { query, collection?, limit?, filters? }
│   └── POST   /ingest                    # Ingest documents
│             Body: { documents: [...], collection }
│
├── /memory
│   ├── POST   /store                     # Store in memory tier
│   │         Body: { tier, data }
│   ├── GET    /search                    # Cross-tier search
│   │         Query: ?q=&tier=&limit=&project_id=
│   └── GET    /context/{agent_id}        # Get assembled context for agent
│             Query: ?task_type=&query=
│
├── /knowledge-graph
│   ├── GET    /query                     # Read-only Cypher query
│   │         Query: ?cypher=
│   ├── GET    /entity/{type}/{id}/relations  # Entity relationships
│   └── GET    /entity/{type}/{id}/traverse   # Graph traversal
│             Query: ?depth=3&direction=out
│
├── /debates
│   ├── GET    /{debate_id}               # Get debate state
│   ├── GET    /{debate_id}/critiques     # Get all critiques
│   ├── GET    /{debate_id}/resolution    # Get resolution
│   └── POST   /{debate_id}/resolve       # Human override resolution
│
├── /deployments
│   ├── GET    /                          # List deployments
│   ├── POST   /                          # Trigger deployment
│   ├── GET    /{deployment_id}           # Get deployment status
│   ├── GET    /{deployment_id}/logs      # Get deployment logs
│   └── POST   /{deployment_id}/rollback  # Trigger rollback
│
├── /monitoring
│   ├── GET    /metrics                   # Aggregated metrics snapshot
│   ├── GET    /alerts                    # Active alerts
│   ├── GET    /alerts/{alert_id}         # Alert detail
│   ├── POST   /alerts/{alert_id}/acknowledge  # Acknowledge alert
│   └── GET    /health                    # System health (all services)
│
├── /incidents
│   ├── GET    /                          # List incidents (?status=&severity=)
│   ├── GET    /{incident_id}             # Get incident detail
│   ├── GET    /{incident_id}/rca         # Get root cause analysis
│   ├── GET    /{incident_id}/patch       # Get generated patch
│   └── POST   /{incident_id}/resolve     # Resolve incident
│
├── /learning
│   ├── GET    /insights                  # Learned improvements
│   │         Query: ?agent_type=&gate_type=
│   ├── GET    /patterns                  # Identified patterns
│   └── GET    /statistics                # Learning statistics
│
└── /admin
    ├── GET    /config                    # System configuration
    ├── PUT    /config                    # Update configuration
    ├── GET    /audit-log                 # Audit trail
    └── POST   /maintenance               # Trigger maintenance tasks
```

---

## 4. gRPC Service Definitions

### 4.1 Key gRPC Services (Internal Only)

```protobuf
service MemoryService {
    rpc StoreArtifact(StoreArtifactRequest) returns (StoreArtifactResponse);
    rpc GetArtifact(GetArtifactRequest) returns (Artifact);
    rpc SearchCrossTier(SearchRequest) returns (SearchResponse);
    rpc AssembleContext(ContextRequest) returns (ContextResponse);
}

service ScoringService {
    rpc Evaluate(EvaluateRequest) returns (EvaluationResult);
    rpc BatchEvaluate(BatchEvaluateRequest) returns (BatchEvaluateResult);
}

service QualityGateService {
    rpc CheckGate(GateCheckRequest) returns (GateCheckResult);
    rpc StartLoop(LoopRequest) returns (LoopResult);
}

service RAGService {
    rpc SemanticSearch(SearchRequest) returns (SearchResponse);
    rpc IngestDocuments(IngestRequest) returns (IngestResponse);
}
```

---

## 5. WebSocket Protocol

### 5.1 Connection

```
ws://localhost:8012/ws?token=<jwt_token>
wss://api.aisc.dev/ws?token=<jwt_token>
```

### 5.2 Client -> Server Messages

```json
// Subscribe to channels
{ "type": "subscribe", "channels": ["project:{id}:*", "agent:{id}:*"] }

// Unsubscribe
{ "type": "unsubscribe", "channels": ["agent:{id}:*"] }

// Ping
{ "type": "ping" }
```

### 5.3 Server -> Client Messages

```json
// Event notification
{
  "type": "event",
  "channel": "project:abc-123:artifacts",
  "event": {
    "event_id": "uuid",
    "event_type": "ArtifactCreated",
    "payload": { ... },
    "timestamp": "ISO8601"
  }
}

// Agent conversation stream
{
  "type": "agent_stream",
  "agent_id": "architect-001",
  "stream_type": "thinking",
  "content": "Analyzing service decomposition...",
  "timestamp": "ISO8601"
}

// System notification
{
  "type": "notification",
  "severity": "warning",
  "title": "Budget at 80%",
  "message": "Project budget at 80% of 1M tokens",
  "timestamp": "ISO8601"
}
```

---

## 6. Correlation & Tracing

Every request across the system carries a correlation ID for tracing:

```
Incoming HTTP request
  |
  X-Correlation-ID: abc-123 (or generated if missing)
  |
  ├── REST call to memory-service
  |     X-Correlation-ID: abc-123
  |     X-Trace-ID: def-456 (W3C TraceContext)
  |
  ├── Kafka event published
  |     event_id: uuid
  |     correlation_id: abc-123
  |
  └── gRPC call to scoring-engine
        metadata: correlation-id: abc-123
        metadata: traceparent: 00-def-456-...
```

---

## 7. Rate Limiting

| Tier | Limit | Window | Scope |
|------|-------|--------|-------|
| Anonymous | 10 req/s | Sliding | Per IP |
| Authenticated User | 100 req/s | Sliding | Per user |
| Admin | 500 req/s | Sliding | Per user |
| Internal Service | 1000 req/s | Sliding | Per service |
| LLM API calls | Configurable budget | Daily | Per project |

---

## 8. Error Handling

### 8.1 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid project name",
    "details": [
      {
        "field": "name",
        "issue": "Name must be between 3 and 200 characters",
        "value": "ab"
      }
    ],
    "request_id": "uuid",
    "correlation_id": "uuid",
    "timestamp": "2026-06-18T09:15:00Z"
  }
}
```

### 8.2 Retry Policy (Internal Service Calls)

| Status | Strategy | Max Retries | Backoff |
|--------|----------|:----------:|---------|
| 429 | Retry with backoff | 3 | Exponential (1s, 2s, 4s) |
| 503 | Retry with backoff | 3 | Exponential (1s, 2s, 4s) |
| 500 | Retry once | 1 | Immediate |
| 408 | Retry with backoff | 2 | Exponential (2s, 4s) |
| 4xx (not 429) | Do not retry | 0 | N/A |

### 8.3 Circuit Breaker

```
State: CLOSED -> OPEN (after 5 consecutive failures in 30s)
       OPEN   -> HALF_OPEN (after 60s cooldown)
       HALF_OPEN -> CLOSED (3 consecutive successes)
       HALF_OPEN -> OPEN (any failure)
```

---

*End of Communication Protocol*
