#!/bin/bash
set -e

source ~/.cloudflare/.env

ZONE_NAME="8825.systems"
RECORD_NAME="veritas"
FLY_IPV4="66.241.125.76"
FLY_IPV6="2a09:8280:1::104:9904:0"

echo "🔍 Getting zone ID..."
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

echo "✅ Zone ID: $ZONE_ID"
echo ""

# Delete existing CNAME record
echo "🗑️  Deleting existing CNAME record..."
EXISTING=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$RECORD_NAME.$ZONE_NAME" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json")

RECORD_ID=$(echo "$EXISTING" | jq -r '.result[0].id')
if [ "$RECORD_ID" != "null" ]; then
    curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" > /dev/null
    echo "✅ Deleted old CNAME record"
fi

# Create A record
echo "➕ Creating A record..."
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
        \"type\": \"A\",
        \"name\": \"$RECORD_NAME\",
        \"content\": \"$FLY_IPV4\",
        \"ttl\": 1,
        \"proxied\": false
    }" | jq -r '.success' > /dev/null && echo "✅ A record created"

# Create AAAA record
echo "➕ Creating AAAA record..."
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
        \"type\": \"AAAA\",
        \"name\": \"$RECORD_NAME\",
        \"content\": \"$FLY_IPV6\",
        \"ttl\": 1,
        \"proxied\": false
    }" | jq -r '.success' > /dev/null && echo "✅ AAAA record created"

echo ""
echo "✅ DNS records updated!"
echo "   A    veritas.8825.systems → $FLY_IPV4"
echo "   AAAA veritas.8825.systems → $FLY_IPV6"
echo ""
echo "⏱️  Wait 30-60 seconds for DNS propagation"
