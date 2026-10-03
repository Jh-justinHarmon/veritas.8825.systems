"""Regression tests for corrections required by the independent
predeployment review (packet wpk_fa189292ad894c1e).

Covers document-level source uniqueness, duplicate-document handling,
evaluator layer routing, negative authorization/invalid-input verdicts,
and conflicting-guidance predicate evaluation.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from agents.synthesis_agent import collapse_to_documents  # noqa: E402
from claims.citation_grounding import ground_answer  # noqa: E402
from evals.retrieval_eval import Evaluator  # noqa: E402


def _chunk(chunk_id, doc_id, text, tier=1, relevance=0.5):
    return {
        "chunk_id": chunk_id,
        "document_id": doc_id,
        "source_tier": tier,
        "source_name": f"Source {doc_id}",
        "title": f"Title {doc_id}",
        "url": f"https://docs.example/{doc_id}",
        "text": text,
        "retrieval_meta": {"document_id": doc_id,
                           "relevance": relevance},
    }


class TestDocumentCollapse(unittest.TestCase):
    def test_same_document_chunks_merge_to_one_source(self):
        chunks = [
            _chunk("a1", "doc_a", "Tool schemas carry input parameters.",
                   tier=1, relevance=0.8),
            _chunk("a2", "doc_a", "Missing required fields fail "
                                  "validation.", tier=1, relevance=0.4),
            _chunk("b1", "doc_b", "Permissions isolate workspace access.",
                   tier=2, relevance=0.6),
        ]
        docs = collapse_to_documents(chunks)
        self.assertEqual(len(docs), 2)
        self.assertEqual([d["document_id"] for d in docs],
                         ["doc_a", "doc_b"])
        self.assertEqual(docs[0]["chunk_ids"], ["a1", "a2"])
        self.assertIn("input parameters", docs[0]["text"])
        self.assertIn("validation", docs[0]["text"])
        self.assertEqual(docs[0]["citation_unit"], "document")

    def test_grounded_sources_unique_by_document(self):
        docs = collapse_to_documents([
            _chunk("a1", "doc_a", "Tool schemas carry input parameters."),
            _chunk("a2", "doc_a", "Required fields fail validation."),
        ])
        answer = {"ideas": [{"title": "t", "paragraphs": [
            "Tool schemas carry input parameters [1]."
        ]}]}
        cleaned, receipt = ground_answer(answer, docs)
        emitted = list(cleaned["sources"].values())
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0]["document_id"], "doc_a")
        self.assertEqual(receipt["unique_cited_documents"], 1)

    def test_distinct_documents_stay_distinct_for_conflict_review(self):
        docs = collapse_to_documents([
            _chunk("a1", "doc_a", "Tool schemas require strict types."),
            _chunk("b1", "doc_b", "Tool schemas allow loose typing."),
        ])
        self.assertEqual(len(docs), 2)
        self.assertEqual({d["document_id"] for d in docs},
                         {"doc_a", "doc_b"})


class TestEvaluatorCorrections(unittest.TestCase):
    def _eval(self, **kwargs):
        return Evaluator(chunks=[], **kwargs)

    def test_synthesize_item_asserts_offline_predicates_only(self):
        item = {
            "id": "ge-duplicate-source-01",
            "category": "duplicate_conflicting_sources",
            "input": {"capability": "veritas.synthesize",
                      "payload": {"question": "Compare parameter rules."}},
            "expected": {"status": "COMPLETED",
                         "sources_unique": True,
                         "conflicting_guidance_disclosed": True},
        }
        ev = self._eval()
        ev._retrieval_observation = lambda q: {
            "layer": "retrieval", "abstained": False,
            "doc_ids": ["doc_a", "doc_b"], "doc_ids_unique": True,
            "placeholder_sources": [], "doc_sources": [],
        }
        row = ev.evaluate_item(item)
        by_pred = {p["predicate"]: p for p in row["predicates"]}
        self.assertEqual(row["layer"], "synthesize")
        self.assertEqual(by_pred["sources_unique"]["verdict"], "pass")
        self.assertEqual(by_pred["status"]["verdict"], "not_evaluable")
        self.assertEqual(by_pred["status"]["detail"],
                         "provider_not_authorized")
        self.assertEqual(
            by_pred["conflicting_guidance_disclosed"]["verdict"],
            "not_evaluable")

    def test_conflicting_guidance_predicate_checks_answer_text(self):
        ev = self._eval()
        observed = {"status": "COMPLETED", "json": {
            "ideas": [{"paragraphs": [
                "The two documents differ: one requires strict types, "
                "while the other permits loose typing."]}]}}
        v = ev._check_pred("conflicting_guidance_disclosed", True,
                           observed, "synthesize")
        self.assertEqual(v["verdict"], "pass")
        observed["json"]["ideas"][0]["paragraphs"] = [
            "The tools validate parameters."]
        v = ev._check_pred("conflicting_guidance_disclosed", True,
                           observed, "synthesize")
        self.assertEqual(v["verdict"], "fail")

    def test_negative_authorization_is_explicitly_not_evaluable(self):
        item = {"id": "ge-neg-unauth-01",
                "category": "negative_missing_authorization",
                "input": {"capability": "veritas.synthesize",
                          "payload": {"question": "q"}},
                "expected": {"status": "AUTHORIZATION_REQUIRED"}}
        row = self._eval().evaluate_item(item)
        self.assertEqual(row["layer"], "gateway")
        self.assertEqual(row["predicates"][0]["verdict"], "not_evaluable")
        self.assertEqual(row["predicates"][0]["detail"],
                         "gateway_url_missing")

    def test_invalid_input_is_explicitly_not_evaluable(self):
        item = {"id": "ge-neg-length-01",
                "category": "negative_input_bounds",
                "input": {"payload": {"question": "hi"}},
                "expected": {"status": "BLOCKED",
                             "reason": "QUESTION_OUT_OF_BOUNDS_or_equivalent_typed_reason"}}
        row = self._eval().evaluate_item(item)
        self.assertEqual(row["layer"], "service")
        self.assertTrue(all(p["verdict"] == "not_evaluable"
                            for p in row["predicates"]))
        self.assertEqual(row["predicates"][0]["detail"],
                         "service_url_missing")


if __name__ == "__main__":
    unittest.main()
