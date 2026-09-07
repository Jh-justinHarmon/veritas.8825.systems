import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from claims.runtime_status import (
    FixtureEvidenceAdapter,
    LocalEvidenceAdapter,
    mediate_runtime_status,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "runtime_status_sources.json"
NOW = datetime(2026, 9, 7, 17, 0, tzinfo=timezone.utc)


class RuntimeStatusClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_pass_claim_preserves_receipts_and_freshness(self):
        claim = mediate_runtime_status(FixtureEvidenceAdapter(self.fixture["sources"]), now=NOW)

        self.assertEqual(claim["schema_version"], "veritas_claim/0.1.0")
        self.assertEqual(claim["claim_family"], "runtime_deployment_status")
        self.assertEqual(claim["status"], "SUPPORTED")
        self.assertEqual(claim["authority_class"], "RECEIPT_FACT")
        self.assertEqual(claim["release"], "v17")
        self.assertEqual(claim["image"], "deployment-01M1Y8YZ6QNG7AVV44F178QWGF")
        self.assertEqual(claim["freshness"]["status"], "CURRENT")
        self.assertEqual(len(claim["source_refs"]), 2)
        self.assertEqual(len(claim["receipt_refs"]), 2)
        self.assertEqual(claim["rollback_reference"], "deployment-01KPGWP7RH54EMHFZ649Y4ZG9B")
        self.assertFalse(claim["authority_created_by_veritas"])

    def test_missing_monitoring_receipt_is_unknown(self):
        sources = [self.fixture["sources"][0]]
        claim = mediate_runtime_status(FixtureEvidenceAdapter(sources), now=NOW)

        self.assertEqual(claim["status"], "UNKNOWN")
        self.assertIn("monitoring_review", claim["open_gaps"])
        self.assertEqual(claim["freshness"]["status"], "UNKNOWN")
        self.assertFalse(claim["authority_created_by_veritas"])

    def test_stale_receipts_do_not_support_current_claim(self):
        stale = [dict(source, observed_at="2026-08-01T00:00:00Z") for source in self.fixture["sources"]]
        claim = mediate_runtime_status(FixtureEvidenceAdapter(stale), now=NOW)

        self.assertEqual(claim["status"], "STALE")
        self.assertEqual(claim["freshness"]["status"], "STALE")
        self.assertIn("stale_source", claim["staleness_reasons"])

    def test_watchtower_observation_cannot_upgrade_authority(self):
        sources = [
            *self.fixture["sources"],
            {
                "source_id": "watchtower-observation",
                "source_type": "watchtower_observation",
                "authority_class": "OBSERVED_ADVISORY",
                "observed_at": "2026-09-07T16:59:00Z",
                "source_ref": "watchtower/observation.json",
                "source_hash": "sha256:fixture-watchtower",
                "result": "PASS"
            }
        ]
        claim = mediate_runtime_status(FixtureEvidenceAdapter(sources), now=NOW)

        self.assertEqual(claim["status"], "SUPPORTED")
        self.assertEqual(claim["authority_class"], "RECEIPT_FACT")
        self.assertEqual(claim["watchtower_observations"], ["watchtower-observation"])
        self.assertFalse(claim["authority_created_by_veritas"])

    def test_local_evidence_adapter_loads_allowed_receipts_and_spine_context(self):
        adapter = LocalEvidenceAdapter(
            smoke_receipt_path=FIXTURE_PATH.parent / "v17_production_smoke_receipt.md",
            monitoring_review_path=FIXTURE_PATH.parent / "v17_monitoring_review.md",
            spine_snapshot_path=FIXTURE_PATH.parent / "local_work_lane_spine_snapshot.json",
        )
        claim = mediate_runtime_status(adapter, now=NOW)

        self.assertEqual(claim["status"], "SUPPORTED")
        self.assertEqual(claim["release"], "v17")
        self.assertEqual(
            claim["image"],
            "registry.fly.io/veritas-8825-systems:deployment-01M1Y8YZ6QNG7AVV44F178QWGF",
        )
        self.assertEqual(
            claim["rollback_reference"],
            "registry.fly.io/veritas-8825-systems:deployment-01KPGWP7RH54EMHFZ649Y4ZG9B",
        )
        self.assertEqual(claim["coordination_refs"][0]["source_type"], "spine_snapshot")
        self.assertFalse(claim["network_accessed"])
        self.assertFalse(claim["secrets_accessed"])

    def test_local_evidence_adapter_rejects_missing_allowed_input(self):
        with self.assertRaises(FileNotFoundError):
            LocalEvidenceAdapter(
                smoke_receipt_path=FIXTURE_PATH.parent / "missing.md",
                monitoring_review_path=FIXTURE_PATH.parent / "v17_monitoring_review.md",
                spine_snapshot_path=FIXTURE_PATH.parent / "local_work_lane_spine_snapshot.json",
            ).read_sources()

    def test_bundled_manifest_is_fixed_path_and_claim_ready(self):
        manifest_path = FIXTURE_PATH.parents[2] / "claims" / "runtime_status_manifest.json"
        claim = mediate_runtime_status(
            LocalEvidenceAdapter.from_bundled_manifest(manifest_path),
            now=NOW,
        )

        self.assertEqual(claim["status"], "SUPPORTED")
        self.assertEqual(claim["coordination_refs"][0]["authority_class"], "SPINE_COORDINATION")
        self.assertFalse(claim["authority_created_by_veritas"])
        with self.assertRaises(ValueError):
            LocalEvidenceAdapter.from_bundled_manifest(FIXTURE_PATH)


if __name__ == "__main__":
    unittest.main()
