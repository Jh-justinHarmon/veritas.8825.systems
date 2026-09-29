# Cloudflare DNS Setup for Veritas

## Status

- ✅ **Fly.io deployment:** LIVE at `https://veritas-8825-systems.fly.dev/`
- ⏳ **Custom domain:** Pending DNS configuration

## Required DNS Record

### CNAME Record

| Field | Value |
|-------|-------|
| **Type** | CNAME |
| **Name** | `veritas` |
| **Target** | `veritas-8825-systems.fly.dev` |
| **Proxied** | ✓ Yes (orange cloud) |
| **TTL** | Auto |

## Manual Setup (Cloudflare Dashboard)

1. Log in to Cloudflare Dashboard
2. Select domain: `8825.systems`
3. Go to **DNS** → **Records**
4. Click **Add record**
5. Configure:
   - Type: `CNAME`
   - Name: `veritas`
   - Target: `veritas-8825-systems.fly.dev`
   - Proxy status: **Proxied** (orange cloud icon)
6. Click **Save**

## Automated Setup (Cloudflare API)

Requires `CLOUDFLARE_API_TOKEN` in Bitwarden.

```bash
# Set variables
ZONE_ID="your_zone_id"
API_TOKEN="your_cloudflare_api_token"

# Create CNAME record
curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "CNAME",
    "name": "veritas",
    "content": "veritas-8825-systems.fly.dev",
    "proxied": true,
    "ttl": 1
  }'
```

## Verification

After DNS propagation (1-5 minutes):

```bash
# Check DNS resolution
dig +short veritas.8825.systems

# Test health endpoint
curl https://veritas.8825.systems/api/health

# Expected response:
# {
#   "status": "healthy",
#   "chunks_loaded": 74,
#   "service": "veritas-api"
# }
```

## Current Status

**Fly.io URL (working):**
- https://veritas-8825-systems.fly.dev/
- Health check: ✅ 200 OK
- Chunks loaded: 74
- Service: veritas-api

**Custom domain (pending):**
- https://veritas.8825.systems/
- Status: DNS not configured
- Action required: Add CNAME record

---

**Next step:** Configure Cloudflare DNS record manually or via API
