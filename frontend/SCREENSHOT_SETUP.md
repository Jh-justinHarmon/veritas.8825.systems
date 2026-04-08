# Background Screenshot Setup

## Required Screenshots

Place the following screenshots in `frontend/public/screenshots/`:

### 1. Claude Screenshot
**Filename:** `claude-screenshot.png`  
**Source:** Screenshot of Claude.ai or Anthropic docs  
**Overlay:** Light white tint (rgba(255, 255, 255, 0.21))

### 2. LangChain Screenshot
**Filename:** `langchain-screenshot.png`  
**Source:** Screenshot of LangChain docs or platform  
**Overlay:** Medium white tint (rgba(255, 255, 255, 0.34))

### 3. Stripe Screenshot
**Filename:** `stripe-screenshot.png`  
**Source:** Screenshot of Stripe docs or dashboard  
**Overlay:** Dark overlay (rgba(0, 0, 0, 0.55))

## Directory Structure

```
frontend/
  public/
    screenshots/
      claude-screenshot.png
      langchain-screenshot.png
      stripe-screenshot.png
```

## Usage

The BackgroundLayer component will automatically load these images based on the selected site:

```tsx
<BackgroundLayer site="claude" />
```

Each screenshot will be:
- Blurred (8px)
- Scaled up slightly (1.05x) to avoid blur edges
- Covered with site-specific overlay tint
- Positioned behind all UI content (z-index: -1)
- Non-interactive (pointer-events: none)

## Next Steps

1. Add your screenshots to `frontend/public/screenshots/`
2. Ensure filenames match exactly (case-sensitive)
3. BackgroundLayer will work automatically when App.tsx includes it
