"""Read-only runtime/deployment claim mediation.

This module deliberately accepts already-captured local evidence records. It does
not read the network, query Fly, read secrets, write receipts, or create authority.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Protocol, Tuple

CLAIM_SCHEMA_VERSION = "veritas_claim/0.1.0"
FRESHNESS_WINDOW_SECONDS = 24 * 60 * 60
REQUIRED_SOURCE_TYPES = {"production_smoke_receipt", "monitoring_review"}
RECEIPT_AUTHORITY_CLASSES = {"RECEIPT_FACT", "RUNTIME_RECEIPT_FACT"}


@dataclass(frozen=True)
class RuntimeStatusSource:
    """One already-captured source record supplied by an evidence adapter."""

    source_id: str
    source_type: str
    authority_class: str
    observed_at: str
    source_ref: str
    source_hash: str
    receipt_id: Optional[str]
    result: str
    release: Optional[str]
    image: Optional[str]
    rollback_reference: Optional[str]

    @classmethod
    def from_mapping(cls, value: Dict[str, object]) -> "RuntimeStatusSource":
        required = ("source_id", "source_type", "authority_class", "observed_at", "source_ref", "source_hash", "result")
        missing = [key for key in required if not value.get(key)]
        if missing:
            raise ValueError(f"runtime source missing required fields: {', '.join(missing)}")
        return cls(
            source_id=str(value["source_id"]),
            source_type=str(value["source_type"]),
            authority_class=str(value["authority_class"]),
            observed_at=str(value["observed_at"]),
            source_ref=str(value["source_ref"]),
            source_hash=str(value["source_hash"]),
            receipt_id=str(value["receipt_id"]) if value.get("receipt_id") else None,
            result=str(value["result"]),
            release=str(value["release"]) if value.get("release") else None,
            image=str(value["image"]) if value.get("image") else None,
            rollback_reference=(
                str(value["rollback_reference"]) if value.get("rollback_reference") else None
            ),
        )


class RuntimeStatusSourceAdapter(Protocol):
    """Read-only boundary for captured evidence; no network or mutation methods."""

    def read_sources(self) -> Iterable[RuntimeStatusSource]:
        ...


class FixtureEvidenceAdapter:
    """Fixture/test adapter representing an existing local evidence/receipt set."""

    def __init__(self, sources: Iterable[Dict[str, object]]) -> None:
        self._sources = tuple(RuntimeStatusSource.from_mapping(source) for source in sources)

    def read_sources(self) -> Tuple[RuntimeStatusSource, ...]:
        return self._sources


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _claim_id(source_ids: List[str], release: Optional[str], image: Optional[str]) -> str:
    material = json.dumps(
        {"source_ids": sorted(source_ids), "release": release, "image": image},
        sort_keys=True,
    ).encode("utf-8")
    return f"runtime-status-{hashlib.sha256(material).hexdigest()[:16]}"


def _source_ref(source: RuntimeStatusSource) -> Dict[str, object]:
    return {
        "source_id": source.source_id,
        "source_type": source.source_type,
        "authority_class": source.authority_class,
        "source_ref": source.source_ref,
        "source_hash": source.source_hash,
        "receipt_id": source.receipt_id,
        "observed_at": source.observed_at,
    }


def format_runtime_claim(
    *,
    status: str,
    sources: List[RuntimeStatusSource],
    freshness_status: str,
    observed_at: Optional[str],
    release: Optional[str],
    image: Optional[str],
    rollback_reference: Optional[str],
    open_gaps: List[str],
    staleness_reasons: List[str],
    watchtower_observations: List[str],
    conflict_set: List[str],
) -> Dict[str, object]:
    authority_class = "RECEIPT_FACT" if status == "SUPPORTED" else "UNKNOWN_OR_UNVERIFIED"
    receipt_refs = [source.receipt_id for source in sources if source.receipt_id]
    source_ids = [source.source_id for source in sources]
    return {
        "schema_version": CLAIM_SCHEMA_VERSION,
        "claim_id": _claim_id(source_ids, release, image),
        "claim_family": "runtime_deployment_status",
        "text": (
            f"Veritas deployment {release or 'unknown'} is {status.lower()}"
            if release
            else "Veritas deployment status is unknown"
        ),
        "status": status,
        "authority_class": authority_class,
        "release": release,
        "image": image,
        "rollback_reference": rollback_reference,
        "source_refs": [_source_ref(source) for source in sources],
        "receipt_refs": receipt_refs,
        "freshness": {
            "observed_at": observed_at,
            "policy": "runtime_status_24h",
            "status": freshness_status,
        },
        "conflict_set": conflict_set,
        "open_gaps": open_gaps,
        "staleness_reasons": staleness_reasons,
        "watchtower_observations": watchtower_observations,
        "authority_created_by_veritas": False,
        "network_accessed": False,
        "secrets_accessed": False,
    }


def mediate_runtime_status(
    adapter: RuntimeStatusSourceAdapter,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, object]:
    """Format one read-only runtime claim from captured local receipt sources."""
    now = now or datetime.now(timezone.utc)
    sources = list(adapter.read_sources())
    watchtower_observations = [
        source.source_id
        for source in sources
        if source.authority_class == "OBSERVED_ADVISORY"
    ]
    receipt_sources = [
        source
        for source in sources
        if source.source_type in REQUIRED_SOURCE_TYPES
        and source.authority_class in RECEIPT_AUTHORITY_CLASSES
    ]
    by_type = {source.source_type: source for source in receipt_sources}
    open_gaps = sorted(REQUIRED_SOURCE_TYPES - set(by_type))
    if open_gaps:
        return format_runtime_claim(
            status="UNKNOWN",
            sources=receipt_sources,
            freshness_status="UNKNOWN",
            observed_at=None,
            release=None,
            image=None,
            rollback_reference=None,
            open_gaps=open_gaps,
            staleness_reasons=[],
            watchtower_observations=watchtower_observations,
            conflict_set=[],
        )

    selected = [by_type[source_type] for source_type in sorted(REQUIRED_SOURCE_TYPES)]
    releases = {source.release for source in selected}
    images = {source.image for source in selected}
    results = {source.result for source in selected}
    conflict_set = []
    if len(releases) > 1 or len(images) > 1:
        conflict_set = [source.source_id for source in selected]
    release = next(iter(releases)) if len(releases) == 1 else None
    image = next(iter(images)) if len(images) == 1 else None
    rollback_values = {source.rollback_reference for source in selected if source.rollback_reference}
    rollback_reference = next(iter(rollback_values)) if len(rollback_values) == 1 else None
    timestamps = [_parse_timestamp(source.observed_at) for source in selected]
    newest_observed = max(timestamps)
    age_seconds = max(0, int((now - newest_observed).total_seconds()))
    stale = any(
        max(0, int((now - timestamp).total_seconds())) > FRESHNESS_WINDOW_SECONDS
        for timestamp in timestamps
    )
    freshness_status = "STALE" if stale else "CURRENT"
    staleness_reasons = ["stale_source"] if stale else []

    if conflict_set:
        status = "CONTRADICTED"
        open_gaps = ["receipt_release_or_image_conflict"]
    elif results == {"PASS", "MONITORING_REVIEW_PASS"} and not stale:
        status = "SUPPORTED"
        open_gaps = []
    elif stale:
        status = "STALE"
        open_gaps = []
    else:
        status = "UNKNOWN"
        open_gaps = ["receipt_result_not_supported"]

    claim = format_runtime_claim(
        status=status,
        sources=selected,
        freshness_status=freshness_status,
        observed_at=newest_observed.isoformat().replace("+00:00", "Z"),
        release=release,
        image=image,
        rollback_reference=rollback_reference,
        open_gaps=open_gaps,
        staleness_reasons=staleness_reasons,
        watchtower_observations=watchtower_observations,
        conflict_set=conflict_set,
    )
    claim["freshness"]["age_seconds"] = age_seconds
    return claim
