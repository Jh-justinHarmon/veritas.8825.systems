# Veritas Architecture V2 — Dynamic Multi-Site Documentation System

**Status:** Active (Pivot from V1 static corpus)  
**Date:** 2026-04-06  
**Rationale:** Claude already has "Ask Docs" for their own documentation. Veritas differentiates by working on ANY documentation site with live scraping and automatic tier discovery.

---

## Core Concept

**Veritas V2 is a meta-documentation system that:**
1. Works on multiple documentation sites (Anthropic, OpenAI, Stripe, etc.)
2. Scrapes official docs on-demand (Tier 1)
3. Automatically discovers vendor blogs and community content (Tier 2/3)
4. Generates cited answers with authority-weighted retrieval
5. Shows trust signals (coverage, authority, sufficiency, risk scores)

**Demo value:** "I built a system that works on ANY docs site" vs "I copied Claude's existing feature"

---

## User Flow

```
1. User opens Veritas
   └─> Sees dropdown: "Select documentation site"
       Options: Anthropic Claude, OpenAI, Stripe, Supabase, etc.

2. User selects site (e.g., "Anthropic Claude")
   └─> Background shows blurred screenshot of Claude docs
   └─> Search field appears: "What do you want to learn about?"

3. User types query: "How do I use streaming with the API?"
   └─> Loading state: "Searching official docs, blogs, and community..."

4. System executes:
   a. Scrapes official docs matching query (Tier 1)
   b. Searches vendor blog for related posts (Tier 2)
   c. Searches Stack Overflow + Reddit (Tier 3)
   d. Chunks all content (512 tokens)
   e. Generates embeddings (cached if seen before)
   f. Retrieves top-k chunks (authority-weighted)
   g. Generates answer with inline citations [1][2][3]
   h. Computes eval scores (coverage, authority, sufficiency, risk)

5. User sees:
   └─> Answer with inline citations
   └─> Sources panel with tier badges (Docs / Blog / Community)
   └─> Trust signals card (4 scores + review recommendation)
   └─> Click citation → Modal with full source content

6. User can:
   └─> Ask follow-up questions (same site context)
   └─> Switch to different documentation site
   └─> Review sources in modal
```

---

## Architecture Layers

### Layer 1: Site Registry & Scraping

**Site Registry** (`backend/sites/registry.json`):
```json
{
  "anthropic": {
    "name": "Anthropic Claude",
    "docs_url": "https://docs.anthropic.com",
    "scraping_strategy": "sitemap",
    "sitemap_url": "https://docs.anthropic.com/sitemap.xml",
    "tier_1_patterns": ["docs.anthropic.com/en/*"],
    "tier_2_search": "site:anthropic.com/news OR site:anthropic.com/research",
    "tier_3_search": "site:stackoverflow.com OR site:reddit.com/r/ClaudeAI"
  },
  "openai": {
    "name": "OpenAI",
    "docs_url": "https://platform.openai.com/docs",
    "scraping_strategy": "crawl",
    "tier_1_patterns": ["platform.openai.com/docs/*"],
    "tier_2_search": "site:openai.com/blog",
    "tier_3_search": "site:stackoverflow.com openai OR site:reddit.com/r/OpenAI"
  }
}
```

**Scraping Module** (`backend/scraping/scraper.py`):
- **Strategy 1: Sitemap-based** - Parse sitemap.xml, fetch all URLs
- **Strategy 2: Crawl-based** - Start from root, follow internal links (max depth 3)
- **Strategy 3: Search-based** - Use site-specific search API if available
- **Output:** Raw HTML per page
- **Caching:** Store scraped content with TTL (24 hours)

**HTML Processing** (`backend/scraping/html_processor.py`):
- Extract main content (strip nav, footer, ads)
- Convert to markdown
- Preserve code blocks
- Extract metadata (title, URL, last_modified)

### Layer 2: Tier Classification & Discovery

**Tier Classifier** (`backend/ingestion/tier_classifier.py`):
```python
def classify_tier(url: str, site_config: dict) -> int:
    """
    Tier 1: Official documentation (matches tier_1_patterns)
    Tier 2: Vendor blog, research, news (tier_2_search results)
    Tier 3: Community (Stack Overflow, Reddit, GitHub issues)
    """
    if matches_pattern(url, site_config['tier_1_patterns']):
        return 1
    elif is_vendor_domain(url, site_config):
        return 2
    else:
        return 3
```

