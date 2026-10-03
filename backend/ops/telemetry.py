"""Operational controls for Veritas (packet wpk_fa189292ad894c1e node
cost_latency_and_operational_controls).

Provider telemetry, per-call ceilings, process rate limiting,
concurrency bounds, circuit breaking, and request correlation.

Truthfulness rules baked in:
  - metrics distinguish zero (measured, value 0) from unmeasured
    (null) — absent instrumentation is never reported as 0 cost
  - ceilings, rate limits, and the circuit breaker fail CLOSED —
    a breached bound refuses the call rather than degrading silently
  - provider errors are recorded by class only (timeout, auth, rate,
    other) — raw provider error text never enters logs or receipts
"""

import os
import threading
import time
import uuid
from typing import Dict, List, Optional

# USD per token — proposed defaults; operator-overridable by env.
# (input, output) pairs; embeddings have output=0.
_MODEL_PRICES = {
    "gpt-4o": (2.50e-6, 10.0e-6),
    "gpt-4o-mini": (0.15e-6, 0.60e-6),
    "text-embedding-3-small": (0.02e-6, 0.0),
    "text-embedding-3-large": (0.13e-6, 0.0),
}


def estimate_cost_usd(model: str, prompt_tokens: Optional[int],
                      completion_tokens: Optional[int]) -> Optional[float]:
    """Estimated USD cost; None when token usage is unmeasured — never
    silently reports unmeasured usage as free."""
    if prompt_tokens is None and completion_tokens is None:
        return None
    prices = _MODEL_PRICES.get(model)
    if prices is None:
        return None
    return (prompt_tokens or 0) * prices[0] \
        + (completion_tokens or 0) * prices[1]


def classify_provider_error(exc: Exception) -> str:
    """Error class only — provider messages may carry internals."""
    name = type(exc).__name__.lower()
    if "timeout" in name or "timedout" in name:
        return "timeout"
    if "auth" in name or "permission" in name:
        return "auth"
    if "rate" in name:
        return "rate_limit"
    if "connection" in name:
        return "connection"
    return "other"


class BudgetExceeded(Exception):
    """Raised when a call would cross a configured ceiling."""


class CircuitOpen(Exception):
    """Raised when the provider circuit breaker refuses a call."""


class RateLimited(Exception):
    """Raised when the request rate exceeds the configured bucket."""


class Ceilings:
    def __init__(self,
                 max_prompt_tokens: int = None,
                 max_total_tokens: int = None,
                 max_latency_ms: float = None,
                 max_cost_usd: float = None):
        e = os.environ.get
        self.max_prompt_tokens = max_prompt_tokens if \
            max_prompt_tokens is not None else \
            int(e("VERITAS_MAX_PROMPT_TOKENS", "12000"))
        self.max_total_tokens = max_total_tokens if \
            max_total_tokens is not None else \
            int(e("VERITAS_MAX_TOTAL_TOKENS", "16000"))
        self.max_latency_ms = max_latency_ms if max_latency_ms is not None \
            else float(e("VERITAS_MAX_CALL_LATENCY_MS", "45000"))
        self.max_cost_usd = max_cost_usd if max_cost_usd is not None else \
            float(e("VERITAS_MAX_CALL_COST_USD", "0.25"))

    def check(self, record: dict):
        if record.get("prompt_tokens") is not None and \
                record["prompt_tokens"] > self.max_prompt_tokens:
            raise BudgetExceeded("PROMPT_TOKEN_CEILING")
        total = (record.get("prompt_tokens") or 0) + \
            (record.get("completion_tokens") or 0)
        if record.get("prompt_tokens") is not None and \
                total > self.max_total_tokens:
            raise BudgetExceeded("TOTAL_TOKEN_CEILING")
        if record.get("latency_ms") is not None and \
                record["latency_ms"] > self.max_latency_ms:
            raise BudgetExceeded("LATENCY_CEILING")
        if record.get("cost_usd") is not None and \
                record["cost_usd"] > self.max_cost_usd:
            raise BudgetExceeded("COST_CEILING")


