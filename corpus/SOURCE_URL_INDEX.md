# Veritas Demo Corpus - Complete Source URL Index

**Last Updated**: 2026-04-10  
**Total Corpora**: 4 (Claude Tool Use, Stripe Webhooks, Claude Vision, Claude Extended Thinking)  
**Total Sources**: 26 URLs across all subjects

---

## Claude Tool Use & Function Calling

**Demo Question**: "My Claude agent keeps calling the wrong tools or inventing parameters. How do I fix tool use errors?"

### Tier 1: Official Documentation (3 sources)
1. **Tool use overview - Claude API Docs**
   - URL: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
   - Role: Core answer foundation - how tool use works
   - Topics: Client-side vs server-side tools, execution flow, pricing

2. **Advanced tool use - Anthropic Engineering Blog**
   - URL: https://www.anthropic.com/engineering/advanced-tool-use
   - Role: Advanced features and optimization patterns
   - Topics: Tool Search Tool, Programmatic Tool Calling, token overhead reduction

3. **Troubleshooting tool use - Claude API Docs**
   - URL: https://platform.claude.com/docs/en/agents-and-tools/tool-use/troubleshooting-tool-use
   - Role: Official troubleshooting guide
   - Topics: Wrong tool selection, parameter hallucination, parallel tool calls, caching

### Tier 2: Implementation Guides (2 sources)
4. **Claude Function Calling and Tool Use Guide - Composio**
   - URL: https://composio.dev/content/claude-function-calling-tools
   - Role: Implementation guide with code examples
   - Topics: Tool definition structure, best practices, error handling

5. **MCP Server Token Overhead - MindStudio Blog**
   - URL: https://www.mindstudio.ai/blog/claude-code-mcp-server-token-overhead
   - Role: Real-world token overhead analysis
   - Topics: MCP overhead (18k tokens/turn), optimization strategies, measurement

### Tier 3: Common Pitfalls (2 sources)
6. **Optimising MCP Server Context Usage - Scott Spence**
   - URL: https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code
   - Role: Real developer experience with optimization
   - Topics: 66% reduction (14,247→4,892 tokens), before/after metrics

7. **Claude Code Skills Common Mistakes - MindStudio Blog**
   - URL: https://www.mindstudio.ai/blog/claude-code-skills-common-mistakes-guide
   - Role: Common mistakes and anti-patterns
   - Topics: Too many skills, ambiguous definitions, cramming functionality

---

## Stripe Webhooks Integration

**Demo Question**: "I set up Stripe webhooks but signature verification keeps failing. What am I doing wrong?"

### Tier 1: Official Documentation (3 sources)
1. **Receive Stripe events in your webhook endpoint**
   - URL: https://docs.stripe.com/webhooks
   - Role: Core answer foundation - webhook mechanics
   - Topics: Event-driven architecture, endpoint requirements, signature verification, best practices

2. **Set up and deploy a webhook - Quickstart**
   - URL: https://docs.stripe.com/webhooks/quickstart
   - Role: Step-by-step implementation guide
   - Topics: Setup workflow, Stripe CLI testing, endpoint registration

3. **Resolve webhook signature verification errors**
   - URL: https://docs.stripe.com/webhooks/signature
   - Role: Official troubleshooting for signature failures
   - Topics: Verification parameters, common errors, secret management, test vs live mode

### Tier 2: Implementation Guides (2 sources)
4. **Stripe Webhooks Implementation Guide - Hooklistener**
   - URL: https://www.hooklistener.com/learn/stripe-webhooks-implementation
   - Role: Comprehensive implementation best practices
   - Topics: Signature mechanics (HMAC-SHA256), testing strategies, production patterns

5. **Stripe Webhooks - ngrok documentation**
   - URL: https://ngrok.com/docs/integrations/webhooks/stripe-webhooks
   - Role: Local development testing workflow
   - Topics: Tunnel setup, pre-production testing

### Tier 3: Common Pitfalls (2 sources)
6. **Debugging Stripe Webhook Signature Verification Errors in Production**
   - URL: https://dev.to/nerdincode/debugging-stripe-webhook-signature-verification-errors-in-production-1h7c
   - Role: Real production failure - test vs live mode mismatch
   - Topics: Test mode secret in production (90% of failures), environment config

7. **bodyParser middleware conflict - GitHub Issue #734**
   - URL: https://github.com/stripe/stripe-node/issues/734
   - Role: Express.js raw body access problem
   - Topics: bodyParser.raw() vs bodyParser.json() conflict, req.rawBody workaround

---

## Claude Vision Capabilities

**Demo Question**: "I'm using Claude Vision but getting poor quality results and hallucinations. What am I doing wrong?"

### Tier 1: Official Documentation (3 sources)
1. **Vision - Claude API Docs**
   - URL: https://platform.claude.com/docs/en/build-with-claude/vision
   - Role: Core answer foundation - vision capabilities and API usage
   - Topics: Multimodal capabilities, image input methods, supported formats, limitations

2. **Best practices for using vision with Claude**
   - URL: https://platform.claude.com/cookbook/multimodal-best-practices-for-vision
   - Role: Official best practices and prompt engineering
   - Topics: Hallucination mitigation, role assignment, counting fixes

3. **Claude Vision for Document Analysis - Developer's Guide**
   - URL: https://getstream.io/blog/anthropic-claude-visual-reasoning/
   - Role: Comprehensive implementation guide
   - Topics: Document analysis, prompt engineering for visual tasks, output structure

