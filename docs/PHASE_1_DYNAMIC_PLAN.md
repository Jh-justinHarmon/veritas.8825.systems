# Phase 1: Dynamic Ingestion — Implementation Plan

**Duration:** 2-3 days  
**Status:** Ready to start  
**Dependencies:** Site registry complete

---

## Overview

Phase 1 builds the dynamic ingestion pipeline that scrapes documentation sites on-demand, discovers tier 2/3 content, and prepares content for retrieval.

**Key difference from V1:** Instead of pre-scraped static corpus, we scrape and classify content in real-time based on user queries.

---

## Components to Build

### 1. Scraping Module (`backend/scraping/`)

**Files:**
- `scraper.py` - Main scraping orchestrator
- `sitemap_scraper.py` - Sitemap-based scraping
- `crawl_scraper.py` - Crawl-based scraping
- `html_processor.py` - HTML to markdown conversion
- `cache.py` - Scraping cache with TTL

**Scraper Interface:**
```python
class DocumentScraper:
    def scrape_site(self, site_id: str, query: str) -> List[Document]:
        """
        Scrape documentation site for content matching query.
        
        Args:
            site_id: Site identifier from registry (e.g., "anthropic")
            query: User's search query to filter relevant pages
            
        Returns:
            List of Document objects with content and metadata
        """
        pass
```

**Sitemap Strategy:**
1. Fetch sitemap.xml
2. Parse all URLs
3. Filter URLs matching query keywords (simple text match)
4. Fetch HTML for matching URLs
5. Process HTML to extract content
6. Cache results (24-hour TTL)

**Crawl Strategy:**
1. Start from docs root URL
2. Follow internal links (max depth 3)
3. Filter pages matching query keywords
4. Fetch HTML for matching pages
5. Process HTML to extract content
6. Cache results (24-hour TTL)

**HTML Processing:**
1. Use BeautifulSoup to parse HTML
2. Extract main content using selectors from site config
3. Remove nav, footer, ads using exclude selectors
4. Convert to markdown using `html2text` or `markdownify`
5. Preserve code blocks
6. Extract metadata (title, URL, last_modified from headers)

**Cache Schema (SQLite):**
```sql
CREATE TABLE scrape_cache (
    url TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    metadata JSON,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_site_expires ON scrape_cache(site_id, expires_at);
```

### 2. Tier Discovery (`backend/search/`)

**Files:**
- `tier_discovery.py` - Main tier discovery orchestrator
- `google_search.py` - Google Custom Search API integration
- `tier_classifier.py` - URL pattern-based tier classification

**Tier Discovery Flow:**
```python
class TierDiscovery:
    def discover_tier_2_3(self, site_id: str, query: str) -> List[Document]:
        """
        Discover tier 2/3 content using Google Custom Search.
        
        Args:
            site_id: Site identifier from registry
            query: User's search query
            
        Returns:
            List of Document objects with tier 2/3 content
        """
        # 1. Load site config
        # 2. Construct tier 2 search query
        # 3. Execute Google Custom Search
        # 4. Scrape result URLs
        # 5. Classify tier (2 or 3) based on URL patterns
        # 6. Return documents with tier metadata
        pass
```

**Google Custom Search Setup:**
1. Create Google Cloud project
2. Enable Custom Search API
3. Create Custom Search Engine (CSE)
4. Configure to search entire web
5. Store API key and CSE ID in `.env`

**Tier Classification Logic:**
```python
def classify_tier(url: str, site_config: dict) -> int:
    """
    Classify document tier based on URL patterns.
    
    Tier 1: Official documentation (matches tier_1_patterns)
    Tier 2: Vendor blog, research, news (vendor domain but not docs)
    Tier 3: Community (Stack Overflow, Reddit, GitHub)
    """
    # Check tier 1 patterns
    for pattern in site_config['tier_1_patterns']:
        if matches_glob(url, pattern):
            return 1
    
    # Check if vendor domain (tier 2)
    vendor_domain = extract_domain(site_config['docs_url'])
    if vendor_domain in url:
        return 2
    
    # Otherwise tier 3 (community)
    return 3
```

### 3. Embedding Cache (`backend/cache/`)

**Files:**
- `embedding_cache.py` - Embedding cache with TTL and LRU eviction

**Cache Schema (SQLite):**
```sql
CREATE TABLE embedding_cache (
    content_hash TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,
    dimension INTEGER NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1
);

CREATE INDEX idx_last_accessed ON embedding_cache(last_accessed);
```

**Cache Interface:**
```python
class EmbeddingCache:
    def get(self, content: str) -> Optional[List[float]]:
        """Get cached embedding for content (by hash)"""
        pass
    
    def set(self, content: str, embedding: List[float]):
        """Store embedding in cache"""
        pass
    
    def evict_lru(self, max_entries: int = 10000):
        """Evict least recently used entries"""
        pass
```

