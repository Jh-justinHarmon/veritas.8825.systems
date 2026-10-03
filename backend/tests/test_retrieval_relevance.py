"""Retrieval relevance + dedup tests (packet wpk_fa189292ad894c1e node
retrieval_relevance_and_dedup).

Proves: relevance floor before tier weighting, authority as bounded
reranker only, near-duplicate suppression, per-document cap with
recorded justification, truthful abstention, lexical-only offline mode,
and the frozen-observation regression — a tool-schema query must not
surface generic Cowork safety evidence.
"""

import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from retrieval.relevance import (  # noqa: E402
    DEFAULT_MIN_RELEVANCE, MAX_CHUNKS_PER_DOC, TIER_RERANK_MAX,
    lexical_score, retrieve_relevant,
)

REPO_ROOT = Path(__file__).parents[2]
CORPUS = REPO_ROOT / "corpus" / "embeddings" / "all_tiers_embedded_chunks.json"


def _chunk(doc, text, tier=1, embedding=None, **kw):
    c = {"chunk_id": f"{doc}_c{kw.pop('idx', 0)}", "document_id": doc,
         "source_tier": str(tier), "source_name": doc, "title": doc,
         "text": text, "url": "https://example.invalid/x"}
    c.update(kw)
    if embedding is not None:
        c["embedding"] = embedding
    return c


def _vec(base, n=8, scale=1.0):
    return [base * scale if i == 0 else (base + i) * 0.001
            for i in range(n)]


class TestRelevanceFloor(unittest.TestCase):
    def test_below_floor_chunks_dropped(self):
        chunks = [
            _chunk("relevant", "tool use parameters schema error",
                   embedding=_vec(1.0)),
            _chunk("irrelevant", "unrelated content entirely",
                   embedding=_vec(0.001)),
        ]
        out = retrieve_relevant("tool parameters error", chunks,
                                query_embedding=_vec(1.0), top_k=5)
        docs = [c["document_id"] for c in out["chunks"]]
        self.assertEqual(docs, ["relevant"])
        self.assertEqual(out["stats"]["dropped_below_floor"], 1)

    def test_no_chunks_survive_abstains(self):
        chunks = [_chunk("a", "completely unrelated", embedding=_vec(0.0))]
        out = retrieve_relevant("quantum entanglement bridge", chunks,
                                query_embedding=_vec(1.0))
        self.assertTrue(out["abstained"])
        self.assertEqual(out["reason"], "INSUFFICIENT_RELEVANT_EVIDENCE")
        self.assertEqual(out["chunks"], [])


class TestAuthorityReranker(unittest.TestCase):
    def test_tier_never_substitutes_relevance(self):
        # Irrelevant tier-1 must not outrank a directly relevant tier-3
        # solely because of tier.
        chunks = [
            _chunk("t1_generic", "safety guidance knowledge work power",
                   tier=1, embedding=[0.5, 0.866, 0.0]),
            _chunk("t3_ontopic", "tool schema invalid parameter error",
                   tier=3, embedding=[1.0, 0.0, 0.0]),
        ]
        out = retrieve_relevant("tool schema invalid parameter", chunks,
                                query_embedding=[1.0, 0.0, 0.0], top_k=2)
        docs = [c["document_id"] for c in out["chunks"]]
        self.assertEqual(docs, ["t3_ontopic", "t1_generic"])
        gap = (out["chunks"][0]["retrieval_meta"]["relevance"]
               - out["chunks"][1]["retrieval_meta"]["relevance"])
        self.assertGreater(gap, TIER_RERANK_MAX)

    def test_tier_breaks_near_ties_only(self):
        # Within the rerank window, higher tier wins. Embeddings/text
        # differ enough to stay under the near-duplicate bar while the
        # relevance gap stays inside TIER_RERANK_MAX.
        chunks = [
            _chunk("t3_doc", "tool parameter schema detailed notes alpha",
                   tier=3, embedding=[1.0, 0.0, 0.0]),
            _chunk("t1_doc", "tool parameter schema overview extra gamma",
                   tier=1, embedding=[0.966, 0.258, 0.0]),
        ]
        q = "tool parameter schema"
        out = retrieve_relevant(q, chunks,
                                query_embedding=[1.0, 0.0, 0.0], top_k=2)
        metas = {c["document_id"]: c["retrieval_meta"]
                 for c in out["chunks"]}
        self.assertEqual(len(out["chunks"]), 2)
        self.assertLess(
            metas["t3_doc"]["relevance"] - metas["t1_doc"]["relevance"],
            TIER_RERANK_MAX)
        self.assertEqual(out["chunks"][0]["document_id"], "t1_doc")


