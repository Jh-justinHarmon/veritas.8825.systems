# Veritas — Governed AI Answer Engine

**🌐 Live Demo:** [https://veritas.8825.systems](https://veritas.8825.systems)  
**📦 Repository:** [github.com/Jh-justinHarmon/veritas.8825.systems](https://github.com/Jh-justinHarmon/veritas.8825.systems)

---

## Why I Built This

Most RAG systems retrieve documents and generate answers, but they collapse documentation, blogs, and real-world experience into a single answer, so you can’t see how that answer was constructed.

I built Veritas to explore a different approach: answers should show how understanding is constructed across different types of sources, not just what the answer is.

---

## What This Is

Veritas is a governed AI answer engine for developer documentation that:

- Retrieves from official docs, vendor content, and community sources  
- Treats sources differently based on their role and authority  
- Generates answers with citations  
- Structures answers by source type  
- Logs runs so answers can be traced and replayed  

The system does not just generate answers — it shows how the answer is constructed, and what each source contributes to that understanding.

---

## Core Idea

Not all sources play the same role.

- Official docs define what is true  
- Blogs and examples show how it’s used  
- Community content shows where it breaks  

Most systems mix these together.

Veritas keeps them separate and makes their roles explicit.

The goal is not just to answer the question, but to show:

**how the answer emerges from different types of knowledge**

---

## How Answers Are Structured

Each answer is broken into three layers:

- **Core Answer** — what is defined in official documentation  
- **Implementation Insight** — how it is used in practice  
- **Common Pitfalls** — where developers run into issues  

This mirrors how developers actually learn: first what the system does, then how to use it, then where it breaks.

---

## How It Works

1. Documents are ingested and tagged by source tier:
   - Tier 1 — Official documentation  
   - Tier 2 — Vendor blogs and examples  
   - Tier 3 — Community content  

2. Retrieval combines similarity and authority:
   - 70% semantic similarity  
   - 30% source authority  

3. The system generates a structured answer with citations.

4. The answer is scored across four dimensions:
   - Coverage — did we answer the question  
   - Authority — how strong the sources are  
   - Sufficiency — whether documentation is enough  
   - Risk — whether the answer needs review  

5. Every run is logged so it can be inspected and replayed.

---

## What This Demonstrates

This project demonstrates:

- Source-aware retrieval instead of similarity-only retrieval  
- Structured answer generation across source types  
- Explicit answer scoring  
- Provenance and traceability  
- Replayable runs  

The focus is not the model.  
The focus is **how answers are constructed and grounded**.

---

## Scope

This is a deliberately scoped V1:

- Single domain (developer documentation)  
- Small corpus (a few doc sets)  
- Single-user  
- No agents, no workflows, no live search  

The goal is to ship a working system quickly, not build a full platform.

---

## Deployment

**Production:** Deployed on Fly.io with Cloudflare DNS

- **Primary URL:** [https://veritas-8825-systems.fly.dev](https://veritas-8825-systems.fly.dev)
- **Custom Domain:** [https://veritas.8825.systems](https://veritas.8825.systems)
- **Health Check:** [/api/health](https://veritas-8825-systems.fly.dev/api/health)
- **Region:** Dallas (dfw)
- **Auto-scaling:** Enabled (scales to zero when idle)
- **Cost:** $0-5/month

### Tech Stack

- **Backend:** Flask + Gunicorn (Python 3.9)
- **Frontend:** React + Vite + TailwindCSS
- **Deployment:** Fly.io (Docker)
- **DNS:** Cloudflare
- **Retrieval:** OpenAI embeddings + semantic search
- **Synthesis:** OpenAI GPT-4

---

## Project Structure

```
veritas/
├── backend/           # Flask API server
│   ├── agents/        # Synthesis agent
│   ├── ingestion/     # Document processing & embedding
│   ├── retrieval/     # Semantic search
│   └── app.py         # Main API
├── frontend/          # React + Vite UI
│   ├── src/
│   │   ├── pages/     # Home page
│   │   ├── api/       # API client
│   │   └── adapters/  # Data transformation
│   └── tests/         # Playwright E2E tests
├── corpus/            # Tier-tagged documents & embeddings
├── fly.toml           # Fly.io deployment config
├── Dockerfile         # Production container
└── README.md
```

---

## What This Project Is (In One Sentence)

Veritas answers developer questions using documentation, blogs, and real-world experience, and shows how each source contributes to your understanding, not just the final answer.
