# AISC — Event Catalog

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Event Architecture

All actions in AISC emit events to Apache Kafka. Events decouple microservices, enable event sourcing for state reconstruction, and feed the Self-Learning Engine.

### 1.1 Event Envelope

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "ArtifactScored",
  "timestamp": "2026-06-18T09:15:00.000Z",
  "source_service": "scoring-engine",
  "source_agent": "qa_agent",
  "correlation_id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "770e8400-e29b-41d4-a716-446655440002",
  "task_id": "880e8400-e29b-41d4-a716-446655440003",
  "payload": {},
  "version": "1.0"
}
```

### 1.2 Kafka Topic Configuration

| Property | Value |
|----------|-------|
| Partitions per topic | 3-10 (based on throughput) |
| Replication factor | 3 |
| Retention | 7 days (events), 30 days (audit) |
| Compression | snappy |
| Cleanup policy | delete (events), compact (state snapshots) |

---

## 2. Complete Event Catalog (47 Events)

### 2.1 Project Events

#### ProjectCreated
| Field | Detail |
|-------|--------|
| **Publisher** | Orchestrator Service |
| **Consumers** | Memory Service, Observability, WebSocket Gateway |
| **Topic** | `aisc.projects` |
| **Description** | New project has been created by a user |
```json
{
  "event_type": "ProjectCreated",
  "payload": {
    "project_id": "uuid",
    "name": "My SaaS App",
    "owner_id": "uuid",
    "config": { "budget_tokens": 1000000 },
    "created_by": "user@example.com"
  }
}
```

#### ProjectUpdated
| Publisher | Orchestrator Service |
| Consumers | Memory Service, WebSocket Gateway |
| Topic | `aisc.projects` |
```json
{
  "event_type": "ProjectUpdated",
  "payload": {
    "project_id": "uuid",
    "changes": { "status": "running" },
    "updated_by": "user@example.com"
  }
}
```

#### ProjectArchived
| Publisher | Orchestrator Service |
| Consumers | Memory Service, Self-Learning Engine |
| Topic | `aisc.projects` |
```json
{
  "event_type": "ProjectArchived",
  "payload": {
    "project_id": "uuid",
    "reason": "Project completed successfully",
    "archived_by": "orchestrator"
  }
}
```

---

### 2.2 Workflow Events

#### WorkflowStarted
| Publisher | Orchestrator Service |
| Consumers | All agents involved, Memory Service, WebSocket |
| Topic | `aisc.workflows` |
```json
{
  "event_type": "WorkflowStarted",
  "payload": {
    "workflow_id": "uuid",
    "project_id": "uuid",
    "total_nodes": 15,
    "agent_types_involved": ["pm", "research", "architect", "developer"]
  }
}
```

#### WorkflowNodeCompleted
| Publisher | Orchestrator Service |
| Consumers | Orchestrator Service (self, to advance DAG) |
| Topic | `aisc.workflows` |
```json
{
  "event_type": "WorkflowNodeCompleted",
  "payload": {
    "workflow_id": "uuid",
    "node_id": "uuid",
    "task_id": "uuid",
    "agent_type": "architect",
    "artifacts_produced": ["uuid1", "uuid2"],
    "duration_ms": 45000
  }
}
```

#### WorkflowCompleted
| Publisher | Orchestrator Service |
| Consumers | Self-Learning Engine, Memory Service |
| Topic | `aisc.workflows` |
```json
{
  "event_type": "WorkflowCompleted",
  "payload": {
    "workflow_id": "uuid",
    "project_id": "uuid",
    "total_tasks": 15,
    "total_iterations": 42,
    "total_tokens": 850000,
    "duration_ms": 3600000
  }
}
```

#### WorkflowFailed
| Publisher | Orchestrator Service |
| Consumers | Self-Healing Engine, Observability |
| Topic | `aisc.workflows` |
```json
{
  "event_type": "WorkflowFailed",
  "payload": {
    "workflow_id": "uuid",
    "failed_node_id": "uuid",
    "failed_task_id": "uuid",
    "error": "Max iterations reached for code gate",
    "escalation_id": "uuid"
  }
}
```

---

### 2.3 Task Events

#### TaskCreated
| Publisher | Orchestrator Service |
| Consumers | Agent Runtime, Memory Service |
| Topic | `aisc.tasks` |
```json
{
  "event_type": "TaskCreated",
  "payload": {
    "task_id": "uuid",
    "project_id": "uuid",
    "task_type": "code_generation",
    "assigned_agent_type": "developer",
    "priority": 5,
    "input": {},
    "dependencies": ["uuid1"]
  }
}
```

#### TaskAssigned
| Publisher | Orchestrator Service |
| Consumers | Agent Runtime, Memory Service, WebSocket |
| Topic | `aisc.tasks` |
```json
{
  "event_type": "TaskAssigned",
  "payload": {
    "task_id": "uuid",
    "agent_id": "developer-001",
    "agent_type": "developer",
    "queue_wait_ms": 500
  }
}
```

#### TaskStarted
| Publisher | Agent Runtime |
| Consumers | Orchestrator, Memory Service |
| Topic | `aisc.tasks` |
```json
{
  "event_type": "TaskStarted",
  "payload": {
    "task_id": "uuid",
    "agent_id": "developer-001",
    "agent_type": "developer"
  }
}
```

#### TaskCompleted
| Publisher | Agent Runtime |
| Consumers | Orchestrator, Quality Gate Service, Memory Service, WebSocket |
| Topic | `aisc.tasks` |
```json
{
  "event_type": "TaskCompleted",
  "payload": {
    "task_id": "uuid",
    "agent_id": "developer-001",
    "artifact_ids": ["uuid1", "uuid2"],
    "tokens_used": 15000,
    "llm_model": "claude-3.5-sonnet",
    "duration_ms": 45000
  }
}
```

#### TaskFailed
| Publisher | Agent Runtime |
| Consumers | Orchestrator, Self-Healing Engine, WebSocket |
| Topic | `aisc.tasks` |
```json
{
  "event_type": "TaskFailed",
  "payload": {
    "task_id": "uuid",
    "agent_id": "developer-001",
    "error": "LLM provider timeout after 3 retries",
    "error_type": "llm_provider_error",
    "retry_count": 3,
    "tokens_consumed_before_failure": 5000
  }
}
```

---

### 2.4 Artifact Lifecycle Events

#### ArtifactDraftCreated
| Publisher | Agent Runtime |
| Consumers | Quality Gate Service, Memory Service |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactDraftCreated",
  "payload": {
    "artifact_id": "uuid",
    "project_id": "uuid",
    "task_id": "uuid",
    "type": "prd",
    "format": "markdown",
    "created_by_agent": "product_manager",
    "version": 1
  }
}
```

