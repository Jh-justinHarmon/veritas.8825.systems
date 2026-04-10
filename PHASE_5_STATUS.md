# Veritas Phase 5: Trace & History - Status

## Backend: ✅ Complete

### History Storage (`backend/history/`)

**Implemented:**
- `HistoryStore` class for managing synthesis history
- JSON-based storage (`history/synthesis_history.json`)
- Automatic session ID generation (UUID)
- Pagination support (limit/offset)
- History entry preview format

**Features:**
- `save_synthesis(question, answer, trace)` - Save session with trace data
- `get_all_history(limit, offset)` - Get paginated history list
- `get_history_by_id(session_id)` - Get full history entry
- `delete_history(session_id)` - Remove history entry
- Automatic limit to 100 most recent entries

### API Endpoints (`backend/app.py`)

**Implemented:**
- `GET /api/history` - List history (paginated)
- `GET /api/history/<id>` - Get specific entry
- `DELETE /api/history/<id>` - Delete entry
- Updated `POST /api/synthesize` to save history automatically

**Trace Data Captured:**
- Retrieved chunks (source_name, title, tier, text_preview)
- Chunk count
- Synthesis model used
- Timestamp

**Backend tested and working:** ✅

```bash
# Test history API
curl http://localhost:5001/api/history
# Returns: [] (empty initially, populated after synthesis)
```

---

## Frontend: 🚧 Partial

### Completed:
- `frontend/src/api/veritas.ts` - History API client functions
- `frontend/src/components/HistoryPanel.tsx` - History sidebar component
- Type definitions for `HistoryEntry` and `HistoryDetail`

### Remaining Work:
1. **Fix import conflicts** in `Home.tsx`
   - Duplicate `cn` import (from utils vs local)
   - Need to remove local `cn` function

2. **Add HistoryPanel to layout**
   - Integrate `<HistoryPanel>` into main layout
   - Wire up `handleSelectHistory` callback
   - Pass `currentSessionId` prop

3. **Update VeritasAnswer type**
   - Add optional `session_id` field to match API response

4. **Test end-to-end flow**
   - Synthesize answer → history saved
   - Click history entry → previous answer loads
   - Verify UI updates correctly

---

## What Works Now

**Backend fully functional:**
1. Every synthesis request automatically saves to history
2. History API returns list of previous questions
3. Can retrieve full answer + trace data by session ID
4. Can delete history entries

**Example flow:**
```bash
# 1. Synthesize answer (automatically saves to history)
curl -X POST http://localhost:5001/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"question": "Why is Claude calling the wrong tool?"}'

# Response includes session_id:
# {"session_id": "abc-123", "question": "...", "ideas": [...], "sources": {...}}

# 2. Get history list
curl http://localhost:5001/api/history

# 3. Get specific history entry
curl http://localhost:5001/api/history/abc-123

# 4. Delete history entry
curl -X DELETE http://localhost:5001/api/history/abc-123
```

---

## Next Steps for Full Integration

### 1. Fix Home.tsx Imports
```typescript
// Remove local cn function (line 23-25)
// Keep only: import { cn } from "../lib/utils";
```

### 2. Add HistoryPanel to Layout
```typescript
return (
  <div className="flex h-screen">
    <HistoryPanel 
      onSelectHistory={handleSelectHistory}
      currentSessionId={currentSessionId}
    />
    <div className="flex-1">
      {/* existing content */}
    </div>
  </div>
);
```

### 3. Update API Response Type
```typescript
// In veritas.ts
export interface VeritasAnswer {
  session_id?: string;  // Add this
  question: string;
  ideas: VeritasIdea[];
  sources: Record<string, any>;
}
```

### 4. Playwright Test for History
```typescript
test('should save and load history', async ({ page }) => {
  await page.goto('http://localhost:5175');
  
  // Wait for initial synthesis
  await page.waitForSelector('text=/tool|parameter/i');
  
  // Check history panel appears
  const historyPanel = await page.locator('text=History').count();
  expect(historyPanel).toBeGreaterThan(0);
  
  // Verify history entry exists
  const historyEntry = await page.locator('text=/Why is Claude/i').count();
  expect(historyEntry).toBeGreaterThan(0);
});
```

---

## Design: Trace Visualization (Future)

**Not yet implemented:**
- Expandable trace panel showing retrieval scores
- Source-to-concept mapping visualization
- Chunk similarity scores display

**Deferred because:**
- Backend trace data is captured and available
- Can be added incrementally without breaking existing features
- Focus on core history functionality first

---

## Summary

**Phase 5 Backend:** ✅ Complete and tested  
**Phase 5 Frontend:** 🚧 Partial (API client + component created, integration pending)  
**Phase 5 Trace Viz:** 📋 Designed but not implemented

**Current demo has:**
- Full tier diversity (SPEC, PRACTICE, FAILURE)
- Inline citations
- Source attribution with URLs
- Backend history storage (automatic)
- History API endpoints (working)

**To complete Phase 5 UI:**
- Fix import conflicts
- Integrate HistoryPanel component
- Add Playwright test
- Validate per DoD protocol
