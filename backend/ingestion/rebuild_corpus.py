"""Deterministic corpus rebuild against the approved source manifest.

Reads the embedded chunk store, admits only chunks whose documents are
approved and non-placeholder per corpus/source_manifest.json, and writes
the production chunk file plus a manifest carrying corpus_version and
manifest_sha256 so downstream receipts can bind the exact corpus build.

No provider calls: existing embeddings are preserved verbatim. Sources
without approved embeddings simply never ship.

Usage:
    python3 backend/ingestion/rebuild_corpus.py --corpus-version corpus-YYYY-MM-DD-vN
"""

import argparse
import json
from pathlib import Path

from source_policy import (
    chunk_is_production_safe,
    corpus_inventory_hash,
    is_placeholder_url,
    load_source_manifest,
)

CORPUS_DIR = Path(__file__).parent.parent.parent / "corpus"
EMBEDDINGS_DIR = CORPUS_DIR / "embeddings"
CHUNKS_FILE = EMBEDDINGS_DIR / "all_tiers_embedded_chunks.json"
OUT_MANIFEST = EMBEDDINGS_DIR / "all_tiers_manifest.json"


def rebuild(corpus_version: str) -> dict:
    manifest = load_source_manifest()
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))

    admitted, rejected = [], []
    for chunk in chunks:
        if chunk_is_production_safe(chunk, manifest):
            admitted.append(chunk)
        else:
            rejected.append(chunk.get("document_id"))

    for chunk in admitted:
        if is_placeholder_url(chunk.get("url")):
            raise SystemExit(
                f"REFUSING_BUILD: placeholder URL survived admission "
                f"({chunk.get('chunk_id')})")

    inventory_hash = corpus_inventory_hash(admitted)
    CHUNKS_FILE.write_text(
        json.dumps(admitted, indent=2, ensure_ascii=False),
        encoding="utf-8")

    tier_breakdown = {}
    for chunk in admitted:
        t = chunk.get("source_tier")
        tier_breakdown[f"tier_{t}"] = tier_breakdown.get(f"tier_{t}", 0) + 1

    out_manifest = {
        "source": "Veritas corpus - manifest-approved sources only",
        "corpus_version": corpus_version,
        "manifest_sha256": inventory_hash,
        "total_chunks": len(admitted),
        "tier_breakdown": tier_breakdown,
        "embedding_model": admitted[0]["embedding_model"] if admitted else None,
        "chunks_file": "all_tiers_embedded_chunks.json",
        "source_manifest": "../source_manifest.json",
        "quarantined_document_ids": sorted(set(rejected)),
    }
    OUT_MANIFEST.write_text(
        json.dumps(out_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8")
    return out_manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-version", required=True)
    args = ap.parse_args()
    m = rebuild(args.corpus_version)
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
