---
source_name: Stripe Webhooks Documentation
url: https://docs.stripe.com/webhooks/quickstart
source_tier: 1
document_title: Set up and deploy a webhook - Quickstart
---

# Webhook Quickstart Guide

## Setup Steps

1. **Create handler function**
2. **Test with Stripe CLI** (`stripe listen`)
3. **Register endpoint in Dashboard**
4. **Deploy to production**

## Stripe CLI Usage

Use `stripe listen` to find the endpoint secret for local testing. The CLI forwards webhook events to your local development server.

### Local Testing Workflow

The Stripe CLI is essential for webhook development:
- Simulates webhook events locally
- Provides a test mode signing secret
- Forwards events to your localhost
- Shows real-time delivery status

## Interactive Webhook Builder

An interactive webhook endpoint builder is available at docs.stripe.com/webhooks/quickstart to build a webhook endpoint function in your programming language.

## Testing Before Production

The Stripe CLI allows you to test your webhook implementation thoroughly before deploying to production, ensuring signature verification and event handling work correctly.
