# Veritas V1 — Simplified Execution Protocol

**Status:** Active  
**Date:** 2026-04-07  
**Approach:** Hardcode first, formalize later

---

## Core Insight (From External Review)

**The full execution plan was correct about the risk (schema drift) but over-engineered for V1 speed.**

**Key realization:**
> "You are not building the system yet — you are proving the demo."

**Therefore:** Build for **one undeniable experience** first, then generalize.

---

## Simplified 5-Phase Protocol

### Phase 1: Hardcode the Truth (No Schema Yet)

**Duration:** 1-2 hours  
**Deliverable:** One perfect example response

**What to create:**
- Write the final 3-layer answer manually for **Anthropic Extended Thinking**
- Define exact contribution percentages
- Define exact trust card values
- Define exact citations (4-5 sources)

**This is your ground truth.**

**Exit criteria:**
- One complete JSON object that represents the perfect answer
- Human reviews and says "this is exactly what I want to see"
- **No schema files yet**
- **No generalization yet**

---

### Phase 2: UI Only (Mock Inline)

**Duration:** 6-8 hours  
**Deliverable:** Working UI with hardcoded data

**What to create:**
- React components with **hardcoded JSON inside the component**
- No external mock files
- No API calls
- No schema files

**Components:**
1. Site selector (hardcoded to "Anthropic")
2. Topic selector (hardcoded to "Extended Thinking")
3. 3-layer answer display
4. Source contribution bar
5. Trust card
6. Citations modal

**Exit criteria:**
- UI renders perfectly with hardcoded data
- All interactions work
- Human says "this feels like a real product"
- **No backend yet**

---

### Phase 3: Extract Contract (Formalize After UI Feels Right)

**Duration:** 1-2 hours  
**Deliverable:** TypeScript interface based on working UI

**What to create:**
- Extract hardcoded JSON into `types.ts`
- Simple interfaces (no Pydantic yet)
- Document the shape that works

**This is your real contract based on reality, not speculation.**

**Exit criteria:**
- TypeScript types match the hardcoded data exactly
- No changes to UI needed
- Contract is just documentation of what already works

---

### Phase 4: Backend (Match, Don't Design)

**Duration:** 2-3 hours  
**Deliverable:** One endpoint returning exact same shape

**What to create:**
- `POST /ask` endpoint
- Returns **exact same JSON** as hardcoded data
- No creativity, no redesign
- Wire up existing retrieval + answer gen + eval modules

**Exit criteria:**
- curl test returns identical JSON to hardcoded data
- Field names match exactly
- Structure matches exactly
- **No frontend changes yet**

---

### Phase 5: Integration (Trivial Swap)

**Duration:** 30 minutes  
**Deliverable:** UI connected to backend

**What to change:**
```javascript
// Before
const data = hardcodedData;

// After
const data = await fetch('/ask', {
  method: 'POST',
  body: JSON.stringify({ siteId: 'anthropic', topicId: 'extended_thinking' })
}).then(r => r.json());
```

**Exit criteria:**
- UI works identically with API
- No visual changes
- No errors

---

## What This Avoids

**From the full protocol:**
- ❌ Premature schema design
- ❌ Over-generalization (9 topics upfront)
- ❌ Multi-phase gates
- ❌ Building for cases that don't exist yet

**Why this is better:**
- ✅ Proves one experience is undeniable
- ✅ Contract emerges from reality, not speculation
- ✅ Faster iteration
- ✅ Less rework when requirements change

---

## What This Keeps (Critical)

**From the full protocol:**
- ✅ Schema drift awareness
- ✅ Contract must become explicit (but later)
- ✅ No integration until UI is stable
- ✅ One endpoint at a time

**These rules still apply.**

---

## The One Topic to Start With

**Anthropic Extended Thinking**

**Why this one:**
- Strong tier 2 coverage (official Anthropic blog)
- Clear 3-layer structure:
  - Core: What it is (docs)
  - Implementation: How to use it (blog)
  - Pitfalls: Latency/cost issues (community)
- Good citation diversity

---

## Exact First Artifact

