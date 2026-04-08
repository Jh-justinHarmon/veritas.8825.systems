# Veritas UI Specification — Source Contribution & Trust Signals

**Version:** 2.0 Refined  
**Date:** 2026-04-07  
**Focus:** Visual source contribution + multi-source trust card

---

## Design Principles

1. **Instant comprehension** - User understands in <2 seconds
2. **Source visibility** - Always show what came from where
3. **No jargon** - Plain language, clear labels
4. **Visual hierarchy** - Answer → Contribution → Trust

---

## Component 1: Answer Display (3-Layer Structure)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Core Answer] 🟢 Docs-backed                            │
│                                                          │
│ Streaming returns tokens incrementally using            │
│ Server-Sent Events (SSE). The API sends delta events    │
│ as tokens are generated... [1][2]                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ [Implementation Insight] 🔵 In practice                 │
│                                                          │
│ In practice, you'll want to buffer partial responses    │
│ and handle incomplete JSON objects until the stream     │
│ completes... [3]                                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ [Common Pitfalls] ⚫ Common issues                      │
│                                                          │
│ Developers often forget to handle connection drops      │
│ mid-stream, which can leave the UI in an inconsistent   │
│ state... [4]                                            │
└─────────────────────────────────────────────────────────┘
```

### Visual Styling

**Section headers:**
- Font: 14px, semi-bold
- Color: Tier-specific (green/blue/gray)
- Icon: Tier badge (🟢/🔵/⚫)
- Tag: Light background pill

**Section content:**
- Font: 16px, regular
- Line height: 1.6
- Padding: 16px
- Border-left: 3px solid tier-color

**Citations:**
- Inline: `[1]` as clickable pill
- Hover: Show source tier icon
- Click: Open source modal

### Color Palette

```css
--tier-1-color: #10b981;  /* Green - Docs */
--tier-2-color: #3b82f6;  /* Blue - Blog */
--tier-3-color: #6b7280;  /* Gray - Community */

--tier-1-bg: #d1fae5;
--tier-2-bg: #dbeafe;
--tier-3-bg: #e5e7eb;
```

---

## Component 2: Source Contribution Bar

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ Source Contribution                                      │
│                                                          │
│ Docs        ██████████████░░░░░░ 70%                    │
│ Blog        ████░░░░░░░░░░░░░░░░ 20%                    │
│ Community   ██░░░░░░░░░░░░░░░░░░ 10%                    │
└─────────────────────────────────────────────────────────┘
```

### Visual Styling

