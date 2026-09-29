# Claude Tool Use Demo Corpus - Summary

**Created**: 2026-04-10  
**Subject**: Claude Tool Use & Function Calling  
**Demo Question**: "My Claude agent keeps calling the wrong tools or inventing parameters. How do I fix tool use errors?"

---

## Corpus Overview

**Total Sources**: 7  
**Tier Distribution**:
- Tier 1 (Official Docs): 3 sources
- Tier 2 (Implementation Guides): 2 sources  
- Tier 3 (Common Pitfalls): 2 sources

**Tier Separation Quality**: ⭐⭐⭐⭐⭐ (5/5)  
**Implementation Gap**: Strong  
**Demo Strength**: **Highest** - Best first demo candidate

---

## Source Breakdown

### Tier 1: Official Documentation (Authority 1.0)

#### 1. Tool use overview - Claude API Docs
- **URL**: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview`
- **Role**: Core answer foundation - how tool use works
- **Key Extractions**:
  - Client-side vs server-side tools
  - Tool execution flow: define → Claude decides → tool_use blocks → execute → tool_result → final response
  - Agent capabilities: tools improve benchmark performance
  - Pricing: based on input/output tokens, additional charges for server-side tools

#### 2. Advanced tool use - Anthropic Engineering Blog
- **URL**: `https://www.anthropic.com/engineering/advanced-tool-use`
- **Role**: Advanced features and optimization patterns
- **Key Extractions**:
  - **Tool Search Tool**: Discovers tools on-demand, reduces token overhead
  - **Token overhead problem**: Loading many tool definitions consumes thousands of tokens per request
  - **Programmatic Tool Calling**: Dynamic tool execution based on runtime conditions
  - **Best practices**: Combine Tool Search Tool with Programmatic Tool Calling

#### 3. Troubleshooting tool use - Claude API Docs
- **URL**: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/troubleshooting-tool-use`
- **Role**: Official troubleshooting guide for common errors
- **Key Extractions**:
  - **Claude calls wrong tool**: Ambiguous tool definitions, use specific names/descriptions
  - **Claude invents parameters**: Unclear schema, add examples and enum constraints
  - **Parallel tool calls**: Dependencies between tools cause failures
  - **Caching issues**: Modified tool definitions may serve stale cache

---

### Tier 2: Implementation Guides (Authority 0.7)

#### 4. Claude Function Calling and Tool Use Guide - Composio
- **URL**: `https://composio.dev/content/claude-function-calling-tools`
- **Role**: Implementation guide with code examples and best practices
- **Key Extractions**:
  - **Tool definition structure**: name (unique ID), description (critical for selection), input_schema (JSON schema)
  - **Best practices**:
    - Clear, specific tool names describing the action
    - Detailed descriptions explaining WHEN to use the tool
    - Strict input schemas with required fields, types, examples
    - Validate inputs before execution, return clear errors
  - **Example**: Calculator app with add/subtract/multiply/divide tools
  - **Error handling**: Claude may generate syntactically valid but semantically incorrect parameters

#### 5. MCP Server Token Overhead - MindStudio Blog
- **URL**: `https://www.mindstudio.ai/blog/claude-code-mcp-server-token-overhead`
- **Role**: Real-world token overhead analysis and optimization
- **Key Extractions**:
  - **Problem**: Each MCP server loads tool definitions into EVERY message
  - **Typical overhead**: 3-4 servers = 18,000 tokens per turn = 14% of 128k context window
  - **Breakdown**: filesystem (4,200), fetch (3,800), memory (2,100), brave-search (7,900) = 18,000 total
  - **Impact**: Reduces available context, increases costs, causes context window exhaustion
  - **Optimization strategies**:
    - Remove unused MCP servers
    - Use project-level configurations
    - Trim tool descriptions
    - Consolidate similar tools
    - Use Tool Search Tool for large libraries
  - **Measurement**: Check 'Input tokens' in API responses, baseline with no servers

---

### Tier 3: Common Pitfalls (Authority 0.4)

