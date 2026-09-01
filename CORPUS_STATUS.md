# Veritas Hiring Release — Corpus Status

**Release:** `iem-work-sample-v1`
**Status:** Deliberately not bundled
**Last reviewed:** 2026-09-01

## Current truth

This hiring release does not include raw source documents, generated embeddings, or a local corpus snapshot. Those materials are excluded because third-party redistribution rights and the relationship between the deployed corpus and the source checkout were not sufficiently clean for a hiring-facing repository.

The separately deployed demo reported 74 loaded chunks at the time of review and successfully answered the canonical query using three observed source tiers. That deployed corpus is not represented as bundled source in this branch.

## Why the corpus is excluded

- Raw third-party source content may have redistribution restrictions.
- Generated embeddings may retain source text and metadata.
- The prior repository state included placeholder/example source records.
- The prior documentation claimed 56 docs-only chunks while the live service reported 74 chunks and three tiers.
- A hiring reviewer does not need the full corpus to evaluate the product-quality and governance approach.

## Reproduction boundary

This branch is a curated source-and-scope release, not a turnkey local reproduction. Do not add unreviewed source files or private data to make it locally runnable. Any future demo corpus must use verified public excerpts or synthetic records and must update this file, `SOURCES_MANIFEST.md`, the README, and the runtime behavior together.
