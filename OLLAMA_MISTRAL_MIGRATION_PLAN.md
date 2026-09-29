# Ollama/Mistral Migration to Veritas v5

**Date:** 2026-04-17  
**Status:** PLANNING

---

## Objective

Integrate Ollama (local LLM) and Mistral (API-based) as alternative synthesis backends for Veritas, enabling:
1. **Cost control** — Use local Ollama for development/testing
2. **Provider diversity** — Fallback options if OpenAI unavailable
3. **Specialized models** — Mistral for specific reasoning tasks

**Note:** This migration focuses on **Veritas provider diversity** (Path 2: Digital Council). For **Windsurf integration** (Path 1), see `WINDSURF_MCP_INTEGRATION.md` which uses Mistral as an MCP-backed cognitive service layer, not a request interceptor.

---

## Current State

### Veritas Architecture

**Current synthesis flow:**
```
Question → Retrieval → Synthesis (OpenAI GPT-4o) → Answer
```

**Key files:**
- `backend/app.py` — Flask API server
- `backend/agents/synthesis_agent.py` — OpenAI-based synthesis
- `backend/ingestion/embed_chunks.py` — OpenAI embeddings

**Current provider:** OpenAI only
- Model: `gpt-4o` (synthesis)
- Embeddings: `text-embedding-3-small`
- Credential: `OPENAI_API_KEY`

### 8825-Team Implementation

**Ollama backend:**
- File: `8825/system/intelligence/dli_router_mcp/ollama_backend.py`
- URL: `http://localhost:11434`
- Model: `phi:2.7b` (default)
- **No credentials required**

**Mistral backend:**
- File: `8825/system/intelligence/dli_router_mcp/mistral_backend.py`
- API: `api.mistral.ai`
- Models: 4 specialist profiles (general, reasoning, code, math)
- Credential: `MISTRAL_API_KEY` (from Bitwarden)

---

## Migration Strategy

### Phase 1: Provider Abstraction Layer

**Create:** `backend/providers/llm_provider.py`

**Purpose:** Abstract LLM calls behind unified interface

**Interface:**
```python
class LLMProvider:
    def generate(self, prompt: str, system: str, **kwargs) -> dict:
        """
        Returns:
        {
            "response": str,
            "model": str,
            "latency_ms": int,
            "cost_usd": float,
            "tokens_used": int
        }
        """
        pass
```

**Implementations:**
1. `OpenAIProvider` — Current (GPT-4o)
2. `OllamaProvider` — Local (phi:2.7b, llama3, etc.)
3. `MistralProvider` — API (mistral-small, mistral-large)

### Phase 2: Port Ollama Backend

**Source:** `8825-Team/8825/system/intelligence/dli_router_mcp/ollama_backend.py`

**Target:** `backend/providers/ollama_provider.py`

**Changes needed:**
- Adapt to Veritas `LLMProvider` interface
- Add availability check (`is_available()`)
- Handle connection errors gracefully
- Default to `localhost:11434`

**Configuration:**
```python
# backend/.env (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi:2.7b
```

### Phase 3: Port Mistral Backend

**Source:** `8825-Team/8825/system/intelligence/dli_router_mcp/mistral_backend.py`

**Target:** `backend/providers/mistral_provider.py`

**Changes needed:**
- Adapt to Veritas `LLMProvider` interface
- Load `MISTRAL_API_KEY` from environment
- Support specialist profiles (general, reasoning, code, math)
- Add budget tracking (optional)

**Configuration:**
```python
# backend/.env
MISTRAL_API_KEY=<from Bitwarden>
MISTRAL_PROFILE=general  # or reasoning, code, math
```

### Phase 4: Provider Selection Logic

**Create:** `backend/providers/provider_selector.py`

**Selection strategy:**
```python
def select_provider(mode: str = "auto") -> LLMProvider:
    """
    Modes:
    - "auto": OpenAI → Mistral → Ollama (fallback chain)
    - "openai": Force OpenAI
    - "mistral": Force Mistral
    - "ollama": Force Ollama (local)
    - "cheap": Ollama → Mistral → OpenAI (cost priority)
    """
    pass
```

**Fallback logic:**
1. Check if provider is available
2. If unavailable, try next in chain
3. Log provider selection
4. Return working provider or error

### Phase 5: Update Synthesis Agent

**Modify:** `backend/agents/synthesis_agent.py`

