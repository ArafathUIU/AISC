# AISC — Self-Healing Engine

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Overview

The Self-Healing Engine autonomously detects, diagnoses, and repairs production failures. It closes the loop from monitoring to recovery, producing validated patches deployed via canary without human intervention for known failure patterns.

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────┐
│              SELF-HEALING SERVICE (Port 8009)               │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │ Failure  │   │   RCA    │   │  Patch   │   │  Patch  │ │
│  │ Detector │──►│  Engine  │──►│Generator │──►│Validator│ │
│  └──────────┘   └──────────┘   └──────────┘   └────┬────┘ │
│                                                     │      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────▼────┐ │
│  │Pattern   │◄──│ Incident │◄──│ Canary   │◄──│ Deploy  │ │
│  │Recognizer│   │ Recorder │   │ Monitor  │   │  Patch  │ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Incident Lifecycle

```
DETECTED -> ANALYZING -> PATCHING -> VALIDATING -> DEPLOYING -> RESOLVED
    |           |            |           |             |            |
    |           |            |           |             |            |
    └─── Any stage can ESCALATE to human ──────────────┘
```

### 3.1 Incident Severity vs Auto-Fix Policy

| Severity | Auto-Fix? | Conditions |
|----------|:---------:|------------|
| CRITICAL | No | Immediate escalation. Data integrity or security at risk. |
| HIGH | Conditional | Auto-fix only if RCA confidence >= 90% AND pattern is known |
| MEDIUM | Yes | Auto-fix if RCA confidence >= 70% |
| LOW | Yes | Auto-fix with canary deployment |

---

## 4. Root Cause Analysis Engine

### 4.1 RCA Process

```
PERFORM_RCA(incident):
    
    // 1. Gather evidence
    logs = query_elk(
        service: incident.service_name,
        time_range: [incident.detected_at - 5min, incident.detected_at + 5min],
        level: "ERROR|CRITICAL",
        limit: 100
    )
    
    metrics = query_prometheus(
        service: incident.service_name,
        time_range: [incident.detected_at - 15min, incident.detected_at + 5min],
        metrics: ["error_rate", "latency", "cpu", "memory", "db_connections"]
    )
    
    traces = query_jaeger(
        service: incident.service_name,
        time_range: [incident.detected_at - 5min, incident.detected_at + 5min],
        min_duration_ms: 1000,
        status: "error"
    )
    
    // 2. Query knowledge graph for similar incidents
    similar_incidents = neo4j.run("""
        MATCH (i:Incident {service_name: $service})
        WHERE i.severity = $severity OR i.error_type = $error_type
        MATCH (i)-[:CAUSED_BY]->(bug:Bug)
        MATCH (bug)-[:AFFECTS]->(api:APIEndpoint)
        MATCH (api)<-[:IMPLEMENTS_API]-(file:SourceFile)
        RETURN i, bug, file
        ORDER BY i.detected_at DESC
        LIMIT 10
    """)
    
    // 3. Semantic search for similar error patterns
    similar_errors = qdrant.search(
        collection: "error_patterns",
        query_vector: embed(incident.description + incident.error_message),
        limit: 5,
        score_threshold: 0.75
    )
    
    // 4. LLM-powered RCA
    rca_prompt = f"""
    You are a senior SRE performing root cause analysis.
    
    INCIDENT: {incident.title}
    SERVICE: {incident.service_name}
    ERROR: {incident.error_message}
    
    LOGS (sample):
    {format_logs(logs[:20])}
    
    METRICS AT TIME OF INCIDENT:
    {format_metrics(metrics)}
    
    ERROR TRACES:
    {format_traces(traces[:10])}
    
    SIMILAR PAST INCIDENTS:
    {format_similar(similar_incidents[:5])}
    
    SIMILAR ERROR PATTERNS:
    {format_patterns(similar_errors[:3])}
    
    ANALYZE AND OUTPUT:
    {{
      "root_cause": "specific technical root cause",
      "confidence": 0.0-1.0,
      "affected_code": "file:line",
      "evidence": ["evidence point 1", "evidence point 2"],
      "is_known_pattern": true/false,
      "similar_incident_ids": ["uuid"],
      "suggested_fix": "specific fix approach"
    }}
    """
    
    rca = llm.generate(rca_prompt, model="claude-3.5-sonnet")
    
    RETURN rca
```

---

## 5. Patch Generation

### 5.1 Patch Generator