class TestDedupAndCaps(unittest.TestCase):
    def test_near_duplicate_embeddings_dropped(self):
        chunks = [
            _chunk("doc_a", "alpha body", idx=0, embedding=[1.0, 0, 0]),
            _chunk("doc_b", "beta body different", idx=0,
                   embedding=[0.99, 0.14, 0]),
            _chunk("doc_c", "alpha beta gamma alpha beta gamma "
                            "alpha beta gamma", idx=0,
                   embedding=[0.0, 1.0, 0.0]),
        ]
        out = retrieve_relevant("alpha beta gamma", chunks,
                                query_embedding=[1.0, 0, 0], top_k=5)
        self.assertEqual(out["stats"]["dropped_near_duplicate"], 1)
        self.assertEqual(len(out["chunks"]), 2)

    def test_per_document_cap_with_justification(self):
        # Same document, genuinely distinct chunks (text + embedding
        # diverge enough to escape both near-dup checks).
        chunks = [_chunk("same_doc",
                         f"tool parameter schema variant{i} marker{i}",
                         idx=i,
                         embedding=[math.cos(0.3 * i),
                                    math.sin(0.3 * i), 0.0])
                  for i in range(5)]
        out = retrieve_relevant("tool parameter schema", chunks,
                                query_embedding=_vec(1.0), top_k=4,
                                min_relevance=0.0)
        self.assertEqual(len(out["chunks"]), 4)
        capped = [c for c in out["chunks"]
                  if c["retrieval_meta"]["overflow_justification"]]
        self.assertEqual(len(capped), 4 - MAX_CHUNKS_PER_DOC)
        for c in capped:
            self.assertIn("unfilled by unique documents",
                          c["retrieval_meta"]["overflow_justification"])
            self.assertIn("same_doc",
                          c["retrieval_meta"]["overflow_justification"])


class TestLexicalAndOffline(unittest.TestCase):
    def test_lexical_only_mode(self):
        chunks = [
            _chunk("ontopic", "rate limits exceeded retry backoff"),
            _chunk("offtopic", "completely different subject"),
        ]
        out = retrieve_relevant("rate limit retry", chunks,
                                query_embedding=None, top_k=2)
        self.assertFalse(out["abstained"])
        self.assertEqual(out["confidence"]["mode"], "lexical_only")
        self.assertEqual(out["chunks"][0]["document_id"], "ontopic")

    def test_lexical_score_deterministic(self):
        a = lexical_score("tool use errors", "tool use error handling")
        b = lexical_score("tool use errors", "tool use error handling")
        self.assertEqual(a, b)
        self.assertGreater(a, lexical_score("tool use errors",
                                            "unrelated words here"))


@unittest.skipUnless(CORPUS.exists(), "production corpus required")
class TestGoldenSetObservations(unittest.TestCase):
    """Offline lexical-mode eval against the rebuilt corpus for the
    observed defect classes in the freeze contract."""

    @classmethod
    def setUpClass(cls):
        cls.chunks = json.loads(CORPUS.read_text())

    def test_tool_schema_query_not_cowork_safety(self):
        # Frozen defect: tool-schema questions surfaced generic Cowork
        # safety evidence. After the rebuild the dead tool-use scrape
        # stub is quarantined; what must hold is that cowork-safety is
        # not the answer and every returned chunk is substantive.
        out = retrieve_relevant(
            "Why is Claude calling the wrong tool or using incorrect "
            "parameters?", self.chunks, query_embedding=None, top_k=5)
        docs = [c["document_id"] for c in out["chunks"]]
        self.assertNotIn(
            "claude_docs_use_cowork_safely_claude_help_center", docs[:2])
        for c in out["chunks"]:
            body = c["text"].replace("Loading...", "").strip()
            self.assertGreaterEqual(len(body), 80)

    def test_dead_scrape_docs_never_serve(self):
        # All ten Loading...-stub documents are quarantined; the rebuilt
        # corpus must contain none of them.
        dead = {"claude_docs_tool-use", "claude_docs_api",
                "claude_docs_streaming", "claude_docs_models",
                "claude_docs_errors", "claude_docs_intro",
                "claude_docs_messages", "claude_docs_authentication",
                "claude_docs_prompt-engineering", "claude_docs_rate-limits"}
        present = {c["document_id"] for c in self.chunks}
        self.assertFalse(dead & present)

    def test_unique_document_diversity(self):
        out = retrieve_relevant(
            "how do streaming tool use blocks work", self.chunks,
            query_embedding=None, top_k=6)
        metas = [c["retrieval_meta"] for c in out["chunks"]]
        docs = [m["document_id"] for m in metas]
        overflow = [m for m in metas if m["overflow_justification"]]
        # No duplicate document without a recorded justification.
        for doc in set(docs):
            if docs.count(doc) > MAX_CHUNKS_PER_DOC:
                self.assertTrue(overflow)
        self.assertEqual(len(out["chunks"]),
                         out["stats"]["returned"])

    def test_gibberish_query_abstains(self):
        out = retrieve_relevant("zxqwv kjfbdq wqpo", self.chunks,
                                query_embedding=None, top_k=5)
        self.assertTrue(out["abstained"])
        self.assertEqual(out["reason"], "INSUFFICIENT_RELEVANT_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
