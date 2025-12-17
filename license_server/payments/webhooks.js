/**
 * Stripe Webhook Handlers
 * Handles Stripe webhook events for subscription and payment management
 */

class StripeWebhookHandler {
    constructor(stripeManager, dbPool) {
        this.stripe = stripeManager.stripe;
        this.webhookSecret = stripeManager.webhookSecret;
        this.db = dbPool;
    }

    /**
     * Handle webhook event
     */
    async handleWebhook(req, res) {
        const sig = req.headers['stripe-signature'];
        let event;

        try {
            // req.body is already a Buffer when using express.raw()
            event = this.stripe.webhooks.constructEvent(req.body, sig, this.webhookSecret);
        } catch (err) {
            console.error('Webhook signature verification failed:', err.message);
            return res.status(400).send(`Webhook Error: ${err.message}`);
        }

        // Handle the event
        try {
            switch (event.type) {
                case 'customer.subscription.created':
                    await this.handleSubscriptionCreated(event.data.object);
                    break;
                case 'customer.subscription.updated':
                    await this.handleSubscriptionUpdated(event.data.object);
                    break;
                case 'customer.subscription.deleted':
                    await this.handleSubscriptionDeleted(event.data.object);
                    break;
                case 'invoice.payment_succeeded':
                    await this.handleInvoicePaymentSucceeded(event.data.object);
                    break;
                case 'invoice.payment_failed':
                    await this.handleInvoicePaymentFailed(event.data.object);
                    break;
                case 'customer.subscription.trial_will_end':
                    await this.handleTrialWillEnd(event.data.object);
                    break;
                case 'checkout.session.completed':
                    await this.handleCheckoutCompleted(event.data.object);
                    break;
                default:
                    console.log(`Unhandled event type: ${event.type}`);
            }

            res.json({ received: true });
        } catch (error) {
            console.error('Webhook handler error:', error);
            res.status(500).json({ error: 'Webhook handler failed' });
        }
    }

    /**
     * Handle subscription created
     */
    async handleSubscriptionCreated(subscription) {
        const client = await this.db.connect();
        try {
            const customerId = subscription.customer;
            const subscriptionId = subscription.id;
            const priceId = subscription.items.data[0].price.id;
            
            // Get customer to find user_id
            const customer = await this.stripe.customers.retrieve(customerId);
            const userId = customer.metadata?.user_id;

            if (!userId) {
                console.error('No user_id in customer metadata');
                return;
            }

            // Determine plan from price ID
            const plan = this.determinePlanFromPrice(priceId);
            const expiresAt = new Date(subscription.current_period_end * 1000);

            // Create or update entitlement
            await client.query(
                `INSERT INTO entitlements 
                 (user_id, product_id, plan, status, stripe_subscription_id, stripe_customer_id, expires_at, features, max_devices)
                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                 ON CONFLICT (user_id) DO UPDATE
                 SET plan = $3, status = $4, stripe_subscription_id = $5, expires_at = $7, updated_at = NOW()`,
                [
                    userId,
                    'upload_bridge_pro',
                    plan,
                    'active',
                    subscriptionId,
                    customerId,
                    expiresAt,
                    JSON.stringify(this.getFeaturesForPlan(plan)),
                    1 // max_devices
                ]
            );

            console.log(`✅ Created entitlement for user ${userId}, subscription ${subscriptionId}`);
        } finally {
            client.release();
        }
    }

    /**
     * Handle subscription updated
     */
    async handleSubscriptionUpdated(subscription) {
        const client = await this.db.connect();
        try {
            const subscriptionId = subscription.id;
            const priceId = subscription.items.data[0].price.id;
            const expiresAt = new Date(subscription.current_period_end * 1000);
            const plan = this.determinePlanFromPrice(priceId);

            // Update entitlement
            await client.query(
                `UPDATE entitlements
                 SET plan = $1, expires_at = $2, features = $3, updated_at = NOW()
                 WHERE stripe_subscription_id = $4`,
                [
                    plan,
                    expiresAt,
                    JSON.stringify(this.getFeaturesForPlan(plan)),
                    subscriptionId
                ]
            );

            console.log(`✅ Updated entitlement for subscription ${subscriptionId}`);
        } finally {
            client.release();
        }
    }

