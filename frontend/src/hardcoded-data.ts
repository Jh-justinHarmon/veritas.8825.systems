// Phase 1: Hardcoded Ground Truth for Tool Use & Function Calling
// This is the perfect example that defines what Veritas should look and feel like

export const HARDCODED_RESPONSE = {
  sections: [
    {
      title: "Core Answer",
      content: "Tool use in Claude works through an agentic loop where the model decides which tools to call, generates the parameters, and then processes the results. When you define a tool, you're providing Claude with a JSON schema that describes the tool's name, description, and input parameters [1][2]. The model uses this schema to understand what each tool does and when to use it.\n\nThe key components of a tool definition are: a clear, specific name that indicates the tool's purpose; a detailed description that explains what the tool does and when to use it; and an input schema that specifies each parameter's type, description, and whether it's required [2]. Claude reads these definitions at the start of each conversation and uses them to decide which tool to call based on the user's request.\n\nWhen Claude decides to use a tool, it returns a tool_use content block with the tool name and the input parameters it generated [1]. Your application then executes the tool with those parameters and returns the result in a tool_result block. Claude processes this result and continues the conversation, potentially calling more tools or providing a final answer.\n\nThe most common reason tools fail is vague or ambiguous descriptions [6]. If your tool description doesn't clearly explain what the tool does and when to use it, Claude may call the wrong tool or skip calling tools entirely. Similarly, if parameter descriptions are missing or unclear, Claude may hallucinate parameter values or use incorrect types.",
      tier: 1,
      citations: [1, 2, 6]
    },
    {
      title: "Implementation Insight",
      content: "In practice, the quality of your tool definitions directly determines how reliably Claude uses them. The most effective tool definitions follow several key patterns that aren't obvious from the API documentation alone [4].\n\nFirst, use specific, action-oriented tool names. Instead of 'search', use 'search_customer_database' or 'search_product_catalog' [4]. The name should make it immediately clear what the tool does and what domain it operates in. This helps Claude distinguish between similar tools and reduces wrong tool selection.\n\nSecond, write tool descriptions as if you're explaining to a junior developer when to use the tool [4]. Include concrete examples of situations where the tool is appropriate. For instance, instead of 'Searches for users,' write 'Searches for users by email, username, or user ID. Use this when you need to look up a specific user's information or verify if a user exists in the system.'\n\nThird, be explicit about parameter constraints using JSON Schema features [2][4]. If a parameter only accepts specific values, use an enum to list them. If there's a format requirement (like email or date), specify it in the description. If parameters have dependencies, document that clearly.\n\nFinally, break complex operations into focused, single-purpose tools rather than creating one multi-purpose tool [3][5]. A tool that tries to do too many things will have a complex parameter schema that's hard for Claude to use correctly. It's better to have create_user, update_user, and delete_user as separate tools than one manage_user tool with an action parameter.",
      tier: 2,
      citations: [2, 3, 4, 5]
    },
    {
      title: "Common Pitfalls",
      content: "The most frustrating issue developers encounter is Claude calling the wrong tool when multiple tools seem similar [6]. This happens because the model is making a decision based on semantic similarity between the user's request and your tool descriptions. If you have get_user and search_users tools, and both descriptions mention 'finding users,' Claude might pick the wrong one. The fix is to make the distinction explicit in the descriptions: 'Use get_user when you have a specific user ID. Use search_users when you need to find users matching criteria like name or email.'\n\nParameter hallucination is the second major pain point [6]. Claude will confidently generate parameter values that seem plausible but don't actually exist in your system. For example, if you have a status parameter but don't specify the valid values, Claude might use 'pending' when your system only accepts 'active' or 'inactive.' This fails silently in the API call, and Claude receives an error it has to recover from. The solution is to always use enum for parameters with fixed values and provide examples in the description for parameters with specific formats.\n\nContext window bloat becomes a problem when you define too many tools or tools with very large schemas [3][7]. Each tool definition consumes tokens from your context window before the conversation even starts. If you define 20 tools with detailed schemas, you might use 5,000-10,000 tokens just on tool definitions. This leaves less room for conversation history and can slow down responses. The fix is to only include tools that are relevant to the current conversation, or use a two-stage approach where you first determine which category of tools is needed, then load only those tools.\n\nFinally, developers often forget that Claude doesn't have memory of previous tool calls across conversation turns unless you explicitly include that information [6]. If Claude calls a tool to get a user ID, then you start a new message, Claude won't remember that user ID unless it's in the conversation history. This can lead to Claude calling the same tool repeatedly. The fix is to ensure tool results are included in the conversation history and that Claude's responses reference the information it retrieved.",
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
