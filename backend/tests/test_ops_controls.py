"""Operational controls tests (packet wpk_fa189292ad894c1e node
cost_latency_and_operational_controls).

Proves: truthful cost accounting (zero vs unmeasured), ceilings fail
closed, rate limiter/concurrency bounds refuse excess, circuit breaker
opens on consecutive failures and half-opens after cooldown, correlation
ids span the receipt, and the read-only cache honors TTL.
"""

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from ops.telemetry import (  # noqa: E402
    BudgetExceeded, CallTelemetry, Ceilings, CircuitBreaker, CircuitOpen,
    ConcurrencyGate, RateLimited, SafeReadCache, ServiceMetrics,
    TokenBucket, classify_provider_error, estimate_cost_usd,
)


class TestCostTruth(unittest.TestCase):
    def test_estimated_cost_known_model(self):
        c = estimate_cost_usd("gpt-4o", 1000, 500)
        self.assertAlmostEqual(c, 1000 * 2.5e-6 + 500 * 10e-6)

    def test_unmeasured_is_none_not_zero(self):
        self.assertIsNone(estimate_cost_usd("gpt-4o", None, None))
        self.assertIsNone(estimate_cost_usd("unknown-model", 100, 10))

    def test_receipt_distinguishes_unmeasured(self):
        t = CallTelemetry(correlation_id="vx-test")
        t.record(kind="chat", model="unknown-model", latency_ms=10,
                 prompt_tokens=None)
        r = t.receipt()
        self.assertIsNone(r["total_cost_usd"])
        self.assertEqual(r["cost_unmeasured_calls"], 1)
        t2 = CallTelemetry()
        t2.record(kind="chat", model="gpt-4o", latency_ms=5,
                  prompt_tokens=100, completion_tokens=50)
        self.assertGreater(t2.receipt()["total_cost_usd"], 0)


class TestCeilings(unittest.TestCase):
    def test_prompt_token_ceiling(self):
        t = CallTelemetry(ceilings=Ceilings(max_prompt_tokens=10))
        with self.assertRaises(BudgetExceeded):
            t.record(kind="chat", model="gpt-4o", latency_ms=1,
                     prompt_tokens=11)

    def test_latency_ceiling(self):
        t = CallTelemetry(ceilings=Ceilings(max_latency_ms=5))
        with self.assertRaises(BudgetExceeded):
            t.record(kind="chat", model="gpt-4o", latency_ms=50)

    def test_cost_ceiling(self):
        t = CallTelemetry(ceilings=Ceilings(max_cost_usd=0.000001))
        with self.assertRaises(BudgetExceeded):
            t.record(kind="chat", model="gpt-4o", latency_ms=1,
                     prompt_tokens=10000, completion_tokens=10000)

    def test_within_ceiling_passes(self):
        t = CallTelemetry(ceilings=Ceilings())
        t.record(kind="chat", model="gpt-4o", latency_ms=100,
                 prompt_tokens=100, completion_tokens=50)
        self.assertEqual(len(t.calls), 1)


class TestRateAndConcurrency(unittest.TestCase):
    def test_token_bucket_refuses_after_burst(self):
        b = TokenBucket(rate_per_minute=0, burst=3)
        for _ in range(3):
            b.acquire()
        with self.assertRaises(RateLimited):
            b.acquire()

    def test_bucket_refills(self):
        b = TokenBucket(rate_per_minute=6000, burst=1)
        b.acquire()
        with self.assertRaises(RateLimited):
            b.acquire()
        time.sleep(0.05)  # 6000rpm = 100/s -> refill within 50ms
        b.acquire()

    def test_concurrency_gate_fails_closed(self):
        g = ConcurrencyGate(max_concurrent=1)
        g.acquire()
        with self.assertRaises(RateLimited):
            g.acquire()
        g.release()
        g.acquire()  # released slot reusable
        g.release()


class TestCircuitBreaker(unittest.TestCase):
    def test_opens_after_threshold_and_fails_closed(self):
        cb = CircuitBreaker(threshold=2, cooldown_s=60)
        cb.before_call(); cb.after_call(ok=False)
        cb.before_call(); cb.after_call(ok=False)
        self.assertEqual(cb.state, "open")
        with self.assertRaises(CircuitOpen):
            cb.before_call()

    def test_half_open_probe_then_close(self):
        cb = CircuitBreaker(threshold=1, cooldown_s=0.01)
        cb.before_call(); cb.after_call(ok=False)
        self.assertEqual(cb.state, "open")
        time.sleep(0.02)
        self.assertEqual(cb.state, "half_open")
        cb.before_call()              # single probe admitted
        with self.assertRaises(CircuitOpen):
            cb.before_call()          # second probe refused
        cb.after_call(ok=True)        # probe succeeded -> closed
        self.assertEqual(cb.state, "closed")
        cb.before_call(); cb.after_call(ok=True)

    def test_probe_failure_reopens(self):
        cb = CircuitBreaker(threshold=1, cooldown_s=0.01)
        cb.before_call(); cb.after_call(ok=False)
        time.sleep(0.02)
        cb.before_call(); cb.after_call(ok=False)
        self.assertEqual(cb.state, "open")


class TestSanitizationAndCorrelation(unittest.TestCase):
    def test_provider_errors_classified(self):
        class TimeoutError(Exception):
            pass
        self.assertEqual(classify_provider_error(TimeoutError("x")),
                         "timeout")
        self.assertEqual(classify_provider_error(ValueError("boom")),
                         "other")

    def test_correlation_id_spans_calls(self):
        t = CallTelemetry(correlation_id="vx-abc")
        t.record(kind="embedding", model="text-embedding-3-small",
                 latency_ms=1, prompt_tokens=5)
        t.record(kind="chat", model="gpt-4o", latency_ms=2,
                 prompt_tokens=10, completion_tokens=5)
        r = t.receipt()
        self.assertEqual(r["correlation_id"], "vx-abc")
        self.assertTrue(all(c["correlation_id"] == "vx-abc"
                            for c in r["calls"]))
        self.assertEqual(r["provider_calls"], 2)

    def test_metrics_counters(self):
        m = ServiceMetrics()
        m.inc("synthesize_requests"); m.inc("provider_timeouts")
        snap = m.snapshot()
        self.assertEqual(snap["synthesize_requests"], 1)
        self.assertEqual(snap["provider_timeouts"], 1)
        self.assertEqual(snap["circuit_rejections"], 0)  # measured zero

    def test_read_cache_ttl(self):
        c = SafeReadCache(ttl_s=0.01)
        self.assertIsNone(c.get("k"))
        c.put("k", ["a"])
        self.assertEqual(c.get("k"), ["a"])
        time.sleep(0.02)
        self.assertIsNone(c.get("k"))


if __name__ == "__main__":
    unittest.main()
