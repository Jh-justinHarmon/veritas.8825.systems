# Veritas V2 Architecture — Refined (Constrained Realism)

**Status:** Active  
**Date:** 2026-04-07  
**Refinement:** Shifted from live scraping to curated multi-site system

---

## Core Positioning

**Veritas is a curated understanding system for technical documentation.**

Not:
- A docs chatbot
- A live web scraper
- An answer validation tool

But:
- A system that combines documentation, blog insights, and real-world experience into structured, source-aware explanations

---

## Key Insight: Constrained Realism

**User perception:** "This works across multiple sites and topics dynamically"  
**System reality:** Pre-loaded, high-quality slices per site × topic

**Why this works:**
- Feels dynamic to the user ✅
- Actually deterministic under the hood ✅
- No scraping failures ❌
- No latency spikes ❌
- No API/search dependency ❌

**We're simulating breadth while proving depth.**

---

## Product Experience

### 1. Site Selection
**Dropdown:** 3 sites
- Anthropic (LLM API)
- LangChain (Framework/orchestration)
- Stripe (Developer platform)

**Why these 3:**
- Domain diversity (not 3 similar APIs)
- Strong documentation ecosystems
- Clear tier 2/3 availability

### 2. Topic Selection
**Dropdown:** 3 topics per site (not free text)

**Anthropic:**
- Streaming responses
- Tool use / function calling
- Rate limits

**LangChain:**
- RAG / retrieval basics
- Agents vs chains
- Tools integration

**Stripe:**
- Webhooks
- Idempotency
- Payment intents

**Why constrained topics:**
- Guarantees good retrieval
- Avoids demo failure
- Shows intentional curation

### 3. Answer Display (3-Layer Structure)

**NEW: Structured explanation format**

```
[Core Answer] — Specification
(Tier 1 dominant)
Clear, correct explanation of how it works
Citations: [1][2]
Tag: 🟢 Docs-backed

[Implementation Insight] — In Practice
(Tier 2 dominant)
What this means in real usage
Simplifies or reframes docs
Citations: [3]
Tag: 🔵 In practice

[Common Pitfalls] — Real-World Issues
(Tier 3 dominant)
Where developers get stuck
Edge cases and gotchas
Citations: [4][5]
Tag: ⚫ Common issues
```

**Example:**
```
How streaming works in Claude:

[Core Answer]
Streaming returns tokens incrementally using Server-Sent Events (SSE). 
The API sends delta events as tokens are generated... [1][2]

[Implementation Insight]
In practice, you'll want to buffer partial responses and handle 
incomplete JSON objects until the stream completes... [3]

[Common Pitfalls]
Developers often forget to handle connection drops mid-stream, 
which can leave the UI in an inconsistent state... [4]
```

### 4. Source Contribution (Visual)

**NEW: Source contribution bar**

```
Source Contribution
Docs        ██████████ 70%
Blog        ████░░░░░░ 20%
Community   ██░░░░░░░░ 10%
```

**Inline citation markers:**
- [1] 🟢 Docs
- [3] 🔵 Blog
- [4] ⚫ Community

### 5. Trust Card (Multi-Source Aware)

**Updated trust card:**

```
Trust Signal
-------------------------
Coverage     ████████░░ 82%
Authority    High (Docs-led)
Contribution Balanced (Docs + supporting context)
Sufficiency  ✅ Docs sufficient
Review       🟢 Looks good
-------------------------
```

**NEW: Contribution Quality metric**

Based on source mix:
- **Docs-led** (Docs ≥ 70%): ✅ Docs-led, well-supported
- **Balanced** (Docs 40-70%): ⚠️ Mixed authority
- **Weak grounding** (Docs < 40%): ❌ Weak grounding

### 6. Source Modal

Click citation → Modal opens with:
- Full source text
- Tier badge
- Source metadata (URL, date, author)
- Relevance highlight (which part was cited)

---

## Data Strategy

**Per site × topic:**
- Tier 1 (Docs): 3-5 chunks
- Tier 2 (Blog): 2-3 sources
- Tier 3 (Community): 2-3 sources

**Total data requirement:**
- 3 sites × 3 topics = 9 combinations
- ~8 sources per combination
- **~70 total sources**

