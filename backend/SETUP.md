# Veritas Backend Setup

## Quick Start

### 1. Set Up API Key

Run the setup script:

```bash
python3 setup_api_key.py
```

**What happens:**
1. Script prompts: `Paste your OPENAI_API_KEY and press Enter:`
2. You paste your key
3. Press Enter
4. Key is saved to `.env`
5. Done!

**Example:**
```
============================================================
Veritas API Key Setup
============================================================

Paste your OPENAI_API_KEY and press Enter:
> sk-proj-your-key-here

✓ Saved to /path/to/backend/.env
✓ Done.

You can now run the Veritas backend:
  python3 app.py
```

### 2. Start Backend

```bash
python3 app.py
```

The server will start on `http://localhost:5001`

**Expected output:**
```
✓ OPENAI_API_KEY loaded: sk-svcacct-U84dH91Wj...LL0A
[synthesis_agent] ✓ OPENAI_API_KEY accessible: sk-svcacct-U84dH91Wj...LL0A
Loading embedded chunks...
Loaded 74 chunks
Tier breakdown: {1: 60, 2: 6, 3: 8}

============================================================
Veritas API Server
============================================================
Chunks loaded: 74
Endpoints:
  - GET    /
  - GET    /api/health
  - GET    /api/examples
  - POST   /api/synthesize
  - GET    /api/history
  - GET    /api/history/<id>
  - DELETE /api/history/<id>
============================================================
```

## Verification

### Test Environment Loading

```bash
python3 verify_env.py
```

**Expected:**
```
✓ OPENAI_API_KEY found in shell environment
  Shell key: sk-proj-...

Loading .env...
✓ SUCCESS: OPENAI_API_KEY loaded
  Format: ✓ Valid OpenAI key format
```

### Test OpenAI Authentication

```bash
python3 test_openai_auth.py
```

**Expected:**
```
✓ API Key loaded: sk-svcacct-...
✓ SUCCESS: API call succeeded
  Embedding dimensions: 1536
  Model: text-embedding-3-small
```

## Files

- **`setup_api_key.py`** — Interactive API key setup (v4 style)
- **`verify_env.py`** — Verify `.env` file loads correctly
- **`test_openai_auth.py`** — Test actual OpenAI API authentication
- **`.env`** — Your API key (gitignored, never committed)
- **`.env.example`** — Template showing required format

## Security

- `.env` is in `.gitignore` — **never committed to git**
- `.env.*` patterns also ignored
- Setup script validates key format (must start with `sk-`)
- Keys are never printed after saving

## Troubleshooting

### "No key provided"
You pressed Enter without pasting a key. Run the script again.

### "Key doesn't start with 'sk-'"
Your key may be invalid. OpenAI keys start with `sk-proj-` or `sk-svcacct-`.

### "401 - Incorrect API key"
Your key is invalid or expired. Get a new key from:
https://platform.openai.com/account/api-keys

### "Address already in use"
Port 5001 is in use. Kill the existing process:
```bash
lsof -ti:5001 | xargs kill -9
```

## Environment Variable Priority

The backend uses `load_dotenv(override=True)` to ensure `.env` file takes precedence over shell environment variables.

**Priority order:**
1. `.env` file (highest priority)
2. Shell environment variables (ignored due to `override=True`)

This ensures consistent behavior regardless of shell configuration.
