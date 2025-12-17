/**
 * Stripe Payment Integration
 * Handles Stripe API configuration and product/price management
 */

const Stripe = require('stripe');

class StripeManager {
    constructor(config, dbPool) {
        this.stripe = new Stripe(config.STRIPE_SECRET_KEY, {
            apiVersion: '2023-10-16',
        });
        this.db = dbPool;
        this.webhookSecret = config.STRIPE_WEBHOOK_SECRET;
        
        // Product IDs (configure these in Stripe Dashboard)
        this.products = {
            pro_monthly: config.STRIPE_PRODUCT_MONTHLY_ID || 'prod_monthly',
            pro_yearly: config.STRIPE_PRODUCT_YEARLY_ID || 'prod_yearly',
            pro_perpetual: config.STRIPE_PRODUCT_PERPETUAL_ID || 'prod_perpetual',
        };
    }

    /**
     * Create or retrieve Stripe customer for user
     */
    async getOrCreateCustomer(userId, email) {
        const client = await this.db.connect();
        try {
            // Check if customer already exists in database
            const result = await client.query(
                'SELECT stripe_customer_id FROM entitlements WHERE user_id = $1 AND stripe_customer_id IS NOT NULL LIMIT 1',
                [userId]
            );

            if (result.rows.length > 0 && result.rows[0].stripe_customer_id) {
                // Verify customer exists in Stripe
                try {
                    const customer = await this.stripe.customers.retrieve(result.rows[0].stripe_customer_id);
                    return customer;
                } catch (error) {
                    // Customer doesn't exist in Stripe, create new one
                }
            }

            // Create new Stripe customer
            const customer = await this.stripe.customers.create({
                email: email,
                metadata: {
                    user_id: userId
                }
            });

            return customer;
        } finally {
            client.release();
        }
    }

    /**
     * Create Checkout Session for subscription
     */
    async createCheckoutSession(customerId, priceId, successUrl, cancelUrl, metadata = {}) {
        const session = await this.stripe.checkout.sessions.create({
            customer: customerId,
            payment_method_types: ['card'],
            line_items: [
                {
                    price: priceId,
                    quantity: 1,
                },
            ],
            mode: 'subscription', // or 'payment' for one-time
            success_url: successUrl,
            cancel_url: cancelUrl,
            metadata: metadata,
            subscription_data: {
                metadata: metadata
            }
        });

        return session;
    }

    /**
     * Create one-time payment session (for perpetual licenses)
     */
    async createPaymentSession(customerId, priceId, successUrl, cancelUrl, metadata = {}) {
        const session = await this.stripe.checkout.sessions.create({
            customer: customerId,
            payment_method_types: ['card'],
            line_items: [
                {
                    price: priceId,
                    quantity: 1,
                },
            ],
            mode: 'payment',
            success_url: successUrl,
            cancel_url: cancelUrl,
            metadata: metadata
        });

        return session;
    }

    /**
     * Get subscription details
     */
    async getSubscription(subscriptionId) {
        return await this.stripe.subscriptions.retrieve(subscriptionId);
    }

    /**
     * Cancel subscription
     */
    async cancelSubscription(subscriptionId) {
        return await this.stripe.subscriptions.cancel(subscriptionId);
    }

    /**
     * Update subscription (upgrade/downgrade)
     */
    async updateSubscription(subscriptionId, newPriceId) {
        const subscription = await this.stripe.subscriptions.retrieve(subscriptionId);
        
        return await this.stripe.subscriptions.update(subscriptionId, {
            items: [{
                id: subscription.items.data[0].id,
                price: newPriceId,
            }],
            proration_behavior: 'always_invoice',
        });
    }

    /**
     * Get customer's payment methods
     */
    async getPaymentMethods(customerId) {
        return await this.stripe.paymentMethods.list({
            customer: customerId,
            type: 'card',
        });
    }

    /**
     * Update customer's default payment method
     */
    async updateDefaultPaymentMethod(customerId, paymentMethodId) {
        return await this.stripe.customers.update(customerId, {
            invoice_settings: {
                default_payment_method: paymentMethodId,
            },
        });
    }

    /**
     * Create billing portal session
     */
    async createBillingPortalSession(customerId, returnUrl) {
        return await this.stripe.billingPortal.sessions.create({
            customer: customerId,
            return_url: returnUrl,
        });
    }
}

module.exports = StripeManager;