**Manageable, controlled, high-signal.**

---

## Architecture Layers

### Layer 1: Site & Topic Registry

**File:** `backend/sites/registry_v2.json`

```json
{
  "sites": {
    "anthropic": {
      "id": "anthropic",
      "name": "Anthropic Claude",
      "topics": {
        "streaming": {
          "id": "streaming",
          "name": "Streaming responses",
          "tier_1_sources": [...],
          "tier_2_sources": [...],
          "tier_3_sources": [...]
        },
        "tool_use": {...},
        "rate_limits": {...}
      }
    },
    "langchain": {...},
    "stripe": {...}
  }
}
```

### Layer 2: Chunking & Embedding (Reused from V1)

- Same 512-token chunking
- Same OpenAI embeddings
- Tier metadata preserved
- **NEW: Pre-compute all embeddings** (no runtime API calls)

### Layer 3: Retrieval (Reused from V1)

- Same authority-weighted retrieval
- Formula: `0.7 * cosine_similarity + 0.3 * tier_weight`
- Tier weights: T1=1.0, T2=0.6, T3=0.3

**NEW: Always retrieve from all 3 tiers**
- Not fallback logic
- Tier 2/3 are interpretation layers, not backup sources

### Layer 4: Answer Generation (NEW 3-Layer Format)

**Prompt structure:**

```
You are generating a structured technical explanation.

Context chunks (with tier labels):
[Tier 1] {chunk_1}
[Tier 2] {chunk_2}
[Tier 3] {chunk_3}

Generate answer in 3 sections:

1. Core Answer (use Tier 1 primarily)
   - Explain the specification/mechanism
   - Cite sources with [1][2]

2. Implementation Insight (use Tier 2)
   - Explain practical usage
   - Simplify or reframe docs
   - Cite sources with [3]

3. Common Pitfalls (use Tier 3)
   - Surface real-world issues
   - Edge cases developers hit
   - Cite sources with [4][5]

Each section should be 2-3 sentences.
```

### Layer 5: Eval Scoring (Updated)

**Coverage** (unchanged):
- % of sentences with citations

**Authority** (refined):
- Weighted average of cited sources
- Docs=1.0, Blog=0.6, Community=0.3

**NEW: Contribution Balance**:
- Docs ≥ 70% → "Docs-led"
- Docs 40-70% → "Balanced"
- Docs < 40% → "Weak grounding"

**Sufficiency** (reinterpreted):
- Docs alone answer question?
- YES → "Docs sufficient, additional context provided"
- NO → "Requires multi-source synthesis"

**Risk** (unchanged):
- Hallucination detection
- Citation density
- Hedging language

### Layer 6: API & UI

**FastAPI Backend:**

```python
@app.post("/ask")
async def ask_question(site_id: str, topic_id: str):
    """
    1. Load pre-chunked, pre-embedded sources for site × topic
    2. Retrieve top-k chunks (all 3 tiers)
    3. Generate 3-layer answer
    4. Compute contribution balance
    5. Return structured response
    """
    pass

@app.get("/sites")
async def list_sites():
    """Return 3 available sites"""
    pass

@app.get("/topics/{site_id}")
async def list_topics(site_id: str):
    """Return 3 topics for site"""
    pass
```

**React Frontend:**

Components:
- `SiteSelector` - Dropdown with site logos
- `TopicSelector` - Dropdown with 3 topics
- `AnswerDisplay` - 3-layer structured format
- `SourceContribution` - Visual bar chart
- `TrustCard` - Multi-source aware metrics
- `SourceModal` - Citation deep-dive

---

## Demo Narrative (2-Minute Script)

### 0:00 — Opening

"Anthropic is ahead of most — their Ask Docs feature retrieves documentation and generates grounded answers with citations directly from their docs."

### 0:10 — The Gap

"But those answers are grounded only in official documentation — they don't incorporate blog insights or real-world developer experience, and you don't see how different types of sources contribute to the explanation."

### 0:20 — Introduce Veritas

"Veritas combines documentation, blog insights, and community experience into a curated, source-aware explanation."

### 0:30 — Interaction

Select: Anthropic → Streaming responses

"Let's ask about streaming responses."

### 0:40 — Walk the 3-Layer Output