```
GENERATE_PATCH(incident, rca):
    
    // Read the affected source code
    affected_code = pg.query("""
        SELECT content FROM artifacts
        WHERE id IN (
            SELECT artifact_id FROM artifact_links
            WHERE child_artifact_id = (SELECT id FROM artifacts WHERE file_path = ?)
        )
        ORDER BY version DESC LIMIT 1
    """, rca.affected_code)
    
    patch_prompt = f"""
    You are a senior developer fixing a production bug.
    
    ROOT CAUSE: {rca.root_cause}
    CONFIDENCE: {rca.confidence}
    AFFECTED CODE: {rca.affected_code}
    
    CURRENT CODE:
    ```python
    {affected_code}
    ```
    
    SUGGESTED FIX APPROACH: {rca.suggested_fix}
    
    REQUIREMENTS:
    1. Produce a minimal, focused fix
    2. Do NOT refactor unrelated code
    3. Add proper error handling
    4. Include a regression test that reproduces the bug and verifies the fix
    5. Include a rollback plan
    
    OUTPUT:
    {{
      "patch_description": "one-line summary",
      "code_diff": "unified diff",
      "affected_files": ["file1", "file2"],
      "regression_test": "test code that reproduces the issue",
      "rollback_plan": "steps to roll back",
      "risk_assessment": "low|medium|high",
      "risk_rationale": "explanation"
    }}
    """
    
    patch = llm.generate(patch_prompt, model="claude-3.5-sonnet")
    
    RETURN patch
```

### 5.2 Patch Quality Requirements

```
PATCH_MUST:
    - Pass all existing tests
    - Include a new regression test that:
        - Reproduces the exact error without the fix
        - Passes with the fix applied
    - Pass security scan (bandit): zero new HIGH/CRITICAL
    - Pass secret scan: zero new findings
    - Not decrease test coverage
    - Not change any public API signatures (unless the bug requires it)
    - Be minimal: change as few lines as possible
```

---

## 6. Patch Validation

### 6.1 Validation Pipeline

```
VALIDATE_PATCH(patch):
    
    results = {}
    
    // 1. Apply patch in sandbox
    sandbox = create_sandbox()
    sandbox.apply_patch(patch.code_diff)
    
    // 2. Run existing test suite
    test_result = sandbox.run_tests()
    IF not test_result.all_passed:
        RETURN {status: "REJECTED", reason: "Existing tests fail", details: test_result.failures}
    
    // 3. Verify regression test reproduces bug
    sandbox.revert_patch()
    regress_result = sandbox.run_test(patch.regression_test)
    IF regress_result.passed:
        RETURN {status: "REJECTED", reason: "Regression test does NOT reproduce the bug"}
    
    // 4. Verify regression test passes with fix
    sandbox.apply_patch(patch.code_diff)
    fix_result = sandbox.run_test(patch.regression_test)
    IF not fix_result.passed:
        RETURN {status: "REJECTED", reason: "Fix does not resolve the issue"}
    
    // 5. Security scan
    security_result = sandbox.run_bandit()
    IF security_result.new_critical or security_result.new_high:
        RETURN {status: "REJECTED", reason: "Patch introduces security vulnerability"}
    
    // 6. Secret scan
    secret_result = sandbox.run_secret_scan()
    IF secret_result.findings > 0:
        RETURN {status: "REJECTED", reason: "Patch contains secrets"}
    
    // 7. Coverage check
    coverage_before = get_current_coverage()
    coverage_after = sandbox.get_coverage()
    IF coverage_after.line_pct < coverage_before.line_pct:
        RETURN {status: "REJECTED", reason: "Coverage decreased"}
    
    RETURN {
        status: "VALIDATED",
        test_results: test_result,
        security_scan: security_result,
        coverage: coverage_after
    }
```

---

## 7. Autonomous Deployment

### 7.1 Canary Deployment Flow

