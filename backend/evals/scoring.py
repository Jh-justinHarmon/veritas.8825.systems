"""
Eval Scoring Module for Veritas

Scores answer quality across 4 dimensions:
1. Coverage: How much of the answer is backed by sources?
2. Authority: What's the average tier of sources used?
3. Sufficiency: Does the answer fully address the question?
4. Risk: Are there any hallucination or accuracy concerns?

Based on ARCHITECTURE_V1.md scoring logic.
"""

import re
from typing import Dict, List, Tuple


def compute_coverage_score(answer_text: str, citations: List[Dict]) -> Tuple[float, str]:
    """
    Calculate coverage score: percentage of answer backed by citations.
    
    Args:
        answer_text: Generated answer text
        citations: List of citation dicts
    
    Returns:
        Tuple of (score, explanation)
    """
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', answer_text) if s.strip()]
    
    if not sentences:
        return 0.0, "No sentences found in answer"
    
    # Count sentences with citations
    citation_pattern = r'\[\d+\]'
    cited_sentences = [s for s in sentences if re.search(citation_pattern, s)]
    
    score = len(cited_sentences) / len(sentences)
    
    # Determine quality level
    if score >= 0.9:
        level = "Excellent"
    elif score >= 0.7:
        level = "Good"
    elif score >= 0.5:
        level = "Partial"
    else:
        level = "Insufficient"
    
    explanation = f"{level}: {len(cited_sentences)}/{len(sentences)} sentences cited ({score:.1%})"
    
    return score, explanation


def compute_authority_score(citations: List[Dict]) -> Tuple[float, str]:
    """
    Calculate authority score: average tier of sources used.
    
    Tier weights:
    - Tier 1: 1.0 (Official docs)
    - Tier 2: 0.7 (Vendor content)
    - Tier 3: 0.4 (Community)
    
    Args:
        citations: List of citation dicts with source_tier
    
    Returns:
        Tuple of (score, explanation)
    """
    if not citations:
        return 0.0, "No citations found"
    
    tier_weights = {
        1: 1.0,
        2: 0.7,
        3: 0.4
    }
    
    # Calculate weighted average
    total_weight = sum(tier_weights.get(c.get('source_tier', 3), 0.4) for c in citations)
    score = total_weight / len(citations)
    
    # Count by tier
    tier_counts = {}
    for citation in citations:
        tier = citation.get('source_tier', 3)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    tier_breakdown = ", ".join([f"T{t}:{count}" for t, count in sorted(tier_counts.items())])
    
    # Determine quality level
    if score >= 0.9:
        level = "Excellent (mostly official docs)"
    elif score >= 0.7:
        level = "Good (mix of official and vendor)"
    elif score >= 0.5:
        level = "Fair (mix of sources)"
    else:
        level = "Low (mostly community sources)"
    
    explanation = f"{level} - {tier_breakdown} ({score:.2f} avg)"
    
    return score, explanation


def compute_sufficiency_score(question: str, answer: str, citations: List[Dict]) -> Tuple[float, str]:
    """
    Calculate sufficiency score: does answer fully address the question?
    
    For V1, this is a heuristic based on:
    - Answer length (longer = more thorough)
    - Number of citations (more = better supported)
    - Presence of "I don't have information" (indicates gaps)
    
    Args:
        question: Original question
        answer: Generated answer
        citations: List of citations
    
    Returns:
        Tuple of (score, explanation)
    """
    # Check for explicit "no information" statements
    if "I don't have information" in answer or "I don't know" in answer:
        return 0.3, "Answer indicates missing information"
    
    # Heuristic scoring
    score = 0.5  # Base score
    
    # Length bonus (longer answers tend to be more thorough)
    if len(answer) > 500:
        score += 0.2
    elif len(answer) > 200:
        score += 0.1
    
    # Citation bonus (more citations = better support)
    if len(citations) >= 4:
        score += 0.2
    elif len(citations) >= 2:
        score += 0.1
    
    # Cap at 1.0
    score = min(score, 1.0)
    
    # Determine quality level
    if score >= 0.8:
        level = "Thorough"
    elif score >= 0.6:
        level = "Adequate"
    elif score >= 0.4:
        level = "Partial"
    else:
        level = "Incomplete"
    
    explanation = f"{level}: {len(answer)} chars, {len(citations)} citations"
    
    return score, explanation


