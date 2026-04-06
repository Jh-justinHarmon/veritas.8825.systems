"""
Process downloaded Claude API PDF documentation into JSON format with tier metadata.

This script extracts text from PDF files and converts them to the Veritas
document format with tier tagging.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2


# Input directory (Downloads folder)
DOWNLOADS_DIR = Path.home() / "Downloads"

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "corpus" / "tier1_anthropic_docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def process_claude_pdf(pdf_path: Path) -> Dict:
    """Process a Claude documentation PDF into Veritas format."""
    print(f"Processing: {pdf_path.name}")
    
    # Extract text
    content = extract_text_from_pdf(pdf_path)
    
    if not content:
        print(f"  ⚠️  No content extracted from {pdf_path.name}")
        return None
    
    # Generate document ID from filename
    doc_id = pdf_path.stem.lower().replace(" ", "_").replace("-", "_")
    doc_id = f"claude_docs_{doc_id}"
    
    # Extract title from filename (remove " - Claude API Docs.pdf" suffix)
    title = pdf_path.stem
    if " - Claude API Docs" in title:
        title = title.replace(" - Claude API Docs", "")
    elif " - Claude Help Center" in title:
        title = title.replace(" - Claude Help Center", "")
    
    # Create document
    doc = {
        "id": doc_id,
        "source_tier": 1,
        "source_name": "Anthropic Claude Documentation",
        "url": f"https://docs.anthropic.com/en/docs/{doc_id.replace('claude_docs_', '')}",
        "title": title,
        "date": datetime.now().isoformat(),
        "content": content,
        "source_file": pdf_path.name,
        "processed_at": datetime.now().isoformat()
    }
    
    return doc


def main():
    """Main processing function."""
    print("Processing Claude PDF documentation...")
    print(f"Input directory: {DOWNLOADS_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Find all Claude PDF files in Downloads
    pdf_files = list(DOWNLOADS_DIR.glob("*Claude*.pdf"))
    
    if not pdf_files:
        print("\n⚠️  No Claude PDF files found in Downloads folder")
        print("Expected files like: 'Intro to Claude - Claude API Docs.pdf'")
        return
    
    print(f"\nFound {len(pdf_files)} PDF files")
    
    processed_docs = []
    
    for pdf_path in sorted(pdf_files):
        doc = process_claude_pdf(pdf_path)
        
        if doc:
            processed_docs.append(doc)
            
            # Save individual doc
            filename = f"{doc['id']}.json"
            filepath = OUTPUT_DIR / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Saved: {filename} ({len(doc['content'])} chars)")
    
    # Save manifest
    manifest = {
        "source": "Anthropic Claude Documentation",
        "tier": 1,
        "processed_at": datetime.now().isoformat(),
        "total_docs": len(processed_docs),
        "docs": [
            {
                "id": doc["id"],
                "title": doc["title"],
                "url": doc["url"],
                "content_length": len(doc["content"])
            }
            for doc in processed_docs
        ]
    }
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Processing complete!")
    print(f"  Total docs: {len(processed_docs)}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Total content: {sum(len(doc['content']) for doc in processed_docs):,} characters")


if __name__ == "__main__":
    main()
