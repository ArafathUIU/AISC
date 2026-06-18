# AISC — Self-Learning Engine

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Overview

The Self-Learning Engine records every quality loop iteration across all agents, extracts patterns of success and failure, optimizes system prompts, and continuously improves agent performance over time. It is the mechanism by which AISC gets better at building software.

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────┐
│            SELF-LEARNING SERVICE (Port 8008)                │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │Iteration │   │Knowledge │   │ Pattern  │   │ Prompt  │ │
│  │Recorder  │──►│Extractor │──►│Validator │──►│Optimizer│ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────┘ │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │Context   │   │Trend     │   │Knowledge │               │
│  │Injector  │   │Analyzer  │   │  Graph   │               │
│  └──────────┘   └──────────┘   │ Updater  │               │
│                                └──────────┘               │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Learning Data Model

### 3.1 What Gets Recorded

Every recursive loop iteration across every agent captures:

| Field | Source | Purpose |
|-------|--------|---------|
| `artifact_type` | Task context | What was being produced |
| `gate_type` | Quality gate | Which quality gate applied |
| `agent_type` | Agent runtime | Which agent produced it |
| `model_used` | LLM router | Which LLM was used |
| `system_prompt_hash` | Prompt store | Which prompt version |
| `input_prompt` | Task context | What the agent was asked |
| `output_content` | Agent output | What was produced |
| `iteration_count` | Loop controller | How many iterations |
| `scores_history` | Scoring engine | Score progression |
| `final_score` | Scoring engine | Final score |
| `passed` | Quality gate | Did it pass? |
| `critiques` | Review agents | All feedback received |
| `improvements` | Improvement agent | Changes per iteration |
| `tokens_total` | LLM provider | Cost |
| `total_duration_ms` | Clock | Time spent |

---

## 4. Knowledge Extraction Pipeline

### 4.1 Batch Extraction (hourly)

```
EXTRACT_KNOWLEDGE_BATCH(hourly):
    
    // Get unprocessed learning records from last hour
    records = pg.query("""
        SELECT * FROM learning_records
        WHERE extracted_knowledge IS NULL
        AND created_at > NOW() - INTERVAL '2 hours'
        ORDER BY created_at ASC
        LIMIT 500
    """)
    
    IF records is empty: RETURN
    
    // Group by agent_type and gate_type for focused analysis
    groups = group_by(records, key: r => (r.agent_type, r.gate_type))
    
    FOR EACH (agent_type, gate_type), group_records in groups:
        
        passed = [r for r in group_records if r.passed]
        failed = [r for r in group_records if not r.passed]
        
        extraction_prompt = f"""
        Analyze these {agent_type} agent iterations for {gate_type}.
        
        PASSED ({len(passed)} records):
        {format_summary(passed, max_examples=5)}
        
        FAILED ({len(failed)} records):
        {format_summary(failed, max_examples=5)}
        
        EXTRACT PATTERNS:
        1. What distinguishes passing from failing outputs?
        2. What prompt patterns led to first-iteration passes?
        3. What common mistakes caused failures?
        4. What improvement strategies were most effective?
        5. What prompt modifications would improve success rate?
        
        OUTPUT JSON:
        {{
          "patterns": [
            {{
              "type": "success_pattern|failure_pattern|prompt_improvement",
              "description": "specific pattern",
              "confidence": 0.0-1.0,
              "support": N,
              "applicable_to": ["agent_type"],
              "prompt_modification": "specific change to make"
            }}
          ],
          "summary": {{
            "pass_rate": float,
            "avg_iterations": float,
            "avg_score": float,
            "trend": "improving|stable|declining"
          }}
        }}
        """
        
        knowledge = llm.generate(extraction_prompt, model="gpt-4o-mini")
        
        // Store extracted patterns
        FOR pattern in knowledge.patterns:
            // Qdrant: for semantic retrieval
            qdrant.upsert("knowledge_snippets", {
                id: uuid(),
                vector: embed(pattern.description, model="text-embedding-3-large"),
                payload: {
                    knowledge_type: pattern.type,
                    description: pattern.description,
                    confidence: pattern.confidence,
                    support_count: pattern.support,
                    prompt_modification: pattern.prompt_modification,
                    source_records: [r.id for r in group_records],
                    active: true,
                    created_at: now()
                }
            })
            
            // Neo4j: for relationship queries
            neo4j.merge(:LearnedPattern {
                id: uuid(),
                pattern_type: pattern.type,
                category: f"{agent_type}_{gate_type}",
                description: pattern.description,
                confidence: pattern.confidence,
                support_count: pattern.support
            })
            neo4j.create_relationships(pattern, group_records)
        
        // Mark records as processed
        pg.update("learning_records")
          .set(extracted_knowledge=knowledge)
          .where(id IN [r.id for r in group_records])
```

