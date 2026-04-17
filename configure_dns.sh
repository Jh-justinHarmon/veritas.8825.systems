#!/bin/bash
# Veritas Cloudflare DNS Configuration
# Configures veritas.8825.systems → veritas-8825-systems.fly.dev

set -e

ZONE_NAME="8825.systems"
RECORD_NAME="veritas"
TARGET="veritas-8825-systems.fly.dev"

# Check for CF_API_TOKEN
if [ -z "$CF_API_TOKEN" ]; then
    echo "❌ CF_API_TOKEN not set"
    echo ""
    echo "Options to set it:"
    echo "1. From Bitwarden:"
    echo "   export BW_SESSION=\$(bw unlock --raw)"
    echo "   export CF_API_TOKEN=\$(bw get item 'Cloudflare 8825-4.1' | jq -r '.login.password')"
    echo ""
    echo "2. Manually:"
    echo "   export CF_API_TOKEN='your-token-here'"
    echo ""
    exit 1
fi

echo "🔍 Finding zone ID for $ZONE_NAME..."

# Get zone ID
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ "$ZONE_ID" == "null" ] || [ -z "$ZONE_ID" ]; then
    echo "❌ Could not find zone: $ZONE_NAME"
    exit 1
fi

echo "✅ Zone ID: $ZONE_ID"
echo ""
echo "🔍 Checking for existing DNS record..."

# Check if record exists
EXISTING_RECORD=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$RECORD_NAME.$ZONE_NAME" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json")

RECORD_ID=$(echo "$EXISTING_RECORD" | jq -r '.result[0].id')

if [ "$RECORD_ID" != "null" ] && [ -n "$RECORD_ID" ]; then
    echo "📝 Updating existing CNAME record..."
    
    RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{
            \"type\": \"CNAME\",
            \"name\": \"$RECORD_NAME\",
            \"content\": \"$TARGET\",
            \"ttl\": 1,
            \"proxied\": false
        }")
else
    echo "➕ Creating new CNAME record..."
    
    RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{
            \"type\": \"CNAME\",
            \"name\": \"$RECORD_NAME\",
            \"content\": \"$TARGET\",
            \"ttl\": 1,
            \"proxied\": false
        }")
fi

# Check response
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

if [ "$SUCCESS" == "true" ]; then
    echo ""
    echo "✅ DNS record configured successfully!"
    echo ""
    echo "📋 Record Details:"
    echo "   Type: CNAME"
    echo "   Name: $RECORD_NAME.$ZONE_NAME"
    echo "   Target: $TARGET"
    echo "   Proxied: No (DNS only)"
    echo ""
    echo "🌐 Your app will be accessible at:"
    echo "   https://$RECORD_NAME.$ZONE_NAME"
    echo ""
    echo "⏱️  DNS propagation may take a few minutes"
else
    echo ""
    echo "❌ Failed to configure DNS record"
    echo "Response: $RESPONSE"
    exit 1
fi
