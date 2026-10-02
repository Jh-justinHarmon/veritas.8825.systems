---
source_name: Stripe Webhooks - ngrok Testing
url: https://ngrok.com/docs/integrations/webhooks/stripe-webhooks
source_tier: 2
document_title: Stripe Webhooks - ngrok documentation
---

# Local Webhook Testing with ngrok

## Purpose

Expose localhost to internet for webhook testing. Create a publicly accessible tunnel to your local development server for Stripe webhook delivery.

## Workflow

Once your app is running locally, you're ready to put it online securely using ngrok. Copy your ngrok authtoken from the dashboard. The ngrok agent uses your authtoken to authenticate when you start a tunnel.

## Testing Benefit

Test webhooks before production deployment. With ngrok running you can now test the site using your local dev domain. You will see any configured stripe events configured for the webhook displayed in the console window and can debug them using your IDE.

## Development Workflow

1. Start your local development server
2. Run ngrok to create a tunnel: `ngrok http 3000`
3. Copy the ngrok HTTPS URL
4. Add the ngrok URL to your Stripe webhook endpoints
5. Test webhook delivery in real-time
6. Debug using your local IDE with live Stripe events
