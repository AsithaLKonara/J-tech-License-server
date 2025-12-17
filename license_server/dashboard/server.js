/**
 * Dashboard Backend API
 * Provides API endpoints for web dashboard (device management, billing, account settings)
 */

const express = require('express');
const router = express.Router();

class DashboardAPI {
    constructor(dbPool, auth0Manager, stripeManager) {
        this.db = dbPool;
        this.auth0Manager = auth0Manager;
        this.stripeManager = stripeManager;
    }

    /**
     * Get current user info
     * GET /dashboard/api/user
     */
    async getUser(req, res) {
        try {
            const user = req.user;
            
            res.json({
                id: user.id,
                email: user.email,
                created_at: user.created_at
            });
        } catch (error) {
            console.error('Get user error:', error);
            res.status(500).json({ error: `Failed to get user: ${error.message}` });
        }
    }

    /**
     * Get user entitlements
     * GET /dashboard/api/entitlements
     */
    async getEntitlements(req, res) {
        try {
            const userId = req.user.id;
            const client = await this.db.connect();
            
            try {
                const result = await client.query(
                    `SELECT * FROM entitlements 
                     WHERE user_id = $1 
                     ORDER BY created_at DESC`,
                    [userId]
                );

                res.json({
                    entitlements: result.rows
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Get entitlements error:', error);
            res.status(500).json({ error: `Failed to get entitlements: ${error.message}` });
        }
    }

    /**
     * List user's devices
     * GET /dashboard/api/devices
     */
    async listDevices(req, res) {
        try {
            const userId = req.user.id;
            const client = await this.db.connect();
            
            try {
                const result = await client.query(
                    `SELECT d.*, e.plan, e.product_id
                     FROM devices d
                     JOIN entitlements e ON d.entitlement_id = e.id
                     WHERE d.user_id = $1
                     ORDER BY d.last_seen DESC`,
                    [userId]
                );

                res.json({
                    devices: result.rows
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('List devices error:', error);
            res.status(500).json({ error: `Failed to list devices: ${error.message}` });
        }
    }

    /**
     * Revoke device
     * POST /dashboard/api/devices/:id/revoke
     */
    async revokeDevice(req, res) {
        try {
            const userId = req.user.id;
            const deviceId = req.params.id;
            const client = await this.db.connect();
            
            try {
                // Verify device belongs to user
                const checkResult = await client.query(
                    'SELECT * FROM devices WHERE id = $1 AND user_id = $2',
                    [deviceId, userId]
                );

                if (checkResult.rows.length === 0) {
                    return res.status(404).json({ error: 'Device not found' });
                }

                await client.query(
                    'DELETE FROM devices WHERE id = $1 AND user_id = $2',
                    [deviceId, userId]
                );

                res.json({
                    success: true,
                    message: 'Device revoked successfully'
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Revoke device error:', error);
            res.status(500).json({ error: `Failed to revoke device: ${error.message}` });
        }
    }

    /**
     * Rename device
     * POST /dashboard/api/devices/:id/rename
     */
    async renameDevice(req, res) {
        try {
            const userId = req.user.id;
            const deviceId = req.params.id;
            const { device_name } = req.body;
            const client = await this.db.connect();
            
            try {
                if (!device_name) {
                    return res.status(400).json({ error: 'Device name is required' });
                }

                // Verify device belongs to user
                const checkResult = await client.query(
                    'SELECT * FROM devices WHERE id = $1 AND user_id = $2',
                    [deviceId, userId]
                );

                if (checkResult.rows.length === 0) {
                    return res.status(404).json({ error: 'Device not found' });
                }

                await client.query(
                    'UPDATE devices SET device_name = $1 WHERE id = $2 AND user_id = $3',
                    [device_name, deviceId, userId]
                );

                res.json({
                    success: true,
                    message: 'Device renamed successfully'
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Rename device error:', error);
            res.status(500).json({ error: `Failed to rename device: ${error.message}` });
        }
    }

    /**
     * Get billing information
     * GET /dashboard/api/billing
     */
    async getBilling(req, res) {
        try {
            const userId = req.user.id;
            const client = await this.db.connect();
            
            try {
                // Get entitlement with Stripe info
                const result = await client.query(
                    `SELECT stripe_customer_id, stripe_subscription_id, plan, status, expires_at
                     FROM entitlements
                     WHERE user_id = $1 AND stripe_customer_id IS NOT NULL
                     ORDER BY created_at DESC
                     LIMIT 1`,
                    [userId]
                );

                if (result.rows.length === 0) {
                    return res.json({
                        has_subscription: false,
                        message: 'No active subscription'
                    });
                }

                const entitlement = result.rows[0];
                let subscription = null;
                let paymentMethods = [];

                // Get subscription details from Stripe
                if (entitlement.stripe_subscription_id && this.stripeManager) {
                    try {
                        subscription = await this.stripeManager.getSubscription(entitlement.stripe_subscription_id);
                        paymentMethods = await this.stripeManager.getPaymentMethods(entitlement.stripe_customer_id);
                    } catch (error) {
                        console.error('Failed to fetch Stripe data:', error);
                    }
                }

                res.json({
                    has_subscription: true,
                    customer_id: entitlement.stripe_customer_id,
                    subscription_id: entitlement.stripe_subscription_id,
                    plan: entitlement.plan,
                    status: entitlement.status,
                    expires_at: entitlement.expires_at,
                    subscription: subscription,
                    payment_methods: paymentMethods.data || []
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Get billing error:', error);
            res.status(500).json({ error: `Failed to get billing info: ${error.message}` });
        }
    }

    /**
     * Update payment method
     * POST /dashboard/api/billing/update-payment
     */
    async updatePaymentMethod(req, res) {
        try {
            const userId = req.user.id;
            const { payment_method_id } = req.body;
            const client = await this.db.connect();
            
            try {
                if (!payment_method_id) {
                    return res.status(400).json({ error: 'Payment method ID is required' });
                }

                // Get customer ID
                const result = await client.query(
                    'SELECT stripe_customer_id FROM entitlements WHERE user_id = $1 AND stripe_customer_id IS NOT NULL LIMIT 1',
                    [userId]
                );

                if (result.rows.length === 0) {
                    return res.status(404).json({ error: 'No Stripe customer found' });
                }

                const customerId = result.rows[0].stripe_customer_id;

                // Update default payment method
                if (this.stripeManager) {
                    await this.stripeManager.updateDefaultPaymentMethod(customerId, payment_method_id);
                }

                res.json({
                    success: true,
                    message: 'Payment method updated successfully'
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Update payment method error:', error);
            res.status(500).json({ error: `Failed to update payment method: ${error.message}` });
        }
    }
}

module.exports = DashboardAPI;
