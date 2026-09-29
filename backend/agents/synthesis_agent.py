"""
Synthesis Agent - Concept-Driven Answer Generation

Transforms retrieved documentation excerpts into structured, insight-rich answers
using concept-driven synthesis (not sequential summarization).

Based on Replit synthesis approach with refined prompt engineering.
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load .env with override to ensure we use the file, not shell environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

SYNTHESIS_SYSTEM_PROMPT = """You are a technical synthesis engine.

Your task is to transform retrieved documentation excerpts into a structured, insight-rich answer.

You MUST NOT summarize documents sequentially.
You MUST synthesize across sources into unified concepts.

CRITICAL REQUIREMENT - TIER 1 FIRST:

Sources marked "Type: docs [AUTHORITATIVE - CITE THIS]" are Tier 1 official documentation.
These are your PRIMARY sources. You MUST prioritize them.

MANDATORY CITATION RULE:
- Look for sources with "[AUTHORITATIVE - CITE THIS]" marker
- EVERY idea MUST cite at least 2 of these Tier 1 sources
- Cite Tier 1 sources BEFORE citing any other sources
- Most of your citations should be Tier 1

After establishing facts with Tier 1, you may add:
- Type: practice (Tier 2) for implementation examples
- Type: failure (Tier 3) for edge cases

Example: [1][2][3][7] where [1][2][3] have the [AUTHORITATIVE] marker

---

OUTPUT FORMAT (STRICT JSON):

{
  "ideas": [
    {
      "title": "string (declarative concept statement)",
      "paragraphs": ["string", "string"],
      "sourceIds": ["1", "2"]
    }
  ],
  "sources": {
    "1": "source title or description",
    "2": "source title or description"
  }
}

---

SYNTHESIS RULES:

1. CONCEPT-DRIVEN STRUCTURE
- Break the answer into 2–4 key ideas
- Each idea represents a core concept the user must understand
- Titles must be declarative statements (not questions, not labels)

GOOD: "Tool selection depends on schema clarity"
BAD: "Tool Selection" or "How tools are selected"

---

2. PARAGRAPH REQUIREMENTS
Each idea must include 1–2 paragraphs that:

- Integrate multiple sources in the SAME paragraph
- Include inline citations in brackets [1][2][3] after claims
- Combine:
  • documentation facts
  • real-world behavior or implementation patterns
  • failure modes or edge cases

DO NOT separate these into different sections.

CITATION FORMAT:
- Use [1], [2], [3] etc. to cite sources inline
- Place citations immediately after the claim they support
- Multiple citations can be adjacent: [1][2]
- Every factual claim should have at least one citation
- Example: "Claude requires explicit permissions [1]. The model uses tool schemas to decide which tool to call [2][3]."

---

3. SYNTHESIS (NOT SUMMARY)
DO NOT:
- Describe one source at a time
- List findings sequentially
- Write "Source 1 says…, Source 2 says…"

DO:
- Merge insights into a single explanation
- Explain mechanisms + implications together
- Show how pieces relate

---

4. INSIGHT GENERATION
Each idea should include at least one of:

- A pattern ("this always happens when...")
- A reframing ("the model isn't failing — it's...")
- A design principle ("you're not building X, you're designing Y")

---

5. CONCRETE DETAIL
Include specific, grounded details when available:

- parameter names
- API behavior
- example phrasing
- exact failure modes

Avoid vague statements.

---

6. SOURCE USAGE
- Use sourceIds to reference supporting material
- Each idea MUST cite 2–4 sources
- Sources should be distributed across ideas

TIER HIERARCHY (CRITICAL):
Sources are labeled by type:
- Type: docs (Tier 1) = Official documentation, specifications, authoritative sources [PRIMARY SOURCE]
- Type: practice (Tier 2) = Real-world implementation patterns, community practices [SUPPLEMENTARY]
- Type: failure (Tier 3) = Failure modes, edge cases, debugging scenarios [SUPPLEMENTARY]

CITATION REQUIREMENTS:
- EVERY idea MUST be grounded in Tier 1 (docs) citations as the foundation
- Tier 1 should represent 50-70% of all citations
- Each idea needs at least 2 Tier 1 citations
- Tier 2/3 sources supplement Tier 1 facts with context and examples
- ALWAYS cite Tier 1 first, then add Tier 2/3

