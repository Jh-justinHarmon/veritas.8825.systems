---
source_name: Stripe Webhooks Documentation
url: https://docs.stripe.com/webhooks/signature
source_tier: 1
document_title: Resolve webhook signature verification errors
---

# Signature Verification Troubleshooting

## Verification Parameters

When processing webhook events, call the `constructEvent()` function with three parameters:

1. **requestBody** - The request body string sent by Stripe
2. **signature** - The Stripe-Signature header
3. **endpointSecret** - The secret associated with your endpoint

## Common Verification Errors

If you get the following "Webhook signature verification failed" error, at least one of the three parameters you passed to the `constructEvent()` function is incorrect.

## Most Common Mistake

**The most common error is using the wrong endpoint secret.**

- If you're using a webhook endpoint created in the Dashboard, open the endpoint in the Dashboard and click the "Reveal secret" link near the top of the page to view the secret.
- If you're using the Stripe CLI, the secret is printed in the Terminal when you run the `stripe listen` command.

## Secret Prefix Distinction

In both cases, the secret starts with a `whsec_` prefix, but the secret itself is different.

**Critical:** Don't verify signatures on events forwarded by the CLI using the secret from a Dashboard-managed endpoint, or the other way around.

## Raw Body Requirement

The request body must be the body string that Stripe sends in UTF-8 encoding without any changes. When you print it as a string, it looks similar to:

```json
{ "id": "evt_xxx", "object": "event", "data": { ... } }
```

## Debugging Steps

1. **Check the endpoint secret** - Print the `endpointSecret` used in your code, and make sure that it matches the one you found above.
2. **Verify raw body** - Ensure your framework isn't modifying the request body before verification.
3. **Check test vs live mode** - Make sure you're using the correct secret for your environment.
