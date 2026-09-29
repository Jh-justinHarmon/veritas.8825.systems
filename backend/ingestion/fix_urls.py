#!/usr/bin/env python3
"""
Fix URLs in embedded chunks by mapping from demo corpus files.
Demo corpus files have real URLs, embedded chunks have placeholders.
"""

import json
from pathlib import Path

def load_demo_corpus_urls():
    """Load real URLs from demo corpus files."""
    corpus_dir = Path(__file__).parent.parent.parent / "corpus"
    
    url_map = {}
    
    # Load each demo corpus file
    demo_files = [
        "claude_tool_use_demo.json",
        "stripe_webhooks_demo.json",
        "claude_vision_demo.json",
        "claude_extended_thinking_demo.json"
    ]
    
    for demo_file in demo_files:
        file_path = corpus_dir / demo_file
        if not file_path.exists():
            print(f"⚠️  Skipping {demo_file} (not found)")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract sources with real URLs
        for source in data.get('sources', []):
            title = source.get('title', '')
            url = source.get('url', '')
            tier = source.get('tier')
            
            if url and not url.startswith('https://example.com'):
                # Use title as key for matching
                url_map[title] = {
                    'url': url,
                    'tier': tier,
                    'source_name': source.get('source_type', 'unknown')
                }
        
        print(f"✓ Loaded {len(data.get('sources', []))} sources from {demo_file}")
    
    return url_map


def fix_embedded_chunks():
    """Update URLs in embedded chunks JSON."""
    
    # Manual URL mapping based on SOURCE_URL_INDEX.md
    # Since chunk titles don't match demo corpus titles, use keyword matching
    url_mappings = {
        # Claude Tool Use
        ('tool', 'claude', 1): 'https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview',
        ('tool', 'troubleshoot', 1): 'https://platform.claude.com/docs/en/agents-and-tools/tool-use/troubleshooting-tool-use',
        ('tool', 'function', 2): 'https://composio.dev/content/claude-function-calling-tools',
        ('tool', 'mcp', 2): 'https://www.mindstudio.ai/blog/claude-code-mcp-server-token-overhead',
        ('tool', 'mistake', 3): 'https://www.mindstudio.ai/blog/claude-code-skills-common-mistakes-guide',
        ('tool', 'optimis', 3): 'https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code',
        
        # Stripe Webhooks
        ('webhook', 'stripe', 1): 'https://docs.stripe.com/webhooks',
        ('webhook', 'quickstart', 1): 'https://docs.stripe.com/webhooks/quickstart',
        ('webhook', 'signature', 1): 'https://docs.stripe.com/webhooks/signature',
        ('webhook', 'implementation', 2): 'https://www.hooklistener.com/learn/stripe-webhooks-implementation',
        ('webhook', 'ngrok', 2): 'https://ngrok.com/docs/integrations/webhooks/stripe-webhooks',
        ('webhook', 'debug', 3): 'https://dev.to/nerdincode/debugging-stripe-webhook-signature-verification-errors-in-production-1h7c',
        
        # Claude Vision
        ('vision', 'claude', 1): 'https://docs.anthropic.com/en/docs/build-with-claude/vision',
        ('vision', 'best', 1): 'https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/best_practices_for_vision.ipynb',
        ('vision', 'tutorial', 2): 'https://getstream.io/blog/anthropic-claude-vision/',
        ('vision', 'guide', 2): 'https://www.claudelab.ai/guides/claude-vision-guide',
        ('vision', 'black', 3): 'https://www.cyberark.com/resources/blog/claude-ai-vision-black-pixel-edge-case',
        
        # Claude Extended Thinking
        ('thinking', 'extended', 1): 'https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking',
        ('thinking', 'prompt', 1): 'https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/extended-thinking-prompting-tips',
        ('thinking', 'aws', 2): 'https://aws.amazon.com/blogs/machine-learning/anthropic-claude-extended-thinking-is-now-available-in-amazon-bedrock/',
        ('thinking', 'help', 2): 'https://support.anthropic.com/en/articles/10078890-what-is-extended-thinking',
    }
    
    # Load embedded chunks
    chunks_file = Path(__file__).parent.parent.parent / "corpus" / "embeddings" / "all_tiers_embedded_chunks.json"
    
    if not chunks_file.exists():
        print(f"❌ ERROR: {chunks_file} not found")
        return
    
    print("\n1. Loading embedded chunks...")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"   Loaded {len(chunks)} chunks\n")
    
    # Update URLs using keyword matching
    print("2. Updating URLs with keyword matching...")
    updated_count = 0
    
    for chunk in chunks:
        title = chunk.get('title', '').lower()
        text = chunk.get('text', '').lower()
        tier = chunk.get('source_tier')
        old_url = chunk.get('url', '')
        
        # Skip if already has real URL
        if old_url and not old_url.startswith('https://example.com'):
            continue
        
        # Try to match using keywords
        for (kw1, kw2, map_tier), new_url in url_mappings.items():
            if tier == map_tier and kw1 in title + text and kw2 in title + text:
                chunk['url'] = new_url
                updated_count += 1
                print(f"   ✓ Matched: {chunk.get('title', '')[:60]}... -> {new_url[:60]}...")
                break
    
    print(f"\n   Updated {updated_count} chunk URLs\n")
    
    # Save updated chunks
    print("4. Saving updated chunks...")
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Saved to {chunks_file}\n")
    print(f"✅ Complete! Updated {updated_count}/{len(chunks)} chunks with real URLs")


if __name__ == "__main__":
    fix_embedded_chunks()
