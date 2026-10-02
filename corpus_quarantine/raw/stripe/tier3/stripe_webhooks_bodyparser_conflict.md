---
source_name: Stripe Webhooks - Express bodyParser Conflict
url: https://github.com/stripe/stripe-node/issues/734
source_tier: 3
document_title: Express bodyParser middleware conflict with Stripe webhook verification
---

# Framework Pitfall: Express bodyParser Middleware Conflict

## The Problem

The problem is that `bodyParser.raw()` will conflict with all other middleware like `bodyParser.json()`. The solution is to use `bodyParser.json()` and use the verify function to grab the rawBuffer and save it as a request property.

## Root Cause

`bodyParser.raw()` and `bodyParser.json()` conflict with each other and one will not run if the other has already ran, so **the first middleware wins**.

## Symptom

**SignatureVerificationError even with correct secret**

If you use in your express app `bodyParser.json()` for all routes, and then have a dedicated route for stripe's webhook, then the second call to `bodyParser.json({verify: ...})` as done in the example has no effect.

## The Solution

```javascript
// The below middleware is a workaround so we can get both `rawBody` 
// and our normal `body`. Stripe webhooks need the rawBody
app.use(bodyParser.json({
  verify: (req, res, buf, encoding) => {
    if (buf && buf.length) {
      req.rawBody = buf.toString(encoding || 'utf8');
    }
  },
  type: 'application/json'
})); // for parsing application/json
```

## Usage

Then user can use `req.rawBody` to construct the event like this:

```javascript
stripe.webhooks.constructEvent(
  req.rawBody, 
  req.headers['stripe-signature'], 
  config.stripe.webhookSecret
);
```

## Documentation Gap

> "This is the only way to have the raw body and the json body at the same time in one express application, while **your docs do not show any warnings at all about this problem**."

## Framework Specificity

**Express.js specific issue.** Other frameworks (Rails, Django, NestJS) have similar raw body access challenges.

## Related Issue

GitHub Issue #341 describes the same problem:

> "Only if I comment out the first call to bodyParser.json does it work. Which mean that I cannot have a call to bodyParser just for my route."

## Why This Happens

1. Express app uses `bodyParser.json()` globally for all routes
2. Stripe webhook route tries to use `bodyParser.raw()` or `bodyParser.json({verify: ...})`
3. First middleware already consumed the request body
4. Second middleware gets nothing
5. Stripe signature verification fails because raw body is unavailable

## The Fix Pattern

Always use the `verify` callback in your global `bodyParser.json()` configuration to capture `req.rawBody` **before** the body is parsed. This ensures both parsed JSON and raw body are available for all routes.
