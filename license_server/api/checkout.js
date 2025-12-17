/**
 * Stripe Checkout API Endpoints
 * Handles payment session creation and checkout flow
 */

const express = require('express');
const router = express.Router();

class CheckoutAPI {
    constructor(stripeManager, auth0Manager) {
        this.stripeManager = stripeManager;
        this.auth0Manager = auth0Manager;
    }

    /**
     * Create checkout session
     * POST /api/checkout/create-session
     */
    async createSession(req, res) {
        try {
            const { plan, success_url, cancel_url } = req.body;
            const user = req.user; // From auth middleware

            if (!plan || !['monthly', 'yearly', 'perpetual'].includes(plan)) {
                return res.status(400).json({ error: 'Invalid plan. Must be monthly, yearly, or perpetual' });
            }

            // Get or create Stripe customer
            const customer = await this.stripeManager.getOrCreateCustomer(user.id, user.email);

            // Get price ID for plan (configure these in Stripe Dashboard)
            const priceId = this.getPriceIdForPlan(plan);

            // Determine mode
            const mode = plan === 'perpetual' ? 'payment' : 'subscription';

            // Create session
            const session = mode === 'payment' 
                ? await this.stripeManager.createPaymentSession(
                    customer.id,
                    priceId,
                    success_url || `${process.env.FRONTEND_URL || 'http://localhost:3000'}/checkout/success`,
                    cancel_url || `${process.env.FRONTEND_URL || 'http://localhost:3000'}/checkout/cancel`,
                    { user_id: user.id, plan: plan }
                )
                : await this.stripeManager.createCheckoutSession(
                    customer.id,
                    priceId,
                    success_url || `${process.env.FRONTEND_URL || 'http://localhost:3000'}/checkout/success`,
                    cancel_url || `${process.env.FRONTEND_URL || 'http://localhost:3000'}/checkout/cancel`,
                    { user_id: user.id, plan: plan }
                );

            res.json({
                success: true,
                session_id: session.id,
                url: session.url
            });
        } catch (error) {
            console.error('Create checkout session error:', error);
            res.status(500).json({ error: `Failed to create checkout session: ${error.message}` });
        }
    }

    /**
     * Handle successful checkout
     * GET /api/checkout/success
     */
    async success(req, res) {
        try {
            const { session_id } = req.query;

            if (!session_id) {
                return res.status(400).json({ error: 'Session ID is required' });
            }

            // Retrieve session from Stripe
            const session = await this.stripeManager.stripe.checkout.sessions.retrieve(session_id);

            res.json({
                success: true,
                message: 'Payment successful',
                session: {
                    id: session.id,
                    customer: session.customer,
                    mode: session.mode
                }
            });
        } catch (error) {
            console.error('Checkout success error:', error);
            res.status(500).json({ error: `Failed to process success: ${error.message}` });
        }
    }

    /**
     * Handle cancelled checkout
     * GET /api/checkout/cancel
     */
    async cancel(req, res) {
        res.json({
            success: false,
            message: 'Checkout cancelled'
        });
    }

    /**
     * Create billing portal session
     * POST /api/checkout/billing-portal
     */
    async createBillingPortalSession(req, res) {
        try {
            const user = req.user;
            const { return_url } = req.body;

            // Get customer ID from entitlements
            const client = await this.stripeManager.db.connect();
            try {
                const result = await client.query(
                    'SELECT stripe_customer_id FROM entitlements WHERE user_id = $1 AND stripe_customer_id IS NOT NULL LIMIT 1',
                    [user.id]
                );

                if (result.rows.length === 0 || !result.rows[0].stripe_customer_id) {
                    return res.status(404).json({ error: 'No Stripe customer found' });
                }

                const customerId = result.rows[0].stripe_customer_id;
                const session = await this.stripeManager.createBillingPortalSession(
                    customerId,
                    return_url || `${process.env.FRONTEND_URL || 'http://localhost:3000'}/dashboard`
                );

                res.json({
                    success: true,
                    url: session.url
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Create billing portal session error:', error);
            res.status(500).json({ error: `Failed to create billing portal session: ${error.message}` });
        }
    }

    /**
     * Get price ID for plan
     */
    getPriceIdForPlan(plan) {
        // These should be configured in Stripe Dashboard and stored in environment variables
        const priceIds = {
            monthly: process.env.STRIPE_PRICE_MONTHLY_ID || 'price_monthly',
            yearly: process.env.STRIPE_PRICE_YEARLY_ID || 'price_yearly',
            perpetual: process.env.STRIPE_PRICE_PERPETUAL_ID || 'price_perpetual'
        };

        return priceIds[plan] || priceIds.monthly;
    }
}

module.exports = CheckoutAPI;
