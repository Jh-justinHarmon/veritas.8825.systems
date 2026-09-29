# Veritas Public Artifact — Constraint Specification
**Date:** 2026-04-16  
**Purpose:** Expose multi-domain synthesis capability as constrained, undeniable artifact  
**Build Time:** <2 days  
**Status:** Specification complete, ready for implementation

---

## Most Important

- **Core capability:** Multi-domain knowledge synthesis that produces structured insights from technical documentation
- **Single interaction:** User asks question → System returns synthesized concepts with tier-weighted sources (official docs prioritized)

---

## Artifact Definition

### Input → Output

**Input:**
- Single text question (e.g., "How do I implement Claude tool use with error handling?")
- No file uploads
- No multi-turn conversations
- No authentication required

**Output:**
- 3-5 synthesized concepts (structured ideas, not raw retrieval)
- Each concept includes:
  - Title
  - Explanation paragraph
  - Inline citations with tier labels (SPEC/PRACTICE/PITFALL)
  - Source URLs
- Quality metrics visible:
  - Tier diversity (how many tier 1/2/3 sources used)
  - Citation density (citations per paragraph)
  - Source coverage (% of retrieved sources cited)

**Time to value:** <30 seconds (question → synthesized answer)

---

### Interface (What User Sees)

**Single-page web UI:**

