"""
Test abstraction reversibility: Can we reconstruct original text from abstracted chunks?

This tests information preservation in the abstraction layer.
"""

import json
import os
from openai import OpenAI
from chunk_abstractor import compress_text

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def attempt_reconstruction(abstracted_text: str, original_text: str) -> dict:
    """
    Attempt to reconstruct original text from abstracted version.
    
    Returns:
        - reconstructed_text: LLM's attempt at reconstruction
        - similarity_score: How close to original (0-1)
        - information_preserved: What was kept
        - information_lost: What was removed
    """
    
    prompt = f"""Given this abstracted/compressed text, attempt to reconstruct the original detailed text.

Abstracted text:
{abstracted_text}

Reconstruct the original with:
- Specific examples
- Detailed phrasing
- Code snippets if applicable
- Full explanations

Reconstructed text:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        reconstructed = response.choices[0].message.content.strip()
        
        # Measure similarity
        similarity_prompt = f"""Compare these two texts and rate their semantic similarity on a scale of 0.0 to 1.0.

Original:
{original_text}

Reconstructed:
{reconstructed}

Provide:
1. Similarity score (0.0-1.0)
2. What information was preserved
3. What information was lost

Format as JSON:
{{"similarity": 0.0, "preserved": ["item1", "item2"], "lost": ["item1", "item2"]}}"""
        
        analysis_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": similarity_prompt}],
            temperature=0.0,
            max_tokens=300
        )
        
        analysis = json.loads(analysis_response.choices[0].message.content.strip())
        
        return {
            "reconstructed_text": reconstructed,
            "similarity_score": analysis.get("similarity", 0.0),
            "information_preserved": analysis.get("preserved", []),
            "information_lost": analysis.get("lost", [])
        }
    
    except Exception as e:
        print(f"Reconstruction failed: {e}")
        return {
            "reconstructed_text": "",
            "similarity_score": 0.0,
            "information_preserved": [],
            "information_lost": ["reconstruction_failed"],
            "error": str(e)
        }


def test_reversibility():
    """Test abstraction reversibility with sample chunks."""
    
    # Load a sample chunk
    import sys
    from pathlib import Path
    chunks_file = Path(__file__).parent.parent.parent / "corpus" / "embeddings" / "all_tiers_embedded_chunks.json"
    
    with open(chunks_file, 'r') as f:
        all_chunks = json.load(f)
    
    # Test with any tier 1 chunk (has examples and detail)
    tier1_chunks = [c for c in all_chunks if c.get('source_tier') == 1]
    
    if not tier1_chunks:
        print("No tier 1 chunks found")
        return
    
    # Use first tier 1 chunk
    test_chunk = tier1_chunks[0]
    original_text = test_chunk['text']
    
    print("="*60)
    print("REVERSIBILITY TEST")
    print("="*60)
    print(f"\nChunk ID: {test_chunk.get('id', 'unknown')}")
    print(f"Source: {test_chunk.get('source_name', 'unknown')}")
    print(f"Tier: {test_chunk.get('source_tier', 'unknown')}")
    print(f"\nOriginal length: {len(original_text)} chars")
    
    # Step 1: Compress
    print("\n--- STEP 1: COMPRESS ---")
    abstracted_text = compress_text(original_text)
    print(f"Abstracted length: {len(abstracted_text)} chars")
    print(f"Compression ratio: {len(abstracted_text)/len(original_text):.2%}")
    print(f"\nAbstracted text:\n{abstracted_text}")
    
    # Step 2: Attempt reconstruction
    print("\n--- STEP 2: RECONSTRUCT ---")
    result = attempt_reconstruction(abstracted_text, original_text)
    
    print(f"\nReconstructed length: {len(result['reconstructed_text'])} chars")
    print(f"\nReconstructed text:\n{result['reconstructed_text']}")
    
    # Step 3: Analysis
    print("\n--- STEP 3: ANALYSIS ---")
    print(f"Similarity score: {result['similarity_score']:.2f}")
    print(f"\nInformation preserved:")
    for item in result['information_preserved']:
        print(f"  ✓ {item}")
    print(f"\nInformation lost:")
    for item in result['information_lost']:
        print(f"  ✗ {item}")
    
    # Verdict
    print("\n--- VERDICT ---")
    if result['similarity_score'] >= 0.8:
        print("✅ REVERSIBLE - High fidelity reconstruction possible")
    elif result['similarity_score'] >= 0.5:
        print("⚠️  PARTIALLY REVERSIBLE - Core concepts preserved, details lost")
    else:
        print("❌ NOT REVERSIBLE - Significant information loss")
    
    return result


if __name__ == "__main__":
    test_reversibility()