Example citation pattern: [1][2][3][7] where [1][2][3] are Tier 1 docs, [7] is Tier 3 failure

---

7. TONE
- Explanatory, not academic
- Insightful, not verbose
- Confident, not speculative

---

INPUT FORMAT:

You will receive:
- A user question
- A set of retrieved excerpts with IDs

Use ONLY the provided excerpts.
Do not use outside knowledge.

---

GOAL:

Produce an answer that:
- Feels like an expert explanation
- Surfaces underlying patterns
- Combines multiple perspectives into clarity

NOT a summary. A synthesis."""


def _is_placeholder_source(url: str) -> bool:
    return not url or "example.com" in url.lower()


def format_retrieval_context(chunks: List[Dict]) -> str:
    """
    Format retrieved chunks into context for synthesis prompt.
    Sorts by tier (1 first) to make official docs more prominent.
    
    Args:
        chunks: List of retrieved chunks with text, source metadata, and tier
        
    Returns:
        Formatted context string with numbered excerpts
    """
    # Sort chunks by tier (tier 1 first) to make official docs prominent
    sorted_chunks = sorted(chunks, key=lambda c: c.get('source_tier', 3))
    
    context_parts = []
    
    for i, chunk in enumerate(sorted_chunks, 1):
        source_name = chunk.get('source_name', 'Unknown Source')
        source_url = chunk.get('source_url') or chunk.get('url', '')
        tier = chunk.get('source_tier', 3)
        text = chunk.get('text', '')
        
        if _is_placeholder_source(source_url):
            source_name = 'Synthetic demo source'
            source_url = ''
        
        # Format tier as knowledge type with emphasis on tier 1
        tier_label = {1: 'docs', 2: 'practice', 3: 'failure'}.get(tier, 'unknown')
        tier_emphasis = " [AUTHORITATIVE - CITE THIS]" if tier == 1 else ""
        
        context_parts.append(f"""[{i}] {source_name}
Type: {tier_label}{tier_emphasis}
URL: {source_url}
Text: {text}
""")
    
    return "\n---\n".join(context_parts)


def synthesize_answer(
    question: str,
    retrieved_chunks: List[Dict],
    model: str = "gpt-4o",
    api_key: Optional[str] = None
) -> Dict:
    """
    Synthesize concept-driven answer from retrieved chunks.
    
    Args:
        question: User's question
        retrieved_chunks: List of retrieved documentation chunks
        model: OpenAI model to use (default: gpt-4o)
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        
    Returns:
        Dict with question, ideas[], and sources{}
    """
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("OpenAI API key required (set OPENAI_API_KEY or pass api_key)")
    
    client = OpenAI(api_key=api_key)
    
    # Format retrieval context
    context = format_retrieval_context(retrieved_chunks)
    
    # Build user prompt
    user_prompt = f"""QUESTION:
{question}

RETRIEVED EXCERPTS:
{context}