**Tier 2/3 Discovery** (`backend/search/tier_discovery.py`):
- **Google Custom Search API** for tier 2/3 content
- Query construction: `{user_query} {tier_2_search}` or `{user_query} {tier_3_search}`
- Fetch top 10 results per tier
- Scrape content from result URLs
- Classify tier based on URL patterns

### Layer 3: Chunking & Embedding (Reused from V1)

**Chunking** (`backend/ingestion/chunker.py`):
- Same as V1: 512 tokens per chunk, 50 token overlap
- Preserve tier metadata in each chunk
- Store source URL, title, tier

**Embedding** (`backend/ingestion/embedder.py`):
- Same as V1: OpenAI `text-embedding-3-small`
- **NEW: Embedding Cache** (`backend/cache/embedding_cache.db`):
  ```sql
  CREATE TABLE embeddings (
    content_hash TEXT PRIMARY KEY,
    embedding BLOB,
    created_at TIMESTAMP,
    last_accessed TIMESTAMP
  );
  ```
- Check cache before calling OpenAI API
- TTL: 30 days, LRU eviction

### Layer 4: Retrieval & Answer Generation (Reused from V1)

**Semantic Retrieval** (`backend/retrieval/simple_retriever.py`):
- Same as V1: Cosine similarity + authority weighting
- Formula: `0.7 * cosine_similarity + 0.3 * tier_weight`
- Tier weights: Tier 1=1.0, Tier 2=0.7, Tier 3=0.4
- Return top-k chunks (k=6)

**Answer Generation** (`backend/agents/answer_agent.py`):
- Same as V1: GPT-4o-mini with prompt template
- Inline citations `[1][2][3]`
- Citations map to source chunks

### Layer 5: Eval Scoring (Reused from V1)

**Scoring Module** (`backend/evals/scoring.py`):
- Same 4 dimensions:
  1. **Coverage:** % of sentences with citations
  2. **Authority:** Tier-weighted average
  3. **Sufficiency:** Answer completeness heuristics
  4. **Risk:** Hallucination detection
- Overall score: 30% coverage + 20% authority + 30% sufficiency + 20% risk
- Review recommendation: Flag if any score < threshold

### Layer 6: API & UI

**FastAPI Backend** (`backend/api/server.py`):
```python
@app.post("/ask")
async def ask_question(request: AskRequest):
    """
    1. Load site config
    2. Scrape Tier 1 docs (or use cache)
    3. Search Tier 2/3 (Google Custom Search)
    4. Chunk + embed (with cache)
    5. Retrieve top-k
    6. Generate answer
    7. Compute eval scores
    8. Return response
    """
    pass

@app.get("/sites")
async def list_sites():
    """Return available documentation sites"""
    pass
```

**React Frontend** (`frontend/src/`):
- **Site Selector:** Dropdown with site logos
- **Search Field:** With blurred background (site screenshot)
- **Results Display:**
  - Answer with inline citations
  - Sources panel with tier badges
  - Trust signals card (4 scores)
- **Source Modal:** Full source content on citation click

---

## Data Flow

```
User Query: "How do I use streaming with the API?"
    ↓
Site Config: Load Anthropic config
    ↓
Tier 1 Scraping: Fetch docs.anthropic.com pages matching "streaming"
    ↓
Tier 2/3 Discovery: Google search for blog posts + Stack Overflow
    ↓
HTML Processing: Extract content, convert to markdown
    ↓
Tier Classification: Assign tier 1/2/3 based on URL
    ↓
Chunking: Split into 512-token chunks
    ↓
Embedding: Generate embeddings (check cache first)
    ↓
Retrieval: Top-6 chunks (authority-weighted)
    ↓
Answer Generation: GPT-4o-mini with citations
    ↓
Eval Scoring: Compute 4 dimensions
    ↓
Response: Return answer + sources + scores
```

---

## What's Reused from V1

✅ **Chunking logic** - Works on any text  
✅ **Embedding generation** - Same OpenAI API  
✅ **Semantic retrieval** - Same algorithm  
✅ **Authority weighting** - Still tier-based  
✅ **Answer generation** - Same prompt structure  
✅ **Eval scoring** - All 4 dimensions  
✅ **Citation system** - Still inline `[1][2][3]`

---

## What's New in V2

🆕 **Live scraping** - On-demand content fetching  
🆕 **Multi-site support** - Works on any docs site  
🆕 **Tier classifier** - Automatic tier assignment  
🆕 **Tier 2/3 discovery** - Google Custom Search integration  
🆕 **Embedding cache** - SQLite with TTL  
🆕 **Site selector UI** - Dropdown with blurred background  
🆕 **Source modal** - Deep-dive on citations

