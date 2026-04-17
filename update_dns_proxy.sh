#!/bin/bash
set -e

source ~/.cloudflare/.env

ZONE_NAME="8825.systems"
RECORD_NAME="veritas"

echo "🔍 Getting zone and record IDs..."

ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

RECORD_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$RECORD_NAME.$ZONE_NAME" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

echo "✅ Zone ID: $ZONE_ID"
echo "✅ Record ID: $RECORD_ID"
echo ""
echo "📝 Updating DNS record to DNS-only (disabling proxy)..."

RESPONSE=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"proxied": false}')

SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

if [ "$SUCCESS" == "true" ]; then
    echo "✅ DNS record updated to DNS-only mode"
    echo ""
    echo "⏱️  Wait 30 seconds for DNS to propagate, then test:"
    echo "   curl https://veritas.8825.systems/api/health"
else
    echo "❌ Failed to update record"
    echo "$RESPONSE" | jq .
fi