    /**
     * Handle subscription deleted
     */
    async handleSubscriptionDeleted(subscription) {
        const client = await this.db.connect();
        try {
            const subscriptionId = subscription.id;

            // Revoke entitlement
            await client.query(
                `UPDATE entitlements
                 SET status = 'cancelled', updated_at = NOW()
                 WHERE stripe_subscription_id = $1`,
                [subscriptionId]
            );

            console.log(`✅ Cancelled entitlement for subscription ${subscriptionId}`);
        } finally {
            client.release();
        }
    }

    /**
     * Handle invoice payment succeeded
     */
    async handleInvoicePaymentSucceeded(invoice) {
        const client = await this.db.connect();
        try {
            const subscriptionId = invoice.subscription;
            if (!subscriptionId) {
                // One-time payment
                return;
            }

            const expiresAt = new Date(invoice.period_end * 1000);

            // Extend entitlement expiry
            await client.query(
                `UPDATE entitlements
                 SET expires_at = $1, status = 'active', updated_at = NOW()
                 WHERE stripe_subscription_id = $2`,
                [expiresAt, subscriptionId]
            );

            console.log(`✅ Extended entitlement for subscription ${subscriptionId}`);
        } finally {
            client.release();
        }
    }

    /**
     * Handle invoice payment failed
     */
    async handleInvoicePaymentFailed(invoice) {
        const client = await this.db.connect();
        try {
            const subscriptionId = invoice.subscription;
            if (!subscriptionId) {
                return;
            }

            // Mark entitlement as payment_failed
            await client.query(
                `UPDATE entitlements
                 SET status = 'payment_failed', updated_at = NOW()
                 WHERE stripe_subscription_id = $1`,
                [subscriptionId]
            );

            console.log(`⚠️ Payment failed for subscription ${subscriptionId}`);
        } finally {
            client.release();
        }
    }

    /**
     * Handle trial will end
     */
    async handleTrialWillEnd(subscription) {
        // Send notification to user (implement notification service)
        console.log(`⚠️ Trial ending soon for subscription ${subscription.id}`);
    }

    /**
     * Handle checkout completed (for one-time payments)
     */
    async handleCheckoutCompleted(session) {
        if (session.mode === 'payment') {
            // One-time payment (perpetual license)
            const client = await this.db.connect();
            try {
                const customerId = session.customer;
                const customer = await this.stripe.customers.retrieve(customerId);
                const userId = customer.metadata?.user_id;

                if (!userId) {
                    console.error('No user_id in customer metadata');
                    return;
                }

                // Create perpetual entitlement
                await client.query(
                    `INSERT INTO entitlements 
                     (user_id, product_id, plan, status, stripe_customer_id, expires_at, features, max_devices)
                     VALUES ($1, $2, $3, $4, $5, NULL, $6, $7)
                     ON CONFLICT (user_id) DO UPDATE
                     SET plan = $3, status = $4, expires_at = NULL, updated_at = NOW()`,
                    [
                        userId,
                        'upload_bridge_pro',
                        'perpetual',
                        'active',
                        customerId,
                        JSON.stringify(this.getFeaturesForPlan('perpetual')),
                        1
                    ]
                );

                console.log(`✅ Created perpetual entitlement for user ${userId}`);
            } finally {
                client.release();
            }
        }
    }

    /**
     * Determine plan from Stripe price ID
     */
    determinePlanFromPrice(priceId) {
        // This should match your Stripe price IDs
        // You can also query Stripe API to get price details
        if (priceId.includes('monthly') || priceId.includes('month')) {
            return 'monthly';
        } else if (priceId.includes('yearly') || priceId.includes('year')) {
            return 'yearly';
        } else if (priceId.includes('perpetual') || priceId.includes('lifetime')) {
            return 'perpetual';
        }
        return 'monthly'; // default
    }

    /**
     * Get features for plan
     */
    getFeaturesForPlan(plan) {
        const baseFeatures = ['pattern_upload', 'wifi_upload'];
        
        switch (plan) {
            case 'trial':
                return baseFeatures;
            case 'monthly':
            case 'yearly':
            case 'perpetual':
                return [...baseFeatures, 'advanced_controls', 'cloud_sync', 'preset_library'];
            default:
                return baseFeatures;
        }
    }
}

module.exports = StripeWebhookHandler;
