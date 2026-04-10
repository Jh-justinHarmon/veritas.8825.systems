# Claude Tool Use: Common Failure Cases and Debugging

## Source Information
- **Type:** Failure Analysis / Debugging Guide
- **Author:** Developer Community
- **Context:** Documented failures and solutions from production systems

---

## The "Wrong Tool" Problem

One of the most frequently reported issues is Claude calling the wrong tool when multiple similar tools are available. This typically happens when tool descriptions are too similar or too vague.

**Failure case:** A developer implemented `get_user_profile` and `get_user_settings` tools with descriptions like "Gets user information" and "Gets user data". Claude would randomly choose between them because the descriptions didn't clearly differentiate their purposes.

**Root cause:** Ambiguous tool descriptions that don't specify the exact use case or data returned.

**Solution:** Rewrite descriptions to be extremely specific about when each tool should be used. For example: "Gets user profile information including name, email, and avatar URL. Use this when you need to display user identity information" vs "Gets user preference settings including theme, language, and notification preferences. Use this when you need to know how the user has configured their experience."

## Parameter Hallucination

Claude sometimes generates parameters that don't exist in the schema or uses incorrect types. This is particularly common with complex nested objects or when parameter names are ambiguous.

**Failure case:** A tool schema defined a parameter `user_id` (string), but Claude would sometimes generate `userId` (camelCase) or `id` (shortened). The tool would fail because the parameter name didn't match.

**Root cause:** Parameter naming inconsistency across the API or unclear parameter descriptions.

**Solution:** Use consistent naming conventions across all tools (either snake_case or camelCase, never mixed). Add explicit examples in the parameter description showing the exact format expected.

## Tool Result Ignored

Developers report cases where Claude calls a tool, receives the result, but then doesn't use the information in its response. This creates a poor user experience where Claude appears to ignore the data it just retrieved.

**Failure case:** Claude called a `search_documentation` tool, received relevant results, but then responded with "I don't have information about that" without referencing the search results.

**Root cause:** Tool result format didn't match Claude's expectations, or the result was too verbose/unstructured for Claude to parse effectively.

**Solution:** Return tool results in a structured, concise format. Use clear labels and avoid returning raw JSON dumps. If the result is large, summarize key points at the top of the result.

## Infinite Tool Call Loops

In some cases, Claude enters a loop where it repeatedly calls the same tool with the same parameters, never making progress toward answering the user's question.

**Failure case:** A `get_weather` tool was called 5 times in a row with the same city parameter, each time receiving the same result, but Claude kept calling it again.

**Root cause:** The tool result didn't signal completion clearly, or Claude misinterpreted the result as an error requiring retry.

**Solution:** Implement loop detection in your application layer. After 2-3 identical tool calls, intervene with a system message explaining that the tool has already been called and provide the cached result.

## Permission Errors Not Handled

When Claude attempts to use a tool that requires permissions the user hasn't granted, the error handling often fails to guide Claude toward a solution.

**Failure case:** Claude tried to call a `read_file` tool, received a permission error, and then simply told the user "I can't access that file" without explaining how to grant permission.

**Root cause:** Error messages from the tool were too technical or didn't include actionable guidance.

**Solution:** Return error messages that include both the problem and the solution. For example: "Permission denied: Claude doesn't have access to read files in this directory. To grant permission, go to Settings > Permissions and enable file access for Claude."

## Schema Validation Failures

Complex tool schemas with nested objects or strict validation rules can cause Claude to generate invalid parameters that fail schema validation.

**Failure case:** A tool required a parameter with format `{"action": "create", "data": {...}}`, but Claude would sometimes generate `{"action": "create", "payload": {...}}`, failing validation.

**Root cause:** Schema was too complex or parameter names weren't intuitive.

**Solution:** Simplify schemas to use flat parameter structures when possible. If nesting is required, provide explicit examples in the schema description showing the exact structure expected.

## Token Limit Exceeded

When working with large tool results or many tools, Claude can hit token limits, causing truncation or failure to complete responses.

**Failure case:** A `search_codebase` tool returned 50KB of code snippets. Claude hit the token limit mid-response and the answer was cut off.

**Root cause:** Tool results were too large relative to the available context window.

**Solution:** Implement result pagination or summarization. Return a summary of results with an option to "get more details" via a follow-up tool call. Never return more than 2-3KB of data in a single tool result.