### Tier 2: Implementation Guides (2 sources)
4. **Claude Vision (Image Recognition) Guide - Claude Lab**
   - URL: https://claudelab.net/en/articles/claude-ai/vision-guide
   - Role: Comprehensive implementation guide
   - Topics: Image placement strategy, token optimization, cost calculation, troubleshooting

5. **Claude Vision: Analyzing Images, Charts & Visual Documents**
   - URL: https://learn-prompting.fr/blog/claude-vision-guide
   - Role: Best practices for quality and cost optimization
   - Topics: Quality optimization, cost optimization, format selection, resolution guidelines

### Tier 3: Common Pitfalls (2 sources)
6. **Claude Vision Black Pixels Edge Case and Fix**
   - URL: https://medium.com/cyberark-engineering/beware-of-llm-vision-hallucinations-a657fa15d340
   - Role: Real production failure - black pixel hallucination
   - Topics: 99.99997% black pixels treated as tiny image, preprocessing solution

7. **Best practices for using vision - Hallucination Example**
   - URL: https://platform.claude.com/cookbook/multimodal-best-practices-for-vision
   - Role: Real hallucination example and fix
   - Topics: Counting hallucinations (9 dogs → 10), role assignment + step-by-step reasoning fix

---

## Claude Extended Thinking

**Demo Question**: "When should I use Claude's extended thinking mode and how do I optimize the thinking budget?"

### Tier 1: Official Documentation (3 sources)
1. **Building with extended thinking - Claude API Docs**
   - URL: https://platform.claude.com/docs/en/build-with-claude/extended-thinking
   - Role: Core answer foundation - what extended thinking is
   - Topics: Thinking budget, API usage, feature compatibility, performance considerations

2. **Extended thinking tips - Claude API Docs**
   - URL: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/extended-thinking-tips
   - Role: Official prompting best practices
   - Topics: Adaptive vs extended thinking, budget management, use case selection

3. **Claude's extended thinking - Anthropic News**
   - URL: https://www.anthropic.com/news/visible-extended-thinking
   - Role: Product announcement and use case explanation
   - Topics: Visible thinking, performance benchmarks, safety considerations

### Tier 2: Implementation Guides (2 sources)
4. **Extended thinking - Amazon Bedrock**
   - URL: https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html
   - Role: AWS implementation guide with best practices
   - Topics: Task selection, budget optimization, context handling, performance tradeoffs

5. **Using extended thinking - Claude Help Center**
   - URL: https://support.claude.com/en/articles/10574485-using-extended-thinking
   - Role: User-facing guide on when to use
   - Topics: Use case selection, when NOT to use, tips for effective use

### Tier 3: Common Pitfalls (1 source)
6. **When should I use web search, extended thinking, and Research?**
   - URL: https://support.claude.com/en/articles/11095361-when-should-i-use-web-search-extended-thinking-and-research
   - Role: Feature comparison and selection guidance
   - Topics: Extended thinking vs other features, combining features, cost considerations

---

## URL Statistics by Site

### Claude API / Anthropic
- **Total URLs**: 13
- **Tier 1**: 9 (official docs + engineering blog)
- **Tier 2**: 2 (AWS docs, Help Center)
- **Tier 3**: 2 (Help Center, cookbook examples)

### Stripe
- **Total URLs**: 7
- **Tier 1**: 3 (official docs)
- **Tier 2**: 2 (Hooklistener, ngrok)
- **Tier 3**: 2 (DEV Community, GitHub)

### Third-Party Sources
- **Total URLs**: 6
- Composio, MindStudio (2), Scott Spence, Claude Lab, Learnia, GetStream, CyberArk Medium, Hooklistener, ngrok, DEV Community, GitHub

---

## URL Verification Status

All URLs were successfully retrieved and content extracted during corpus building (2026-04-09 to 2026-04-10).

**Access Issues Encountered**:
- `https://stackoverflow.com/questions/77973781/stripe-webhook-cannot-access-express-request-raw-body` - Forbidden (replaced with GitHub issue)
- `https://hookvm.com/integrations/stripe` - EOF error (replaced with alternative)

**All other URLs**: ✅ Successfully retrieved and processed

---

## Usage Notes

### For Demo Building
- Use Tier 1 URLs for "Core Answer" layer
- Use Tier 2 URLs for "Implementation Insight" layer
- Use Tier 3 URLs for "Common Pitfalls" layer

### For Source Attribution
- All sources include full URL in JSON corpus files
- URLs are preserved in `url` field of each source object
- Tier and authority metadata included for filtering

### For Content Updates
- Re-fetch URLs periodically to check for doc updates
- Official docs (Tier 1) most stable
- Community content (Tier 3) may become stale or deleted

---

## Related Files

- **Corpus Files**: `claude_tool_use_demo.json`, `stripe_webhooks_demo.json`, `claude_vision_demo.json`, `claude_extended_thinking_demo.json`
- **Summary Files**: `CLAUDE_TOOL_USE_SUMMARY.md`, `STRIPE_WEBHOOKS_SUMMARY.md`
- **This Index**: `SOURCE_URL_INDEX.md`

**Corpus Location**: `/Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin Harmon/AI_SYSTEMS/8825-modules/Veritas/corpus/`
