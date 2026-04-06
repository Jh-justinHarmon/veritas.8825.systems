# Veritas V1 Architecture

**Version:** 1.0  
**Date:** April 6, 2026  
**Status:** Phase 0 Complete

---

## System Overview

Veritas is a governed AI answer engine that retrieves developer documentation from multiple source tiers, generates cited answers, evaluates answer quality, and provides full execution trace and replay.

**Core Innovation:** Multi-tier source classification with transparent authority scoring.

---

## Architecture Diagram

```
User Question (UI)
      ↓
[Question Input Handler]
      ↓
[RetrievalEngine] → Authority-weighted search (0.7 cosine + 0.3 authority)
      ↓
Retrieved Documents (with tier metadata)
      ↓
[Answer Generation Agent] → Generate with inline citations
      ↓
Answer + Citations
      ↓
[Eval Scoring System] → 4 scores (coverage, authority, sufficiency, risk)
      ↓
[ExecutionTransaction] → Commit to ledger with provenance
      ↓
[ProofProtocol] → Update authority scores
      ↓
[UI] → Display answer + sources + evals + trace
```

---

## Data Flow

### 1. Document Ingestion (Phase 1)

**Input:** Raw documents (HTML, Markdown, PDF)

**Process:**
1. Scrape/download documents
2. Tag with source tier (Tier 1/2/3)
3. Extract metadata (source_name, url, title, date)
4. Chunk documents (512 tokens, 64 overlap)
5. Embed chunks (OpenAI embeddings)
6. Store in artifact store with tier metadata

**Output:** Chunked documents with tier tags in artifact store

**Critical invariant:** Tier metadata must be preserved through entire pipeline

---

### 2. Retrieval (Phase 1)

**Input:** User question (text)

**Process:**
1. Embed question (OpenAI embeddings)
2. Vector search across all chunks (cosine similarity)
3. Score each chunk: `score = (0.7 * cosine_similarity) + (0.3 * authority_score)`
4. Authority score based on tier: Tier 1 = 1.0, Tier 2 = 0.7, Tier 3 = 0.4
5. Return top K chunks (K=6 for V1)

**Output:** Ranked list of chunks with tier metadata

**Why authority-weighted:** Ensures high-quality sources rank higher even with slightly lower semantic similarity

---

### 3. Answer Generation (Phase 2)

**Input:** Question + retrieved chunks

**Process:**
1. Format prompt with question and chunks
2. Instruct model to cite sources with [1], [2], etc.
3. Generate answer (Claude or GPT-4)
4. Extract citations from answer text
5. Map citation numbers to source documents

**Output:** Answer text + citation mappings

**Allowed shortcuts for V1:**
- Simple prompt template (no fancy chain-of-thought)
- Hardcoded citation extraction (regex-based)
- No citation validation (trust model output)

---

### 4. Eval Scoring (Phase 3)

**Input:** Answer + citations + source documents

**Process:**

**Score 1: Coverage Score**
```python
coverage_score = cited_sentences / total_sentences
```

**Score 2: Authority Score**
```python
authority_score = (
    (tier1_citations * 1.0) + 
    (tier2_citations * 0.6) + 
    (tier3_citations * 0.3)
) / total_citations
```

**Score 3: Documentation Sufficiency**
```python
if all_citations_tier1:
    sufficiency = "Docs Sufficient"
elif any_citations_tier3:
    sufficiency = "Docs Insufficient"
else:
    sufficiency = "Docs Partial"
```

**Score 4: Review Recommendation**
```python
review_needed = (
    coverage_score < 0.7 OR
    authority_score < 0.6 OR
    sufficiency == "Docs Insufficient"
)
```

**Output:** 4 scores + review flag

**Allowed shortcuts for V1:**
- Simple sentence splitting (split on `. `)
- Hardcoded thresholds (0.7, 0.6)
- No ML-based scoring

---

### 5. Run Logging (Phase 3)

**Input:** Question + answer + citations + scores + sources

**Process:**
1. Create ExecutionTransaction
2. Log to SQLite ledger (append-only)
3. Store run metadata (timestamp, model, retrieval count, scores)
4. Update ProofProtocol authority scores

**Output:** Run ID + ledger entry

**Why ledger-backed:** Enables replay, audit, and authority score updates based on usage

---

### 6. UI Display (Phase 4-5)

**Components:**

**Main Answer Screen:**
- Question input
- Answer text with inline citations
- Sources panel (tier badges, snippets)
- Trust signals card (4 scores)

**Trace View:**
- Retrieval step (docs retrieved, tier distribution)
- Generation step (model used, duration)
- Eval step (scores computed)
- Logging step (run ID)

**Run History:**
- List of past runs
- Click to replay

**Output:** Interactive UI showing full execution context

---

## Component Integration

### Integration with 8825-v5

**Existing components used:**

1. **RetrievalEngine** (`8825-v5/runtime/core/retrieval/retrieval_engine.py`)
   - Authority-weighted retrieval already implemented
   - Modify to use tier-based authority scores

2. **ExecutionTransaction** (`8825-v5/runtime/core/transaction/`)
   - Ledger-backed provenance already implemented
   - Use for run logging

3. **ProofProtocol** (`8825-v5/runtime/core/proof/proof_protocol.py`)
   - Authority scoring from usage signals already implemented
   - Use for updating source authority over time

