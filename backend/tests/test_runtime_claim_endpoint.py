import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "fixture-test-key")
sys.path.insert(0, str(Path(__file__).parents[1]))

from app import app


class RuntimeClaimEndpointTests(unittest.TestCase):
    def setUp(self):
        self.previous = app.config.get("VERITAS_INTERNAL_CLAIMS_ENABLED")

    def tearDown(self):
        app.config["VERITAS_INTERNAL_CLAIMS_ENABLED"] = self.previous

    def test_endpoint_is_disabled_by_default(self):
        app.config["VERITAS_INTERNAL_CLAIMS_ENABLED"] = False
        response = app.test_client().get(
            "/api/claims/runtime-status",
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )
        self.assertEqual(response.status_code, 404)

    def test_endpoint_requires_loopback_when_enabled(self):
        app.config["VERITAS_INTERNAL_CLAIMS_ENABLED"] = True
        response = app.test_client().get(
            "/api/claims/runtime-status",
            environ_base={"REMOTE_ADDR": "10.0.0.8"},
        )
        self.assertEqual(response.status_code, 404)

    def test_loopback_endpoint_returns_claim_schema_when_enabled(self):
        app.config["VERITAS_INTERNAL_CLAIMS_ENABLED"] = True
        response = app.test_client().get(
            "/api/claims/runtime-status",
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["schema_version"], "veritas_claim/0.1.0")
        self.assertIn(payload["status"], {"SUPPORTED", "STALE", "UNKNOWN"})
        self.assertFalse(payload["authority_created_by_veritas"])
        self.assertFalse(payload["network_accessed"])
        self.assertFalse(payload["secrets_accessed"])


if __name__ == "__main__":
    unittest.main()
