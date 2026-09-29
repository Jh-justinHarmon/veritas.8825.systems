# Veritas Deployment Process

**Status:** Ready for deployment  
**Target URL:** `veritas.8825.systems`  
**Last Updated:** 2026-04-17

---

## Established 8825 Deployment Pattern

Based on proven process from `8825-Team`:
1. **Design in Replit** (prototype/develop)
2. **Pull down codebase** (refine locally)
3. **Set up DNS in Cloudflare** (CNAME to Fly.io)
4. **Deploy to Fly.io** (production hosting)

---

## Step 1: Prepare Codebase

### Frontend Build
```bash
cd /Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin\ Harmon/AI_SYSTEMS/8825-modules/Veritas/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Output: dist/ directory with static assets
```

### Backend Preparation
```bash
cd /Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin\ Harmon/AI_SYSTEMS/8825-modules/Veritas/backend

# Verify requirements.txt exists
cat requirements.txt

# Test locally
python3 run.py
```

---

## Step 2: Create Fly.io App

```bash
cd /Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin\ Harmon/AI_SYSTEMS/8825-modules/Veritas

# Login to Fly.io
flyctl auth login

# Create app
flyctl app create veritas-8825-systems

# Or if app exists
flyctl config set app veritas-8825-systems
```

---

## Step 3: Create fly.toml

**Location:** `/Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin Harmon/AI_SYSTEMS/8825-modules/Veritas/fly.toml`

```toml
app = "veritas-8825-systems"
primary_region = "ord"

[build]
  builder = "heroku/buildpacks:20"

[env]
  PYTHON_VERSION = "3.9"
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = 'stop'      # CRITICAL: Stop when idle (cost prevention)
  auto_start_machines = true       # Auto-start on traffic
  min_machines_running = 0         # Allow scaling to zero
  processes = ['app']

[[vm]]
  memory = '512mb'
  cpu_kind = 'shared'
  cpus = 1

[deploy]
  release_command = "python3 backend/run.py"
```

**Cost Prevention:**
- `auto_stop_machines = 'stop'` - Stops when idle
- `min_machines_running = 0` - Scales to zero
- **Expected cost:** $0-5/month (only when actively used)

---

## Step 4: Set Environment Variables

```bash
# Set OpenAI API key (required for synthesis)
flyctl secrets set OPENAI_API_KEY="your-openai-api-key"

# Verify
flyctl secrets list
```

---

## Step 5: Deploy to Fly.io

```bash
cd /Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin\ Harmon/AI_SYSTEMS/8825-modules/Veritas

# Build and deploy
flyctl deploy

# Watch deployment
flyctl logs

# Check status
flyctl status
```

---

## Step 6: Configure DNS in Cloudflare

**Domain:** `8825.systems` (already owned)

### In Cloudflare Dashboard:

1. **Navigate to DNS settings** for `8825.systems`

2. **Create CNAME record:**
   - **Name:** `veritas`
   - **Target:** `veritas-8825-systems.fly.dev`
   - **Proxy status:** Proxied (orange cloud) ✓
   - **TTL:** Auto

3. **Wait for DNS propagation** (~5 minutes)

4. **Test:**
   ```bash
   curl https://veritas.8825.systems/api/health
   ```

---

## Step 7: Validate Deployment

### Health Check
```bash
curl https://veritas.8825.systems/api/health
# Expected: {"status": "ok", "chunks_loaded": 74, "service": "veritas"}
```

### Canonical Demo Test
```bash
curl -X POST https://veritas.8825.systems/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"question":"Why is Claude calling the wrong tool or using incorrect parameters?"}'
```

**Expected:**
- 4 concepts synthesized
- 3 tiers represented (SPEC/PRACTICE/FAILURE)
- Inline citations present
- Response time <30 seconds

### Frontend Access
```bash
open https://veritas.8825.systems
```

