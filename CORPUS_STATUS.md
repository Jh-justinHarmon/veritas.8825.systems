# Veritas Corpus Status

## Current State

**Total chunks:** 56  
**All tier 1 (docs):** 56  
**Tier 2 (practice):** 0  
**Tier 3 (failure):** 0  

**Source:** `corpus/embeddings/tier1_embedded_chunks.json`

## What This Means

**Sources sidebar will only show:**
- SPEC badges (tier 1 = docs)
- Anthropic Claude Documentation sources
- Official documentation references

**No practice or failure sources because:**
- Corpus was built from official Claude docs only
- No community practice examples ingested
- No failure case studies ingested

## To Add Tier 2/3 Sources

### Tier 2 (Practice) - Real-world implementation examples
**Potential sources:**
- Developer blog posts about Claude integration
- GitHub repos with Claude tool use examples
- Stack Overflow answers about Claude API usage
- Community guides and tutorials

### Tier 3 (Failure) - Documented failure cases
**Potential sources:**
- GitHub issues reporting Claude tool use problems
- Blog posts about debugging Claude integrations
- Post-mortems of Claude implementation challenges
- Community discussions of edge cases

## Ingestion Process

1. **Collect documents** (PDFs, markdown, text)
2. **Place in:** `corpus/raw/tier2/` or `corpus/raw/tier3/`
3. **Run ingestion:**
   ```bash
   cd backend
   python3 ingestion/process_pdf_docs.py --tier 2
   python3 ingestion/process_pdf_docs.py --tier 3
   ```
4. **Embed chunks:**
   ```bash
   python3 ingestion/embed_chunks.py --tier 2
   python3 ingestion/embed_chunks.py --tier 3
   ```
5. **Update retrieval** to load tier 2/3 chunks

## Current Limitation

**V1 Demo uses docs-only corpus.** This is sufficient to demonstrate:
- Concept-driven synthesis
- Inline citations
- Source attribution
- Multi-source integration

**For production:** Add tier 2/3 sources to provide practice examples and failure cases alongside official documentation.
