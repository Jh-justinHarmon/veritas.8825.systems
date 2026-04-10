# Veritas Backend Integration Guide

## Status: Phase 4 Backend Integration Complete ✓

### What's Working

**✅ Synthesis Agent**
- Concept-driven answer generation
- Multi-perspective integration (docs + practice + failure)
- Structured JSON output (ideas[] + sources{})
- Replit-quality synthesis

**✅ Flask API Server**
- Running on `http://localhost:5001`
- CORS enabled for frontend
- 56 embedded chunks loaded
- End-to-end flow: question → embedding → retrieval → synthesis

**✅ Retrieval System**
- Authority-weighted scoring (70% similarity + 30% tier authority)
- Tier metadata preservation
- Claude documentation corpus

---

## API Endpoints

### `POST /api/synthesize`

**Request:**
```json
{
  "question": "string (5-500 chars)"
}
```

**Response:**
```json
{
  "question": "string",
  "ideas": [
    {
      "title": "Declarative concept statement",
      "paragraphs": ["string", "string"],
      "sourceIds": ["1", "2"]
    }
  ],
  "sources": {
    "1": "Source title or description",
    "2": "Source title or description"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"question": "Why is Claude calling the wrong tool?"}'
```

### `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "chunks_loaded": 56,
  "service": "veritas-api"
}
```

### `GET /api/examples`

**Response:**
```json
[
  {
    "id": "tool-use-errors",
    "question": "Why is Claude calling the wrong tool or using incorrect parameters?",
    "description": "Tool selection, schema design, parameter specification"
  }
]
```

---

## Frontend Integration

### Step 1: Create API Client

**File:** `frontend/src/api/veritas.ts`

```typescript
export interface VeritasIdea {
  title: string;
  paragraphs: string[];
  sourceIds: string[];
}

export interface VeritasAnswer {
  question: string;
  ideas: VeritasIdea[];
  sources: Record<string, string>;
}

const API_BASE_URL = 'http://localhost:5001';

