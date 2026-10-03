"""Claim-level citation grounding for Veritas synthesis.

Contract (packet wpk_fa189292ad894c1e node citation_grounding_and_synthesis):
every material claim must be supported by a cited retrieved chunk, every
emitted source must actually be cited, citation IDs must resolve to real
chunks after sorting/dedup/enrichment, and the receipt must report
coverage, precision, tier-1 share and unsupported-claim disposition —
truthfully, including lower-tier-only evidence.

Grounding is lexical entailment-lite: deterministic, provider-free, and
conservative. It catches fabricated/stale citation IDs, unused sources,
and claims with no cited evidence. It is a grounding gate, not a
verifier — the receipt reports what could be checked.
"""

import re
from typing import Dict, List, Optional, Tuple

_CITE_RE = re.compile(r"\[(\d+)\]")
_SENT_RE = re.compile(r"(?<=[.!?])\s+|(?<=\n)\s*")

_SUPPORT_OVERLAP_MIN = 0.30  # fraction of a claim's content terms that
# must appear in at least one cited source for the claim to count as
# supported. Proposed threshold, not an empirical claim — callers may
# supply a different floor via ground_answer(min_claim_support=...).

# Bounded contradiction awareness: explicit negation markers only. A
# claim whose shared content terms fall inside a negation window in the
# claim but outside it in the cited source (or vice versa) is flagged
# contradiction_suspected and never counted as supported. This catches
# "X does not support Y" cited to "X supports Y" — it cannot detect
# semantic contradiction without explicit negation markers, and the
# receipt states that guarantee boundary rather than overclaiming.
_NEG_TOKENS = frozenset(
    "not no never cannot cant can't won't wont isn't aren't wasn't "
    "weren't doesn't don't didn't shouldn't couldn't mustn't without "
    "nor neither".split())
_NEG_WINDOW = 3  # tokens following a negation marker


def _negated_terms(text: str) -> set:
    """Content terms occurring within _NEG_WINDOW tokens after a
    negation marker — the deterministic polarity signal."""
    toks = _TOKEN_RE.findall((text or "").lower())
    out = set()
    for i, tok in enumerate(toks):
        bare = tok.rstrip("'")
        if tok in _NEG_TOKENS or bare in _NEG_TOKENS \
                or tok.endswith("n't"):
            for w in toks[i + 1: i + 1 + _NEG_WINDOW]:
                for part in re.split(r"[_\-]", w):
                    if len(part) <= 2 or part in _STOP:
                        continue
                    out.add(part)
                    if part.endswith("s") and len(part) > 3:
                        out.add(part[:-1])
    return out

_STOP = frozenset("""
a an the and or of to in for on with is are was were be been by at from
that this it its as do does did not no but if then than so such what why
how when where which who whom can could should would will may might
you your we our they their he she his her them us i
""".split())
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_\-]*")


def _terms(text: str) -> set:
    """Content terms: split snake/kebab compounds and normalize simple
    plurals so 'input_schema' covers 'input' and 'schemas' == 'schema'.
    Conservative morphology — no provider, no external stemmer."""
    out = set()
    for tok in _TOKEN_RE.findall((text or "").lower()):
        for part in re.split(r"[_\-]", tok):
            if len(part) <= 2 or part in _STOP:
                continue
            out.add(part)
            if part.endswith("s") and len(part) > 3:
                out.add(part[:-1])
    return out


def segment_claims(paragraph: str) -> List[Tuple[str, List[int]]]:
    """Split a paragraph into material claims.

    A material claim is a sentence bearing at least one assertion —
    sentences that only carry citations to prior text or are shorter
    than 4 content terms are treated as connective tissue, not claims.
    Returns (claim_text, cited_ids) pairs; cited_ids are the [n]
    references attached to the sentence.
    """
    claims = []
    for sent in _SENT_RE.split(paragraph or ""):
        sent = sent.strip()
        if not sent:
            continue
        ids = [int(m.group(1)) for m in _CITE_RE.finditer(sent)]
        body = _CITE_RE.sub("", sent).strip()
        if len(_terms(body)) < 4:
            continue
        claims.append((sent, ids))
    return claims


def _claim_support(claim_text: str, cited_chunks: List[Dict],
                   min_support: float) -> Tuple[bool, bool]:
    """Returns (supported, contradiction_suspected).

    A claim is supported when at least one cited source covers enough
    of the claim's content terms AND no shared term carries conflicting
    negation polarity between claim and source. Overlap-sufficient but
    polarity-conflicting evidence is reported as contradiction_suspected
    — never as support."""
    if not cited_chunks:
        return False, False
    claim_terms = _terms(_CITE_RE.sub("", claim_text))
    if not claim_terms:
        return True, False  # vacuous — nothing material to support
    claim_neg = _negated_terms(_CITE_RE.sub("", claim_text))
    any_contradicted = False
    for chunk in cited_chunks:
        chunk_text = (chunk.get("text") or "") \
            + " " + (chunk.get("title") or "")
        chunk_terms = _terms(chunk_text)
        if not chunk_terms:
            continue
        shared = claim_terms & chunk_terms
        if len(shared) / len(claim_terms) < min_support:
            continue
        chunk_neg = _negated_terms(chunk_text)
        if (shared & (claim_neg - chunk_neg)) \
                or (shared & (chunk_neg - claim_neg)):
            any_contradicted = True
            continue
        return True, False
    return False, any_contradicted


