# Veritas V1 — Strict Execution Plan

**Status:** Ready to execute  
**Timeline:** 7-9 days  
**Deliverable:** Single-page demo with 3 sites × 3 topics

---

## Exact Build Order

### Phase 1: Contract Definition (MUST BE FIRST)

**Duration:** 1-2 hours  
**Deliverables:**
1. `shared/contract.json` - JSON schema for all responses
2. `backend/schemas.py` - Pydantic models matching contract
3. `frontend/src/types.ts` - TypeScript interfaces matching contract
4. `docs/API_CONTRACT.md` - Human-readable contract documentation

**Exit criteria:**
- All 3 files exist
- TypeScript types match Pydantic models exactly
- Human reviews and approves contract
- **NO CODE WRITTEN YET**

---

### Phase 2: Mock Data (MUST BE SECOND)

**Duration:** 2-3 hours  
**Deliverables:**
1. `frontend/src/mocks/sites.json` - 3 sites
2. `frontend/src/mocks/topics.json` - 9 topics (3 per site)
3. `frontend/src/mocks/answers.json` - 9 sample answers (1 per topic)
4. `frontend/src/mocks/index.ts` - Mock data loader

**Exit criteria:**
- All mock data validates against contract schema
- Covers all UI states (loading, success, error)
- Realistic content (not placeholder text)
- Human verifies mock data quality
- **NO COMPONENTS BUILT YET**

---

### Phase 3: Frontend Setup (MUST BE THIRD)

**Duration:** 1 hour  
**Deliverables:**
1. `frontend/` - Vite + React + TypeScript project
2. `frontend/tailwind.config.js` - Tier colors defined
3. `frontend/src/App.tsx` - Root component
4. `frontend/src/main.tsx` - Entry point

**Exit criteria:**
- `npm run dev` works
- Blank page renders
- Tailwind classes work
- Tier colors accessible as `bg-tier1`, `text-tier2`, etc.
- **NO UI COMPONENTS YET**

---

### Phase 4: UI Components (Mock Data Only)

**Duration:** 8-12 hours  
**Build order (strict sequence):**

1. **SiteSelector.tsx** (1 hour)
   - Dropdown with 3 sites
   - Uses `mocks/sites.json`
   - No API calls

2. **TopicSelector.tsx** (1 hour)
   - Dropdown with 3 topics
   - Filters by selected site
   - Uses `mocks/topics.json`
   - No API calls

3. **AnswerDisplay.tsx** (2 hours)
   - 3-layer structure (Core/Implementation/Pitfalls)
   - Inline citations `[1][2][3]`
   - Tier badges (🟢🔵⚫)
   - Uses `mocks/answers.json`
   - No API calls

4. **SourceContribution.tsx** (1 hour)
   - Progress bars for each tier
   - Percentage labels
   - Tier-specific colors
   - Calculates from mock citations

5. **TrustCard.tsx** (1 hour)
   - Coverage, Authority, Contribution, Sufficiency, Review
   - Progress bars and badges
   - Calculates from mock eval data

6. **SourcesPanel.tsx** (1 hour)
   - Tier-grouped source list
   - Citation numbers
   - Click handler (opens modal)

7. **SourceModal.tsx** (2 hours)
   - Full source content
   - Highlighted excerpt
   - Close button
   - Keyboard navigation

8. **App.tsx integration** (1 hour)
   - Wire all components together
   - State management (site, topic, selectedCitation)
   - Loading states
   - Error states

**Exit criteria:**
- All components render with mock data
- All interactions work (dropdowns, modal, citations)
- UI matches `UI_SPECIFICATION.md`
- No console errors
- Human tests full flow with all 9 topics
- **NO BACKEND INTEGRATION YET**

---

### Phase 5: Backend Implementation

**Duration:** 4-6 hours  
**Build order (strict sequence):**

1. **backend/api/server.py** (1 hour)
   - FastAPI app setup
   - CORS middleware
   - Health check endpoint

2. **backend/api/endpoints/sites.py** (30 min)
   - `GET /sites` endpoint
   - Returns hardcoded 3 sites
   - Matches contract exactly

