"""
Simple retrieval system for Veritas V1

Uses cosine similarity on embeddings to find relevant chunks.
For V1, we're using a simple in-memory approach.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def retrieve_chunks(
    query_embedding: List[float],
    all_chunks: List[Dict],
    top_k: int = 6,
    authority_weight: float = 0.3
) -> List[Dict]:
    """
    Retrieve top-k most relevant chunks using authority-weighted scoring.
    
    Scoring formula (from architecture doc):
    score = (0.7 * cosine_similarity) + (0.3 * authority_score)
    
    Authority scores by tier:
    - Tier 1: 1.0 (Official docs)
    - Tier 2: 0.7 (Vendor content)
    - Tier 3: 0.4 (Community)
    
    Args:
        query_embedding: Query embedding vector
        all_chunks: List of all chunks with embeddings
        top_k: Number of chunks to return
        authority_weight: Weight for authority score (default 0.3)
    
    Returns:
        List of top-k chunks sorted by score
    """
    # Authority scores by tier
    tier_authority = {
        1: 1.0,
        2: 0.7,
        3: 0.4
    }
    
    scored_chunks = []
    
    for chunk in all_chunks:
        # Skip chunks without embeddings
        if 'embedding' not in chunk:
            continue
        
        # Calculate cosine similarity
        similarity = cosine_similarity(query_embedding, chunk['embedding'])
        
        # Get authority score based on tier
        tier = chunk.get('source_tier', 3)
        authority = tier_authority.get(tier, 0.4)
        
        # Combined score: 70% similarity + 30% authority
        score = (0.7 * similarity) + (0.3 * authority)
        
        scored_chunks.append({
            'chunk': chunk,
            'score': score,
            'similarity': similarity,
            'authority': authority
        })
    
    # Sort by score (descending)
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top-k chunks
    return [item['chunk'] for item in scored_chunks[:top_k]]


def load_chunks(chunks_file: Path = None) -> List[Dict]:
    """Load all embedded chunks from file."""
    if chunks_file is None:
        chunks_file = Path(__file__).parent.parent.parent / "corpus" / "embeddings" / "tier1_embedded_chunks.json"
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    # Test retrieval
    print("Testing simple retriever...")
    
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")
    
    # Test with first chunk's embedding as query
    if chunks:
        test_embedding = chunks[0]['embedding']
        results = retrieve_chunks(test_embedding, chunks, top_k=3)
        
        print(f"\nTop 3 results for test query:")
        for i, chunk in enumerate(results, 1):
            print(f"{i}. {chunk['title']} (Tier {chunk['source_tier']})")
            print(f"   {chunk['text'][:100]}...")
