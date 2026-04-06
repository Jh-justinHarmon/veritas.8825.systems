"""
Chunk documents with tier metadata preservation.

This script takes the processed JSON documents and chunks them into
smaller pieces suitable for embedding and retrieval, while preserving
tier metadata throughout.

Critical invariant: Tier metadata MUST survive chunking.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


# Chunking parameters (from architecture doc)
CHUNK_SIZE = 512  # tokens (approximate as chars * 0.25)
CHUNK_OVERLAP = 64  # tokens overlap
CHARS_PER_TOKEN = 4  # rough approximation

CHUNK_SIZE_CHARS = CHUNK_SIZE * CHARS_PER_TOKEN  # ~2048 chars
CHUNK_OVERLAP_CHARS = CHUNK_OVERLAP * CHARS_PER_TOKEN  # ~256 chars


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If not at the end, try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending within last 20% of chunk
            search_start = end - int(chunk_size * 0.2)
            sentence_end = max(
                text.rfind('. ', search_start, end),
                text.rfind('.\n', search_start, end),
                text.rfind('!\n', search_start, end),
                text.rfind('?\n', search_start, end)
            )
            
            if sentence_end > search_start:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start forward, accounting for overlap
        start = end - overlap
    
    return chunks


def chunk_document(doc: Dict) -> List[Dict]:
    """
    Chunk a document while preserving tier metadata.
    
    Args:
        doc: Document dict with content and metadata
    
    Returns:
        List of chunk dicts, each with tier metadata
    """
    content = doc.get('content', '')
    
    if not content:
        return []
    
    text_chunks = chunk_text(content)
    
    chunked_docs = []
    
    for i, text_content in enumerate(text_chunks):
        chunk_doc = {
            "chunk_id": f"{doc['id']}_chunk_{i}",
            "document_id": doc['id'],
            "chunk_index": i,
            "total_chunks": len(text_chunks),
            
            # CRITICAL: Preserve tier metadata
            "source_tier": doc['source_tier'],
            "source_name": doc['source_name'],
            "url": doc['url'],
            "title": doc['title'],
            
            # Chunk content
            "text": text_content,
            "char_count": len(text_content),
            
            # Metadata
            "chunked_at": datetime.now().isoformat()
        }
        
        chunked_docs.append(chunk_doc)
    
    return chunked_docs


def main():
    """Main chunking function."""
    print("Chunking documents with tier metadata preservation...")
    
    # Input directory
    input_dir = Path(__file__).parent.parent.parent / "corpus" / "tier1_anthropic_docs"
    
    # Output directory
    output_dir = Path(__file__).parent.parent.parent / "corpus" / "chunks"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Load all JSON docs
    json_files = list(input_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "manifest.json"]
    
    print(f"\nFound {len(json_files)} documents to chunk")
    
    all_chunks = []
    
    for json_file in sorted(json_files):
        with open(json_file, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        
        print(f"\nChunking: {doc['title']}")
        print(f"  Content length: {len(doc['content'])} chars")
        
        chunks = chunk_document(doc)
        
        print(f"  Created {len(chunks)} chunks")
        
        all_chunks.extend(chunks)
    
    # Save all chunks to single file
    chunks_file = output_dir / "tier1_chunks.json"
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Create chunk manifest
    manifest = {
        "source": "Anthropic Claude Documentation (Tier 1)",
        "tier": 1,
        "chunked_at": datetime.now().isoformat(),
        "total_documents": len(json_files),
        "total_chunks": len(all_chunks),
        "chunk_size_chars": CHUNK_SIZE_CHARS,
        "chunk_overlap_chars": CHUNK_OVERLAP_CHARS,
        "chunks_file": "tier1_chunks.json",
        "tier_metadata_preserved": True
    }
    
    manifest_file = output_dir / "chunks_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Chunking complete!")
    print(f"  Total documents: {len(json_files)}")
    print(f"  Total chunks: {len(all_chunks)}")
    print(f"  Average chunks per doc: {len(all_chunks) / len(json_files):.1f}")
    print(f"  Chunks file: {chunks_file}")
    print(f"  Manifest: {manifest_file}")
    
    # Verify tier metadata preservation
    print(f"\n✓ Tier metadata verification:")
    tier_counts = {}
    for chunk in all_chunks:
        tier = chunk.get('source_tier')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    for tier, count in sorted(tier_counts.items()):
        print(f"  Tier {tier}: {count} chunks")
    
    if all(chunk.get('source_tier') == 1 for chunk in all_chunks):
        print(f"  ✓ All chunks have tier metadata preserved")
    else:
        print(f"  ⚠️  WARNING: Some chunks missing tier metadata!")


if __name__ == "__main__":
    main()