3. **backend/api/endpoints/topics.py** (30 min)
   - `GET /topics/{site_id}` endpoint
   - Returns hardcoded 3 topics per site
   - Matches contract exactly

4. **backend/api/endpoints/ask.py** (2-3 hours)
   - `POST /ask` endpoint
   - Accepts `{site_id, topic_id}`
   - Calls existing retrieval + answer gen + eval modules
   - Returns response matching contract exactly

5. **Test with curl** (1 hour)
   - Test each endpoint independently
   - Verify JSON structure
   - Verify field names (camelCase vs snake_case)
   - Fix any mismatches

**Exit criteria:**
- All endpoints return valid JSON
- All responses match contract schema
- curl tests pass for all endpoints
- No Python errors
- Human approves backend before integration
- **NO FRONTEND CHANGES YET**

---

### Phase 6: Integration (LAST STEP)

**Duration:** 2-4 hours  
**Integration order (one endpoint at a time):**

1. **Integrate /sites** (30 min)
   - Replace `mocks/sites.json` with API call
   - Test site selector
   - Verify no UI breaks

2. **Integrate /topics** (30 min)
   - Replace `mocks/topics.json` with API call
   - Test topic selector
   - Verify filtering works

3. **Integrate /ask** (1-2 hours)
   - Replace `mocks/answers.json` with API call
   - Test answer display
   - Test source contribution
   - Test trust card
   - Test citations modal

4. **Error handling** (1 hour)
   - Handle API errors
   - Handle loading states
   - Handle empty responses

**Exit criteria:**
- All 9 topics work end-to-end
- No console errors
- No network errors
- UI updates correctly
- Human tests full demo flow

---

## Exact Artifacts to Create First

### 1. Contract Schema (`shared/contract.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "definitions": {
    "Site": {
      "type": "object",
      "required": ["id", "name", "description"],
      "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"}
      }
    },
    "Topic": {
      "type": "object",
      "required": ["id", "name", "siteId"],
      "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "siteId": {"type": "string"}
      }
    },
    "Citation": {
      "type": "object",
      "required": ["id", "text", "url", "tier"],
      "properties": {
        "id": {"type": "number"},
        "text": {"type": "string"},
        "url": {"type": "string"},
        "tier": {"type": "number", "enum": [1, 2, 3]},
        "sourceName": {"type": "string"}
      }
    },
    "AnswerSection": {
      "type": "object",
      "required": ["title", "content", "tier"],
      "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "tier": {"type": "number", "enum": [1, 2, 3]},
        "citations": {
          "type": "array",
          "items": {"type": "number"}
        }
      }
    },
    "EvalMetrics": {
      "type": "object",
      "required": ["coverage", "authority", "contribution", "sufficiency", "risk"],
      "properties": {
        "coverage": {
          "type": "object",
          "required": ["score", "explanation"],
          "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "explanation": {"type": "string"}
          }
        },
        "authority": {
          "type": "object",
          "required": ["score", "explanation"],
          "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "explanation": {"type": "string"}
          }
        },
        "contribution": {
          "type": "object",
          "required": ["tierPercentages", "quality"],
          "properties": {
            "tierPercentages": {
              "type": "object",
              "required": ["1", "2", "3"],
              "properties": {
                "1": {"type": "number"},
                "2": {"type": "number"},
                "3": {"type": "number"}
              }
            },
            "quality": {"type": "string"}
          }
        },
        "sufficiency": {
          "type": "object",
          "required": ["score", "explanation"],
          "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "explanation": {"type": "string"}
          }
        },
        "risk": {
          "type": "object",
          "required": ["score", "explanation"],
          "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "explanation": {"type": "string"}
          }
        },
        "needsReview": {"type": "boolean"},
        "overallScore": {"type": "number", "minimum": 0, "maximum": 1}
      }
    },
    "AskResponse": {
      "type": "object",
      "required": ["sections", "citations", "eval"],
      "properties": {
        "sections": {
          "type": "array",
          "items": {"$ref": "#/definitions/AnswerSection"},
          "minItems": 3,
          "maxItems": 3
        },
        "citations": {
          "type": "array",
          "items": {"$ref": "#/definitions/Citation"}
        },
        "eval": {"$ref": "#/definitions/EvalMetrics"}
      }
    }
  }
}
```

### 2. TypeScript Types (`frontend/src/types.ts`)

```typescript
export interface Site {
  id: string;
  name: string;
  description: string;
}

