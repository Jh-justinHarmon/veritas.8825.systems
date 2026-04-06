# Veritas — Governed AI Answer Engine

## Why I Built This

Most RAG systems retrieve documents and generate answers, but they don't tell you how trustworthy the answer is or how much of it is backed by official documentation versus weaker sources.

I built Veritas to explore source-aware answer generation where the system tracks where information comes from, weights sources by authority, and scores how well an answer is supported by documentation.

The goal is not just to generate answers, but to show how reliable the answer is and why.

---

## What This Is

Veritas is an AI answer engine for developer documentation that:

- Retrieves information from official docs, vendor content, and community sources
- Weights sources by authority
- Generates answers with citations
- Scores answer quality and documentation coverage
- Logs runs with full trace and replay

The system is designed so answers are not just generated — they are **scored, traced, and explained**.

---

## Core Idea

Not all sources are equal.

Official documentation is more reliable than blog posts.  
Blog posts are more reliable than random forum answers.

Veritas ranks sources by authority and tracks how much of an answer is supported by high-authority sources versus low-authority ones.

The system answers the question, but it also answers a second question:

**"How much should I trust this answer?"**

---

## How It Works (High Level)

1. Documents are ingested and tagged by source tier:
   - Tier 1 — Official documentation
   - Tier 2 — Vendor blogs and examples
   - Tier 3 — Community content

2. Retrieval uses both similarity and authority:
   - 70% semantic similarity
   - 30% source authority

3. The system generates an answer with inline citations.

4. The answer is scored across four dimensions:
   - Coverage — Did we answer the question?
   - Authority — Are the sources high quality?
   - Sufficiency — Is there enough documentation to support the answer?
   - Risk — Does this answer need human review?

5. Every run is logged to a ledger so the answer can be traced and replayed.

---

## What This Demonstrates

This project demonstrates:

- Retrieval with source authority weighting
- Answer generation with citations
- Answer quality scoring
- Provenance and traceability
- Replayable runs
- Governance and execution boundaries

The focus is on building a **trustworthy answer system**, not just a chatbot.

---

## Project Structure

```
veritas/
├── backend/           # FastAPI server
├── frontend/          # React UI
├── docs/              # Architecture docs
├── corpus/            # Ingested documents (tier-tagged)
└── README.md
```

---

## Scope

This is a single-domain system focused on developer documentation.

It is designed to demonstrate:

- Source-aware retrieval
- Answer scoring
- Provenance and traceability
- Governed execution

This is not a general-purpose agent or search engine.  
It is a governed answer engine for technical documentation.

---

## What This Project Is (In One Sentence)

Veritas answers developer questions using documentation, shows its sources, and scores how much of the answer is backed by authoritative documentation.

---

## License

MIT License - See LICENSE file for details