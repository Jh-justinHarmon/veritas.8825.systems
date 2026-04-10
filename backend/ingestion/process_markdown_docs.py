"""
Process markdown documents (tier 2/3) into JSON format for chunking and embedding.

This script converts markdown files to the Veritas document format with tier metadata.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from chunk_docs import chunk_document
from embed_chunks import generate_embedding, EMBEDDING_MODEL


def process_markdown_file(md_path: Path, tier: int) -> Dict:
    """Process a markdown file into Veritas format."""
    print(f"Processing: {md_path.name} (Tier {tier})")
    
    # Read markdown content
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content:
        print(f"  ⚠️  No content in {md_path.name}")
        return None
    
    # Extract title from first heading or filename
    title = md_path.stem.replace('_', ' ').title()
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            break
    
    # Generate document ID
    doc_id = f"tier{tier}_{md_path.stem.lower()}"
    
    # Determine source name based on tier
    source_names = {
        2: "Claude Tool Use: Community Practice",
        3: "Claude Tool Use: Failure Analysis"
    }
    
    # Create document
    doc = {
        "id": doc_id,
        "source_tier": tier,
        "source_name": source_names.get(tier, f"Tier {tier} Source"),
        "url": f"https://example.com/docs/{doc_id}",  # Placeholder
        "title": title,
        "date": datetime.now().isoformat(),
        "content": content,
        "source_file": md_path.name,
        "processed_at": datetime.now().isoformat()
    }
    
    return doc


def process_tier_directory(tier_dir: Path, tier_num: int) -> list:
    """Process all markdown files in a tier directory."""
    md_files = list(tier_dir.glob("*.md"))
    
    if not md_files:
        print(f"\n⚠️  No markdown files found in {tier_dir}")
        return []
    
    print(f"\nProcessing Tier {tier_num} from {tier_dir}")
    print(f"Found {len(md_files)} markdown files")
    
    all_chunks = []
    
    for md_file in sorted(md_files):
        # Process markdown to document
        doc = process_markdown_file(md_file, tier_num)
        if not doc:
            continue
        
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
    print("Processing Tier 2 and Tier 3 markdown content...")
    
    # Directories
    corpus_dir = Path(__file__).parent.parent.parent / "corpus"
    tier2_dir = corpus_dir / "raw" / "tier2"
    tier3_dir = corpus_dir / "raw" / "tier3"
    output_dir = corpus_dir / "embeddings"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process Tier 2
    tier2_chunks = process_tier_directory(tier2_dir, 2)
    
    # Process Tier 3
    tier3_chunks = process_tier_directory(tier3_dir, 3)
    
    # Load existing Tier 1 chunks
    tier1_file = output_dir / "tier1_embedded_chunks.json"
    if tier1_file.exists():
        with open(tier1_file, 'r', encoding='utf-8') as f:
            tier1_chunks = json.load(f)
    else:
        tier1_chunks = []
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Tier 1: {len(tier1_chunks)} chunks")
    print(f"  Tier 2: {len(tier2_chunks)} chunks")
    print(f"  Tier 3: {len(tier3_chunks)} chunks")
    print(f"  Total: {len(tier1_chunks) + len(tier2_chunks) + len(tier3_chunks)} chunks")
    
    # Combine all chunks
    all_chunks = tier1_chunks + tier2_chunks + tier3_chunks
    
    # Save combined chunks
    combined_file = output_dir / "all_tiers_embedded_chunks.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved combined chunks to: {combined_file}")
    
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