#### ArtifactSubmittedForReview
| Publisher | Agent Runtime |
| Consumers | Debate Service, Quality Gate Service |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactSubmittedForReview",
  "payload": {
    "artifact_id": "uuid",
    "artifact_type": "architecture_document",
    "gate_type": "architecture_gate",
    "version": 3
  }
}
```

#### ArtifactReviewStarted
| Publisher | Debate Service |
| Consumers | Observability |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactReviewStarted",
  "payload": {
    "artifact_id": "uuid",
    "debate_id": "uuid",
    "reviewer_ids": ["reviewer-A", "reviewer-B", "reviewer-C"]
  }
}
```

#### ArtifactCritiqueGenerated
| Publisher | Reviewer Agent (via Agent Runtime) |
| Consumers | Consensus Agent |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactCritiqueGenerated",
  "payload": {
    "artifact_id": "uuid",
    "debate_id": "uuid",
    "reviewer_id": "reviewer-A",
    "critique": {
      "overall_score": 84,
      "metric_scores": { "scalability": 78, "reliability": 90 },
      "issues": ["No horizontal scaling strategy defined"],
      "strengths": ["Good service decomposition"],
      "improvements": ["Add auto-scaling rules for each service"]
    }
  }
}
```

#### ArtifactConsensusReached
| Publisher | Consensus Agent |
| Consumers | Orchestrator, Improvement Agent (if needed) |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactConsensusReached",
  "payload": {
    "artifact_id": "uuid",
    "debate_id": "uuid",
    "consensus": "pass",
    "agreement_score": 0.85,
    "rounds": 1
  }
}
```