#### 6. Optimising MCP Server Context Usage - Scott Spence
- **URL**: `https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code`
- **Role**: Real developer experience with MCP overhead optimization
- **Key Extractions**:
  - **Problem discovery**: "I noticed my Claude Code conversations were consuming massive amounts of tokens before I even started"
  - **Before state**: 20 tools loaded, 14,247 tokens consumed before any conversation
  - **Optimization process**:
    - Identified which tools actually used (only 5 out of 20)
    - Removed unused MCP servers
    - Trimmed verbose descriptions
    - Consolidated related tools
  - **After state**: 8 tools loaded, 4,892 tokens consumed
  - **Result**: **66% reduction** (from 14,247 to 4,892 tokens)
  - **Key insight**: "Most developers don't realize MCP tools are loaded into EVERY message. It's not a one-time cost - it's per-turn overhead. A 100-turn conversation with 14k overhead = 1.4M tokens just for tool definitions."
  - **Developer quote**: "I had no idea I was paying for tool definitions on every message. Removing unused servers cut my token usage by two-thirds."

#### 7. Claude Code Skills Common Mistakes - MindStudio Blog
- **URL**: `https://www.mindstudio.ai/blog/claude-code-skills-common-mistakes-guide`
- **Role**: Common mistakes and anti-patterns in tool design
- **Key Extractions**:
  - **Mistake #1**: Installing too many skills without understanding overhead
    - **Symptom**: Claude runs out of context mid-conversation, becomes slow
  - **Mistake #2**: Using default tool definitions without customization
    - **Symptom**: Wrong tool selection, generic descriptions lead to confusion
  - **Mistake #3**: Cramming everything into one massive tool
    - **Symptom**: Makes tool selection harder, increases error rates
  - **Best practice**: Create focused, well-defined tools with clear boundaries
  - **Symptom of wrong tool**: "If Claude consistently calls the wrong tool, the issue is usually ambiguous tool descriptions or overlapping functionality"

---

## 3-Layer Answer Structure

### Core Answer (Tier 1)
Claude tool use follows a request-response cycle:
1. Define tools with `name`, `description`, `input_schema`
2. Claude decides which tool(s) to use
3. Claude generates `tool_use` blocks
4. You execute and return `tool_result` blocks
5. Claude uses results for final response

**Common errors**:
- **Claude calls wrong tool** = ambiguous tool definitions, use specific names/descriptions
- **Claude invents parameters** = unclear schema, add examples and enum constraints
- **Parallel tool call issues** = dependencies between tools

**Advanced**: Tool Search Tool reduces token overhead by discovering tools on-demand instead of loading all definitions upfront.

### Implementation Insight (Tier 2)
**Tool definition structure**: 
- `name` (unique ID)
- `description` (critical for tool selection - Claude uses this to decide WHEN to call)
- `input_schema` (JSON schema with types/constraints)

**Best practices**:
1. Clear, specific tool names describing the action
2. Detailed descriptions explaining WHEN to use the tool
3. Strict schemas with required fields, types, examples
4. Validate inputs before execution, return clear errors

**Token overhead problem**: Each MCP server loads tool definitions into EVERY message.
- Typical setup: 3-4 servers = 18,000 tokens per turn = 14% of 128k context window
- **Optimization**: Remove unused servers, use project-level configs, trim descriptions, consolidate similar tools, use Tool Search Tool for large libraries
- **Measurement**: Check 'Input tokens' in API responses

### Common Pitfalls (Tier 3)

**PITFALL #1: MCP Server Token Overhead** (66% reduction possible)
- **Symptom**: 14,000+ tokens consumed before conversation starts, context window exhaustion, high costs
- **Root cause**: MCP tools loaded into EVERY message, not one-time cost
  - 100-turn conversation with 14k overhead = 1.4M tokens just for tool definitions
- **Real example**: 
  - Before: 20 tools = 14,247 tokens per turn
  - After optimization: 8 tools = 4,892 tokens per turn
  - **66% reduction**
