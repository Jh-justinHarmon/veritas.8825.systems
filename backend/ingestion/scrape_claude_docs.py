"""
Scrape Anthropic Claude documentation from platform.claude.com/docs

This script scrapes the official Claude API documentation and saves it
with tier metadata for the Veritas answer engine.

Tier: 1 (Official Documentation)
Source: platform.claude.com/docs
"""

import json
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Base URL for Claude docs
BASE_URL = "https://docs.anthropic.com"
DOCS_BASE = f"{BASE_URL}/en/docs"

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "corpus" / "tier1_anthropic_docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def scrape_page(url: str) -> Dict:
    """Scrape a single documentation page."""
    print(f"Scraping: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Untitled"
        
        # Extract main content (adjust selectors based on actual site structure)
        content_div = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        
        if content_div:
            # Remove navigation, headers, footers
            for tag in content_div.find_all(['nav', 'header', 'footer']):
                tag.decompose()
            
            content_text = content_div.get_text(separator='\n', strip=True)
        else:
            content_text = ""
        
        # Create document metadata
        doc = {
            "id": f"claude_docs_{url.split('/')[-1]}",
            "source_tier": 1,
            "source_name": "Anthropic Claude Documentation",
            "url": url,
            "title": title_text,
            "date": datetime.now().isoformat(),
            "content": content_text,
            "scraped_at": datetime.now().isoformat()
        }
        
        return doc
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def get_doc_urls() -> List[str]:
    """
    Get list of documentation URLs to scrape.
    
    For V1, we'll start with a curated list of key pages.
    In production, this would crawl the sitemap or navigation.
    """
    # Key Claude API documentation pages
    urls = [
        f"{DOCS_BASE}/intro",
        f"{DOCS_BASE}/api",
        f"{DOCS_BASE}/models",
        f"{DOCS_BASE}/messages",
        f"{DOCS_BASE}/streaming",
        f"{DOCS_BASE}/tool-use",
        f"{DOCS_BASE}/prompt-engineering",
        f"{DOCS_BASE}/rate-limits",
        f"{DOCS_BASE}/errors",
        f"{DOCS_BASE}/authentication",
    ]
    
    return urls


def main():
    """Main scraping function."""
    print("Starting Claude documentation scrape...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    urls = get_doc_urls()
    print(f"Found {len(urls)} pages to scrape")
    
    scraped_docs = []
    
    for url in urls:
        doc = scrape_page(url)
        if doc:
            scraped_docs.append(doc)
            
            # Save individual doc
            filename = f"{doc['id']}.json"
            filepath = OUTPUT_DIR / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Saved: {filename}")
        
        # Be polite - don't hammer the server
        time.sleep(1)
    
    # Save manifest
    manifest = {
        "source": "Anthropic Claude Documentation",
        "tier": 1,
        "scraped_at": datetime.now().isoformat(),
        "total_docs": len(scraped_docs),
        "docs": [
            {
                "id": doc["id"],
                "title": doc["title"],
                "url": doc["url"]
            }
            for doc in scraped_docs
        ]
    }
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Scraping complete!")
    print(f"  Total docs: {len(scraped_docs)}")
    print(f"  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
