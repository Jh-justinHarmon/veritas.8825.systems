"""Relevance-gated hybrid retrieval for Veritas (hardening).

Replaces the tier-quota retriever. Pipeline order is the contract:

  1. hybrid relevance = embedding cosine + lexical keyphrase overlap
  2. minimum relevance floor — chunks below it never reach scoring
  3. near-duplicate suppression (embedding + token overlap)
  4. per-document cap with recorded justification for overflow
  5. authority (tier) as a bounded reranker among relevant survivors —
     it can reorder near-equal relevance but never substitute for it
  6. truthful abstention when no evidence survives the floor

Every returned chunk carries a ``retrieval_meta`` trace (scores, tier,
document id, dedup/overflow decisions) so a synthesized answer can be
audited chunk-by-chunk back to the source manifest.
"""

import math
import re
from typing import Dict, List, Optional

# Minimum hybrid relevance a chunk must reach before tier weighting is
# even considered. Observed vs proposed distinction is preserved: these
# are proposed thresholds from the frozen eval contract, tunable via
# function args, not empirical claims.
DEFAULT_MIN_RELEVANCE = 0.22
# Above this floor the answer is confident; below it we still answer but
# flag low_confidence, and with zero survivors we abstain outright.
DEFAULT_ABSTAIN_SCORE = 0.0  # abstain when nothing survives the floor
MAX_CHUNKS_PER_DOC = 2
NEAR_DUP_COSINE = 0.97
NEAR_DUP_JACCARD = 0.85
EMBEDDING_WEIGHT = 0.65
LEXICAL_WEIGHT = 0.35
# Authority may shift rank by at most this much — it reranks relevant
# survivors, never pulls an irrelevant tier-1 over a relevant tier-3.
TIER_RERANK_MAX = 0.04

TIER_AUTHORITY = {1: 1.0, 2: 0.7, 3: 0.4}

_STOP = frozenset("""
a an the and or of to in for on with is are was were be been by at from
that this it its as do does did not no but if then than so such what why
how when where which who whom can could should would will may might
claude api docs documentation anthropic
""".split())

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_\-]*")


def _tokens(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower())
            if t not in _STOP and len(t) > 1]


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def lexical_score(query: str, text: str, title: str = "") -> float:
    """Deterministic keyphrase relevance: query-term coverage weighted by
    term frequency in the chunk, title matches boosted. No provider."""
    q_terms = _tokens(query)
    if not q_terms:
        return 0.0
    body = _tokens(text)
    title_toks = set(_tokens(title))
    if not body:
        return 0.0
    tf = {}
    for t in body:
        tf[t] = tf.get(t, 0) + 1
    coverage = 0.0
    for qt in set(q_terms):
        if qt in tf:
            # saturating term frequency + title boost
            coverage += min(1.0, tf[qt] / 3.0) + (0.5 if qt in title_toks else 0.0)
    return min(1.0, coverage / len(set(q_terms)))


def _canonical_doc(chunk: Dict) -> str:
    return str(chunk.get("document_id")
               or chunk.get("source_name")
               or chunk.get("chunk_id")
               or "")