class CallTelemetry:
    """Per-request provider telemetry with one correlation id spanning
    the gateway request, provider attempts, stored result and receipt."""

    def __init__(self, correlation_id: str = None,
                 ceilings: Ceilings = None):
        self.correlation_id = correlation_id or f"vx-{uuid.uuid4()}"
        self.ceilings = ceilings or Ceilings()
        self.calls: List[Dict] = []

    def record(self, *, kind: str, model: str, latency_ms: float,
               prompt_tokens: Optional[int] = None,
               completion_tokens: Optional[int] = None,
               ok: bool = True, error_class: Optional[str] = None):
        rec = {
            "kind": kind, "model": model,
            "latency_ms": round(latency_ms, 1),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": estimate_cost_usd(model, prompt_tokens,
                                          completion_tokens),
            "ok": ok, "error_class": error_class,
            "correlation_id": self.correlation_id,
        }
        self.ceilings.check(rec)
        self.calls.append(rec)
        return rec

    def receipt(self) -> dict:
        """Bounded truthful receipt — actual provider work and cost."""
        measured = [c for c in self.calls if c["cost_usd"] is not None]
        return {
            "correlation_id": self.correlation_id,
            "provider_calls": len(self.calls),
            "failures": sum(1 for c in self.calls if not c["ok"]),
            "total_prompt_tokens": sum(c["prompt_tokens"] or 0
                                       for c in self.calls),
            "total_completion_tokens": sum(c["completion_tokens"] or 0
                                           for c in self.calls),
            "total_latency_ms": round(sum(c["latency_ms"]
                                          for c in self.calls), 1),
            # null when no call returned usage — unmeasured, not free
            "total_cost_usd": round(sum(c["cost_usd"] for c in
                                        measured), 6)
                if measured else None,
            "cost_measured_calls": len(measured),
            "cost_unmeasured_calls": len(self.calls) - len(measured),
            "calls": self.calls,
        }


class TokenBucket:
    """Process-local rate limiter; fails closed (RateLimited)."""

    def __init__(self, rate_per_minute: int = None, burst: int = None):
        e = os.environ.get
        self.rate = rate_per_minute if rate_per_minute is not None else \
            int(e("VERITAS_RATE_RPM", "60"))
        self.burst = burst if burst is not None else \
            int(e("VERITAS_RATE_BURST", "10"))
        self._tokens = float(self.burst)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self):
        with self._lock:
            now = time.monotonic()
            self._tokens = min(self.burst,
                               self._tokens
                               + (now - self._last) * self.rate / 60.0)
            self._last = now
            if self._tokens < 1.0:
                raise RateLimited("RATE_LIMITED")
            self._tokens -= 1.0


class ConcurrencyGate:
    """Bounded concurrency; fails closed rather than queueing without
    bound."""

    def __init__(self, max_concurrent: int = None):
        e = os.environ.get
        limit = max_concurrent if max_concurrent is not None else \
            int(e("VERITAS_MAX_CONCURRENCY", "4"))
        self._sem = threading.BoundedSemaphore(limit)

    def acquire(self):
        if not self._sem.acquire(blocking=False):
            raise RateLimited("CONCURRENCY_BOUND")

    def release(self):
        self._sem.release()


class CircuitBreaker:
    """Provider circuit breaker. Opens after N consecutive provider
    failures; while open every call fails closed fast; after the
    cooldown a single half-open probe is allowed."""

    def __init__(self, threshold: int = None, cooldown_s: float = None):
        e = os.environ.get
        self.threshold = threshold if threshold is not None else \
            int(e("VERITAS_BREAKER_THRESHOLD", "3"))
        self.cooldown_s = cooldown_s if cooldown_s is not None else \
            float(e("VERITAS_BREAKER_COOLDOWN_S", "30"))
        self._consecutive_failures = 0
        self._opened_at: Optional[float] = None
        self._probe_in_flight = False
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "closed"
        if time.monotonic() - self._opened_at >= self.cooldown_s:
            return "half_open"
        return "open"

    def before_call(self):
        with self._lock:
            st = self.state
            if st == "open":
                raise CircuitOpen("CIRCUIT_OPEN")
            if st == "half_open":
                if self._probe_in_flight:
                    raise CircuitOpen("CIRCUIT_OPEN")
                self._probe_in_flight = True

    def after_call(self, ok: bool):
        with self._lock:
            if self.state == "half_open":
                self._probe_in_flight = False
            if ok:
                self._consecutive_failures = 0
                self._opened_at = None
            else:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.threshold:
                    self._opened_at = time.monotonic()


class ServiceMetrics:
    """Process counters. Convention: counters present = measured zeros;
    metrics not yet instrumented for a request are absent (null in
    receipts), never coerced to 0."""

    KEYS = ("synthesize_requests", "synthesize_abstentions",
            "synthesize_rate_limited", "synthesize_concurrency_rejected",
            "provider_retries", "provider_timeouts",
            "provider_failures", "circuit_rejections",
            "budget_rejections", "result_read_failures",
            "history_write_failures")

    def __init__(self):
        self._c = {k: 0 for k in self.KEYS}
        self._lock = threading.Lock()

    def inc(self, key: str):
        with self._lock:
            self._c[key] = self._c.get(key, 0) + 1

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._c)


class SafeReadCache:
    """TTL cache for read-only surfaces only (examples list). Mutation
    surfaces never route through it. Invalidation: TTL expiry or process
    restart — documented contract, no implicit staleness."""

    def __init__(self, ttl_s: float = 60.0):
        self.ttl_s = ttl_s
        self._store: Dict[str, tuple] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires = entry
            if time.monotonic() >= expires:
                del self._store[key]
                return None
            return value

    def put(self, key: str, value):
        with self._lock:
            self._store[key] = (value, time.monotonic() + self.ttl_s)
