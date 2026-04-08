// Phase 1: Hardcoded Ground Truth for Tool Use & Function Calling
// This is the perfect example that defines what Veritas should look and feel like

export const HARDCODED_RESPONSE = {
  sections: [
    {
      title: "Core Answer",
      content: "Claude selects tools based on how well your tool definitions match the user's intent. Each tool includes a name, description, and parameter schema, and the model uses these to decide which tool to call and how to populate its arguments [1][2].\n\nIf tools are vaguely defined or overlapping, Claude may choose the wrong tool because descriptions are ambiguous, infer missing parameters incorrectly, or generate arguments that don't match your intended structure [6].\n\nIn other words, the model isn't 'failing' — it's making the best decision it can based on the signals you provided in the tool schema [1][2]. When Claude decides to use a tool, it returns a tool_use content block with the tool name and generated parameters. Your application executes the tool and returns the result, which Claude processes to continue the conversation.",
      tier: 1,
      citations: [1, 2, 6]
    },
    {
      title: "Implementation Insight",
      content: "In practice, reliable tool use comes down to making your tools unambiguous and easy for the model to reason about [4].\n\nStrong patterns include:\n\n• Be extremely specific in tool descriptions [4]\nInstead of 'Get user data,' use: 'Retrieve a user's account details by user ID for account management tasks.'\n\n• Use constrained schemas wherever possible [2][4]\nUse enum for fixed values, mark required fields explicitly, avoid optional fields unless necessary.\n\n• Design tools to be distinct, not flexible [3][5]\nMany small, focused tools work better than one large 'do everything' tool.\n\n• Include examples in descriptions [4]\nShow when the tool should be used — this improves selection accuracy significantly.\n\nThe key idea: You're not just defining an API — you're designing a decision surface for the model.",
      tier: 2,
      citations: [2, 3, 4, 5]
    },
    {
      title: "Common Pitfalls",
      content: "Most failures come from subtle design issues that aren't obvious from the docs:\n\n• Vague or overlapping tool descriptions [6]\n→ Claude picks the 'closest match,' which may be wrong\n\n• Missing or underspecified parameters [6]\n→ The model fills in gaps, leading to hallucinated or incorrect values\n\n• Too many tools in context [3][7]\n→ Tool selection degrades as the model has more options to choose from\n\n• Overly flexible schemas [6]\n→ The model has too much freedom and produces inconsistent arguments\n\n• Tools that require hidden assumptions [6]\n→ If something isn't explicitly stated in the schema, the model won't reliably infer it\n\n**The pattern across all of these: Claude isn't misbehaving — it's exposing ambiguity in your tool design.**\n\n**Key takeaway: Tool use failures are usually not model errors — they're schema design problems made visible.**",
      tier: 3,
      citations: [3, 6, 7]
    }
  ],
  citations: [
    {
      id: 1,
      text: "Tool use in Claude works through an agentic loop. When you provide Claude with tool definitions, it can decide to use one or more tools to help answer a user's question. The model analyzes the available tools, determines which ones are relevant, generates the appropriate input parameters, and requests tool execution.",
      url: "https://docs.anthropic.com/en/docs/build-with-claude/tool-use",
      tier: 1,
      sourceName: "Claude API Documentation: Tool Use Overview"
    },
    {
      id: 2,
      text: "A tool definition includes a name, description, and input_schema. The name should be descriptive and specific. The description should explain what the tool does and when to use it. The input_schema is a JSON Schema object that defines the expected parameters, their types, and whether they're required.",
      url: "https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools",
      tier: 1,
      sourceName: "Claude API Documentation: Defining Tools"
    },
    {
      id: 3,
      text: "When working with many tools, context window management becomes critical. The Tool Search Tool pattern allows Claude to first search through available tools before deciding which ones to use, reducing the upfront token cost. For applications with 50+ tools, this can save 20,000+ tokens per request.",
      url: "https://www.anthropic.com/engineering/advanced-tool-use",
      tier: 1,
      sourceName: "Anthropic Engineering: Advanced Tool Use Patterns"
    },
    {
      id: 4,
      text: "To improve tool use reliability, follow these best practices: Use specific, action-oriented names (search_customer_by_email vs search). Write descriptions that include when to use the tool, not just what it does. Leverage JSON Schema features like enum for constrained values. Break complex tools into focused, single-purpose tools.",
      url: "https://composio.dev/tools/claude-ai/function-calling",
      tier: 2,
      sourceName: "Composio: Claude Function Calling Best Practices"
    },
    {
      id: 5,
      text: "Tool design anti-pattern: Creating one 'super tool' with many optional parameters and an action field. This creates ambiguity for the model and increases parameter hallucination. Instead, create separate tools for each distinct action, even if they operate on the same resource.",
      url: "https://www.anthropic.com/engineering/advanced-tool-use#tool-design-patterns",
      tier: 2,
      sourceName: "Anthropic Engineering: Tool Design Patterns"
    },
    {
      id: 6,
      text: "Common tool use issues: Claude calls the wrong tool (fix: make tool descriptions more distinct), Claude hallucinates parameters (fix: use enum and provide examples), Claude doesn't call any tools (fix: ensure descriptions clearly indicate when the tool should be used), Tool results aren't used (fix: verify tool_result blocks are included in conversation history).",
      url: "https://docs.anthropic.com/en/docs/build-with-claude/tool-use#troubleshooting",
      tier: 3,
      sourceName: "Claude API Documentation: Troubleshooting Tool Use"
    },
    {
      id: 7,
      text: "Real-world experience: After adding MCP tools to Claude Desktop, I noticed my context window was filling up before conversations even started. Measuring showed 15,000+ tokens consumed by tool definitions alone. The solution was to audit which tools were actually needed and remove unused ones, plus implement lazy loading for optional tools.",
      url: "https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-desktop",
      tier: 3,
      sourceName: "Developer Blog: Optimizing MCP Tool Context Usage"
    }
  ],
  eval: {
    coverage: {
      score: 0.88,
      explanation: "Excellent — most claims are cited with specific sources"
    },
    authority: {
      score: 0.86,
      explanation: "High (Docs-led with strong vendor guidance)"
    },
    contribution: {
      tierPercentages: {
        1: 43,
        2: 29,
        3: 28
      },
      quality: "Balanced (Docs + implementation + real-world)"
    },
    sufficiency: {
      score: 0.92,
      explanation: "Docs sufficient, enhanced with practical guidance"
    },
    risk: {
      score: 0.87,
      explanation: "Low risk — well-cited with concrete examples"
    },
    needsReview: false,
    overallScore: 0.88
  }
};

// Site and topic data for selectors
export const SITE_DATA = {
  id: "anthropic",
  name: "Anthropic Claude",
  description: "Claude AI API and platform documentation"
};

export const TOPIC_DATA = {
  id: "tool_use",
  name: "Tool Use & Function Calling",
  siteId: "anthropic"
};
