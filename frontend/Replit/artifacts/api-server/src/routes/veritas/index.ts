import { Router } from "express";
import { anthropic } from "@workspace/integrations-anthropic-ai";
import { SynthesizeAnswerBody } from "@workspace/api-zod";

const router = Router();

const SYSTEM_PROMPT = `You are Veritas, a technical knowledge synthesis engine for developers.

When given a developer question, produce a structured answer that integrates three types of knowledge:
- "docs": Official documentation, specs, and API references
- "practice": Real-world usage patterns, idiomatic approaches, SDK usage, community consensus
- "failure": Known failure modes, bugs, common mistakes, gotchas, error messages

Your response must be ONLY a valid JSON object — no markdown, no preamble. Follow this structure exactly:

{
  "ideas": [
    {
      "id": "short-kebab-id",
      "concept": "A precise one-sentence declarative thesis about this key concept",
      "paragraphs": [
        "Paragraph text integrating multiple perspectives. Use backticks for inline code: \`code\`. Use [source-id] immediately after a claim to cite it. Do NOT separate paragraphs by knowledge type — weave them together."
      ],
      "sourceIds": ["source-id-1", "source-id-2"]
    }
  ],
  "sources": {
    "source-id": {
      "label": "Full source name",
      "short": "domain.com/path or short reference",
      "type": "docs" | "practice" | "failure",
      "meta": "Version, date, or context (e.g. 'v1.4 · March 2025' or '2024')",
      "excerpt": "A specific, concrete technical detail — a code pattern, error message, API field, or direct quote"
    }
  }
}

Rules:
1. Produce 3–5 ideas. Each idea is a key concept the developer must understand to answer the question well.
2. Concept statements are declarative assertions, not questions or headings.
3. Each idea's paragraphs integrate all three knowledge types in unified prose — docs, practice, and failure perspectives appear in the same paragraph, not separate ones.
4. Use [source-id] immediately after any specific claim. Cite inline, not at the end of paragraphs.
5. Use \`backticks\` for all inline code: method names, property names, types, error names, config keys.
6. Source IDs must be lowercase kebab-case and unique.
7. Excerpts must be specific and concrete: a code snippet, an exact error string, an API field name, a version number — never a generic summary.
8. Sources span the full range: official docs/specs, SDK source code, blog posts by respected practitioners, GitHub issues, Stack Overflow, community forums, Hacker News threads.
9. Do not add commentary, markdown fences, or any text outside the JSON object.`;

const EXAMPLE_QUESTIONS = [
  {
    id: "streaming-tool-use",
    question: "How do I stream tool use responses in Claude?",
    description: "Event protocol, JSON accumulation, execution gating, token budget",
  },
  {
    id: "react-suspense-errors",
    question: "How does error handling work with React Suspense?",
    description: "Error boundaries, async boundaries, production failure modes",
  },
  {
    id: "postgres-transactions",
    question: "When should I use database transactions in PostgreSQL?",
    description: "ACID guarantees, isolation levels, deadlock failure patterns",
  },
  {
    id: "typescript-generics",
    question: "How do TypeScript generics interact with conditional types?",
    description: "Inference, distributivity, common pattern failures",
  },
];

router.get("/examples", (_req, res) => {
  res.json(EXAMPLE_QUESTIONS);
});

router.post("/synthesize", async (req, res) => {
  const parseResult = SynthesizeAnswerBody.safeParse(req.body);
  if (!parseResult.success) {
    res.status(400).json({
      error: "INVALID_REQUEST",
      message: "Question must be between 5 and 500 characters.",
    });
    return;
  }

  const { question } = parseResult.data;

  try {
    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 8192,
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: "user",
          content: question,
        },
      ],
    });

    const rawContent = message.content[0];
    if (rawContent.type !== "text") {
      throw new Error("Unexpected response type from Claude");
    }

    let jsonText = rawContent.text.trim();
    // Strip markdown code fences if Claude wraps the response
    if (jsonText.startsWith("```")) {
      jsonText = jsonText.replace(/^```(?:json)?\n?/, "").replace(/\n?```$/, "").trim();
    }

    const answer = JSON.parse(jsonText);

    res.json({
      question,
      ideas: answer.ideas,
      sources: answer.sources,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("Veritas synthesis error:", message);
    res.status(500).json({
      error: "SYNTHESIS_FAILED",
      message: "Failed to synthesize an answer. Please try again.",
    });
  }
});

export default router;
