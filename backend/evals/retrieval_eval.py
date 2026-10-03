"""Offline retrieval evaluation against the frozen golden set.

Runs every golden item carrying a synthesize-style question through
``retrieve_relevant`` in lexical-only mode (no provider calls — the
embedding path is exercised by unit tests with synthetic vectors).
Reports per-item retrieval metrics bound to the eval contract:

  - placeholder-free results
  - unique canonical documents
  - per-doc overflow justifications present when caps exceeded
  - truthful abstention on inadequate evidence

Usage:
    python3 backend/evals/retrieval_eval.py
        [--golden PATH] [--corpus PATH] [--json]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from retrieval.relevance import retrieve_relevant  # noqa: E402

DEFAULT_GOLDEN = (Path(__file__).parents[3] / "veritas-deploy"
                  / "tests" / "fixtures" / "veritas"
                  / "veritas_golden_eval_set_v1.json")
DEFAULT_CORPUS = (Path(__file__).parents[2] / "corpus" / "embeddings"
                  / "all_tiers_embedded_chunks.json")


def _question(item: dict) -> str:
    return ((item.get("input") or {}).get("payload") or {}).get(
        "question") or ""


def run_eval(golden_path: Path, corpus_path: Path,
             min_relevance: float = 0.22) -> dict:
    golden = json.loads(golden_path.read_text())
    chunks = json.loads(corpus_path.read_text())
    rows, abstained, tool_ok = [], 0, True
    for item in golden.get("items", []):
        q = _question(item)
        if not q:
            continue
        out = retrieve_relevant(q, chunks, query_embedding=None,
                                min_relevance=min_relevance)
        docs = [c["document_id"] for c in out["chunks"]]
        placeholder = [d for d in docs
                       if "quarantine" in d or "example" in d]
        dupes_without_justification = sum(
            1 for d in set(docs)
            if docs.count(d) > 2
            and not any((c.get("retrieval_meta") or {})
                        .get("overflow_justification")
                        for c in out["chunks"]
                        if c["document_id"] == d))
        row = {
            "id": item.get("id"),
            "category": item.get("category"),
            "abstained": out["abstained"],
            "returned": len(docs),
            "unique_documents": len(set(docs)),
            "placeholder_sources": placeholder,
            "dup_overflow_unjustified": dupes_without_justification,
            "best_relevance": out["confidence"]["best_relevance"],
        }
        if out["abstained"]:
            abstained += 1
        rows.append(row)
    return {
        "eval_set": golden.get("eval_set_id"),
        "mode": "lexical_only",
        "items_evaluated": len(rows),
        "items_abstained": abstained,
        "placeholder_sources_total": sum(len(r["placeholder_sources"])
                                         for r in rows),
        "unjustified_dupes_total": sum(r["dup_overflow_unjustified"]
                                       for r in rows),
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=str(DEFAULT_GOLDEN))
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = run_eval(Path(args.golden), Path(args.corpus))
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"eval_set={report['eval_set']} mode={report['mode']}")
    print(f"items={report['items_evaluated']} "
          f"abstained={report['items_abstained']} "
          f"placeholders={report['placeholder_sources_total']} "
          f"unjustified_dupes={report['unjustified_dupes_total']}")
    for r in report["rows"]:
        print(f"  {r['id']}: abstained={r['abstained']} "
              f"returned={r['returned']} uniq_docs={r['unique_documents']} "
              f"best={r['best_relevance']}")


if __name__ == "__main__":
    main()
