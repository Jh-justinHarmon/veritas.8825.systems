"""
Lightweight chunk abstraction for input-agnostic testing.

This is NOT the final representation layer.
This is a controlled degradation test to prove reasoning emerges
from conceptual structure, not raw data fidelity.
"""

import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def compress_text(text: str) -> str:
    """
    Compress text to core statements only.
    
    Strategy:
    - Keep mechanisms and relationships
    - Remove examples, specific phrasing, verbosity
    - Preserve signal, remove surface detail
    """
    
    prompt = f"""Extract only the core conceptual statements from this text.

Rules:
- Keep: mechanisms, relationships, structure
- Remove: examples, specific phrasing, verbosity
- Output: 2-3 sentences maximum capturing the essential claim

Text:
{text}

Core statements:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheap and fast for compression
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        compressed = response.choices[0].message.content.strip()
        return compressed
    
    except Exception as e:
        print(f"Compression failed: {e}")
        # Fallback: simple heuristic
        sentences = text.split('. ')
        return '. '.join(sentences[:2]) + '.'


def abstract_chunks(chunks: list) -> list:
    """
    Create abstracted version of chunks for input-agnostic testing.
    
    Preserves:
    - Chunk IDs (for citation mapping)
    - Source metadata (tier, URL, etc.)
    
    Compresses:
    - Text content (removes examples, keeps core statements)
    """
    abstracted = []
    
    for i, chunk in enumerate(chunks):
        print(f"  Abstracting chunk {i+1}/{len(chunks)}...")
        
        # Create a copy of the chunk and only modify the text
        abstracted_chunk = chunk.copy()
        abstracted_chunk["text"] = compress_text(chunk["text"])
        
        abstracted.append(abstracted_chunk)
    
    return abstracted