export async function synthesizeAnswer(question: string): Promise<VeritasAnswer> {
  const response = await fetch(`${API_BASE_URL}/api/synthesize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Synthesis failed');
  }

  return await response.json();
}

export async function getExamples() {
  const response = await fetch(`${API_BASE_URL}/api/examples`);
  return await response.json();
}
```

### Step 2: Update Home.tsx to Use API

**File:** `frontend/src/pages/Home.tsx`

**Current (Mock Mode):**
```typescript
const answer = getHardcodedAnswer();  // Mock data
```

**Updated (API Mode):**
```typescript
import { useQuery } from '@tanstack/react-query';
import { synthesizeAnswer } from '../api/veritas';

// Inside Home component:
const [question, setQuestion] = useState('');
const [submitted, setSubmitted] = useState(false);

const { data: answer, isLoading, error } = useQuery({
  queryKey: ['answer', question],
  queryFn: () => synthesizeAnswer(question),
  enabled: submitted && question.length >= 5,
});

// Render loading/error states
if (isLoading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
```

### Step 3: Add Question Input UI

**Add to Home.tsx:**
```typescript
function AskView({ onSubmit }: { onSubmit: (q: string) => void }) {
  const [input, setInput] = useState('');

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">Ask Veritas</h1>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask a question about developer documentation..."
        className="w-full p-4 border rounded-lg"
        rows={4}
      />
      <button
        onClick={() => onSubmit(input)}
        disabled={input.length < 5}
        className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg"
      >
        Ask
      </button>
    </div>
  );
}
```

### Step 4: Update Data Adapter (Optional)

**Current adapter transforms hardcoded data.**

**For API integration:**
- API already returns correct format (ideas[] + sources{})
- Adapter can be simplified or removed
- Direct pass-through from API to UI

**Simplified adapter:**
```typescript
// frontend/src/adapters/veritasAdapter.ts
export function transformApiResponse(apiResponse: any): VeritasAnswer {
  // API response already matches UI contract
  // Just map title → concept for UI compatibility
  return {
    question: apiResponse.question,
    ideas: apiResponse.ideas.map(idea => ({
      id: idea.title.toLowerCase().replace(/\s+/g, '-'),
      concept: idea.title,  // Use title as concept
      paragraphs: idea.paragraphs,
      sourceIds: idea.sourceIds
    })),
    sources: Object.entries(apiResponse.sources).reduce((acc, [id, title]) => {
      acc[id] = {
        label: title as string,
        short: (title as string).split(' - ')[0] || title as string,
        type: 'docs',  // Default, could be enhanced
        meta: '2024',
        excerpt: ''
      };
      return acc;
    }, {} as Record<string, VeritasSource>)
  };
}
```

---

## Running the Full Stack

### Terminal 1: Backend API
```bash
cd backend
unset OPENAI_API_KEY  # Use .env file
python3 app.py
```

**Expected output:**
```
Loading embedded chunks...
Loaded 56 chunks

============================================================
Veritas API Server
============================================================
Chunks loaded: 56
Endpoints:
  - GET  /api/health
  - GET  /api/examples
  - POST /api/synthesize
============================================================

 * Running on http://127.0.0.1:5001
```

### Terminal 2: Frontend Dev Server
```bash
cd frontend
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5174/
➜  Network: use --host to expose
```

### Test the Integration

1. **Open browser:** `http://localhost:5174`
2. **Enter question:** "Why is Claude calling the wrong tool?"
3. **Submit**
4. **Verify:**
   - Loading state appears
   - API call to `http://localhost:5001/api/synthesize`
   - 3 concepts render with thesis statements
   - Citations are clickable
   - Source sidebar populates

---

## Data Flow

```
User Question
    ↓
Frontend (React Query)
    ↓
POST /api/synthesize
    ↓
Flask API (app.py)
    ↓
1. Generate embedding (embed_chunks.py)
    ↓
2. Retrieve chunks (simple_retriever.py)
   - Cosine similarity
   - Authority weighting
   - Top 10 chunks
    ↓
3. Synthesize answer (synthesis_agent.py)
   - Concept-driven prompt
   - GPT-4o
   - Structured JSON output
    ↓
Response: { question, ideas[], sources{} }
    ↓
Frontend renders ReadingView
```

---

## Current Limitations

**Known Issues:**
- Source type classification is generic ('docs' for all)
- Source excerpts are empty (not populated from chunks)
- No eval scoring integration yet
- No trace/history features yet

**To Fix:**
1. **Enhance source metadata in synthesis:**
   ```python
   # In synthesis_agent.py format_retrieval_context()
   # Pass tier info to LLM for type classification
   ```

2. **Add eval scoring:**
   ```python
   # In app.py after synthesis
   from evals.scoring import evaluate_answer
   scores = evaluate_answer(question, answer_text, citations)
   ```

3. **Populate source excerpts:**
   ```python
   # Map sourceIds back to original chunks
   # Extract relevant excerpt from chunk text
   ```

---

## Next Steps

**Phase 5: Trace & History**
- Add trace view (retrieval steps, synthesis process)
- Run history (in-memory or JSON storage)
- Replay functionality

**Phase 6: Demo & Launch**
- Record demo video
- Write README
- Deploy to Fly.io
- Make repo public

---

## Troubleshooting

**Port 5000 already in use:**
- macOS AirPlay Receiver uses port 5000
- API now runs on port 5001
- Update frontend API_BASE_URL if needed

**CORS errors:**
- Verify Flask-CORS is installed
- Check allowed origins in app.py
- Frontend must run on localhost:5173 or 5174

**Synthesis fails:**
- Check OPENAI_API_KEY in backend/.env
- Verify chunks loaded (should see "Loaded 56 chunks")
- Check Flask logs for detailed error

**Empty response:**
- Verify question length (5-500 chars)
- Check retrieval returned chunks
- Review synthesis_agent.py logs

---

## Architecture Boundaries (Reminder)

**Backend:** Retrieval engine
- Provides evidence, not synthesis
- Authority-weighted scoring
- Tier metadata preservation

**Synthesis Agent:** Answer composer
- Transforms retrieval → concepts
- Multi-perspective integration
- Structured JSON output

**Frontend:** Canonical interface
- Defines answer contract (ideas[] + sources{})
- Concept-driven reading experience
- Citation and source navigation

**The backend serves the frontend's contract, not the other way around.**
