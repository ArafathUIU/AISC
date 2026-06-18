# AISC — Recursive Quality Engine Specification

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0
**Status**: Complete Specification

---

# Table of Contents

1. [Overview](#1-overview)
2. [Artifact Taxonomy](#2-artifact-taxonomy)
3. [Requirements Quality Gate](#3-requirements-quality-gate)
4. [Architecture Quality Gate](#4-architecture-quality-gate)
5. [Code Quality Gate](#5-code-quality-gate)
6. [Testing Quality Gate](#6-testing-quality-gate)
7. [Security Quality Gate](#7-security-quality-gate)
8. [Deployment Quality Gate](#8-deployment-quality-gate)
9. [Scoring Engine Algorithm](#9-scoring-engine-algorithm)
10. [Loop Controller](#10-loop-controller)
11. [Escalation System](#11-escalation-system)
12. [Improvement Strategies](#12-improvement-strategies)
13. [Gate Fusion Matrix](#13-gate-fusion-matrix)
14. [Full Specification Tables](#14-full-specification-tables)

---

# 1. Overview

The Recursive Quality Engine (RQE) is the central nervous system of AISC. Every artifact — regardless of type — must pass through a Generate -> Review -> Critique -> Improve -> Evaluate -> Score cycle until its aggregate quality score meets or exceeds a predefined threshold.

If the threshold is not met, the artifact loops back for improvement. If the maximum iteration count is reached without passing, the artifact is escalated for human intervention.

This document defines every metric, formula, threshold, and behavior of the RQE.

---

# 2. Artifact Taxonomy

| Artifact Type | Produced By | Consumed By | Gate |
|---------------|-------------|-------------|------|
| PRD | PM Agent | Architect, Research, Orchestrator | Requirements Gate |
| User Stories | PM Agent | Architect, Developer, QA | Requirements Gate |
| Feature Specifications | PM Agent | Architect, Developer | Requirements Gate |
| Architecture Document | Architect Agent | Developer, DevOps, Security | Architecture Gate |
| API Contracts (OpenAPI) | Architect Agent | Developer, QA | Architecture Gate |
| ER Diagrams / DDL | Architect Agent | Developer | Architecture Gate |
| Source Code (Backend) | Developer Agent | QA, Security, DevOps | Code Gate |
| Source Code (Frontend) | Developer Agent | QA, Security, DevOps | Code Gate |
| Unit Tests | QA Agent | Developer, Scoring Engine | Testing Gate |
| Integration Tests | QA Agent | DevOps | Testing Gate |
| E2E Tests | QA Agent | DevOps | Testing Gate |
| Security Report | Security Agent | Developer, DevOps | Security Gate |
| Deployment Config | DevOps Agent | Orchestrator, Monitor | Deployment Gate |
| Running Deployment | DevOps Agent | Monitor, Self-Healing | Deployment Gate |
| Research Report | Research Agent | PM, Architect | Requirements Gate |
| Bug Fix / Patch | Self-Healing Agent | QA, DevOps | Code Gate + Testing Gate |

---

# 3. Requirements Quality Gate

## 3.1 Metrics

| # | Metric | Weight | Description | Evaluator |
|---|--------|--------|-------------|-----------|
| R1 | **Completeness** | 25% | Are all required sections present and filled? (Problem Statement, Target Users, Success Metrics, Features, Constraints, Assumptions, Dependencies) | Structural check + LLM |
| R2 | **Clarity** | 20% | Is the language unambiguous? Are terms defined? Can a developer understand without clarification? | LLM linguistic analysis |
| R3 | **Consistency** | 20% | Are there internal contradictions? Do features align with problem statement? Are priorities consistent? | LLM cross-reference check |
| R4 | **Feasibility** | 20% | Is the requirement technically achievable? Are constraints realistic? Is the scope reasonable? | LLM + Research Agent knowledge |
| R5 | **Business Alignment** | 15% | Do the requirements actually solve the stated business problem? Are success metrics measurable and tied to business value? | LLM alignment check |

## 3.2 Scoring Formula

```
FOR each metric M in {R1..R5}:
    raw_score[m] = evaluator(m, artifact)
    normalized[m] = clamp(raw_score[m], 0, 100)

weighted_score = SUM(normalized[m] * weight[m]) for all m

aggregate_score = weighted_score

# Penalty for missing required sections
IF any_required_section_empty:
    aggregate_score *= 0.70

# Bonus for quantified metrics
IF business_metrics_quantified:
    aggregate_score = min(aggregate_score + 3, 100)
```

## 3.3 Threshold Configuration

```yaml
requirements_gate:
  minimum_score: 90
  max_iterations: 5
  metrics:
    completeness:
      threshold: 90
      critical: true    # Must pass individually
    clarity:
      threshold: 85
      critical: false
    consistency:
      threshold: 85
      critical: false
    feasibility:
      threshold: 85
      critical: false
    business_alignment:
      threshold: 90
      critical: true
```

## 3.4 Escalation Conditions

| Condition | Action |
|-----------|--------|
| Max iterations (5) reached with score < 90 | Escalate to human PM with full iteration history |
| Score < 50 after 2 iterations | Immediate escalation (fundamental misunderstanding) |
| Score unchanged for 2 consecutive iterations | Escalation (improvement agent stuck) |
| Critical metric (completeness or business alignment) fails 3 times independently | Escalation |
| Token cost exceeds budget for this artifact | Pause, notify, request budget approval |

## 3.5 Improvement Strategies

| Failure Pattern | Strategy |
|-----------------|----------|
| Low completeness | Prompt: "Identify all missing sections. The following sections are required: [Problem Statement, Target Users, Success Metrics, Features, Constraints, Assumptions, Dependencies]. Fill each." |
| Low clarity | Prompt: "Rewrite using plain language. Remove jargon. Define all domain terms. Add a glossary. Ensure each sentence has exactly one interpretation." |
| Low consistency | Prompt: "Identify contradictions between sections. For each: explain why it is contradictory, then resolve by choosing the version that better aligns with the problem statement." |
| Low feasibility | Prompt: "Assess each feature against known technical constraints. Flag infeasible items. Suggest simpler alternatives that achieve the same user goal. Reduce scope to what is achievable in 4 weeks." |
| Low business alignment | Prompt: "For each feature, ask: Does this directly contribute to the success metrics? If not, remove or deprioritize. Ensure every feature traces to a measurable business outcome." |

---

# 4. Architecture Quality Gate

## 4.1 Metrics

| # | Metric | Weight | Description | Evaluator |
|---|--------|--------|-------------|-----------|
| A1 | **Scalability** | 25% | Can the system handle 10x current load? Are bottlenecks identified? Are stateless services used? Is horizontal scaling designed in? | LLM + architectural patterns DB |
| A2 | **Reliability** | 20% | Are single points of failure eliminated? Is redundancy designed? Are failover strategies defined? Are retry/circuit-breaker patterns present? | LLM pattern matching |
| A3 | **Security** | 25% | Are security boundaries defined? Is the principle of least privilege applied? Are data flows secure? Is authN/authZ designed at the architecture level? | LLM + Security Agent review |
| A4 | **Maintainability** | 15% | Are services loosely coupled? Are interfaces clearly defined? Is the architecture documented in ADRs? Is it understandable by a new developer? | LLM complexity analysis |
| A5 | **Cost Efficiency** | 15% | Are resource needs estimated? Are managed services preferred where appropriate? Is there a cost model? Are serverless options considered? | LLM + cloud pricing data |

## 4.2 Scoring Formula

```
FOR each metric M in {A1..A5}:
    raw_score[m] = evaluator(m, artifact)
    normalized[m] = clamp(raw_score[m], 0, 100)

weighted_score = SUM(normalized[m] * weight[m])

aggregate_score = weighted_score

# Critical checks (each independently can cap the score)
IF has_single_point_of_failure:
    aggregate_score = min(aggregate_score, 70)

IF has_circular_service_dependency:
    aggregate_score = min(aggregate_score, 60)

IF no_authentication_designed:
    aggregate_score = min(aggregate_score, 40)

# Bonus for ADRs
IF adr_count >= 3:
    aggregate_score = min(aggregate_score + 2, 100)
```

## 4.3 Threshold Configuration

```yaml
architecture_gate:
  minimum_score: 90
  max_iterations: 5
  metrics:
    scalability:
      threshold: 90
      critical: true
    reliability:
      threshold: 85
      critical: true
    security:
      threshold: 90
      critical: true
    maintainability:
      threshold: 80
      critical: false
    cost_efficiency:
      threshold: 75
      critical: false
```

## 4.4 Escalation Conditions

| Condition | Action |
|-----------|--------|
| Max iterations (5) reached with score < 90 | Escalate to human architect |
| Critical metric (scalability, reliability, security) fails 3 times individually | Escalation |
| Circular dependency detected and not resolved in 2 iterations | Escalation |
| Architecture contradicting requirements (detected by cross-reference) | Escalate with both documents |
| Score < 60 after 2 iterations | Immediate escalation |

## 4.5 Improvement Strategies

| Failure Pattern | Strategy |
|-----------------|----------|
| Low scalability | Prompt: "Identify the top 3 bottlenecks. Redesign to use message queues for async processing. Add caching layers. Split monolithic service into read/write separation." |
| Low reliability | Prompt: "Identify every single point of failure. For each: add redundancy. Add health checks and auto-restart. Add circuit breakers. Define SLA and ensure architecture supports it." |
| Low security | Prompt: "Draw trust boundaries. Ensure data at rest and in transit is encrypted. Apply least privilege between services. Add API gateway as security boundary. Define auth flow end-to-end." |
| Low maintainability | Prompt: "Simplify the service graph. Merge over-split services. Split over-merged services. Ensure each service has a single responsibility. Add service interface documentation." |
| Low cost efficiency | Prompt: "Right-size resources. Consider serverless for low-traffic services. Use managed databases. Estimate monthly cost for each component. Compare with alternatives." |

---

# 5. Code Quality Gate

## 5.1 Metrics

| # | Metric | Weight | Description | Evaluator |
|---|--------|--------|-------------|-----------|
| C1 | **Complexity** | 20% | Cyclomatic complexity, nesting depth, function length, class size. Measured via radon. | radon (automated) |
| C2 | **Maintainability** | 20% | Maintainability index from radon. Code readability, documentation, naming conventions, consistency. | radon + LLM review |
| C3 | **Testability** | 20% | Is the code structured for testing? Are dependencies injectable? Are pure functions used where possible? Is there separation of concerns? | LLM structural review |
| C4 | **Performance** | 20% | Are there obvious performance issues? N+1 queries, missing indexes, blocking I/O in async context, unnecessary allocations? | LLM + AST analysis |
| C5 | **Security** | 20% | Are there input validation gaps, SQL injection vectors, unsafe deserialization, missing auth checks, exposed secrets? | bandit + LLM review |

## 5.2 Scoring Formula

```
# Automated metrics (C1, C2)
c1_score = radon_complexity_score(code)   # 0-100, higher is better
c2_score = radon_maintainability_score(code)

# LLM-evaluated metrics (C3, C4, C5)
c3_score = llm.evaluate(code, "testability_criteria")
c4_score = llm.evaluate(code, "performance_criteria")
c5_score = llm.evaluate(code, "security_criteria")

weighted_score = c1_score*0.20 + c2_score*0.20 + c3_score*0.20 + c4_score*0.20 + c5_score*0.20

aggregate_score = weighted_score

# Death penalties
IF bandit_finds_critical:
    aggregate_score = min(aggregate_score, 50)

IF radon_cyclomatic > 20 (any function):
    aggregate_score = min(aggregate_score, 70)

IF mypy_type_errors > 0:
    aggregate_score = min(aggregate_score, 85)

IF ruff_lint_errors > 0:
    aggregate_score = min(aggregate_score, 80)
```

## 5.3 Radon Scoring Translation

| Radon Rank | Complexity Score | Description |
|------------|-----------------|-------------|
| A (1-5) | 95-100 | Excellent, trivial to understand |
| B (6-10) | 85-94 | Good, well-structured |
| C (11-20) | 70-84 | Moderate, needs attention |
| D (21-30) | 50-69 | Complex, hard to maintain |
| E (31-40) | 25-49 | Very complex, refactor urgently |
| F (>40) | 0-24 | Unacceptable, rewrite required |

## 5.4 Threshold Configuration

```yaml
code_gate:
  minimum_score: 92
  max_iterations: 7
  metrics:
    complexity:
      threshold: 85
      critical: false
    maintainability:
      threshold: 85
      critical: false
    testability:
      threshold: 90
      critical: true
    performance:
      threshold: 85
      critical: false
    security:
      threshold: 95
      critical: true    # Must be very high - security is non-negotiable
```

## 5.5 Escalation Conditions

| Condition | Action |
|-----------|--------|
| Max iterations (7) reached with score < 92 | Escalate to human developer |
| bandit finds critical vulnerability that persists 3 iterations | Immediate escalation |
| Score decreases 2 iterations in a row | Escalation (getting worse) |
| Performance score < 50 (fundamental algorithm problem) | Escalation |
| Code fails to even import/compile after 2 iterations | Immediate escalation |

## 5.6 Improvement Strategies

| Failure Pattern | Strategy |
|-----------------|----------|
| High complexity | Prompt: "Refactor the most complex function into smaller functions. Extract methods. Use early returns. Reduce nesting. Max 10 lines per function, max 3 levels of nesting." |
| Low maintainability | Prompt: "Add docstrings to all public functions. Use descriptive variable names. Add type hints everywhere. Extract magic numbers into named constants. Follow PEP 8 strictly." |
| Low testability | Prompt: "Inject dependencies through constructor. Use protocols/ABCs for interfaces. Extract side effects to boundaries. Make pure functions where possible. Avoid global state." |
| Poor performance | Prompt: "Profile the slow paths. Add database indexes. Use connection pooling. Batch queries. Add caching. Use async where appropriate. Avoid N+1 queries." |
| Security issues | Prompt: "Validate all inputs with Pydantic. Use parameterized queries. Hash passwords with bcrypt. Add CSRF protection. Add rate limiting. Check authorization on every endpoint. Never log secrets." |

---

# 6. Testing Quality Gate

## 6.1 Metrics

| # | Metric | Weight | Description | Evaluator |
|---|--------|--------|-------------|-----------|
| T1 | **Coverage** | 30% | Line coverage %, branch coverage %, function coverage % from coverage.py | coverage.py (automated) |
| T2 | **Mutation Score** | 30% | % of mutants killed by test suite from mutmut. Surviving mutants indicate weak tests. | mutmut (automated) |
| T3 | **Reliability** | 20% | Flakiness detection: run tests N times. Pass rate. Determinism. Test isolation (no shared state causing order-dependent failures). | pytest repeat + LLM |
| T4 | **Edge Case Coverage** | 20% | Are edge cases tested? (null, empty, max values, boundary conditions, error paths, race conditions) | LLM review of test file |

## 6.2 Scoring Formula

```
# Automated metrics
ty1_score = coverage_line_pct    # 0-100
ty2_score = mutation_score_pct   # 0-100

# Semi-automated
flakiness_pct = passed_runs / total_runs * 100
ty3_score = flakiness_pct

# LLM-evaluated
ty4_score = llm.evaluate(test_file, "edge_case_criteria")

weighted_score = ty1_score*0.30 + ty2_score*0.30 + ty3_score*0.20 + ty4_score*0.20

aggregate_score = weighted_score

# Penalties
IF mutation_score < 60:
    aggregate_score = min(aggregate_score, 60)

IF tests_crash (not fail, crash):
    aggregate_score = min(aggregate_score, 30)

IF coverage < 50:
    aggregate_score = min(aggregate_score, 50)

IF any_test_flaky (passes sometimes, fails sometimes in 5 runs):
    aggregate_score = min(aggregate_score, 70)
```

## 6.3 Threshold Configuration

```yaml
testing_gate:
  minimum_score: 95
  max_iterations: 5
  metrics:
    coverage:
      threshold: 90   # 90% line coverage minimum
      critical: true
    mutation_score:
      threshold: 80   # 80% mutants killed
      critical: true
    reliability:
      threshold: 95   # 95% of runs pass deterministically
      critical: true
    edge_cases:
      threshold: 85
      critical: false
```

## 6.4 Escalation Conditions

| Condition | Action |
|-----------|--------|
| Max iterations (5) with score < 95 | Escalate to human QA |
| Tests crash (not logical failure, interpreter crash) | Immediate escalation |
| Coverage decreases from one iteration to the next | Escalation |
| Mutation score < 30 after 2 iterations | Escalation (fundamental test quality issue) |
| 3+ flaky tests detected | Escalation (test reliability issue) |

## 6.5 Improvement Strategies

| Failure Pattern | Strategy |
|-----------------|----------|
| Low coverage | Prompt: "Analyze coverage report. Identify the uncovered lines/functions/branches. Generate new tests specifically for uncovered code. Prioritize branches and error paths over boilerplate." |
| Low mutation score | Prompt: "Surviving mutants indicate weak assertions. For each surviving mutant: strengthen the assertions to detect the behavioral change. If a mutant is equivalent (cannot be killed), document why." |
| Flaky tests | Prompt: "For each flaky test, identify: shared mutable state, time dependency, network dependency, order dependency. Rewrite using: isolated fixtures, mocked time, mocked network, explicit ordering via pytest-order." |
| Missing edge cases | Prompt: "For each function: test with None, empty string, empty list, zero, negative numbers, max int, unicode, very long strings, concurrent access. Generate parametrized tests covering all boundaries." |

---

# 7. Security Quality Gate

## 7.1 Metrics

| # | Metric | Weight | Description | Evaluator |
|---|--------|--------|-------------|-----------|
| S1 | **Vulnerability Scan** | 35% | bandit + safety scans. Count of HIGH/MEDIUM/LOW findings. CVE severity. | bandit + safety (automated) |
| S2 | **LLM Security Review** | 25% | LLM reviews all code for: logic flaws, race conditions, auth bypass, insecure defaults, missing rate limiting, improper error handling exposing internals. | LLM deep review |
| S3 | **Secret Detection** | 20% | Scans all files for hardcoded secrets: API keys, tokens, passwords, private keys, connection strings. Entropy-based detection. | detect-secrets + regex |
| S4 | **Dependency Audit** | 10% | Audits all dependencies for known CVEs. Checks for outdated packages. Flags unmaintained packages. | safety + pip-audit (automated) |
| S5 | **Compliance Check** | 10% | Checks against OWASP Top 10, PCI-DSS (if applicable), GDPR basics (PII handling). | LLM compliance review |

## 7.2 Scoring Formula

```
# Automated
s1_score = 100 - SUM(vulnerability_penalties)
    # HIGH: -40 each, MEDIUM: -15 each, LOW: -5 each
    # CRITICAL CVE: -100 (instant 0)

s3_score = 100 if no_secrets_found else max(0, 100 - secrets_found * 30)

s4_score = 100 if no_critical_cves else max(0, 100 - critical_cves * 50 - high_cves * 20)

# LLM-evaluated
s2_score = llm.evaluate(code, "security_review_criteria")
s5_score = llm.evaluate(code, "compliance_criteria")

weighted_score = s1_score*0.35 + s2_score*0.25 + s3_score*0.20 + s4_score*0.10 + s5_score*0.10

aggregate_score = weighted_score

# Immediate failure conditions (security is non-negotiable)
IF any_critical_cve:
    aggregate_score = 0          # Gate MUST fail

IF any_secret_found:
    aggregate_score = min(aggregate_score, 30)

IF bandit_HIGH_count > 0:
    aggregate_score = min(aggregate_score, 50)

IF auth_bypass_possible:
    aggregate_score = 0          # Gate MUST fail
```

## 7.3 Threshold Configuration

```yaml
security_gate:
  minimum_score: 98    # Security gate is the strictest
  max_iterations: 3    # Few iterations - security issues should be fixable fast
  halt_on: critical    # If any critical finding, halt immediately (do not loop)
  metrics:
    vulnerability_scan:
      threshold: 95
      critical: true
    llm_security_review:
      threshold: 95
      critical: true
    secret_detection:
      threshold: 100   # Must be 100 - zero secrets allowed
      critical: true
    dependency_audit:
      threshold: 90
      critical: false
    compliance_check:
      threshold: 90
      critical: false
```

## 7.4 Escalation Conditions

| Condition | Action |
|-----------|--------|
| Any critical CVE found | Gate fails immediately. Do not loop. Escalate to human security review. |
| Secret found | Gate fails immediately. Escalate. Do not loop (secret must be revoked, not just removed from code). |
| Auth bypass possible | Gate fails. Escalate. Critical security architecture flaw. |
| Score < 50 after 1 iteration | Escalate (fundamental security problems). |
| 3 bandit HIGH findings persist after 2 iterations | Escalate. |

## 7.5 Improvement Strategies

| Failure Pattern | Strategy |
|-----------------|----------|
| bandit HIGH findings | Prompt: "Fix the specific HIGH-severity findings reported by bandit. Do not change anything else. For each finding, apply the recommended fix from bandit documentation." |
| Secrets detected | Prompt: "WARNING: Secrets found in code. Remove hardcoded secrets. Replace with environment variables or Vault references. Never hardcode credentials." |
| CVEs in dependencies | Prompt: "Upgrade the vulnerable dependencies to the latest patched version. If no patch exists, replace the dependency with a secure alternative." |
| Auth issues | Prompt: "Implement proper authentication check on every endpoint. Verify JWT on every request. Check authorization (RBAC) for the specific resource. Never rely on client-side auth." |
| Input validation gaps | Prompt: "Every user input must be validated with Pydantic models. Define min/max lengths, regex patterns, allowed values. Reject invalid input with 422. Never trust client input." |

---

# 8. Deployment Quality Gate

## 8.1 Metrics

| # | Metric | Weight | Description | Evaluator |
|---|--------|--------|-------------|-----------|
| D1 | **Stability** | 40% | Error rate (5xx / total requests), crash loop detection, OOM kills, pod restart count. Window: 5 minutes post-deploy. | Prometheus metrics |
| D2 | **Availability** | 35% | Health check success rate, uptime %, endpoint reachability. All health endpoints must return 200. | Prometheus blackbox exporter |
| D3 | **Performance** | 25% | P50/P95/P99 latency vs baseline (pre-deploy). Must not degrade by more than 20%. Throughput must not drop by more than 10%. | Prometheus histograms |

## 8.2 Scoring Formula

```
# D1: Stability
error_rate_5xx = count_5xx / total_requests
IF error_rate_5xx == 0:
    d1_score = 100
ELIF error_rate_5xx < 0.01:    # < 1% error rate
    d1_score = 90 - (error_rate_5xx * 1000)
ELIF error_rate_5xx < 0.05:    # < 5% error rate
    d1_score = 70 - (error_rate_5xx * 100)
ELSE:
    d1_score = max(0, 30 - (error_rate_5xx * 100))

IF any_pod_restart:
    d1_score = min(d1_score, 60)

# D2: Availability
health_pass_rate = successful_health_checks / total_health_checks
d2_score = health_pass_rate * 100

# D3: Performance
p95_degradation = (p95_current - p95_baseline) / p95_baseline
IF p95_degradation < 0:       # Actually faster
    d3_score = 100
ELIF p95_degradation < 0.10:  # <10% slower
    d3_score = 95 - (p95_degradation * 50)
ELIF p95_degradation < 0.20:  # 10-20% slower
    d3_score = 80 - (p95_degradation * 100)
ELIF p95_degradation < 0.50:  # 20-50% slower
    d3_score = 50 - (p95_degradation * 50)
ELSE:                          # >50% slower
    d3_score = max(0, 20 - (p95_degradation * 10))

throughput_degradation = (throughput_current - throughput_baseline) / throughput_baseline
IF throughput_degradation < -0.20:  # >20% drop
    d3_score = min(d3_score, 40)

weighted_score = d1_score*0.40 + d2_score*0.35 + d3_score*0.25

aggregate_score = weighted_score

# Immediate triggers
IF error_rate_5xx > 0.10:     # >10% errors
    aggregate_score = 0         # AUTO-ROLLBACK

IF d2_score < 50:               # <50% availability
    aggregate_score = 0         # AUTO-ROLLBACK

IF any_oom_kill:
    aggregate_score = min(aggregate_score, 30)
```

## 8.3 Threshold Configuration

```yaml
deployment_gate:
  minimum_score: 95
  max_iterations: 3
  observation_window_seconds: 300   # 5 minutes
  canary_traffic_percent: 10        # Start at 10%
  promote_after_stable: 600         # 10 minutes stable before full promote
  auto_rollback_triggers:
    - error_rate > 10%
    - availability < 50%
    - p95_latency > 3x baseline
    - any OOM kill
    - any crash loop
  metrics:
    stability:
      threshold: 95
      critical: true
    availability:
      threshold: 99
      critical: true
    performance:
      threshold: 90
      critical: false
```

## 8.4 Escalation Conditions

| Condition | Action |
|-----------|--------|
| Auto-rollback triggered | Rollback immediately. Create incident. Escalate to DevOps + Self-Healing. |
| 3 sequential rollbacks for same service | Escalate to human SRE. Lock service from further auto-deployment. |
| Canary degrades but not enough to auto-rollback (score 70-94) | Pause. Extend observation window to 15 min. If no improvement, rollback + escalate. |
| Deployment gate fails 3 times (3 deployment attempts) | Escalate. Something fundamentally wrong with the deployment configuration. |

## 8.5 Improvement Strategies

| Failure Pattern | Strategy |
|-----------------|----------|
| High error rate | Prompt: "Analyze error logs from the failed deployment. Identify the top error. Fix the root cause (not the symptom). Add error handling. Add regression test for the specific error." |
| Low availability | Prompt: "Health checks are failing. Check: are probes correctly configured? Is the startup time too long? Is the port correct? Are dependencies healthy? Fix health check endpoint and probe config." |
| Performance degradation | Prompt: "Analyze latency histograms. Identify the slow endpoint. Profile it. Check: N+1 queries, missing indexes, connection pool exhaustion, GC pauses. Apply targeted optimization." |
| OOM / Crash loop | Prompt: "Memory profile the service. Find the memory leak. Check for unbounded collections. Increase heap if legitimate need, but prefer fixing the leak. Add memory limits to prevent cascade." |

---

# 9. Scoring Engine Algorithm

## 9.1 Core Algorithm

```
SCORING_ENGINE.evaluate(artifact, gate_type):
    
    gate_config = load_gate_config(gate_type)
    metric_results = {}
    
    // PHASE 1: Run all metric evaluators (can be parallel)
    FOR metric in gate_config.metrics:
        evaluator = select_evaluator(metric.type, metric.evaluator)
        raw_score = evaluator.evaluate(artifact)
        justification = evaluator.justify(raw_score)
        metric_results[metric.name] = {
            score: clamp(raw_score, 0, 100),
            justification: justification,
            passed: raw_score >= metric.threshold
        }
    
    // PHASE 2: Compute weighted aggregate
    aggregate = SUM(
        metric_results[m].score * gate_config.metrics[m].weight
        FOR m in gate_config.metrics
    )
    
    // PHASE 3: Apply death penalties
    FOR penalty in gate_config.death_penalties:
        IF penalty.condition(metric_results):
            aggregate = min(aggregate, penalty.max_score)
    
    // PHASE 4: Apply bonuses
    FOR bonus in gate_config.bonuses:
        IF bonus.condition(metric_results):
            aggregate = min(aggregate + bonus.value, 100)
    
    // PHASE 5: Determine overall pass/fail
    critical_metrics_pass = ALL(
        metric_results[m].passed
        FOR m in gate_config.metrics
        WHERE m.critical == true
    )
    
    overall_pass = (aggregate >= gate_config.minimum_score) AND critical_metrics_pass
    
    RETURN ScoringResult(
        artifact_id: artifact.id,
        gate_type: gate_type,
        aggregate_score: aggregate,
        metric_results: metric_results,
        passed: overall_pass,
        timestamp: now(),
        iteration: artifact.iteration
    )
```

## 9.2 Evaluator Selection Matrix

| Metric Category | Evaluator Type | Implementation |
|-----------------|----------------|----------------|
| Automated Static | `AutomatedEvaluator` | Runs CLI tool (radon, bandit, coverage.py, mutmut). Parses output. Maps to 0-100 scale. |
| Metrics Query | `PrometheusEvaluator` | Queries Prometheus API for current metrics. Compares to baseline. Computes score. |
| LLM Review | `LLMEvaluator` | Sends artifact + evaluation criteria to LLM. Receives structured score + justification. |
| Structural Check | `StructuralEvaluator` | Validates JSON/YAML/Markdown structure. Checks required fields exist. |
| Regex / Pattern | `PatternEvaluator` | Runs regex/pattern matching (secret detection, code patterns). Counts matches. |

## 9.3 LLM Evaluator Prompt Template

```
You are a quality evaluator for the {gate_type} quality gate.
You are evaluating a {artifact_type} artifact.

ARTIFACT:
{artifact_content}

EVALUATE THE FOLLOWING METRIC:
Metric: {metric_name}
Definition: {metric_definition}
Scale: 0 (worst) to 100 (best)

SCORING RUBRIC:
95-100: Exceptional. Exceeds all expectations. Best practice exemplified.
85-94:  Good. Meets expectations. Minor improvements possible.
70-84:  Adequate. Passable but has notable issues.
50-69:  Poor. Significant issues that must be addressed.
25-49:  Very Poor. Major issues. Fundamental problems.
0-24:   Unacceptable. Completely fails the metric.

OUTPUT FORMAT (JSON):
{
  "score": <0-100>,
  "justification": "<2-3 sentences explaining the score>",
  "issues": ["<specific issue 1>", "<specific issue 2>"],
  "strengths": ["<specific strength 1>"],
  "improvement_suggestions": ["<actionable suggestion 1>"]
}
```

## 9.4 Score Aggregation Across Iterations

```
// Track progression across recursive loops
artifact.score_history = [
    {iteration: 1, aggregate: 72, passed: false},
    {iteration: 2, aggregate: 84, passed: false},
    {iteration: 3, aggregate: 91, passed: true},
]

// Metrics:
improvement_rate = (score[i] - score[i-1]) / score[i-1]
convergence_detected = improvement_rate < 0.02 for 2 consecutive iterations
stuck_detected = score unchanged or decreased for 2 consecutive iterations

// Store for self-learning
record = {
    artifact_type: "prd",
    prompt: original_prompt,
    iterations: artifact.score_history,
    final_score: artifact.score_history[-1].aggregate,
    passed: artifact.score_history[-1].passed,
    total_tokens: sum_of_all_iteration_tokens,
    total_cost: total_tokens * model_cost_per_token
}
```

---

# 10. Loop Controller

## 10.1 State Machine

```
                    ┌─────────────┐
                    │   CREATED   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
              ┌────►│  GENERATING │
              │     └──────┬──────┘
              │            │
              │            ▼
              │     ┌─────────────┐
              │     │  EVALUATING │◄──────────────┐
              │     └──────┬──────┘               │
              │            │                       │
              │     ┌──────▼──────┐               │
              │     │  SCORING    │               │
              │     └──────┬──────┘               │
              │            │                       │
              │     ┌──────▼──────┐    ┌──────────┴──────┐
              │     │ SCORE >=    │ NO │ CRITIQUING      │
              │     │ THRESHOLD?  ├───►│ (Review Agent)   │
              │     └──────┬──────┘    └────────┬─────────┘
              │            │ YES                │
              │            ▼                    ▼
              │     ┌─────────────┐    ┌─────────────┐
              │     │  APPROVED   │    │  IMPROVING  │
              │     └─────────────┘    │  (Improve    │
              │                        │  Agent)      │
              │                        └──────┬───────┘
              │                               │
              │                        ┌──────▼──────┐
              │                        │ ITERATION < │ YES
              │                        │ MAX?        ├──────┘
              │                        └──────┬──────┘
              │                               │ NO
              │                               ▼
              │                        ┌─────────────┐
              │                        │  ESCALATED  │
              │                        └─────────────┘
              │
              │     ┌─────────────┐
              └─────┤  IMPROVING  │ (return path for improvements)
                    └─────────────┘
```

## 10.2 Loop Controller Algorithm

```
LOOP_CONTROLLER.run(artifact, gate_type, task_context):
    
    gate = GateConfig.load(gate_type)
    iteration = artifact.iteration or 0
    
    emit(RecursiveLoopStarted, {artifact_id, gate_type})
    
    WHILE iteration < gate.max_iterations:
        
        iteration += 1
        emit(LoopIteration, {artifact_id, iteration, gate_type})
        
        // Step 1: Generate or Improve
        IF iteration == 1:
            // First pass: initial generation
            artifact = agent.generate(task_context)
        ELSE:
            // Subsequent passes: improve based on critique
            artifact = improvement_agent.refine(artifact, critique)
        
        emit(ArtifactUpdated, {artifact_id, iteration})
        
        // Step 2: Score
        score_result = scoring_engine.evaluate(artifact, gate_type)
        emit(ArtifactScored, {artifact_id, score_result})
        
        // Step 3: Check pass
        IF score_result.passed:
            emit(QualityGatePassed, {artifact_id, score_result, iteration})
            artifact.status = APPROVED
            STORE artifact in memory
            RETURN {status: APPROVED, artifact, score_result, iteration}
        
        // Step 4: Check for stuck/degradation
        IF is_degrading(artifact.score_history):
            IF iteration >= 2:  // Gave it a chance
                ESCALATE("Score degrading", artifact, score_result)
                RETURN {status: ESCALATED}
        
        IF is_stuck(artifact.score_history, min_iterations=3):
            ESCALATE("Score plateaued", artifact, score_result)
            RETURN {status: ESCALATED}
        
        // Step 5: Check for immediate escalation conditions
        IF should_escalate_early(score_result, gate_type):
            ESCALATE("Early escalation condition met", artifact, score_result)
            RETURN {status: ESCALATED}
        
        // Step 6: Critique
        critique = review_agent.critique(artifact, score_result)
        emit(ArtifactCritiqued, {artifact_id, critique, iteration})
        
        // Step 7: Store iteration data for learning
        learning_service.record({
            artifact_id, iteration, gate_type,
            prompt: task_context,
            output: artifact,
            critique: critique,
            scores: score_result,
            tokens_used: llm.get_last_tokens()
        })
        
        artifact.score_history.append(score_result)
        artifact.iteration = iteration
    
    // Max iterations reached without passing
    emit(QualityGateFailed, {artifact_id, score_result, gate_type, max_reached: true})
    ESCALATE("Max iterations reached without passing gate", artifact, score_result)
    RETURN {status: ESCALATED, artifact, score_result, iteration}
```

## 10.3 Stuck & Degradation Detection

```
IS_DEGRADING(score_history):
    IF len(score_history) < 2: RETURN false
    last_two = score_history[-2:]
    RETURN last_two[1].aggregate < last_two[0].aggregate

IS_STUCK(score_history, min_iterations=3):
    IF len(score_history) < min_iterations: RETURN false
    recent = score_history[-min_iterations:]
    scores = [s.aggregate for s in recent]
    improvement = [(scores[i] - scores[i-1]) for i in range(1, len(scores))]
    avg_improvement = mean(improvement)
    RETURN avg_improvement < 1.0   // Less than 1 point per iteration on average

SHOULD_ESCALATE_EARLY(score_result, gate_type):
    gate = GateConfig.load(gate_type)
    
    // Check gate-specific early escalation conditions
    IF gate_type == "security" AND score_result.aggregate < 50:
        RETURN true  // Security issues are urgent
    
    IF score_result.aggregate < 30:
        RETURN true  // Fundamental problem - unlikely to self-correct
    
    IF gate_type == "deployment" AND score_result.aggregate == 0:
        RETURN true  // Auto-rollback scenario - fix before redeploy
    
    RETURN false
```

## 10.4 Loop Configuration Summary

| Gate | Min Score | Max Iterations | Degradation Threshold | Stuck Threshold | Early Escalate < |
|------|-----------|----------------|----------------------|-----------------|-------------------|
| Requirements | 90 | 5 | Score drops 2x consecutive | < 1pt improvement for 3 iterations | Score < 30 |
| Architecture | 90 | 5 | Score drops 2x consecutive | < 1pt improvement for 3 iterations | Score < 30 |
| Code | 92 | 7 | Score drops 2x consecutive | < 1pt improvement for 3 iterations | Score < 30 |
| Testing | 95 | 5 | Score drops 2x consecutive | < 1pt improvement for 3 iterations | Score < 30 |
| Security | 98 | 3 | N/A (critical halt) | N/A | Score < 50 OR any critical CVE |
| Deployment | 95 | 3 | Auto-rollback | N/A | Score == 0 (auto-rollback) |

---

# 11. Escalation System

## 11.1 Escalation Types

| Type | Trigger | Severity | Target | Timeout |
|------|---------|----------|--------|---------|
| `max_iterations_exceeded` | Loop exhausted without passing | HIGH | Human role matching agent type | 4 hours |
| `score_degrading` | Score decreasing over iterations | MEDIUM | Human role matching agent type | 8 hours |
| `score_stuck` | Score plateaued, no improvement | MEDIUM | Human role matching agent type | 8 hours |
| `early_escalation` | Score critically low, unlikely to self-correct | HIGH | Human role matching agent type | 2 hours |
| `security_critical` | Critical CVE or auth bypass found | CRITICAL | Security team + On-call | 30 minutes |
| `deployment_rollback` | Auto-rollback triggered | CRITICAL | DevOps/SRE + On-call | 15 minutes |
| `cost_overrun` | Token budget exceeded | LOW | Project owner | 24 hours |
| `circular_dependency` | Architecture has circular dependency | HIGH | Human architect | 4 hours |
| `consensus_deadlock` | Debate cannot reach consensus | MEDIUM | Human architect or PM | 4 hours |

## 11.2 Escalation Payload

```json
{
  "escalation_id": "uuid",
  "type": "max_iterations_exceeded",
  "severity": "HIGH",
  "artifact": {
    "id": "uuid",
    "type": "architecture_document",
    "gate_type": "architecture_gate"
  },
  "project_id": "uuid",
  "task_id": "uuid",
  "agent_type": "architect_agent",
  "target_role": "human_architect",
  "history": {
    "iterations": 5,
    "final_score": 84,
    "threshold": 90,
    "score_progression": [72, 78, 82, 84, 84],
    "stuck_at": 3
  },
  "context": {
    "original_task": "...",
    "critiques": ["..."],
    "specific_failures": ["Low scalability: 65/100", "Missing security boundaries: 72/100"]
  },
  "suggested_actions": [
    "Review scalability section and suggest alternative architecture patterns",
    "Add explicit trust boundaries between services"
  ],
  "created_at": "ISO8601",
  "timeout": "ISO8601",
  "status": "OPEN"
}
```

## 11.3 Escalation Resolution

```
ON human_response(escalation_id, resolution):
    
    escalation = load(escalation_id)
    
    SWITCH resolution.action:
        
        CASE "accept_as_is":
            // Human overrides gate - force approve
            artifact.force_approved(by: human, reason: resolution.reason)
            emit(ArtifactForceApproved, {artifact, human, reason})
            CONTINUE workflow
        
        CASE "reject_and_reassign":
            // Human provides corrected artifact
            artifact = resolution.corrected_artifact
            // Run through gate one more time to validate
            score = scoring_engine.evaluate(artifact, gate_type)
            IF score.passed:
                CONTINUE workflow
            ELSE:
                // Human fix also didn't pass - escalate again
                RE_ESCALATE with human correction + new score
        
        CASE "modify_threshold":
            // Human lowers threshold for this specific case
            gate.threshold = resolution.new_threshold
            // Re-evaluate
            score = scoring_engine.evaluate(artifact, gate_type)
            IF score.passed:
                CONTINUE workflow
            ELSE:
                RE_ESCALATE
        
        CASE "cancel_task":
            // Human decides to abandon this task
            task.cancel(reason: resolution.reason)
            emit(TaskCancelled, {task, reason})
            ORCHESTRATOR.cleanup(task)
```

---

# 12. Improvement Strategies

## 12.1 Strategy Selection Algorithm

```
SELECT_STRATEGY(artifact, score_result, gate_type):

    // Identify the lowest-scoring metrics (top N)
    failing_metrics = SORT_BY_SCORE_ASC(score_result.metric_results)
    top_failures = failing_metrics[:2]   // Focus on worst 2
    
    // Match to improvement strategies
    strategies = []
    FOR each failure in top_failures:
        pattern = CLASSIFY_FAILURE(failure, artifact)
        strategy = LOOKUP_STRATEGY(gate_type, failure.metric, pattern)
        strategies.append(strategy)
    
    // Compose a comprehensive improvement prompt
    combined_strategy = MERGE_STRATEGIES(strategies)
    
    RETURN combined_strategy
```

## 12.2 Pattern Classification

```
CLASSIFY_FAILURE(metric_result, artifact):

    score = metric_result.score
    name = metric_result.name
    justification = metric_result.justification
    
    IF score < 30:
        return "CRITICAL"    // Fundamental problem
    ELIF score < 60:
        return "MAJOR"       // Significant problem
    ELIF score < 80:
        return "MODERATE"    // Notable issues
    ELSE:
        return "MINOR"       // Close to passing
    
    // Sub-classification by issue type
    // (extracted from justification via LLM or keyword matching)
    // e.g., "missing", "contradictory", "too complex", "insecure", "slow"
```

## 12.3 Strategy Catalog by Gate

### 12.3.1 Requirements Improvement Strategies (Complete)

| Metric | CRITICAL (0-29) | MAJOR (30-59) | MODERATE (60-79) | MINOR (80-89) |
|--------|-----------------|---------------|-------------------|---------------|
| Completeness | Rewrite from scratch. Structural template required. List all mandatory sections and fill each. | Identify all gaps. Fill each gap with substantive content (not placeholder). | Add missing details to existing sections. Expand on brief sections. | Add missing edge cases. Clarify boundary conditions. |
| Clarity | Full rewrite in plain language. Use Flesch-Kincaid grade 8 target. | Rewrite ambiguous sections. Add glossary. Use examples for complex concepts. | Clarify individual sentences flagged as ambiguous. Add concrete examples. | Scan for jargon. Add 1-sentence definitions for domain terms. |
| Consistency | Identify and resolve all contradictions systematically. Re-align entire document. | Resolve specific contradictions. Re-align feature priorities with problem statement. | Cross-check related sections. Ensure numbers match across document. | Verify one section against its references. Fix minor inconsistencies. |
| Feasibility | Complete re-scoping. Remove infeasible features. Propose alternatives. | Replace specific infeasible features with alternatives. Add feasibility notes. | Add technical feasibility assessments. Note assumptions and risks. | Verify each feature against known constraints. Add caveats. |
| Business Alignment | Re-ground in business problem. Ensure every feature traces to success metric. | Re-prioritize using MoSCoW. Cut features not aligned to core problem. | Strengthen traceability from feature to KPI. Add measurable outcomes. | Sharpen success metrics. Make them SMART. |

### 12.3.2 Architecture Improvement Strategies (Complete)

| Metric | CRITICAL (0-29) | MAJOR (30-59) | MODERATE (60-79) | MINOR (80-89) |
|--------|-----------------|---------------|-------------------|---------------|
| Scalability | Restructure architecture entirely. Introduce message queues, CDNs, read replicas, caching layers. | Identify top 3 bottlenecks. Add caching for hottest paths. Add async processing for non-critical paths. | Add horizontal scaling design. Specify auto-scaling rules. Add cache strategy. | Add load estimates. Specify instance sizes. Document scaling plan. |
| Reliability | Eliminate all SPOFs. Add redundancy everywhere. Add health checks and auto-healing. | Add redundancy for critical services. Add retry with backoff. Add circuit breakers. | Define SLA targets per service. Add health check endpoints. Document failover procedures. | Add graceful degradation paths. Improve error handling documentation. |
| Security | Full security architecture redesign. Add API gateway, WAF, encryption everywhere, auth boundary review. | Add auth at all service boundaries. Encrypt all data at rest. Add rate limiting. | Add specific security controls for flagged services. Document trust boundaries. | Add input validation details. Add specific security headers. Review one weak point. |
| Maintainability | Simplify over-engineered design. Merge over-split services. Define clear interfaces. | Reduce service count. Clarify service responsibilities. Add interface documentation. | Add ADRs for all major decisions. Improve service boundary documentation. | Add README to each service. Improve naming consistency. |
| Cost Efficiency | Full cost model rebuild. Right-size everything. Consider serverless for low-traffic paths. | Replace expensive patterns with cheaper alternatives. Add cost estimates per service. | Add resource estimates. Identify cost optimization opportunities. | Add cost model with monthly estimates. Document trade-offs. |

### 12.3.3 Code Improvement Strategies (Complete)

| Metric | CRITICAL (0-29) | MAJOR (30-59) | MODERATE (60-79) | MINOR (80-89) |
|--------|-----------------|---------------|-------------------|---------------|
| Complexity | Full refactor. Split into smaller functions. Max 10 lines per function, 3 nesting levels. Extract classes. | Identify top 3 complex functions. Refactor each. Extract methods. Reduce nesting. | Refactor specific complex blocks identified by radon. Add early returns. | Simplify specific functions flagged as complex. Add comments on non-obvious logic. |
| Maintainability | Rewrite with consistent patterns. Add docstrings everywhere. Follow style guide strictly. | Add docstrings to all public interfaces. Standardize patterns across files. | Fix specific maintainability issues from radon report. | Improve variable naming. Add type hints where missing. |
| Testability | Major restructure. Inject all dependencies. Use protocols/interfaces. Separate I/O from logic. | Refactor worst offenders: singletons, global state, hardcoded dependencies. | Add dependency injection for specific modules. Extract pure functions. | Add interfaces for specific dependencies. Improve mockability. |
| Performance | Identify and fix critical performance bugs. Profile and optimize hot paths. | Fix N+1 queries. Add missing indexes. Add caching for slow queries. | Optimize specific slow functions. Batch operations. | Add query optimization. Review connection pooling. |
| Security | Fix all bandit HIGH findings. Add input validation everywhere. Implement proper auth. | Fix all bandit MEDIUM+ findings. Add output encoding. Review auth on all endpoints. | Fix specific flagged vulnerabilities. Add rate limiting. | Review specific endpoints for missing validation. |

### 12.3.4 Testing Improvement Strategies (Complete)

| Metric | CRITICAL (0-29) | MAJOR (30-59) | MODERATE (60-79) | MINOR (80-89) |
|--------|-----------------|---------------|-------------------|---------------|
| Coverage | Generate comprehensive test suite from scratch. Cover every public function. | Generate tests for all uncovered modules. Prioritize high-risk code. | Generate tests for specific uncovered functions and branches. | Add tests for uncovered edge cases. |
| Mutation Score | Rewrite assertions to be stronger. Test behavior, not implementation. Kill surviving mutants. | Strengthen assertions for specific tests with surviving mutants. | Identify and kill specific mutant categories. | Review specific surviving mutants. Add edge case assertions. |
| Reliability | Fix all flaky tests. Remove shared state. Mock time/network. Use isolated fixtures. | Identify and fix top flaky tests. Add test isolation. | Review specific flaky tests. Add retry with analyze-on-failure. | Add test stability comment. Mark known-flaky with link to issue. |
| Edge Cases | Generate edge case tests comprehensively: null, empty, boundary, error, concurrent. | Add edge case tests for critical paths. Parametrize boundary values. | Add specific edge cases identified in review. | Add missing boundary tests for specific functions. |

### 12.3.5 Security Improvement Strategies (Complete)

| Metric | CRITICAL (0-29) | MAJOR (30-59) | MODERATE (60-79) | MINOR (80-89) |
|--------|-----------------|---------------|-------------------|---------------|
| Vulnerability Scan | Fix all HIGH and CRITICAL bandit findings immediately. Halt any deployment. | Fix all MEDIUM findings. Review all LOW findings. | Fix specific flagged patterns. | Review all findings. Document false positives. |
| LLM Security Review | Full security redesign of flagged areas. | Address specific logic flaws and race conditions. | Fix specific insecure defaults. Add missing security headers. | Review specific flagged patterns. |
| Secret Detection | Remove all secrets. Rotate any exposed credentials immediately. Implement pre-commit hook. | Remove flagged potential secrets. Add to .gitignore. | Review flagged entropy matches. Add false positive annotations. | Configure secret scanning rules. |
| Dependency Audit | Upgrade all vulnerable dependencies. Replace unmaintained packages. | Upgrade critical/High CVE dependencies. | Review and update flagged packages. | Schedule regular dependency updates. |
| Compliance | Full compliance review. Address all OWASP Top 10 gaps. | Address specific compliance gaps. | Review and document compliance posture. | Add compliance documentation. |

### 12.3.6 Deployment Improvement Strategies (Complete)

| Metric | CRITICAL (0-29) | MAJOR (30-59) | MODERATE (60-79) | MINOR (80-89) |
|--------|-----------------|---------------|-------------------|---------------|
| Stability | Rollback immediately. Debug error logs. Fix root cause. Add error handling. Re-test. | Analyze error logs. Fix top error. Add specific error handling. | Investigate error patterns. Add more robust error handling. | Review error budget. Add alerting on specific error types. |
| Availability | Fix failing health checks. Verify probe configuration. Ensure dependencies are healthy. | Review health check endpoint. Adjust probe timing. Add dependency health cascade. | Tune probe parameters. Adjust startup time. | Review health check logic. |
| Performance | Rollback if >3x baseline. Profile hot path. Fix performance regression. | Profile slow endpoints. Optimize queries. Add caching. | Tune specific slow queries. Increase connection pools. | Review performance metrics. Adjust resource limits. |

---

# 13. Gate Fusion Matrix

When an artifact passes through multiple gates (e.g., Code + Security + Testing before deployment), the gates are fused:

```
FUSED_GATE_RESULT = {
    passed: ALL individual gates passed,
    aggregate_score: MIN(individual aggregate scores),
    gates: {
        code: {score: 94, passed: true},
        security: {score: 98, passed: true},
        testing: {score: 91, passed: false},  // This causes overall failure
        deployment: {score: 97, passed: true}
    },
    blocking_gate: "testing",  // The gate that caused failure
    overall_passed: false
}
```

## 13.1 Pre-Deployment Gate Chain

```
Code Generation Complete
    │
    ▼
┌─────────┐
│ CODE    │── FAIL ──► Loop (Code Improvement)
│ GATE    │
└────┬────┘
     │ PASS
     ▼
┌─────────┐
│ TESTING │── FAIL ──► Loop (Test Improvement)
│ GATE    │
└────┬────┘
     │ PASS
     ▼
┌─────────┐
│ SECURITY│── FAIL ──► Loop or Halt (if critical)
│ GATE    │
└────┬────┘
     │ PASS
     ▼
┌─────────┐
│ DEPLOY  │── Start canary deployment
└─────────┘
```

---

# 14. Full Specification Tables

## 14.1 Gate Summary

| Gate | Artifacts | Metrics Count | Min Score | Max Iterations | Critical Metrics | Auto-Halt Conditions |
|------|-----------|---------------|-----------|----------------|-----------------|---------------------|
| Requirements | PRD, User Stories, Feature Specs, Research Reports | 5 | 90 | 5 | Completeness (90), Business Alignment (90) | Score < 50 after 2 iterations |
| Architecture | Architecture Doc, API Contracts, ERDs | 5 | 90 | 5 | Scalability (90), Reliability (85), Security (90) | Circular dependency or score < 60 after 2 iterations |
| Code | Source Code (Backend, Frontend) | 5 | 92 | 7 | Testability (90), Security (95) | bandit critical finding, code doesn't compile |
| Testing | Unit, Integration, E2E Tests | 4 | 95 | 5 | Coverage (90), Mutation Score (80), Reliability (95) | Tests crash, coverage decreases |
| Security | Security Reports, Vulnerability Scans | 5 | 98 | 3 | Vulnerability Scan (95), LLM Review (95), Secrets (100) | Any critical CVE, any secret found, auth bypass |
| Deployment | Deploy Config, Running Deployment | 3 | 95 | 3 | Stability (95), Availability (99) | Error rate > 10%, OOM kill, crash loop |

## 14.2 Metric Weights Cross-Reference

| Metric | Requirements | Architecture | Code | Testing | Security | Deployment |
|--------|:-----------:|:------------:|:----:|:-------:|:--------:|:----------:|
| Completeness | 25% | — | — | — | — | — |
| Clarity | 20% | — | — | — | — | — |
| Consistency | 20% | — | — | — | — | — |
| Feasibility | 20% | — | — | — | — | — |
| Business Alignment | 15% | — | — | — | — | — |
| Scalability | — | 25% | — | — | — | — |
| Reliability | — | 20% | — | — | — | — |
| Architecture Security | — | 25% | — | — | — | — |
| Maintainability (Arch) | — | 15% | — | — | — | — |
| Cost Efficiency | — | 15% | — | — | — | — |
| Complexity | — | — | 20% | — | — | — |
| Maintainability (Code) | — | — | 20% | — | — | — |
| Testability | — | — | 20% | — | — | — |
| Performance (Code) | — | — | 20% | — | — | — |
| Code Security | — | — | 20% | — | — | — |
| Coverage | — | — | — | 30% | — | — |
| Mutation Score | — | — | — | 30% | — | — |
| Test Reliability | — | — | — | 20% | — | — |
| Edge Cases | — | — | — | 20% | — | — |
| Vulnerability Scan | — | — | — | — | 35% | — |
| LLM Security Review | — | — | — | — | 25% | — |
| Secret Detection | — | — | — | — | 20% | — |
| Dependency Audit | — | — | — | — | 10% | — |
| Compliance | — | — | — | — | 10% | — |
| Stability | — | — | — | — | — | 40% |
| Availability | — | — | — | — | — | 35% |
| Performance (Deploy) | — | — | — | — | — | 25% |

## 14.3 Total Metrics Inventory

| Gate | Total Metrics | Automated | LLM-Based | Structural |
|------|:-----------:|:---------:|:---------:|:----------:|
| Requirements | 5 | 0 | 4 | 1 |
| Architecture | 5 | 0 | 5 | 0 |
| Code | 5 | 2 | 3 | 0 |
| Testing | 4 | 2 | 1 | 1 |
| Security | 5 | 3 | 2 | 0 |
| Deployment | 3 | 3 | 0 | 0 |
| **Total** | **27** | **10** | **15** | **2** |

---

# Appendices

## Appendix A: Evaluation LLM Prompt (Full)

```
SYSTEM PROMPT:
You are the AISC Quality Evaluation Engine. You are evaluating artifacts 
for quality in the {gate_type} quality gate. You are objective, thorough, 
and consistent. You always provide specific, actionable feedback.

Your evaluation will be used to determine whether the artifact advances 
to the next phase or returns for improvement.

You output ONLY valid JSON. No preamble, no explanation outside the JSON.

USER PROMPT:
Gate Type: {gate_type}
Artifact Type: {artifact_type}
Metric: {metric_name}
Metric Definition: {metric_definition}
Threshold: {threshold}

ARTIFACT TO EVALUATE:
---
{artifact_content}
---

SCORING RUBRIC:
95-100: Exceptional. Best practice exemplified. No improvements needed.
85-94:  Good. Meets expectations. Minor improvements possible.
70-84:  Adequate. Passable but has notable issues that should be addressed.
50-69:  Poor. Significant issues. Must be improved before advancing.
25-49:  Very Poor. Major fundamental problems.
0-24:   Unacceptable. Completely fails the metric.

OUTPUT ONLY THIS JSON:
{
  "score": <integer 0-100>,
  "justification": "<2-4 sentence explanation>",
  "issues": ["<specific, actionable issue>", ...],
  "strengths": ["<specific strength>", ...],
  "improvement_suggestions": ["<specific, actionable suggestion>", ...]
}
```

## Appendix B: Radon Scoring Translation Table

| Radon Cyclomatic | Radon Maintainability | Score Range | Grade |
|-----------------|----------------------|-------------|-------|
| 1-3 | A (Excellent) | 95-100 | A |
| 4-5 | B (Good) | 85-94 | B |
| 6-10 | C (Moderate) | 70-84 | C |
| 11-15 | D (Complex) | 50-69 | D |
| 16-25 | E (Very Complex) | 25-49 | E |
| 26+ | F (Unacceptable) | 0-24 | F |

## Appendix C: Bandit Severity to Score Impact

| Bandit Severity | Score Impact | Description |
|-----------------|-------------|-------------|
| CRITICAL | -100 (instant 0) | Gate fails. No loop. |
| HIGH | -40 per finding | Max score capped at 50 if any HIGH |
| MEDIUM | -15 per finding | Cumulative impact |
| LOW | -5 per finding | Minor impact |

## Appendix D: Deployment Scoring Examples

```
Example 1: Clean deployment
  - Error rate: 0%
  - Health checks: 100%
  - P95 latency: same as baseline
  Score: 100/100 -> PASS

Example 2: Minor latency increase
  - Error rate: 0.5%
  - Health checks: 100%
  - P95 latency: +8% from baseline
  Score: 95/100 -> PASS (borderline)

Example 3: Moderate errors
  - Error rate: 3%
  - Health checks: 98%
  - P95 latency: +15% from baseline
  Score: ~76/100 -> FAIL -> Loop

Example 4: Severe - auto rollback
  - Error rate: 12%
  Score: 0/100 -> AUTO ROLLBACK -> Escalate

Example 5: OOM kill
  - Error rate: 2%
  - 1 OOM kill detected
  Score: min(calculated, 30) -> FAIL -> Escalate
```

---

*End of Recursive Quality Engine Specification*
