"""Source admission policy for the Veritas corpus.

Every document that reaches production embedding must resolve to an
APPROVED entry in corpus/source_manifest.json carrying a canonical,
non-placeholder URL. Placeholder, malformed, duplicate, or unapproved
material is refused before embedding — never silently admitted.

Fail-closed contract: a source that cannot be positively validated is
quarantined, never "fixed up" into the corpus.
"""

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

# Reserved documentation domains that can never be production sources.
PLACEHOLDER_HOSTS = {
    "example.com", "example.org", "example.net",
    "example.edu", "example.invalid",
}

# Hostname suffixes that indicate non-canonical material.
PLACEHOLDER_HOST_SUFFIXES = (".example.com", ".example.org", ".example.net")

# Body-level scaffolding markers that make a document unfit even when the
# URL is well-formed.
PLACEHOLDER_TEXT_PATTERNS = (
    re.compile(r"lorem\s+ipsum", re.IGNORECASE),
    re.compile(r"\bTODO\b.{0,40}(content|text|fill)", re.IGNORECASE),
    re.compile(r"placeholder\s+(text|content|url|link)", re.IGNORECASE),
)

_VALID_TIERS = {1, 2, 3}


class SourceAdmissionError(ValueError):
    """Raised when a source fails admission validation."""


def _canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_placeholder_url(url) -> bool:
    """True when the URL is missing, malformed, or on a reserved
    placeholder domain."""
    if not isinstance(url, str) or not url.strip():
        return True
    try:
        host = (urlparse(url.strip()).hostname or "").lower()
    except ValueError:
        return True
    if not host:
        return True
    if host in PLACEHOLDER_HOSTS:
        return True
    return any(host.endswith(sfx) for sfx in PLACEHOLDER_HOST_SUFFIXES)


def body_has_placeholder_markers(text: str) -> bool:
    return any(p.search(text or "") for p in PLACEHOLDER_TEXT_PATTERNS)


def load_source_manifest(manifest_path: Path = None) -> dict:
    if manifest_path is None:
        manifest_path = (Path(__file__).parent.parent.parent
                         / "corpus" / "source_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    if manifest.get("manifest_version") != "1.0.0":
        raise SourceAdmissionError("MANIFEST_VERSION_UNSUPPORTED")
    # Zero-placeholder contract: no entry in the production manifest may
    # carry a placeholder URL in any URL field, whatever its status.
    # Quarantined placeholder observations live in the separate
    # provenance ledger, never here.
    for entry in manifest.get("documents", []):
        for field in ("canonical_url", "observed_url"):
            url = entry.get(field)
            if url is not None and is_placeholder_url(url):
                raise SourceAdmissionError(
                    "MANIFEST_PLACEHOLDER_URL:"
                    f"{entry.get('document_id')}:{field}")
    return manifest


def approved_entries(manifest: dict) -> dict:
    """document_id -> manifest entry for approved sources only."""
    return {e["document_id"]: e for e in manifest.get("documents", [])
            if e.get("status") == "approved"}


def admit_source_document(doc: dict, manifest: dict,
                          _seen_ids: set = None) -> dict:
    """Validate one source document against the manifest.

    Returns the approved manifest entry. Raises SourceAdmissionError on
    any failure — callers must quarantine, never coerce.
    """
    doc_id = doc.get("id") or doc.get("document_id")
    if not isinstance(doc_id, str) or not doc_id.strip():
        raise SourceAdmissionError("SOURCE_ID_MISSING")
    if _seen_ids is not None:
        if doc_id in _seen_ids:
            raise SourceAdmissionError("SOURCE_ID_DUPLICATE")
        _seen_ids.add(doc_id)

    entry = approved_entries(manifest).get(doc_id)
    if entry is None:
        raise SourceAdmissionError("SOURCE_NOT_IN_APPROVED_MANIFEST")

    url = doc.get("url") or entry.get("canonical_url")
    if is_placeholder_url(url):
        raise SourceAdmissionError("SOURCE_URL_PLACEHOLDER")
    if entry.get("canonical_url") != url:
        raise SourceAdmissionError("SOURCE_URL_MANIFEST_MISMATCH")

    if doc.get("source_tier") not in _VALID_TIERS:
        raise SourceAdmissionError("SOURCE_TIER_INVALID")
    if entry.get("tier") != doc.get("source_tier"):
        raise SourceAdmissionError("SOURCE_TIER_MANIFEST_MISMATCH")

    body = doc.get("content") or doc.get("text") or ""
    if body_has_placeholder_markers(body):
        raise SourceAdmissionError("SOURCE_BODY_PLACEHOLDER")

    # raw_content_sha256 binds the raw source body at admission;
    # content_sha256 binds the embedded chunk text (corpus identity).
    expected_hash = entry.get("raw_content_sha256")
    if expected_hash and content_sha256(body) != expected_hash:
        raise SourceAdmissionError("SOURCE_CONTENT_HASH_MISMATCH")

    return entry


# Scrape-failure stubs: pages rendered client-side that captured only a
# loading shell carry zero evidentiary content.
_DEAD_SCRAPE_PATTERN = re.compile(r"^(?:\s*Loading\.{0,3}\s*)+$")
MIN_SUBSTANTIVE_CHARS = 80


def chunk_has_substantive_content(chunk: dict) -> bool:
    """True when the chunk body carries real content — not a dead
    scrape shell or a sub-threshold fragment."""
    text = (chunk.get("text") or "").strip()
    if not text:
        return False
    if _DEAD_SCRAPE_PATTERN.match(text):
        return False
    stripped = re.sub(r"(?m)^\s*Loading\.{0,3}\s*$", "", text).strip()
    return len(stripped) >= MIN_SUBSTANTIVE_CHARS


def chunk_is_production_safe(chunk: dict, manifest: dict) -> bool:
    """A stored embedded chunk may serve production answers only when its
    document is approved, non-placeholder, and the chunk body carries
    substantive content (dead scrape shells are not evidence)."""
    doc_id = chunk.get("document_id")
    entry = approved_entries(manifest).get(doc_id)
    if entry is None:
        return False
    if not chunk_has_substantive_content(chunk):
        return False
    return not is_placeholder_url(chunk.get("url")) \
        and entry.get("canonical_url") == chunk.get("url")


def corpus_inventory_hash(chunks: list) -> str:
    """Deterministic hash over the production corpus inventory:
    document_id, chunk_id, tier, canonical url, text hash. Stable across
    rebuilds with identical content."""
    items = sorted(
        (
            {
                "chunk_id": c["chunk_id"],
                "document_id": c["document_id"],
                "source_tier": c.get("source_tier"),
                "url": c.get("url"),
                "text_sha256": content_sha256(c.get("text") or ""),
            }
            for c in chunks
        ),
        key=lambda d: d["chunk_id"])
    return hashlib.sha256(_canonical_json(items)).hexdigest()
