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
from openai import OpenAI
from dotenv import load_dotenv

from claims.citation_grounding import ground_answer, needs_retry

load_dotenv()

SYNTHESIS_SYSTEM_PROMPT = """You are a technical synthesis engine.

Your task is to transform retrieved documentation excerpts into a structured, insight-rich answer.

You MUST NOT summarize documents sequentially.
You MUST synthesize across sources into unified concepts.

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
- Cite ONLY excerpt IDs that actually appear in RETRIEVED EXCERPTS;
  fabricated or unresolvable IDs are stripped before the answer ships
- Every key in "sources" MUST be cited at least once in the text —
  uncited sources are dropped from the response entirely
- If the excerpts do not support a claim, omit the claim; never
  stretch a source to fit
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
- Each idea should cite 2–4 sources
- Sources should be distributed across ideas

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


def format_retrieval_context(chunks: List[Dict]) -> str:
    """
    Format retrieved chunks into context for synthesis prompt.
    
    Args:
        chunks: List of retrieved chunks with text, source metadata, and tier
        
    Returns:
        Formatted context string with numbered excerpts
    """
    context_parts = []
    
    for i, chunk in enumerate(chunks, 1):
        source_name = chunk.get('source_name', 'Unknown Source')
        source_url = chunk.get('source_url', '')
        tier = chunk.get('source_tier', 3)
        text = chunk.get('text', '')
        
        # Format tier as knowledge type
        tier_label = {1: 'docs', 2: 'practice', 3: 'failure'}.get(tier, 'unknown')
        
        context_parts.append(f"""[{i}] {source_name}
Type: {tier_label}
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

    base_prompt = f"""QUESTION:
{question}

RETRIEVED EXCERPTS:
{context}

Synthesize a structured answer following the rules above. Output ONLY the JSON object."""

    # Bounded retry: one retry, only for malformed JSON or a high share
    # of unsupported claims — never to chase tier share or coverage.
    max_attempts = 2
    last_error = None
    for attempt in range(max_attempts):
        if attempt == 0:
            user_prompt = base_prompt
        else:
            unsupported_hint = ""
            if last_error and last_error.get("unsupported"):
                listed = "\n".join(f"- {c['claim']}" for c in
                                   last_error["unsupported"][:8])
                unsupported_hint = (
                    "\n\nThe prior draft cited insufficiently supported "
                    "claims. Drop or rewrite these claims so each is "
                    f"directly backed by a cited excerpt:\n{listed}")
            user_prompt = base_prompt + unsupported_hint
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            answer_text = response.choices[0].message.content
            answer_json = json.loads(answer_text)
        except json.JSONDecodeError:
            last_error = {"unsupported": None}
            continue
        except Exception as e:
            return {
                "question": question,
                "error": f"Synthesis failed: {e}",
                "ideas": [],
                "sources": {}
            }

        # Claim-level grounding: strip unresolvable citations, drop
        # uncited sources, enrich only real chunks, score coverage.
        cleaned, receipt = ground_answer(answer_json, retrieved_chunks)
        if attempt < max_attempts - 1 and needs_retry(answer_json, receipt):
            last_error = {"unsupported":
                          receipt.get("unsupported_claims") or []}
            continue
        return {
            "question": question,
            "ideas": cleaned.get("ideas", []),
            "sources": cleaned.get("sources", {}),
            "evidence_limitation": cleaned.get("evidence_limitation"),
            "citation_receipt": receipt,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "retrieved_chunk_count": len(retrieved_chunks),
            "synthesis_attempts": attempt + 1,
        }

    return {
        "question": question,
        "error": "Failed to parse JSON response after bounded retry",
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
