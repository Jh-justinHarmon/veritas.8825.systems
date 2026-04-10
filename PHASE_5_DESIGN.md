# Veritas Phase 5: Trace & History

## Objective

Add conversation history and synthesis trace capabilities to Veritas, enabling users to:
1. View previous questions and answers
2. Revisit synthesis results
3. Trace the reasoning path (which sources were used, how concepts were formed)
4. Compare answers across different queries

---

## Core Features

### 1. History Storage

**Backend:**
- Store each synthesis request/response pair
- Include metadata: timestamp, question, answer, sources used, retrieval scores
- Persist to JSON file or lightweight database

**Data Structure:**
```json
{
  "id": "uuid",
  "timestamp": "ISO-8601",
  "question": "string",
  "answer": {
    "ideas": [...],
    "sources": {...}
  },
  "trace": {
    "retrieved_chunks": [...],
    "retrieval_scores": [...],
    "synthesis_model": "gpt-4o",
    "synthesis_duration_ms": 1234
  }
}
```

### 2. History API Endpoints

**GET /api/history**
- Returns list of previous synthesis sessions
- Supports pagination
- Returns: `[{id, timestamp, question, preview}, ...]`

**GET /api/history/:id**
- Returns full synthesis result for a specific session
- Includes complete answer and trace data

**DELETE /api/history/:id**
- Removes a history entry

### 3. Frontend History UI

**History Sidebar/Panel:**
- List of previous questions (chronological)
- Click to load previous answer
- Visual indicator of current vs historical view
- Search/filter history

**History Item Display:**
- Question text
- Timestamp (relative: "2 hours ago")
- Preview of first concept
- Badge showing source count

### 4. Trace Visualization

**Show synthesis trace:**
- Which chunks were retrieved (with scores)
- How sources mapped to concepts
- Retrieval ranking visualization
- Source tier distribution

**Trace Panel:**
- Expandable section showing "how this answer was built"
- Retrieved chunks with similarity scores
- Source-to-concept mapping
- Synthesis metadata (model, duration, chunk count)

---

## UI/UX Design

### History Panel (Left Sidebar)

```
┌─────────────────────────┐
│ HISTORY                 │
├─────────────────────────┤
│ ○ Why is Claude...      │
│   2 hours ago • 3 ideas │
│                         │
│ ○ How to debug tool...  │
│   Yesterday • 4 ideas   │
│                         │
│ ○ Parameter validation  │
│   2 days ago • 2 ideas  │
└─────────────────────────┘
```

### Trace Panel (Expandable)

```
┌─────────────────────────────────────┐
│ ▼ SYNTHESIS TRACE                   │
├─────────────────────────────────────┤
│ Retrieved 10 chunks (0.8s)          │
│                                     │
│ Top Sources:                        │
│ 1. Anthropic Docs [0.94] → Idea 1  │
│ 2. Practice Guide [0.87] → Idea 2  │
│ 3. Failure Case [0.82] → Idea 3    │
│                                     │
│ Synthesis: GPT-4o (2.3s)            │
└─────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 5.1: Backend History Storage

1. Create `backend/history/` module
2. Implement `HistoryStore` class
   - `save_synthesis(question, answer, trace)`
   - `get_all_history(limit, offset)`
   - `get_history_by_id(id)`
   - `delete_history(id)`
3. Add history endpoints to Flask API
4. Test with curl

### Phase 5.2: Frontend History UI

1. Create `frontend/src/components/HistoryPanel.tsx`
2. Add history API client functions
3. Implement history list rendering
4. Add click-to-load functionality
5. Style history panel

### Phase 5.3: Trace Visualization

1. Extend synthesis API to return trace data
2. Create `frontend/src/components/TracePanel.tsx`
3. Visualize retrieval scores
4. Show source-to-concept mapping
5. Add expand/collapse interaction

### Phase 5.4: Integration & Polish

1. Add history panel to main layout
2. Implement current vs historical view switching
3. Add search/filter to history
4. Polish animations and transitions
5. Validate with Playwright

---

## Success Criteria (DoD)

**Playwright tests must verify:**
- History panel displays previous questions
- Clicking history item loads previous answer
- Trace panel shows retrieval scores
- Source-to-concept mapping visible
- All features work end-to-end

**Screenshot must show:**
- History panel with multiple entries
- Trace panel expanded with scores
- Previous answer loaded correctly
- Visual distinction between current and historical

---

## Technical Considerations

**Storage:**
- Start with JSON file (`history/synthesis_history.json`)
- Migrate to SQLite if performance needed
- Keep file size manageable (limit to 100 most recent)

**Performance:**
- Lazy load history (don't load all on startup)
- Cache current session in memory
- Paginate history list

**Privacy:**
- History stored locally only
- No external transmission
- User can clear history

---

## Next Steps

1. Implement backend history storage
2. Add API endpoints
3. Create frontend history UI
4. Add trace visualization
5. Validate with Playwright per DoD protocol
