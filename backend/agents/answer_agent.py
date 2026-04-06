"""
Answer Generation Agent for Veritas

This agent generates answers to questions using retrieved documents
and includes inline citations that map back to source documents.

Critical invariant: Citations must preserve tier metadata.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from retrieval.simple_retriever import retrieve_chunks

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Models
ANSWER_MODEL = "gpt-4o-mini"  # Cost-effective for V1
EMBEDDING_MODEL = "text-embedding-3-small"


def generate_query_embedding(query: str) -> List[float]:
    """Generate embedding for a query using OpenAI API."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return None


def generate_answer_with_citations(
    question: str,
    retrieved_chunks: List[Dict],
    model: str = ANSWER_MODEL
) -> Dict:
    """
    Generate an answer to a question using retrieved chunks.
    
    Args:
        question: User's question
        retrieved_chunks: List of chunk dicts with text and metadata
        model: OpenAI model to use
    
    Returns:
        Dict with answer text, citations, and metadata
    """
    # Format context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        source_info = f"[{i}] {chunk['title']} (Tier {chunk['source_tier']})"
        context_parts.append(f"{source_info}\n{chunk['text']}\n")
    
    context = "\n".join(context_parts)
    
    # Create prompt
    prompt = f"""You are a technical documentation assistant. Answer the user's question using ONLY the provided documentation excerpts.

CRITICAL RULES:
1. Use inline citations like [1], [2], [3] to reference sources
2. Every factual claim MUST have a citation
3. If information is not in the provided sources, say "I don't have information about that in the documentation"
4. Do not make up information or use external knowledge

DOCUMENTATION EXCERPTS:
{context}

USER QUESTION:
{question}

Provide a clear, accurate answer with inline citations."""
    
    # Generate answer
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful technical documentation assistant that always cites sources."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1000
        )
        
        answer_text = response.choices[0].message.content
        
        # Extract citations from answer
        citations = extract_citations(answer_text, retrieved_chunks)
        
        return {
            "question": question,
            "answer": answer_text,
            "citations": citations,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "retrieved_chunk_count": len(retrieved_chunks)
        }
        
    except Exception as e:
        return {
            "question": question,
            "answer": f"Error generating answer: {e}",
            "citations": [],
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


def extract_citations(answer_text: str, retrieved_chunks: List[Dict]) -> List[Dict]:
    """
    Extract citation numbers from answer text and map to source chunks.
    
    Args:
        answer_text: Generated answer with inline citations like [1], [2]
        retrieved_chunks: List of chunks that were used for generation
    
    Returns:
        List of citation dicts with number, chunk info, and tier metadata
    """
    # Find all citation numbers in the answer
    citation_pattern = r'\[(\d+)\]'
    citation_numbers = set(re.findall(citation_pattern, answer_text))
    
    citations = []
    
    for num_str in sorted(citation_numbers, key=int):
        num = int(num_str)
        
        # Map citation number to chunk (1-indexed)
        if 1 <= num <= len(retrieved_chunks):
            chunk = retrieved_chunks[num - 1]
            
            citation = {
                "citation_number": num,
                "chunk_id": chunk.get("chunk_id"),
                "document_id": chunk.get("document_id"),
                
                # CRITICAL: Preserve tier metadata
                "source_tier": chunk.get("source_tier"),
                "source_name": chunk.get("source_name"),
                "title": chunk.get("title"),
                "url": chunk.get("url"),
                
                # Snippet for display
                "snippet": chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
            }
            
            citations.append(citation)
    
    return citations


def test_answer_generation():
    """Test the answer generation agent with sample data."""
    print("Testing Answer Generation Agent...")
    
    # Load embedded chunks (all tiers)
    chunks_file = Path(__file__).parent.parent.parent / "corpus" / "embeddings" / "all_tiers_embedded_chunks.json"
    
    if not chunks_file.exists():
        print(f"❌ Chunks file not found: {chunks_file}")
        return
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        all_chunks = json.load(f)
    
    print(f"✓ Loaded {len(all_chunks)} chunks")
    
    # Show tier distribution
    tier_counts = {}
    for chunk in all_chunks:
        tier = chunk.get('source_tier')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print(f"✓ Tier distribution:")
    for tier in sorted(tier_counts.keys()):
        print(f"  Tier {tier}: {tier_counts[tier]} chunks")
    
    # Test questions (focused on Claude Cowork)
    test_questions = [
        "What is Claude Cowork?",
        "How do I get started with Cowork?",
        "What can Claude do with computer use in Cowork?",
        "How do I use plugins in Cowork?",
        "How do I use Cowork safely?"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")
        
        # Generate query embedding
        query_embedding = generate_query_embedding(question)
        if not query_embedding:
            print("❌ Failed to generate query embedding")
            continue
        
        # Retrieve relevant chunks using semantic search (with authority weighting)
        retrieved_chunks = retrieve_chunks(query_embedding, all_chunks, top_k=6)
        
        print(f"✓ Retrieved {len(retrieved_chunks)} chunks")
        for i, chunk in enumerate(retrieved_chunks[:3], 1):
            print(f"  {i}. {chunk['title'][:60]}... (Tier {chunk['source_tier']})")
        
        result = generate_answer_with_citations(question, retrieved_chunks)
        
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nCitations ({len(result['citations'])}):")
        for citation in result['citations']:
            print(f"  [{citation['citation_number']}] {citation['title']} (Tier {citation['source_tier']})")
            print(f"      {citation['snippet']}")
        
        print(f"\nModel: {result['model']}")
        print(f"Chunks used: {result['retrieved_chunk_count']}")


if __name__ == "__main__":
    test_answer_generation()
