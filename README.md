# Veritas — A Governed AI Answer Engine for Developer Documentation

**Status:** V1 Development (Phase 0 Complete)  
**Timeline:** 10-14 days to V1 public demo  
**Positioning:** Applied AI Systems Engineer portfolio project

---

## What This Is

A governed AI answer engine for developer documentation that combines official docs, vendor examples, and community knowledge while clearly signaling source reliability and answer confidence.

**Core differentiator:** Multi-tier source classification (Docs > Blogs > Community) with transparent scoring showing how much of each answer is backed by authoritative sources versus weaker sources.

---

## Why This Matters

Most RAG demos retrieve docs and generate answers. Veritas goes further:

| Normal RAG Demo | Veritas |
|-----------------|---------|
| Retrieves docs | Authority-weighted retrieval (70% similarity + 30% authority) |
| Generates answer | Generates + cites + scores quality |
| Shows sources | Shows provenance + source tier + influence |
| No evals | 4-score eval system (coverage, authority, sufficiency, risk) |
| No logging | Ledger-backed run logging with replay |
| No governance | Execution invariants + scope enforcement |

This demonstrates **systems thinking**, not just prompt engineering.

---

## V1 Scope (Locked)

**Must Have:**
- Document ingestion with tier tagging (Tier 1: Docs, Tier 2: Blogs, Tier 3: Community)
- Authority-weighted retrieval (0.7 cosine + 0.3 authority)
- Answer generation with inline citations
- 4-score eval system (coverage, authority, documentation sufficiency, review recommendation)
- Run logging to ledger (ExecutionTransaction)
- UI: question input, answer display, sources panel, trust signals card, trace view, run history
- Demo video (2-3 minutes)

**Explicitly Excluded from V1:**
- Multi-agent orchestration
- Autonomous task execution
- Multi-user authentication
- Live web search
- Workflow builders
- Fancy memory features

---

## Tech Stack

**Backend:**
- Python + FastAPI
- 8825-v5 RetrievalEngine (authority-weighted retrieval)
- 8825-v5 ExecutionTransaction (ledger-backed provenance)
- 8825-v5 ProofProtocol (authority scoring)
- OpenAI API (embeddings + LLM)
- SQLite ledger

**Frontend:**
- React + TypeScript
- TailwindCSS
- shadcn/ui components
- Lucide icons

**Deployment:**
- Vercel (frontend)
- Railway/Render (backend)

---

## V1 Corpus

**Domain:** Developer documentation and technical content

**Source Tiers:**
- **Tier 1 (Official Docs):** Stripe API docs, Anthropic API docs, LangChain docs
- **Tier 2 (Vendor Content):** Official blog posts, official code examples, official tutorials
- **Tier 3 (Community):** GitHub issues/discussions, Stack Overflow (curated), community forums

**V1 Scope:** 2-3 doc sets, ~200-300 total documents

---

## Project Structure

```
veritas/
├── backend/           # FastAPI server + 8825-v5 integration
├── frontend/          # React UI
├── docs/              # Architecture docs, V1 spec
├── corpus/            # Ingested documents (tier-tagged)
└── README.md
```

---

## Positioning

This project demonstrates capabilities for **Applied AI Systems Engineer** roles at:
- **Anthropic:** Eval design, epistemic honesty, transparency, human oversight
- **Perplexity:** Retrieval + citations, answer quality, source ranking, product UI
- **AI Startups:** Working system (not demo), production-ready architecture, operational thinking

**One-sentence pitch:**  
"I built a source-aware AI answer engine for developer documentation that retrieves official docs, blogs, and community content, generates cited answers, and scores how much of the answer is backed by authoritative sources versus weaker sources, with full trace and replay."

---

## Governance

This project is governed by the **Veritas Project Spine v1.0** which enforces:
- V1 ships in 10-14 days
- Single-user, single-domain, single-page
- No agents, no autonomous workflows, no live web search
- Hardcoded scoring allowed, ugly UI allowed
- Working demo before polish
- Demo video is part of V1 definition of done

**Reality check:** Veritas is a career project, not an architecture project. Its job is not to be perfect. Its job is to ship and demonstrate capabilities.

---

## License

MIT License - See LICENSE file for details