**Expected:**
- Question loads: "Why is Claude calling the wrong tool or using incorrect parameters?"
- Synthesis completes in <30 seconds
- 4 concepts displayed
- Sources sidebar shows tier breakdown
- Citations are hoverable

---

## Monitoring

### View Logs
```bash
flyctl logs -a veritas-8825-systems
```

### Check Status
```bash
flyctl status -a veritas-8825-systems
```

### SSH into App
```bash
flyctl ssh console -a veritas-8825-systems
```

### Restart App
```bash
flyctl restart -a veritas-8825-systems
```

---

## Troubleshooting

### App won't start
```bash
flyctl logs -a veritas-8825-systems
# Check for missing dependencies or import errors
```

### DNS not resolving
```bash
nslookup veritas.8825.systems
# Should return veritas-8825-systems.fly.dev
```

### Synthesis fails
```bash
# Check if OPENAI_API_KEY is set
flyctl secrets list -a veritas-8825-systems

# Check backend logs
flyctl logs -a veritas-8825-systems | grep ERROR
```

### HTTPS certificate issues
```bash
# Fly.io auto-generates certs, may take 5-10 minutes
curl https://veritas.8825.systems/api/health
```

---

## Updating Deployment

### After code changes:

```bash
# Commit to GitHub
cd /Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin\ Harmon/AI_SYSTEMS/8825-modules/Veritas
git add .
git commit -m "Update Veritas"
git push origin main

# Deploy
flyctl deploy

# Verify
flyctl logs
```

### Update environment variables:

```bash
# Change OPENAI_API_KEY
flyctl secrets set OPENAI_API_KEY="new-key"

# Restart to apply
flyctl restart
```

---

## Cost Management

**Fly.io Configuration:**
- `auto_stop_machines = 'stop'` ✓
- `min_machines_running = 0` ✓
- Memory: 512MB
- CPU: 1 shared

**Expected Cost:** $0-5/month (only when actively used)

**Monthly Audit:**
```bash
flyctl apps list
flyctl status -a veritas-8825-systems
```

**If unused for 30+ days:**
```bash
flyctl apps suspend veritas-8825-systems
# Or destroy if no longer needed
flyctl apps destroy veritas-8825-systems --yes
```

---

## Security Checklist

- [ ] OPENAI_API_KEY not in git repo (use `flyctl secrets`)
- [ ] HTTPS enabled (automatic on Fly.io)
- [ ] CORS configured correctly (backend allows frontend origin)
- [ ] No sensitive data in logs
- [ ] API rate limiting considered (OpenAI API limits)

---

## Success Criteria

✅ **Public URL works** — `https://veritas.8825.systems` accessible  
✅ **Health check passes** — `/api/health` returns 200  
✅ **Synthesis works** — Question → 4 concepts in <30 seconds  
✅ **Quality metrics visible** — Tier labels, citations, source sidebar  
✅ **Screenshot proof captured** — `tests/screenshots/success.png`  
✅ **Playwright tests passing** — 2/2 tests pass

---

## Next Steps

1. ✅ UI simplified (mode toggle removed, history removed)
2. ✅ Playwright validation passing
3. ⏳ Create `fly.toml`
4. ⏳ Deploy to Fly.io
5. ⏳ Configure Cloudflare DNS
6. ⏳ Test public access
7. ⏳ Create final proof screenshot
8. ⏳ Update README
9. ⏳ Make repo public

---

## References

- **Fly.io Cost Prevention:** `8825-Team/FLY_IO_COST_PREVENTION_GUIDE.md`
- **Replit Deployment Protocol:** `8825-Team/8825/system/protocols/REPLIT_DEPLOYMENT_PROTOCOL.md`
- **Setup.8825.systems Deploy:** `8825-Team/apps/setup.8825.systems/DEPLOY.md`
- **Veritas Spine:** `veritas_project_spine_v1.4.json`
- **Public Artifact Spec:** `PUBLIC_ARTIFACT_SPEC.md`
