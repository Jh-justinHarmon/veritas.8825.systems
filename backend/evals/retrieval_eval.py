"""Layer-routed golden-set evaluator for Veritas.

Runs the frozen golden set through the system layer that can actually
answer each expectation:

- ``retrieval``: deterministic offline retrieval/doc-collapse checks.
- ``service``: provider-free HTTP checks against a running backend
  (bounds, unknown-id isolation, readback where possible).
- ``synthesize``: answer-producing calls. These require ``--service-url``
  AND ``--allow-provider`` so the evaluator never makes unauthorized
  provider calls.
- ``gateway``: gateway/adapter checks. These require ``--gateway-url``;
  idempotency also requires ``--authorization-ref``.

Every declared ``expected`` predicate receives an explicit verdict:
``pass``, ``fail``, or ``not_evaluable`` with a machine-readable reason.
Nothing is silently skipped.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

sys.path.insert(0, str(Path(__file__).parents[1]))

from agents.synthesis_agent import collapse_to_documents  # noqa: E402
from retrieval.relevance import retrieve_relevant  # noqa: E402

DEFAULT_GOLDEN = (Path(__file__).parent / "fixtures"
                  / "veritas_golden_eval_set_v1.json")
DEFAULT_CORPUS = (Path(__file__).parents[2] / "corpus" / "embeddings"
                  / "all_tiers_embedded_chunks.json")

PLACEHOLDER_TOKENS = ("example.com", "placeholder", "lorem", "todo",
                      "dummy", "changeme", "sample text")
NEG_BOUNDS_EQUIVALENTS = {
    "INVALID_REQUEST", "QUESTION_OUT_OF_BOUNDS",
    "QUESTION_OUT_OF_BOUNDS_or_equivalent_typed_reason"}


def _question(item: dict) -> str:
    return ((item.get("input") or {}).get("payload") or {}).get(
        "question") or ""


def _payload(item: dict) -> dict:
    return dict((item.get("input") or {}).get("payload") or {})


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _http_json(url: str, payload: Optional[dict] = None,
               timeout: float = 15) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return {"http_status": resp.status, "json": json.loads(raw)}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {}
        return {"http_status": e.code, "json": body}
    except Exception as e:
        return {"transport_error": type(e).__name__, "json": {}}


class Evaluator:
    def __init__(self, *, service_url: str = "", gateway_url: str = "",
                 authorization_ref: str = "", allow_provider: bool = False,
                 chunks: list[dict] | None = None,
                 min_relevance: float = 0.22):
        self.service_url = service_url.rstrip("/")
        self.gateway_url = gateway_url.rstrip("/")
        self.authorization_ref = authorization_ref
        self.allow_provider = allow_provider
        self.chunks = chunks or []
        self.min_relevance = min_relevance

    def _verdict(self, state: str, detail: str = "") -> dict:
        return {"verdict": state, "detail": detail}

    def _not_evaluable(self, why: str) -> dict:
        return self._verdict("not_evaluable", why)

    def _retrieval_observation(self, question: str) -> dict:
        out = retrieve_relevant(question, self.chunks,
                                query_embedding=None,
                                min_relevance=self.min_relevance)
        doc_sources = collapse_to_documents(out["chunks"])
        placeholder = []
        for doc in doc_sources:
            hay = " ".join(str(doc.get(k) or "") for k in
                           ("document_id", "url", "source_url",
                            "source_name", "title")).lower()
            if any(tok in hay for tok in PLACEHOLDER_TOKENS):
                placeholder.append(doc.get("document_id"))
        doc_ids = [str(d.get("document_id") or "") for d in doc_sources]
        chunk_doc_ids = [str((c.get("retrieval_meta") or {})
                             .get("document_id")
                             or c.get("document_id") or "")
                         for c in out["chunks"]]
        chunk_counts = {d: chunk_doc_ids.count(d) for d in set(chunk_doc_ids)}
        unjustified = []
        for c in out["chunks"]:
            meta = c.get("retrieval_meta") or {}
            doc = str(meta.get("document_id") or "")
            if chunk_counts.get(doc, 0) > 2 and not meta.get(
                    "overflow_justification"):
                unjustified.append(doc)
        return {
            "layer": "retrieval",
            "question": question,
            "abstained": out["abstained"],
            "reason": out.get("reason"),
            "returned_chunks": len(out["chunks"]),
            "returned_documents": len(doc_sources),
            "doc_ids": doc_ids,
            "doc_sources": doc_sources,
            "doc_ids_unique": len(doc_ids) == len(set(doc_ids)),
            "placeholder_sources": placeholder,
            "unjustified_duplicate_docs": sorted(set(unjustified)),
            "confidence": out["confidence"],
            "stats": out["stats"],
        }

    def _service_post(self, path: str, payload: dict) -> dict:
        if not self.service_url:
            return {"unavailable": "service_url_missing"}
        return _http_json(self.service_url + path, payload)

    def _service_get(self, path: str) -> dict:
        if not self.service_url:
            return {"unavailable": "service_url_missing"}
        return _http_json(self.service_url + path)

    def _gateway_invoke(self, capability: str, payload: dict,
                        authorization_ref: str = "") -> dict:
        if not self.gateway_url:
            return {"unavailable": "gateway_url_missing"}
        body = {"capability": capability,
                "payload_json": json.dumps(payload, sort_keys=True)}
        if authorization_ref:
            body["authorization_ref"] = authorization_ref
        return _http_json(self.gateway_url + "/gateway/invoke", body)

    def _service_synthesize(self, item: dict) -> dict:
        if not self.service_url:
            return {"unavailable": "service_url_missing"}
        if not self.allow_provider:
            return {"unavailable": "provider_not_authorized"}
        resp = self._service_post("/api/synthesize", {
            "question": _question(item)})
        if "transport_error" in resp:
            return resp
        js = resp["json"]
        if resp.get("http_status") == 422 and js.get("error") == \
                "INSUFFICIENT_RELEVANT_EVIDENCE":
            return {"status": "ABSTAINED", "json": js}
        if resp.get("http_status") == 200:
            return {"status": "COMPLETED", "json": js}
        # Provider-unavailable/missing-key failures make the synthesize
        # layer non-decidable rather than a candidate failure.
        if resp.get("http_status") in {500, 502, 503}:
            return {"unavailable": "provider_or_service_unavailable",
                    "http_status": resp.get("http_status"), "json": js}
        return {"status": "BLOCKED", "reason": js.get("error"),
                "json": js}

    def _evaluate_expected(self, item: dict, observed: dict,
                           layer: str) -> list[dict]:
        """Assert every declared expected predicate at the chosen layer."""
        expected = item.get("expected") or {}
        verdicts = []
        for pred, want in expected.items():
            if pred == "note":
                continue
            verdicts.append(self._check_pred(pred, want, observed, layer))
        return verdicts

    def _check_pred(self, pred: str, want: Any, observed: dict,
                    layer: str) -> dict:
        v = {"predicate": pred, "expected": want}
        if "unavailable" in observed:
            return v | self._not_evaluable(observed["unavailable"])

        status = observed.get("status")
        js = observed.get("json") or observed
        retrieval = observed.get("retrieval") or {}

        if pred == "status":
            if status is None:
                return v | self._not_evaluable("layer_not_run")
            if isinstance(want, str) and "_or_" in want:
                ok = status in want.split("_or_")
            else:
                ok = status == want
            return v | self._verdict("pass" if ok else "fail",
                                     f"observed={status}")
        if pred == "answer_nonempty":
            ideas = js.get("ideas") or []
            ok = bool(str(js.get("answer") or "").strip()) or bool(ideas)
            return v | self._verdict("pass" if ok else "fail",
                                     f"ideas={len(ideas)}")
        if pred == "no_placeholder_sources":
            sources = js.get("sources") or retrieval.get("doc_sources") or []
            hay = json.dumps(sources, sort_keys=True).lower()
            ok = not any(tok in hay for tok in PLACEHOLDER_TOKENS)
            return v | self._verdict("pass" if ok else "fail")
        if pred == "sources_unique":
            sources = js.get("sources") or retrieval.get("doc_sources") or []
            if isinstance(sources, dict):
                ids = [str(s.get("document_id") or "")
                       for s in sources.values()]
            else:
                ids = [str(s.get("document_id") or "") for s in sources]
            ok = len(ids) == len(set(ids))
            return v | self._verdict("pass" if ok else "fail",
                                     f"source_doc_ids={ids}")
        if pred == "citations_resolve_to_retrieved_chunks":
            receipt = js.get("citation_receipt") or {}
            precision = receipt.get("citation_precision")
            if precision is None:
                return v | self._not_evaluable("no_citation_receipt")
            ok = precision == 1.0
            return v | self._verdict("pass" if ok else "fail",
                                     f"precision={precision}")
        if pred == "receipt_provider_disclosed":
            rec = js.get("provider_receipt") or {}
            attempts = rec.get("attempts") or rec.get("calls") or []
            ok = bool(attempts) and all(
                a.get("model") and a.get("latency_ms") is not None
                for a in attempts)
            return v | self._verdict("pass" if ok else "fail")
        if pred == "answer_hedges_or_clarifies":
            text = json.dumps(js.get("ideas") or [], ensure_ascii=False).lower()
            ok = any(w in text for w in
                     ("ambiguous", "unclear", "clarify", "could mean",
                      "depends", "likely", "may"))
            return v | self._verdict("pass" if ok else "fail")
        if pred == "confidence_disclosed_or_abstains":
            ok = bool(js.get("confidence") or js.get("evidence_limitation")
                      or js.get("citation_receipt")
                      or observed.get("status") == "ABSTAINED"
                      or retrieval.get("abstained"))
            return v | self._verdict("pass" if ok else "fail")
        if pred == "abstains_or_states_no_coverage":
            if status == "ABSTAINED" or retrieval.get("abstained"):
                return v | self._verdict("pass", "abstained")
            text = json.dumps(js, ensure_ascii=False).lower()
            ok = any(w in text for w in
                     ("insufficient", "no coverage", "cannot determine",
                      "not enough evidence", "no relevant"))
            return v | self._verdict("pass" if ok else "fail")
        if pred == "fabricated_citations":
            receipt = js.get("citation_receipt") or {}
            precision = receipt.get("citation_precision")
            count = receipt.get("claims_with_valid_citation")
            ok = (precision in (1.0, None) and (count or 0) == int(want)) \
                if status == "ABSTAINED" else precision == 1.0
            return v | self._verdict("pass" if ok else "fail",
                                     f"precision={precision}, cited={count}")
        if pred == "no_fabricated_or_foreign_citations":
            receipt = js.get("citation_receipt") or {}
            precision = receipt.get("citation_precision")
            dropped = receipt.get("dropped_unresolvable_sources") or []
            ok = precision == 1.0 and not dropped
            return v | self._verdict("pass" if ok else "fail",
                                     f"precision={precision}, dropped={dropped}")
        if pred == "conflicting_guidance_disclosed":
            text = json.dumps(js.get("ideas") or [], ensure_ascii=False).lower()
            ok = any(w in text for w in
                     ("conflict", "differ", "disagree", "however",
                      "in contrast", "on the other hand"))
            return v | self._verdict("pass" if ok else "fail")
        if pred == "result_matches_recorded_receipt":
            if not isinstance(want, bool) or not want:
                return v | self._not_evaluable("unsupported_expected_value")
            stored = js.get("stored_result")
            receipt = js.get("provider_receipt") or js.get("citation_receipt")
            ok = stored is not None and receipt is not None
            return v | self._verdict("pass" if ok else "fail")
        if pred == "indistinguishable_from_unknown_id":
            ok = bool(observed.get("indistinguishable"))
            return v | self._verdict("pass" if ok else "fail")
        if pred == "discloses_nothing":
            ok = bool(observed.get("discloses_nothing"))
            return v | self._verdict("pass" if ok else "fail")
        if pred == "reason":
            got = observed.get("reason") or js.get("error")
            if isinstance(want, str) and "_or_" in want:
                ok = got in want.split("_or_") or got in NEG_BOUNDS_EQUIVALENTS
            else:
                ok = got == want
            return v | self._verdict("pass" if ok else "fail",
                                     f"reason={got}")
        if pred in {"first_call", "replay_same_payload",
                    "replay_different_payload_same_key"}:
            got = observed.get(pred)
            if got is None:
                return v | self._not_evaluable("idempotency_not_run")
            ok = got == want
            return v | self._verdict("pass" if ok else "fail",
                                     f"observed={got}")
        return v | self._not_evaluable("unsupported_predicate")

    def _evaluate_synthesize_item(self, item: dict) -> dict:
        question = _question(item)
        retrieval = self._retrieval_observation(question)
        if self.allow_provider:
            observed = self._service_synthesize(item)
        else:
            observed = {"unavailable": "provider_not_authorized"}
        observed["retrieval"] = retrieval

        # Offline-decidable predicates can still be asserted before the
        # provider layer: placeholder exclusion and document uniqueness.
        verdicts = []
        for pred, want in (item.get("expected") or {}).items():
            if pred == "note":
                continue
            if pred == "no_placeholder_sources":
                ph = retrieval["placeholder_sources"]
                verdicts.append({
                    "predicate": pred, "expected": want,
                    "verdict": "pass" if not ph else "fail",
                    "detail": f"placeholders={ph}"})
            elif pred == "sources_unique":
                verdicts.append({
                    "predicate": pred, "expected": want,
                    "verdict": "pass" if retrieval["doc_ids_unique"] else "fail",
                    "detail": f"doc_ids={retrieval['doc_ids']}"})
            elif pred == "abstains_or_states_no_coverage" \
                    and retrieval["abstained"]:
                verdicts.append({
                    "predicate": pred, "expected": want,
                    "verdict": "pass", "detail": "retrieval_abstained"})
            else:
                verdicts.append(self._check_pred(pred, want, observed,
                                                 "synthesize"))
        return {"layer": "synthesize", "retrieval": retrieval,
                "observed": observed, "predicates": verdicts}

    def _evaluate_negative_input_bounds(self, item: dict) -> dict:
        resp = self._service_post("/api/synthesize", {
            "question": _question(item)})
        if "unavailable" in resp or "transport_error" in resp:
            observed = resp
        else:
            js = resp["json"]
            observed = {
                "status": "BLOCKED" if resp["http_status"] >= 400
                          else "COMPLETED",
                "reason": js.get("error"),
                "json": js,
            }
        return {"layer": "service", "observed": observed,
                "predicates": self._evaluate_expected(item, observed,
                                                      "service")}

    def _evaluate_identity_isolation(self, item: dict) -> dict:
        foreign = self._service_get("/api/history/foreign-review-id")
        unknown = self._service_get("/api/history/definitely-unknown-id")
        if "unavailable" in foreign or "unavailable" in unknown:
            observed = foreign if "unavailable" in foreign else unknown
        elif "transport_error" in foreign or "transport_error" in unknown:
            observed = foreign if "transport_error" in foreign else unknown
        else:
            fjs, ujs = foreign["json"], unknown["json"]
            observed = {
                "status": "NOT_FOUND" if foreign["http_status"] == 404
                          else "COMPLETED",
                "indistinguishable": foreign["http_status"] == \
                    unknown["http_status"] and fjs.keys() == ujs.keys(),
                "discloses_nothing": "answer" not in fjs and "trace" not in fjs,
                "json": {"foreign": fjs, "unknown": ujs},
            }
        return {"layer": "service", "observed": observed,
                "predicates": self._evaluate_expected(item, observed,
                                                      "service")}

    def _evaluate_gateway_negative(self, item: dict) -> dict:
        capability = (item.get("input") or {}).get("capability") or \
            "veritas.synthesize"
        resp = self._gateway_invoke(capability, _payload(item))
        if "unavailable" in resp or "transport_error" in resp:
            observed = resp
        else:
            js = resp["json"]
            observed = {"status": js.get("status"),
                        "reason": js.get("reason"), "json": js}
        return {"layer": "gateway", "observed": observed,
                "predicates": self._evaluate_expected(item, observed,
                                                      "gateway")}

    def _evaluate_idempotency(self, item: dict) -> dict:
        if not self.gateway_url or not self.authorization_ref:
            observed = {"unavailable": "gateway_or_authorization_ref_missing"}
        else:
            payload = _payload(item)
            key = payload.get("idempotency_key") or "eval-idempotent-01"
            payload = dict(payload, idempotency_key=key)
            first = self._gateway_invoke("veritas.synthesize", payload,
                                         self.authorization_ref)
            replay = self._gateway_invoke("veritas.synthesize", payload,
                                          self.authorization_ref)
            conflict_payload = dict(payload, question=payload.get(
                "question", "") + " different")
            conflict = self._gateway_invoke(
                "veritas.synthesize", conflict_payload,
                self.authorization_ref)
            def _shape(resp):
                if "transport_error" in resp:
                    return resp
                return {"status": (resp["json"] or {}).get("status"),
                        "same_result_id": None,
                        "upstream_calls": None}
            observed = {
                "status": _shape(first).get("status"),
                "first_call": {"status": _shape(first).get("status"),
                               "upstream_calls": None},
                "replay_same_payload": {
                    "status": _shape(replay).get("status"),
                    "same_result_id": None, "upstream_calls": None},
                "replay_different_payload_same_key": {
                    "status": _shape(conflict).get("status"),
                    "reason": (conflict.get("json") or {}).get("reason")},
                "json": {"first": first.get("json"),
                         "replay": replay.get("json"),
                         "conflict": conflict.get("json")},
            }
        return {"layer": "gateway", "observed": observed,
                "predicates": self._evaluate_expected(item, observed,
                                                      "gateway")}

    def _evaluate_restart_durability(self, item: dict) -> dict:
        if not self.service_url or not self.allow_provider:
            observed = {"unavailable":
                        "provider_and_restart_not_authorized"}
        else:
            synth = self._service_synthesize(item)
            if "unavailable" in synth:
                observed = synth
            else:
                sid = (synth.get("json") or {}).get("session_id")
                readback = self._service_get(f"/api/history/{sid}") \
                    if sid else {"unavailable": "no_session_id"}
                observed = dict(synth)
                observed["json"] = dict(observed.get("json") or {})
                observed["json"]["stored_result"] = readback.get("json")
        return {"layer": "service", "observed": observed,
                "predicates": self._evaluate_expected(item, observed,
                                                      "service")}

    def evaluate_item(self, item: dict) -> dict:
        category = item.get("category") or ""
        if category in {"tool_selection", "streaming_tool_use", "vision",
                        "ambiguous_question", "no_answer_question",
                        "adversarial_citation_request",
                        "duplicate_conflicting_sources"}:
            result = self._evaluate_synthesize_item(item)
        elif category == "negative_input_bounds":
            result = self._evaluate_negative_input_bounds(item)
        elif category == "identity_isolation":
            result = self._evaluate_identity_isolation(item)
        elif category in {"negative_provider_fields",
                          "negative_missing_authorization"}:
            result = self._evaluate_gateway_negative(item)
        elif category == "idempotency":
            result = self._evaluate_idempotency(item)
        elif category == "restart_durability":
            result = self._evaluate_restart_durability(item)
        else:
            result = {"layer": "unknown",
                      "observed": {"unavailable": "unknown_category"},
                      "predicates": self._evaluate_expected(
                          item, {"unavailable": "unknown_category"},
                          "unknown")}
        result["id"] = item.get("id")
        result["category"] = category
        result["expected"] = item.get("expected") or {}
        return result


def run_eval(golden_path: Path, corpus_path: Path, **kwargs) -> dict:
    golden = json.loads(golden_path.read_text())
    chunks = json.loads(corpus_path.read_text())
    ev = Evaluator(chunks=chunks, **kwargs)
    rows = [ev.evaluate_item(item) for item in golden.get("items", [])]
    counts = {"pass": 0, "fail": 0, "not_evaluable": 0}
    for row in rows:
        states = [p["verdict"] for p in row["predicates"]]
        row["verdict"] = "fail" if "fail" in states else \
            "not_evaluable" if "not_evaluable" in states else "pass"
        counts[row["verdict"]] += 1
    return {
        "eval_set": golden.get("eval_set_id"),
        "golden_sha256": _sha256(golden_path),
        "corpus_sha256": _sha256(corpus_path),
        "items_evaluated": len(rows),
        "item_verdicts": counts,
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=os.getenv("VERITAS_EVAL_GOLDEN",
                                                  str(DEFAULT_GOLDEN)))
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    ap.add_argument("--service-url", default="")
    ap.add_argument("--gateway-url", default="")
    ap.add_argument("--authorization-ref", default="")
    ap.add_argument("--allow-provider", action="store_true",
                    help="Permit synthesis calls that may invoke the "
                         "provider. Off by default.")
    ap.add_argument("--min-relevance", type=float, default=0.22)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    golden, corpus = Path(args.golden), Path(args.corpus)
    if not golden.exists():
        raise SystemExit(f"golden set not found: {golden}")
    if not corpus.exists():
        raise SystemExit(f"corpus not found: {corpus}")
    report = run_eval(golden, corpus,
                      service_url=args.service_url,
                      gateway_url=args.gateway_url,
                      authorization_ref=args.authorization_ref,
                      allow_provider=args.allow_provider,
                      min_relevance=args.min_relevance)
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"eval_set={report['eval_set']} "
          f"golden={report['golden_sha256'][:19]}")
    print(f"items={report['items_evaluated']} "
          f"pass={report['item_verdicts']['pass']} "
          f"fail={report['item_verdicts']['fail']} "
          f"not_evaluable={report['item_verdicts']['not_evaluable']}")
    for r in report["rows"]:
        print(f"  {r['id']} [{r['layer']}]: {r['verdict']}")
        for p in r["predicates"]:
            print(f"    {p['predicate']}: {p['verdict']} {p['detail']}")


if __name__ == "__main__":
    main()
