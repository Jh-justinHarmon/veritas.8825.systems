"""
Answer generation with automatic eval scoring.

Combines answer_agent.py with scoring.py to generate answers
and automatically evaluate their quality.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.answer_agent import generate_query_embedding, generate_answer_with_citations
from retrieval.simple_retriever import retrieve_chunks, load_chunks
from evals.scoring import evaluate_answer


def answer_with_eval(question: str, all_chunks: list, top_k: int = 6) -> dict:
    """
    Generate an answer and evaluate it automatically.
    
    Args:
        question: User's question
        all_chunks: All available chunks
        top_k: Number of chunks to retrieve
    
    Returns:
        Dict with answer, citations, and eval scores
    """
    # Generate query embedding
    query_embedding = generate_query_embedding(question)
    if not query_embedding:
        return {
            "question": question,
            "error": "Failed to generate query embedding"
        }
    
    # Retrieve relevant chunks
    retrieved_chunks = retrieve_chunks(query_embedding, all_chunks, top_k=top_k)
    
    # Generate answer with citations
    answer_result = generate_answer_with_citations(question, retrieved_chunks)
    
    # Evaluate answer quality
    eval_result = evaluate_answer(
        question=question,
        answer=answer_result['answer'],
        citations=answer_result['citations']
    )
    
    # Combine results
    return {
        "question": question,
        "answer": answer_result['answer'],
        "citations": answer_result['citations'],
        "eval": eval_result,
        "retrieved_chunks": len(retrieved_chunks),
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Test answer generation with eval."""
    print("Testing Answer Generation with Eval Scoring...")
    print("="*60)
    
    # Load chunks
    chunks = load_chunks()
    print(f"\n✓ Loaded {len(chunks)} chunks")
    
    # Show tier distribution
    tier_counts = {}
    for chunk in chunks:
        tier = chunk.get('source_tier')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print(f"✓ Tier distribution:")
    for tier in sorted(tier_counts.keys()):
        print(f"  Tier {tier}: {tier_counts[tier]} chunks")
    
    # Test questions
    test_questions = [
        "What is Claude Cowork?",
        "How do I get started with Cowork?",
        "What are the safety considerations for using Cowork?"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")
        
        result = answer_with_eval(question, chunks)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        # Display answer
        print(f"\nAnswer:\n{result['answer'][:500]}...")
        
        # Display eval scores
        print(f"\n📊 Eval Scores:")
        print(f"  Overall: {result['eval']['overall_score']:.2f}")
        print(f"  Needs Review: {result['eval']['needs_review']}")
        
        for dimension, data in result['eval']['scores'].items():
            print(f"  {dimension.title()}: {data['score']:.2f} - {data['explanation']}")
        
        print(f"\n  Recommendation: {result['eval']['recommendation']}")
        
        # Display citations
        print(f"\n📚 Citations ({len(result['citations'])}):")
        for citation in result['citations'][:3]:
            print(f"  [{citation['citation_number']}] {citation['title'][:50]}... (Tier {citation['source_tier']})")


if __name__ == "__main__":
    main()
