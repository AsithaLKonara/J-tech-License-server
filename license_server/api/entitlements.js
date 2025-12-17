/**
 * Entitlement API Endpoints
 * Handles entitlement tokens, device management, and session management
 */

const crypto = require('crypto');

class EntitlementAPI {
    constructor(dbPool, tokenSigner, auth0Manager) {
        this.db = dbPool;
        this.tokenSigner = tokenSigner;
        this.auth0Manager = auth0Manager;
        
        // Token lifetime based on plan (in seconds)
        this.TOKEN_LIFETIMES = {
            trial: 24 * 60 * 60,      // 24 hours
            monthly: 3 * 24 * 60 * 60,  // 3 days
            yearly: 14 * 24 * 60 * 60,  // 14 days
            perpetual: 30 * 24 * 60 * 60 // 30 days
        };
    }

    /**
     * Exchange Auth0 token for session token
     * POST /api/auth/login
     */
    async login(req, res) {
        try {
            const { auth0_token, device_id, device_name } = req.body;

            if (!auth0_token) {
                return res.status(400).json({ error: 'Auth0 token is required' });
            }

            // Verify Auth0 token and get user
            const decoded = await this.auth0Manager.verifyAuth0Token(auth0_token);
            const user = await this.auth0Manager.getOrCreateUser(decoded);

            // Get active entitlement
            const entitlement = await this.getActiveEntitlement(user.id);
            if (!entitlement) {
                return res.status(403).json({ 
                    error: 'No active entitlement found',
                    requires_subscription: true 
                });
            }

            // Check device limit
            if (device_id) {
                const deviceCount = await this.getDeviceCount(user.id, entitlement.id);
                if (deviceCount >= entitlement.max_devices) {
                    // Check if this device is already registered
                    const existingDevice = await this.getDevice(user.id, device_id);
                    if (!existingDevice) {
                        return res.status(403).json({ 
                            error: 'Device limit reached',
                            max_devices: entitlement.max_devices,
                            current_devices: deviceCount
                        });
                    }
                }
            }

            // Register or update device
            if (device_id) {
                await this.registerDevice(user.id, entitlement.id, device_id, device_name);
            }

            // Generate session token
            const sessionToken = await this.createSession(user.id);

            // Generate entitlement token
            const entitlementToken = await this.generateEntitlementToken(
                user.id,
                entitlement,
                device_id
            );

            res.json({
                success: true,
                session_token: sessionToken,
                entitlement_token: entitlementToken,
                user: {
                    id: user.id,
                    email: user.email
                },
                entitlement: {
                    id: entitlement.id,
                    plan: entitlement.plan,
                    features: entitlement.features,
                    expires_at: entitlement.expires_at
                }
            });
        } catch (error) {
            console.error('Login error:', error);
            res.status(500).json({ error: `Login failed: ${error.message}` });
        }
    }

    /**
     * Refresh session token
     * POST /api/auth/refresh
     */
    async refresh(req, res) {
        try {
            const { session_token } = req.body;

            if (!session_token) {
                return res.status(400).json({ error: 'Session token is required' });
            }

            // Verify session token
            const session = await this.verifySession(session_token);
            if (!session) {
                return res.status(401).json({ error: 'Invalid session token' });
            }

            // Get user and entitlement
            const user = await this.getUser(session.user_id);
            const entitlement = await this.getActiveEntitlement(user.id);

            if (!entitlement) {
                return res.status(403).json({ error: 'No active entitlement found' });
            }

            // Generate new entitlement token
            const entitlementToken = await this.generateEntitlementToken(
                user.id,
                entitlement,
                req.body.device_id
            );

            res.json({
                success: true,
                entitlement_token: entitlementToken,
                entitlement: {
                    id: entitlement.id,
                    plan: entitlement.plan,
                    features: entitlement.features,
                    expires_at: entitlement.expires_at
                }
            });
        } catch (error) {
            console.error('Refresh error:', error);
            res.status(500).json({ error: `Refresh failed: ${error.message}` });
        }
    }

    /**
     * Get current user entitlements
     * GET /api/entitlements/current
     */
    async getCurrentEntitlements(req, res) {
        try {
            const userId = req.user.id;

            const entitlements = await this.getUserEntitlements(userId);
            const activeEntitlement = entitlements.find(e => e.status === 'active' && 
                (!e.expires_at || new Date(e.expires_at) > new Date()));

            res.json({
                entitlements: entitlements,
                active: activeEntitlement
            });
        } catch (error) {
            console.error('Get entitlements error:', error);
            res.status(500).json({ error: `Failed to get entitlements: ${error.message}` });
        }
    }

