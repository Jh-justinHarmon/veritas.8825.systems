"""
Quality metrics for comparing raw vs abstracted synthesis.

Measures that synthesis quality is maintained despite input degradation.
"""

from typing import Dict, List


def measure_synthesis_quality(answer: Dict) -> Dict:
    """
    Measure synthesis quality metrics.
    
    Metrics:
    - Idea count: Number of concepts synthesized
    - Idea coherence: Average paragraph count per idea
    - Source diversity: Number of unique tiers cited
    - Citation density: Citations per paragraph
    - Concept clarity: Title specificity (word count)
    
    Returns quality scores that should be equivalent between raw and abstracted modes.
    """
    
    ideas = answer.get('ideas', [])
    sources = answer.get('sources', {})
    
    # 1. Idea count
    idea_count = len(ideas)
    
    # 2. Idea coherence (paragraphs per idea)
    total_paragraphs = sum(len(idea.get('paragraphs', [])) for idea in ideas)
    avg_paragraphs_per_idea = total_paragraphs / idea_count if idea_count > 0 else 0
    
    # 3. Source diversity (unique tiers)
    tiers = set(source.get('tier') for source in sources.values())
    tier_diversity = len(tiers)
    
    # 4. Citation density (citations per paragraph)
    total_citations = sum(len(idea.get('sourceIds', [])) for idea in ideas)
    citation_density = total_citations / total_paragraphs if total_paragraphs > 0 else 0
    
    # 5. Concept clarity (average title word count)
    total_title_words = sum(len(idea.get('title', '').split()) for idea in ideas)
    avg_title_words = total_title_words / idea_count if idea_count > 0 else 0
    
    # 6. Source coverage (sources cited / sources available)
    cited_sources = set()
    for idea in ideas:
        cited_sources.update(idea.get('sourceIds', []))
    valid_cited_sources = cited_sources.intersection(sources.keys())
    source_coverage = min(1.0, len(valid_cited_sources) / len(sources)) if sources else 0.0
    
    return {
        "idea_count": idea_count,
        "paragraphs_per_idea": round(avg_paragraphs_per_idea, 2),
        "tier_diversity": tier_diversity,
        "citation_density": round(citation_density, 2),
        "concept_clarity": round(avg_title_words, 1),
        "source_coverage": round(source_coverage, 2),
        "total_paragraphs": total_paragraphs,
        "total_citations": total_citations
    }


def compare_quality(raw_answer: Dict, abstracted_answer: Dict) -> Dict:
    """
    Compare quality metrics between raw and abstracted modes.
    
    Returns:
    - raw_metrics: Quality scores for raw mode
    - abstracted_metrics: Quality scores for abstracted mode
    - differences: Absolute differences
    - quality_maintained: Boolean for each metric (difference < threshold)
    - overall_verdict: PASS if quality maintained across all metrics
    """
    
    raw_metrics = measure_synthesis_quality(raw_answer)
    abstracted_metrics = measure_synthesis_quality(abstracted_answer)
    
    # Calculate differences
    differences = {}
    quality_maintained = {}
    
    # Thresholds for "quality maintained"
    thresholds = {
        "idea_count": 1,  # ±1 idea is acceptable
        "paragraphs_per_idea": 0.5,  # ±0.5 paragraphs per idea
        "tier_diversity": 0,  # Must maintain all tiers
        "citation_density": 0.3,  # ±0.3 citations per paragraph
        "concept_clarity": 2.0,  # ±2 words in title
        "source_coverage": 0.2  # ±20% source coverage
    }
    
    for metric in raw_metrics:
        if metric in ["total_paragraphs", "total_citations"]:
            continue  # Skip totals, not quality metrics
        
        raw_val = raw_metrics[metric]
        abs_val = abstracted_metrics[metric]
        diff = abs(raw_val - abs_val)
        
        differences[metric] = round(diff, 2)
        quality_maintained[metric] = diff <= thresholds.get(metric, 0.5)
    
    # Overall verdict
    all_maintained = all(quality_maintained.values())
    
    return {
        "raw_metrics": raw_metrics,
        "abstracted_metrics": abstracted_metrics,
        "differences": differences,
        "quality_maintained": quality_maintained,
        "overall_verdict": "PASS" if all_maintained else "FAIL",
        "pass_count": sum(quality_maintained.values()),
        "total_metrics": len(quality_maintained)
    }


def format_comparison_report(comparison: Dict) -> str:
    """Format comparison as human-readable report."""
    
    raw = comparison["raw_metrics"]
    abstracted = comparison["abstracted_metrics"]
    diffs = comparison["differences"]
    maintained = comparison["quality_maintained"]
    
    report = []
    report.append("="*60)
    report.append("QUALITY COMPARISON: RAW vs ABSTRACTED")
    report.append("="*60)
    report.append("")
    
    metrics = [
        ("Idea Count", "idea_count"),
        ("Paragraphs per Idea", "paragraphs_per_idea"),
        ("Tier Diversity", "tier_diversity"),
        ("Citation Density", "citation_density"),
        ("Concept Clarity (words)", "concept_clarity"),
        ("Source Coverage", "source_coverage")
    ]
    
    for label, key in metrics:
        status = "✓" if maintained[key] else "✗"
        report.append(f"{status} {label:25} | RAW: {raw[key]:6} | ABS: {abstracted[key]:6} | Δ: {diffs[key]:6}")
    
    report.append("")
    report.append(f"Overall: {comparison['overall_verdict']} ({comparison['pass_count']}/{comparison['total_metrics']} metrics maintained)")
    report.append("="*60)
    
    return "\n".join(report)