Synthesize a structured answer following the rules above. Output ONLY the JSON object."""
    
    # Debug: Print first 500 chars of context to verify tier 1 markers
    print(f"\n[DEBUG] Context preview (first 500 chars):\n{context[:500]}\n")
    
    # Call LLM (with retry for tier 1 enforcement)
    max_retries = 2
    answer_json = {}
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Higher for synthesis creativity
                max_tokens=4000,  # Room for detailed synthesis
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            answer_text = response.choices[0].message.content
            
            # Parse JSON
            answer_json = json.loads(answer_text)
            
            # Validate tier 1 citations
            tier1_cited = set()
            for idea in answer_json.get("ideas", []):
                for source_id in idea.get("sourceIds", []):
                    idx = int(source_id) - 1
                    if 0 <= idx < len(retrieved_chunks):
                        if retrieved_chunks[idx].get('source_tier') == 1:
                            tier1_cited.add(source_id)
            
            # Check if we have tier 1 citations
            if len(tier1_cited) >= 2 or attempt == max_retries - 1:
                print(f"[TIER1] Cited {len(tier1_cited)} tier 1 sources (attempt {attempt + 1})")
                break
            else:
                print(f"[TIER1] Only {len(tier1_cited)} tier 1 citations, retrying... (attempt {attempt + 1})")
                user_prompt += "\n\nREMINDER: You MUST cite at least 2 sources marked [AUTHORITATIVE - CITE THIS]."
                continue
                
        except json.JSONDecodeError:
            if attempt == max_retries - 1:
                return {
                    "question": question,
                    "error": "Failed to parse JSON response",
                    "ideas": [],
                    "sources": {}
                }
            continue
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "question": question,
                    "error": f"Synthesis failed: {e}",
                    "ideas": [],
                    "sources": {}
                }
            continue
    
    # Map source IDs back to chunk metadata for rich source information
    try:
        llm_sources = answer_json.get("sources", {})
        enriched_sources = {}
        
        for source_id, source_title in llm_sources.items():
            # Source IDs are 1-indexed strings like "1", "2", etc.
            chunk_index = int(source_id) - 1
            if 0 <= chunk_index < len(retrieved_chunks):
                chunk = retrieved_chunks[chunk_index]
                source_url = chunk.get('source_url') or chunk.get('url', '')
                is_placeholder = _is_placeholder_source(source_url)
                enriched_sources[source_id] = {
                    "title": "Synthetic demo source" if is_placeholder else source_title,
                    "url": "" if is_placeholder else source_url,
                    "source_name": "Synthetic demo source" if is_placeholder else chunk.get('source_name', 'Unknown Source'),
                    "tier": 3 if is_placeholder else chunk.get('source_tier', 3),
                    "document_title": "Synthetic demonstration record" if is_placeholder else chunk.get('title', '')
                }
            else:
                # Fallback if source ID doesn't map to a chunk
                enriched_sources[source_id] = {
                    "title": source_title,
                    "url": "",
                    "source_name": source_title,
                    "tier": 3,
                    "document_title": ""
                }
        
        return {
            "question": question,
            "ideas": answer_json.get("ideas", []),
            "sources": enriched_sources,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "retrieved_chunk_count": len(retrieved_chunks)
        }
        
    except Exception as e:
        return {
            "question": question,
            "error": f"Synthesis failed: {e}",
            "ideas": [],
            "sources": {}
        }


def test_synthesis():
    """
    Test synthesis with sample question and mock retrieval results.
    Run: python -m backend.agents.synthesis_agent
    """
    # Mock retrieval results (simulating what retriever would return)
    mock_chunks = [
        {
            "text": "Tool use in Claude works through an agentic loop. When you provide Claude with tool definitions, it can decide to use one or more tools to help answer a user's question. The model analyzes the available tools, determines which ones are relevant, generates the appropriate input parameters, and requests tool execution.",
            "source_name": "Claude API Documentation: Tool Use Overview",
            "source_url": "https://docs.anthropic.com/en/docs/build-with-claude/tool-use",
            "source_tier": 1
        },
        {
            "text": "A tool definition includes a name, description, and input_schema. The name should be descriptive and specific. The description should explain what the tool does and when to use it. The input_schema is a JSON Schema object that defines the expected parameters, their types, and whether they're required.",
            "source_name": "Claude API Documentation: Defining Tools",
            "source_url": "https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools",
            "source_tier": 1
        },
        {
            "text": "To improve tool use reliability, follow these best practices: Use specific, action-oriented names (search_customer_by_email vs search). Write descriptions that include when to use the tool, not just what it does. Leverage JSON Schema features like enum for constrained values. Break complex tools into focused, single-purpose tools.",
            "source_name": "Composio: Claude Function Calling Best Practices",
            "source_url": "https://composio.dev/tools/claude-ai/function-calling",
            "source_tier": 2
        },
        {
            "text": "Common tool use failures: Vague tool descriptions lead to incorrect tool selection. Missing or underspecified parameters cause the model to hallucinate values. Too many tools in context degrades selection accuracy. Overly flexible schemas produce inconsistent arguments.",
            "source_name": "GitHub Issue: Tool Use Reliability",
            "source_url": "https://github.com/anthropics/anthropic-sdk-python/issues/234",
            "source_tier": 3
        }
    ]
    
    question = "Why is Claude calling the wrong tool or using incorrect parameters?"
    
    print("Testing synthesis agent...")
    print(f"Question: {question}\n")
    
    result = synthesize_answer(question, mock_chunks)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        if "raw_response" in result and result["raw_response"]:
            print(f"\nRaw response:\n{result['raw_response']}")
    else:
        print("SUCCESS!\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    test_synthesis()
