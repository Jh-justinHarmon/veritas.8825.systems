# Phase 2: Component Structure & Layout

**Goal:** Build UI that makes the 3-layer answer feel like a real product

---

## Exact 7 Components

### 1. **App.tsx** (Root Container)
**Responsibility:** 
- Overall layout and state management
- Holds selected site, topic, and citation modal state
- Renders all child components in correct order

**State:**
```typescript
const [selectedSite, setSelectedSite] = useState(SITE_DATA);
const [selectedTopic, setSelectedTopic] = useState(TOPIC_DATA);
const [selectedCitation, setSelectedCitation] = useState<number | null>(null);
```

**Layout order:**
1. Header with site/topic selectors
2. AnswerDisplay (3 layers)
3. SourceContribution (bar chart)
4. TrustCard (metrics)
5. SourcesPanel (grouped citations)
6. SourceModal (conditional)

---

### 2. **SiteSelector.tsx**
**Responsibility:**
- Display current site (Anthropic Claude)
- For V1: hardcoded, no dropdown (just display)
- Future: dropdown with 3 sites

**Props:**
```typescript
interface SiteSelectorProps {
  site: { id: string; name: string; description: string };
}
```

**Visual:**
- Small badge or label
- Site name + icon
- Subtle, not prominent

---

### 3. **TopicSelector.tsx**
**Responsibility:**
- Display current topic (Tool Use & Function Calling)
- For V1: hardcoded, no dropdown (just display)
- Future: dropdown with 3 topics per site

**Props:**
```typescript
interface TopicSelectorProps {
  topic: { id: string; name: string; siteId: string };
}
```

**Visual:**
- Larger than site selector
- Topic name as heading
- Clear, prominent

---

### 4. **AnswerDisplay.tsx** (Most Important)
**Responsibility:**
- Render 3 sections (Core/Implementation/Pitfalls)
- Each section has title, content, tier badge
- Inline citations are clickable
- **Pitfalls section is visually distinct**

**Props:**
```typescript
interface AnswerDisplayProps {
  sections: Array<{
    title: string;
    content: string;
    tier: 1 | 2 | 3;
    citations: number[];
  }>;
  onCitationClick: (citationId: number) => void;
}
```

**Visual:**
- 3 sections stacked vertically
- Each section has:
  - Title with tier badge (🟢 Tier 1, 🔵 Tier 2, ⚫ Tier 3)
  - Content with inline citations `[1][2]`
  - Citations are clickable buttons
- **Pitfalls section:**
  - Slightly darker background (bg-gray-50)
  - Subtle border or callout
  - Bold text for anchor lines (already in content)
  - Tighter spacing

---

### 5. **SourceContribution.tsx**
**Responsibility:**
- Show tier contribution percentages as horizontal bars
- Visual representation of source mix

**Props:**
```typescript
interface SourceContributionProps {
  tierPercentages: {
    1: number;
    2: number;
    3: number;
  };
}
```

**Visual:**
- 3 horizontal progress bars
- Each bar: tier color, percentage label
- Tier 1: #10b981 (green)
- Tier 2: #3b82f6 (blue)
- Tier 3: #6b7280 (gray)
- Labels: "Docs 43%", "Blog 29%", "Community 28%"

---

### 6. **TrustCard.tsx**
**Responsibility:**
- Display 5 eval metrics
- Show overall score and review flag

**Props:**
```typescript
interface TrustCardProps {
  eval: {
    coverage: { score: number; explanation: string };
    authority: { score: number; explanation: string };
    contribution: { tierPercentages: object; quality: string };
    sufficiency: { score: number; explanation: string };
    risk: { score: number; explanation: string };
    needsReview: boolean;
    overallScore: number;
  };
}
```

**Visual:**
- Card with border
- 5 metrics, each with:
  - Label
  - Score (0-1 as percentage or High/Low)
  - Brief explanation
- Overall score at bottom
- Review flag if needed (🟢 Looks good / 🟡 Needs review)

---

### 7. **SourceModal.tsx**
**Responsibility:**
- Show full citation details when user clicks citation
- Display source name, URL, tier, excerpt

**Props:**
```typescript
interface SourceModalProps {
  citation: {
    id: number;
    text: string;
    url: string;
    tier: 1 | 2 | 3;
    sourceName: string;
  } | null;
  onClose: () => void;
}
```

**Visual:**
- Modal overlay (dark background)
- Modal content (white card, centered)
- Close button (X in top right)
- Citation details:
  - Source name (heading)
  - Tier badge
  - Excerpt text
  - URL link
- Keyboard support (Esc to close)

---

## Layout Sketch

```
┌─────────────────────────────────────────┐
│ Header                                   │
│ ┌─────────┐  ┌──────────────────────┐  │
│ │ Site    │  │ Topic                │  │
│ └─────────┘  └──────────────────────┘  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Answer Display                           │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Core Answer 🟢 Tier 1              │  │
│ │ Content with citations [1][2]...   │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Implementation Insight 🔵 Tier 2   │  │
│ │ Content with citations [3][4]...   │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Common Pitfalls ⚫ Tier 3          │  │
│ │ [VISUALLY DISTINCT - darker bg]    │  │
│ │ Content with bold anchors...       │  │
│ └────────────────────────────────────┘  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Source Contribution                      │
│ Docs        ████████░░ 43%              │
│ Blog        █████░░░░░ 29%              │
│ Community   █████░░░░░ 28%              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Trust Card                               │
│ Coverage:     88% ████████░░            │
│ Authority:    High (Docs-led)           │
│ Contribution: Balanced                  │
│ Sufficiency:  92% █████████░            │
│ Risk:         87% (Low)                 │
│ ─────────────────────────────────       │
│ Overall: 88%  🟢 Looks good             │
└─────────────────────────────────────────┘

[SourceModal appears on citation click]
```

---

## Component Build Order (Sequential)

1. **App.tsx** - Basic structure, no content yet
2. **SiteSelector.tsx** - Simple display component
3. **TopicSelector.tsx** - Simple display component
4. **AnswerDisplay.tsx** - Core component, most complex
5. **SourceContribution.tsx** - Progress bars
6. **TrustCard.tsx** - Metrics display
7. **SourceModal.tsx** - Modal overlay

---

## Key UI Decisions

### Pitfalls Section Visual Distinction
- Background: `bg-gray-900/50` (slightly different dark surface, not light)
- Border: `border-l-4 border-gray-700` (muted left accent)
- Padding: `p-6` (tighter than other sections)
- Typography: Stronger weight for anchor lines (font-semibold or font-bold)
- Note: Distinct without looking like a pasted light card in dark UI

### Citation Click Behavior
- Inline citations `[1]` are `<button>` elements
- Click opens SourceModal with that citation
- Modal has dark overlay, centered card
- Esc key or X button closes modal

### Tier Colors (Defined in tailwind.config.js)
```javascript
colors: {
  tier1: '#10b981',  // green
  tier2: '#3b82f6',  // blue
  tier3: '#6b7280',  // gray
}
```

### Order (Critical)
1. Answer (human, useful)
2. Source Contribution (transparency)
3. Trust Card (metrics)

**Not:** Metrics first (feels analytical, not human)

---

## Next Step

Begin building components in order, starting with:
1. Set up Vite + React + TailwindCSS
2. Configure tier colors
3. Build App.tsx structure
4. Build each component sequentially

**Timeline:** 6-8 hours
