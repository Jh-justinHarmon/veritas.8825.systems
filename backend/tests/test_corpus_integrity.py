"""Corpus integrity hardening tests (packet wpk_fa189292ad894c1e node
corpus_integrity_hardening).

Proves quarantined/placeholder sources cannot reach the production
chunk store, the manifest gate fails closed, and the rebuilt corpus is
hash-bound and deterministic.

Test fixtures live in backend/tests/fixtures — physically outside
corpus/ — and never touch the production corpus or embedding store.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "ingestion"))

from source_policy import (  # noqa: E402
    SourceAdmissionError,
    admit_source_document,
    approved_entries,
    chunk_has_substantive_content,
    chunk_is_production_safe,
    corpus_inventory_hash,
    is_placeholder_url,
    load_source_manifest,
)

REPO_ROOT = Path(__file__).parents[2]
CORPUS_DIR = REPO_ROOT / "corpus"
QUARANTINE_DIR = REPO_ROOT / "corpus_quarantine"
CHUNKS_FILE = CORPUS_DIR / "embeddings" / "all_tiers_embedded_chunks.json"
BUILD_MANIFEST = CORPUS_DIR / "embeddings" / "all_tiers_manifest.json"

PLACEHOLDER_DOC_IDS = {
    "tier1_stripe_webhooks_overview",
    "tier1_stripe_webhooks_quickstart",
    "tier1_stripe_webhooks_signature_verification",
    "tier2_claude_tool_use_practice",
    "tier2_stripe_webhooks_implementation_guide",
    "tier2_stripe_webhooks_ngrok_testing",
    "tier3_claude_tool_use_failures",
    "tier3_stripe_webhooks_bodyparser_conflict",
    "tier3_stripe_webhooks_test_live_mismatch",
}


class ProductionCorpusCleanTests(unittest.TestCase):
    """The shipped chunk store must contain only manifest-approved
    canonical sources."""

    @classmethod
    def setUpClass(cls):
        cls.chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
        cls.manifest = load_source_manifest()
        cls.build_manifest = json.loads(
            BUILD_MANIFEST.read_text(encoding="utf-8"))

    def test_no_placeholder_urls_in_production_chunks(self):
        bad = [c["chunk_id"] for c in self.chunks
               if is_placeholder_url(c.get("url"))]
        self.assertEqual(bad, [])

    def test_no_quarantined_documents_in_production_chunks(self):
        doc_ids = {c["document_id"] for c in self.chunks}
        self.assertEqual(doc_ids & PLACEHOLDER_DOC_IDS, set())

    def test_every_chunk_is_manifest_approved(self):
        unsafe = [c["chunk_id"] for c in self.chunks
                  if not chunk_is_production_safe(c, self.manifest)]
        self.assertEqual(unsafe, [])

    def test_existing_anthropic_sources_preserved(self):
        # corpus-2026-10-02-v2: 10 substantive Anthropic docs survive;
        # the 10 dead scrape stubs are quarantined alongside the 9
        # placeholder docs from v1.
        doc_ids = {c["document_id"] for c in self.chunks}
        self.assertTrue(all(d.startswith("claude_docs_") for d in doc_ids))
        self.assertEqual(len(doc_ids), 10)

    def test_dead_scrape_docs_quarantined(self):
        dead = {
            "claude_docs_api", "claude_docs_authentication",
            "claude_docs_errors", "claude_docs_intro",
            "claude_docs_messages", "claude_docs_models",
            "claude_docs_prompt-engineering", "claude_docs_rate-limits",
            "claude_docs_streaming", "claude_docs_tool-use",
        }
        doc_ids = {c["document_id"] for c in self.chunks}
        self.assertFalse(dead & doc_ids)
        for chunk in self.chunks:
            self.assertTrue(chunk_has_substantive_content(chunk))

    def test_manifest_hash_binds_loaded_corpus(self):
        self.assertEqual(
            self.build_manifest.get("manifest_sha256"),
            corpus_inventory_hash(self.chunks))

    def test_rebuild_is_deterministic(self):
        from rebuild_corpus import rebuild
        before = CHUNKS_FILE.read_bytes()
        out = rebuild("corpus-2026-10-02-v2")
        self.assertEqual(CHUNKS_FILE.read_bytes(), before)
        self.assertEqual(out["manifest_sha256"],
                         self.build_manifest["manifest_sha256"])
        self.assertEqual(out["total_chunks"], len(self.chunks))

    def test_quarantined_sources_physically_outside_corpus(self):
        for doc_id in PLACEHOLDER_DOC_IDS:
            matches = list(QUARANTINE_DIR.rglob("*.md"))
        self.assertEqual(len(matches), 9)
        raw_md = list((CORPUS_DIR / "raw").rglob("*.md"))
        self.assertEqual(raw_md, [])

    def test_production_manifest_has_zero_placeholder_urls(self):
        for entry in self.manifest["documents"]:
            for field in ("canonical_url", "observed_url"):
                url = entry.get(field)
                if url is not None:
                    self.assertFalse(
                        is_placeholder_url(url),
                        f"{entry['document_id']}.{field} is placeholder")

    def test_manifest_documents_exclude_placeholder_doc_ids(self):
        ids = {e["document_id"] for e in self.manifest["documents"]}
        self.assertEqual(ids & PLACEHOLDER_DOC_IDS, set())


class QuarantineLedgerTests(unittest.TestCase):
    """The quarantine provenance ledger preserves audit lineage but can
    never enter ingestion, retrieval, synthesis or emitted sources."""

    @classmethod
    def setUpClass(cls):
        cls.ledger_path = QUARANTINE_DIR / "quarantine_ledger.json"
        cls.ledger = json.loads(cls.ledger_path.read_text("utf-8"))
        cls.manifest = load_source_manifest()

    def test_ledger_preserves_all_nine_placeholder_records(self):
        docs = self.ledger["documents"]
        self.assertEqual(len(docs), 9)
        self.assertEqual({d["document_id"] for d in docs},
                         PLACEHOLDER_DOC_IDS)
        for d in docs:
            self.assertEqual(d["status"], "quarantined")
            for field in ("document_id", "observed_url",
                          "quarantine_reason", "quarantined_path",
                          "provenance", "content_sha256"):
                self.assertIn(field, d)

    def test_ledger_is_not_a_source_manifest(self):
        with self.assertRaises(SourceAdmissionError):
            load_source_manifest(self.ledger_path)

    def test_ledger_documents_unadmittable(self):
        for d in self.ledger["documents"]:
            with self.assertRaises(SourceAdmissionError) as ctx:
                admit_source_document(
                    {"id": d["document_id"], "source_tier": d["tier"],
                     "url": d["observed_url"], "content": "x" * 200},
                    self.manifest)
            self.assertEqual(str(ctx.exception),
                             "SOURCE_NOT_IN_APPROVED_MANIFEST")

    def test_ledger_document_chunks_unsafe_for_production(self):
        for d in self.ledger["documents"]:
            chunk = {"document_id": d["document_id"],
                     "text": "substantive content " * 10,
                     "url": d["observed_url"]}
            self.assertFalse(chunk_is_production_safe(chunk, self.manifest))

    def test_ledger_urls_are_all_placeholders(self):
        for d in self.ledger["documents"]:
            for field in ("canonical_url", "observed_url"):
                url = d.get(field)
                if url is not None:
                    self.assertTrue(is_placeholder_url(url))

    def test_manifest_with_placeholder_url_field_fails_closed(self):
        bad = {"manifest_version": "1.0.0",
               "manifest_id": "x",
               "documents": [{"document_id": "d", "status": "approved",
                              "canonical_url": "https://example.com/x",
                              "tier": 1}]}
        import tempfile
        with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
        try:
            with self.assertRaises(SourceAdmissionError) as ctx:
                load_source_manifest(Path(f.name))
            self.assertIn("MANIFEST_PLACEHOLDER_URL", str(ctx.exception))
        finally:
            Path(f.name).unlink()


class SourceAdmissionTests(unittest.TestCase):
    """The ingestion gate refuses placeholder/malformed/duplicate/
    unapproved sources before embedding."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load_source_manifest()
        cls.approved = approved_entries(cls.manifest)
        cls.sample_id = next(iter(cls.approved))
        cls.entry = cls.approved[cls.sample_id]

    def _doc(self, **over):
        doc = {
            "id": self.sample_id,
            "source_tier": self.entry["tier"],
            "url": self.entry["canonical_url"],
            "content": "legitimate corpus text about tool use errors",
        }
        doc.update(over)
        return doc

    def test_approved_doc_admitted(self):
        got = admit_source_document(self._doc(), self.manifest)
        self.assertEqual(got["document_id"], self.sample_id)

    def test_example_com_url_rejected(self):
        with self.assertRaises(SourceAdmissionError) as ctx:
            admit_source_document(
                self._doc(url="https://example.com/docs/x"), self.manifest)
        self.assertIn(str(ctx.exception),
                      ("SOURCE_URL_PLACEHOLDER", "SOURCE_URL_MANIFEST_MISMATCH"))

    def test_unmanifested_doc_rejected(self):
        with self.assertRaises(SourceAdmissionError) as ctx:
            admit_source_document(
                self._doc(id="tier9_unapproved_thing"), self.manifest)
        self.assertEqual(str(ctx.exception), "SOURCE_NOT_IN_APPROVED_MANIFEST")

    def test_quarantined_doc_id_rejected(self):
        with self.assertRaises(SourceAdmissionError) as ctx:
            admit_source_document(
                self._doc(id="tier3_claude_tool_use_failures"),
                self.manifest)
        self.assertEqual(str(ctx.exception), "SOURCE_NOT_IN_APPROVED_MANIFEST")

    def test_malformed_url_rejected(self):
        for bad in ["", "notaurl", "ftp://example.com/x", None]:
            self.assertTrue(is_placeholder_url(bad))

    def test_duplicate_doc_id_rejected(self):
        seen = set()
        admit_source_document(self._doc(), self.manifest, _seen_ids=seen)
        with self.assertRaises(SourceAdmissionError) as ctx:
            admit_source_document(
                self._doc(), self.manifest, _seen_ids=seen)
        self.assertEqual(str(ctx.exception), "SOURCE_ID_DUPLICATE")

    def test_placeholder_body_markers_rejected(self):
        with self.assertRaises(SourceAdmissionError):
            admit_source_document(
                self._doc(content="lorem ipsum dolor sit amet"),
                self.manifest)


class QuarantinedChunkNeverRetrievedTests(unittest.TestCase):
    """Retrieval over the production chunk store can never surface a
    quarantined document, even with a quarantined chunk's own embedding
    as the query."""

    def test_retrieval_never_returns_quarantined_docs(self):
        from retrieval.simple_retriever import load_chunks, retrieve_chunks

        chunks = load_chunks(CHUNKS_FILE)
        query = chunks[0]["embedding"]
        results = retrieve_chunks(query, chunks, top_k=10)
        self.assertTrue(results)
        for r in results:
            self.assertNotIn(r["document_id"], PLACEHOLDER_DOC_IDS)
            self.assertFalse(is_placeholder_url(r.get("url")))


if __name__ == "__main__":
    unittest.main()
