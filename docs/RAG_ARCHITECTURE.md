# AISC — RAG Architecture

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Overview

The Retrieval-Augmented Generation (RAG) system grounds all AI agents in factual, retrievable knowledge. It prevents hallucination by providing agents with relevant context from internal and external sources before they generate outputs.

---

## 2. Pipeline Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      RAG SERVICE (Port 8006)                │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │Document  │   │Embedding │   │ Vector   │   │Context  │ │
│  │Ingestion │──►│Generation│──►│ Storage  │──►│Assembly │ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────┘ │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │Chunking  │   │Reranking │   │Citation  │               │
│  │Strategy  │   │(Cross-   │   │Generator │               │
│  │          │   │ Encoder) │   │          │               │
│  └──────────┘   └──────────┘   └──────────┘               │
└────────────────────────────────────────────────────────────┘
```

### 2.1 Query Flow

```
User/Agent Query
      │
      ▼
┌─────────────┐
│ 1. EMBED    │  Convert query to vector using embedding model
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2. RETRIEVE │  KNN search in Qdrant (top-k = 20 candidates)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 3. RERANK   │  Cross-encoder re-ranks 20 -> top-5 most relevant
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 4. ASSEMBLE │  Build context from top-5 passages + metadata
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 5. GENERATE │  LLM prompt = system_prompt + assembled_context + query
└─────────────┘
```

---

## 3. Embedding Models

| Model | Dimensions | Use Case | Hosting | Latency |
|-------|:----------:|----------|---------|:-------:|
| `all-MiniLM-L6-v2` | 768 | Code & document search | Local (CPU) | < 10ms |
| `all-mpnet-base-v2` | 768 | High-quality document search | Local (CPU) | < 20ms |
| `text-embedding-3-small` | 1536 | Agent experience memory | OpenAI API | < 100ms |
| `text-embedding-3-large` | 3072 | High-precision knowledge snippets | OpenAI API | < 200ms |

### 3.1 Model Selection Logic

```
SELECT_EMBEDDING_MODEL(collection, precision_requirement):
    IF collection == "knowledge_snippets" OR precision == "high":
        RETURN text-embedding-3-large (3072d)
    ELIF collection == "agent_memory":
        RETURN text-embedding-3-small (1536d)
    ELSE:
        RETURN all-MiniLM-L6-v2 (768d)  // Fast, local, free
```

---

## 4. Document Ingestion Pipeline

### 4.1 Chunking Strategy

```
CHUNK_DOCUMENT(document, collection_type):
    
    SWITCH collection_type:
        
        CASE "code":
            // Split by function/class boundaries
            splitter = CodeSplitter(language=detect_language(document))
            chunk_size = 512 tokens (avoid splitting mid-function)
            overlap = 64 tokens
            
        CASE "documentation":
            // Split by markdown headers
            splitter = MarkdownHeaderSplitter()
            chunk_size = 512 tokens
            overlap = 128 tokens
            
        CASE "agent_experience":
            // Split by task boundaries
            splitter = TokenSplitter()
            chunk_size = 1024 tokens
            overlap = 256 tokens
    
    chunks = splitter.split(document)
    
    FOR EACH chunk:
        chunk.metadata = {
            source: document.source,
            chunk_index: chunk.index,
            total_chunks: len(chunks),
            prev_chunk_id: chunk.id - 1,
            next_chunk_id: chunk.id + 1
        }
    
    RETURN chunks
```

### 4.2 Ingestion API

```
POST /api/v1/rag/ingest
Body:
{
  "collection": "code_embeddings",
  "documents": [
    {
      "content": "async def create_user(...)",
      "metadata": {
        "artifact_id": "uuid",
        "file_path": "services/auth/src/routes/users.py",
        "language": "python",
        "type": "function",
        "tags": ["auth", "user", "crud"]
      }
    }
  ],
  "options": {
    "chunk_size": 512,
    "overlap": 64,
    "embedding_model": "all-MiniLM-L6-v2"
  }
}

Response:
{
  "ingested": 3,
  "chunks_created": 12,
  "collection": "code_embeddings",
  "duration_ms": 450
}
```

### 4.3 Deduplication Strategy

```
BEFORE ingestion:
    content_hash = sha256(chunk.content)
    existing = qdrant.search(
        collection=collection,
        query_filter={must: [{key: "content_hash", match: {value: content_hash}}]},
        limit=1,
        score_threshold=0.99
    )
    IF existing:
        SKIP (already ingested)
        UPDATE metadata only (tags, timestamps)
```

---

## 5. Retrieval & Reranking

### 5.1 Retrieval Query

```
POST /api/v1/rag/query
Body:
{
  "query": "How to authenticate users in FastAPI with JWT?",
  "collections": ["code_embeddings", "doc_embeddings"],
  "limit": 20,
  "filters": {
    "language": "python",
    "tags": ["auth", "jwt"]
  },
  "score_threshold": 0.7,
  "rerank": true,
  "rerank_top_k": 5
}

Response:
{
  "results": [
    {
      "collection": "code_embeddings",
      "score": 0.94,
      "content": "async def login(...)",
      "metadata": {
        "file_path": "services/auth/src/routes/auth.py",
        "type": "function",
        "tags": ["auth", "jwt", "login"]
      }
    }
  ],
  "query_duration_ms": 85,
  "rerank_duration_ms": 45
}
```

### 5.2 Cross-Encoder Reranking

```
RERANK(query, candidates, top_k):
    
    // Cross-encoder: sentence-transformers/ms-marco-MiniLM-L-6-v2
    pairs = [(query, candidate.content) for candidate in candidates]
    scores = cross_encoder.predict(pairs)
    
    // Sort by cross-encoder score (descending)
    ranked = sort_by_score(candidates, scores, descending=true)
    
    // Apply diversity penalty (avoid near-duplicate passages)
    diverse = apply_mmr(ranked, diversity_lambda=0.7)
    
    RETURN diverse[:top_k]
