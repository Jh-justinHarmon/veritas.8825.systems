---
source_name: Stripe Webhooks - Test/Live Mode Mismatch
url: https://dev.to/nerdincode/debugging-stripe-webhook-signature-verification-errors-in-production-1h7c
source_tier: 3
document_title: Debugging Stripe Webhook Signature Verification Errors in Production
---

# Production Failure: Test vs Live Mode Secret Mismatch

## The Problem

After deploying to production, Stripe kept returning this error:

> "Webhook signature verification failed. No signatures found matching the expected signature for payload."

I was sure my raw body handling was correct, and the endpoint URL was accurate. Locally, everything worked using the Stripe CLI. But in production… webhook requests kept failing.

## Root Cause

Turns out the issue was very simple but easy to overlook: **I was using the Test Mode webhook signing secret (`whsec_...`) in production, while Stripe was sending Live Mode events.**

## Key Insight

Stripe signs test and live events with different secrets, and if you mismatch them, signature verification will always fail — even if your code is perfect.

## Symptom

- ✅ Works locally with `stripe listen`
- ❌ Fails in production

## The Solution

**Environment-Based Configuration**

To avoid this, I updated my environment variables and Stripe initialization code to handle different modes based on the environment.

```javascript
// Wrong - hardcoded test secret in production
const endpointSecret = 'whsec_test_abc123...';

// Right - environment-based configuration
const endpointSecret = process.env.NODE_ENV === 'production'
  ? process.env.STRIPE_WEBHOOK_SECRET_LIVE
  : process.env.STRIPE_WEBHOOK_SECRET_TEST;
```

## Testing Tip

**Use Stripe CLI for Local Testing:**
1. `stripe login`
2. `stripe listen --forward-to localhost:5000/api/v1/webhook/stripe`
3. `stripe trigger checkout.session.completed`

Make sure your local environment uses the test mode secrets to match the CLI's default behavior.

## Warning

Small mistakes like using the wrong webhook secret can cost you hours of debugging. If you're getting a "Webhook signature verification failed" error, double-check your mode (test/live) and environment configuration.

## Developer Quote

> "The Test Mode vs Live Mode secret mismatch is such a common gotcha - I've seen it catch multiple teams."

## Impact

This is the **#1 production failure mode** for Stripe webhooks - accounting for approximately 90% of "works locally, fails in production" cases.
