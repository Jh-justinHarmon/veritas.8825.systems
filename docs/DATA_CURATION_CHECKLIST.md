# Veritas Data Curation Checklist — 9 Topics

**Total requirement:** ~70 sources across 3 sites × 3 topics  
**Per topic:** 3-5 Tier 1, 2-3 Tier 2, 2-3 Tier 3

---

## Site 1: Anthropic Claude

### Topic 1: Streaming Responses

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Streaming API reference page
- [ ] Server-Sent Events (SSE) guide
- [ ] Streaming examples in API docs
- [ ] Error handling for streams
- [ ] Streaming parameters documentation

**Tier 2 (Blog) - 2-3 sources:**
- [ ] Anthropic blog: Best practices for streaming
- [ ] Anthropic blog: Real-time AI responses
- [ ] Anthropic research: Streaming architecture

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Common streaming issues
- [ ] Reddit r/ClaudeAI: Streaming implementation tips
- [ ] GitHub issues: Streaming edge cases

### Topic 2: Tool Use / Function Calling

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Tool use API reference
- [ ] Function calling guide
- [ ] Tool schemas documentation
- [ ] Tool execution examples
- [ ] Tool use best practices

**Tier 2 (Blog) - 2-3 sources:**
- [ ] Anthropic blog: Introducing tool use
- [ ] Anthropic blog: Advanced function calling patterns
- [ ] Anthropic research: Tool use capabilities

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Tool use debugging
- [ ] Reddit r/ClaudeAI: Function calling examples
- [ ] GitHub: Tool use implementation patterns

### Topic 3: Rate Limits

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Rate limits documentation
- [ ] API quotas and limits
- [ ] Rate limit headers guide
- [ ] Handling 429 errors
- [ ] Rate limit tiers

**Tier 2 (Blog) - 2-3 sources:**
- [ ] Anthropic blog: Understanding rate limits
- [ ] Anthropic blog: Scaling API usage
- [ ] Anthropic updates: Rate limit changes

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Rate limit strategies
- [ ] Reddit r/ClaudeAI: Rate limit workarounds
- [ ] GitHub: Rate limit handling code

---

## Site 2: LangChain

### Topic 1: RAG / Retrieval Basics

**Tier 1 (Docs) - 3-5 sources:**
- [ ] RAG documentation overview
- [ ] Retrieval chains guide
- [ ] Vector store integration
- [ ] Embedding models setup
- [ ] RAG examples

**Tier 2 (Blog) - 2-3 sources:**
- [ ] LangChain blog: RAG best practices
- [ ] LangChain blog: Retrieval strategies
- [ ] LangChain tutorials: Building RAG systems

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: RAG implementation issues
- [ ] Reddit r/LangChain: RAG tips
- [ ] GitHub discussions: RAG patterns

### Topic 2: Agents vs Chains

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Agents documentation
- [ ] Chains documentation
- [ ] Agent types guide
- [ ] Chain composition
- [ ] When to use agents vs chains

**Tier 2 (Blog) - 2-3 sources:**
- [ ] LangChain blog: Understanding agents
- [ ] LangChain blog: Chain patterns
- [ ] LangChain tutorials: Agent vs chain decision tree

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Agent vs chain use cases
- [ ] Reddit r/LangChain: Agent examples
- [ ] GitHub: Chain composition patterns

### Topic 3: Tools Integration

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Tools documentation
- [ ] Custom tools guide
- [ ] Tool calling in agents
- [ ] Built-in tools reference
- [ ] Tool integration examples

**Tier 2 (Blog) - 2-3 sources:**
- [ ] LangChain blog: Building custom tools
- [ ] LangChain blog: Tool integration patterns
- [ ] LangChain tutorials: Advanced tool use

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Custom tool issues
- [ ] Reddit r/LangChain: Tool integration tips
- [ ] GitHub: Tool implementation examples

---

## Site 3: Stripe

### Topic 1: Webhooks

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Webhooks overview
- [ ] Webhook events reference
- [ ] Webhook signatures guide
- [ ] Testing webhooks
- [ ] Webhook best practices