- **Fix**:
  1. Audit which tools actually used
  2. Remove unused MCP servers
  3. Trim verbose descriptions
  4. Consolidate related tools
- **Developer quote**: "I had no idea I was paying for tool definitions on every message."

**PITFALL #2: Ambiguous Tool Definitions**
- **Symptom**: Claude calls wrong tool consistently, invents parameters
- **Root cause**:
  1. Vague descriptions - Claude can't distinguish similar tools
  2. Generic names - no clear purpose
  3. Cramming everything into one tool - makes selection harder
- **Fix**:
  1. Make tool purposes distinct
  2. Use specific descriptions explaining WHEN to use
  3. Create focused, single-purpose tools
  4. Add examples to parameter descriptions

**PITFALL #3: Installing Too Many Skills**
- **Symptom**: Claude runs out of context mid-conversation, becomes slow
- **Root cause**: Each skill adds overhead without understanding cumulative impact
- **Fix**: Monitor context usage, remove unused tools, organize by domain/workflow

---

## Demo Validation

### Tier Separation Quality: ⭐⭐⭐⭐⭐ (5/5)
- **Tier 1** explains mechanics (how tool use works, execution flow)
- **Tier 2** explains implementation patterns (tool structure, token overhead problem)
- **Tier 3** exposes systematic failures (MCP overhead with concrete numbers, ambiguous definitions, too many skills)

**Excellent progression**: "how it works" → "how to implement well" → "why it fails in practice"

### Implementation Gap: Strong
- MCP token overhead **not obvious** from official docs (per-turn cost vs one-time)
- Ambiguous tool definition failures require real-world experience to understand
- 66% reduction metric shows massive optimization opportunity

### Demo Strength: **Highest** - Best First Demo Candidate
- **MCP overhead has concrete numbers**: 14k→4.9k tokens = 66% reduction
- **Wrong tool selection is universal**: Every API integration faces tool design challenges
- **Clear before/after story**: 20 tools → 8 tools, 14,247 tokens → 4,892 tokens
- **Compelling "aha" moment**: "I had no idea I was paying for tool definitions on every message"

### Coverage Completeness: Complete
Covers:
- ✅ What tool use is (execution flow, client vs server-side)
- ✅ How to implement well (tool structure, best practices)
- ✅ Systematic failure modes (overhead + wrong selection + parameter hallucination)
- ✅ Concrete optimization strategies (remove, trim, consolidate)

---

## Comparison with Other Subjects

| Subject | Tier Quality | Demo Strength | Implementation Gap | Recommendation |
|---------|--------------|---------------|-------------------|----------------|
| **Claude Tool Use** | ⭐⭐⭐⭐⭐ | **Highest** | Strong | **✅ BEST FIRST DEMO** |
| Stripe Webhooks | ⭐⭐⭐⭐⭐ | Very High | Strong | ✅ Excellent 2nd demo |
| Claude Vision | ⭐⭐⭐⭐ | Medium-High | Moderate | Good 3rd demo |
| Claude Extended Thinking | ⭐⭐⭐ | Medium | Weak | Skip for now |

**Why Tool Use is best**:
1. **Universal problem**: Every developer building with LLM APIs faces tool design
2. **Concrete metrics**: 66% token reduction, 14k→4.9k overhead
3. **Systematic failures**: Not edge cases - fundamental design issues
4. **Clear value prop**: Veritas shows you what docs don't - the hidden per-turn cost

---

## Next Steps

1. **Test corpus with sample query** - validate 3-layer answer synthesis
2. **Compare with Stripe Webhooks** - prove multi-domain capability
3. **Build demo UI** - show tier separation visually
4. **Validate value proposition**: "Not just docs, but why your implementation is expensive"

---

## Files Created

- `claude_tool_use_demo.json` - Complete corpus with extracted content and tier metadata
- `CLAUDE_TOOL_USE_SUMMARY.md` - This summary document

**Corpus Location**: `/Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin Harmon/AI_SYSTEMS/8825-modules/Veritas/corpus/`