def compute_risk_score(answer: str, citations: List[Dict]) -> Tuple[float, str]:
    """
    Calculate risk score: potential hallucination or accuracy concerns.
    
    Lower risk = higher score (inverted)
    
    Risk indicators:
    - Uncited factual claims
    - Hedging language ("might", "possibly", "unclear")
    - Very few citations for long answer
    
    Args:
        answer: Generated answer
        citations: List of citations
    
    Returns:
        Tuple of (score, explanation) where higher score = lower risk
    """
    risk_flags = []
    risk_score = 1.0  # Start with no risk
    
    # Check citation density
    if len(answer) > 500 and len(citations) < 2:
        risk_flags.append("Low citation density for long answer")
        risk_score -= 0.3
    
    # Check for hedging language (might indicate uncertainty)
    hedging_words = ['might', 'possibly', 'unclear', 'uncertain', 'may be', 'could be']
    hedging_count = sum(1 for word in hedging_words if word in answer.lower())
    if hedging_count > 2:
        risk_flags.append(f"Excessive hedging ({hedging_count} instances)")
        risk_score -= 0.2
    
    # Check for definitive claims without citations
    # Look for sentences without citations that contain strong claims
    sentences = [s.strip() for s in re.split(r'[.!?]+', answer) if s.strip()]
    citation_pattern = r'\[\d+\]'
    uncited_sentences = [s for s in sentences if not re.search(citation_pattern, s)]
    
    # Count strong claim words in uncited sentences
    strong_claim_words = ['is', 'are', 'will', 'must', 'always', 'never', 'definitely']
    uncited_claims = sum(1 for s in uncited_sentences if any(word in s.lower() for word in strong_claim_words))
    
    if uncited_claims > 3:
        risk_flags.append(f"{uncited_claims} uncited factual claims")
        risk_score -= 0.3
    
    # Cap at 0.0 minimum
    risk_score = max(risk_score, 0.0)
    
    # Determine risk level (inverted)
    if risk_score >= 0.8:
        level = "Low risk"
    elif risk_score >= 0.6:
        level = "Moderate risk"
    elif risk_score >= 0.4:
        level = "Elevated risk"
    else:
        level = "High risk"
    
    if risk_flags:
        explanation = f"{level}: {'; '.join(risk_flags)}"
    else:
        explanation = f"{level}: No major concerns detected"
    
    return risk_score, explanation


def evaluate_answer(question: str, answer: str, citations: List[Dict]) -> Dict:
    """
    Evaluate an answer across all 4 dimensions.
    
    Args:
        question: Original question
        answer: Generated answer
        citations: List of citation dicts
    
    Returns:
        Dict with scores and overall evaluation
    """
    # Compute all scores
    coverage_score, coverage_exp = compute_coverage_score(answer, citations)
    authority_score, authority_exp = compute_authority_score(citations)
    sufficiency_score, sufficiency_exp = compute_sufficiency_score(question, answer, citations)
    risk_score, risk_exp = compute_risk_score(answer, citations)
    
    # Overall score (weighted average)
    overall_score = (
        0.3 * coverage_score +
        0.2 * authority_score +
        0.3 * sufficiency_score +
        0.2 * risk_score
    )
    
    # Determine if review is needed
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
        "scores": {
            "coverage": {
                "score": coverage_score,
                "explanation": coverage_exp
            },
            "authority": {
                "score": authority_score,
                "explanation": authority_exp
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
        "recommendation": "Review recommended" if needs_review else "Answer looks good"
    }


if __name__ == "__main__":
    # Test with sample data
    test_question = "What is Claude Cowork?"
    test_answer = "Claude Cowork is a tool for knowledge work [1]. It runs on desktop and handles multi-step tasks [2]. Users can delegate work and get polished deliverables [3]."
    test_citations = [
        {"source_tier": 1, "title": "Official Docs"},
        {"source_tier": 1, "title": "Getting Started"},
        {"source_tier": 2, "title": "Blog Post"}
    ]
    
    result = evaluate_answer(test_question, test_answer, test_citations)
    
    print("Eval Results:")
    print(f"Overall Score: {result['overall_score']:.2f}")
    print(f"Needs Review: {result['needs_review']}")
    print(f"\nScores:")
    for dimension, data in result['scores'].items():
        print(f"  {dimension.title()}: {data['score']:.2f} - {data['explanation']}")
    print(f"\nRecommendation: {result['recommendation']}")