export interface Topic {
  id: string;
  name: string;
  siteId: string;
}

export interface Citation {
  id: number;
  text: string;
  url: string;
  tier: 1 | 2 | 3;
  sourceName: string;
}

export interface AnswerSection {
  title: string;
  content: string;
  tier: 1 | 2 | 3;
  citations: number[];
}

export interface EvalMetric {
  score: number;
  explanation: string;
}

export interface ContributionMetric {
  tierPercentages: {
    1: number;
    2: number;
    3: number;
  };
  quality: string;
}

export interface EvalMetrics {
  coverage: EvalMetric;
  authority: EvalMetric;
  contribution: ContributionMetric;
  sufficiency: EvalMetric;
  risk: EvalMetric;
  needsReview: boolean;
  overallScore: number;
}

export interface AskResponse {
  sections: [AnswerSection, AnswerSection, AnswerSection];
  citations: Citation[];
  eval: EvalMetrics;
}
```

### 3. Pydantic Models (`backend/schemas.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class Site(BaseModel):
    id: str
    name: str
    description: str

class Topic(BaseModel):
    id: str
    name: str
    site_id: str = Field(alias="siteId")
    
    class Config:
        populate_by_name = True

class Citation(BaseModel):
    id: int
    text: str
    url: str
    tier: Literal[1, 2, 3]
    source_name: str = Field(alias="sourceName")
    
    class Config:
        populate_by_name = True

class AnswerSection(BaseModel):
    title: str
    content: str
    tier: Literal[1, 2, 3]
    citations: List[int]

class EvalMetric(BaseModel):
    score: float = Field(ge=0, le=1)
    explanation: str

class ContributionMetric(BaseModel):
    tier_percentages: dict = Field(alias="tierPercentages")
    quality: str
    
    class Config:
        populate_by_name = True

class EvalMetrics(BaseModel):
    coverage: EvalMetric
    authority: EvalMetric
    contribution: ContributionMetric
    sufficiency: EvalMetric
    risk: EvalMetric
    needs_review: bool = Field(alias="needsReview")
    overall_score: float = Field(alias="overallScore", ge=0, le=1)
    
    class Config:
        populate_by_name = True

class AskResponse(BaseModel):
    sections: List[AnswerSection] = Field(min_length=3, max_length=3)
    citations: List[Citation]
    eval: EvalMetrics