    /**
     * Get signed entitlement token
     * POST /api/entitlements/token
     */
    async getEntitlementToken(req, res) {
        try {
            const userId = req.user.id;
            const { device_id } = req.body;

            const entitlement = await this.getActiveEntitlement(userId);
            if (!entitlement) {
                return res.status(403).json({ error: 'No active entitlement found' });
            }

            const token = await this.generateEntitlementToken(userId, entitlement, device_id);

            res.json({
                success: true,
                token: token
            });
        } catch (error) {
            console.error('Get token error:', error);
            res.status(500).json({ error: `Failed to generate token: ${error.message}` });
        }
    }

    /**
     * List user's devices
     * GET /api/devices
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
     * Register new device
     * POST /api/devices/register
     */
    async registerDevice(req, res) {
        try {
            const userId = req.user.id;
            const { device_id, device_name } = req.body;

            if (!device_id) {
                return res.status(400).json({ error: 'Device ID is required' });
            }

            const entitlement = await this.getActiveEntitlement(userId);
            if (!entitlement) {
                return res.status(403).json({ error: 'No active entitlement found' });
            }

            // Check device limit
            const deviceCount = await this.getDeviceCount(userId, entitlement.id);
            if (deviceCount >= entitlement.max_devices) {
                const existingDevice = await this.getDevice(userId, device_id);
                if (!existingDevice) {
                    return res.status(403).json({ 
                        error: 'Device limit reached',
                        max_devices: entitlement.max_devices
                    });
                }
            }

            const device = await this.registerDevice(userId, entitlement.id, device_id, device_name);

            res.json({
                success: true,
                device: device
            });
        } catch (error) {
            console.error('Register device error:', error);
            res.status(500).json({ error: `Failed to register device: ${error.message}` });
        }
    }

    /**
     * Revoke device
     * DELETE /api/devices/:id
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
     * Check device status
     * GET /api/devices/:id/status
     */
    async getDeviceStatus(req, res) {
        try {
            const userId = req.user.id;
            const deviceId = req.params.id;

            const device = await this.getDevice(userId, deviceId);
            if (!device) {
                return res.status(404).json({ error: 'Device not found' });
            }

            res.json({
                device: device,
                is_active: true,
                last_seen: device.last_seen
            });
        } catch (error) {
            console.error('Get device status error:', error);
            res.status(500).json({ error: `Failed to get device status: ${error.message}` });
        }
    }

    // Helper methods

    async getActiveEntitlement(userId) {
        const client = await this.db.connect();
        try {
            const result = await client.query(
                `SELECT * FROM entitlements
                 WHERE user_id = $1
                   AND status = 'active'
                   AND (expires_at IS NULL OR expires_at > NOW())
                 ORDER BY created_at DESC
                 LIMIT 1`,
                [userId]
            );

            return result.rows[0] || null;
        } finally {
            client.release();
        }
    }

    async getUserEntitlements(userId) {
        const client = await this.db.connect();
        try {
            const result = await client.query(
                'SELECT * FROM entitlements WHERE user_id = $1 ORDER BY created_at DESC',
                [userId]
            );
            return result.rows;
        } finally {
            client.release();
        }
    }

    async generateEntitlementToken(userId, entitlement, deviceId) {
        const now = Math.floor(Date.now() / 1000);
        const lifetime = this.TOKEN_LIFETIMES[entitlement.plan] || this.TOKEN_LIFETIMES.monthly;
        const expiresAt = now + lifetime;

        const payload = {
            sub: userId,
            product: entitlement.product_id,
            features: entitlement.features || [],
            plan: entitlement.plan,
            max_devices: entitlement.max_devices,
            device_id: deviceId || null, // Device binding
            issued_at: now,
            expires_at: expiresAt,
            nonce: this.tokenSigner.generateNonce(), // Replay attack prevention
            iat: now, // Issued at
            jti: this.tokenSigner.generateNonce() // JWT ID for revocation
        };

        const signedToken = this.tokenSigner.signEntitlementToken(payload);
        
        // Store token ID for revocation tracking (optional)
        // In production, store jti in database for revocation list
        
        return signedToken;
    }
    
