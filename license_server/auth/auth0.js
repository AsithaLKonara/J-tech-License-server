/**
 * Auth0 Authentication Integration
 * Handles JWT verification, user creation/retrieval, and authentication middleware
 */

const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');
const { Pool } = require('pg');

class Auth0Manager {
    constructor(config, dbPool) {
        this.config = config;
        this.db = dbPool;
        
        // Auth0 configuration
        this.domain = config.AUTH0_DOMAIN;
        this.audience = config.AUTH0_AUDIENCE;
        this.issuer = `https://${config.AUTH0_DOMAIN}/`;
        
        // Initialize JWKS client for token verification
        this.jwksClient = jwksClient({
            jwksUri: `https://${config.AUTH0_DOMAIN}/.well-known/jwks.json`,
            cache: true,
            cacheMaxAge: 86400000 // 24 hours
        });
    }

    /**
     * Get signing key for JWT verification
     */
    async getSigningKey(kid) {
        return new Promise((resolve, reject) => {
            this.jwksClient.getSigningKey(kid, (err, key) => {
                if (err) {
                    return reject(err);
                }
                const signingKey = key.getPublicKey();
                resolve(signingKey);
            });
        });
    }

    /**
     * Verify Auth0 JWT token
     */
    async verifyAuth0Token(token) {
        try {
            // Decode token to get kid (key ID)
            const decoded = jwt.decode(token, { complete: true });
            if (!decoded || !decoded.header || !decoded.header.kid) {
                throw new Error('Invalid token format');
            }

            // Get signing key
            const signingKey = await this.getSigningKey(decoded.header.kid);

            // Verify token
            const verified = jwt.verify(token, signingKey, {
                audience: this.audience,
                issuer: this.issuer,
                algorithms: ['RS256']
            });

            return verified;
        } catch (error) {
            throw new Error(`Token verification failed: ${error.message}`);
        }
    }

    /**
     * Get or create user from Auth0 user data
     */
    async getOrCreateUser(auth0User) {
        const client = await this.db.connect();
        try {
            const { sub: auth0Id, email } = auth0User;

            // Check if user exists
            let result = await client.query(
                'SELECT * FROM users WHERE auth0_id = $1 OR email = $2',
                [auth0Id, email]
            );

            if (result.rows.length > 0) {
                // User exists, update auth0_id if needed
                const user = result.rows[0];
                if (!user.auth0_id && auth0Id) {
                    await client.query(
                        'UPDATE users SET auth0_id = $1, updated_at = NOW() WHERE id = $2',
                        [auth0Id, user.id]
                    );
                    user.auth0_id = auth0Id;
                }
                return user;
            }

            // Create new user
            result = await client.query(
                `INSERT INTO users (email, auth0_id, created_at, updated_at)
                 VALUES ($1, $2, NOW(), NOW())
                 RETURNING *`,
                [email, auth0Id]
            );

            return result.rows[0];
        } finally {
            client.release();
        }
    }

    /**
     * Express middleware to require authentication
     */
    requireAuth() {
        return async (req, res, next) => {
            try {
                // Get token from Authorization header
                const authHeader = req.headers.authorization;
                if (!authHeader || !authHeader.startsWith('Bearer ')) {
                    return res.status(401).json({ error: 'No authorization token provided' });
                }

                const token = authHeader.substring(7); // Remove 'Bearer ' prefix

                // Verify token
                const decoded = await this.verifyAuth0Token(token);

                // Get or create user
                const user = await this.getOrCreateUser(decoded);

                // Attach user to request
                req.user = user;
                req.auth0Token = decoded;

                next();
            } catch (error) {
                return res.status(401).json({ error: `Authentication failed: ${error.message}` });
            }
        };
    }

    /**
     * Optional authentication middleware (doesn't fail if no token)
     */
    optionalAuth() {
        return async (req, res, next) => {
            try {
                const authHeader = req.headers.authorization;
                if (authHeader && authHeader.startsWith('Bearer ')) {
                    const token = authHeader.substring(7);
                    const decoded = await this.verifyAuth0Token(token);
                    const user = await this.getOrCreateUser(decoded);
                    req.user = user;
                    req.auth0Token = decoded;
                }
                next();
            } catch (error) {
                // Continue without authentication
                next();
            }
        };
    }

    /**
     * Extract user from token (for internal use)
     */
    async getUserFromToken(token) {
        const decoded = await this.verifyAuth0Token(token);
        return await this.getOrCreateUser(decoded);
    }
}

module.exports = Auth0Manager;