Point to Core Answer:
"You get the specification from official docs..."

Point to Implementation Insight:
"...practical guidance from blog posts..."

Point to Common Pitfalls:
"...and real-world issues from the community."

### 0:50 — Source Contribution

Point to bar:
"This answer is primarily grounded in official documentation, but incorporates supporting context from blog and community sources."

### 1:00 — Trust Card

"And you can see exactly how trustworthy this explanation is — coverage, authority, contribution balance."

### 1:10 — Source Modal

Click citation → modal opens

"Every claim is traceable to its exact source."

### 1:20 — Generalization

Switch: Anthropic → LangChain

"This isn't specific to one system — it works across different documentation ecosystems."

### 1:30 — Close

"Veritas doesn't just give you an answer — it shows you how to understand it."

### 1:40 — Final Line

"Because answer quality isn't the same as answer trustworthiness."

---

## What's Reused from V1

✅ Chunking logic  
✅ Embedding generation  
✅ Semantic retrieval  
✅ Authority weighting  
✅ Citation system  
✅ Eval scoring (coverage, authority, sufficiency, risk)

---

## What's New in V2 Refined

🆕 **Constrained realism** - Pre-loaded slices, not live scraping  
🆕 **3-layer answer format** - Core/Implementation/Pitfalls  
🆕 **Source contribution** - Visual bar + inline markers  
🆕 **Contribution balance** - New trust metric  
🆕 **Topic selection** - Dropdown, not free text  
🆕 **Always use all tiers** - Not fallback logic

---

## Implementation Phases (Updated)

### Phase 0: Planning ✓
- Architecture V2 Refined
- Site & topic selection
- 3-layer answer format design

### Phase 1: Data Curation (2 days)
**Deliverables:**
- 9 topic datasets (3 sites × 3 topics)
- ~70 sources total (docs + blog + community)
- Pre-chunked and embedded
- Stored in `corpus/curated/`

**Structure:**
```
corpus/curated/
  anthropic/
    streaming/
      tier1_docs.json
      tier2_blog.json
      tier3_community.json
    tool_use/
      ...
  langchain/
    ...
  stripe/
    ...
```

### Phase 2: Answer Generation (1 day)
**Deliverables:**
- 3-layer prompt template
- Answer generation with structured sections
- Citation mapping per layer
- Test on all 9 topics

### Phase 3: Eval Scoring (1 day)
**Deliverables:**
- Contribution balance metric
- Updated trust card logic
- Source contribution calculation
- Test on all 9 topics

### Phase 4: UI (2-3 days)
**Deliverables:**
- Site selector dropdown
- Topic selector dropdown
- 3-layer answer display
- Source contribution bar
- Updated trust card
- Source modal

### Phase 5: Deployment (1 day)
**Deliverables:**
- Deploy to Fly.io
- Public URL
- Demo video (2 minutes)

**Total: 7-9 days**

---

## Success Metrics

**Technical:**
- All 9 topics have high-quality answers
- Contribution balance accurately reflects source mix
- Trust card visually clear in <2 seconds

**Demo:**
- Can switch between sites seamlessly
- 3-layer format feels curated, not generated
- Source contribution is visually obvious
- Trust signals accurately reflect answer quality

**Portfolio:**
- "Curated understanding system" is clear differentiator
- Multi-source synthesis demonstrates systems thinking
- Clean UI matches modern documentation UX
- Positioning vs Anthropic Ask Docs is credible

---

## Key Invariants

1. **Tier 2/3 inform, never override Tier 1**
2. **Always retrieve from all 3 tiers** (not fallback)
3. **Contribution balance must be visible** (not hidden metric)
4. **3-layer format is mandatory** (not optional)
5. **Topics are constrained** (no free text for V1)

---

## Final Positioning

**One-liner:**
"Veritas combines documentation, blog insights, and real-world experience into curated, source-aware explanations for technical topics."

**Differentiation from Anthropic Ask Docs:**
"Anthropic gives you grounded answers from documentation — Veritas shows you how understanding emerges across documentation, blogs, and real-world experience."

**Category:**
Not "docs chatbot" — **"Curated knowledge system for developers"**

---

**This architecture makes Veritas a portfolio standout by demonstrating product thinking, not just technical capability.**
