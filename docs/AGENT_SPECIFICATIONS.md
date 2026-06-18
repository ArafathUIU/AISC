# AISC — Agent Design Specification

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0
**Status**: Complete Specification

---

# Table of Contents

1. [Overview](#1-overview)
2. [Orchestrator Agent](#2-orchestrator-agent)
3. [Product Manager Agent](#3-product-manager-agent)
4. [Research Agent](#4-research-agent)
5. [Architect Agent](#5-architect-agent)
6. [Developer Agent](#6-developer-agent)
7. [QA Agent](#7-qa-agent)
8. [Security Agent](#8-security-agent)
9. [DevOps Agent](#9-devops-agent)
10. [Monitoring Agent](#10-monitoring-agent)
11. [Self-Healing Agent](#11-self-healing-agent)
12. [Cross-Agent Matrix](#12-cross-agent-matrix)

---

# 1. Overview

Each AISC agent is a specialized AI entity with defined responsibilities, tools, memory access, and quality gates. Agents operate within the Agent Runtime and communicate via the Event Bus. Every agent inherits from `BaseAgent` and follows the recursive quality loop.

---

# 2. Orchestrator Agent

## 2.1 Purpose

The Orchestrator Agent acts as the CEO of the AI software company. It does not produce software artifacts directly — it coordinates, schedules, prioritizes, and resolves conflicts across all other agents.

## 2.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| O1 | **Project Coordination** | Receives project definition from human. Decomposes into phases and tasks. Creates the workflow DAG. |
| O2 | **Agent Scheduling** | Matches tasks to agents by capability. Manages agent availability. Queues tasks when all agents busy. |
| O3 | **Workflow Management** | Tracks DAG execution. Advances nodes when dependencies satisfied. Detects and resolves deadlocks. |
| O4 | **Dependency Tracking** | Ensures artifacts are produced in correct order. Code depends on architecture. Tests depend on code. |
| O5 | **Priority Management** | Assigns priorities. Implements priority-based scheduling with aging. Handles priority inversion. |
| O6 | **Escalation Handling** | Receives escalations from quality gates and agents. Routes to appropriate human. Tracks resolution. |
| O7 | **Resource Governance** | Manages token budgets per project. Enforces cost limits. Pauses tasks when budget exceeded. |
| O8 | **Status Reporting** | Emits project status updates. Provides real-time progress via WebSocket. Generates summary reports. |

## 2.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Project Definition | Human (via UI/API) | Natural language + optional structured fields |
| Business Context | Human | Market description, goals, constraints |
| Agent Status Updates | Agent Runtime | `AgentStatusChanged` events |
| Task Results | All Agents | `TaskCompleted` / `TaskFailed` events |
| Quality Gate Results | Quality Gate Service | `QualityGatePassed` / `QualityGateFailed` events |
| Escalation Responses | Human | Structured resolution via UI |
| Budget Status | Self-monitoring | Token usage metrics from LLM router |
| Deadline Constraints | Human (optional) | ISO8601 timestamp |

## 2.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Workflow DAG | Self, UI | Directed Acyclic Graph of tasks |
| Task Assignments | Agent Runtime | `TaskAssigned` event |
| Priority Updates | Agent Runtime | Reprioritized task queue |
| Project Status | UI, Human | Real-time WebSocket + REST response |
| Escalation Tickets | Human | Structured ticket with full context |
| Budget Warnings | Human | Notification when approaching limit |
| Completion Report | Human, Self-Learning | Summary of project outcomes |

## 2.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `WorkflowDAGEngine` | Create, traverse, and optimize task DAGs | Every project |
| `AgentScheduler` | Match tasks to available agents | Continuous |
| `DependencyResolver` | Validate and resolve task dependencies | Per task creation |
| `PriorityManager` | Assign and age priorities | Continuous |
| `EscalationRouter` | Route escalations to correct human role | On escalation |
| `BudgetTracker` | Monitor and enforce token budgets | Continuous |
| `WebSocketNotifier` | Push real-time updates to UI | On every state change |
| `RAGQueryTool` | Retrieve relevant project context and patterns | For complex decisions |

## 2.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (projects, tasks, workflows) | Yes | Yes | Persistent project state |
| Redis (agent states, task queue) | Yes | Yes | Real-time scheduling state |
| Knowledge Graph (project relationships) | Yes | Yes | Track project-requirement-artifact links |
| Vector DB (similar projects) | Yes | No | Retrieve patterns from past projects |
| Agent Session State | Yes | No | Monitor agent health |

## 2.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `projects:create` | Global | Create new projects |
| `projects:read` | All | Read any project |
| `projects:update` | All | Update project metadata |
| `projects:archive` | Owned | Archive completed/cancelled projects |
| `tasks:create` | All | Create tasks within projects |
| `tasks:assign` | All | Assign tasks to agents |
| `tasks:cancel` | All | Cancel pending tasks |
| `agents:monitor` | All | Read agent status and history |
| `agents:config` | All | Update agent configurations |
| `workflows:manage` | All | Create, update, delete workflows |
| `escalations:manage` | All | Create and route escalations |
| `budget:manage` | All | Set and enforce token budgets |

## 2.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Scheduling Efficiency** | 25% | Ratio of agent idle time to total time. Tasks queued vs immediate assignment. | Automated (Redis metrics) |
| **Dependency Resolution Accuracy** | 25% | % of tasks that start with all dependencies truly satisfied. Zero false-starts. | Automated (workflow state) |
| **Escalation Response Time** | 20% | Time from escalation created to resolution (routed to correct human). | Automated (event timestamps) |
| **Resource Utilization** | 15% | Token cost vs budget. Priority adherence. | Automated (LLM router + budget) |
| **Deadlock Resolution** | 15% | Time to detect and resolve dependency deadlocks. | Automated (workflow engine) |

## 2.9 Quality Gates

The Orchestrator itself is not subject to the recursive quality loop in the same way as artifact-producing agents. Instead, it is evaluated on:

```yaml
orchestrator_monitoring:
  scheduling_latency:
    max: 500ms                    # Max time to assign task
  deadlock_detection_interval:
    max: 30s                      # Max time between deadlock checks
  escalation_routing_time:
    max: 2s                       # Time to route escalation
  stale_task_threshold:
    max: 5min                     # Task unassigned for >5min triggers alert
```

## 2.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| Deadlock detected (circular dependency in DAG) | Alert human. Present dependency graph. Suggest resolution. |
| All agents of a required type are in ERROR state | Alert human. No capable agent available. |
| Task has been queued for > 30 minutes (agent starvation) | Escalate. May indicate capacity issue. |
| Project token budget exceeded by > 20% | Escalate to project owner for budget decision. |
| Human override received that contradicts quality gate | Log. Notify. Execute human decision with audit trail. |
| 3 consecutive task failures for same agent type | Escalate. May indicate agent configuration issue. |

---

# 3. Product Manager Agent

## 3.1 Purpose

The Product Manager Agent translates business ideas into structured, actionable product requirements. It ensures that what gets built actually solves the right problem.

## 3.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| P1 | **Requirement Gathering** | Expands a business idea into a comprehensive PRD. Identifies problem, users, goals. |
| P2 | **User Story Generation** | Decomposes features into user stories with acceptance criteria in Gherkin format. |
| P3 | **Feature Prioritization** | Prioritizes features using MoSCoW (Must/Should/Could/Won't). Considers dependencies and value. |
| P4 | **Roadmap Planning** | Creates phased development roadmap with milestones and effort estimates. |
| P5 | **Success Metric Definition** | Defines measurable KPIs for each feature and the product as a whole. |
| P6 | **Market Analysis** | Incorporates research from Research Agent. Identifies user personas and their needs. |
| P7 | **Constraint Documentation** | Documents technical, business, timeline, and budget constraints. |

## 3.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Business Idea / Problem Statement | Human or Orchestrator | Natural language |
| Market Research | Research Agent | Research Report |
| Competitor Analysis | Research Agent | Competitive Matrix |
| Technical Constraints | Orchestrator, Human | Structured constraints |
| Target Audience / Personas | Human (optional) | User persona descriptions |
| Budget / Timeline | Human | Constraints |
| Previous PRDs (for learning) | Self-Learning Engine | Structured PRD with scores |

## 3.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Product Requirements Document (PRD) | Architect, Research, Human | Structured markdown |
| User Stories | Architect, Developer, QA | List of "As a/I want/So that" + Gherkin |
| Feature Specifications | Architect, Developer | Detailed feature descriptions |
| Development Roadmap | Human, Orchestrator | Phased milestones |
| Success Metrics (KPIs) | Human | Measurable goals |
| Risk Assessment | Human, Orchestrator | Identified risks + mitigations |

## 3.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `RAGQueryTool` | Retrieve similar PRDs, domain knowledge, industry standards | Every generation |
| `WebSearchTool` | Research market trends, user expectations | For new domains |
| `MoSCoWPrioritizer` | Structured prioritization of features | Every feature list |
| `UserStoryGenerator` | Generate consistent user stories from features | Every feature |
| `GherkinValidator` | Validate acceptance criteria syntax | Per story |
| `RoadmapGenerator` | Create phased roadmap | Per project |

## 3.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (artifacts) | Yes | Yes | Store PRDs, stories, roadmaps |
| Redis (session) | Yes | Yes | Intermediate drafts during generation |
| Vector DB | Yes | Yes | Query similar requirements; store embeddings |
| Knowledge Graph | Yes | Yes | Link requirements to features, stories, acceptance criteria |
| RAG | Yes | No | Retrieve domain knowledge, industry standards |

## 3.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `artifacts:create` | Assigned project | Create PRD, user stories, feature specs |
| `artifacts:update` | Own artifacts | Modify own artifacts during improvement loop |
| `artifacts:read` | Assigned project | Read research and architecture documents |
| `rag:query` | Global | Query RAG for context |
| `web:search` | Global | Web search for market research |
| `knowledge_graph:write` | Assigned project | Create requirement-feature-story relationships |

## 3.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Completeness** | 25% | All required PRD sections filled with substantive content | Structural + LLM |
| **Clarity** | 20% | Unambiguous language. Defined terms. Understandable by developers. | LLM linguistic analysis |
| **Consistency** | 20% | No internal contradictions. Features aligned with problem statement. | LLM cross-reference |
| **Feasibility** | 20% | Requirements technically achievable within constraints | LLM + Research Agent |
| **Business Alignment** | 15% | Features directly contribute to solving the business problem | LLM alignment check |

## 3.9 Quality Gates

```yaml
pm_quality_gate:
  type: requirements_gate
  minimum_score: 90
  max_iterations: 5
  critical_metrics: [completeness, business_alignment]
  review_process: multi_agent_debate  # 3 reviewers + consensus
  artifacts:
    - PRD
    - User Story set
    - Feature Specifications
    - Development Roadmap
```

## 3.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| Max iterations (5) reached, score < 90 | Escalate to human PM with full iteration history and last best version |
| Completeness < 50 after 3 iterations | Escalate — fundamental structural issue |
| Business alignment < 60 after 3 iterations | Escalate — may indicate wrong product direction |
| Score unchanged for 2 consecutive iterations | Escalate — improvement agent stuck |
| Research Agent returns "no data available" for critical domain | Escalate — domain may be too novel |
| Generated PRD contradicts explicit human constraint | Escalate — agent violating human input |

---

# 4. Research Agent

## 4.1 Purpose

The Research Agent investigates technologies, competitors, and domain knowledge to inform decisions by all other agents. It serves as the internal knowledge analyst.

## 4.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| R1 | **Technology Evaluation** | Compares technologies against structured criteria. Recommends best fit for requirements. |
| R2 | **Competitor Analysis** | Identifies competitors. Analyzes features, pricing, strengths, weaknesses. |
| R3 | **Documentation Retrieval** | Fetches and summarizes documentation for frameworks, APIs, and tools. |
| R4 | **Industry Research** | Investigates industry trends, best practices, and emerging technologies. |
| R5 | **Risk Assessment** | Identifies technical and market risks for proposed solutions. |
| R6 | **Knowledge Synthesis** | Combines multiple sources into coherent, cited research reports. |

## 4.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Research Questions | PM Agent, Architect, Orchestrator | Natural language questions |
| Technology Shortlist | Architect Agent | List of candidate technologies |
| Competitor Names | PM Agent | List of competitors to analyze |
| Domain Context | PM Agent, PRD | Business domain description |
| Constraints | Orchestrator | Budget, timeline, technical constraints |
| Previous Research | Self-Learning Engine | Past research reports for related domains |

## 4.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Research Report | PM, Architect, Human | Structured markdown with citations |
| Technology Recommendation | Architect, Developer | Scored comparison matrix |
| Competitive Matrix | PM, Human | Feature/pricing/strength comparison table |
| Risk Assessment | PM, Orchestrator | Identified risks with severity and likelihood |
| Documentation Summary | Developer | Condensed API/framework documentation |
| Knowledge Graph Updates | Knowledge Agent | Entity-relationship data from research |

## 4.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `WebSearchTool` | Search web for documentation, competitors, trends | Every task |
| `RAGQueryTool` | Query internal knowledge base for past research | Every task |
| `TechnologyEvaluator` | Scored comparison of technologies | Per comparison |
| `CompetitorAnalyzer` | Structured competitive analysis | Per analysis |
| `DocumentationFetcher` | Fetch and parse framework/API docs | On demand |
| `SourceValidator` | Verify citations and fact-check claims | Every output |
| `RiskAssessor` | Structured risk evaluation | Per assessment |

## 4.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (research artifacts) | Yes | Yes | Store research reports |
| Vector DB | Yes | Yes | Query similar research; store research embeddings |
| Knowledge Graph | Yes | Yes | Link technologies to projects, competitors to markets |
| RAG | Yes | Yes | Retrieve and contribute to knowledge base |
| Redis (session) | Yes | Yes | Intermediate analysis state |

## 4.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `artifacts:create` | Assigned project | Create research reports |
| `artifacts:update` | Own artifacts | Update research during improvement |
| `rag:query` | Global | Query internal knowledge |
| `rag:ingest` | Global | Add new findings to knowledge base |
| `web:search` | Global | Search external sources |
| `knowledge_graph:write` | Assigned project | Add research relationships |

## 4.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Source Quality** | 30% | Are sources authoritative? Up-to-date? Diverse (not single source)? | LLM + automated check |
| **Relevance** | 25% | Does the research directly answer the question? No tangential information. | LLM relevance check |
| **Completeness** | 20% | Are all aspects of the question addressed? Gaps identified? | LLM coverage analysis |
| **Objectivity** | 15% | Balanced view? Pros and cons presented? Bias acknowledged? | LLM tone analysis |
| **Actionability** | 10% | Can the consumer act on this research? Clear recommendations? | LLM assessment |

## 4.9 Quality Gates

```yaml
research_quality_gate:
  type: requirements_gate    # Research uses same gate as requirements
  minimum_score: 85          # Slightly lower — research is informational
  max_iterations: 3
  critical_metrics: [source_quality, relevance]
  special_rules:
    - All external claims must have citations
    - Research must include "limitations" section
    - Recommendations must include confidence levels
```

## 4.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| No authoritative sources found for critical technology | Escalate — domain may be too new or niche |
| Conflicting information from equally authoritative sources | Escalate — flag for human judgment |
| Technology recommendation contradicts established company standards | Escalate — policy conflict |
| Research budget (web search tokens) exhausted | Escalate — request budget increase |
| Score < 70 after 2 iterations | Escalate — fundamental quality issue |

---

# 5. Architect Agent

## 5.1 Purpose

The Architect Agent designs the technical blueprint for the system. It translates requirements into a concrete architecture that the Developer Agent can implement.

## 5.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| AR1 | **System Architecture Design** | Designs the overall system topology. Decomposes into services/components. Defines interactions. |
| AR2 | **Service Decomposition** | Applies Domain-Driven Design bounded contexts. Defines service boundaries and responsibilities. |
| AR3 | **API Contract Design** | Designs REST/GraphQL/gRPC APIs. Creates OpenAPI 3.1 specifications. |
| AR4 | **Database Schema Design** | Designs ER diagrams, table structures, indexes, relationships. Generates DDL. |
| AR5 | **Security Architecture** | Designs trust boundaries, auth flows, data encryption patterns, network segmentation. |
| AR6 | **Technology Selection** | Recommends specific technologies based on Research Agent input and requirements. |
| AR7 | **Architecture Decision Records** | Documents every significant architectural decision with context and rationale. |

## 5.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| PRD | PM Agent | Structured product requirements |
| User Stories | PM Agent | User stories with acceptance criteria |
| Feature Specifications | PM Agent | Detailed feature descriptions |
| Research Reports | Research Agent | Technology evaluations, recommendations |
| Technical Constraints | Human, Orchestrator | Must-use technologies, budget limits |
| Non-Functional Requirements | PM Agent | Scalability, availability, performance targets |
| Past Architectures | Self-Learning Engine | Successful patterns from similar projects |

## 5.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Architecture Document | Developer, DevOps, Human | Structured markdown with Mermaid diagrams |
| Service Decomposition Map | Developer | List of services with responsibilities |
| API Contracts (OpenAPI 3.1) | Developer, QA | OpenAPI YAML/JSON |
| ER Diagrams / DDL | Developer | Mermaid ER + SQL DDL |
| Sequence Diagrams | Developer | Mermaid sequence diagrams for key flows |
| Technology Stack Decisions | Developer, DevOps | Documented with rationale |
| ADRs | All, Human | Architecture Decision Records |
| Security Architecture | Security Agent, DevOps | Trust boundary diagrams, auth flows |

## 5.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `RAGQueryTool` | Retrieve architecture patterns, best practices | Every design |
| `ServiceDecomposer` | DDD-based service boundary identification | Per system design |
| `APIContractGenerator` | Generate OpenAPI 3.1 specs | Per service |
| `DBSchemaGenerator` | Generate ER diagrams and DDL | Per data model |
| `MermaidRenderer` | Validate and render Mermaid diagrams | Every diagram |
| `TechnologyMatcher` | Match requirements to technology recommendations | Per technology decision |
| `ADRGenerator` | Generate structured ADRs | Per significant decision |
| `ComplexityAnalyzer` | Analyze architecture for circular dependencies, SPOFs | Every design |

## 5.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (artifacts) | Yes | Yes | Store architecture docs, API specs, ADRs |
| Vector DB | Yes | Yes | Query similar architectures; store design embeddings |
| Knowledge Graph | Yes | Yes | Create service-API-database relationships |
| RAG | Yes | No | Retrieve architectural patterns, framework docs |
| Redis (session) | Yes | Yes | Intermediate design state |

## 5.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `artifacts:create` | Assigned project | Create architecture documents |
| `artifacts:update` | Own artifacts | Update during improvement loop |
| `artifacts:read` | Assigned project | Read requirements, research |
| `rag:query` | Global | Query architecture knowledge base |
| `knowledge_graph:write` | Assigned project | Create architecture relationships |
| `technology:recommend` | Assigned project | Recommend technologies |

## 5.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Scalability** | 25% | Can system handle 10x load? Horizontal scaling designed? Bottlenecks identified? | LLM pattern analysis |
| **Reliability** | 20% | No SPOFs. Redundancy. Failover strategies. Circuit breakers. Retry patterns. | LLM + pattern DB |
| **Security** | 25% | Trust boundaries defined. AuthN/AuthZ architected. Encryption. Principle of least privilege. | LLM + Security Agent review |
| **Maintainability** | 15% | Loose coupling. Clear interfaces. ADRs present. Comprehensible to new developer. | LLM complexity analysis |
| **Cost Efficiency** | 15% | Resource estimates. Managed service preference. Cost model. Serverless consideration. | LLM + cloud pricing data |

## 5.9 Quality Gates

```yaml
architecture_quality_gate:
  type: architecture_gate
  minimum_score: 90
  max_iterations: 5
  critical_metrics: [scalability, reliability, security]
  review_process: multi_agent_debate  # 3 reviewers + consensus
  artifacts:
    - Architecture Document
    - Service Decomposition Map
    - API Contracts
    - ER Diagrams / DDL
    - ADRs (minimum 3 required)
  death_penalties:
    - circular_dependency: caps at 60
    - single_point_of_failure: caps at 70
    - no_authentication_designed: caps at 40
```

## 5.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| Circular dependency detected and not resolved in 2 iterations | Escalate to human architect |
| Max iterations (5) reached, score < 90 | Escalate with architecture doc and iteration history |
| Architecture contradicts requirements (cross-reference failure) | Escalate with both artifacts |
| Security architecture score < 60 after 2 iterations | Escalate — fundamental security design flaw |
| Two reviewer agents strongly disagree (score delta > 30) | Escalate — significant design disagreement |
| Technology recommendation rejected by Security Agent | Escalate — security-vs-features tradeoff |

---

# 6. Developer Agent

## 6.1 Purpose

The Developer Agent writes production-quality source code from architecture specifications and API contracts. It supports backend (Python/FastAPI primary), frontend (React/Next.js), and mobile (Flutter/React Native) generation.

## 6.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| D1 | **Backend Generation** | Generates FastAPI services from OpenAPI specs. Includes models, routes, services, middleware. |
| D2 | **Frontend Generation** | Generates React/Next.js components, pages, API clients, hooks from API contracts. |
| D3 | **Database Integration** | Implements SQLAlchemy models, migrations, queries, connection pooling. |
| D4 | **API Implementation** | Implements endpoints with validation, error handling, auth checks, business logic. |
| D5 | **Code Refactoring** | Refactors code based on critiques. Preserves functionality while improving quality. |
| D6 | **Test-Aware Coding** | Writes code that is inherently testable. Uses dependency injection, pure functions. |
| D7 | **Documentation Generation** | Generates inline docstrings, README files, and API documentation. |

## 6.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| API Contracts (OpenAPI) | Architect Agent | OpenAPI 3.1 YAML/JSON |
| ER Diagrams / DDL | Architect Agent | SQL DDL + Mermaid ER |
| Architecture Document | Architect Agent | Service decomposition, patterns, decisions |
| Technology Stack | Architect Agent | Specific frameworks, libraries, versions |
| User Stories | PM Agent | Stories with acceptance criteria |
| Code Critiques | Reviewer Agents, Quality Gate | Specific issues to fix |
| Existing Code (for refactoring) | Self (previous iteration) | Source files |

## 6.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Source Code (Backend) | QA, Security, DevOps | Python files (.py) with type hints |
| Source Code (Frontend) | QA, Security | TypeScript/TSX files |
| Database Migrations | DevOps | Alembic migration files |
| Requirements Files | DevOps | requirements.txt / pyproject.toml |
| Dockerfile | DevOps | Multi-stage Dockerfile |
| API Documentation | Human | Auto-generated from docstrings |
| Refactored Code | QA, Security | Updated source files with changelog |

## 6.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `CodeGenerationTool` | LLM-powered code generation with framework awareness | Every task |
| `StaticAnalysisTool` | Run ruff, mypy, radon on generated code | After every generation |
| `TestRunnerTool` | Run existing tests to verify no regressions | After refactoring |
| `RAGQueryTool` | Retrieve framework docs, coding patterns | For unfamiliar patterns |
| `GitOpsTool` | Stage, commit generated code | Per generation batch |
| `ImportResolver` | Verify all imports resolve correctly | After generation |
| `ASTAnalyzer` | Analyze code structure for patterns | After generation |

## 6.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (code artifacts) | Yes | Yes | Store generated code and versions |
| Vector DB | Yes | Yes | Query similar code patterns; store code embeddings |
| Knowledge Graph | Yes | Yes | Link code to APIs, databases, requirements |
| Redis (session) | Yes | Yes | Active code generation state |
| RAG | Yes | No | Retrieve framework patterns, API docs |

## 6.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `artifacts:create` | Assigned project | Create code artifacts |
| `artifacts:update` | Own artifacts | Update code during improvement |
| `artifacts:read` | Assigned project | Read architecture, API specs |
| `code:execute` | Sandbox only | Run code in sandbox for validation |
| `git:write` | Project repo | Stage and commit code |
| `rag:query` | Global | Query code patterns, docs |

## 6.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Complexity** | 20% | Cyclomatic complexity, nesting depth, function length. Via radon. | radon (automated) |
| **Maintainability** | 20% | Maintainability index, readability, docstrings, naming, consistency. | radon + LLM |
| **Testability** | 20% | DI patterns, pure functions, separation of concerns, mockability. | LLM structural review |
| **Performance** | 20% | No N+1 queries, proper indexing, async where appropriate, caching. | LLM + AST analysis |
| **Security** | 20% | Input validation, parameterized queries, auth on all endpoints, no secrets. | bandit + LLM |

## 6.9 Quality Gates

```yaml
code_quality_gate:
  type: code_gate
  minimum_score: 92
  max_iterations: 7
  critical_metrics: [testability, security]
  review_process: automated_first + debate_if_borderline
  automated_checks:
    - ruff: zero errors
    - mypy: strict mode, zero errors
    - radon: no F-ranked functions
    - bandit: no HIGH or CRITICAL findings
    - imports_resolve: all imports valid
  artifacts:
    - All generated .py files
    - All generated .tsx files
    - Database migrations
```

## 6.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| Code fails to import/compile after 2 iterations | Escalate — likely architectural issue, not code issue |
| bandit CRITICAL finding persists after 2 iterations | Escalate — may need architecture change |
| Max iterations (7) reached, score < 92 | Escalate with code and full critique history |
| Score decreases 2 iterations in a row | Escalate — getting worse |
| Performance score < 30 (algorithmic issue) | Escalate — may need architecture-level optimization |
| Generated code significantly deviates from API contract | Escalate — agent misunderstanding the spec |

---

# 7. QA Agent

## 7.1 Purpose

The QA Agent ensures that all generated code is thoroughly tested. It writes unit, integration, and E2E tests, analyzes coverage, runs mutation testing, and detects flaky tests.

## 7.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| Q1 | **Unit Test Generation** | Generates pytest unit tests for every function/method. Covers happy path, errors, edges. |
| Q2 | **Integration Test Generation** | Generates integration tests for API endpoints. Uses TestClient, test databases. |
| Q3 | **E2E Test Generation** | Generates Playwright/Cypress E2E tests for critical user flows. |
| Q4 | **Coverage Analysis** | Runs coverage.py. Identifies uncovered code. Generates tests to fill gaps. |
| Q5 | **Mutation Testing** | Runs mutmut. Identifies surviving mutants. Strengthens assertions. |
| Q6 | **Flakiness Detection** | Runs tests N times. Identifies non-deterministic tests. Fixes or flags. |
| Q7 | **Test Quality Review** | Reviews tests for: meaningful assertions, proper mocking, test isolation, readability. |

## 7.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Source Code | Developer Agent | Python/TypeScript files |
| API Contracts | Architect Agent | OpenAPI 3.1 specs |
| User Stories | PM Agent | Stories with acceptance criteria |
| Requirements | PM Agent | PRD with success criteria |
| Coverage Reports | coverage.py | XML/JSON coverage data |
| Mutation Reports | mutmut | Surviving mutant list |
| Previous Tests | Self (previous iteration) | Test files |

## 7.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Unit Tests | Developer, Scoring Engine | pytest files (test_*.py) |
| Integration Tests | Developer, DevOps | pytest files with TestClient |
| E2E Tests | DevOps (CI/CD) | Playwright .spec.ts files |
| Coverage Report | Quality Gate, Human | Coverage percentage + uncovered lines |
| Mutation Score Report | Quality Gate | % killed + surviving mutants |
| Flakiness Report | Developer, Human | List of flaky tests with failure rate |
| Test Quality Assessment | Quality Gate | Structured evaluation |

## 7.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `TestGeneratorTool` | LLM-powered test generation from source code | Every task |
| `TestRunnerTool` | Execute pytest with coverage | After every generation |
| `CoverageAnalyzer` | Parse coverage.xml, identify gaps | After every run |
| `MutationRunner` | Execute mutmut, analyze surviving mutants | Per test suite |
| `FlakinessDetector` | Run tests N times, detect non-determinism | Per test suite |
| `PlaywrightRunner` | Execute E2E tests | After E2E generation |
| `RAGQueryTool` | Retrieve testing patterns and best practices | For complex scenarios |

## 7.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (test artifacts) | Yes | Yes | Store test files and reports |
| Vector DB | Yes | Yes | Query similar test patterns; store test embeddings |
| Knowledge Graph | Yes | Yes | Link tests to code, requirements, bugs |
| Redis (session) | Yes | Yes | Active test generation state |
| RAG | Yes | No | Retrieve testing patterns |

## 7.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `artifacts:create` | Assigned project | Create test artifacts |
| `artifacts:update` | Own artifacts | Update tests during improvement |
| `artifacts:read` | Assigned project | Read source code, API specs, requirements |
| `code:execute` | Sandbox only | Run tests in sandbox |
| `rag:query` | Global | Query testing patterns |

## 7.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Coverage** | 30% | Line, branch, function coverage %. | coverage.py (automated) |
| **Mutation Score** | 30% | % of mutants killed. Weak tests = surviving mutants. | mutmut (automated) |
| **Reliability** | 20% | Tests pass deterministically. No flakiness. Isolated fixtures. | pytest repeat + LLM |
| **Edge Case Coverage** | 20% | Tests for null, empty, boundary, error paths, race conditions. | LLM review |

## 7.9 Quality Gates

```yaml
testing_quality_gate:
  type: testing_gate
  minimum_score: 95
  max_iterations: 5
  critical_metrics: [coverage, mutation_score, reliability]
  automated_checks:
    - coverage_line >= 90%
    - coverage_branch >= 80%
    - mutation_score >= 80%
    - flaky_test_count == 0
    - all_tests_pass: true
  artifacts:
    - Unit test files
    - Integration test files
    - E2E test files
    - Coverage report
    - Mutation score report
```

## 7.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| Tests crash (interpreter error, not assertion failure) | Escalate immediately — code or environment issue |
| Coverage decreases from previous iteration | Escalate — regression in test quality |
| 3+ flaky tests detected | Escalate — test reliability crisis |
| Mutation score < 30 after 2 iterations | Escalate — fundamental test weakness |
| Max iterations (5) reached, score < 95 | Escalate with test suite and coverage report |
| Tests pass but mutation testing reveals all assertions are trivial | Escalate — tests exist but provide no real validation |

---

# 8. Security Agent

## 8.1 Purpose

The Security Agent audits all code and configurations for vulnerabilities. It is the final gatekeeper before any code reaches production. Security findings can halt deployment entirely.

## 8.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| S1 | **Vulnerability Detection** | Runs SAST tools (bandit). Identifies OWASP Top 10 vulnerabilities. |
| S2 | **Secret Scanning** | Scans all files for hardcoded secrets, tokens, keys, passwords. |
| S3 | **Dependency Auditing** | Checks all dependencies for known CVEs. Flags unmaintained packages. |
| S4 | **LLM-Powered Security Review** | Deep review of code for logic flaws, race conditions, auth bypass, insecure defaults. |
| S5 | **Penetration Testing** | Automated pen-testing against staging environment (OWASP ZAP). |
| S6 | **Compliance Checking** | Checks against OWASP Top 10, basic GDPR/PII handling patterns. |
| S7 | **Security Report Generation** | Produces comprehensive security assessment with risk ratings. |

## 8.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Source Code | Developer Agent | All code files |
| Dependencies | Developer Agent | requirements.txt, package.json |
| Deployment Config | DevOps Agent | Dockerfiles, K8s manifests |
| Architecture Document | Architect Agent | Security architecture section |
| API Contracts | Architect Agent | OpenAPI specs to check auth |
| Staging Environment URL | DevOps Agent | URL for pen-testing |
| Past Security Reports | Self-Learning Engine | Historical vulnerabilities and fixes |

## 8.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Vulnerability Report | Developer, Quality Gate | Structured findings with severity |
| Secret Scan Report | Developer, Human | List of detected secrets with locations |
| Dependency Audit Report | Developer, DevOps | CVE list with fix versions |
| Security Assessment | Human, Orchestrator | Comprehensive security report |
| Pen-Test Results | DevOps, Human | ZAP scan results |
| Compliance Report | Human | OWASP/GDPR compliance status |
| Fix Recommendations | Developer | Specific code changes to fix each finding |

## 8.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `SecurityScannerTool` | bandit SAST + safety dependency check | Every scan |
| `SecretScannerTool` | detect-secrets + entropy analysis + regex | Every scan |
| `DependencyAuditor` | safety + pip-audit | Every scan |
| `PenetrationTester` | OWASP ZAP automated scan | Per staging deploy |
| `LLMSecurityReviewer` | Deep code review for logic flaws | Every review |
| `ComplianceChecker` | OWASP/GDPR pattern matching | Per review |
| `RAGQueryTool` | Retrieve CVE details, fix patterns | For findings |

## 8.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (security artifacts) | Yes | Yes | Store security reports |
| Vector DB | Yes | Yes | Query similar vulnerability patterns |
| Knowledge Graph | Yes | Yes | Link vulnerabilities to code, fixes, CVEs |
| Redis (session) | Yes | Yes | Active scan state |
| RAG | Yes | No | Retrieve CVE details and fix patterns |

## 8.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `artifacts:create` | Assigned project | Create security reports |
| `artifacts:read` | All projects | Read any code for security audit |
| `code:execute` | Sandbox only | Run security scanners |
| `deployment:block` | All projects | Can halt deployment pipeline |
| `secrets:alert` | Global | Can trigger secret rotation alerts |
| `rag:query` | Global | Query security knowledge base |

## 8.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Vulnerability Scan** | 35% | Count and severity of bandit findings. | bandit (automated) |
| **LLM Security Review** | 25% | Logic flaws, race conditions, auth bypass, insecure defaults. | LLM deep review |
| **Secret Detection** | 20% | Zero secrets policy. Any secret = critical failure. | detect-secrets + regex |
| **Dependency Audit** | 10% | Known CVEs in dependencies. | safety (automated) |
| **Compliance Check** | 10% | OWASP Top 10, basic GDPR. | LLM compliance review |

## 8.9 Quality Gates

```yaml
security_quality_gate:
  type: security_gate
  minimum_score: 98
  max_iterations: 3
  critical_metrics: [vulnerability_scan, llm_security_review, secret_detection]
  halt_immediately:
    - Any CRITICAL CVE found
    - Any secret detected
    - Auth bypass possible
    - SQL injection vector found
  automated_checks:
    - bandit: zero HIGH, zero CRITICAL
    - safety: zero CRITICAL CVEs
    - detect-secrets: zero findings
  artifacts:
    - Vulnerability Report
    - Secret Scan Report
    - Dependency Audit Report
    - Security Assessment
```

## 8.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| Critical CVE found | Halt immediately. Escalate. Do not loop. |
| Secret found in code | Halt immediately. Escalate. Trigger credential rotation. |
| Auth bypass discovered | Halt immediately. Escalate. Architecture-level security flaw. |
| Zero-day exploit pattern detected | Escalate to security team with highest priority. |
| 3+ HIGH bandit findings persist after 2 iterations | Escalate — systemic security issue. |
| Security score < 40 on first evaluation | Escalate — code is fundamentally insecure. |

---

# 9. DevOps Agent

## 9.1 Purpose

The DevOps Agent containerizes, deploys, and orchestrates the infrastructure for all generated applications. It builds CI/CD pipelines and manages the full deployment lifecycle.

## 9.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| DO1 | **Containerization** | Generates multi-stage Dockerfiles per service. Optimizes for size and caching. |
| DO2 | **Kubernetes Manifests** | Generates Deployment, Service, ConfigMap, Secret, HPA, PDB, Ingress manifests. |
| DO3 | **Infrastructure as Code** | Generates Terraform for cloud infrastructure (DBs, clusters, networking). |
| DO4 | **CI/CD Pipeline Generation** | Generates GitHub Actions workflows for CI, staging deploy, production deploy. |
| DO5 | **Deployment Execution** | Applies K8s manifests. Monitors rollout. Verifies health. Runs smoke tests. |
| DO6 | **Canary & Blue-Green Deployments** | Implements progressive delivery strategies with automated rollback. |
| DO7 | **Secret Management** | Integrates with Vault. Ensures no secrets in plaintext configs. |

## 9.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Source Code | Developer Agent | Application code files |
| Architecture Document | Architect Agent | Service topology, dependencies |
| API Contracts | Architect Agent | Endpoints, ports |
| ER Diagrams | Architect Agent | Database requirements |
| Dockerfiles | Self/Developer Agent | Container definitions |
| Test Results | QA Agent | All tests passing |
| Security Approval | Security Agent | Security gate passed |

## 9.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Dockerfiles | Container Registry | Multi-stage Dockerfiles |
| Kubernetes Manifests | K8s Cluster | YAML manifests |
| Terraform Plans | Cloud Provider | HCL files |
| CI/CD Workflows | GitHub Actions | YAML workflow files |
| Deployment Reports | Orchestrator, Human | Deployment status, timings |
| Helm Charts | K8s Cluster | Helm chart packages |
| Rollback Plans | Self-Healing, Human | Rollback procedures |

## 9.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `DockerOpsTool` | Build, tag, push Docker images | Every deployment |
| `KubernetesDeployer` | Apply manifests, watch rollout, verify | Every deployment |
| `TerraformRunner` | Terraform plan, validate, apply | Infra changes |
| `HelmManager` | Package and deploy Helm charts | Per service |
| `CanaryController` | Traffic splitting, gradual promotion | Production deploys |
| `SecretManager` | Vault integration, secret injection | Every deployment |
| `SmokeTestRunner` | Run basic health checks post-deploy | After every deploy |
| `RAGQueryTool` | Retrieve infrastructure patterns | For unfamiliar setups |

## 9.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (deployment artifacts) | Yes | Yes | Store deployment configs, history |
| Vector DB | Yes | Yes | Query similar infra patterns |
| Knowledge Graph | Yes | Yes | Link deployments to services, projects |
| Redis (session) | Yes | Yes | Active deployment state |
| Secret Store (Vault) | Yes | Yes | Inject secrets; never store in plaintext |

## 9.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `artifacts:create` | Assigned project | Create deployment configurations |
| `artifacts:read` | Assigned project | Read code, architecture, tests |
| `deployment:execute` | Staging + Production | Deploy to environments |
| `deployment:rollback` | Staging + Production | Trigger rollbacks |
| `infrastructure:provision` | Cloud accounts | Terraform apply |
| `secrets:read` | Vault | Read secrets for injection |
| `registry:write` | Container registry | Push Docker images |
| `kubernetes:manage` | Cluster | Apply and manage K8s resources |

## 9.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **Stability** | 40% | Error rate post-deploy, crash loops, OOM kills, pod restarts. | Prometheus metrics |
| **Availability** | 35% | Health check success rate. All endpoints reachable. Uptime. | Prometheus blackbox exporter |
| **Performance** | 25% | P50/P95/P99 latency vs baseline. Throughput. | Prometheus histograms |

## 9.9 Quality Gates

```yaml
devops_quality_gate:
  type: deployment_gate
  minimum_score: 95
  max_iterations: 3
  observation_window: 300s      # 5 minutes
  canary_traffic_percent: 10    # Start at 10%
  promote_after_stable: 600s    # 10 minutes
  critical_metrics: [stability, availability]
  auto_rollback:
    - error_rate > 10%
    - availability < 50%
    - p95_latency > 3x baseline
    - any OOM kill
    - any crash loop
  artifacts:
    - Deployment status report
    - Canary analysis report
```

## 9.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| Auto-rollback triggered | Rollback immediately. Create incident. Escalate to SRE + Self-Healing. |
| 3 sequential rollbacks for same service | Escalate. Lock service from auto-deployment. |
| Docker build fails 2x consecutively | Escalate — likely code or Dockerfile issue. |
| Terraform plan shows destructive changes | Escalate — requires human approval. |
| Infrastructure cost estimate exceeds budget by > 30% | Escalate to project owner. |
| Deployment to production blocked by Security Gate | Escalate — security-vs-delivery tradeoff. |

---

# 10. Monitoring Agent

## 10.1 Purpose

The Monitoring Agent watches production systems, detects anomalies, generates alerts, and provides operational insights. It is the eyes and ears of the autonomous system.

## 10.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| M1 | **Performance Monitoring** | Tracks latency, throughput, error rate, resource usage across all services. |
| M2 | **Anomaly Detection** | Statistical anomaly detection on key metrics. Identifies deviations from baseline. |
| M3 | **Alert Generation** | Creates structured alerts with severity, context, and suggested actions. |
| M4 | **Log Analysis** | Queries ELK for error patterns. Correlates with metrics anomalies. |
| M5 | **Dashboard Maintenance** | Updates Grafana dashboards. Adds new panels for new services. |
| M6 | **Trend Analysis** | Identifies long-term trends. Predicts capacity needs. Flags degrading services. |
| M7 | **Health Reporting** | Provides system-wide health status. Cascading dependency health. |

## 10.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Prometheus Metrics | All services | Time-series metrics |
| Application Logs | ELK Stack | Structured JSON logs |
| OpenTelemetry Traces | All services | Distributed traces |
| Deployment Events | DevOps Agent | Deployment started/completed/rolled back |
| Alert History | Self | Past alerts and resolutions |
| Service Topology | Architect Agent, Knowledge Graph | Service dependency map |

## 10.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Metric Anomaly Alerts | Self-Healing, Human, UI | Structured alert with context |
| System Health Report | UI, Human | Aggregated health status |
| Performance Reports | Human, Self-Learning | Daily/weekly performance summaries |
| Capacity Forecasts | DevOps, Human | Predicted resource needs |
| Alert Feed | WebSocket Gateway, UI | Real-time alert stream |
| Incident Triggers | Self-Healing Agent | `FailureDetected` events |

## 10.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `PrometheusQuerier` | Query Prometheus for metrics | Every 30s |
| `AnomalyDetector` | Statistical anomaly detection (3-sigma, moving average) | Every 30s |
| `LogAnalyzer` | Query ELK, correlate with metrics | On alert |
| `AlertGenerator` | Create and route structured alerts | On anomaly |
| `GrafanaManager` | Update dashboard panels, add new services | Per deployment |
| `TrendAnalyzer` | Long-term trend analysis and forecasting | Hourly/daily |
| `DependencyHealthChecker` | Cascading health check across service graph | Every 30s |

## 10.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (alert history) | No | Yes | Store alert records |
| Redis (alert state) | Yes | Yes | Active alert deduplication |
| Prometheus | Yes | No | Query metrics |
| ELK | Yes | No | Query logs |
| Knowledge Graph | Yes | No | Service dependency mapping |
| RAG | Yes | No | Retrieve past incident patterns |

## 10.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `metrics:read` | All services | Query Prometheus metrics |
| `logs:read` | All services | Query ELK logs |
| `alerts:create` | Global | Generate alerts |
| `alerts:route` | Global | Route alerts to Self-Healing or human |
| `dashboards:manage` | Grafana | Update dashboards |
| `incidents:create` | Global | Create incident records |

## 10.8 Evaluation Metrics

The Monitoring Agent is not subject to the recursive quality loop directly. Instead, it is measured on operational KPIs:

| KPI | Target | Description |
|-----|--------|-------------|
| **Detection Time** | < 30s | Time from incident start to anomaly detection |
| **False Positive Rate** | < 5% | Alerts that do not correspond to real issues |
| **False Negative Rate** | < 1% | Real issues that were not detected |
| **Alert Signal-to-Noise** | > 80% | Alerts that lead to action vs. informational |
| **Mean Time to Detect (MTTD)** | < 60s | Average time to detect production issues |

## 10.9 Quality Gates

```yaml
monitoring_quality_gate:
  type: operational
  evaluation: continuous
  alerts:
    no_data_alert:
      condition: "No metrics received from any service for > 60s"
      severity: CRITICAL
    high_error_rate:
      condition: "5xx rate > 1% for > 2 minutes"
      severity: HIGH
    latency_spike:
      condition: "P95 latency > 3x baseline for > 5 minutes"
      severity: MEDIUM
    resource_exhaustion:
      condition: "CPU/Memory > 90% for > 5 minutes"
      severity: HIGH
    disk_full:
      condition: "Disk usage > 85%"
      severity: CRITICAL
```

## 10.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| CRITICAL alert persists > 5 minutes without resolution | Escalate to human SRE |
| Same alert fires > 10 times in 1 hour (alert storm) | Escalate — deduplication failure or cascading failure |
| All services in a project go unhealthy simultaneously | Escalate — infrastructure-level failure |
| Prometheus or ELK becomes unavailable | Escalate — observability blind spot |
| Anomaly detection model confidence drops below threshold | Escalate — may need retraining or reconfiguration |

---

# 11. Self-Healing Agent

## 11.1 Purpose

The Self-Healing Agent autonomously detects, diagnoses, and repairs production failures. It closes the loop from monitoring to recovery without human intervention for known failure patterns.

## 11.2 Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| H1 | **Failure Detection** | Subscribes to `AlertTriggered` and `FailureDetected` events from Monitoring. |
| H2 | **Root Cause Analysis** | Gathers logs, metrics, traces around failure time. Queries knowledge graph for similar past incidents. Uses LLM to hypothesize root cause. |
| H3 | **Patch Generation** | Generates code fix for the root cause. Includes regression test. Creates rollback plan. |
| H4 | **Patch Validation** | Runs full test suite against patch. Runs security scan. Verifies fix resolves the issue. |
| H5 | **Autonomous Deployment** | Deploys patch via canary. Monitors for 10 minutes. Promotes if stable. Rolls back if degraded. |
| H6 | **Incident Documentation** | Records full incident lifecycle. RCA, patch, validation results, deployment outcome. Feeds Self-Learning. |
| H7 | **Pattern Recognition** | Identifies recurring failure patterns across incidents. Suggests preventive measures. |

## 11.3 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Alerts | Monitoring Agent | `AlertTriggered` events with context |
| Failure Events | Monitoring Agent | `FailureDetected` events |
| Application Logs | ELK Stack | Structured logs around failure time |
| Metrics | Prometheus | Time-series around failure |
| Traces | OpenTelemetry | Distributed traces of failing requests |
| Similar Incidents | Knowledge Graph | Past incidents with same signature |
| Service Topology | Knowledge Graph | Dependency map |
| Source Code | Developer Agent | Code for affected service |

## 11.4 Outputs

| Output | Consumer | Format |
|--------|----------|--------|
| Root Cause Analysis | Human, Self-Learning | Structured RCA with confidence score |
| Code Patch | QA, DevOps | Git diff with explanation |
| Regression Test | QA | Test that reproduces and verifies fix |
| Rollback Plan | DevOps | Step-by-step rollback procedure |
| Deployment Report | Human, Self-Learning | Patch deployment outcome |
| Incident Record | Knowledge Graph, Self-Learning | Full incident lifecycle |
| Preventive Recommendations | Human, Developer | Suggestions to prevent recurrence |

## 11.5 Tools

| Tool | Purpose | Usage Frequency |
|------|---------|-----------------|
| `RCAAnalyzer` | LLM-powered RCA using logs, metrics, traces | Every incident |
| `PatchGenerator` | LLM-powered code fix generation | After RCA |
| `TestValidator` | Run full test suite against patch | Every patch |
| `SecurityValidator` | Run bandit + secret scan on patch | Every patch |
| `CanaryDeployer` | Deploy patch to canary, monitor, promote/rollback | Every validated patch |
| `IncidentRecorder` | Document full incident lifecycle | Every incident |
| `PatternRecognizer` | Identify recurring failure patterns | Across incidents |
| `GitOpsTool` | Create PR with patch | Every patch |
| `RAGQueryTool` | Retrieve similar incidents and fixes | For RCA |

## 11.6 Memory Access

| Memory Tier | Read | Write | Purpose |
|-------------|:----:|:-----:|---------|
| PostgreSQL (incidents) | Yes | Yes | Store incident records, RCAs, patches |
| Vector DB | Yes | Yes | Query similar incidents; store incident embeddings |
| Knowledge Graph | Yes | Yes | Link incidents to services, root causes, fixes |
| Redis (session) | Yes | Yes | Active incident state |
| ELK | Yes | No | Query logs for RCA |
| Prometheus | Yes | No | Query metrics for RCA |
| RAG | Yes | No | Retrieve fix patterns |

## 11.7 Permissions

| Permission | Scope | Description |
|------------|-------|-------------|
| `incidents:manage` | All projects | Create, update, resolve incidents |
| `code:read` | All projects | Read any code for RCA |
| `code:write` | Sandbox + PR | Generate patches (PR only, not direct push) |
| `deployment:execute` | Staging only | Deploy patches to staging for validation |
| `deployment:canary` | Production | Canary deploy validated patches |
| `deployment:rollback` | Production | Rollback if patch degrades |
| `logs:read` | All services | Query logs for RCA |
| `metrics:read` | All services | Query metrics for RCA |

## 11.8 Evaluation Metrics

| Metric | Weight | Description | Evaluator |
|--------|--------|-------------|-----------|
| **RCA Accuracy** | 30% | Was the root cause correctly identified? (Human-verified post-hoc) | Human audit |
| **Patch Success Rate** | 30% | % of deployed patches that resolve the incident without causing regression | Automated (metrics post-patch) |
| **Mean Time to Recovery (MTTR)** | 20% | Time from incident detected to patch deployed and verified | Automated (event timestamps) |
| **False Fix Rate** | 10% | % of patches that did not resolve the incident (needed 2+ attempts) | Automated |
| **Regression Rate** | 10% | % of patches that introduced new issues | Automated (monitoring post-patch) |

## 11.9 Quality Gates

```yaml
self_healing_quality_gate:
  type: operational
  patch_validation_requirements:
    - All existing tests must pass
    - New regression test must pass
    - Security scan: zero new HIGH/CRITICAL findings
    - Coverage must not decrease
    - Patch must be reviewed by QA Agent
  canary_criteria:
    - Error rate == 0 for 5 minutes
    - P95 latency within 20% of baseline
    - Health checks: 100% pass
  confidence_requirements:
    - auto_deploy: confidence >= 90% and severity <= MEDIUM
    - human_approval_required: confidence < 90% or severity == HIGH
    - escalation_required: confidence < 50% or severity == CRITICAL
```

## 11.10 Escalation Rules

| Condition | Action |
|-----------|--------|
| RCA confidence < 50% | Escalate — cannot determine root cause with confidence |
| Patch validation fails 2 consecutive attempts | Escalate — unable to produce valid fix |
| Patch rolled back from production | Escalate — fix caused regression |
| Same incident recurs within 24 hours of patch | Escalate — fix did not address root cause |
| CRITICAL severity incident | Escalate immediately (do not attempt auto-fix) |
| Incident affects data integrity (DB corruption, data loss) | Escalate immediately — data recovery may be required |
| Fix requires architecture-level change | Escalate — beyond scope of patching |
| 3+ independent services affected simultaneously | Escalate — likely infrastructure or cascading failure |

---

# 12. Cross-Agent Matrix

## 12.1 Agent Interaction Map

```
                    Orchestrator
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    Product Mgr ──► Research ◄────── Architect
         │               │               │
         │               └───────┬───────┘
         │                       │
         ▼                       ▼
      [Requirements]      [Architecture]
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
                Developer
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
        QA        Security     DevOps
         │           │           │
         └───────────┼───────────┘
                     │
                     ▼
               [Deployment]
                     │
                     ▼
                Monitoring
                     │
                     ▼
               Self-Healing
```

## 12.2 Agent Dependency Matrix

| Consumer \ Producer | Orch | PM | Research | Architect | Developer | QA | Security | DevOps | Monitor | Healer |
|--------------------|:----:|:--:|:--------:|:---------:|:---------:|:--:|:--------:|:------:|:-------:|:------:|
| **Orchestrator** | — | G,R | G,R | G,R | G,R | G,R | G,R | G,R | G,R | G,R |
| **PM** | T,R | — | R | | | | | | | |
| **Research** | T,R | R | — | R | | | | | | |
| **Architect** | T,R | R | R | — | | | | | | |
| **Developer** | T,R | R | | R | — | R | R | | | |
| **QA** | T,R | R | | R | R | — | | | | |
| **Security** | T,R | | | R | R | | — | R | | R |
| **DevOps** | T,R | | | R | R | R | R | — | R | R |
| **Monitor** | T,R | | | | | | | R | — | |
| **Self-Healing** | T,R | | | | R | R | R | R | R | — |

**Legend**: T = Tasked by, R = Reads output from, G = Governed by

## 12.3 Information Flow

```
Phase 1: Requirements
  PM ──PRD──► Architect
  PM ──Stories──► Architect, Developer
  Research ──Report──► PM, Architect

Phase 2: Architecture
  Architect ──API Specs──► Developer, QA
  Architect ──ERD──► Developer
  Architect ──Tech Stack──► Developer, DevOps

Phase 3: Development
  Developer ──Code──► QA, Security, DevOps
  QA ──Tests──► Developer, DevOps
  Security ──Report──► Developer, DevOps

Phase 4: Deployment
  DevOps ──Deployment──► Monitor
  Monitor ──Alerts──► Self-Healing

Phase 5: Recovery
  Self-Healing ──Patch──► QA, DevOps
  Self-Healing ──RCA──► Knowledge Graph, Learning
```

## 12.4 Quality Gate Responsibility Matrix

| Gate | Evaluated By | Agents Involved in Loop | Reviewers |
|------|-------------|------------------------|-----------|
| Requirements | Scoring Engine | PM, Improvement | 3 Reviewer Agents + Consensus |
| Architecture | Scoring Engine | Architect, Improvement | 3 Reviewer Agents + Consensus |
| Code | Scoring Engine | Developer, Improvement | Automated first, debate if borderline |
| Testing | Scoring Engine | QA, Improvement | Automated metrics + 1 LLM review |
| Security | Scoring Engine | Security + Developer | Automated (bandit, safety) + LLM |
| Deployment | Scoring Engine + Prometheus | DevOps, Improvement | Automated metrics from Prometheus |

## 12.5 Escalation Routing Table

| Escalation Source | Target Human Role | Priority | SLA |
|-------------------|-------------------|----------|-----|
| Orchestrator — Deadlock | Project Manager / Architect | HIGH | 4 hours |
| Orchestrator — Budget Exceeded | Project Owner | LOW | 24 hours |
| PM — Requirements Gate Failed | Product Manager | HIGH | 4 hours |
| Research — No Sources Found | Domain Expert | MEDIUM | 8 hours |
| Architect — Architecture Gate Failed | Architect / Tech Lead | HIGH | 4 hours |
| Developer — Code Gate Failed | Senior Developer | MEDIUM | 4 hours |
| QA — Testing Gate Failed | QA Lead | MEDIUM | 4 hours |
| Security — Critical CVE | Security Team | CRITICAL | 30 minutes |
| Security — Secret Found | Security Team + On-call | CRITICAL | 15 minutes |
| DevOps — Auto-rollback | SRE / DevOps | CRITICAL | 15 minutes |
| Monitor — CRITICAL Alert | SRE / On-call | CRITICAL | 5 minutes |
| Self-Healing — RCA Confidence < 50% | Senior Developer + SRE | HIGH | 1 hour |
| Self-Healing — Patch Rolled Back | Senior Developer + SRE | HIGH | 1 hour |

## 12.6 Tool Access Matrix

| Tool | PM | Research | Architect | Developer | QA | Security | DevOps | Monitor | Healer |
|------|:--:|:--------:|:---------:|:---------:|:--:|:--------:|:------:|:-------:|:------:|
| RAGQueryTool | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| WebSearchTool | Yes | Yes | | | | | | | |
| CodeGenerationTool | | | | Yes | Yes | | | | Yes |
| StaticAnalysisTool | | | | Yes | | Yes | | | |
| TestRunnerTool | | | | Yes | Yes | | | Yes | Yes |
| SecurityScannerTool | | | | | | Yes | | | Yes |
| GitOpsTool | | | | Yes | | | Yes | | Yes |
| DockerOpsTool | | | | | | | Yes | | |
| K8sDeployer | | | | | | | Yes | | Yes |
| PrometheusQuerier | | | | | | | | Yes | Yes |
| LogAnalyzer | | | | | | | | Yes | Yes |
| AnomalyDetector | | | | | | | | Yes | |
| RCAAnalyzer | | | | | | | | | Yes |
| PatchGenerator | | | | | | | | | Yes |

---

*End of Agent Design Specification*
