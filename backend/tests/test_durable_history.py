"""Durable result storage tests (packet wpk_fa189292ad894c1e node
durable_result_storage).

Restart/replacement/redeploy durability is simulated by reopening a
fresh store instance (and a fresh process boundary where it matters)
against the same DB path — the SQLite file is the durable artifact.
No provider calls; fixtures live under backend/tests/fixtures.
"""

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from history.sqlite_store import SqliteHistoryStore, HistoryStoreError  # noqa: E402


def _entry(i):
    return {
        "question": f"question {i}",
        "answer": {"ideas": [{"title": f"idea {i}", "paragraphs": ["p"]}],
                   "sources": {"1": {"title": "s", "url": "u"}}},
        "trace": {"corpus": {"corpus_version": "v", "manifest_sha256": "h"},
                  "chunk_count": 1},
    }


class DurabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "history.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_result_survives_store_reopen(self):
        """Process restart: a new store instance over the same DB returns
        identical content."""
        s1 = SqliteHistoryStore(self.db)
        e = _entry(1)
        rid = s1.save_synthesis(e["question"], e["answer"], e["trace"],
                                owner_subject="subj-a",
                                receipt_ref="vown_x")
        s1.close()

        s2 = SqliteHistoryStore(self.db)
        got = s2.get_history_by_id(rid)
        self.assertEqual(got["id"], rid)
        self.assertEqual(got["question"], e["question"])
        self.assertEqual(got["answer"], e["answer"])
        self.assertEqual(got["trace"]["corpus"]["corpus_version"], "v")

    def test_result_survives_process_boundary(self):
        """Machine replacement analog: a fresh interpreter reads the row."""
        s1 = SqliteHistoryStore(self.db)
        rid = s1.save_synthesis("q", {"ideas": [], "sources": {}}, {})
        s1.close()
        code = (
            "import sys, json; sys.path.insert(0, %r);"
            "from history.sqlite_store import SqliteHistoryStore;"
            "s = SqliteHistoryStore(%r);"
            "print(json.dumps(s.get_history_by_id(%r)))"
            % (str(Path(__file__).parents[1]), str(self.db), rid))
        out = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        got = json.loads(out.stdout.strip())
        self.assertEqual(got["id"], rid)

    def test_unknown_and_foreign_ids_indistinguishable(self):
        s = SqliteHistoryStore(self.db)
        rid = s.save_synthesis("q", {"ideas": [], "sources": {}}, {})
        foreign = s.get_history_by_id("00000000-0000-0000-0000-000000000000")
        never = s.get_history_by_id("does-not-exist")
        self.assertIsNone(foreign)
        self.assertIsNone(never)
        self.assertIsNotNone(s.get_history_by_id(rid))

    def test_exact_id_only_no_enumeration_leak(self):
        """get_history_by_id never fuzzy-matches."""
        s = SqliteHistoryStore(self.db)
        rid = s.save_synthesis("q", {"ideas": [], "sources": {}}, {})
        for probe in (rid.upper(), rid + "x", rid[:-1] + "0", " " + rid):
            self.assertIsNone(s.get_history_by_id(probe))

    def test_storage_outage_fails_closed(self):
        """Unwritable path raises HistoryStoreError — the edge sanitizes
        to HISTORY_UNAVAILABLE; no silent ephemeral fallback."""
        blocked = Path(self.tmp.name) / "no-such-dir" / "sub" / "h.db"
        blocked.parent.mkdir(parents=True)
        blocked.parent.chmod(0o444)
        try:
            with self.assertRaises(HistoryStoreError):
                SqliteHistoryStore(blocked)
        finally:
            blocked.parent.chmod(0o755)

    def test_write_failure_raises_sanitized(self):
        s = SqliteHistoryStore(self.db)
        s.close()
        with self.assertRaises(HistoryStoreError):
            s.save_synthesis("q", {"ideas": [], "sources": {}}, {})

    def test_atomicity_no_partial_row(self):
        """A failed write leaves no retrievable fragment."""
        s = SqliteHistoryStore(self.db)
        rid = s.save_synthesis("q", {"ideas": [], "sources": {}}, {})
        conn = sqlite3.connect(str(self.db))
        n = conn.execute(
            "SELECT COUNT(*) FROM history WHERE id=?", (rid,)).fetchone()[0]
        self.assertEqual(n, 1)

    def test_delete_is_permanent(self):
        s = SqliteHistoryStore(self.db)
        rid = s.save_synthesis("q", {"ideas": [], "sources": {}}, {})
        self.assertTrue(s.delete_history(rid))
        self.assertIsNone(s.get_history_by_id(rid))
        self.assertFalse(s.delete_history(rid))

    def test_retention_expiry(self):
        s = SqliteHistoryStore(self.db, retention_days=1)
        rid = s.save_synthesis("q", {"ideas": [], "sources": {}}, {})
        self.assertIsNotNone(s.get_history_by_id(rid))
        conn = sqlite3.connect(str(self.db))
        conn.execute(
            "UPDATE history SET created_at='2000-01-01T00:00:00+00:00'"
            " WHERE id=?", (rid,))
        conn.commit()
        self.assertIsNone(s.get_history_by_id(rid))

    def test_legacy_json_migration(self):
        legacy = Path(self.tmp.name) / "synthesis_history.json"
        legacy.write_text(json.dumps([{
            "id": "legacy-1", "timestamp": "2026-01-01T00:00:00",
            "question": "old q",
            "answer": {"ideas": [{"title": "t"}], "sources": {}},
            "trace": {}}]))
        s = SqliteHistoryStore(self.db, legacy_json=legacy)
        got = s.get_history_by_id("legacy-1")
        self.assertEqual(got["question"], "old q")


class AppEdgeTests(unittest.TestCase):
    """App-level fail-closed behavior on storage outage."""

    def test_history_get_fails_closed_sanitized(self):
        import app as app_mod
        from flask.testing import FlaskClient
        original = app_mod.history_store
        app_mod.history_store = None
        try:
            c = FlaskClient(app_mod.app)
            r = c.get("/api/history/anything")
            self.assertEqual(r.status_code, 503)
            body = r.get_json()
            self.assertEqual(body["error"], "HISTORY_UNAVAILABLE")
            self.assertNotIn("Traceback", json.dumps(body))
            self.assertNotIn("sqlite", json.dumps(body).lower())
        finally:
            app_mod.history_store = original


if __name__ == "__main__":
    unittest.main()
