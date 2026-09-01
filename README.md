# Veritas — IEM Hiring-Safe Work Sample

**Live demo:** https://veritas.8825.systems
**Hiring release branch:** `iem-work-sample-v1`
**Purpose:** A deliberately scoped AI knowledge-synthesis work sample for the IEM AI Operations Analyst application.

## Problem

AI systems can return plausible answers without making their evidence, source authority, or review risk visible. Veritas explores a narrower operational question: how can an AI answer be structured so a reviewer can see how it was constructed, which sources support it, and when the result needs additional review?

## Justin’s role

Justin scoped and built the Veritas concept, interaction model, retrieval/evaluation workflow, source-aware answer structure, and quality-measurement approach. The work sample demonstrates product and AI-operations judgment; it does not claim that every deployment or infrastructure component was built independently.

## What was built

- A single-question AI answer workflow.
- Source-aware retrieval that distinguishes source authority.
- Structured synthesis into concepts rather than a raw text dump.
- Inline citations and source inspection.
- Quality signals for coverage, authority, sufficiency, and risk.
- Logged/replayable behavior in the deployed implementation.
- A deliberately narrow V1 designed to prove the quality model before expanding scope.

## Canonical demo query

Use this query in the live demo:

> How do I implement Claude tool use with error handling?

The verified live service responded successfully on 2026-09-01 with structured ideas, three source tiers, measurable source coverage, and approximately 1.7–1.8 citations per paragraph. The live health endpoint reported 74 loaded chunks.

## Workflow

```text
Question
  → retrieval
  → source-aware context
  → structured synthesis
  → quality evaluation
  → human review when evidence or risk requires it
```

## Quality signals

- **Source authority:** official documentation is distinguished from practice and failure material.
- **Coverage:** whether the answer addresses the question.
- **Authority:** strength and relevance of supporting sources.
- **Sufficiency:** whether the available documentation is adequate.
- **Risk:** whether the answer should receive additional review.
- **Citations:** factual claims remain inspectable through source references.

## Privacy and governance choices

- No client, employer, or private 8825 source material is included in this hiring branch.
- User questions and generated traces are not persisted by the hiring-release API.
- Raw and embedded corpus material is intentionally excluded from this branch because third-party redistribution rights were not established for every source.
- The source manifest records the intended source categories, exclusions, and review status.
- The deployed demo and this source branch are treated as separate surfaces; this branch was not deployed as part of the cleanup.

## Scope and limitations

This is a source-and-documentation release for a deliberately scoped AI system. The deployed demo is a single-user V1 with a small corpus and a single interaction.

This work sample is **not**:

- An autonomous agent platform.
- Enterprise AI operations at scale.
- MLOps.
- A model-development project.
- Guaranteed hallucination prevention.
- No-human-review-required automation.
- A claim of enterprise adoption, time savings, or business ROI.
- A claim that the system includes live search, user uploads, accounts, or multi-turn history.

## Release contents

The hiring branch keeps the core application code, evaluation/scope documentation, license, and deployment configuration needed to understand the project. It excludes history, test output, screenshots, internal planning, migration/setup notes, raw third-party corpus files, generated embeddings, and local development artifacts.

The corpus is not bundled in this release. The live demo remains the executable evidence surface; the repository is the curated source and decision record. See `SOURCES_MANIFEST.md` for the exact boundary.

## Review status

- Public live demo: verified HTTP 200.
- Live health endpoint: verified healthy with 74 loaded chunks.
- Canonical query: verified successful.
- Public repository: branch created locally from `origin/main` and curated for hiring use.
- Secret scan: no obvious API keys, private keys, passwords, or credential values found in reviewed release content.
- Production deployment: not changed by this release.
- Recording: not created.
- Final case study: not created.
- IEM submission: not performed.

## Running context

The hiring branch intentionally omits the deployed corpus and is not presented as a turnkey local reproduction. Do not add private or unreviewed source material to make it run locally. Any future local demo corpus must pass source-rights, privacy, and provenance review first.

## License

See `LICENSE`. The project license does not automatically grant redistribution rights for third-party documentation or source content; those sources are therefore excluded from this hiring release unless separately cleared.
