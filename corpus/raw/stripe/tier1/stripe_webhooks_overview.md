---
source_name: Stripe Webhooks Documentation
url: https://docs.stripe.com/webhooks
source_tier: 1
document_title: Receive Stripe events in your webhook endpoint
---

# Stripe Webhooks

## What are Webhooks?

Stripe uses webhooks to push real-time event data to your application's webhook endpoint when events happen in your Stripe account. Stripe uses HTTPS to send webhook events to your app as a JSON payload that includes an Event object.

## Endpoint Requirements

Your webhook endpoint must:
- Handle POST requests with a JSON payload consisting of an event object
- Quickly return a successful status code (2xx) prior to any complex logic that might cause a timeout
- Return a 200 response before updating a customer's invoice as paid in your accounting system

## Signature Verification

We recommend using our official libraries to verify signatures. You perform the verification by providing the event payload, the Stripe-Signature header, and the endpoint's secret. If verification fails, you get an error.

### Critical Warning

**Stripe requires the raw body of the request to perform signature verification.** If you're using a framework, make sure it doesn't manipulate the raw body. Any manipulation to the raw body of the request causes the verification to fail.

## Best Practices

### Handle Duplicates

Webhook endpoints might occasionally receive the same event more than once. You can guard against duplicated event receipts by logging the event IDs you've processed, and then not processing already-logged events.

### Async Processing

Configure your handler to process incoming events with an asynchronous queue. Any large spike in webhook deliveries might overwhelm your endpoint hosts.

### Verify from Stripe

Without verification, an attacker could send fake webhook events to your endpoint to trigger actions like fulfilling orders, granting account access, or modifying records. Always verify that webhook events originate from Stripe before acting on them.

### Return Quickly

Your endpoint must quickly return a successful status code (2xx) prior to any complex logic that could cause a timeout. For example, you must return a 200 response before updating a customer's invoice as paid in your accounting system.

## Code Example

```ruby
require 'stripe'
require 'sinatra'

endpoint_secret = 'whsec_...'

post '/my/webhook/url' do
  payload = request.body.read
  sig_header = request.env['HTTP_STRIPE_SIGNATURE']
  event = nil

  begin
    event = Stripe::Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  rescue JSON::ParserError => e
    puts "Error parsing payload: #{e.message}"
    status 400
    return
  rescue Stripe::SignatureVerificationError => e
    puts "Error verifying webhook signature: #{e.message}"
    status 400
    return
  end

  # Handle the event
  case event.type
  when 'payment_intent.succeeded'
    payment_intent = event.data.object
    puts 'PaymentIntent was successful!'
  else
    puts "Unhandled event type: #{event.type}"
  end

  status 200
end
```