def retrieve_relevant(
    query: str,
    all_chunks: List[Dict],
    query_embedding: Optional[List[float]] = None,
    top_k: int = 10,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
    max_per_doc: int = MAX_CHUNKS_PER_DOC,
) -> Dict:
    """Relevance-first hybrid retrieval with dedup and truthful abstention.

    ``query_embedding`` may be None (offline eval / degraded mode) — the
    pipeline then runs lexical-only, which is a weaker but deterministic
    relevance signal and is reported as such in the trace.
    """
    q_tokens = set(_tokens(query))
    scored = []
    dropped_floor = 0
    for chunk in all_chunks:
        text = chunk.get("text") or ""
        sim = _cosine(query_embedding, chunk.get("embedding")) \
            if query_embedding else 0.0
        lex = lexical_score(query, text, chunk.get("title") or "")
        relevance = (EMBEDDING_WEIGHT * sim + LEXICAL_WEIGHT * lex) \
            if query_embedding else lex
        if relevance < min_relevance:
            dropped_floor += 1
            continue
        tier = int(chunk.get("source_tier") or 3)
        scored.append({
            "chunk": chunk,
            "similarity": sim,
            "lexical": lex,
            "relevance": relevance,
            "tier": tier,
            "authority": TIER_AUTHORITY.get(tier, 0.4),
            "doc": _canonical_doc(chunk),
            "tokens": set(_tokens(text)),
        })

    # Near-duplicate suppression: keep the higher-relevance twin.
    scored.sort(key=lambda s: s["relevance"], reverse=True)
    survivors, dropped_dup = [], 0
    for cand in scored:
        dup = False
        for kept in survivors:
            emb_dup = (query_embedding is not None
                       and _cosine(cand["chunk"].get("embedding") or [],
                                   kept["chunk"].get("embedding") or [])
                       >= NEAR_DUP_COSINE)
            if emb_dup or _jaccard(cand["tokens"], kept["tokens"]) \
                    >= NEAR_DUP_JACCARD:
                dup = True
                break
        if dup:
            dropped_dup += 1
            continue
        survivors.append(cand)

    # Per-document cap. Overflow is only admitted to fill otherwise-empty
    # slots and is recorded with a justification — never silently.
    doc_counts: Dict[str, int] = {}
    selected, overflow = [], []
    for item in survivors:
        if doc_counts.get(item["doc"], 0) < max_per_doc:
            doc_counts[item["doc"]] = doc_counts.get(item["doc"], 0) + 1
            selected.append(item)
        else:
            overflow.append(item)
    justifications = []
    if len(selected) < top_k and overflow:
        for item in overflow[: top_k - len(selected)]:
            item = dict(item)
            item["overflow_justification"] = (
                "top_k unfilled by unique documents; extra chunk from "
                f"document {item['doc']} chunk_index "
                f"{item['chunk'].get('chunk_index')}")
            justifications.append(item["overflow_justification"])
            selected.append(item)

    # Authority rerank: bounded shift within survivors only.
    for item in selected:
        item["final_score"] = (
            item["relevance"] + TIER_RERANK_MAX * item["authority"])
    selected.sort(key=lambda s: s["final_score"], reverse=True)
    selected = selected[:top_k]

    abstained = len(selected) == 0
    out_chunks = []
    for item in selected:
        chunk = dict(item["chunk"])
        chunk["retrieval_meta"] = {
            "similarity": round(item["similarity"], 6),
            "lexical": round(item["lexical"], 6),
            "relevance": round(item["relevance"], 6),
            "authority_rerank": round(
                TIER_RERANK_MAX * item["authority"], 6),
            "final_score": round(item["final_score"], 6),
            "document_id": item["doc"],
            "overflow_justification": item.get("overflow_justification"),
        }
        out_chunks.append(chunk)

    best = max((i["relevance"] for i in selected), default=0.0)
    return {
        "chunks": out_chunks,
        "abstained": abstained,
        "reason": "INSUFFICIENT_RELEVANT_EVIDENCE" if abstained else None,
        "confidence": {
            "best_relevance": round(best, 6),
            "min_relevance_floor": min_relevance,
            "mode": "hybrid" if query_embedding else "lexical_only",
            "low_confidence": bool(selected) and best < min_relevance * 1.5,
        },
        "stats": {
            "candidates": len(all_chunks),
            "dropped_below_floor": dropped_floor,
            "dropped_near_duplicate": dropped_dup,
            "unique_documents": len({i["doc"] for i in selected}),
            "returned": len(out_chunks),
            "overflow_justifications": justifications,
        },
    }


def retrieve_chunks(query_embedding, all_chunks, top_k: int = 6,
                    query: str = "", **_legacy) -> List[Dict]:
    """Backwards-compatible list-only wrapper over retrieve_relevant.

    ``ensure_tier_diversity``/``authority_weight`` legacy kwargs are
    accepted and ignored — forced tier quotas are exactly the defect this
    module removes."""
    return retrieve_relevant(query, all_chunks,
                             query_embedding=query_embedding,
                             top_k=top_k)["chunks"]