---

## 5. Prompt Optimization

### 5.1 Optimization Trigger

```
TRIGGER_PROMPT_OPTIMIZATION(agent_type):
    
    // Check if enough new data since last optimization
    recent_patterns = qdrant.search("knowledge_snippets", {
        filter: {
            must: [
                {key: "knowledge_type", match: {value: "prompt_improvement"}},
                {key: "active", match: {value: true}},
                {key: "applicable_to", match: {any: [agent_type]}}
            ]
        },
        limit: 20
    })
    
    IF len(recent_patterns) < 5: RETURN  // Not enough data
    
    // Check for pending prompt modifications
    pending = [p for p in recent_patterns if not p.prompt_modification_applied]
    
    IF len(pending) >= 3:
        OPTIMIZE_PROMPT(agent_type, pending)
```

### 5.2 Prompt Optimizer

```
OPTIMIZE_PROMPT(agent_type, patterns):
    
    current_prompt = load_prompt_file(f"prompts/{agent_type}.md")
    current_version = extract_version(current_prompt)
    
    optimization_prompt = f"""
    You are optimizing an AI agent's system prompt.
    
    AGENT: {agent_type}
    CURRENT PROMPT (v{current_version}):
    ```
    {current_prompt}
    ```
    
    PROPOSED IMPROVEMENTS (from learning data):
    {format_patterns_for_prompt(patterns)}
    
    TASK: Incorporate these improvements into a new version of the prompt.
    
    RULES:
    1. Preserve all existing working patterns
    2. Add new instructions only where they fill gaps
    3. Keep the prompt well-structured and scannable
    4. Do NOT increase prompt length by more than 20%
    5. Add a ## Recent Learnings section with the most impactful patterns
    6. Increment the version number
    
    OUTPUT: The complete new prompt, followed by a changelog.
    """
    
    new_prompt = llm.generate(optimization_prompt, model="claude-3.5-sonnet")
    
    // Version and store
    new_version = increment_version(current_version)  // e.g., v2.3 -> v2.4
    save_prompt_file(f"prompts/{agent_type}.md", new_prompt)
    git_commit(f"prompts/{agent_type}.md", f"v{new_version}: {summarize_changes(patterns)}")
    
    // Mark patterns as applied
    FOR pattern in patterns:
        pattern.prompt_modification_applied = true
        pattern.prompt_version = new_version
        update_in_qdrant(pattern)
        update_in_neo4j(pattern)
    
    // Emit event so agent runtime picks up new prompt
    EMIT PromptOptimized({
        agent_type: agent_type,
        prompt_version: new_version,
        patterns_incorporated: len(patterns),
        changes_summary: summarize_changes(patterns)
    })
```

---

## 6. Pattern Validation

### 6.1 Continuous Validation (daily)

```
VALIDATE_PATTERNS(daily):
    
    active_patterns = qdrant.scroll("knowledge_snippets", {
        filter: {must: [{key: "active", match: {value: true}}]}
    })
    
    FOR pattern in active_patterns:
        
        // Get recent data (last 7 days) for this pattern's domain
        recent = pg.query("""
            SELECT * FROM learning_records
            WHERE agent_type = ANY(?)
            AND gate_type = ANY(?)
            AND created_at > NOW() - INTERVAL '7 days'
        """, pattern.applicable_to, pattern.applicable_gate_types)
        
        IF len(recent) < 10: CONTINUE  // Not enough new data
        
        // Check if pattern still holds
        validation_prompt = f"""
        Validate whether this learned pattern still holds true:
        
        PATTERN: {pattern.description}
        ORIGINAL CONFIDENCE: {pattern.confidence}
        ORIGINAL SUPPORT: {pattern.support_count}
        
        RECENT DATA ({len(recent)} new records):
        {format_summary(recent, max_examples=10)}
        
        Does the pattern still hold? Has it strengthened or weakened?
        
        OUTPUT:
        {{
          "still_valid": true/false,
          "new_confidence": 0.0-1.0,
          "new_support": N (including original),
          "contradicting_count": N,
          "trend": "strengthening|stable|weakening|contradicted",
          "recommendation": "keep|increase_confidence|decrease_confidence|deactivate"
        }}
        """
        
        validation = llm.generate(validation_prompt, model="gpt-4o-mini")
        
        // Update pattern
        pattern.confidence = validation.new_confidence
        pattern.support_count = validation.new_support
        pattern.last_validated_at = now()
        
        IF validation.recommendation == "deactivate":
            pattern.active = false
            pattern.deactivated_at = now()
            pattern.deactivation_reason = "Contradicted by new data"
        
        // Persist updates
        update_in_qdrant(pattern)
        update_in_neo4j(pattern)
```

