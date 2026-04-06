"""
Process Tier 2 and Tier 3 JSON documents through the chunking and embedding pipeline.

This script processes manually curated Tier 2 (Anthropic blog) and Tier 3 (community)
content to complete Phase 1 deliverables.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import existing pipeline components
from chunk_docs import chunk_document
from embed_chunks import generate_embedding, EMBEDDING_MODEL


def process_tier_directory(tier_dir: Path, tier_num: int) -> list:
    """Process all JSON files in a tier directory."""
    json_files = list(tier_dir.glob("*.json"))
    json_files = [f for f in json_files if not f.name.startswith("CURATION")]
    
    print(f"\nProcessing Tier {tier_num} from {tier_dir.name}")
    print(f"Found {len(json_files)} documents")
    
    all_chunks = []
    
    for json_file in sorted(json_files):
        with open(json_file, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        
        print(f"\n  Processing: {doc['title']}")
        print(f"  Content length: {len(doc['content'])} chars")
        
        # Chunk the document
        chunks = chunk_document(doc)
        print(f"  Created {len(chunks)} chunks")
        
        # Generate embeddings for each chunk
        for chunk in chunks:
            embedding = generate_embedding(chunk['text'])
            if embedding:
                chunk['embedding'] = embedding
                chunk['embedding_model'] = EMBEDDING_MODEL
                chunk['embedded_at'] = datetime.now().isoformat()
                all_chunks.append(chunk)
                print(f"    ✓ Embedded chunk {chunk['chunk_index'] + 1}/{chunk['total_chunks']}")
            else:
                print(f"    ✗ Failed to embed chunk {chunk['chunk_index']}")
    
    return all_chunks


def main():
    """Main processing function."""
    print("Processing Tier 2 and Tier 3 content...")
    
    # Directories
    corpus_dir = Path(__file__).parent.parent.parent / "corpus"
    tier2_dir = corpus_dir / "tier2_anthropic_blog"
    tier3_dir = corpus_dir / "tier3_community"
    output_dir = corpus_dir / "embeddings"
    
    # Process Tier 2
    tier2_chunks = process_tier_directory(tier2_dir, 2)
    
    # Process Tier 3
    tier3_chunks = process_tier_directory(tier3_dir, 3)
    
    # Combine with existing Tier 1 chunks
    tier1_file = output_dir / "tier1_embedded_chunks.json"
    with open(tier1_file, 'r', encoding='utf-8') as f:
        tier1_chunks = json.load(f)
    
    # Filter out "Loading..." chunks from Tier 1
    tier1_real = [c for c in tier1_chunks if "Loading..." not in c.get('text', '')]
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Tier 1: {len(tier1_real)} chunks (filtered from {len(tier1_chunks)})")
    print(f"  Tier 2: {len(tier2_chunks)} chunks")
    print(f"  Tier 3: {len(tier3_chunks)} chunks")
    print(f"  Total: {len(tier1_real) + len(tier2_chunks) + len(tier3_chunks)} chunks")
    
    # Combine all chunks
    all_chunks = tier1_real + tier2_chunks + tier3_chunks
    
    # Save combined chunks
    combined_file = output_dir / "all_tiers_embedded_chunks.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved combined chunks to: {combined_file}")
    
    # Create manifest
    manifest = {
        "source": "Claude Cowork Documentation - All Tiers",
        "processed_at": datetime.now().isoformat(),
        "total_chunks": len(all_chunks),
        "tier_breakdown": {
            "tier_1": len(tier1_real),
            "tier_2": len(tier2_chunks),
            "tier_3": len(tier3_chunks)
        },
        "embedding_model": EMBEDDING_MODEL,
        "chunks_file": "all_tiers_embedded_chunks.json"
    }
    
    manifest_file = output_dir / "all_tiers_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved manifest to: {manifest_file}")
    
    # Verify tier distribution
    print(f"\n✓ Tier metadata verification:")
    tier_counts = {}
    for chunk in all_chunks:
        tier = chunk.get('source_tier')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    for tier in sorted(tier_counts.keys()):
        print(f"  Tier {tier}: {tier_counts[tier]} chunks")


if __name__ == "__main__":
    main()