**Container:**
- Background: Light gray (#f9fafb)
- Border: 1px solid #e5e7eb
- Border-radius: 8px
- Padding: 16px
- Margin-top: 24px

**Title:**
- Font: 14px, semi-bold
- Color: #374151
- Margin-bottom: 12px

**Progress bars:**
- Height: 24px
- Border-radius: 4px
- Background: Tier-specific color
- Unfilled: #e5e7eb
- Label: Inside bar if >30%, outside if <30%

**Labels:**
- Font: 13px, medium
- Color: White (inside bar) or #374151 (outside)
- Percentage: Right-aligned, 13px, semi-bold

### Interaction

**Hover on bar:**
- Tooltip: "X chunks from [tier name]"
- Example: "7 chunks from official documentation"

**Click on bar:**
- Filter sources panel to show only that tier

---

## Component 3: Trust Card (Multi-Source Aware)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ Trust Signal                                             │
│                                                          │
│ Coverage     ████████░░ 82%                             │
│ Authority    High (Docs-led)                            │
│ Contribution Balanced (Docs + supporting context)       │
│ Sufficiency  ✅ Docs sufficient                         │
│ Review       🟢 Looks good                              │
└─────────────────────────────────────────────────────────┘
```

### Visual Styling

**Container:**
- Background: White
- Border: 1px solid #e5e7eb
- Border-radius: 8px
- Padding: 20px
- Box-shadow: 0 1px 3px rgba(0,0,0,0.1)

**Title:**
- Font: 16px, bold
- Color: #111827
- Margin-bottom: 16px

**Metrics:**
- Each row: 8px margin-bottom
- Label: 13px, medium, #6b7280
- Value: 14px, semi-bold, tier-specific color

**Coverage bar:**
- Same style as source contribution
- Color: Gradient green → yellow → red based on %

**Authority label:**
- "High" = Green
- "Medium" = Yellow
- "Low" = Red
- Subtitle in parentheses: 12px, gray

**Contribution quality:**
- Badge style
- Background: Tier-1 color (light)
- Border: Tier-1 color
- Text: Tier-1 color (dark)

**Sufficiency:**
- Icon + text
- ✅ Green / ⚠️ Yellow / ❌ Red

**Review flag:**
- 🟢 Green "Looks good"
- 🔴 Red "Needs review"

### Interaction

**Hover on metric:**
- Tooltip with explanation
- Example: "Coverage: Percentage of answer sentences supported by citations"

**Click on metric:**
- Expand to show detailed breakdown
- Example: Coverage → Show which sentences have citations

---

## Component 4: Sources Panel (Tier-Grouped)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ Sources                                                  │
│                                                          │
│ 🟢 Docs (3)                                             │
│   [1] Streaming API Reference                           │
│   [2] Server-Sent Events Guide                          │
│                                                          │
│ 🔵 Blog (1)                                             │
│   [3] Best Practices for Streaming                      │
│                                                          │
│ ⚫ Community (1)                                         │
│   [4] Common Streaming Pitfalls (Stack Overflow)        │
└─────────────────────────────────────────────────────────┘
```

### Visual Styling

**Container:**
- Background: White
- Border: 1px solid #e5e7eb
- Border-radius: 8px
- Padding: 20px

**Tier sections:**
- Margin-bottom: 16px
- Collapsible (click tier header to expand/collapse)

**Tier header:**
- Icon: Tier badge
- Label: Tier name + count
- Font: 14px, semi-bold
- Color: Tier-specific

**Source items:**
- Padding-left: 24px
- Margin-bottom: 8px
- Citation number: Bold, tier-color
- Title: 14px, clickable link
- Hover: Underline + tier-color

### Interaction

**Click source:**
- Open source modal with full content

**Hover source:**
- Show preview tooltip (first 100 chars)

---

## Component 5: Source Modal

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ ← Back                                    [Citation 1]  │
│                                                          │
│ 🟢 Official Documentation                               │
│ Streaming API Reference                                 │
│ docs.anthropic.com/streaming                            │
│ Last updated: 2024-03-15                                │
│                                                          │
│ ─────────────────────────────────────────────────────   │
│                                                          │
│ [Full source content with highlighted excerpt]          │
│                                                          │
│ Streaming returns tokens incrementally using             │
│ Server-Sent Events (SSE). The API sends delta events    │
│ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^         │
│ (highlighted portion that was cited)                     │
│                                                          │
│ as tokens are generated, allowing you to display        │
│ partial results to users in real-time...                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Visual Styling

**Modal overlay:**
- Background: rgba(0,0,0,0.5)
- Backdrop blur: 4px

**Modal container:**
- Width: 700px max
- Background: White
- Border-radius: 12px
- Padding: 32px
- Box-shadow: 0 20px 25px rgba(0,0,0,0.15)

**Header:**
- Tier badge + tier name
- Source title: 20px, bold
- URL: 13px, gray, clickable
- Last updated: 12px, light gray

**Divider:**
- 1px solid #e5e7eb
- Margin: 20px 0

**Content:**
- Font: 15px, line-height 1.7
- Max-height: 500px
- Overflow: Scroll

**Highlighted excerpt:**
- Background: Tier-color (light)
- Border-left: 3px solid tier-color
- Padding: 2px 4px

**Back button:**
- Top-left
- Icon + "Back"
- Hover: Tier-color

---

## Component 6: Site & Topic Selectors

### Site Selector

```
┌─────────────────────────────────────────────────────────┐
│ Select documentation site                                │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [Icon] Anthropic Claude                          ▼  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Options:                                                 │
│ • Anthropic Claude                                       │
│ • LangChain                                              │
│ • Stripe                                                 │
└─────────────────────────────────────────────────────────┘
```

**Visual styling:**
- Dropdown: 300px wide
- Height: 48px
- Border: 2px solid #e5e7eb
- Border-radius: 8px
- Font: 16px
- Icon: Site logo (24×24px)
- Hover: Border-color → tier-1-color

### Topic Selector

```
┌─────────────────────────────────────────────────────────┐
│ What do you want to understand?                          │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Streaming responses                              ▼  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Topics:                                                  │
│ • Streaming responses                                    │
│ • Tool use / function calling                            │
│ • Rate limits                                            │
└─────────────────────────────────────────────────────────┘
```

**Visual styling:**
- Same as site selector
- Appears after site selection
- Smooth fade-in animation (300ms)

---

## Page Layout (Full View)

```
┌───────────────────────────────────────────────────────────┐
│                      VERITAS                              │
│                                                           │
│  [Blurred background: Site screenshot]                   │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Select documentation site                            │ │
│  │ [Anthropic Claude ▼]                                 │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ What do you want to understand?                      │ │
│  │ [Streaming responses ▼]                              │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
└───────────────────────────────────────────────────────────┘

After selection:

┌───────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────┐ │
│  │ [Core Answer] 🟢 Docs-backed                        │ │
│  │ ...                                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ [Implementation Insight] 🔵 In practice             │ │
│  │ ...                                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ [Common Pitfalls] ⚫ Common issues                  │ │
│  │ ...                                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Source Contribution                                  │ │
│  │ Docs     ██████████████░░░░░░ 70%                   │ │
│  │ Blog     ████░░░░░░░░░░░░░░░░ 20%                   │ │
│  │ Community ██░░░░░░░░░░░░░░░░░░ 10%                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │ Trust Signal     │  │ Sources                      │  │
│  │                  │  │                              │  │
│  │ Coverage   82%   │  │ 🟢 Docs (3)                 │  │
│  │ Authority  High  │  │   [1] Streaming API Ref     │  │
│  │ Contribution     │  │   [2] SSE Guide             │  │
│  │   Balanced       │  │                              │  │
│  │ Sufficiency ✅   │  │ 🔵 Blog (1)                 │  │
│  │ Review 🟢        │  │   [3] Best Practices        │  │
│  │                  │  │                              │  │
│  │                  │  │ ⚫ Community (1)            │  │
│  │                  │  │   [4] Common Pitfalls       │  │
│  └──────────────────┘  └──────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## Responsive Behavior

**Desktop (>1024px):**
- Trust card + Sources side-by-side
- Full width answer sections

**Tablet (768-1024px):**
- Trust card + Sources stacked
- Full width answer sections

**Mobile (<768px):**
- All components stacked
- Collapsible sections
- Source contribution bar: Vertical layout

---

## Animations

**Page load:**
- Fade in: 300ms
- Stagger sections: 100ms delay each

**Site/topic selection:**
- Dropdown: Slide down 200ms
- Background blur: Transition 500ms

**Answer display:**
- Sections: Fade in + slide up 400ms
- Stagger: 150ms delay each

**Source contribution bar:**
- Bars: Grow from 0% to final % over 600ms
- Ease: cubic-bezier(0.4, 0.0, 0.2, 1)

**Modal:**
- Overlay: Fade in 200ms
- Container: Scale up + fade in 300ms
- Close: Reverse animation

---

## Accessibility

**Keyboard navigation:**
- Tab through all interactive elements
- Enter to select dropdown items
- Escape to close modal

**Screen reader:**
- Aria labels on all sections
- Tier badges announced as "Official documentation" / "Blog post" / "Community source"
- Progress bars announced with percentage

**Color contrast:**
- All text: WCAG AA compliant
- Tier colors: Tested for colorblind accessibility

---

## Key UI Principles

1. **Source contribution is always visible** - Not hidden in a tab
2. **3-layer format is visually distinct** - Clear section breaks
3. **Trust card is scannable** - No nested metrics
4. **Citations are inline** - Not footnotes
5. **Modal is focused** - One source at a time

---

**This UI makes source contribution and trust signals instantly comprehensible.**