---

## 7. Context Injection

### 7.1 Pre-Task Knowledge Injection

```
INJECT_LEARNED_CONTEXT(agent_type, task_type, task_input):
    
    // 1. Find applicable patterns from knowledge graph
    patterns = neo4j.run("""
        MATCH (lp:LearnedPattern)
        WHERE lp.active = true
        AND any(agent IN lp.applicable_to WHERE agent = $agent_type)
        AND lp.confidence >= 0.70
        RETURN lp.description, lp.confidence, lp.pattern_type
        ORDER BY lp.confidence DESC
        LIMIT 10
    """, {agent_type: agent_type})
    
    // 2. Semantic search for similar successful tasks
    similar_successes = qdrant.search("agent_memory", {
        vector: embed(task_input),
        filter: {
            must: [
                {key: "agent_type", match: {value: agent_type}},
                {key: "experience_type", match: {value: "success"}},
                {key: "output_quality", range: {gte: 85}}
            ]
        },
        limit: 5
    })
    
    // 3. Retrieve most effective prompt patterns
    best_practices = qdrant.search("knowledge_snippets", {
        vector: embed(f"{agent_type} {task_type} best practices"),
        filter: {
            must: [
                {key: "knowledge_type", match: {value: "success_pattern"}},
                {key: "active", match: {value: true}},
                {key: "confidence", range: {gte: 0.75}}
            ]
        },
        limit: 5
    })
    
    // 4. Assemble injected context
    injected_context = f"""
    ## Learned Best Practices
    
    ### Patterns That Work ({len(patterns)} applied)
    {format_patterns_for_context(patterns)}
    
    ### Similar Successful Tasks
    {format_similar_tasks(similar_successes)}
    
    ### Recommended Approach
    {format_best_practices(best_practices)}
    
    Apply these patterns in your work. They have been validated across previous tasks.
    """
    
    RETURN injected_context
```

---

## 8. Learning Metrics

### 8.1 Key Performance Indicators

| Metric | Target | Measurement |
|--------|:------:|-------------|
| First-Pass Rate | Increase over time | % of artifacts passing gate on iteration 1 |
| Average Iterations to Pass | Decrease over time | Mean iterations per artifact type |
| Average Score Improvement | Positive trend | Delta between first and final iteration scores |
| Cost per Task | Decrease over time | Tokens per completed task |
| Pattern Precision | > 0.80 | % of patterns that still hold after 30 days |
| Knowledge Coverage | Increase over time | % of task types with >= 3 learned patterns |

### 8.2 Learning Dashboard

```
┌─────────────────────────────────────────────────────┐
│              Learning Effectiveness                  │
│                                                      │
│  Iterations to Pass (by week)                        │
│  W1: ████████ 4.2                                   │
│  W2: ██████ 3.8                                     │
│  W3: █████ 3.1                                      │
│  W4: ███ 2.4                                        │
│  W5: ██ 1.9                                         │
│                                                      │
│  Active Patterns: 47 (+12 this week)                 │
│  Deactivated Patterns: 8 (-3 this week)              │
│  Avg Pattern Confidence: 0.82                        │
│  Prompt Versions Deployed: 3 this week               │
│  Cost Reduction: 34% vs baseline                     │
└─────────────────────────────────────────────────────┘
```

---

## 9. Knowledge Retention & Forgetting

```
// Patterns are never deleted, only deactivated
// This allows "re-learning" if conditions change

DEACTIVATE_PATTERN_IF:
    - Confidence drops below 0.50
    - Contradicted by > 50% of recent data
    - Not observed in any successful task for 90 days

REACTIVATE_PATTERN_IF:
    - New data supports it again (confidence > 0.70)
    - Same pattern independently discovered by extraction pipeline

// Full pattern lifecycle
CREATED -> ACTIVE -> WEAKENING -> DEACTIVATED -> (REACTIVATED) -> ACTIVE
                |                                     
                └──> STRENGTHENING ──> ACTIVE (higher confidence)
```

---

## 10. Learning Pipeline Scheduling

```
EVERY 1 HOUR:
    - Record new iterations from event stream
    - Batch knowledge extraction on unprocessed records

EVERY 6 HOURS:
    - Validate active patterns against new data
    - Check if prompt optimization is needed
    - Update knowledge graph with new relationships

EVERY 24 HOURS:
    - Full pattern validation sweep
    - Deactivate contradicted patterns
    - Generate learning dashboard report
    - Clean up old, deactivated patterns (> 180 days)

ON PATTERN ACTIVATED:
    - Immediately check if prompt should be updated
    - If confidence > 0.85, auto-apply prompt modification
    - If confidence 0.70-0.85, create PR for human review
```

---

*End of Self-Learning Engine*