#### ArtifactImproved
| Publisher | Improvement Agent |
| Consumers | Quality Gate Service |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactImproved",
  "payload": {
    "artifact_id": "uuid",
    "previous_version": 3,
    "new_version": 4,
    "changes_summary": "Added horizontal scaling strategy with HPA configuration",
    "critiques_addressed": 3
  }
}
```

#### ArtifactScored
| Publisher | Scoring Engine |
| Consumers | Quality Gate Service, Memory Service |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactScored",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "iteration": 3,
    "aggregate_score": 93.5,
    "metric_scores": {
      "complexity": 95,
      "maintainability": 92,
      "testability": 94,
      "performance": 91,
      "security": 96
    },
    "passed": true
  }
}
```

#### ArtifactApproved
| Publisher | Quality Gate Service |
| Consumers | Orchestrator, Memory Service, Self-Learning Engine |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactApproved",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "score": 93.5,
    "iterations_taken": 3
  }
}
```

#### ArtifactRejected
| Publisher | Quality Gate Service |
| Consumers | Orchestrator, Agent Runtime (trigger improvement loop) |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactRejected",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "score": 78,
    "iteration": 2,
    "failing_metrics": ["performance", "security"],
    "reason": "Score below threshold of 92"
  }
}
```

#### ArtifactFinalized
| Publisher | Quality Gate Service |
| Consumers | Memory Service, Self-Learning Engine |
| Topic | `aisc.artifacts` |
```json
{
  "event_type": "ArtifactFinalized",
  "payload": {
    "artifact_id": "uuid",
    "final_version": 4,
    "final_score": 93.5,
    "total_iterations": 3,
    "gate_type": "code_gate"
  }
}
```

---

### 2.5 Quality & Loop Events

#### QualityGateEvaluated
| Publisher | Quality Gate Service |
| Consumers | Observability |
| Topic | `aisc.quality` |
```json
{
  "event_type": "QualityGateEvaluated",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "iteration": 2,
    "score": 78,
    "passed": false
  }
}
```

#### QualityGatePassed
| Publisher | Quality Gate Service |
| Consumers | Orchestrator |
| Topic | `aisc.quality` |
```json
{
  "event_type": "QualityGatePassed",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "score": 93.5,
    "iterations": 3
  }
}
```

#### QualityGateFailed
| Publisher | Quality Gate Service |
| Consumers | Orchestrator, Agent Runtime |
| Topic | `aisc.quality` |
```json
{
  "event_type": "QualityGateFailed",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "final_score": 88,
    "max_iterations_reached": true,
    "iterations_exhausted": 7,
    "escalation_id": "uuid"
  }
}
```

#### RecursiveLoopStarted
| Publisher | Quality Gate Service |
| Consumers | Observability |
| Topic | `aisc.quality` |
```json
{
  "event_type": "RecursiveLoopStarted",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "max_iterations": 7,
    "threshold": 92
  }
}
```

#### RecursiveLoopIteration
| Publisher | Quality Gate Service |
| Consumers | Self-Learning Engine |
| Topic | `aisc.quality` |
```json
{
  "event_type": "RecursiveLoopIteration",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "iteration": 2,
    "score": 78,
    "score_delta": 6,
    "improving": true
  }
}
```

#### RecursiveLoopCompleted
| Publisher | Quality Gate Service |
| Consumers | Self-Learning Engine |
| Topic | `aisc.quality` |
```json
{
  "event_type": "RecursiveLoopCompleted",
  "payload": {
    "artifact_id": "uuid",
    "gate_type": "code_gate",
    "total_iterations": 3,
    "final_score": 93.5,
    "passed": true,
    "score_progression": [72, 78, 93.5]
  }
}
```

---

### 2.6 Deployment Events

#### DeploymentRequested
| Publisher | Orchestrator Service |
| Consumers | DevOps Agent |
| Topic | `aisc.deployments` |
```json
{
  "event_type": "DeploymentRequested",
  "payload": {
    "project_id": "uuid",
    "service_names": ["auth-service", "user-service"],
    "environment": "staging",
    "strategy": "canary",
    "artifact_ids": ["uuid1", "uuid2"]
  }
}
```

#### BuildStarted / BuildCompleted / BuildFailed
| Publisher | DevOps Agent |
| Consumers | Monitoring (completed), Self-Healing (failed), Observability |
| Topic | `aisc.deployments` |
```json
{
  "event_type": "BuildCompleted",
  "payload": {
    "build_id": "uuid",
    "service_name": "auth-service",
    "image_tag": "sha-abc123",
    "image_size_mb": 145,
    "duration_ms": 120000
  }
}
```