```

### 5.3 Maximum Marginal Relevance (MMR)

```
APPLY_MMR(passages, lambda=0.7):
    selected = [passages[0]]  // Always take highest-scored first
    remaining = passages[1:]
    
    WHILE len(selected) < top_k AND len(remaining) > 0:
        FOR passage in remaining:
            relevance = passage.score
            max_similarity = max(cosine_similarity(passage.embedding, s.embedding) for s in selected)
            mmr_score = lambda * relevance - (1 - lambda) * max_similarity
        best = argmax(mmr_score)
        selected.append(remaining.pop(best))
    
    RETURN selected
```

---

## 6. Context Assembly

### 6.1 Assembly Algorithm

```
ASSEMBLE_CONTEXT(query_results, max_tokens=8000):
    
    context = []
    token_count = 0
    
    // Priority ordering:
    // 1. High-precision knowledge snippets
    // 2. Directly relevant code
    // 3. Related documentation
    // 4. Similar agent experiences
    
    FOR passage in query_results (sorted by score):
        
        formatted = f"""
        [Source: {passage.metadata.file_path or passage.metadata.title}]
        [Type: {passage.metadata.type}]
        [Relevance: {passage.score:.2f}]
        
        {passage.content}
        
        ---
        """
        
        passage_tokens = estimate_tokens(formatted)
        IF token_count + passage_tokens > max_tokens:
            BREAK
        
        context.append(formatted)
        token_count += passage_tokens
    
    assembled = "\n".join(context)
    
    RETURN assembled
```

### 6.2 Agent Prompt Injection

```
BUILD_AGENT_PROMPT(agent_type, task_type, user_query, rag_context):

    system_prompt = load_prompt(agent_type)
    
    assembled_prompt = f"""
    {system_prompt}
    
    ## Relevant Context from Knowledge Base
    
    {rag_context}
    
    ## Task
    
    {user_query}
    
    Use the context above to inform your response. Cite sources when using specific information.
    """
    
    RETURN assembled_prompt
```

---

## 7. Collections & Indexing

### 7.1 Collection Configuration

| Collection | Dims | HNSW m | HNSW ef_construct | ef_search |
|------------|:----:|:------:|:-----------------:|:---------:|
| code_embeddings | 768 | 16 | 100 | 50 |
| doc_embeddings | 768 | 16 | 100 | 50 |
| agent_memory | 1536 | 16 | 100 | 50 |
| test_embeddings | 768 | 16 | 100 | 50 |
| security_findings | 768 | 16 | 100 | 50 |
| error_patterns | 768 | 16 | 100 | 50 |
| knowledge_snippets | 3072 | 32 | 200 | 100 |

### 7.2 Index Maintenance

```
MAINTAIN_INDICES (runs nightly):
    FOR EACH collection:
        // Check index health
        info = qdrant.get_collection(collection)
        
        // Optimize if fragmentation > 20%
        IF info.optimizers_status.fragmentation > 0.20:
            qdrant.update_collection(collection, optimize=True)
        
        // Rebuild if too many deleted vectors
        IF info.points_count > 100000 AND info.indexed_vectors_count / info.points_count < 0.95:
            qdrant.recreate_index(collection)
            qdrant.reindex(collection, batch_size=500)
```

---

## 8. Source Categories

### 8.1 Internal Sources (auto-ingested)

| Source | Collection | Trigger | Priority |
|--------|-----------|---------|----------|
| Generated source code | code_embeddings | On artifact approved | High |
| PRDs, Architecture docs | doc_embeddings | On artifact approved | High |
| API specifications | doc_embeddings | On artifact approved | Medium |
| Test files | test_embeddings | On testing gate passed | Medium |
| Security reports | security_findings | On security gate passed | High |
| Error logs (for learning) | error_patterns | On incident resolved | Medium |
| Agent task outcomes | agent_memory | On task completed | High |
| Learning extractions | knowledge_snippets | On knowledge extracted | High |

### 8.2 External Sources (on-demand)

| Source | Method | Collection | Cache TTL |
|--------|--------|-----------|:---------:|
| Framework documentation | Web fetch + parse | doc_embeddings | 24 hours |
| API reference docs | Web fetch + parse | doc_embeddings | 7 days |
| Research papers | Semantic Scholar API | doc_embeddings | 30 days |
| CVE database | NVD API | security_findings | 24 hours |
| Stack Overflow (high-quality) | API + filter by score | code_embeddings | 7 days |

---

## 9. Quality Monitoring

### 9.1 RAG Performance Metrics

| Metric | Target | Measurement |
|--------|:------:|-------------|
| Retrieval Precision@5 | > 0.85 | Human evaluation of top-5 results |
| Retrieval Recall@20 | > 0.90 | % of relevant docs in top-20 |
| MRR (Mean Reciprocal Rank) | > 0.80 | Rank of first relevant result |
| Query Latency P95 | < 200ms | End-to-end query time |
| Ingestion Throughput | > 100 docs/s | Documents per second |
| Index Freshness | < 60s | Time from artifact creation to searchable |

### 9.2 Feedback Loop

```
ON agent completes task:
    // Agent self-reports whether RAG context was helpful
    feedback = {
        query: original_query,
        results_used: [result_ids the agent actually referenced],
        helpfulness: 1-5,
        hallucination_detected: boolean
    }
    
    STORE feedback for RAG quality improvement
    
    // If hallucination detected:
    IF feedback.hallucination_detected:
        FLAG the retrieval for human review
        WEAKEN the embedding weights of misleading passages
```

---

*End of RAG Architecture*
