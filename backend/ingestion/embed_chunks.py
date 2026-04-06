"""
Generate embeddings for chunks using OpenAI embeddings API.

This script takes the chunked documents and generates embeddings
while preserving tier metadata.

Critical invariant: Tier metadata MUST survive embedding.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import time

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"  # Cost-effective for V1


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a text using OpenAI API."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def embed_chunks(chunks: List[Dict], batch_size: int = 100) -> List[Dict]:
    """
    Generate embeddings for all chunks.
    
    Args:
        chunks: List of chunk dicts
        batch_size: Number of chunks to process at once
    
    Returns:
        List of chunks with embeddings added
    """
    embedded_chunks = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        print(f"\nProcessing batch {i // batch_size + 1} ({len(batch)} chunks)...")
        
        for chunk in batch:
            text = chunk['text']
            
            # Generate embedding
            embedding = generate_embedding(text)
            
            if embedding:
                # Add embedding to chunk (tier metadata already present)
                chunk['embedding'] = embedding
                chunk['embedding_model'] = EMBEDDING_MODEL
                chunk['embedded_at'] = datetime.now().isoformat()
                
                embedded_chunks.append(chunk)
                
                print(f"  ✓ {chunk['chunk_id'][:50]}... (tier {chunk['source_tier']})")
            else:
                print(f"  ✗ Failed: {chunk['chunk_id']}")
            
            # Rate limiting - be polite to API
            time.sleep(0.05)
    
    return embedded_chunks


def main():
    """Main embedding function."""
    print("Generating embeddings for chunks...")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  ERROR: OPENAI_API_KEY not found in environment")
        print("Please create backend/.env file with your OpenAI API key")
        print("See backend/.env.example for template")
        return
    
    # Input file
    chunks_file = Path(__file__).parent.parent.parent / "corpus" / "chunks" / "tier1_chunks.json"
    
    if not chunks_file.exists():
        print(f"\n⚠️  ERROR: Chunks file not found: {chunks_file}")
        print("Run chunk_docs.py first")
        return
    
    # Output directory
    output_dir = Path(__file__).parent.parent.parent / "corpus" / "embeddings"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Input file: {chunks_file}")
    print(f"Output directory: {output_dir}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    
    # Load chunks
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"\nLoaded {len(chunks)} chunks")
    
    # Generate embeddings
    embedded_chunks = embed_chunks(chunks)
    
    # Save embedded chunks
    output_file = output_dir / "tier1_embedded_chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(embedded_chunks, f, indent=2, ensure_ascii=False)
    
    # Create manifest
    manifest = {
        "source": "Anthropic Claude Documentation (Tier 1)",
        "tier": 1,
        "embedded_at": datetime.now().isoformat(),
        "total_chunks": len(embedded_chunks),
        "embedding_model": EMBEDDING_MODEL,
        "embeddings_file": "tier1_embedded_chunks.json",
        "tier_metadata_preserved": True
    }
    
    manifest_file = output_dir / "embeddings_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Embedding complete!")
    print(f"  Total chunks embedded: {len(embedded_chunks)}")
    print(f"  Embeddings file: {output_file}")
    print(f"  Manifest: {manifest_file}")
    
    # Verify tier metadata preservation
    print(f"\n✓ Tier metadata verification:")
    tier_counts = {}
    for chunk in embedded_chunks:
        tier = chunk.get('source_tier')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    for tier, count in sorted(tier_counts.items()):
        print(f"  Tier {tier}: {count} chunks")
    
    if all(chunk.get('source_tier') == 1 for chunk in embedded_chunks):
        print(f"  ✓ All chunks have tier metadata preserved")
    else:
        print(f"  ⚠️  WARNING: Some chunks missing tier metadata!")
    
    # Calculate approximate cost
    total_tokens = sum(len(chunk['text']) // 4 for chunk in embedded_chunks)
    cost = (total_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens for text-embedding-3-small
    print(f"\n💰 Approximate cost: ${cost:.4f}")


if __name__ == "__main__":
    main()