**Changes:**
```python
from providers.provider_selector import select_provider

def synthesize_answer(question, chunks, mode="auto"):
    # Select provider based on mode
    provider = select_provider(mode)
    
    # Build prompt (same as before)
    prompt = build_synthesis_prompt(question, chunks)
    
    # Generate with selected provider
    result = provider.generate(
        prompt=prompt,
        system="You are Veritas...",
        temperature=0.7,
        max_tokens=2048
    )
    
    return {
        "answer": result["response"],
        "provider": result["model"],
        "latency_ms": result["latency_ms"],
        "cost_usd": result["cost_usd"]
    }
```

### Phase 6: API Endpoint Updates

**Modify:** `backend/app.py`

**Add mode parameter:**
```python
@app.route('/api/synthesize', methods=['POST'])
@app.route('/api/synthesize/<mode>', methods=['POST'])
def synthesize(mode="auto"):
    """
    Modes:
    - auto (default): Smart fallback
    - openai: Force OpenAI
    - mistral: Force Mistral
    - ollama: Force local Ollama
    - cheap: Cost-optimized selection
    """
    data = request.json
    question = data.get('question')
    
    # ... retrieval logic ...
    
    # Synthesize with mode
    result = synthesize_answer(question, chunks, mode=mode)
    
    return jsonify(result)
```

**Example requests:**
```bash
# Auto mode (default)
curl -X POST https://veritas.8825.systems/api/synthesize \
  -d '{"question": "How do I use Claude?"}'

# Force Ollama (local)
curl -X POST https://veritas.8825.systems/api/synthesize/ollama \
  -d '{"question": "How do I use Claude?"}'

# Force Mistral
curl -X POST https://veritas.8825.systems/api/synthesize/mistral \
  -d '{"question": "How do I use Claude?"}'
```

---

## File Structure

```
backend/
├── providers/
│   ├── __init__.py
│   ├── llm_provider.py          # Base interface
│   ├── openai_provider.py       # Current (GPT-4o)
│   ├── ollama_provider.py       # Local (phi:2.7b)
│   ├── mistral_provider.py      # API (mistral-small)
│   └── provider_selector.py     # Selection logic
├── agents/
│   └── synthesis_agent.py       # Updated to use providers
├── app.py                        # Updated with mode parameter
└── .env                          # MISTRAL_API_KEY, OLLAMA_BASE_URL
```

---

## Dependencies

### New Python packages

```txt
# requirements.txt additions
mistralai==0.1.0  # Mistral SDK (optional, can use httpx)
```

### Ollama installation (local dev only)

```bash
# macOS
brew install ollama

# Start Ollama server
ollama serve

# Pull models
ollama pull phi:2.7b
ollama pull llama3
```

---

## Configuration

### Environment Variables

```bash
# backend/.env

# OpenAI (existing)
OPENAI_API_KEY=sk-proj-...

# Mistral (new)
MISTRAL_API_KEY=<from Bitwarden>
MISTRAL_PROFILE=general

# Ollama (new, optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi:2.7b

# Provider selection (new)
DEFAULT_PROVIDER=auto  # auto, openai, mistral, ollama, cheap
```

### Load from Bitwarden

```bash
# Load secrets
source AI_SYSTEMS/scripts/load_secrets.sh

# Verify
bash AI_SYSTEMS/scripts/check_secrets.sh
# ✓ OPENAI_API_KEY: present
# ✓ MISTRAL_API_KEY: present
```

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_providers.py

def test_openai_provider():
    provider = OpenAIProvider()
    result = provider.generate("What is 2+2?", system="You are helpful")
    assert "4" in result["response"]
    assert result["model"] == "gpt-4o"

def test_ollama_provider():
    provider = OllamaProvider()
    if not provider.is_available():
        pytest.skip("Ollama not running")
    result = provider.generate("What is 2+2?", system="You are helpful")
    assert result["response"]
    assert result["cost_usd"] == 0.0

def test_mistral_provider():
    provider = MistralProvider()
    result = provider.generate("What is 2+2?", system="You are helpful")
    assert result["response"]
    assert result["model"].startswith("mistral")
```

### Integration Tests

```bash
# Test each mode
curl -X POST http://localhost:5000/api/synthesize/openai \
  -d '{"question": "How do I use Claude tool calling?"}'

curl -X POST http://localhost:5000/api/synthesize/ollama \
  -d '{"question": "How do I use Claude tool calling?"}'

curl -X POST http://localhost:5000/api/synthesize/mistral \
  -d '{"question": "How do I use Claude tool calling?"}'
