# Veritas Scoring Logic — Multi-Source Contribution Balance

**Version:** 2.0 Refined  
**Date:** 2026-04-07  
**Focus:** Tier 2/3 improves explanation without hurting trust

---

## Core Principle

**Tier 2/3 sources inform and clarify, but never override Tier 1.**

**Key insight:**
- Tier 1 = What is correct (specification)
- Tier 2 = How it's used (interpretation)
- Tier 3 = Where it breaks (real-world)

**Scoring must reflect this hierarchy.**

---

## Metric 1: Coverage (Unchanged)

**Definition:** Percentage of answer sentences that contain citations

### Formula

```python
def compute_coverage_score(answer_text: str, citations: List[Dict]) -> Tuple[float, str]:
    """
    Calculate coverage as fraction of sentences with citations.
    """
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', answer_text) if s.strip()]
    
    # Find sentences with citation markers [1], [2], etc.
    citation_pattern = r'\[\d+\]'
    cited_sentences = [s for s in sentences if re.search(citation_pattern, s)]
    
    # Calculate coverage
    if len(sentences) == 0:
        return 0.0, "No sentences found"
    
    coverage = len(cited_sentences) / len(sentences)
    
    # Quality level
    if coverage >= 0.8:
        explanation = "Excellent — most claims are cited"
    elif coverage >= 0.6:
        explanation = "Good — majority of claims cited"
    elif coverage >= 0.4:
        explanation = "Partial — some claims lack citations"
    else:
        explanation = "Insufficient — many claims uncited"
    
    return coverage, explanation
```

### Thresholds

- **Excellent:** ≥ 80%
- **Good:** 60-79%
- **Partial:** 40-59%
- **Insufficient:** < 40%

### No tier weighting

Coverage is tier-agnostic. A citation from Tier 3 still counts as "cited."

---

## Metric 2: Authority (Refined)

**Definition:** Weighted average of source tiers, reflecting documentation dominance

### Formula

```python
def compute_authority_score(citations: List[Dict]) -> Tuple[float, str]:
    """
    Calculate authority based on tier distribution of citations.
    
    Tier weights:
    - Tier 1 (Docs): 1.0
    - Tier 2 (Blog): 0.6
    - Tier 3 (Community): 0.3
    """
    if not citations:
        return 0.0, "No citations"
    
    tier_weights = {1: 1.0, 2: 0.6, 3: 0.3}
    
    # Calculate weighted average
    total_weight = sum(tier_weights.get(c.get('source_tier', 3), 0.3) for c in citations)
    authority_score = total_weight / len(citations)
    
    # Quality level
    if authority_score >= 0.85:
        explanation = "High (Docs-led)"
    elif authority_score >= 0.65:
        explanation = "Medium (Mixed sources)"
    else:
        explanation = "Low (Community-heavy)"
    
    return authority_score, explanation
```

### Thresholds

- **High:** ≥ 0.85 (mostly Tier 1)
- **Medium:** 0.65-0.84 (balanced mix)
- **Low:** < 0.65 (too much Tier 3)

### Example calculations

**Scenario 1:** 5 citations, all Tier 1
```
authority = (1.0 + 1.0 + 1.0 + 1.0 + 1.0) / 5 = 1.0
label = "High (Docs-led)"
```

**Scenario 2:** 5 citations (3 Tier 1, 1 Tier 2, 1 Tier 3)
```
authority = (1.0 + 1.0 + 1.0 + 0.6 + 0.3) / 5 = 0.78
label = "Medium (Mixed sources)"
```

**Scenario 3:** 5 citations (1 Tier 1, 2 Tier 2, 2 Tier 3)
```
authority = (1.0 + 0.6 + 0.6 + 0.3 + 0.3) / 5 = 0.56
label = "Low (Community-heavy)"
```

---

## Metric 3: Contribution Balance (NEW)

**Definition:** How much of the answer comes from each tier (by chunk count)

### Formula

```python
def compute_contribution_balance(citations: List[Dict]) -> Tuple[Dict, str]:
    """
    Calculate percentage contribution from each tier.
    
    Returns:
        tier_percentages: {1: 70%, 2: 20%, 3: 10%}
        quality_label: "Docs-led" | "Balanced" | "Weak grounding"
    """
    if not citations:
        return {}, "No sources"
    
    # Count citations per tier
    tier_counts = {1: 0, 2: 0, 3: 0}
    for citation in citations:
        tier = citation.get('source_tier', 3)
        tier_counts[tier] += 1
    
    # Calculate percentages
    total = len(citations)
    tier_percentages = {
        1: (tier_counts[1] / total) * 100,
        2: (tier_counts[2] / total) * 100,
        3: (tier_counts[3] / total) * 100
    }
    
    # Determine quality label
    docs_pct = tier_percentages[1]
    
    if docs_pct >= 70:
        quality_label = "Docs-led (well-grounded)"
    elif docs_pct >= 40:
        quality_label = "Balanced (mixed authority)"
    else:
        quality_label = "Weak grounding (community-heavy)"
    
    return tier_percentages, quality_label
```