---

## Implementation Phases (Updated)

### Phase 0: Planning ✓
- Architecture V2 design
- Site registry schema
- Updated project spine

### Phase 1: Dynamic Ingestion (NEW)
**Duration:** 2-3 days

**Deliverables:**
- Site registry with 3-5 documentation sites
- Scraping module (sitemap + crawl strategies)
- HTML processor (extract content, convert to markdown)
- Tier classifier (URL pattern matching)
- Tier 2/3 discovery (Google Custom Search API)
- Embedding cache (SQLite)

**Test:** Scrape Anthropic docs, discover tier 2/3 content, classify tiers

### Phase 2: Answer Generation ✓
**Duration:** Already complete (reuse from V1)

**Deliverables:**
- Semantic retrieval with authority weighting
- Answer generation with inline citations
- All existing code works with dynamic content

### Phase 3: Eval Scoring ✓
**Duration:** Already complete (reuse from V1)

**Deliverables:**
- Coverage, authority, sufficiency, risk scores
- Review recommendations
- All existing code works with dynamic content

### Phase 4: UI
**Duration:** 2-3 days

**Deliverables:**
- Site selector dropdown
- Search field with blurred background
- Answer display with inline citations
- Sources panel with tier badges
- Trust signals card (4 scores)
- Source modal for citation deep-dive

### Phase 5: Deployment
**Duration:** 1-2 days

**Deliverables:**
- Deploy to Fly.io
- Public URL
- Demo video (2-3 minutes)

---

## V1 Definition of Done (Updated)

**Can you record a 2-3 minute demo showing:**
1. Open the app at a public URL ✓
2. Select a documentation site from dropdown (e.g., "Anthropic Claude") 🆕
3. Ask a question: "How do I use streaming with the API?" ✓
4. System shows answer with inline citations ✓
5. System shows sources grouped by tier (Docs / Blog / Community) ✓
6. System shows trust signal (4 eval scores) ✓
7. Click a citation → Modal opens with full source 🆕
8. Switch to different site (e.g., "OpenAI") → Ask new question 🆕
9. Explain: "This works on any documentation site" 🆕
10. Repo is public with README ✓

---

## Technical Decisions

### Why Google Custom Search API?
- **Pros:** Reliable, fast, supports site-specific queries
- **Cons:** Costs $5/1000 queries (demo budget: ~$10)
- **Alternative:** Scrape Google results (fragile, against ToS)

### Why SQLite for embedding cache?
- **Pros:** Simple, no external dependencies, fast for demo scale
- **Cons:** Not distributed (fine for V1)
- **Alternative:** Redis (overkill for demo)

### Why sitemap vs crawl?
- **Sitemap:** Fast, complete, respects site structure
- **Crawl:** Fallback for sites without sitemap
- **Both:** Support both strategies

### Why 24-hour cache TTL?
- **Docs change slowly:** Most docs updated weekly/monthly
- **Demo constraint:** Don't want to re-scrape every query
- **User expectation:** "Fresh enough" for demo

---

## Success Metrics

**Technical:**
- Scraping works on 3+ documentation sites
- Tier 2/3 discovery returns relevant results
- Embedding cache hit rate > 50%
- Answer generation < 10 seconds end-to-end

**Demo:**
- Can switch between sites seamlessly
- Sources show clear tier distribution
- Trust signals accurately reflect answer quality
- Modal provides useful source deep-dive

**Portfolio:**
- "Works on any docs site" is clear differentiator
- Live scraping demonstrates systems thinking
- Tier discovery shows search/classification skills
- Clean UI matches modern documentation UX

---

## Next Steps

1. **Implement Phase 1 (Dynamic Ingestion):**
   - Create site registry with Anthropic + OpenAI configs
   - Build scraping module with sitemap strategy
   - Implement tier classifier
   - Integrate Google Custom Search API
   - Build embedding cache

2. **Test with existing Phase 2/3 code:**
   - Verify retrieval works with dynamic content
   - Verify answer generation works
   - Verify eval scoring works

3. **Build Phase 4 UI:**
   - Site selector dropdown
   - Search field with blurred background
   - Results display with sources + scores
   - Source modal

4. **Deploy and demo**

---

**This architecture makes Veritas a portfolio standout, not a clone of existing tools.**