#### DeploymentStarted / DeploymentCompleted / DeploymentFailed
| Publisher | DevOps Agent |
| Consumers | Monitoring (+Observability), Self-Healing (failed), Orchestrator (completed) |
| Topic | `aisc.deployments` |
```json
{
  "event_type": "DeploymentCompleted",
  "payload": {
    "deployment_id": "uuid",
    "environment": "production",
    "services_deployed": ["auth-service", "user-service"],
    "canary_promoted": true,
    "duration_ms": 300000
  }
}
```

#### RollbackInitiated / RollbackCompleted
| Publisher | Self-Healing Agent -> DevOps Agent |
| Consumers | Orchestrator (completed) |
| Topic | `aisc.deployments` |
```json
{
  "event_type": "RollbackCompleted",
  "payload": {
    "deployment_id": "uuid",
    "rollback_to_version": "v2.3.1",
    "reason": "Error rate exceeded 10% threshold",
    "duration_ms": 60000
  }
}
```

---

### 2.7 Production Events

#### MetricAnomalyDetected
| Publisher | Monitoring Agent |
| Consumers | Self-Healing Engine, Observability |
| Topic | `aisc.monitoring` |
```json
{
  "event_type": "MetricAnomalyDetected",
  "payload": {
    "service_name": "user-service",
    "metric": "p95_latency",
    "current_value": 1200,
    "baseline_value": 300,
    "deviation_sigma": 4.5,
    "detected_at": "ISO8601"
  }
}
```

#### AlertTriggered
| Publisher | Monitoring Agent |
| Consumers | Self-Healing Engine, Orchestrator, WebSocket |
| Topic | `aisc.monitoring` |
```json
{
  "event_type": "AlertTriggered",
  "payload": {
    "alert_id": "uuid",
    "severity": "HIGH",
    "title": "P95 latency 4x baseline in user-service",
    "service_name": "user-service",
    "metric": "p95_latency",
    "suggested_actions": ["Check DB connection pool", "Check recent deployment"]
  }
}
```

#### FailureDetected
| Publisher | Monitoring Agent |
| Consumers | Self-Healing Engine |
| Topic | `aisc.monitoring` |
```json
{
  "event_type": "FailureDetected",
  "payload": {
    "service_name": "payment-service",
    "failure_type": "5xx_spike",
    "error_rate": 0.15,
    "started_at": "ISO8601",
    "trace_ids": ["trace1", "trace2"]
  }
}
```

#### RootCauseIdentified
| Publisher | Self-Healing Agent |
| Consumers | Memory Service, Self-Learning Engine |
| Topic | `aisc.incidents` |
```json
{
  "event_type": "RootCauseIdentified",
  "payload": {
    "incident_id": "uuid",
    "rca": {
      "root_cause": "Connection pool exhaustion in /api/v1/users endpoint",
      "confidence": 0.87,
      "evidence": ["logs show 'QueuePool limit overflow'", "trace shows no connection.close() calls"],
      "affected_code": "services/user-service/src/routes/users.py:45-78"
    }
  }
}
```

#### PatchGenerated / PatchValidated / PatchDeployed
| Publisher | Self-Healing Agent |
| Consumers | QA (validated), DevOps (deployed), Orchestrator + Monitoring (deployed) |
| Topic | `aisc.incidents` |
```json
{
  "event_type": "PatchDeployed",
  "payload": {
    "incident_id": "uuid",
    "patch_artifact_id": "uuid",
    "deployment_id": "uuid",
    "canary_promoted": true,
    "error_rate_after": 0.001,
    "duration_ms": 600000
  }
}
```

---

### 2.8 Learning Events

#### IterationRecorded
| Publisher | Any agent (via Agent Runtime) |
| Consumers | Self-Learning Engine |
| Topic | `aisc.learning` |
```json
{
  "event_type": "IterationRecorded",
  "payload": {
    "artifact_type": "prd",
    "gate_type": "requirements_gate",
    "agent_type": "product_manager",
    "iteration": 2,
    "score": 84,
    "passed": false,
    "tokens_used": 5000,
    "model": "claude-3.5-sonnet"
  }
}
```

