"""Citation grounding tests (packet wpk_fa189292ad894c1e node
citation_grounding_and_synthesis).

Negative classes required by the spec: fabricated citations, stale IDs,
irrelevant authoritative sources, unsupported synthesis, unused source
emission, and retry misclassification.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from claims.citation_grounding import (  # noqa: E402
    ground_answer, needs_retry, segment_claims,
)

CHUNKS = [
    {"chunk_id": "c1", "document_id": "doc_tools", "source_tier": "1",
     "source_name": "Tool Use Docs", "title": "Tool use with Claude",
     "url": "https://docs.anthropic.com/en/docs/tool-use",
     "text": "Tool definitions carry a name, description and "
             "input_schema JSON Schema. The model selects tools by "
             "matching the schema description to the task."},
    {"chunk_id": "c2", "document_id": "doc_errors", "source_tier": "2",
     "source_name": "Practice Guide", "title": "Tool errors",
     "url": "https://example.invalid/practice",
     "text": "Missing required parameters cause schema validation "
             "failures. Vague descriptions lead to wrong tool calls."},
    {"chunk_id": "c3", "document_id": "doc_safety", "source_tier": "3",
     "source_name": "Safety Doc", "title": "Cowork safety",
     "url": "https://example.invalid/safety",
     "text": "Cowork safety guidance covers permissions, data "
             "boundaries and workspace isolation."},
]


def _answer(ideas, sources=None):
    return {"ideas": ideas,
            "sources": sources if sources is not None else {}}


def _idea(text, ids=("1",)):
    return {"title": "Concept", "paragraphs": [text],
            "sourceIds": list(ids)}


class TestCitationValidation(unittest.TestCase):
    def test_fabricated_citation_stripped(self):
        a = _answer([_idea(
            "Tool schemas define input parameters [1][99].")])
        cleaned, r = ground_answer(a, CHUNKS)
        # [99] resolves to nothing — stripped from text, counted in
        # precision.
        self.assertNotIn("[99]",
                         cleaned["ideas"][0]["paragraphs"][0])
        self.assertIn("[1]", cleaned["ideas"][0]["paragraphs"][0])
        self.assertLess(r["citation_precision"], 1.0)
        self.assertEqual(r["citation_precision"], 0.5)

    def test_stale_source_id_dropped_not_fabricated(self):
        # LLM emits sources {"7": "Something"} — no chunk 7 exists.
        # Pre-hardening code fabricated a fallback enrichment entry.
        a = _answer([_idea("Tool schemas define parameters [1].")],
                    sources={"1": "Tool Use Docs",
                             "7": "Hallucinated Source"})
        cleaned, r = ground_answer(a, CHUNKS)
        self.assertNotIn("7", cleaned["sources"])
        self.assertIn("7", r["dropped_unresolvable_sources"])
        # The surviving source is enriched from the REAL chunk, not the
        # LLM's claimed title.
        self.assertEqual(cleaned["sources"]["1"]["url"],
                         CHUNKS[0]["url"])
        self.assertEqual(cleaned["sources"]["1"]["document_id"],
                         "doc_tools")

    def test_uncited_source_not_emitted(self):
        a = _answer([_idea("Tool schemas define parameters [1].")],
                    sources={"1": "used", "2": "never cited",
                             "3": "also unused"})
        cleaned, _ = ground_answer(a, CHUNKS)
        self.assertEqual(set(cleaned["sources"]), {"1"})


class TestClaimSupport(unittest.TestCase):
    def test_supported_claim_counts(self):
        a = _answer([_idea(
            "Tool schemas define input parameters and validation "
            "behavior [1].")])
        _, r = ground_answer(a, CHUNKS)
        self.assertEqual(r["claims_supported"], 1)
        self.assertEqual(r["material_claims"], 1)
        self.assertEqual(r["citation_coverage"], 1.0)

    def test_uncited_claim_reported(self):
        a = _answer([_idea(
            "Tool schemas define parameters [1]. "
            "The moon landing was staged in a desert warehouse.")])
        _, r = ground_answer(a, CHUNKS)
        self.assertEqual(r["material_claims"], 2)
        self.assertEqual(r["citation_coverage"], 0.5)
        disps = [c["disposition"] for c in r["unsupported_claims"]]
        self.assertIn("uncited", disps)

    def test_irrelevant_authoritative_source_fails_support(self):
        # Citing a real but irrelevant chunk must not count as support —
        # authority without entailment is not evidence.
        a = _answer([_idea(
            "Tool schemas define required parameters and validation "
            "[3].")], sources={"3": "Safety Doc"})
        _, r = ground_answer(a, CHUNKS)
        disps = [c["disposition"] for c in r["unsupported_claims"]]
        self.assertIn("unsupported_by_cited_chunks", disps)

    def test_segmentation_skips_connective_sentences(self):
        claims = segment_claims("It does. [1]")
        # no content terms — connective, not a material claim
        self.assertEqual(claims, [])
        claims = segment_claims(
            "Tool schemas define required input parameters [1].")
        self.assertEqual(len(claims), 1)


class TestReceiptShape(unittest.TestCase):
    def test_receipt_fields_bounded(self):
        a = _answer([_idea(
            "Tool schemas define input parameters [1].")])
        _, r = ground_answer(a, CHUNKS)
        for key in ("material_claims", "claims_with_valid_citation",
                    "claims_supported", "citation_coverage",
                    "citation_precision", "unique_cited_documents",
                    "tier1_cited_count", "unsupported_claims",
                    "unsupported_disposition", "grounding"):
            self.assertIn(key, r)
        self.assertEqual(r["unique_cited_documents"], 1)
        self.assertEqual(r["tier1_cited_count"], 1)

    def test_lower_tier_only_disclosed(self):
        # Cite only tier-2/3 chunks → evidence limitation surfaces.
        a = _answer([_idea(
            "Missing required parameters cause schema validation "
            "failures [2][3].")])
        cleaned, r = ground_answer(a, CHUNKS)
        self.assertEqual(r["tier1_cited_count"], 0)
        self.assertIsNotNone(r["evidence_limitation"])
        self.assertIn("lower-tier", cleaned["evidence_limitation"])


class TestRetryPredicate(unittest.TestCase):
    def test_malformed_retries(self):
        self.assertTrue(needs_retry(None, None))

    def test_high_unsupported_retries(self):
        receipt = {"material_claims": 4,
                   "unsupported_claims": [{}, {}, {}]}
        self.assertTrue(needs_retry({}, receipt))

    def test_clean_answer_no_retry(self):
        receipt = {"material_claims": 4, "unsupported_claims": []}
        self.assertFalse(needs_retry({}, receipt))

    def test_no_claims_is_malformed(self):
        self.assertTrue(needs_retry({}, {"material_claims": 0,
                                         "unsupported_claims": []}))


if __name__ == "__main__":
    unittest.main()
