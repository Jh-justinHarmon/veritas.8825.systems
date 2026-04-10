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
    authority_weight: float = 0.3,
    ensure_tier_diversity: bool = True
) -> List[Dict]:
    """
    Retrieve most relevant chunks using cosine similarity + authority weighting.
    
    Args:
        query_embedding: Query embedding vector
        all_chunks: List of all available chunks with embeddings
        top_k: Number of chunks to return
        authority_weight: Weight for authority score (0-1)
        ensure_tier_diversity: If True, ensure at least one chunk from each tier
        
    Returns:
        List of top-k most relevant chunks
    """
    # Authority scores by tier (higher tier = higher authority)
    tier_authority = {
        1: 1.0,   # Tier 1: Official docs (highest authority)
        2: 0.7,   # Tier 2: Practice/implementation
        3: 0.4    # Tier 3: Failure cases
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
            'authority': authority,
            'tier': tier
        })
    
    # Sort by score (descending)
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    
    if ensure_tier_diversity:
        # Ensure tier diversity: get top chunks from each tier
        tier_chunks = {1: [], 2: [], 3: []}
        for item in scored_chunks:
            tier = item['tier']
            if tier in tier_chunks:
                tier_chunks[tier].append(item)
        
        # Get top 2 from tier 1, top 2 from tier 2, top 2 from tier 3
        # Adjust if tiers don't have enough chunks
        selected = []
        chunks_per_tier = max(1, top_k // 3)
        
        for tier in [1, 2, 3]:
            tier_top = tier_chunks[tier][:chunks_per_tier]
            selected.extend(tier_top)
        
        # Fill remaining slots with highest scored chunks not yet selected
        remaining_slots = top_k - len(selected)
        if remaining_slots > 0:
            selected_chunk_ids = {id(item['chunk']) for item in selected}
            for item in scored_chunks:
                if id(item['chunk']) not in selected_chunk_ids:
                    selected.append(item)
                    if len(selected) >= top_k:
                        break
        
        # Sort selected by score
        selected.sort(key=lambda x: x['score'], reverse=True)
        return [item['chunk'] for item in selected[:top_k]]
    else:
        # Return top-k chunks by score
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