**Tier 2 (Blog) - 2-3 sources:**
- [ ] Stripe blog: Webhook architecture
- [ ] Stripe blog: Handling webhook failures
- [ ] Stripe engineering: Webhook reliability

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Webhook debugging
- [ ] Reddit r/stripe: Webhook implementation
- [ ] GitHub: Webhook handler examples

### Topic 2: Idempotency

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Idempotency documentation
- [ ] Idempotency keys guide
- [ ] Request idempotency
- [ ] Idempotent API calls
- [ ] Idempotency best practices

**Tier 2 (Blog) - 2-3 sources:**
- [ ] Stripe blog: Understanding idempotency
- [ ] Stripe blog: Preventing duplicate charges
- [ ] Stripe engineering: Idempotency implementation

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Idempotency patterns
- [ ] Reddit r/stripe: Idempotency tips
- [ ] GitHub: Idempotency key handling

### Topic 3: Payment Intents

**Tier 1 (Docs) - 3-5 sources:**
- [ ] Payment Intents API reference
- [ ] Payment Intents guide
- [ ] Payment flow documentation
- [ ] Payment Intent lifecycle
- [ ] Payment Intent examples

**Tier 2 (Blog) - 2-3 sources:**
- [ ] Stripe blog: Payment Intents overview
- [ ] Stripe blog: Migration to Payment Intents
- [ ] Stripe engineering: Payment Intent architecture

**Tier 3 (Community) - 2-3 sources:**
- [ ] Stack Overflow: Payment Intent issues
- [ ] Reddit r/stripe: Payment Intent implementation
- [ ] GitHub: Payment Intent integration examples

---

## Curation Guidelines

### Tier 1 (Official Docs)
**Quality criteria:**
- From official documentation site
- Authoritative and current
- Clear, technical specification
- Code examples preferred

**Format:**
```json
{
  "source_id": "anthropic_streaming_api_ref",
  "source_name": "Streaming API Reference",
  "source_url": "https://docs.anthropic.com/streaming",
  "source_tier": 1,
  "content": "...",
  "metadata": {
    "last_updated": "2024-03-15",
    "section": "API Reference"
  }
}
```

### Tier 2 (Vendor Blog/Research)
**Quality criteria:**
- From vendor's blog, research, or news
- Explains concepts or patterns
- Adds context beyond docs
- Written by vendor team

**Format:**
```json
{
  "source_id": "anthropic_blog_streaming_best_practices",
  "source_name": "Best Practices for Streaming",
  "source_url": "https://anthropic.com/blog/streaming-best-practices",
  "source_tier": 2,
  "content": "...",
  "metadata": {
    "published_date": "2024-02-10",
    "author": "Anthropic Team"
  }
}
```

### Tier 3 (Community)
**Quality criteria:**
- From Stack Overflow, Reddit, GitHub
- Real-world experience
- Practical tips or gotchas
- High upvotes/engagement

**Format:**
```json
{
  "source_id": "stackoverflow_streaming_connection_drops",
  "source_name": "Common Streaming Pitfalls",
  "source_url": "https://stackoverflow.com/questions/...",
  "source_tier": 3,
  "content": "...",
  "metadata": {
    "platform": "Stack Overflow",
    "votes": 42,
    "date": "2024-01-20"
  }
}
```

---

## Progress Tracking

**Anthropic:**
- [ ] Streaming (0/10 sources)
- [ ] Tool Use (0/10 sources)
- [ ] Rate Limits (0/10 sources)

**LangChain:**
- [ ] RAG (0/10 sources)
- [ ] Agents vs Chains (0/10 sources)
- [ ] Tools Integration (0/10 sources)

**Stripe:**
- [ ] Webhooks (0/10 sources)
- [ ] Idempotency (0/10 sources)
- [ ] Payment Intents (0/10 sources)

**Total:** 0/90 sources (target: ~70)

---

## Next Steps

1. **Start with Anthropic Streaming** (most familiar)
2. **Curate Tier 1 first** (foundation)
3. **Add Tier 2 for context** (interpretation)
4. **Add Tier 3 for real-world** (gotchas)
5. **Chunk and embed** (512 tokens)
6. **Test retrieval** (verify tier distribution)

---

**This checklist ensures systematic, high-quality data curation for all 9 topics.**