**Cache Strategy:**
- Hash content with SHA-256
- Check cache before calling OpenAI API
- Update `last_accessed` on cache hit
- TTL: 30 days
- LRU eviction when cache exceeds 10,000 entries

### 4. Integration with Existing Pipeline

**Update `answer_agent.py`:**
```python
def answer_question_dynamic(site_id: str, query: str) -> dict:
    """
    Answer question with dynamic content scraping.
    
    1. Scrape tier 1 docs (with cache)
    2. Discover tier 2/3 content (Google search)
    3. Chunk all content
    4. Embed chunks (with cache)
    5. Retrieve top-k (authority-weighted)
    6. Generate answer with citations
    7. Compute eval scores
    8. Return response
    """
    # Load site config
    site_config = load_site_config(site_id)
    
    # Scrape tier 1
    scraper = DocumentScraper()
    tier_1_docs = scraper.scrape_site(site_id, query)
    
    # Discover tier 2/3
    discovery = TierDiscovery()
    tier_2_3_docs = discovery.discover_tier_2_3(site_id, query)
    
    # Combine all docs
    all_docs = tier_1_docs + tier_2_3_docs
    
    # Chunk
    chunks = chunk_documents(all_docs)
    
    # Embed (with cache)
    cache = EmbeddingCache()
    for chunk in chunks:
        cached_embedding = cache.get(chunk['text'])
        if cached_embedding:
            chunk['embedding'] = cached_embedding
        else:
            embedding = generate_embedding(chunk['text'])
            chunk['embedding'] = embedding
            cache.set(chunk['text'], embedding)
    
    # Retrieve (existing code)
    query_embedding = generate_query_embedding(query)
    top_chunks = retrieve_chunks(query_embedding, chunks, top_k=6)
    
    # Generate answer (existing code)
    answer_result = generate_answer_with_citations(query, top_chunks)
    
    # Eval scoring (existing code)
    eval_result = evaluate_answer(query, answer_result['answer'], answer_result['citations'])
    
    return {
        'answer': answer_result['answer'],
        'citations': answer_result['citations'],
        'eval': eval_result,
        'sources': top_chunks
    }
```

---

## Implementation Order

### Day 1: Scraping Module
1. ✅ Create site registry (`registry.json`)
2. Build `scraper.py` base class
3. Implement `sitemap_scraper.py`
4. Implement `html_processor.py`
5. Build scraping cache (SQLite)
6. Test on Anthropic docs

### Day 2: Tier Discovery
1. Set up Google Custom Search API
2. Implement `google_search.py`
3. Implement `tier_classifier.py`
4. Build `tier_discovery.py` orchestrator
5. Test tier 2/3 discovery on Anthropic

### Day 3: Integration & Cache
1. Build embedding cache (SQLite)
2. Update `answer_agent.py` for dynamic flow
3. Test end-to-end: query → scrape → discover → chunk → embed → retrieve → answer
4. Verify cache hit rates
5. Test on multiple sites (Anthropic, OpenAI)

---

## Testing Strategy

### Unit Tests
- Sitemap parsing
- HTML content extraction
- Tier classification logic
- Cache get/set/evict

### Integration Tests
- Full scraping pipeline (sitemap + crawl)
- Tier 2/3 discovery with Google search
- Embedding cache hit/miss
- End-to-end answer generation

### Manual Tests
- Scrape Anthropic docs for "streaming"
- Discover tier 2/3 content for "Claude API best practices"
- Verify tier distribution (should have mix of 1/2/3)
- Check answer quality with dynamic content

---

## Dependencies

**Python Packages:**
```txt
beautifulsoup4==4.12.3
html2text==2024.2.26
google-api-python-client==2.122.0
lxml==5.1.0
requests==2.31.0
```

**Environment Variables:**
```bash
GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_cse_id
OPENAI_API_KEY=your_openai_key
```

**External Services:**
- Google Custom Search API ($5/1000 queries)
- OpenAI Embeddings API ($0.0001/1K tokens)

---

## Success Criteria

**Phase 1 is complete when:**
1. Can scrape Anthropic docs on-demand (with cache)
2. Can discover tier 2/3 content via Google search
3. Tier classifier correctly assigns tiers based on URLs
4. Embedding cache reduces API calls by >50%
5. End-to-end pipeline works: query → scrape → discover → chunk → embed → retrieve → answer
6. Tested on 3+ documentation sites

---

## Next Steps After Phase 1

1. **Phase 2/3:** Already complete (reuse existing code)
2. **Phase 4:** Build UI with site selector + search field
3. **Phase 5:** Deploy to Fly.io

---

**Ready to start implementation.**