#### KnowledgeExtracted
| Publisher | Self-Learning Engine |
| Consumers | Knowledge Agent, Memory Service |
| Topic | `aisc.learning` |
```json
{
  "event_type": "KnowledgeExtracted",
  "payload": {
    "pattern_id": "uuid",
    "pattern_type": "successful_prompt_pattern",
    "description": "PRDs with quantified success metrics pass in fewer iterations",
    "confidence": 0.87,
    "support_count": 42,
    "applicable_agents": ["product_manager"]
  }
}
```

#### PromptOptimized
| Publisher | Self-Learning Engine |
| Consumers | Agent Runtime |
| Topic | `aisc.learning` |
```json
{
  "event_type": "PromptOptimized",
  "payload": {
    "agent_type": "product_manager",
    "prompt_file": "prompts/product_manager.md",
    "prompt_version": "v2.4",
    "changes": "Added instruction to include quantified success metrics for each feature"
  }
}
```

#### PatternIdentified
| Publisher | Self-Learning Engine |
| Consumers | Knowledge Graph |
| Topic | `aisc.learning` |
```json
{
  "event_type": "PatternIdentified",
  "payload": {
    "pattern_type": "failure_pattern",
    "description": "Missing connection.close() in finally block causes pool exhaustion",
    "occurrences": 7,
    "affected_services": ["user-service", "payment-service"],
    "suggested_prevention": "Add linting rule for unclosed DB connections"
  }
}
```

---

### 2.9 System Events

#### ServiceHealthChanged
| Publisher | Health check monitor |
| Consumers | Observability, WebSocket |
| Topic | `aisc.system` |
```json
{
  "event_type": "ServiceHealthChanged",
  "payload": {
    "service_name": "scoring-engine",
    "previous_status": "healthy",
    "new_status": "degraded",
    "reason": "PostgreSQL connection pool exhausted"
  }
}
```

#### AgentStatusChanged
| Publisher | Agent Runtime |
| Consumers | Orchestrator, WebSocket |
| Topic | `aisc.system` |
```json
{
  "event_type": "AgentStatusChanged",
  "payload": {
    "agent_id": "developer-001",
    "agent_type": "developer",
    "previous_status": "IDLE",
    "new_status": "BUSY",
    "task_id": "uuid"
  }
}
```

#### EscalationCreated / EscalationResolved
| Publisher | Quality Gate Service / Human |
| Consumers | WebSocket, Orchestrator |
| Topic | `aisc.system` |
```json
{
  "event_type": "EscalationCreated",
  "payload": {
    "escalation_id": "uuid",
    "type": "max_iterations_exceeded",
    "severity": "HIGH",
    "target_role": "human_architect",
    "artifact_id": "uuid",
    "timeout": "ISO8601"
  }
}
```

---

## 3. Event Topic Map

| Topic | Partition Count | Events | Retention |
|-------|:--------------:|--------|:---------:|
| `aisc.projects` | 3 | ProjectCreated, ProjectUpdated, ProjectArchived | 30 days |
| `aisc.workflows` | 3 | WorkflowStarted, NodeCompleted, Completed, Failed | 30 days |
| `aisc.tasks` | 6 | TaskCreated, Assigned, Started, Completed, Failed | 7 days |
| `aisc.artifacts` | 6 | All 10 artifact lifecycle events | 7 days |
| `aisc.quality` | 3 | All 6 quality/loop events | 7 days |
| `aisc.deployments` | 3 | All 9 deployment events | 30 days |
| `aisc.monitoring` | 6 | MetricAnomaly, Alert, FailureDetected | 3 days |
| `aisc.incidents` | 3 | RCA, Patch*, Incident* | 30 days |
| `aisc.learning` | 3 | IterationRecorded, KnowledgeExtracted, PromptOptimized, PatternIdentified | 30 days |
| `aisc.system` | 3 | HealthChanged, AgentStatus, Escalation* | 7 days |

---

## 4. Event Ordering Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| Per-project ordering | All events for a project routed to same partition via `project_id` key |
| Per-artifact ordering | Artifact events share partition with project |
| At-least-once delivery | Consumer commits after processing; retry on failure |
| Idempotency | `event_id` deduplication in consumer; idempotent handlers |
| Dead letter queue | Unprocessable events -> `aisc.dlq.{topic}` after 3 retries |

---

*End of Event Catalog*