```

### Playwright Tests

**Update:** `frontend/tests/veritas.spec.ts`

```typescript
test('synthesis works with Ollama mode', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Select Ollama mode
  await page.selectOption('[data-testid="provider-select"]', 'ollama');
  
  // Submit question
  await page.fill('[data-testid="question-input"]', 'How do I use Claude?');
  await page.click('[data-testid="submit-button"]');
  
  // Wait for answer
  await page.waitForSelector('[data-testid="answer-text"]');
  
  // Verify provider badge shows "Ollama"
  await expect(page.locator('[data-testid="provider-badge"]')).toContainText('Ollama');
});
```

---

## Deployment Considerations

### Fly.io Deployment

**Ollama:** Cannot run on Fly.io (requires local installation)
- Ollama mode only available for local development
- Production uses OpenAI or Mistral

**Mistral:** Can run on Fly.io
- Add `MISTRAL_API_KEY` to Fly secrets:
  ```bash
  flyctl secrets set MISTRAL_API_KEY="$MISTRAL_API_KEY" --app veritas-8825-systems
  ```

### Provider Availability Matrix

| Provider | Local Dev | Fly.io Deployment |
|----------|-----------|-------------------|
| OpenAI | ✅ Yes | ✅ Yes |
| Mistral | ✅ Yes | ✅ Yes |
| Ollama | ✅ Yes | ❌ No (local only) |

---

## Cost Analysis

### Per-request costs (estimated)

| Provider | Model | Cost per 1K tokens | Typical synthesis |
|----------|-------|-------------------|-------------------|
| OpenAI | gpt-4o | $0.005 input, $0.015 output | ~$0.02 |
| Mistral | mistral-small | $0.001 input, $0.003 output | ~$0.004 |
| Ollama | phi:2.7b | $0.00 (local) | $0.00 |

**Savings potential:**
- Ollama (local dev): 100% cost reduction
- Mistral (production): 80% cost reduction vs OpenAI

---

## Risks & Mitigations

### Risk 1: Ollama not running locally

**Mitigation:** Graceful fallback to Mistral or OpenAI

```python
if mode == "ollama" and not ollama_provider.is_available():
    logger.warning("Ollama not available, falling back to Mistral")
    mode = "mistral"
```

### Risk 2: Mistral API key missing

**Mitigation:** Clear error message, fallback to OpenAI

```python
if mode == "mistral" and not os.getenv("MISTRAL_API_KEY"):
    logger.error("MISTRAL_API_KEY not set")
    raise ValueError("Mistral mode requires MISTRAL_API_KEY")
```

### Risk 3: Quality degradation with smaller models

**Mitigation:** 
- Default to OpenAI for production
- Use Ollama/Mistral for development/testing
- Add quality metrics comparison

### Risk 4: Increased complexity

**Mitigation:**
- Clean provider abstraction
- Comprehensive tests
- Clear documentation

---

## Success Criteria

1. ✅ Provider abstraction layer implemented
2. ✅ Ollama provider working locally
3. ✅ Mistral provider working with API key
4. ✅ Mode selection via API endpoint
5. ✅ Fallback logic tested
6. ✅ Playwright tests pass for all modes
7. ✅ Documentation updated
8. ✅ Deployed to Fly.io with Mistral support

---

## Timeline

**Phase 1-2 (Provider abstraction + Ollama):** 2-3 hours
**Phase 3 (Mistral):** 1-2 hours
**Phase 4-5 (Selection + Synthesis):** 1-2 hours
**Phase 6 (API updates):** 1 hour
**Testing & validation:** 2-3 hours

**Total:** 7-11 hours

---

## Next Steps

1. **Create provider abstraction layer**
   - Define `LLMProvider` interface
   - Implement `OpenAIProvider` (refactor existing)

2. **Port Ollama backend**
   - Copy from 8825-Team
   - Adapt to Veritas interface
   - Test locally

3. **Port Mistral backend**
   - Copy from 8825-Team
   - Add `MISTRAL_API_KEY` loading
   - Test with Bitwarden secret

4. **Implement provider selection**
   - Create `provider_selector.py`
   - Add fallback logic
   - Test all modes

5. **Update synthesis agent**
   - Integrate provider selection
   - Preserve existing behavior
   - Add mode parameter

6. **Update API endpoints**
   - Add `/api/synthesize/<mode>` routes
   - Update CORS for new endpoints
   - Test with curl

7. **Run Playwright validation**
   - Update tests for provider modes
   - Verify UI shows provider badges
   - Confirm screenshots

8. **Deploy to Fly.io**
   - Add `MISTRAL_API_KEY` secret
   - Deploy and verify
   - Test production endpoints

---

**Status:** READY TO START  
**Estimated effort:** 7-11 hours  
**Risk level:** LOW (clean abstraction, proven backends)
