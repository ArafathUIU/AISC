# AISC — Memory Architecture Specification

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0
**Status**: Complete Specification

---

# Table of Contents

1. [Overview](#1-overview)
2. [Short-Term Memory (Redis)](#2-short-term-memory-redis)
3. [Long-Term Memory (PostgreSQL)](#3-long-term-memory-postgresql)
4. [Semantic Memory (Qdrant)](#4-semantic-memory-qdrant)
5. [Knowledge Graph (Neo4j)](#5-knowledge-graph-neo4j)
6. [Project History](#6-project-history)
7. [Learning Records](#7-learning-records)
8. [Memory Service API](#8-memory-service-api)
9. [Cross-Memory Query Patterns](#9-cross-memory-query-patterns)

---

# 1. Overview

AISC uses a 4-tier memory architecture. Each tier serves a distinct purpose, uses different storage technology, and has its own schema, retrieval, retention, and update strategy.

```
┌──────────────────────────────────────────────────────────────┐
│                    MEMORY SERVICE (Port 8007)                 │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐
│  │ Redis Store │  │ Postgres    │  │ Qdrant Store│  │ Neo4j    │
│  │ (Short-Term)│  │ Store (Long │  │ (Semantic)  │  │ Store    │
│  │             │  │ Term)       │  │             │  │ (Graph)  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬─────┘
│         │                │                │               │
│  ┌──────▼────────────────▼────────────────▼───────────────▼─────┐
│  │                  Unified Query Router                         │
│  │  Routes queries to appropriate store(s) based on query type   │
│  └──────────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────┘

      Short-Term          Long-Term           Semantic            Graph
      ──────────          ─────────           ────────            ─────
      Agent State        Projects          Code Embeddings     Relationships
      Task Context       Tasks             Doc Embeddings      Dependencies
      Session Data       Artifacts         Agent Memory        Traceability
      Active Queues      Evaluations       Context Vectors     Impact Analysis
      Pub/Sub            Workflows                              Pattern Matching
      Rate Limiting      Users
                          Learning Records
                          Incidents
```

## 1.1 Memory Tier Comparison

| Attribute | Short-Term | Long-Term | Semantic | Graph |
|-----------|:----------:|:---------:|:--------:|:-----:|
| **Storage** | Redis 7+ | PostgreSQL 15+ | Qdrant 1.x | Neo4j 5+ |
| **Data Model** | Key-Value | Relational | Vector | Property Graph |
| **Latency** | < 1ms | < 10ms | < 20ms | < 50ms |
| **Persistence** | Optional | Guaranteed | Guaranteed | Guaranteed |
| **Query Type** | Key lookup, Pub/Sub | SQL, Joins, Aggregations | KNN, Similarity | Cypher, Traversal |
| **Typical TTL** | Minutes to hours | Forever (with archival) | Forever (with re-indexing) | Forever |
| **Consistency** | Eventually | Strong (ACID) | Eventually | Strong (ACID) |
| **Scale** | In-memory (GB) | Disk (TB) | Disk (TB vectors) | Disk (TB graph) |

---

# 2. Short-Term Memory (Redis)

## 2.1 Purpose

Volatile, high-speed memory for active operational state. Stores data that is needed with sub-millisecond latency and has a limited lifespan. Lost data can be reconstructed from event sourcing.

## 2.2 Storage

| Property | Value |
|----------|-------|
| **Technology** | Redis 7.2+ (Cluster mode for production) |
| **Connection** | Async (redis-py with connection pool, pool size 20 per service) |
| **Serialization** | orjson (fastest Python JSON) |
| **Key Namespace** | `{service}:{entity}:{id}` |
| **Default TTL** | Configurable per key pattern |
| **Max Memory** | 4GB per node, eviction policy: `volatile-lru` |

## 2.3 Schema

### 2.3.1 Key Patterns

```
# Agent Session State
aisc:agent:{agent_id}:state           → JSON  | Agent lifecycle state, current task
aisc:agent:{agent_id}:context         → JSON  | Current task context, conversation
aisc:agent:{agent_id}:heartbeat       → INT   | Unix timestamp, last heartbeat
aisc:agent:{agent_id}:tool_calls      → LIST  | Recent tool invocation results

# Task Execution State
aisc:task:{task_id}:status            → STRING | PENDING|RUNNING|COMPLETED|FAILED
aisc:task:{task_id}:context           → JSON   | Task input, assigned agent, priority
aisc:task:{task_id}:artifacts         → LIST   | Artifact IDs produced during task
aisc:task:{task_id}:iterations        → JSON   | Loop iteration state for current run

# Workflow State
aisc:workflow:{workflow_id}:dag       → JSON   | Serialized DAG with node statuses
aisc:workflow:{workflow_id}:current   → STRING | Current node ID being executed
aisc:workflow:{workflow_id}:history   → LIST   | Completed node IDs in order

# Quality Loop State
aisc:loop:{artifact_id}:iteration     → INT    | Current iteration number
aisc:loop:{artifact_id}:scores        → LIST   | Score history [72, 84, 91]
aisc:loop:{artifact_id}:critiques     → LIST   | Recent critiques

# Agent Task Queue
aisc:queue:{agent_type}               → ZSET   | Priority queue, score=priority
aisc:queue:{agent_type}:aging         → ZSET   | Aging factor for priority inversion

# Pub/Sub Channels
aisc:channel:project:{project_id}:*   → PUBSUB | All project events
aisc:channel:agent:{agent_id}:*       → PUBSUB | Agent-specific events
aisc:channel:system:*                 → PUBSUB | System-wide broadcasts

# Rate Limiting
aisc:ratelimit:{user_id}:{endpoint}   → INT    | Request counter, sliding window

# WebSocket Connections
aisc:ws:{client_id}:channels          → SET    | Subscribed channels
aisc:ws:{client_id}:metadata          → JSON   | User, project, auth context

# Token Budget Tracking
aisc:budget:{project_id}:total        → INT    | Total token budget
aisc:budget:{project_id}:used         → INT    | Tokens consumed
aisc:budget:{project_id}:last_reset   → INT    | Unix timestamp

# Debate State
aisc:debate:{debate_id}:reviewers     → SET    | Reviewer agent IDs
aisc:debate:{debate_id}:critiques     → HASH   | reviewer_id → critique JSON
aisc:debate:{debate_id}:status        → STRING | IN_REVIEW|CONSENSUS|RESOLVED

# Cache
aisc:cache:rag:{query_hash}           → JSON   | Cached RAG results
aisc:cache:llm:{prompt_hash}          → JSON   | Cached LLM responses (idempotent)
aisc:cache:artifact:{id}:v{version}   → JSON   | Hot artifact cache
```

### 2.3.2 Value Schemas

```json
// aisc:agent:{id}:state
{
  "agent_id": "uuid",
  "agent_type": "developer",
  "status": "BUSY",
  "current_task_id": "uuid",
  "last_heartbeat": 1718736000,
  "started_at": "ISO8601",
  "error_count": 0,
  "tokens_used_today": 145000,
  "model": "claude-3.5-sonnet"
}

// aisc:task:{id}:context
{
  "task_id": "uuid",
  "task_type": "code_generation",
  "project_id": "uuid",
  "workflow_id": "uuid",
  "assigned_agent": "uuid",
  "priority": 5,
  "input": {
    "api_contract_id": "uuid",
    "erd_id": "uuid"
  },
  "dependencies": ["uuid1", "uuid2"],
  "status": "RUNNING",
  "created_at": "ISO8601",
  "started_at": "ISO8601",
  "deadline": "ISO8601"
}

// aisc:loop:{artifact_id}:iterations
{
  "artifact_id": "uuid",
  "gate_type": "code_gate",
  "current_iteration": 3,
  "max_iterations": 7,
  "threshold": 92,
  "score_history": [72, 84],
  "last_improvement_agent": "uuid",
  "stuck_count": 0,
  "started_at": "ISO8601"
}
```

## 2.4 Retrieval Methods

| Access Pattern | Redis Command | Latency | Use Case |
|---------------|--------------|---------|----------|
| Get by key | `GET aisc:agent:{id}:state` | < 0.5ms | Agent status check |
| Get JSON field | `JSON.GET aisc:agent:{id}:state $.status` | < 1ms | Specific field query |
| Set with TTL | `SETEX aisc:agent:{id}:heartbeat 30 {ts}` | < 0.5ms | Heartbeat update |
| Atomic increment | `INCR aisc:budget:{pid}:used` | < 0.5ms | Token tracking |
| List push/range | `LPUSH` / `LRANGE` | < 1ms | Iteration history |
| Sorted set by score | `ZRANGEBYSCORE aisc:queue:developer 0 10` | < 1ms | Priority queue pop |
| Pub/Sub | `PUBLISH` / `SUBSCRIBE` | < 1ms | Event broadcast |
| Set membership | `SADD` / `SMEMBERS` / `SISMEMBER` | < 0.5ms | Channel subscription |
| Pipeline batch | `pipeline.execute()` | < 2ms for 10 ops | Atomic multi-get |
| Lua script | `EVAL` | < 5ms | Atomic multi-step ops |
| Key scan by pattern | `SCAN 0 MATCH aisc:agent:*:state` | Variable | Agent inventory |

## 2.5 Retention Policy

| Key Pattern | TTL | Eviction Strategy | Rationale |
|-------------|-----|-------------------|-----------|
| `aisc:agent:*:heartbeat` | 30s | Expire + delete | Stale agent detection |
| `aisc:agent:*:state` | 1 hour after IDLE | Expire + delete | Clean up inactive agents |
| `aisc:task:*:status` | 24 hours after COMPLETED | Expire + archive to PG | Tasks persisted to long-term |
| `aisc:task:*:context` | 24 hours after COMPLETED | Expire + archive | Context archived with task |
| `aisc:loop:*` | 1 hour after loop COMPLETED/ESCALATED | Expire + delete | Loop state is ephemeral |
| `aisc:queue:*` | Persistent (no TTL) | Manual cleanup | Queue must survive restarts |
| `aisc:channel:*` | Persistent | N/A | Channels are stateless |
| `aisc:ratelimit:*` | Sliding window (1 min) | Expire + delete | Rate limit windows |
| `aisc:ws:*` | Connection duration | Expire on disconnect | Clean up dead connections |
| `aisc:budget:*` | Project lifetime | Archive to PG on project end | Budget tracking |
| `aisc:cache:rag:*` | 1 hour | volatile-lru | RAG results change slowly |
| `aisc:cache:llm:*` | 10 minutes | volatile-lru | LLM responses cached briefly |
| `aisc:cache:artifact:*` | 5 minutes after write | volatile-lru | Hot artifact reads |

### 2.5.1 Memory Pressure Handling

```
WHEN memory_used > 80%:
    1. EVICT expired keys (passive, handled by Redis)
    2. IF still > 80%:
       EVICT volatile-lru keys (least recently used with TTL)
    3. IF still > 80%:
       LOG warning: "Redis memory pressure"
       REDUCE cache TTLs by 50% for: aisc:cache:*
    4. IF still > 85%:
       ALERT: "Redis memory critical"
       FLUSH oldest cache entries aggressively
    5. IF > 90%:
       ALERT: "Redis OOM imminent"
       REJECT new cache writes
```

## 2.6 Update Strategy

| Pattern | Strategy | Consistency |
|---------|----------|-------------|
| Agent heartbeat | Overwrite, no read-before-write | Last-write-wins |
| Agent state | Atomic JSON.MERGE or GET + SET with optimistic lock (WATCH) | Compare-and-swap |
| Task status | State machine: only allow valid transitions (SET with Lua script) | Strong (Lua atomic) |
| Queue priority | ZADD with score update | Atomic |
| Loop scores | LPUSH (append-only history), never update | Immutable |
| Budget counter | INCRBY (atomic increment) | Strong (atomic) |
| Cache entries | SET with TTL, no update (cache miss = recompute) | Eventually |
| Pub/Sub | Publish only, subscribers read latest | At-most-once |

---

# 3. Long-Term Memory (PostgreSQL)

## 3.1 Purpose

Durable, transactional, relational storage for all persistent AISC data. The source of truth for projects, tasks, artifacts, evaluations, users, and all historical records.

## 3.2 Storage

| Property | Value |
|----------|-------|
| **Technology** | PostgreSQL 15+ with PostGIS (optional, for future geo features) |
| **Connection** | Async (asyncpg via SQLAlchemy 2.0, pool size 10-50 per service) |
| **Schema** | `aisc` (dedicated schema, not public) |
| **Extensions** | `uuid-ossp`, `pg_trgm` (trigram search), `pg_stat_statements` |
| **Indexing** | B-tree (default), GIN (JSONB), GiST (trigram), BRIN (time-series) |
| **Partitioning** | By `created_at` (monthly) for high-volume tables |
| **Backup** | Continuous WAL archiving + daily full snapshots |

## 3.3 Schema

### 3.3.1 Entity-Relationship Diagram

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│  users   │       │ projects │       │  tasks   │
├──────────┤       ├──────────┤       ├──────────┤
│ id (PK)  │──┐    │ id (PK)  │──┐    │ id (PK)  │
│ email    │  │    │ name     │  │    │ project   │──┐
│ pass_hash│  │    │ desc     │  │    │ type      │  │
│ role     │  │    │ owner_id │──┤    │ status    │  │
│ settings │  │    │ status   │  │    │ priority  │  │
│ created  │  │    │ config   │  │    │ assigned  │  │
│ updated  │  │    │ created  │  │    │ input     │  │
└──────────┘  │    │ updated  │  │    │ created   │  │
              │    │ deadline │  │    │ started   │  │
┌──────────────┐  │ archived  │  │    │ completed │  │
│project_members│  └──────────┘  │    │ deadline  │  │
├──────────────┤                 │    └──────────┘  │
│ project_id   │──┐              │                   │
│ user_id      │──┤              │    ┌──────────┐   │
│ role         │  │              │    │artifacts │   │
│ permissions  │  │              │    ├──────────┤   │
└──────────────┘  │              │    │ id (PK)  │   │
                  │              │    │ project  │───┤
┌──────────┐      │              │    │ task_id  │───┘
│workflows │      │              │    │ type     │
├──────────┤      │              │    │ content  │
│ id (PK)  │      │              │    │ format   │
│ project  │──────┘              │    │ version  │
│ dag      │                     │    │ status   │
│ status   │                     │    │ parent   │──┐
│ current  │                     │    │ created  │  │
└──────────┘                     │    │ created  │  │  (self-ref)
                                 │    │ updated  │  │
┌──────────────┐                 │    └──────────┘  │
│ evaluations  │                 │      │            │
├──────────────┤                 │      │            │
│ id (PK)      │                 │      │  artifact  │
│ artifact_id  │─────────────────┘      │  versions  │
│ gate_type    │                 ┌──────────────┐   │
│ scores(JSONB)│                 │artifact_vers │   │
│ passed       │                 ├──────────────┤   │
│ iteration    │                 │ artifact_id  │───┤
│ feedback     │                 │ version_num  │   │
│ evaluator    │                 │ content      │   │
│ created      │                 │ diff_from_prev│  │
└──────────────┘                 │ created_by   │   │
                                 │ created_at   │   │
┌──────────────┐                 └──────────────┘   │
│ agent_runs   │                                    │
├──────────────┤                 ┌──────────────┐   │
│ id (PK)      │                 │artifact_links│   │
│ agent_id     │                 ├──────────────┤   │
│ agent_type   │                 │ parent_id    │───┘
│ task_id      │                 │ child_id     │
│ input(JSONB) │                 │ link_type    │
│ output(JSONB)│                 │ created_at   │
│ tokens_in    │                 └──────────────┘
│ tokens_out   │
│ model_used   │
│ duration_ms  │
│ status       │
│ error        │
│ created      │
└──────────────┘

┌──────────────┐       ┌──────────────┐
│ learning_recs│       │  incidents   │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │
│ artifact_type│       │ project_id   │
│ gate_type    │       │ service      │
│ prompt       │       │ severity     │
│ output       │       │ status       │
│ critique     │       │ detected_by  │
│ score_before │       │ detected_at  │
│ score_after  │       │ rca(JSONB)   │
│ iterations   │       │ rca_confidence│
│ passed       │       │ patch_id     │
│ tokens_used  │       │ resolved_at  │
│ agent_type   │       │ created_at   │
│ model        │       │ updated_at   │
│ extracted    │       └──────────────┘
│  _knowledge  │
│ created      │
└──────────────┘

┌──────────────┐       ┌──────────────┐
│  debates     │       │ escalations  │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │
│ artifact_id  │       │ project_id   │
│ status       │       │ type         │
│ reviewer_ids │       │ severity     │
│ final_decision│      │ source       │
│ resolved_by  │       │ artifact_ref │
│ created_at   │       │ context(JSON)│
│ resolved_at  │       │ status       │
└──────────────┘       │ human_response│
                       │ created_at   │
                       │ resolved_at  │
                       │ timeout      │
                       └──────────────┘
```

### 3.3.2 Complete Table Definitions

#### users
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique user ID |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `display_name` | VARCHAR(100) | NOT NULL | Display name |
| `role` | VARCHAR(20) | NOT NULL, CHECK(IN admin,developer,viewer) | System role |
| `settings` | JSONB | DEFAULT '{}' | User preferences |
| `last_login_at` | TIMESTAMPTZ | | Last login timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `deleted_at` | TIMESTAMPTZ | | Soft delete |

**Indexes**: `idx_users_email` on `email` WHERE `deleted_at IS NULL`
**Partitioning**: None

#### projects
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `name` | VARCHAR(200) | NOT NULL | Project name |
| `description` | TEXT | | Free-text description |
| `owner_id` | UUID | FK -> users.id, NOT NULL | Project creator |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, completed, archived, failed |
| `config` | JSONB | DEFAULT '{}' | Project settings, budget, constraints |
| `tech_stack` | JSONB | DEFAULT '{}' | Preferred technologies |
| `deadline` | TIMESTAMPTZ | | Project deadline |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `archived_at` | TIMESTAMPTZ | | Soft archive |

**Indexes**: `idx_projects_status` on `status`, `idx_projects_owner` on `owner_id`

#### project_members
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `project_id` | UUID | FK -> projects.id, PK (composite) | |
| `user_id` | UUID | FK -> users.id, PK (composite) | |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'viewer' | Project-level role |
| `permissions` | JSONB | DEFAULT '{}' | Fine-grained permissions |
| `added_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### tasks
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `project_id` | UUID | FK -> projects.id, NOT NULL | |
| `workflow_id` | UUID | FK -> workflows.id | Parent workflow |
| `parent_task_id` | UUID | FK -> tasks.id | Parent task (hierarchical) |
| `type` | VARCHAR(50) | NOT NULL | Task type enum |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending, queued, running, completed, failed, blocked, cancelled |
| `priority` | INT | NOT NULL, DEFAULT 5 | 1 (highest) - 10 (lowest) |
| `title` | VARCHAR(500) | NOT NULL | Human-readable title |
| `description` | TEXT | | Task description |
| `input` | JSONB | | Task input data |
| `assigned_agent_type` | VARCHAR(50) | | Required agent type |
| `assigned_agent_id` | UUID | | Actual assigned agent |
| `dependencies` | JSONB | DEFAULT '[]' | Array of task IDs that must complete first |
| `artifact_ids` | JSONB | DEFAULT '[]' | Artifacts produced by this task |
| `max_iterations` | INT | DEFAULT 5 | Max recursive loop iterations |
| `current_iteration` | INT | DEFAULT 0 | Current iteration count |
| `token_budget` | INT | | Token budget for this task |
| `tokens_used` | INT | DEFAULT 0 | Tokens consumed |
| `error_message` | TEXT | | Last error message |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `started_at` | TIMESTAMPTZ | | |
| `completed_at` | TIMESTAMPTZ | | |
| `deadline` | TIMESTAMPTZ | | |

**Indexes**: `idx_tasks_project` on `project_id`, `idx_tasks_status` on `status`, `idx_tasks_type_status` on `type, status`, `idx_tasks_assigned` on `assigned_agent_id`

#### workflows
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `project_id` | UUID | FK -> projects.id, NOT NULL | |
| `name` | VARCHAR(200) | NOT NULL | Workflow name |
| `dag` | JSONB | NOT NULL | DAG definition (nodes, edges) |
| `node_statuses` | JSONB | DEFAULT '{}' | Map of node_id -> status |
| `current_node_id` | UUID | | Currently executing node |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'created' | created, running, completed, failed |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `started_at` | TIMESTAMPTZ | | |
| `completed_at` | TIMESTAMPTZ | | |

**Indexes**: `idx_workflows_project` on `project_id`

#### artifacts
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `project_id` | UUID | FK -> projects.id, NOT NULL | |
| `task_id` | UUID | FK -> tasks.id | Task that created this |
| `type` | VARCHAR(50) | NOT NULL | prd, user_story, architecture_doc, api_spec, erd, source_code, test_file, security_report, deployment_config, research_report, etc. |
| `format` | VARCHAR(20) | NOT NULL, DEFAULT 'markdown' | markdown, json, yaml, python, typescript, sql, etc. |
| `name` | VARCHAR(500) | NOT NULL | File/artifact name |
| `content` | TEXT | NOT NULL | Full artifact content |
| `content_hash` | VARCHAR(64) | | SHA-256 of content for dedup |
| `version` | INT | NOT NULL, DEFAULT 1 | Monotonic version counter |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | draft, in_review, approved, rejected, archived |
| `parent_artifact_id` | UUID | FK -> artifacts.id | Parent artifact (e.g., PRD parent of user story) |
| `gate_type` | VARCHAR(50) | | Which quality gate applies |
| `created_by_agent` | VARCHAR(50) | NOT NULL | Which agent type created this |
| `metadata` | JSONB | DEFAULT '{}' | Arbitrary metadata |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

**Indexes**: `idx_artifacts_project` on `project_id`, `idx_artifacts_type` on `type`, `idx_artifacts_task` on `task_id`, `idx_artifacts_parent` on `parent_artifact_id`, `idx_artifacts_project_type` on `project_id, type`, `idx_artifacts_status` on `status`
**Partitioning**: By `created_at` (monthly) if > 1M rows/month

#### artifact_versions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `artifact_id` | UUID | FK -> artifacts.id, NOT NULL | |
| `version_num` | INT | NOT NULL | Version number |
| `content` | TEXT | NOT NULL | Content at this version |
| `content_hash` | VARCHAR(64) | | |
| `diff_from_prev` | TEXT | | Unified diff from previous version |
| `created_by_agent` | VARCHAR(50) | NOT NULL | |
| `change_description` | VARCHAR(500) | | What changed |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| UNIQUE | (artifact_id, version_num) | | |

**Indexes**: `idx_artifact_vers_artifact` on `artifact_id`

#### artifact_links
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `parent_artifact_id` | UUID | FK -> artifacts.id, NOT NULL | Source |
| `child_artifact_id` | UUID | FK -> artifacts.id, NOT NULL | Target |
| `link_type` | VARCHAR(50) | NOT NULL | derives_from, depends_on, implements, tests, deploys, etc. |
| `metadata` | JSONB | DEFAULT '{}' | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| UNIQUE | (parent_artifact_id, child_artifact_id, link_type) | | |

**Indexes**: `idx_artifact_links_parent` on `parent_artifact_id`, `idx_artifact_links_child` on `child_artifact_id`

#### evaluations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `artifact_id` | UUID | FK -> artifacts.id, NOT NULL | |
| `artifact_version` | INT | NOT NULL | Version being evaluated |
| `gate_type` | VARCHAR(50) | NOT NULL | requirements, architecture, code, testing, security, deployment |
| `iteration` | INT | NOT NULL | Which loop iteration |
| `scores` | JSONB | NOT NULL | All metric scores with justifications |
| `aggregate_score` | DECIMAL(5,2) | NOT NULL | Weighted aggregate 0-100 |
| `passed` | BOOLEAN | NOT NULL | Did it meet threshold? |
| `critical_metric_failures` | JSONB | DEFAULT '[]' | Which critical metrics failed |
| `feedback` | TEXT | | Overall feedback summary |
| `evaluator_type` | VARCHAR(20) | NOT NULL | automated, llm, hybrid |
| `evaluator_detail` | VARCHAR(100) | | Specific evaluator used |
| `tokens_used` | INT | DEFAULT 0 | LLM tokens for evaluation |
| `evaluation_duration_ms` | INT | | Time to evaluate |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**Indexes**: `idx_eval_artifact` on `artifact_id`, `idx_eval_artifact_gate` on `artifact_id, gate_type`, `idx_eval_created` on `created_at`

#### agent_runs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `agent_id` | VARCHAR(100) | NOT NULL | Agent instance ID |
| `agent_type` | VARCHAR(50) | NOT NULL | Agent type |
| `task_id` | UUID | FK -> tasks.id | Associated task |
| `run_type` | VARCHAR(20) | NOT NULL | generation, critique, improvement |
| `input` | JSONB | | What was sent to the agent |
| `output` | JSONB | | What the agent produced |
| `output_artifact_ids` | JSONB | DEFAULT '[]' | Artifacts created |
| `system_prompt_hash` | VARCHAR(64) | | Which prompt version used |
| `model_used` | VARCHAR(50) | NOT NULL | LLM model |
| `model_provider` | VARCHAR(20) | NOT NULL | openai, anthropic, deepseek, ollama |
| `tokens_input` | INT | DEFAULT 0 | Prompt tokens |
| `tokens_output` | INT | DEFAULT 0 | Completion tokens |
| `tokens_total` | INT | DEFAULT 0 | Total tokens |
| `cost_usd` | DECIMAL(10,6) | DEFAULT 0 | Estimated cost |
| `duration_ms` | INT | NOT NULL | Execution time |
| `status` | VARCHAR(20) | NOT NULL | success, error, timeout |
| `error_message` | TEXT | | Error details if failed |
| `tool_calls` | JSONB | DEFAULT '[]' | Tools invoked and results |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**Indexes**: `idx_agent_runs_agent` on `agent_id`, `idx_agent_runs_task` on `task_id`, `idx_agent_runs_type` on `agent_type`, `idx_agent_runs_created` on `created_at`
**Partitioning**: By `created_at` (monthly) — high volume

#### learning_records
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `artifact_type` | VARCHAR(50) | NOT NULL | What type of artifact |
| `gate_type` | VARCHAR(50) | NOT NULL | Which quality gate |
| `agent_type` | VARCHAR(50) | NOT NULL | Which agent produced it |
| `model_used` | VARCHAR(50) | | LLM model |
| `system_prompt_hash` | VARCHAR(64) | | Prompt version |
| `input_prompt` | TEXT | | The task prompt |
| `output_content` | TEXT | | Final artifact content |
| `iteration_count` | INT | NOT NULL | How many iterations |
| `scores_history` | JSONB | NOT NULL | Array of scores per iteration |
| `final_score` | DECIMAL(5,2) | | Final aggregate score |
| `passed` | BOOLEAN | NOT NULL | Did it pass the gate? |
| `critiques` | JSONB | DEFAULT '[]' | All critiques received |
| `improvements` | JSONB | DEFAULT '[]' | Improvements applied per iteration |
| `tokens_total` | INT | DEFAULT 0 | Total tokens across all iterations |
| `total_duration_ms` | INT | | Total time across all iterations |
| `extracted_knowledge` | JSONB | | Knowledge extracted from this run |
| `knowledge_applied` | BOOLEAN | DEFAULT false | Applied to future prompts? |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**Indexes**: `idx_learning_type` on `artifact_type`, `idx_learning_agent` on `agent_type`, `idx_learning_passed` on `passed`, `idx_learning_created` on `created_at`

#### incidents
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `project_id` | UUID | FK -> projects.id | |
| `service_name` | VARCHAR(100) | NOT NULL | Affected service |
| `severity` | VARCHAR(20) | NOT NULL | critical, high, medium, low |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'detected' | detected, analyzing, patching, validating, deploying, resolved, escalated |
| `detected_by` | VARCHAR(50) | | monitoring, self_healing, human |
| `detected_at` | TIMESTAMPTZ | NOT NULL | |
| `title` | VARCHAR(500) | NOT NULL | Brief description |
| `description` | TEXT | | Full incident description |
| `affected_metrics` | JSONB | | Metrics at time of incident |
| `log_snippets` | JSONB | | Relevant log entries |
| `trace_ids` | JSONB | DEFAULT '[]' | Distributed trace IDs |
| `rca` | JSONB | | Root cause analysis result |
| `rca_confidence` | DECIMAL(3,2) | | 0.00 - 1.00 |
| `patch_artifact_id` | UUID | FK -> artifacts.id | Generated patch |
| `patch_deployed_at` | TIMESTAMPTZ | | |
| `patch_rollback_at` | TIMESTAMPTZ | | If rolled back |
| `resolved_at` | TIMESTAMPTZ | | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

**Indexes**: `idx_incidents_project` on `project_id`, `idx_incidents_status` on `status`, `idx_incidents_severity` on `severity`, `idx_incidents_service` on `service_name`

#### debates
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `artifact_id` | UUID | FK -> artifacts.id, NOT NULL | |
| `gate_type` | VARCHAR(50) | NOT NULL | |
| `status` | VARCHAR(20) | NOT NULL | open, in_review, consensus, resolved, deadlocked |
| `reviewer_ids` | JSONB | NOT NULL | Array of 3 reviewer agent IDs |
| `consensus_agent_id` | VARCHAR(100) | | |
| `round` | INT | DEFAULT 1 | Current debate round |
| `critiques` | JSONB | DEFAULT '{}' | reviewer_id -> critique JSON |
| `agreement_score` | DECIMAL(3,2) | | % of reviewers agreeing |
| `final_decision` | VARCHAR(20) | | pass, fail, escalate |
| `resolution_note` | TEXT | | How consensus was reached |
| `resolved_by` | VARCHAR(50) | | Agent or "human" |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `resolved_at` | TIMESTAMPTZ | | |

**Indexes**: `idx_debates_artifact` on `artifact_id`

#### escalations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `project_id` | UUID | FK -> projects.id, NOT NULL | |
| `source_type` | VARCHAR(50) | NOT NULL | quality_gate, orchestrator, agent_error, deadlock |
| `source_agent` | VARCHAR(50) | | Agent that escalated |
| `severity` | VARCHAR(20) | NOT NULL | critical, high, medium, low |
| `artifact_id` | UUID | FK -> artifacts.id | Related artifact |
| `task_id` | UUID | FK -> tasks.id | Related task |
| `title` | VARCHAR(500) | NOT NULL | |
| `context` | JSONB | NOT NULL | Full context (scores, history, errors) |
| `target_role` | VARCHAR(50) | NOT NULL | Target human role |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'open' | open, acknowledged, resolved, cancelled |
| `human_response` | JSONB | | Human resolution |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `acknowledged_at` | TIMESTAMPTZ | | |
| `resolved_at` | TIMESTAMPTZ | | |
| `timeout_at` | TIMESTAMPTZ | NOT NULL | Escalation SLA deadline |
| `reminder_sent_at` | TIMESTAMPTZ | | |

**Indexes**: `idx_esc_status` on `status`, `idx_esc_severity` on `severity`, `idx_esc_project` on `project_id`

## 3.4 Retrieval Methods

| Query Pattern | Method | Example |
|--------------|--------|---------|
| Simple CRUD | SQLAlchemy async ORM | `await session.get(Project, id)` |
| Filtered list with pagination | SQLAlchemy select + limit/offset | `select(Task).where(Task.status=='pending').limit(20)` |
| Complex joins | SQLAlchemy with eager loading | `select(Artifact).options(joinedload(Artifact.evaluations))` |
| Aggregation | SQL window functions | `AVG(scores->>'aggregate_score') OVER (PARTITION BY gate_type)` |
| JSONB query | JSONB operators | `scores @> '{"completeness": 95}'` |
| Full-text search | `pg_trgm` trigram search | `WHERE content % 'user authentication'` |
| Time-series | BRIN index scan | `WHERE created_at BETWEEN X AND Y` |
| Graph traversal (simple) | Recursive CTEs | `WITH RECURSIVE artifact_tree AS (...)` |
| Bulk insert | `session.add_all()` + flush | Batch operations |
| Read replica | Separate connection pool for reads | All heavy queries routed to replica |

## 3.5 Retention Policy

| Table | Retention Period | Policy | Rationale |
|-------|-----------------|--------|-----------|
| users | Forever (soft delete) | `deleted_at` flag, never hard delete | GDPR: hard delete on request |
| projects | 5 years after archive | Archive to cold storage after 2 years | Historical reference |
| tasks | 2 years | Partition by month, drop partitions > 2 years | Operational data |
| artifacts | Project lifetime + 2 years | Archive with project | May need for future learning |
| artifact_versions | Same as artifact | Keep all versions | Traceability |
| evaluations | 2 years | Aggregate after 1 year (keep summary, drop details) | Storage cost vs utility |
| agent_runs | 6 months | Aggressively partition, drop old partitions | Very high volume |
| learning_records | Forever | Compress old records | Core learning data |
| incidents | 3 years | Archive after 1 year | Compliance + pattern analysis |
| debates | 1 year | Delete after project archive | Temporary coordination data |
| escalations | 2 years | Archive with project | Audit trail |

## 3.6 Update Strategy

| Pattern | Strategy | Consistency |
|---------|----------|-------------|
| Standard CRUD | SELECT FOR UPDATE in transaction | Serializable |
| Status transitions | State machine validation in application layer | Optimistic locking (version column) |
| Artifact versioning | INSERT new version row + UPDATE artifact.current_version in same transaction | Serializable |
| Score recording | INSERT only (append-only) | Eventually (inserts are safe) |
| Agent run logging | INSERT only, batch writes every 5s | Eventually |
| Bulk updates | Batch UPDATE with WHERE clause, chunked | Read Committed |
| Soft deletes | SET deleted_at = NOW(), never DELETE | Serializable |
| JSONB partial update | `jsonb_set()` or application read-modify-write | Optimistic locking |

---

# 4. Semantic Memory (Qdrant)

## 4.1 Purpose

Vector-based semantic memory for similarity search, context retrieval, and the RAG pipeline. Stores embeddings of all artifacts, code, documentation, and agent experiences for semantic retrieval.

## 4.2 Storage

| Property | Value |
|----------|-------|
| **Technology** | Qdrant 1.9+ (distributed mode for production) |
| **Connection** | Async (qdrant-client, gRPC) |
| **Distance Metric** | Cosine similarity (preferred for text) |
| **Index Type** | HNSW (Hierarchical Navigable Small World) |
| **Embedding Model (768d)** | `all-MiniLM-L6-v2` (local, fast, free) — code + docs |
| **Embedding Model (1536d)** | `text-embedding-3-small` (OpenAI) — agent memory |
| **Embedding Model (3072d)** | `text-embedding-3-large` (OpenAI) — high-precision context |
| **Batch Size** | 100 vectors per upsert |

## 4.3 Schema

### 4.3.1 Collections

| Collection | Dimensionality | Distance | Purpose | Expected Size |
|------------|:-------------:|----------|---------|:-------------:|
| `code_embeddings` | 768 | Cosine | Source code functions, classes, modules | 100K+ vectors |
| `doc_embeddings` | 768 | Cosine | Documentation, architecture docs, PRDs | 50K+ vectors |
| `agent_memory` | 1536 | Cosine | Agent experiences, task contexts | 500K+ vectors |
| `test_embeddings` | 768 | Cosine | Test files and patterns | 50K+ vectors |
| `security_findings` | 768 | Cosine | Vulnerability patterns and fixes | 10K+ vectors |
| `error_patterns` | 768 | Cosine | Error logs and their resolutions | 50K+ vectors |
| `knowledge_snippets` | 3072 | Cosine | High-value extracted knowledge | 100K+ vectors |

### 4.3.2 Payload Schema (per collection)

#### code_embeddings
```json
{
  "artifact_id": "uuid",
  "project_id": "uuid",
  "file_path": "services/auth/src/routes/users.py",
  "language": "python",
  "type": "function",
  "name": "create_user",
  "content": "async def create_user(...)",
  "chunk_index": 0,
  "total_chunks": 3,
  "tags": ["auth", "user", "crud"],
  "created_at": "ISO8601",
  "version": 3
}
```

#### doc_embeddings
```json
{
  "artifact_id": "uuid",
  "project_id": "uuid",
  "artifact_type": "architecture_document",
  "title": "User Service Architecture",
  "section": "3.2 Authentication Flow",
  "content": "The authentication flow uses...",
  "chunk_index": 2,
  "total_chunks": 8,
  "tags": ["architecture", "auth", "user-service"],
  "created_at": "ISO8601"
}
```

#### agent_memory
```json
{
  "agent_type": "developer",
  "agent_id": "uuid",
  "task_type": "code_generation",
  "experience_type": "success",
  "context": "Generated FastAPI endpoint for user CRUD...",
  "prompt_used": "...",
  "output_quality": 94,
  "gate_type": "code_gate",
  "iterations_needed": 2,
  "patterns_used": ["dependency_injection", "pydantic_validation"],
  "tags": ["fastapi", "crud", "user"],
  "created_at": "ISO8601"
}
```

#### error_patterns
```json
{
  "incident_id": "uuid",
  "service_name": "auth-service",
  "error_type": "ConnectionPoolExhausted",
  "error_message": "QueuePool limit of size 10 overflow 20 reached",
  "root_cause": "Missing connection.close() in finally block",
  "fix_pattern": "Add try/finally with connection.close()",
  "severity": "high",
  "resolution_time_ms": 420000,
  "tags": ["connection-pool", "postgresql", "resource-leak"],
  "created_at": "ISO8601"
}
```

## 4.4 Retrieval Methods

| Access Pattern | Method | Parameters | Use Case |
|---------------|--------|------------|----------|
| Semantic search | `search()` | query_vector, limit, score_threshold | Find similar code/docs |
| Filtered search | `search()` + `query_filter` | Filter by collection, project, tags | Scoped semantic search |
| Hybrid search | `search()` with payload filter | Vector + structured filter | "Find auth-related code with score > 0.8" |
| Batch search | `search_batch()` | Multiple query vectors | Bulk embedding lookup |
| Recommendation | `recommend()` | positive_ids, negative_ids | "Similar to this, but not like that" |
| Scroll (export) | `scroll()` | collection, batch_size | Export all embeddings |
| Similarity threshold | `search(score_threshold=0.75)` | Only return relevant | Avoid irrelevant results |

### 4.4.1 Retrieval Query Builder

```
QUERY("How to authenticate users in FastAPI?"):
    1. Generate embedding via sentence-transformers (768d)
    2. qdrant.search(
         collection_name="code_embeddings",
         query_vector=embedding,
         query_filter={
             must: [
                 {key: "language", match: {value: "python"}},
                 {key: "tags", match: {any: ["auth", "authentication", "jwt"]}}
             ]
         },
         limit=10,
         score_threshold=0.7
       )
    3. Rerank results with cross-encoder
    4. Return top-5 passages with metadata
```

## 4.5 Retention Policy

| Collection | Retention | Policy |
|------------|-----------|--------|
| code_embeddings | Project lifetime | Delete when project archived. Update on new code version. |
| doc_embeddings | Project lifetime | Delete when project archived. Update on doc version change. |
| agent_memory | 6 months | Rolling window. Oldest beyond 6 months auto-pruned. |
| test_embeddings | Project lifetime | Same as code. |
| security_findings | 1 year | Retain for pattern analysis. |
| error_patterns | 1 year | Retain for incident pattern matching. |
| knowledge_snippets | Forever | Core knowledge base. Selective pruning of low-value entries. |

## 4.6 Update Strategy

| Pattern | Strategy | Consistency |
|---------|----------|-------------|
| New artifact | Chunk -> embed -> upsert with artifact_id as point ID | Idempotent (upsert) |
| Artifact updated | Delete all chunks with artifact_id, re-chunk, re-embed, re-upsert | Atomic (delete+upsert in batch) |
| Delete artifact | Delete points by artifact_id filter | Immediate |
| Agent memory | Append-only (new points). Old points pruned by TTL. | Eventually (batch) |
| Bulk re-index | Export all -> delete collection -> re-create -> re-ingest | Offline migration |
| Model upgrade | Run in parallel: new collection with new model, gradual traffic shift | Blue-green |

---

# 5. Knowledge Graph (Neo4j)

## 5.1 Purpose

Graph database storing the relationships between all AISC entities. Enables graph traversal queries for impact analysis, dependency chains, pattern recognition, and knowledge discovery.

## 5.2 Storage

| Property | Value |
|----------|-------|
| **Technology** | Neo4j 5.x (Enterprise for production — clustering) |
| **Connection** | Async (neo4j-driver with session pool, pool size 10) |
| **Database** | `aisc` (dedicated database) |
| **Consistency** | ACID |
| **Indexing** | B-tree on all node ID properties, fulltext on content |

## 5.3 Schema

### 5.3.1 Node Types

| Node Label | Key Properties | Description |
|------------|---------------|-------------|
| `Project` | id, name, status | Top-level project node |
| `Requirement` | id, artifact_id, title, priority | A requirement or PRD section |
| `UserStory` | id, artifact_id, role, action, benefit | User story |
| `Feature` | id, artifact_id, name, priority | Feature definition |
| `ArchitectureDecision` | id, artifact_id, title, status | ADR |
| `Microservice` | id, name, responsibility | Microservice definition |
| `APIEndpoint` | id, method, path, service | API endpoint |
| `DatabaseTable` | id, name, schema | Database table |
| `Column` | id, name, type, nullable | Table column |
| `Technology` | id, name, version, category | Technology/framework |
| `SourceFile` | id, path, language | Source code file |
| `Function` | id, name, file, line_start, line_end | Function or method |
| `TestCase` | id, name, type | Unit/integration/e2e test |
| `Bug` | id, incident_id, severity, status | Bug from incident |
| `Solution` | id, patch_id, description | Fix/patch |
| `Deployment` | id, environment, version, status | Deployment record |
| `Incident` | id, severity, status | Production incident |
| `MetricDefinition` | id, name, gate_type | Quality metric definition |
| `LearnedPattern` | id, pattern_type, confidence, source | Extracted knowledge pattern |
| `Agent` | id, type, status | Agent instance (for tracking) |

### 5.3.2 Relationship Types

| Relationship | Direction | Properties | Description |
|-------------|-----------|------------|-------------|
| `HAS_REQUIREMENT` | Project -> Requirement | created_at | Project has this requirement |
| `IMPLEMENTS` | Requirement -> UserStory | created_at | Requirement decomposed to story |
| `HAS_FEATURE` | Requirement -> Feature | priority | Requirement includes feature |
| `BELONGS_TO` | UserStory -> Feature | | Story belongs to feature |
| `USES` | Project -> Technology | purpose, confidence | Technology choice |
| `JUSTIFIED_BY` | ArchitectureDecision -> Technology | rationale | Why this technology |
| `DECOMPOSES_INTO` | ArchitectureDecision -> Microservice | | Service from decision |
| `EXPOSES` | Microservice -> APIEndpoint | | Service exposes endpoint |
| `DEPENDS_ON` | APIEndpoint -> APIEndpoint | type (sync/async) | API dependency |
| `OWNS` | Microservice -> DatabaseTable | | Service owns table |
| `HAS_COLUMN` | DatabaseTable -> Column | ordinal | Table has column |
| `REFERENCES` | Column -> Column | cardinality | Foreign key |
| `IMPLEMENTS_API` | SourceFile -> APIEndpoint | | Code implements endpoint |
| `CONTAINS` | SourceFile -> Function | | File contains function |
| `CALLS` | Function -> Function | call_count | Function call graph |
| `COVERS` | TestCase -> Function | coverage_pct | Test covers function |
| `TESTS` | TestCase -> APIEndpoint | | E2E test covers endpoint |
| `DERIVES_FROM` | Artifact -> Artifact | link_type | Artifact lineage |
| `AFFECTS` | Bug -> APIEndpoint | severity | Bug affects endpoint |
| `CAUSED_BY` | Bug -> Function | | Root cause function |
| `FIXES` | Solution -> Bug | confidence | Fix resolves bug |
| `CONTAINS_FIX` | Solution -> SourceFile | | Patch modifies file |
| `DEPLOYS_TO` | Microservice -> Deployment | version | Service deployment |
| `TRIGGERED_BY` | Incident -> Bug | | Bug caused incident |
| `DETECTED_IN` | Incident -> Deployment | | Incident found in deployment |
| `SIMILAR_TO` | Incident -> Incident | similarity_score | Similar incidents |
| `EVALUATED_BY` | Artifact -> MetricDefinition | score | Quality evaluation |
| `LEARNED_FROM` | LearnedPattern -> Requirement | source_count | Pattern from requirements |
| `APPLIES_TO` | LearnedPattern -> Microservice | | Pattern applies to |
| `GENERATED` | Agent -> Artifact | iteration, tokens | Agent created artifact |
| `ASSIGNED_TO` | Task -> Agent | priority | Task assigned to agent |
| `PRECEDES` | Task -> Task | | Task dependency order |
| `ESCALATED_FROM` | Escalation -> Task | reason | Escalation from task |

### 5.3.3 Common Cypher Traversal Patterns

```cypher
// What APIs does a service expose?
MATCH (s:Microservice {name: "user-service"})-[:EXPOSES]->(api:APIEndpoint)
RETURN api.method, api.path

// What code implements a given API endpoint?
MATCH (api:APIEndpoint {path: "/api/v1/users"})<-[:IMPLEMENTS_API]-(file:SourceFile)
MATCH (file)-[:CONTAINS]->(func:Function)
RETURN file.path, func.name, func.line_start

// What tests cover a function?
MATCH (func:Function {name: "create_user"})<-[:COVERS]-(test:TestCase)
RETURN test.name, test.type, test.coverage_pct

// Impact analysis: if we change this API, what breaks?
MATCH (api:APIEndpoint {path: "/api/v1/users"})
MATCH (api)<-[:DEPENDS_ON*1..3]-(dependent:APIEndpoint)
MATCH (dependent)<-[:TESTS]-(test:TestCase)
RETURN dependent.path, collect(test.name) as affected_tests

// Find similar bugs to this one
MATCH (bug:Bug {id: $bug_id})-[:AFFECTS]->(api:APIEndpoint)
MATCH (similar:Bug)-[:AFFECTS]->(api)
WHERE similar.id <> bug.id
MATCH (similar)-[:CAUSED_BY]->(func:Function)
RETURN similar.id, similar.severity, func.name

// All decisions that led to a microservice
MATCH (ad:ArchitectureDecision)-[:DECOMPOSES_INTO*1..3]->(ms:Microservice {name: $name})
MATCH (ad)-[:JUSTIFIED_BY]->(tech:Technology)
RETURN ad.title, ad.status, tech.name, tech.version

// Pattern: Find architecture decisions that succeeded (high-scoring architectures)
MATCH (ad:ArchitectureDecision)<-[:EVALUATED_BY]-(m:MetricDefinition {name: "scalability"})
WHERE m.score >= 90
MATCH (ad)-[:JUSTIFIED_BY]->(tech:Technology)
RETURN tech.name, count(*) as success_count, avg(m.score) as avg_score
ORDER BY success_count DESC

// Knowledge extraction: What patterns lead to passing the code gate on first try?
MATCH (lp:LearnedPattern {pattern_type: "code_generation"})
MATCH (lp)-[:APPLIES_TO]->(ms:Microservice)
MATCH (ms)-[:EXPOSES]->(api:APIEndpoint)
MATCH (api)<-[:IMPLEMENTS_API]-(file:SourceFile)
RETURN lp.description, count(file) as applications, lp.confidence
```

## 5.4 Retrieval Methods

| Access Pattern | Method | Use Case |
|---------------|--------|----------|
| Cypher query | `session.run(cypher, params)` | Direct graph queries |
| Entity relations | `GET /entity/{type}/{id}/relations` | UI: explore entity connections |
| Shortest path | `shortestPath()` | Find connection between two entities |
| Subgraph | Variable-length patterns `*1..3` | Impact analysis |
| Aggregation | `count()`, `avg()`, `collect()` | Pattern analysis, statistics |
| Fulltext search | `CALL db.index.fulltext.queryNodes()` | Search nodes by text content |
| Graph algorithms | GDS library (PageRank, community detection) | Identify key nodes, clusters |
| Bulk import | `LOAD CSV` / `apoc.load.json` | Initial data loading |

## 5.5 Retention Policy

| Entity Type | Retention | Policy |
|-------------|-----------|--------|
| Project nodes + relationships | Project lifetime + 2 years | Remove when project fully archived |
| Incident -> Bug -> Solution chains | 2 years | Retain for pattern analysis |
| Agent nodes | 30 days after agent termination | Clean up inactive agents |
| LearnedPattern | Forever | Core knowledge — only remove if proven wrong |
| Deployment nodes | 1 year | Rolling window |
| Task nodes | Project lifetime | Remove with project |
| All relationships | Same as connected nodes | Cascade delete |

## 5.6 Update Strategy

| Pattern | Strategy | Consistency |
|---------|----------|-------------|
| New entity | MERGE node, CREATE relationship in single transaction | ACID (transaction) |
| Update entity properties | MATCH node, SET properties | ACID |
| Add relationship | MERGE + CREATE (idempotent) | ACID |
| Remove relationship | MATCH + DELETE relationship only | ACID |
| Bulk graph update | Batch MERGE + CREATE with periodic commits (every 1000 ops) | Eventually (batch) |
| Schema constraint add | `CREATE CONSTRAINT` as migration | Immediate |
| Graph algorithm results | Write-back to node properties via GDS | Eventually (batch job) |

---

# 6. Project History

## 6.1 Purpose

Historical record of completed projects. Includes full artifact lineage, all evaluations, all agent runs, and project metadata. Used by the Self-Learning Engine to improve future projects.

## 6.2 Storage

Project history is not a separate database — it is a **logical view** spanning PostgreSQL (structured data), Qdrant (embeddings), and Neo4j (relationships).

| Component | Storage | Description |
|-----------|---------|-------------|
| Project metadata | PostgreSQL `projects` | Status, config, dates |
| Full artifact tree | PostgreSQL `artifacts` + `artifact_versions` + `artifact_links` | Every version of every artifact |
| Evaluation history | PostgreSQL `evaluations` | All scores, all iterations |
| Agent run logs | PostgreSQL `agent_runs` | Every agent execution |
| Learning records | PostgreSQL `learning_records` | Summarized learning data |
| Artifact embeddings | Qdrant `*_embeddings` collections | Semantic representation |
| Entity relationships | Neo4j full graph | Project subgraph |
| Incident history | PostgreSQL `incidents` | All incidents and RCAs |

## 6.3 Retrieval Methods

```
PROJECT_HISTORY.get_full(project_id):
    // 1. Metadata
    project = pg.query("SELECT * FROM projects WHERE id = ?", project_id)
    
    // 2. Artifact tree
    artifacts = pg.query("""
        WITH RECURSIVE tree AS (
            SELECT * FROM artifacts WHERE project_id = ? AND parent_artifact_id IS NULL
            UNION ALL
            SELECT a.* FROM artifacts a JOIN tree t ON a.parent_artifact_id = t.id
        ) SELECT * FROM tree
    """, project_id)
    
    // 3. Evaluations
    evaluations = pg.query("""
        SELECT e.* FROM evaluations e
        JOIN artifacts a ON e.artifact_id = a.id
        WHERE a.project_id = ?
        ORDER BY e.created_at
    """, project_id)
    
    // 4. Agent runs
    agent_runs = pg.query("""
        SELECT ar.* FROM agent_runs ar
        JOIN tasks t ON ar.task_id = t.id
        WHERE t.project_id = ?
    """, project_id)
    
    // 5. Graph
    graph = neo4j.run("""
        MATCH (p:Project {id: $pid})-[r*1..5]-(n)
        RETURN p, r, n
    """, {pid: project_id})
    
    // 6. Key metrics
    summary = {
        total_iterations: SUM(e.iteration for e in evaluations if not e.passed),
        first_pass_rate: % of artifacts that passed on iteration 1,
        avg_iterations_to_pass: AVG iterations for passed artifacts,
        total_tokens: SUM all agent_run.tokens_total,
        total_cost: SUM all agent_run.cost_usd,
        duration: project.completed_at - project.created_at,
        incident_count: count of incidents for project
    }
    
    RETURN ProjectHistory(full artifact tree, evaluation timeline, agent run logs, graph, summary)
```

## 6.4 Retention Policy

| Action | Timeline | Description |
|--------|----------|-------------|
| Active | During project | All data fully accessible |
| Completed | Project end | Data frozen. No further modifications. |
| Archived | +6 months | Move to cold storage (S3 Glacier). Summary retained in hot DB. |
| Learning extraction | On archive | Run knowledge extraction pipeline before archiving. Store extracted patterns. |
| Deleted | +5 years | Permanent deletion (GDPR/retention policy). Anonymized patterns kept. |

## 6.5 Update Strategy

Project history is **append-only** after project completion. No updates permitted.

```
ARCHIVE_PIPELINE:
    1. Snapshot project graph from Neo4j -> export as JSON
    2. Export all artifact versions -> compressed archive
    3. Export evaluation history -> aggregated summary
    4. Run knowledge extraction on full project
    5. Store extracted knowledge in learning_records and Neo4j
    6. Move raw data to cold storage
    7. Mark project status = 'archived' in PostgreSQL
    8. Delete project-specific embeddings from Qdrant (knowledge retained in learning)
```

---

# 7. Learning Records

## 7.1 Purpose

Structured records of every quality loop iteration, used by the Self-Learning Engine to extract patterns, optimize prompts, and improve future agent performance.

## 7.2 Storage

| Property | Value |
|----------|-------|
| **Primary Store** | PostgreSQL `learning_records` table |
| **Embedding Store** | Qdrant `knowledge_snippets` collection (3072d) |
| **Graph Store** | Neo4j `LearnedPattern` nodes with relationships |
| **Indexing** | Composite index on (artifact_type, gate_type, passed) |

## 7.3 Schema

### 7.3.1 PostgreSQL (already defined in Section 3)

The `learning_records` table captures:

```
learning_records:
  id, artifact_type, gate_type, agent_type, model_used,
  system_prompt_hash, input_prompt, output_content,
  iteration_count, scores_history, final_score, passed,
  critiques, improvements, tokens_total, total_duration_ms,
  extracted_knowledge (JSONB), knowledge_applied, created_at
```

### 7.3.2 Qdrant knowledge_snippets payload

```json
{
  "learning_record_id": "uuid",
  "knowledge_type": "successful_prompt_pattern",
  "category": "prd_generation",
  "description": "PRDs that include quantified success metrics pass requirements gate in 1.4 fewer iterations on average",
  "confidence": 0.87,
  "support_count": 42,
  "contradict_count": 3,
  "applicable_agent_types": ["product_manager"],
  "applicable_gate_types": ["requirements_gate"],
  "prompt_modification": "Add: 'For every feature, define a specific measurable success metric (e.g., reduce X by Y% within Z weeks).'",
  "source_iterations": ["uuid1", "uuid2", ...],
  "created_at": "ISO8601",
  "last_validated_at": "ISO8601",
  "active": true
}
```

### 7.3.3 Neo4j LearnedPattern nodes

```cypher
// Create a learned pattern
MERGE (lp:LearnedPattern {
    id: $id,
    pattern_type: "successful_prompt_pattern",
    category: "prd_generation",
    description: "Quantified success metrics reduce iterations",
    confidence: 0.87,
    support_count: 42,
    active: true
})

// Link pattern to its source records
MATCH (lp:LearnedPattern {id: $id})
MATCH (lr:LearningRecord) WHERE lr.id IN $source_ids
CREATE (lp)-[:LEARNED_FROM]->(lr)

// Link pattern to applicable entities
MATCH (lp:LearnedPattern {id: $id})
MATCH (m:MetricDefinition {name: "business_alignment"})
CREATE (lp)-[:IMPROVES]->(m)
```

## 7.4 Retrieval Methods

| Query | Method | Use Case |
|-------|--------|----------|
| "Find successful patterns for PRD generation" | PostgreSQL: `SELECT * FROM learning_records WHERE artifact_type='prd' AND passed=true ORDER BY final_score DESC LIMIT 100` | Prompt optimization |
| "What prompts led to first-iteration passes?" | PostgreSQL: `SELECT input_prompt FROM learning_records WHERE iteration_count=1 AND passed=true` | Prompt template extraction |
| "What are the most common failure causes?" | Qdrant: semantic search on critiques + aggregate | Pattern analysis |
| "Find similar tasks to current" | Qdrant: embed current task -> search agent_memory | Context injection |
| "Show me the learning trajectory" | PostgreSQL: `SELECT date_trunc('week', created_at), AVG(iteration_count), AVG(final_score) GROUP BY 1 ORDER BY 1` | Learning effectiveness |
| "What patterns apply to this agent?" | Neo4j: `MATCH (lp:LearnedPattern)-[:APPLIES_TO]->(:Microservice) WHERE lp.applicable_agent_types CONTAINS $agent_type` | Pattern injection |

## 7.5 Retention Policy

| Data | Retention | Policy |
|------|-----------|--------|
| Raw learning_records | Forever | Core asset — never delete |
| Extracted knowledge in Qdrant | Forever | Active patterns kept. Inactive (contradicted) patterns soft-deleted. |
| LearnedPattern in Neo4j | Forever | Confidence updated over time. Low-confidence patterns deprecated. |
| Aggregated statistics | Forever | Rolling aggregation for dashboards |

## 7.6 Update Strategy

```
LEARNING_PIPELINE:

    // 1. Record every iteration (streaming)
    ON IterationRecorded event:
        INSERT INTO learning_records (...)

    // 2. Batch extraction (hourly)
    EVERY 1 hour:
        SELECT unprocessed learning_records
        FOR EACH batch:
            knowledge = llm.extract_patterns(batch)
            INSERT extracted knowledge into knowledge_snippets (Qdrant)
            CREATE/MERGE LearnedPattern nodes (Neo4j)
            UPDATE learning_records SET extracted_knowledge = knowledge
    
    // 3. Pattern validation (daily)
    EVERY 24 hours:
        SELECT all active LearnedPatterns
        FOR EACH pattern:
            recent_data = query last 7 days of learning_records
            validate pattern against recent_data
            UPDATE pattern.confidence = new_confidence
            IF confidence < 0.5:
                DEACTIVATE pattern
    
    // 4. Prompt optimization (on pattern change)
    ON pattern activated or confidence changed:
        relevant_prompts = find prompts affected by pattern
        new_prompt = llm.incorporate_pattern(prompt, pattern)
        STORE new prompt version in prompts/
        EMIT PromptOptimized event
```

---

# 8. Memory Service API

## 8.1 Unified API Endpoints

```
POST   /api/v1/memory/store
       Body: { tier: "short|long|semantic|graph", data: {...} }
       Stores data in the specified memory tier.

GET    /api/v1/memory/search
       Query: ?q={text}&tier={short|long|semantic|graph|all}&limit=20&project_id={uuid}
       Searches across memory tiers.

POST   /api/v1/memory/context/{agent_id}
       Body: { task_type: "code_generation", query: "user authentication" }
       Returns assembled context from all relevant tiers.

GET    /api/v1/memory/project/{project_id}/history
       Returns full project history (all tiers).

POST   /api/v1/memory/embedding/ingest
       Body: { collection: "code_embeddings", documents: [...] }
       Ingests documents into Qdrant.

GET    /api/v1/memory/graph/query
       Query: ?cypher={cypher_query}
       Executes read-only Cypher query.

GET    /api/v1/memory/graph/entity/{type}/{id}/relations
       Returns all relationships for an entity.

POST   /api/v1/memory/knowledge/extract
       Body: { learning_record_ids: [...] }
       Triggers knowledge extraction for specified records.

GET    /api/v1/memory/knowledge/patterns
       Query: ?agent_type={type}&gate_type={type}&active=true
       Returns applicable learned patterns.
```

## 8.2 Context Assembly Algorithm

```
ASSEMBLE_CONTEXT(agent_id, task_type, query):
    
    context = {}
    
    // 1. Agent short-term memory (what is agent currently doing?)
    context.agent_state = redis.get(f"aisc:agent:{agent_id}:state")
    context.current_task = redis.get(f"aisc:task:{context.agent_state.task_id}:context")
    
    // 2. Semantic search (what is relevant knowledge?)
    embedding = embed(query)
    context.relevant_code = qdrant.search("code_embeddings", embedding, limit=5)
    context.relevant_docs = qdrant.search("doc_embeddings", embedding, limit=5)
    context.relevant_experiences = qdrant.search("agent_memory", embedding, limit=3)
    
    // 3. Graph context (what is this connected to?)
    IF task has project_id:
        context.project_graph = neo4j.run("""
            MATCH (p:Project {id: $pid})-[r*1..2]-(n)
            RETURN labels(n), n, type(r)
        """)
    
    // 4. Learning patterns (what worked before?)
    context.patterns = pg.query("""
        SELECT * FROM learning_records
        WHERE artifact_type = ?
        AND gate_type = ?
        AND passed = true
        ORDER BY final_score DESC
        LIMIT 5
    """)
    
    // 5. Long-term memory (what artifacts exist?)
    context.existing_artifacts = pg.query("""
        SELECT * FROM artifacts
        WHERE project_id = ?
        ORDER BY created_at DESC
    """)
    
    // 6. Assemble ranked context
    assembled = rank_and_truncate(context, max_tokens=8000)
    
    RETURN assembled
```

## 8.3 Multi-Tier Query Routing

```
ROUTE_QUERY(query):

    SWITCH query.type:
        
        CASE "get_agent_state":
            RETURN redis.get(key)
        
        CASE "search_similar_code":
            embedding = embed(query.text)
            RETURN qdrant.search("code_embeddings", embedding, query.limit)
        
        CASE "get_project_artifacts":
            RETURN pg.query("SELECT * FROM artifacts WHERE project_id = ?", query.project_id)
        
        CASE "trace_artifact_dependencies":
            RETURN neo4j.run("MATCH (a:Artifact {id: $id})-[r*1..3]->(n) RETURN ...")
        
        CASE "find_learning_patterns":
            RETURN pg.query("SELECT * FROM learning_records WHERE artifact_type = ? AND passed = true", query.artifact_type)
        
        CASE "cross_tier_search":
            // Parallel multi-tier search
            results = parallel([
                redis.scan(query.pattern),       // Short-term
                pg.search(query.text),           // Long-term (trigram)
                qdrant.search(query.embedding),  // Semantic
                neo4j.search(query.text)         // Graph
            ])
            RETURN merge_and_rank(results)
        
        CASE "assemble_agent_context":
            RETURN assemble_context(query.agent_id, query.task_type, query.user_query)
```

---

# 9. Cross-Memory Query Patterns

## 9.1 Typical Agent Workflow Memory Access

```
Agent Startup:
    1. Redis: GET agent state, heartbeat registration
    2. PG: GET project info, task details
    3. Qdrant: GET similar task experiences
    4. Neo4j: GET project relationships

Agent Execution:
    1. Qdrant: SEARCH relevant code patterns, docs, past successes
    2. PG: GET related artifacts (architecture, PRD)
    3. Neo4j: GET dependency graph, API contracts
    4. Redis: UPDATE task progress, cache intermediate results

Agent Completion:
    1. PG: INSERT artifact, version, evaluation
    2. Qdrant: UPSERT new embeddings
    3. Neo4j: MERGE new entity nodes, CREATE relationships
    4. Redis: DELETE task state, UPDATE agent to IDLE
    5. Redis PubSub: PUBLISH ArtifactCreated event
```

## 9.2 Data Consistency Across Tiers

| Scenario | Strategy | Consistency |
|----------|----------|-------------|
| Artifact created | Write to PG first (source of truth). On success: write to Qdrant + Neo4j. On failure: retry or log for reconciliation. | Eventually consistent across tiers |
| Artifact updated | Same as create. Old embeddings deleted, new inserted in same Qdrant batch. | Eventually |
| Project archived | Cascade: PG mark archived -> Qdrant delete embeddings -> Neo4j export then delete subgraph | Eventually |
| Incident recorded | Write to PG. On success: create Bug/Solution in Neo4j. On success: embed error in Qdrant. | Eventually |
| Learning pattern extracted | Write to PG learning_records -> Qdrant knowledge_snippets -> Neo4j LearnedPattern. All in batch. | Eventually |

## 9.3 Reconciliation Process

```
RECONCILE (runs daily):
    
    // Find orphaned embeddings (Qdrant points with no matching PG artifact)
    orphaned_embeddings = qdrant_ids - pg_artifact_ids
    DELETE orphaned_embeddings from Qdrant
    
    // Find missing embeddings (PG artifacts with no Qdrant point)
    missing_embeddings = pg_artifact_ids - qdrant_ids
    FOR EACH missing:
        artifact = pg.get(id)
        embedding = embed(artifact.content)
        qdrant.upsert(artifact.id, embedding, payload)
    
    // Find orphaned graph nodes (Neo4j nodes with no matching PG entity)
    orphaned_nodes = neo4j_ids - pg_ids
    DETACH DELETE orphaned_nodes
    
    // Find missing graph nodes
    missing_nodes = pg_ids - neo4j_ids
    FOR EACH missing:
        neo4j.create_node(entity)
```

---

*End of Memory Architecture Specification*
