# Manual Curation Guide for V1

For V1, we're manually curating Claude documentation content to unblock Phase 1 quickly.

## Why Manual Curation for V1

The Anthropic docs site uses JavaScript rendering, which requires headless browser scraping (Selenium/Playwright). For a 10-14 day V1 timeline, manual curation is faster and demonstrates the same capabilities.

**V1 allows shortcuts:** "Manual scraping is fine" (from Veritas spine)

## How to Curate

1. Visit https://docs.anthropic.com/en/docs/[page]
2. Copy the main content text
3. Create a JSON file in this directory with the format below
4. Run the chunking script to process

## JSON Format

```json
{
  "id": "claude_docs_[page_name]",
  "source_tier": 1,
  "source_name": "Anthropic Claude Documentation",
  "url": "https://docs.anthropic.com/en/docs/[page]",
  "title": "[Page Title]",
  "date": "2026-04-06",
  "content": "[Full page content text here]",
  "curated_at": "2026-04-06T01:00:00Z"
}
```

## Priority Pages for V1 (10-15 docs)

**Core API:**
- intro
- api
- models (Claude 3 Opus, Sonnet, Haiku)
- messages (basic API usage)
- streaming
- authentication

**Advanced Features:**
- tool-use
- prompt-engineering
- vision (if available)

**Operations:**
- rate-limits
- errors
- best-practices

## V2 Enhancement

Automated scraping with Playwright can be added in V2 once V1 is shipped and demo'd.