    async checkTokenRevocation(tokenJti) {
        /**Check if token is in revocation list*/
        const client = await this.db.connect();
        try {
            const result = await client.query(
                'SELECT * FROM revoked_tokens WHERE token_hash = $1',
                [tokenJti]
            );
            return result.rows.length > 0;
        } finally {
            client.release();
        }
    }
    
    async revokeToken(tokenJti, userId, reason) {
        /**Revoke a token by adding to revocation list*/
        const client = await this.db.connect();
        try {
            await client.query(
                `INSERT INTO revoked_tokens (token_hash, user_id, reason, revoked_at)
                 VALUES ($1, $2, $3, NOW())`,
                [tokenJti, userId, reason || 'Revoked by user']
            );
        } finally {
            client.release();
        }
    }
    
    async validateEntitlementToken(token) {
        /**Validate entitlement token signature and check revocation*/
        try {
            // Verify signature
            if (!this.tokenSigner.verifyEntitlementToken(token)) {
                return { valid: false, reason: 'Invalid signature' };
            }
            
            // Check revocation
            const jti = token.jti;
            if (jti && await this.checkTokenRevocation(jti)) {
                return { valid: false, reason: 'Token revoked' };
            }
            
            // Check expiry
            const expiresAt = token.expires_at;
            if (expiresAt && Math.floor(Date.now() / 1000) >= expiresAt) {
                return { valid: false, reason: 'Token expired' };
            }
            
            return { valid: true };
        } catch (error) {
            return { valid: false, reason: `Validation error: ${error.message}` };
        }
    }

    async createSession(userId) {
        const client = await this.db.connect();
        try {
            const token = crypto.randomBytes(32).toString('hex');
            const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
            const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

            await client.query(
                `INSERT INTO sessions (user_id, token_hash, expires_at)
                 VALUES ($1, $2, $3)`,
                [userId, tokenHash, expiresAt]
            );

            return token;
        } finally {
            client.release();
        }
    }

    async verifySession(sessionToken) {
        const client = await this.db.connect();
        try {
            const tokenHash = crypto.createHash('sha256').update(sessionToken).digest('hex');
            const result = await client.query(
                `SELECT * FROM sessions
                 WHERE token_hash = $1 AND expires_at > NOW()`,
                [tokenHash]
            );

            if (result.rows.length === 0) {
                return null;
            }

            return result.rows[0];
        } finally {
            client.release();
        }
    }

    async registerDevice(userId, entitlementId, deviceId, deviceName) {
        const client = await this.db.connect();
        try {
            // Check if device already exists
            const existing = await client.query(
                'SELECT * FROM devices WHERE user_id = $1 AND device_id = $2',
                [userId, deviceId]
            );

            if (existing.rows.length > 0) {
                // Update existing device
                const result = await client.query(
                    `UPDATE devices
                     SET entitlement_id = $1, device_name = $2, last_seen = NOW()
                     WHERE user_id = $3 AND device_id = $4
                     RETURNING *`,
                    [entitlementId, deviceName, userId, deviceId]
                );
                return result.rows[0];
            } else {
                // Insert new device
                const result = await client.query(
                    `INSERT INTO devices (user_id, entitlement_id, device_id, device_name, last_seen)
                     VALUES ($1, $2, $3, $4, NOW())
                     RETURNING *`,
                    [userId, entitlementId, deviceId, deviceName]
                );
                return result.rows[0];
            }
        } finally {
            client.release();
        }
    }

    async getDevice(userId, deviceId) {
        const client = await this.db.connect();
        try {
            const result = await client.query(
                'SELECT * FROM devices WHERE user_id = $1 AND device_id = $2',
                [userId, deviceId]
            );
            return result.rows[0] || null;
        } finally {
            client.release();
        }
    }

    async getDeviceCount(userId, entitlementId) {
        const client = await this.db.connect();
        try {
            const result = await client.query(
                `SELECT COUNT(*) as count FROM devices
                 WHERE user_id = $1 AND entitlement_id = $2`,
                [userId, entitlementId]
            );
            return parseInt(result.rows[0].count, 10);
        } finally {
            client.release();
        }
    }

    async getUser(userId) {
        const client = await this.db.connect();
        try {
            const result = await client.query('SELECT * FROM users WHERE id = $1', [userId]);
            return result.rows[0];
        } finally {
            client.release();
        }
    }
}

module.exports = EntitlementAPI;