```
DEPLOY_PATCH_AUTONOMOUSLY(patch, incident):
    
    // Only auto-deploy if confidence high enough
    IF incident.rca.confidence < 0.70:
        ESCALATE for human review
        RETURN
    
    // 1. Create PR with explanation
    pr = github.create_pr(
        title: f"[AUTO-FIX] {patch.patch_description}",
        body: f"""
        ## Automated Patch
        
        **Incident**: {incident.title}
        **Root Cause**: {incident.rca.root_cause}
        **RCA Confidence**: {incident.rca.confidence:.0%}
        
        ### Changes
        {patch.code_diff}
        
        ### Regression Test
        {patch.regression_test}
        
        ### Rollback Plan
        {patch.rollback_plan}
        
        ---
        *Generated by AISC Self-Healing Engine*
        """,
        branch: f"auto-fix/incident-{incident.id}"
    )
    
    // 2. Auto-merge if high confidence
    IF incident.rca.confidence >= 0.90:
        github.merge_pr(pr.number)
    ELSE:
        // Wait for CI to pass, then auto-merge
        WAIT for CI checks to pass (timeout: 10 min)
        IF ci_passed:
            github.merge_pr(pr.number)
        ELSE:
            ESCALATE: "CI failed on auto-fix PR"
            RETURN
    
    // 3. Build and deploy canary (10% traffic)
    deployment = deploy_canary(
        service: incident.service_name,
        image_tag: f"fix-{incident.id}",
        traffic_percent: 10
    )
    
    // 4. Monitor canary for 5 minutes
    canary_result = monitor_canary(deployment, duration_seconds=300)
    
    // 5. Decision
    IF canary_result.stable:
        // Promote to 100% in 25% increments
        promote_canary(deployment, increments=[25, 50, 100])
        
        // Observe full deployment for 10 minutes
        full_result = monitor_deployment(deployment, duration_seconds=600)
        
        IF full_result.stable:
            INCIDENT.resolve()
            EMIT PatchDeployed
        ELSE:
            ROLLBACK deployment
            EMIT PatchRolledBack
            ESCALATE: "Patch caused degradation after full promotion"
    ELSE:
        ROLLBACK deployment
        EMIT PatchRolledBack
        ESCALATE: "Patch caused degradation in canary"
```

### 7.2 Canary Health Criteria

```
MONITOR_CANARY(deployment, duration_seconds):
    
    metrics = {
        error_rate_max: 0.01,         // < 1% errors
        p95_latency_max_increase: 0.20, // < 20% increase
        health_check_min: 0.99,       // > 99% health
        oom_kills: 0,                 // No OOM
        crash_loops: 0                // No crash loops
    }
    
    FOR check every 10 seconds for duration_seconds:
        current = query_prometheus(deployment.service, deployment.canary_pods)
        
        FOR metric, threshold in metrics:
            IF violates_threshold(current[metric], threshold):
                RETURN {stable: false, violating_metric: metric}
    
    RETURN {stable: true}
```

---

## 8. Pattern Recognition

### 8.1 Recurring Failure Detection

```
DETECT_PATTERNS (runs daily):
    
    recent_incidents = pg.query("""
        SELECT * FROM incidents
        WHERE created_at > NOW() - INTERVAL '30 days'
    """)
    
    // Cluster by: (service_name, error_type, root_cause_signature)
    clusters = group_by(recent_incidents, 
        key: incident => (incident.service_name, extract_error_class(incident.error_message))
    )
    
    FOR EACH cluster WHERE count >= 3:
        pattern = {
            pattern_type: "recurring_failure",
            service: cluster.service_name,
            error_class: cluster.error_type,
            occurrence_count: len(cluster),
            time_span_days: cluster.last.detected_at - cluster.first.detected_at,
            average_resolution_time_ms: avg([i.resolved_at - i.detected_at for i in cluster]),
            suggested_prevention: GENERATE_PREVENTION_SUGGESTION(cluster)
        }
        
        // Store in knowledge graph
        neo4j.create(:LearnedPattern {
            pattern_type: "recurring_failure",
            confidence: min(0.95, cluster.count / 10),
            description: pattern.suggested_prevention,
            source: "self-healing-engine"
        })
        
        // Emit for learning
        EMIT PatternIdentified(pattern)
```

---

## 9. Self-Healing Confidence Scoring

| Factor | Weight | Impact |
|--------|:------:|--------|
| RCA confidence | 30% | LLM's self-assessed confidence |
| Similar past incidents fixed | 25% | How many identical patterns were fixed before |
| Patch validation results | 25% | All tests pass, security clean |
| Code change size | 10% | Smaller diffs = higher confidence |
| Affected service criticality | 10% | Non-critical services = higher auto-fix tolerance |

```
AUTO_FIX_SCORE = 
    rca_confidence * 0.30 +
    similar_fix_success_rate * 0.25 +
    patch_validation_score * 0.25 +
    (1 - normalized_diff_size) * 0.10 +
    (1 - service_criticality) * 0.10

IF AUTO_FIX_SCORE >= 0.80:
    AUTO_DEPLOY
ELIF AUTO_FIX_SCORE >= 0.60:
    CREATE_PR + REQUEST_HUMAN_APPROVAL
ELSE:
    ESCALATE_FULLY
```

---

*End of Self-Healing Engine*
