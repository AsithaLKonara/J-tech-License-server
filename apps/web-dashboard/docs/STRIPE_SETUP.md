# Stripe Payment Configuration Guide

This guide explains how to configure Stripe payment processing for production.

## Prerequisites

1. Stripe account (create at https://stripe.com)
2. Access to Stripe Dashboard
3. Production domain with SSL certificate

## Step 1: Get Stripe API Keys

1. Log into [Stripe Dashboard](https://dashboard.stripe.com)
2. Ensure you're in **Live mode** (toggle in top right)
3. Navigate to **Developers** → **API keys**
4. Copy the following:
   - **Publishable key** (starts with `pk_live_`)
   - **Secret key** (starts with `sk_live_`) - Click "Reveal test key" if needed

## Step 2: Create Price IDs

1. In Stripe Dashboard, go to **Products**
2. Create three products for your subscription plans:
   - Monthly Plan
   - Annual Plan
   - Lifetime Plan
3. For each product, create a price:
   - Set the price amount
   - Set billing period (monthly, yearly, or one-time)
   - Copy the **Price ID** (starts with `price_`)

## Step 3: Configure Environment Variables

Update `.env` file with your Stripe credentials:

```env
STRIPE_KEY=pk_live_your_publishable_key_here
STRIPE_SECRET=sk_live_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PRICE_MONTHLY=price_your_monthly_price_id
STRIPE_PRICE_ANNUAL=price_your_annual_price_id
STRIPE_PRICE_LIFETIME=price_your_lifetime_price_id
```

## Step 4: Set Up Stripe Webhook

Webhooks allow Stripe to notify your application of payment events.

### 4.1 Create Webhook Endpoint

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Configure:
   - **Endpoint URL**: `https://yourdomain.com/webhook/stripe`
   - **Description**: Upload Bridge Webhook
   - **Events to send**: Select the following events:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
4. Click **Add endpoint**

### 4.2 Get Webhook Secret

1. After creating the endpoint, click on it
2. In the **Signing secret** section, click **Reveal**
3. Copy the secret (starts with `whsec_`)
4. Add to `.env` as `STRIPE_WEBHOOK_SECRET`

### 4.3 Test Webhook (Optional)

1. In the webhook endpoint page, click **Send test webhook**
2. Select an event type (e.g., `checkout.session.completed`)
3. Click **Send test webhook**
4. Check your application logs to verify the webhook was received and processed

## Step 5: Test Payment Flow

### 5.1 Test Checkout Session Creation

1. Navigate to subscription page
2. Select a plan
3. Click "Subscribe"
4. Verify redirect to Stripe Checkout

### 5.2 Test Successful Payment

Use Stripe's test card numbers:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- Use any future expiry date (e.g., 12/34)
- Use any 3-digit CVC

### 5.3 Verify Webhook Processing

1. Complete a test payment
2. Check application logs for webhook processing
3. Verify subscription was created in database
4. Verify user has active entitlement

## Step 6: Configure Stripe Settings

### 6.1 Business Information

1. Go to **Settings** → **Business settings**
2. Complete business information:
   - Business name
   - Address
   - Tax ID (if applicable)
   - Contact email

### 6.2 Branding

1. Go to **Settings** → **Branding**
2. Upload your logo
3. Set brand colors
4. This will appear in checkout pages

### 6.3 Email Receipts

1. Go to **Settings** → **Emails**
2. Configure receipt emails
3. Set up email templates

## Webhook Security

The application validates webhook signatures to ensure requests come from Stripe.

### Signature Validation

The `StripeWebhookController` validates signatures using:
- Request payload
- Stripe signature header
- Webhook secret

### Security Best Practices

1. **Always use HTTPS** for webhook endpoint
2. **Keep webhook secret secure** - never commit to version control
3. **Validate signatures** - the application does this automatically
4. **Use idempotency** - handle duplicate webhook events gracefully
5. **Log webhook events** - for debugging and audit trails

## Testing in Production

### Test Mode vs Live Mode

- **Test mode**: Use test keys (`pk_test_`, `sk_test_`) - no real charges
- **Live mode**: Use live keys (`pk_live_`, `sk_live_`) - real charges

### Switching to Live Mode

1. Update `.env` with live keys
2. Update webhook endpoint to production URL
3. Test with small transaction first
4. Monitor logs and Stripe Dashboard

## Troubleshooting

### Webhook Not Received

1. Verify webhook URL is publicly accessible
2. Check SSL certificate is valid
3. Verify webhook secret matches
4. Check firewall/security settings
5. Review Stripe Dashboard → Webhooks → Logs

### Webhook Signature Verification Failed

1. Verify `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
2. Check webhook endpoint is using HTTPS
3. Ensure request body is raw (not parsed)
4. Review application logs for details

### Payment Processing Errors

1. Check Stripe Dashboard → Payments → Logs
2. Review application logs
3. Verify API keys are correct
4. Check account status (not restricted)
5. Verify payment methods are enabled

### Subscription Not Created

1. Check webhook logs in Stripe Dashboard
2. Review application logs
3. Verify database connection
4. Check user exists in database
5. Review `StripeService::handleWebhook()` method

## API Documentation

### StripeService Methods

- `createCheckoutSession(User $user, string $planType)`: Creates Stripe Checkout session
- `handleWebhook(string $payload, string $signature)`: Processes webhook events
- `cancelSubscription(string $subscriptionId)`: Cancels a subscription

### Webhook Events Handled

- `checkout.session.completed`: Creates subscription after successful payment
- `customer.subscription.updated`: Updates subscription status
- `customer.subscription.deleted`: Handles subscription cancellation
- `invoice.payment_succeeded`: Records successful payment
- `invoice.payment_failed`: Handles failed payments

## Support

- Stripe Documentation: https://stripe.com/docs
- Stripe Support: https://support.stripe.com
- Stripe API Reference: https://stripe.com/docs/api