### Thresholds

- **Docs-led:** Tier 1 ≥ 70%
- **Balanced:** Tier 1 40-69%
- **Weak grounding:** Tier 1 < 40%

### Display format

```
Source Contribution
Docs        ██████████████░░░░░░ 70%
Blog        ████░░░░░░░░░░░░░░░░ 20%
Community   ██░░░░░░░░░░░░░░░░░░ 10%

Quality: Docs-led (well-grounded)
```

---

## Metric 4: Sufficiency (Reinterpreted)

**Definition:** Can the question be answered from Tier 1 alone?

### Formula

```python
def compute_sufficiency_score(
    question: str, 
    answer: str, 
    citations: List[Dict],
    tier_percentages: Dict
) -> Tuple[float, str]:
    """
    Determine if Tier 1 sources alone are sufficient.
    
    This is NOT about answer length, but about whether
    documentation provides complete information.
    """
    # Check for explicit insufficiency markers
    insufficiency_phrases = [
        "I don't have information",
        "I don't know",
        "unclear from documentation",
        "not documented"
    ]
    
    if any(phrase in answer.lower() for phrase in insufficiency_phrases):
        return 0.3, "Insufficient — missing information acknowledged"
    
    # Check tier 1 dominance
    docs_pct = tier_percentages.get(1, 0)
    
    if docs_pct >= 70:
        # Docs are dominant — sufficient
        explanation = "Docs sufficient, additional context provided"
        score = 1.0
    elif docs_pct >= 40:
        # Mixed sources — partial sufficiency
        explanation = "Requires multi-source synthesis"
        score = 0.7
    else:
        # Community-heavy — docs insufficient
        explanation = "Docs insufficient, relies on community"
        score = 0.4
    
    # Bonus for answer length (indicates thoroughness)
    if len(answer) > 500:
        score = min(1.0, score + 0.1)
    
    # Bonus for multiple citations
    if len(citations) >= 5:
        score = min(1.0, score + 0.1)
    
    return score, explanation
```

### Thresholds

- **Sufficient:** ≥ 0.8 (Docs-led)
- **Partial:** 0.5-0.79 (Mixed)
- **Insufficient:** < 0.5 (Community-heavy or missing info)

### Key insight

**Tier 2/3 don't reduce sufficiency if Tier 1 is dominant.**

Example:
- 70% Tier 1, 20% Tier 2, 10% Tier 3
- Sufficiency = "Docs sufficient, additional context provided"
- Score = 1.0

This is correct because:
- Docs answered the question
- Blog/community added clarity
- Not a fallback situation

---

## Metric 5: Risk (Unchanged)

**Definition:** Likelihood of hallucination or incorrect information

### Formula

```python
def compute_risk_score(answer: str, citations: List[Dict]) -> Tuple[float, str]:
    """
    Calculate risk inversely related to hallucination likelihood.
    
    Higher score = lower risk
    """
    risk_score = 1.0  # Start with low risk
    
    # Check 1: Citation density
    if len(answer) > 500 and len(citations) < 2:
        risk_score -= 0.3  # Long answer, few citations = risky
    
    # Check 2: Hedging language (indicates uncertainty)
    hedging_words = ['might', 'possibly', 'unclear', 'uncertain', 'may be', 'could be']
    hedging_count = sum(1 for word in hedging_words if word in answer.lower())
    
    if hedging_count > 3:
        risk_score -= 0.2  # Too much hedging = uncertain
    
    # Check 3: Uncited factual claims
    # (Simple heuristic: sentences with numbers/technical terms but no citations)
    sentences = [s.strip() for s in re.split(r'[.!?]+', answer) if s.strip()]
    citation_pattern = r'\[\d+\]'
    
    technical_uncited = 0
    for sentence in sentences:
        has_number = bool(re.search(r'\d+', sentence))
        has_citation = bool(re.search(citation_pattern, sentence))
        
        if has_number and not has_citation:
            technical_uncited += 1
    
    if technical_uncited > 2:
        risk_score -= 0.3  # Uncited technical claims = risky
    
    # Ensure score stays in [0, 1]
    risk_score = max(0.0, min(1.0, risk_score))
    
    # Quality level (inverted — high score = low risk)
    if risk_score >= 0.8:
        explanation = "Low risk — well-cited, confident"
    elif risk_score >= 0.6:
        explanation = "Medium risk — some uncertainty"
    else:
        explanation = "High risk — check carefully"
    
    return risk_score, explanation
```

