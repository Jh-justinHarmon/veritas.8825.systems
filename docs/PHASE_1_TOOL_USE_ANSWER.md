# Phase 1: Tool Use & Function Calling — 3-Layer Answer

**Demo Question:** "I defined tools for Claude but it keeps calling the wrong one or hallucinating parameters. What am I doing wrong?"

---

## Core Answer (Tier 1: Specification)

Tool use in Claude works through an agentic loop where the model decides which tools to call, generates the parameters, and then processes the results. When you define a tool, you're providing Claude with a JSON schema that describes the tool's name, description, and input parameters. The model uses this schema to understand what each tool does and when to use it.

The key components of a tool definition are: a clear, specific name that indicates the tool's purpose; a detailed description that explains what the tool does and when to use it; and an input schema that specifies each parameter's type, description, and whether it's required. Claude reads these definitions at the start of each conversation and uses them to decide which tool to call based on the user's request.

When Claude decides to use a tool, it returns a `tool_use` content block with the tool name and the input parameters it generated. Your application then executes the tool with those parameters and returns the result in a `tool_result` block. Claude processes this result and continues the conversation, potentially calling more tools or providing a final answer.

The most common reason tools fail is vague or ambiguous descriptions. If your tool description doesn't clearly explain what the tool does and when to use it, Claude may call the wrong tool or skip calling tools entirely. Similarly, if parameter descriptions are missing or unclear, Claude may hallucinate parameter values or use incorrect types.

---

## Implementation Insight (Tier 2: Best Practices)

In practice, the quality of your tool definitions directly determines how reliably Claude uses them. The most effective tool definitions follow several key patterns that aren't obvious from the API documentation alone.

First, use specific, action-oriented tool names. Instead of `search`, use `search_customer_database` or `search_product_catalog`. The name should make it immediately clear what the tool does and what domain it operates in. This helps Claude distinguish between similar tools and reduces wrong tool selection.

Second, write tool descriptions as if you're explaining to a junior developer when to use the tool. Include concrete examples of situations where the tool is appropriate. For instance, instead of "Searches for users," write "Searches for users by email, username, or user ID. Use this when you need to look up a specific user's information or verify if a user exists in the system."

Third, be explicit about parameter constraints using JSON Schema features. If a parameter only accepts specific values, use an `enum` to list them. If there's a format requirement (like email or date), specify it in the description. If parameters have dependencies (like "if you provide X, you must also provide Y"), document that clearly in the description.

Fourth, break complex operations into focused, single-purpose tools rather than creating one multi-purpose tool. A tool that tries to do too many things will have a complex parameter schema that's hard for Claude to use correctly. It's better to have `create_user`, `update_user`, and `delete_user` as separate tools than one `manage_user` tool with a `action` parameter.

Finally, when you have many tools (more than 10-15), consider using tool choice strategies. You can use `tool_choice: auto` to let Claude decide, `tool_choice: any` to force a tool call, or `tool_choice: {type: "tool", name: "specific_tool"}` to force a specific tool. For complex workflows, you might even implement a "tool search tool" pattern where Claude first calls a meta-tool to discover which tools are relevant before making the actual tool calls.

---

## Common Pitfalls (Tier 3: Real-World Friction)

The most frustrating issue developers encounter is Claude calling the wrong tool when multiple tools seem similar. This happens because the model is making a decision based on semantic similarity between the user's request and your tool descriptions. If you have `get_user` and `search_users` tools, and both descriptions mention "finding users," Claude might pick the wrong one. The fix is to make the distinction explicit in the descriptions: "Use get_user when you have a specific user ID. Use search_users when you need to find users matching criteria like name or email."

Parameter hallucination is the second major pain point. Claude will confidently generate parameter values that seem plausible but don't actually exist in your system. For example, if you have a `status` parameter but don't specify the valid values, Claude might use "pending" when your system only accepts "active" or "inactive." This fails silently in the API call, and Claude receives an error it has to recover from. The solution is to always use `enum` for parameters with fixed values and provide examples in the description for parameters with specific formats.

Context window bloat becomes a problem when you define too many tools or tools with very large schemas. Each tool definition consumes tokens from your context window before the conversation even starts. If you define 20 tools with detailed schemas, you might use 5,000-10,000 tokens just on tool definitions. This leaves less room for conversation history and can slow down responses. The fix is to only include tools that are relevant to the current conversation, or use a two-stage approach where you first determine which category of tools is needed, then load only those tools.

Another common issue is tools that return too much data. If your tool returns a 50KB JSON response, Claude has to process all of that in its context window. This can cause the model to miss important details or run out of context space. The solution is to have your tools return only the essential information, or implement pagination where Claude can request more details if needed.

Finally, developers often forget that Claude doesn't have memory of previous tool calls across conversation turns unless you explicitly include that information. If Claude calls a tool to get a user ID, then you start a new message, Claude won't remember that user ID unless it's in the conversation history. This can lead to Claude calling the same tool repeatedly. The fix is to ensure tool results are included in the conversation history and that Claude's responses reference the information it retrieved.

---

## Source Attribution

**Core Answer sources:**
- [1] Claude API Documentation: Tool Use Overview
- [2] Claude API Documentation: Defining Tools
- [3] Anthropic Engineering Blog: Advanced Tool Use

**Implementation Insight sources:**
- [4] Composio Guide: Claude Function Calling Best Practices
- [5] Anthropic Engineering Blog: Tool Search Tool Pattern

**Common Pitfalls sources:**
- [6] Claude API Documentation: Troubleshooting Tool Use
- [7] Developer Experience: Context Window Optimization with MCP Tools

---

## Next Step

Convert this plain English answer into structured JSON with:
- 3 sections (Core Answer, Implementation Insight, Common Pitfalls)
- 7 citations mapped to specific sentences
- Tier metadata (1, 2, 3)
- Trust card values (coverage, authority, contribution, sufficiency, risk)