**New components needed:**

1. **Answer Generation Agent** (`backend/agents/answer_agent.py`)
   - Prompt template
   - Citation extraction
   - Citation mapping

2. **Eval Scoring Module** (`backend/evals/scoring.py`)
   - 4 scoring functions
   - Review recommendation logic

3. **React Frontend** (`frontend/`)
   - Question input
   - Answer display
   - Sources panel
   - Trust card
   - Trace view
   - Run history

---

## Scoring Logic Details

### Coverage Score

**Purpose:** How much of the answer is backed by sources?

**Calculation:**
```python
def compute_coverage_score(answer_text: str, citations: list) -> float:
    sentences = answer_text.split('. ')
    cited_sentences = [s for s in sentences if has_citation(s)]
    return len(cited_sentences) / len(sentences)
```

**Thresholds:**
- 0.9+ = Excellent
- 0.7-0.9 = Good
- 0.5-0.7 = Partial
- <0.5 = Insufficient

---

### Authority Score

**Purpose:** What portion of the answer is backed by high-authority sources?

**Calculation:**
```python
def compute_authority_score(citations: list) -> float:
    tier_weights = {1: 1.0, 2: 0.6, 3: 0.3}
    weighted_sum = sum(tier_weights[c.tier] for c in citations)
    return weighted_sum / len(citations)
```

**Thresholds:**
- 0.8+ = Docs-backed
- 0.5-0.8 = Mixed authority
- <0.5 = Community-reliant

---

### Documentation Sufficiency

**Purpose:** Did official docs fully answer the question?

**States:**
- **Docs Sufficient:** All citations from Tier 1
- **Docs Partial:** Mix of Tier 1 and Tier 2
- **Docs Insufficient:** Required Tier 3 sources

**Why this matters:** Signals when official documentation is incomplete

---

### Review Recommendation

**Purpose:** Should a human review this answer?

**Logic:**
```python
def should_review(coverage: float, authority: float, sufficiency: str) -> bool:
    return (
        coverage < 0.7 or
        authority < 0.6 or
        sufficiency == "Docs Insufficient"
    )
```

---

## Data Models

### Document

```python
{
    "id": "stripe_webhooks_001",
    "source_tier": 1,  # 1=Docs, 2=Blogs, 3=Community
    "source_name": "Stripe API Documentation",
    "url": "https://stripe.com/docs/webhooks",
    "title": "Webhooks - Stripe Documentation",
    "date": "2026-03-15",
    "content": "...",
    "chunks": [
        {
            "chunk_id": "stripe_webhooks_001_chunk_0",
            "text": "...",
            "embedding": [0.1, 0.2, ...],
            "source_tier": 1  # Inherited from parent
        }
    ]
}
```

### Answer

```python
{
    "question": "How do I implement webhooks in Stripe?",
    "answer_text": "To implement webhooks in Stripe, you need to...[1]",
    "citations": [
        {
            "number": 1,
            "document_id": "stripe_webhooks_001",
            "chunk_id": "stripe_webhooks_001_chunk_0",
            "source_tier": 1,
            "source_name": "Stripe API Documentation"
        }
    ],
    "scores": {
        "coverage": 0.92,
        "authority": 0.85,
        "sufficiency": "Docs Sufficient",
        "review_needed": false
    },
    "run_id": "run_abc123",
    "timestamp": "2026-04-06T05:00:00Z"
}
```

---

## Technology Choices

### Why FastAPI (Backend)
- Fast, modern Python framework
- Built-in async support
- Easy integration with 8825-v5 components

### Why React + TypeScript (Frontend)
- Industry standard for AI product UIs
- Type safety reduces bugs
- Rich ecosystem (TailwindCSS, shadcn/ui)

### Why SQLite (Ledger)
- Append-only ledger pattern
- No external database needed
- Easy to replay and audit

### Why OpenAI Embeddings
- High quality, well-tested
- Fast API
- Cost-effective for V1 corpus size

---

## V1 Constraints

**What we're NOT building:**

- ❌ Multi-agent orchestration
- ❌ Autonomous workflows
- ❌ Live web search
- ❌ Multi-user auth
- ❌ Advanced reranking
- ❌ Custom embedding models

**What we ARE building:**

- ✅ Single-user, single-domain answer engine
- ✅ Fixed corpus (no live search)
- ✅ Simple scoring (hardcoded thresholds)
- ✅ Functional UI (ugly is fine)
- ✅ Working demo (polish later)

---

## Success Criteria

**V1 is DONE when:**

1. Can record 2-3 minute demo video showing:
   - Ask question about developer docs
   - System shows answer with inline citations
   - System shows sources grouped by tier
   - System shows trust signal (Docs sufficient/partial/insufficient)
   - Open trace panel
   - Explain how system works

2. App is live at public URL

3. Repo is public with README

4. Demo video is published

**Timeline:** 10-14 days from Phase 0 start

---

## Next Steps

**Phase 1 (2-3 days):** Corpus ingestion + retrieval
**Phase 2 (2-3 days):** Answer generation + citations
**Phase 3 (2 days):** Eval scoring + run logging
**Phase 4 (3-4 days):** Core UI
**Phase 5 (2 days):** Trace + history
**Phase 6 (2 days):** Demo + launch