**File:** `frontend/src/App.tsx` (or wherever you start)

**Hardcoded data structure:**

```typescript
const HARDCODED_RESPONSE = {
  sections: [
    {
      title: "Core Answer",
      content: "Extended Thinking allows Claude to process complex queries by showing its reasoning steps. The feature can be enabled via the API parameter extended_thinking=true... [1][2]",
      tier: 1,
      citations: [1, 2]
    },
    {
      title: "Implementation Insight",
      content: "In practice, you'll want to enable extended thinking for tasks requiring multi-step reasoning, such as code debugging or complex analysis... [3]",
      tier: 2,
      citations: [3]
    },
    {
      title: "Common Pitfalls",
      content: "Developers often forget that extended thinking increases latency and token usage significantly. Plan for 2-3x longer response times... [4]",
      tier: 3,
      citations: [4]
    }
  ],
  citations: [
    {
      id: 1,
      text: "Extended Thinking is a feature that allows Claude to show its reasoning process before providing an answer...",
      url: "https://docs.anthropic.com/extended-thinking",
      tier: 1,
      sourceName: "Extended Thinking Documentation"
    },
    {
      id: 2,
      text: "The feature can be enabled via the API parameter extended_thinking=true in your request...",
      url: "https://docs.anthropic.com/api-reference",
      tier: 1,
      sourceName: "API Reference"
    },
    {
      id: 3,
      text: "Best practices suggest using extended thinking for complex reasoning tasks where showing the thought process adds value...",
      url: "https://anthropic.com/blog/extended-thinking-best-practices",
      tier: 2,
      sourceName: "Anthropic Blog: Extended Thinking Best Practices"
    },
    {
      id: 4,
      text: "Common issue: Extended thinking can significantly increase response time (2-3x) and token usage. Budget accordingly...",
      url: "https://stackoverflow.com/questions/claude-extended-thinking-latency",
      tier: 3,
      sourceName: "Stack Overflow: Extended Thinking Performance"
    }
  ],
  eval: {
    coverage: {
      score: 0.85,
      explanation: "Excellent — most claims are cited"
    },
    authority: {
      score: 0.88,
      explanation: "High (Docs-led)"
    },
    contribution: {
      tierPercentages: { 1: 50, 2: 25, 3: 25 },
      quality: "Balanced (Docs + supporting context)"
    },
    sufficiency: {
      score: 0.9,
      explanation: "Docs sufficient, additional context provided"
    },
    risk: {
      score: 0.85,
      explanation: "Low risk — well-cited, confident"
    },
    needsReview: false,
    overallScore: 0.87
  }
};
```

**This is the ground truth. Build the UI to display this perfectly.**

---

## When to Generalize

**After Phase 5 works:**
- Add second topic (Vision Capabilities)
- Extract common patterns
- Create proper mock data files
- Add site/topic switching logic

**But not before.**

---

## Timeline (Simplified)

**Total: 3-4 days for first working demo**

- Phase 1: Hardcode truth (1-2 hours) — Day 1 morning
- Phase 2: UI with inline data (6-8 hours) — Day 1-2
- Phase 3: Extract contract (1-2 hours) — Day 2
- Phase 4: Backend (2-3 hours) — Day 3
- Phase 5: Integration (30 min) — Day 3
- Polish (1 day) — Day 4

**Then add remaining 8 topics:** 2-3 days

**Total to full demo:** 5-7 days (faster than original 7-9)

---

## Key Rules (Non-Negotiable)

1. **Start with one perfect example**
2. **Hardcode in component, not external file**
3. **UI must feel right before formalizing contract**
4. **Backend matches UI, not the other way around**
5. **Integration is last, not concurrent**

---

## What Success Looks Like

**After Phase 2:**
- Human can interact with UI
- It feels like a real product
- All interactions work
- Data is hardcoded but nobody would know

**After Phase 5:**
- Same UI, same experience
- Data comes from backend
- No visual difference
- Ready to add more topics

---

**This is the simplified protocol. Optimized for V1 speed while keeping schema drift discipline.**