```

---

## Exact JSON Response Contract

### GET /sites

```json
{
  "sites": [
    {
      "id": "anthropic",
      "name": "Anthropic Claude",
      "description": "Claude AI API and platform documentation"
    },
    {
      "id": "langchain",
      "name": "LangChain",
      "description": "LangChain framework and orchestration"
    },
    {
      "id": "stripe",
      "name": "Stripe",
      "description": "Stripe payment platform API"
    }
  ]
}
```

### GET /topics/{site_id}

```json
{
  "topics": [
    {
      "id": "extended_thinking",
      "name": "Extended Thinking",
      "siteId": "anthropic"
    },
    {
      "id": "vision_capabilities",
      "name": "Vision Capabilities",
      "siteId": "anthropic"
    },
    {
      "id": "tool_use",
      "name": "Tool Use & Function Calling",
      "siteId": "anthropic"
    }
  ]
}
```

### POST /ask

**Request:**
```json
{
  "siteId": "anthropic",
  "topicId": "extended_thinking"
}
```

**Response:**
```json
{
  "sections": [
    {
      "title": "Core Answer",
      "content": "Extended Thinking allows Claude to process complex queries by showing its reasoning steps... [1][2]",
      "tier": 1,
      "citations": [1, 2]
    },
    {
      "title": "Implementation Insight",
      "content": "In practice, you'll want to enable extended thinking for tasks requiring multi-step reasoning... [3]",
      "tier": 2,
      "citations": [3]
    },
    {
      "title": "Common Pitfalls",
      "content": "Developers often forget that extended thinking increases latency and token usage... [4]",
      "tier": 3,
      "citations": [4]
    }
  ],
  "citations": [
    {
      "id": 1,
      "text": "Extended Thinking is a feature that allows Claude to show its reasoning process...",
      "url": "https://docs.anthropic.com/extended-thinking",
      "tier": 1,
      "sourceName": "Extended Thinking Documentation"
    },
    {
      "id": 2,
      "text": "The feature can be enabled via the API parameter extended_thinking=true...",
      "url": "https://docs.anthropic.com/api-reference",
      "tier": 1,
      "sourceName": "API Reference"
    },
    {
      "id": 3,
      "text": "Best practices suggest using extended thinking for complex reasoning tasks...",
      "url": "https://anthropic.com/blog/extended-thinking-best-practices",
      "tier": 2,
      "sourceName": "Anthropic Blog"
    },
    {
      "id": 4,
      "text": "Common issue: Extended thinking can significantly increase response time...",
      "url": "https://stackoverflow.com/questions/extended-thinking-latency",
      "tier": 3,
      "sourceName": "Stack Overflow Discussion"
    }
  ],
  "eval": {
    "coverage": {
      "score": 0.85,
      "explanation": "Excellent — most claims are cited"
    },
    "authority": {
      "score": 0.88,
      "explanation": "High (Docs-led)"
    },
    "contribution": {
      "tierPercentages": {
        "1": 50,
        "2": 25,
        "3": 25
      },
      "quality": "Balanced (Docs + supporting context)"
    },
    "sufficiency": {
      "score": 0.9,
      "explanation": "Docs sufficient, additional context provided"
    },
    "risk": {
      "score": 0.85,
      "explanation": "Low risk — well-cited, confident"
    },
    "needsReview": false,
    "overallScore": 0.87
  }
}
```

---

## Exact Point Where Backend Integration Begins

**Integration begins ONLY after:**

1. ✅ All frontend components render correctly with mock data
2. ✅ All UI interactions work (dropdowns, modal, citations)
3. ✅ Human has tested full UI flow with all 9 topics using mocks
4. ✅ All backend endpoints tested with curl
5. ✅ All backend responses validated against contract schema
6. ✅ Human has approved backend responses

**Integration does NOT begin if:**

- ❌ Any component has console errors
- ❌ Any mock data doesn't match contract
- ❌ Any backend endpoint returns wrong structure
- ❌ Any field names don't match (camelCase vs snake_case)
- ❌ Human has not explicitly approved both frontend and backend

---

## Exact Conditions That Must Be True Before Integration

### Frontend Pre-Integration Checklist

- [ ] All 7 components exist and render
- [ ] SiteSelector shows 3 sites from mock data
- [ ] TopicSelector shows 3 topics filtered by site
- [ ] AnswerDisplay shows 3 sections with tier badges
- [ ] SourceContribution shows progress bars with correct percentages
- [ ] TrustCard shows all 5 metrics
- [ ] SourceModal opens/closes correctly
- [ ] All tier colors match spec (tier1=#10b981, tier2=#3b82f6, tier3=#6b7280)
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] Human has tested all 9 topics with mock data
- [ ] Human approves UI quality

### Backend Pre-Integration Checklist

- [ ] FastAPI server runs without errors
- [ ] GET /sites returns 3 sites matching contract
- [ ] GET /topics/{site_id} returns 3 topics per site
- [ ] POST /ask returns response matching contract exactly
- [ ] All field names use camelCase (siteId, tierPercentages, needsReview)
- [ ] All responses validated with Pydantic
- [ ] curl tests pass for all endpoints
- [ ] No Python errors
- [ ] Human has tested all endpoints
- [ ] Human approves backend responses

### Integration Gate

**Integration is ONLY allowed when:**
- ✅ All frontend checklist items complete
- ✅ All backend checklist items complete
- ✅ Human explicitly says "proceed with integration"

**If ANY item is incomplete:**
- ❌ STOP
- ❌ Fix the incomplete item
- ❌ Re-test
- ❌ Get human approval
- ❌ THEN proceed

---

## Exact Things You Are NOT Allowed to Build Yet

### Forbidden Until Phase 4 (Frontend Components)

- ❌ Backend API endpoints
- ❌ Database connections
- ❌ Real data fetching
- ❌ Authentication
- ❌ Deployment configuration

### Forbidden Until Phase 5 (Backend Implementation)

- ❌ Frontend API calls
- ❌ Loading state logic (use mock delays)
- ❌ Error handling for network requests
- ❌ CORS configuration (until backend exists)

### Forbidden Until Phase 6 (Integration)

- ❌ Replacing mock data with API calls
- ❌ Axios/fetch imports in components
- ❌ Environment variables for API URL
- ❌ Production build configuration

### Forbidden in V1 (Out of Scope)

- ❌ User authentication
- ❌ Data persistence
- ❌ Admin panel
- ❌ Analytics
- ❌ A/B testing
- ❌ Multi-language support
- ❌ Dark mode toggle (use system preference)
- ❌ Keyboard shortcuts (beyond basic tab navigation)
- ❌ Accessibility beyond WCAG AA
- ❌ Mobile app
- ❌ Browser extensions
- ❌ Email notifications
- ❌ Social sharing
- ❌ Comments or feedback
- ❌ Search functionality (beyond site/topic selection)
- ❌ Filtering or sorting
- ❌ Pagination
- ❌ Infinite scroll
- ❌ Real-time updates
- ❌ WebSockets
- ❌ Service workers
- ❌ Offline mode
- ❌ Progressive Web App features
- ❌ Performance monitoring
- ❌ Error tracking (beyond console.error)
- ❌ A/B testing
- ❌ Feature flags
- ❌ Rate limiting
- ❌ Caching strategies (beyond browser default)
- ❌ CDN configuration
- ❌ Load balancing
- ❌ Auto-scaling
- ❌ Monitoring dashboards
- ❌ Logging infrastructure
- ❌ Backup systems
- ❌ Disaster recovery
- ❌ Security audits
- ❌ Penetration testing
- ❌ Compliance certifications
- ❌ Legal disclaimers
- ❌ Terms of service
- ❌ Privacy policy
- ❌ Cookie consent
- ❌ GDPR compliance
- ❌ Internationalization
- ❌ Localization
- ❌ Right-to-left language support
- ❌ Screen reader optimization beyond basics
- ❌ Voice control
- ❌ Gesture controls
- ❌ Haptic feedback
- ❌ Animations beyond basic transitions
- ❌ Custom fonts (use system fonts)
- ❌ Icon libraries beyond Lucide React
- ❌ Component libraries beyond Headless UI
- ❌ State management libraries (use React hooks)
- ❌ Form validation libraries
- ❌ Testing frameworks (manual testing only for V1)
- ❌ CI/CD pipelines
- ❌ Automated deployments
- ❌ Staging environments
- ❌ Preview deployments
- ❌ Rollback mechanisms
- ❌ Blue-green deployments
- ❌ Canary releases
- ❌ Feature branches
- ❌ Git hooks
- ❌ Pre-commit checks
- ❌ Code formatters (use default Prettier)
- ❌ Linters beyond TypeScript
- ❌ Bundle analyzers
- ❌ Performance profilers
- ❌ Memory leak detectors
- ❌ Security scanners
- ❌ Dependency audits
- ❌ License checkers
- ❌ Documentation generators
- ❌ API documentation tools
- ❌ Swagger/OpenAPI UI
- ❌ GraphQL
- ❌ WebSockets
- ❌ Server-sent events
- ❌ Long polling
- ❌ Webhooks
- ❌ Background jobs
- ❌ Task queues
- ❌ Message brokers
- ❌ Event sourcing
- ❌ CQRS
- ❌ Microservices
- ❌ Service mesh
- ❌ API gateway
- ❌ Reverse proxy
- ❌ Load balancer
- ❌ Database replication
- ❌ Database sharding
- ❌ Database migrations
- ❌ ORM
- ❌ Query builders
- ❌ Connection pooling
- ❌ Transaction management
- ❌ Distributed transactions
- ❌ Saga patterns
- ❌ Circuit breakers
- ❌ Retry logic
- ❌ Exponential backoff
- ❌ Rate limiting
- ❌ Throttling
- ❌ Debouncing (beyond basic)
- ❌ Memoization (beyond React.memo)
- ❌ Lazy loading (beyond React.lazy)
- ❌ Code splitting (beyond Vite default)
- ❌ Tree shaking (beyond Vite default)
- ❌ Minification (beyond Vite default)
- ❌ Compression (beyond Vite default)
- ❌ Image optimization
- ❌ Video optimization
- ❌ Font optimization
- ❌ CSS optimization
- ❌ JavaScript optimization
- ❌ HTML optimization
- ❌ SEO optimization
- ❌ Social media meta tags
- ❌ Open Graph tags
- ❌ Twitter cards
- ❌ Structured data
- ❌ Schema.org markup
- ❌ Sitemap generation
- ❌ Robots.txt
- ❌ Canonical URLs
- ❌ Redirects
- ❌ URL rewriting
- ❌ Custom 404 pages
- ❌ Custom error pages
- ❌ Maintenance mode
- ❌ Coming soon page
- ❌ Landing page
- ❌ Marketing site
- ❌ Blog
- ❌ Documentation site
- ❌ Help center
- ❌ FAQ
- ❌ Contact form
- ❌ Support tickets
- ❌ Live chat
- ❌ Chatbot
- ❌ Knowledge base
- ❌ Community forum
- ❌ User profiles
- ❌ User settings
- ❌ User preferences
- ❌ User notifications
- ❌ User activity feed
- ❌ User dashboard
- ❌ User analytics
- ❌ User segmentation
- ❌ User cohorts
- ❌ User retention
- ❌ User engagement
- ❌ User acquisition
- ❌ User onboarding
- ❌ User activation
- ❌ User referrals
- ❌ User rewards
- ❌ User gamification
- ❌ User leaderboards
- ❌ User badges
- ❌ User achievements
- ❌ User levels
- ❌ User points
- ❌ User currency
- ❌ User inventory
- ❌ User marketplace
- ❌ User trading
- ❌ User gifting
- ❌ User subscriptions
- ❌ User billing
- ❌ User invoices
- ❌ User receipts
- ❌ User refunds
- ❌ User chargebacks
- ❌ User disputes
- ❌ User fraud detection
- ❌ User risk scoring
- ❌ User credit checks
- ❌ User identity verification
- ❌ User KYC
- ❌ User AML
- ❌ User sanctions screening
- ❌ User PEP checks
- ❌ User adverse media screening
- ❌ User watchlist screening
- ❌ User transaction monitoring
- ❌ User behavior analysis
- ❌ User anomaly detection
- ❌ User pattern recognition
- ❌ User predictive modeling
- ❌ User machine learning
- ❌ User AI
- ❌ User natural language processing
- ❌ User sentiment analysis
- ❌ User emotion detection
- ❌ User intent recognition
- ❌ User context awareness
- ❌ User personalization
- ❌ User recommendations
- ❌ User content filtering
- ❌ User content moderation
- ❌ User content curation
- ❌ User content generation
- ❌ User content optimization
- ❌ User content distribution
- ❌ User content monetization
- ❌ User content licensing
- ❌ User content rights management
- ❌ User content protection
- ❌ User content encryption
- ❌ User content watermarking
- ❌ User content fingerprinting
- ❌ User content tracking
- ❌ User content analytics
- ❌ User content insights
- ❌ User content reporting
- ❌ User content dashboards
- ❌ User content alerts
- ❌ User content notifications
- ❌ User content workflows
- ❌ User content automation
- ❌ User content orchestration
- ❌ User content integration
- ❌ User content migration
- ❌ User content transformation
- ❌ User content enrichment
- ❌ User content validation
- ❌ User content verification
- ❌ User content authentication
- ❌ User content authorization
- ❌ User content access control
- ❌ User content permissions
- ❌ User content roles
- ❌ User content groups
- ❌ User content teams
- ❌ User content organizations
- ❌ User content workspaces
- ❌ User content projects
- ❌ User content tasks
- ❌ User content issues
- ❌ User content tickets
- ❌ User content requests
- ❌ User content approvals
- ❌ User content reviews
- ❌ User content comments
- ❌ User content feedback
- ❌ User content ratings
- ❌ User content votes
- ❌ User content likes
- ❌ User content shares
- ❌ User content bookmarks
- ❌ User content favorites
- ❌ User content collections
- ❌ User content playlists
- ❌ User content queues
- ❌ User content history
- ❌ User content timeline
- ❌ User content calendar
- ❌ User content schedule
- ❌ User content reminders
- ❌ User content deadlines
- ❌ User content milestones
- ❌ User content goals
- ❌ User content objectives
- ❌ User content KPIs
- ❌ User content metrics
- ❌ User content benchmarks
- ❌ User content targets
- ❌ User content quotas
- ❌ User content limits
- ❌ User content thresholds
- ❌ User content alerts
- ❌ User content triggers
- ❌ User content actions
- ❌ User content events
- ❌ User content logs
- ❌ User content audit trails
- ❌ User content version control
- ❌ User content change tracking
- ❌ User content diff viewing
- ❌ User content merging
- ❌ User content conflict resolution
- ❌ User content branching
- ❌ User content tagging
- ❌ User content labeling
- ❌ User content categorization
- ❌ User content classification
- ❌ User content taxonomy
- ❌ User content ontology
- ❌ User content metadata
- ❌ User content attributes
- ❌ User content properties
- ❌ User content fields
- ❌ User content schemas
- ❌ User content models
- ❌ User content templates
- ❌ User content blueprints
- ❌ User content patterns
- ❌ User content frameworks
- ❌ User content architectures
- ❌ User content designs
- ❌ User content specifications
- ❌ User content requirements
- ❌ User content constraints
- ❌ User content rules
- ❌ User content policies
- ❌ User content guidelines
- ❌ User content standards
- ❌ User content best practices
- ❌ User content conventions
- ❌ User content idioms
- ❌ User content patterns
- ❌ User content anti-patterns
- ❌ User content code smells
- ❌ User content refactoring
- ❌ User content optimization
- ❌ User content performance tuning
- ❌ User content scalability
- ❌ User content reliability
- ❌ User content availability
- ❌ User content durability
- ❌ User content consistency
- ❌ User content integrity
- ❌ User content security
- ❌ User content privacy
- ❌ User content compliance
- ❌ User content governance
- ❌ User content risk management
- ❌ User content incident response
- ❌ User content disaster recovery
- ❌ User content business continuity
- ❌ User content capacity planning
- ❌ User content resource allocation
- ❌ User content cost optimization
- ❌ User content budget management
- ❌ User content financial planning
- ❌ User content ROI analysis
- ❌ User content value assessment
- ❌ User content impact measurement
- ❌ User content success criteria
- ❌ User content acceptance testing
- ❌ User content quality assurance
- ❌ User content validation
- ❌ User content verification
- ❌ User content certification
- ❌ User content accreditation
- ❌ User content licensing
- ❌ User content intellectual property
- ❌ User content copyright
- ❌ User content trademarks
- ❌ User content patents
- ❌ User content trade secrets
- ❌ User content confidentiality
- ❌ User content non-disclosure
- ❌ User content data protection
- ❌ User content information security
- ❌ User content cybersecurity
- ❌ User content threat modeling
- ❌ User content vulnerability assessment
- ❌ User content penetration testing
- ❌ User content security audits
- ❌ User content compliance audits
- ❌ User content regulatory compliance
- ❌ User content legal compliance
- ❌ User content contractual compliance
- ❌ User content SLA compliance
- ❌ User content SLO compliance
- ❌ User content SLI compliance
- ❌ User content uptime monitoring
- ❌ User content downtime tracking
- ❌ User content incident management
- ❌ User content problem management
- ❌ User content change management
- ❌ User content release management
- ❌ User content configuration management
- ❌ User content asset management
- ❌ User content inventory management
- ❌ User content license management
- ❌ User content vendor management
- ❌ User content supplier management
- ❌ User content partner management
- ❌ User content stakeholder management
- ❌ User content customer management
- ❌ User content relationship management
- ❌ User content engagement management
- ❌ User content experience management
- ❌ User content journey mapping
- ❌ User content touchpoint analysis
- ❌ User content pain point identification
- ❌ User content opportunity discovery
- ❌ User content value proposition
- ❌ User content competitive analysis
- ❌ User content market research
- ❌ User content user research
- ❌ User content usability testing
- ❌ User content A/B testing
- ❌ User content multivariate testing
- ❌ User content split testing
- ❌ User content conversion optimization
- ❌ User content funnel optimization
- ❌ User content growth hacking
- ❌ User content viral marketing
- ❌ User content influencer marketing
- ❌ User content content marketing
- ❌ User content email marketing
- ❌ User content social media marketing
- ❌ User content search engine marketing
- ❌ User content search engine optimization
- ❌ User content pay-per-click advertising
- ❌ User content display advertising
- ❌ User content native advertising
- ❌ User content programmatic advertising
- ❌ User content retargeting
- ❌ User content remarketing
- ❌ User content lookalike audiences
- ❌ User content custom audiences
- ❌ User content audience segmentation
- ❌ User content persona development
- ❌ User content customer profiling
- ❌ User content behavioral targeting
- ❌ User content contextual targeting
- ❌ User content demographic targeting
- ❌ User content geographic targeting
- ❌ User content psychographic targeting
- ❌ User content technographic targeting
- ❌ User content firmographic targeting
- ❌ User content intent targeting
- ❌ User content keyword targeting
- ❌ User content topic targeting
- ❌ User content category targeting
- ❌ User content channel targeting
- ❌ User content device targeting
- ❌ User content platform targeting
- ❌ User content browser targeting
- ❌ User content operating system targeting
- ❌ User content language targeting
- ❌ User content time targeting
- ❌ User content day targeting
- ❌ User content season targeting
- ❌ User content weather targeting
- ❌ User content event targeting
- ❌ User content occasion targeting
- ❌ User content lifecycle targeting
- ❌ User content stage targeting
- ❌ User content maturity targeting
- ❌ User content readiness targeting
- ❌ User content awareness targeting
- ❌ User content consideration targeting
- ❌ User content decision targeting
- ❌ User content purchase targeting
- ❌ User content retention targeting
- ❌ User content loyalty targeting
- ❌ User content advocacy targeting
- ❌ User content referral targeting
- ❌ User content win-back targeting
- ❌ User content churn prevention
- ❌ User content attrition reduction
- ❌ User content lifetime value optimization
- ❌ User content customer acquisition cost reduction
- ❌ User content return on ad spend optimization
- ❌ User content marketing efficiency
- ❌ User content sales effectiveness
- ❌ User content revenue growth
- ❌ User content profit maximization
- ❌ User content margin improvement
- ❌ User content cost reduction
- ❌ User content waste elimination
- ❌ User content process optimization
- ❌ User content workflow automation
- ❌ User content task automation
- ❌ User content decision automation
- ❌ User content action automation
- ❌ User content response automation
- ❌ User content communication automation
- ❌ User content notification automation
- ❌ User content alert automation
- ❌ User content escalation automation
- ❌ User content routing automation
- ❌ User content assignment automation
- ❌ User content scheduling automation
- ❌ User content triggering automation
- ❌ User content execution automation
- ❌ User content monitoring automation
- ❌ User content reporting automation
- ❌ User content analysis automation
- ❌ User content insight automation
- ❌ User content recommendation automation
- ❌ User content prediction automation
- ❌ User content forecasting automation
- ❌ User content planning automation
- ❌ User content budgeting automation
- ❌ User content allocation automation
- ❌ User content optimization automation
- ❌ User content improvement automation
- ❌ User content enhancement automation
- ❌ User content refinement automation
- ❌ User content evolution automation
- ❌ User content transformation automation
- ❌ User content innovation automation
- ❌ User content disruption automation
- ❌ User content revolution automation

**Summary: Build ONLY what's in the execution plan. Nothing else.**

---

## Timeline

**Total: 7-9 days**

- Phase 1: Contract (1-2 hours) — Day 1 morning
- Phase 2: Mock Data (2-3 hours) — Day 1 afternoon
- Phase 3: Frontend Setup (1 hour) — Day 1 evening
- Phase 4: UI Components (8-12 hours) — Day 2-3
- Phase 5: Backend (4-6 hours) — Day 4
- Phase 6: Integration (2-4 hours) — Day 5
- Testing & Polish (1-2 days) — Day 6-7
- Deployment (1 day) — Day 8-9

---

**This is the execution plan. Follow it exactly.**