def ground_answer(answer_json: dict, retrieved_chunks: List[Dict],
                  min_claim_support: float = _SUPPORT_OVERLAP_MIN
                  ) -> Tuple[dict, dict]:
    """Ground a parsed synthesis answer against the retrieved chunks.

    Returns (cleaned_answer, receipt). The cleaned answer has:
      - unresolvable citation markers stripped from idea text
      - unresolvable sourceIds dropped
      - sources map containing ONLY chunks actually cited in text,
        enriched from real chunk metadata (never fabricated)
      - evidence_limitation disclosed when no cited chunk is tier 1

    The receipt reports: claim coverage (fraction of material claims
    with at least one valid citation), citation precision (fraction of
    citation markers resolving to a real chunk), supported-claim share,
    unique cited documents, tier-1 cited count, and the disposition of
    unsupported claims.
    """
    ideas = answer_json.get("ideas") or []
    n_chunks = len(retrieved_chunks)

    total_markers = 0
    resolved_markers = 0
    material_claims = 0
    cited_claims = 0
    supported_claims = 0
    cited_ids = set()
    unsupported = []
    contradiction_suspected = 0

    cleaned_ideas = []
    for idea in ideas:
        idea = dict(idea)
        paras = []
        for para in (idea.get("paragraphs") or []):
            for sent, ids in segment_claims(para):
                material_claims += 1
                valid = [i for i in ids if 1 <= i <= n_chunks]
                total_markers += len(ids)
                resolved_markers += len(valid)
                cited_ids.update(valid)
                cited_chunks = [retrieved_chunks[i - 1] for i in valid]
                if not valid:
                    unsupported.append({
                        "claim": _CITE_RE.sub("", sent).strip()[:160],
                        "disposition": "uncited"})
                else:
                    cited_claims += 1
                    sup, contra = _claim_support(
                        sent, cited_chunks, min_claim_support)
                    if sup:
                        supported_claims += 1
                    else:
                        if contra:
                            contradiction_suspected += 1
                        unsupported.append({
                            "claim": _CITE_RE.sub("", sent).strip()[:160],
                            "disposition": "contradiction_suspected"
                                if contra else
                                "unsupported_by_cited_chunks"})
            # Strip unresolvable [n] markers; keep valid ones verbatim.
            def _strip_bad(m):
                return m.group(0) if 1 <= int(m.group(1)) <= n_chunks \
                    else ""
            paras.append(_CITE_RE.sub(_strip_bad, para))
        idea["paragraphs"] = paras
        # sourceIds: keep only ids that are both resolvable and cited.
        raw_ids = idea.get("sourceIds") or []
        idea["sourceIds"] = [str(i) for i in raw_ids
                             if str(i).isdigit()
                             and 1 <= int(i) <= n_chunks
                             and int(i) in cited_ids]
        cleaned_ideas.append(idea)

    # Emit only cited sources, enriched from the real chunk —
    # an LLM-supplied title is advisory; canonical metadata wins.
    enriched = {}
    for sid in sorted(cited_ids):
        chunk = retrieved_chunks[sid - 1]
        enriched[str(sid)] = {
            "title": chunk.get("title") or chunk.get("source_name"),
            "url": chunk.get("url") or "",
            "source_name": chunk.get("source_name") or "",
            "tier": chunk.get("source_tier"),
            "document_id": chunk.get("document_id"),
            "document_title": chunk.get("title") or "",
        }

    llm_sources = answer_json.get("sources") or {}
    dropped_sources = sorted(set(llm_sources) - {str(i) for i in cited_ids})

    cited_tiers = {int(retrieved_chunks[i - 1].get("source_tier") or 3)
                   for i in cited_ids}
    tier1_cited = sum(1 for i in cited_ids
                      if int(retrieved_chunks[i - 1].get("source_tier")
                             or 3) == 1)

    evidence_limitation = None
    if cited_ids and 1 not in cited_tiers:
        evidence_limitation = (
            "This answer rests only on lower-tier evidence; no "
            "tier-1 documentation was cited.")

    receipt = {
        "material_claims": material_claims,
        "claims_with_valid_citation": cited_claims,
        "claims_supported": supported_claims,
        "citation_coverage": round(cited_claims / material_claims, 4)
            if material_claims else None,
        "citation_precision": round(resolved_markers / total_markers, 4)
            if total_markers else None,
        "unique_cited_documents": len(
            {retrieved_chunks[i - 1].get("document_id")
             for i in cited_ids}),
        "tier1_cited_count": tier1_cited,
        "dropped_unresolvable_sources": dropped_sources,
        "unsupported_claims": unsupported,
        "contradiction_suspected_claims": contradiction_suspected,
        "unsupported_disposition":
            "reported" if unsupported else "none",
        "evidence_limitation": evidence_limitation,
        "min_claim_support": min_claim_support,
        "grounding": "lexical_entailment_lite_v2",
        "guarantee_scope": "Support = term-overlap floor plus explicit "
            "negation-window polarity check. Detects negation-marked "
            "contradiction only; semantic contradiction without "
            "explicit negation markers is outside this bound.",
    }

    cleaned = dict(answer_json)
    cleaned["ideas"] = cleaned_ideas
    cleaned["sources"] = enriched
    cleaned["citation_receipt"] = receipt
    if evidence_limitation:
        cleaned["evidence_limitation"] = evidence_limitation
    return cleaned, receipt


def needs_retry(answer_json: Optional[dict], receipt: Optional[dict],
                max_unsupported_ratio: float = 0.5) -> bool:
    """Bounded retry predicate: retry only on malformed output or a high
    share of unsupported claims — never to inflate tier share."""
    if answer_json is None:
        return True  # malformed/unparseable
    if receipt is None:
        return False
    claims = receipt.get("material_claims") or 0
    if claims == 0:
        return True  # no claims at all is malformed output
    unsupported = len(receipt.get("unsupported_claims") or [])
    # Boundary is inclusive: at exactly max_unsupported_ratio the output
    # is below the support floor and must retry/abstain/fail closed.
    return (unsupported / claims) >= max_unsupported_ratio