```
┌─────────────────────────────────────────────────────────┐
│  Veritas — Multi-Domain Knowledge Synthesis             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Ask a technical question:                             │
│  ┌─────────────────────────────────────────────────┐  │
│  │ How do I implement Claude tool use with error  │  │
│  │ handling?                                       │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  [Synthesize]                                          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 4 Concepts • 3 Tiers • 2.25 Cite/Para • 100%   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Concept 1: Structured Tool Definition               │
│  ────────────────────────────────────────────────────  │
│  Claude requires tools defined with strict JSON       │
│  schema including name, description, and input_schema │
│  [SPEC: Claude API Docs] [PRACTICE: Tool Use Guide]  │
│                                                         │
│  Concept 2: Error Handling Patterns                   │
│  ────────────────────────────────────────────────────  │
│  Implement try-catch blocks around tool execution     │
│  and return structured error responses to Claude      │
│  [PRACTICE: Error Handling] [PITFALL: Silent Fails]  │
│                                                         │
│  [View Sources (8)]                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key elements:**
- Single input field (question)
- Single button (Synthesize)
- Quality metrics bar (tier diversity, citation density, coverage)
- Concept cards (title + paragraph + inline citations)
- Expandable sources sidebar (tier labels, URLs)

**What's NOT shown:**
- No navigation menu
- No user accounts
- No history
- No settings
- No dashboards
- No multi-domain corpus selection (uses demo corpus: Claude + Stripe)

---

## Scope Constraints

### What is NOT Included

**❌ No multi-turn conversations**
- Each question is independent
- No context retention
- No follow-up questions

**❌ No corpus management**
- Fixed demo corpus (Claude Tool Use + Stripe Webhooks)
- No user-uploaded documents
- No corpus selection UI

**❌ No user accounts or authentication**
- Public, anonymous access
- No saved history
- No personalization

**❌ No mode toggle**
- RAW mode only (no abstracted mode)
- Simplifies interface
- Focuses on core capability

**❌ No advanced features**
- No export (PDF, markdown)
- No sharing
- No bookmarking
- No API access

**❌ No analytics or tracking**
- No usage metrics collection
- No user behavior tracking
- Privacy-first (no data retention)

---

## Success Criteria

### What Makes This Undeniable

**1. Quality is immediately visible**
- Tier labels (SPEC/PRACTICE/PITFALL) show source authority
- Citation density metric proves synthesis quality
- Source coverage metric proves comprehensive retrieval

**2. Output is structured, not raw**
- Concepts have titles (not just paragraphs)
- Inline citations (not footnotes)
- Clear hierarchy (concept → explanation → sources)

**3. Multi-domain capability is proven**
- Demo corpus includes 2 domains (Claude + Stripe)
- Single question can synthesize across both
- Tier diversity shows authoritative + practical sources

**4. Time to value is <30 seconds**
- No onboarding required
- No account creation
- Single interaction: question → answer

**5. Technical depth is evident**
- Tier-weighted retrieval (prioritizes official docs)
- Quality metrics (not just "here's an answer")
- Source attribution (every claim is cited)

---

### What a Hiring Manager Immediately Understands

**After 30 seconds:**
> "This person built a system that synthesizes technical documentation across multiple domains, prioritizes authoritative sources, and produces structured insights with quality metrics."

**Not:**
> "This person built a chatbot"

**Not:**
> "This person integrated an LLM API"

**Is:**
> "This person built a knowledge synthesis system with tier-weighted retrieval and measurable quality"

---

## Canonical Demo

### Input (Example Question)

```
How do I implement Claude tool use with error handling?
```

### Output (Example Synthesis)

**Quality Metrics:**
- 4 Concepts
- 3 Tiers (SPEC + PRACTICE + PITFALL)
- 2.25 Citations/Paragraph
- 100% Source Coverage

**Concept 1: Structured Tool Definition**
> Claude requires tools defined with strict JSON schema including name, description, and input_schema. Each tool must specify required parameters and their types. [SPEC: Claude API Documentation] [PRACTICE: Tool Use Implementation Guide]

**Concept 2: Error Handling Patterns**
> Implement try-catch blocks around tool execution and return structured error responses to Claude. Use error codes and descriptive messages to help Claude recover from failures. [PRACTICE: Error Handling Best Practices] [PITFALL: Silent Tool Failures]

**Concept 3: Validation and Retry Logic**
> Validate tool inputs before execution and implement exponential backoff for transient failures. Claude can retry failed tool calls if given clear error signals. [SPEC: Tool Response Format] [PITFALL: Infinite Retry Loops]

**Concept 4: Logging and Observability**
> Log all tool invocations with timestamps, inputs, outputs, and errors for debugging. Structured logs enable pattern detection and failure analysis. [PRACTICE: Production Monitoring] [PITFALL: Missing Context in Errors]

**Sources (8):**
1. [SPEC] Claude API Documentation — Tool Use (platform.claude.com)
2. [SPEC] Tool Response Format Specification (docs.anthropic.com)
3. [PRACTICE] Tool Use Implementation Guide (mindstudio.ai)
4. [PRACTICE] Error Handling Best Practices (scottspence.com)
5. [PRACTICE] Production Monitoring (internal)
6. [PITFALL] Silent Tool Failures (internal)
7. [PITFALL] Infinite Retry Loops (internal)
8. [PITFALL] Missing Context in Errors (internal)

---

## Proof Layer

### What Output Demonstrates Quality

**1. Tier diversity**
- Mix of SPEC (official docs) + PRACTICE (implementation guides) + PITFALL (failure cases)
- Proves multi-tier corpus, not single-source retrieval

**2. Citation density**
- 2+ citations per paragraph
- Proves synthesis, not summarization

**3. Source coverage**
- 100% of retrieved sources cited
- Proves comprehensive synthesis, not cherry-picking

**4. Structured output**
- Concepts have titles
- Clear hierarchy
- Not raw text dump

**5. Cross-domain capability**
- Can answer Claude questions (domain 1)
- Can answer Stripe questions (domain 2)
- Can synthesize across both if question spans domains

---

## Implementation Constraints

### Technical Stack (Existing)

**Frontend:**
- React + TypeScript (already built)
- Tailwind CSS (already styled)
- Deployed on Replit (already operational)

**Backend:**
- FastAPI (already built)
- Qdrant vector DB (already populated with 74 chunks)
- OpenAI API (already integrated)

**Changes Required:**
- Remove mode toggle (RAW only)
- Remove history UI (single interaction only)
- Remove examples dropdown (optional: keep as demo trigger)
- Simplify header (remove navigation)
- Add public URL (veritas.8825.systems or similar)

**Build Time:** <2 days
- Day 1: UI simplification + public deployment
- Day 2: Testing + canonical demo validation

---

## Deployment Specification

### Public Entry Point

**URL:** `veritas.8825.systems` (or `veritas-demo.8825.systems`)

**Hosting:** Replit (already operational)

**Domain:** 8825.systems subdomain (already owned)

**SSL:** Cloudflare (already configured)

---

### Monitoring (Minimal)

**Health check:** `/api/health` (already exists)

**Uptime monitoring:** UptimeRobot or similar (free tier)

**No user tracking:** Privacy-first, no analytics

---

## Start Here

### First Concrete Step

**1. Simplify existing Veritas UI**

**Changes:**
- Remove mode toggle (keep RAW mode only)
- Remove history panel (single interaction)
- Remove navigation menu (single page)
- Keep quality metrics overlay
- Keep sources sidebar
- Keep examples dropdown (optional demo trigger)

**Files to modify:**
- `frontend/src/App.tsx` — Remove mode toggle, history panel
- `frontend/src/components/Header.tsx` — Simplify to title only
- `frontend/src/components/QueryInput.tsx` — Keep as-is
- `frontend/src/components/SynthesisResult.tsx` — Keep as-is
- `frontend/src/components/QualityMetrics.tsx` — Keep as-is

**Estimated time:** 2-4 hours

---

**2. Deploy to public URL**

**Steps:**
- Configure `veritas.8825.systems` subdomain in Cloudflare
- Point to Replit deployment
- Enable SSL
- Test public access

**Estimated time:** 1-2 hours

---

**3. Validate canonical demo**

**Test:**
- Input: "How do I implement Claude tool use with error handling?"
- Expected: 4 concepts, 3 tiers, 2+ cite/para, 100% coverage
- Verify: Quality metrics match expected output

**Estimated time:** 1 hour

---

**4. Create proof artifact**

**Document:**
- Screenshot of canonical demo
- Quality metrics visible
- Sources sidebar expanded
- Save as `VERITAS_PUBLIC_DEMO.png`

**Estimated time:** 30 minutes

---

**Total build time:** <1 day (6-8 hours)

---

## Success Validation

### Artifact is "Undeniable" When:

✅ **Public URL works** — Anyone can access without authentication  
✅ **Single interaction succeeds** — Question → Synthesis in <30 seconds  
✅ **Quality is visible** — Tier labels, citation density, source coverage shown  
✅ **Output is structured** — Concepts have titles, inline citations, clear hierarchy  
✅ **Multi-domain proven** — Can answer Claude questions AND Stripe questions  
✅ **Canonical demo validated** — Example input/output matches expected quality

---

## Anti-Patterns (What NOT to Do)

**❌ Don't add user accounts** — Delays launch, adds complexity  
**❌ Don't add corpus management** — Scope creep into product  
**❌ Don't add multi-turn conversations** — Delays launch, adds state management  
**❌ Don't add export features** — Not core to capability proof  
**❌ Don't add analytics** — Privacy risk, not needed for signal  
**❌ Don't add API access** — Scope creep, not needed for demo  

---

## Summary

**Core capability:** Multi-domain knowledge synthesis with tier-weighted retrieval

**Artifact:** Single-page web UI at `veritas.8825.systems`

**Interaction:** Question → Synthesized concepts (<30 seconds)

**Scope:** Single interaction, no accounts, no history, no corpus management

**Build time:** <1 day (6-8 hours)

**Success:** Public URL + canonical demo + quality metrics visible

---

**Specification Complete:** 2026-04-16  
**Status:** Ready for implementation  
**Next Step:** Simplify UI (remove mode toggle, history, navigation)  
**Architect:** Cascade (8825 System)