### Thresholds

- **Low risk:** ≥ 0.8
- **Medium risk:** 0.6-0.79
- **High risk:** < 0.6

---

## Overall Evaluation

### Combined scoring

```python
def evaluate_answer(
    question: str, 
    answer: str, 
    citations: List[Dict]
) -> Dict:
    """
    Combine all metrics into overall evaluation.
    """
    # Compute individual scores
    coverage_score, coverage_exp = compute_coverage_score(answer, citations)
    authority_score, authority_exp = compute_authority_score(citations)
    tier_percentages, contribution_exp = compute_contribution_balance(citations)
    sufficiency_score, sufficiency_exp = compute_sufficiency_score(
        question, answer, citations, tier_percentages
    )
    risk_score, risk_exp = compute_risk_score(answer, citations)
    
    # Overall weighted score
    overall_score = (
        0.3 * coverage_score +
        0.2 * authority_score +
        0.3 * sufficiency_score +
        0.2 * risk_score
    )
    
    # Review recommendation
    needs_review = (
        coverage_score < 0.7 or
        authority_score < 0.6 or
        sufficiency_score < 0.6 or
        risk_score < 0.6 or
        overall_score < 0.7
    )
    
    return {
        "overall_score": overall_score,
        "needs_review": needs_review,
        "metrics": {
            "coverage": {
                "score": coverage_score,
                "explanation": coverage_exp
            },
            "authority": {
                "score": authority_score,
                "explanation": authority_exp
            },
            "contribution": {
                "tier_percentages": tier_percentages,
                "explanation": contribution_exp
            },
            "sufficiency": {
                "score": sufficiency_score,
                "explanation": sufficiency_exp
            },
            "risk": {
                "score": risk_score,
                "explanation": risk_exp
            }
        },
        "recommendation": (
            "Needs human review" if needs_review else "Looks good"
        )
    }
```

---

## Key Invariants

1. **Tier 2/3 cannot increase authority score** - Only Tier 1 = 1.0
2. **Tier 2/3 don't reduce sufficiency if Tier 1 is dominant** - 70%+ Tier 1 = sufficient
3. **Coverage is tier-agnostic** - Any citation counts
4. **Contribution balance is always visible** - Not a hidden metric
5. **Review flag is conservative** - Any metric < threshold triggers review

---

## Example Evaluation

**Input:**
- Question: "How does streaming work in Claude?"
- Answer: 3-layer format (Core + Implementation + Pitfalls)
- Citations: [1, 2] Tier 1, [3] Tier 2, [4] Tier 3

**Computation:**

```python
coverage = 4 cited sentences / 5 total = 0.80 (Excellent)
authority = (1.0 + 1.0 + 0.6 + 0.3) / 4 = 0.725 (Medium)
contribution = {1: 50%, 2: 25%, 3: 25%} → "Balanced"
sufficiency = 0.7 (Mixed sources)
risk = 0.85 (Low risk)

overall = 0.3*0.80 + 0.2*0.725 + 0.3*0.7 + 0.2*0.85
        = 0.24 + 0.145 + 0.21 + 0.17
        = 0.765

needs_review = False (all metrics above thresholds)
recommendation = "Looks good"
```

**Display:**

```
Trust Signal
-------------------------
Coverage     ████████░░ 80%
Authority    Medium (Mixed sources)
Contribution Balanced (Docs + supporting context)
Sufficiency  Requires multi-source synthesis
Review       🟢 Looks good
-------------------------
```

---

## Testing Strategy

**Test cases:**

1. **Docs-only answer** (all Tier 1)
   - Authority = 1.0 (High)
   - Contribution = "Docs-led"
   - Sufficiency = "Docs sufficient"

2. **Balanced answer** (70% T1, 20% T2, 10% T3)
   - Authority = 0.88 (High)
   - Contribution = "Docs-led"
   - Sufficiency = "Docs sufficient, additional context"

3. **Community-heavy answer** (30% T1, 30% T2, 40% T3)
   - Authority = 0.54 (Low)
   - Contribution = "Weak grounding"
   - Sufficiency = "Docs insufficient"
   - needs_review = True

4. **Missing citations** (coverage < 0.7)
   - needs_review = True

---

**This scoring logic makes Tier 2/3 valuable for explanation without compromising trust.**
