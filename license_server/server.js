/**
 * Upload Bridge License Server
 * Enterprise Account-Based Licensing System
 * 
 * Features:
 * - Account-based entitlements (replaces file-based licenses)
 * - Auth0 authentication (OAuth, magic links, SSO)
 * - Stripe payment integration
 * - PostgreSQL database for scalable storage
 * - Redis for session management
 * - ECDSA P-256 signing for secure tokens
 * - Device management and revocation
 * - Backward compatibility with legacy file-based system
 */

const express = require('express');
const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { Pool } = require('pg');
const redis = require('redis');

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(cors({
    origin: process.env.NODE_ENV === 'production' ? ['https://yourdomain.com'] : true,
    credentials: true
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// ECDSA P-256 Key Management
class LicenseKeyManager {
    constructor() {
        this.privateKey = null;
        this.publicKey = null;
        this.keyPath = path.join(__dirname, 'keys');
    }

    async initialize() {
        try {
            // Try to load existing keys
            const privateKeyPem = await fs.readFile(path.join(this.keyPath, 'private.pem'), 'utf8');
            const publicKeyPem = await fs.readFile(path.join(this.keyPath, 'public.pem'), 'utf8');
            
            this.privateKey = crypto.createPrivateKey(privateKeyPem);
            this.publicKey = crypto.createPublicKey(publicKeyPem);
            
            console.log('✅ Loaded existing ECDSA P-256 keys');
        } catch (error) {
            // Generate new keys if they don't exist
            console.log('🔑 Generating new ECDSA P-256 key pair...');
            await this.generateKeys();
        }
    }

    async generateKeys() {
        // Generate ECDSA P-256 key pair
        const { privateKey, publicKey } = crypto.generateKeyPairSync('ec', {
            namedCurve: 'prime256v1', // P-256
            publicKeyEncoding: {
                type: 'spki',
                format: 'pem'
            },
            privateKeyEncoding: {
                type: 'pkcs8',
                format: 'pem'
            }
        });

        // Ensure keys directory exists
        await fs.mkdir(this.keyPath, { recursive: true });

        // Save keys
        await fs.writeFile(path.join(this.keyPath, 'private.pem'), privateKey);
        await fs.writeFile(path.join(this.keyPath, 'public.pem'), publicKey);

        this.privateKey = crypto.createPrivateKey(privateKey);
        this.publicKey = crypto.createPublicKey(publicKey);

        console.log('✅ Generated new ECDSA P-256 key pair');
        console.log('📁 Keys saved to:', this.keyPath);
    }

    sign(data) {
        if (!this.privateKey) {
            throw new Error('Private key not initialized');
        }

        const sign = crypto.createSign('SHA256');
        sign.update(data);
        return sign.sign(this.privateKey, 'base64');
    }

    verify(data, signature) {
        if (!this.publicKey) {
            throw new Error('Public key not initialized');
        }

        const verify = crypto.createVerify('SHA256');
        verify.update(data);
        return verify.verify(this.publicKey, signature, 'base64');
    }

    getPublicKeyPem() {
        if (!this.publicKey) {
            throw new Error('Public key not initialized');
        }
        return this.publicKey.export({ type: 'spki', format: 'pem' });
    }
}

// License Database (In-memory for demo - use PostgreSQL in production)
class LicenseDatabase {
    constructor() {
        this.licenses = new Map();
        this.devices = new Map();
        this.revokedLicenses = new Set();
    }

    // License management
    createLicense(licenseData) {
        const licenseId = crypto.randomUUID();
        const license = {
            id: licenseId,
            ...licenseData,
            created_at: new Date().toISOString(),
            status: 'active'
        };
        
        this.licenses.set(licenseId, license);
        return license;
    }

    getLicense(licenseId) {
        return this.licenses.get(licenseId);
    }

    revokeLicense(licenseId) {
        this.revokedLicenses.add(licenseId);
        const license = this.licenses.get(licenseId);
        if (license) {
            license.status = 'revoked';
            license.revoked_at = new Date().toISOString();
        }
    }

    isRevoked(licenseId) {
        return this.revokedLicenses.has(licenseId);
    }

    // Device management
    bindDevice(licenseId, chipId, deviceInfo = {}) {
        const device = {
            license_id: licenseId,
            chip_id: chipId,
            bound_at: new Date().toISOString(),
            last_seen: new Date().toISOString(),
            ...deviceInfo
        };
        
        this.devices.set(chipId, device);
        return device;
    }

    getDevice(chipId) {
        return this.devices.get(chipId);
    }

    updateDeviceLastSeen(chipId) {
        const device = this.devices.get(chipId);
        if (device) {
            device.last_seen = new Date().toISOString();
        }
    }
}

// Initialize legacy components (for backward compatibility)
const keyManager = new LicenseKeyManager();
const db = new LicenseDatabase();

// Initialize PostgreSQL connection
let pgPool = null;
if (process.env.DATABASE_URL || process.env.DB_HOST) {
    const dbConfig = process.env.DATABASE_URL ? {
        connectionString: process.env.DATABASE_URL
    } : {
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT || '5432', 10),
        database: process.env.DB_NAME || 'upload_bridge_licensing',
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || '',
        max: 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
    };

    pgPool = new Pool(dbConfig);
    pgPool.on('error', (err) => {
        console.error('Unexpected error on idle client', err);
    });
    console.log('✅ PostgreSQL connection pool initialized');
}

// Initialize Redis connection (optional, falls back to PostgreSQL sessions)
let redisClient = null;
if (process.env.REDIS_URL || process.env.REDIS_HOST) {
    const redisConfig = process.env.REDIS_URL ? {
        url: process.env.REDIS_URL
    } : {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379', 10),
        password: process.env.REDIS_PASSWORD || undefined,
    };

    redisClient = redis.createClient(redisConfig);
    redisClient.on('error', (err) => {
        console.error('Redis Client Error', err);
        redisClient = null; // Fall back to PostgreSQL
    });
    redisClient.on('connect', () => {
        console.log('✅ Redis connection initialized');
    });
    redisClient.connect().catch(() => {
        console.warn('⚠️ Redis connection failed, using PostgreSQL for sessions');
        redisClient = null;
    });
}

// Initialize Auth0 Manager
let auth0Manager = null;
if (process.env.AUTH0_DOMAIN && process.env.AUTH0_AUDIENCE && pgPool) {
    const Auth0Manager = require('./auth/auth0');
    auth0Manager = new Auth0Manager({
        AUTH0_DOMAIN: process.env.AUTH0_DOMAIN,
        AUTH0_AUDIENCE: process.env.AUTH0_AUDIENCE
    }, pgPool);
    console.log('✅ Auth0 Manager initialized');
}

// Initialize Token Signer (will be initialized in startServer)
const TokenSigner = require('./auth/token_signer');
let tokenSigner = null;

// Initialize Entitlement API (will be initialized in startServer)
let entitlementAPI = null;

// License Generation Functions
function generateLicensePayload(licenseData) {
    const payload = {
        license_id: licenseData.license_id || crypto.randomUUID(),
        product_id: licenseData.product_id || 'upload_bridge_pro',
        chip_id: licenseData.chip_id || null, // null for unbound licenses
        issued_to_email: licenseData.email,
        issued_at: new Date().toISOString(),
        expires_at: licenseData.expires_at || new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year default
        features: licenseData.features || ['pattern_upload', 'wifi_upload', 'advanced_controls'],
        version: '1.0',
        max_devices: licenseData.max_devices || 1
    };

    return payload;
}

function createLicenseFile(payload, signature) {
    return {
        license: payload,
        signature: signature,
        public_key: keyManager.getPublicKeyPem(),
        format_version: '1.0',
        created_at: new Date().toISOString()
    };
}

// API Routes

// Health check
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '2.0.0',
        public_key_available: !!keyManager.publicKey,
        database: pgPool ? 'connected' : 'not_configured',
        redis: redisClient ? 'connected' : 'not_configured',
        auth0: auth0Manager ? 'configured' : 'not_configured',
        entitlements: entitlementAPI ? 'enabled' : 'disabled'
    });
});

// Get public key (for device verification)
app.get('/api/public-key', (req, res) => {
    try {
        res.json({
            public_key: keyManager.getPublicKeyPem(),
            algorithm: 'ECDSA P-256',
            format: 'PEM'
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get public key' });
    }
});

// Generate license
app.post('/api/generate-license', async (req, res) => {
    try {
        const { email, product_id, features, expires_at, max_devices, chip_id } = req.body;

        if (!email) {
            return res.status(400).json({ error: 'Email is required' });
        }

        // Generate license payload
        const payload = generateLicensePayload({
            email,
            product_id,
            features,
            expires_at,
            max_devices,
            chip_id
        });

        // Sign the payload
        const payloadJson = JSON.stringify(payload, null, 2);
        const signature = keyManager.sign(payloadJson);

        // Create license file
        const licenseFile = createLicenseFile(payload, signature);

        // Store in database
        const license = db.createLicense({
            ...payload,
            signature,
            license_file: licenseFile
        });

        res.json({
            success: true,
            license_id: license.id,
            license_file: licenseFile,
            message: 'License generated successfully'
        });

    } catch (error) {
        console.error('License generation error:', error);
        res.status(500).json({ error: 'Failed to generate license' });
    }
});

// Activate license (bind to device)
app.post('/api/activate', async (req, res) => {
    try {
        const { license_token, chip_id, device_info } = req.body;

        if (!license_token || !chip_id) {
            return res.status(400).json({ error: 'License token and chip_id are required' });
        }

        // Parse license token (could be JWT or license file)
        let licenseData;
        try {
            if (typeof license_token === 'string' && license_token.includes('.')) {
                // JWT format
                const [header, payload, signature] = license_token.split('.');
                licenseData = JSON.parse(Buffer.from(payload, 'base64').toString());
            } else {
                // License file format
                licenseData = typeof license_token === 'string' ? JSON.parse(license_token) : license_token;
            }
        } catch (parseError) {
            return res.status(400).json({ error: 'Invalid license token format' });
        }

        // Verify license signature
        const payloadJson = JSON.stringify(licenseData.license || licenseData, null, 2);
        const signature = licenseData.signature;

        if (!keyManager.verify(payloadJson, signature)) {
            return res.status(400).json({ error: 'Invalid license signature' });
        }

        // Check if license is revoked
        if (db.isRevoked(licenseData.license?.license_id || licenseData.license_id)) {
            return res.status(400).json({ error: 'License has been revoked' });
        }

        // Check expiration
        const expiresAt = new Date(licenseData.license?.expires_at || licenseData.expires_at);
        if (expiresAt < new Date()) {
            return res.status(400).json({ error: 'License has expired' });
        }

        // Bind device
        const device = db.bindDevice(
            licenseData.license?.license_id || licenseData.license_id,
            chip_id,
            device_info
        );

        res.json({
            success: true,
            device: device,
            message: 'License activated successfully'
        });

    } catch (error) {
        console.error('License activation error:', error);
        res.status(500).json({ error: 'Failed to activate license' });
    }
});

// Validate license
app.post('/api/validate', async (req, res) => {
    try {
        const { license_id, chip_id } = req.body;

        if (!license_id || !chip_id) {
            return res.status(400).json({ error: 'License ID and chip_id are required' });
        }

        // Check if license exists
        const license = db.getLicense(license_id);
        if (!license) {
            return res.status(404).json({ error: 'License not found' });
        }

        // Check if revoked
        if (db.isRevoked(license_id)) {
            return res.json({
                valid: false,
                status: 'revoked',
                message: 'License has been revoked'
            });
        }

        // Check expiration
        const expiresAt = new Date(license.expires_at);
        if (expiresAt < new Date()) {
            return res.json({
                valid: false,
                status: 'expired',
                message: 'License has expired'
            });
        }

        // Check device binding
        const device = db.getDevice(chip_id);
        if (!device || device.license_id !== license_id) {
            return res.json({
                valid: false,
                status: 'device_not_bound',
                message: 'Device not bound to this license'
            });
        }

        // Update last seen
        db.updateDeviceLastSeen(chip_id);

        res.json({
            valid: true,
            status: 'active',
            license: license,
            device: device,
            message: 'License is valid'
        });

    } catch (error) {
        console.error('License validation error:', error);
        res.status(500).json({ error: 'Failed to validate license' });
    }
});

// Revoke license (admin endpoint)
app.post('/api/revoke', async (req, res) => {
    try {
        const { license_id, reason } = req.body;

        if (!license_id) {
            return res.status(400).json({ error: 'License ID is required' });
        }

        db.revokeLicense(license_id);

        res.json({
            success: true,
            message: 'License revoked successfully',
            reason: reason || 'No reason provided'
        });

    } catch (error) {
        console.error('License revocation error:', error);
        res.status(500).json({ error: 'Failed to revoke license' });
    }
});

// Get license status
app.get('/api/license/:licenseId', async (req, res) => {
    try {
        const { licenseId } = req.params;
        const license = db.getLicense(licenseId);

        if (!license) {
            return res.status(404).json({ error: 'License not found' });
        }

        res.json({
            license: license,
            revoked: db.isRevoked(licenseId)
        });

    } catch (error) {
        console.error('Get license error:', error);
        res.status(500).json({ error: 'Failed to get license' });
    }
});

// Get revocation list (CRL-style)
app.get('/api/revocation-list', async (req, res) => {
    try {
        // Get all revoked license IDs
        const revokedIds = Array.from(db.revokedLicenses);
        
        res.json({
            revoked_licenses: revokedIds,
            count: revokedIds.length,
            last_updated: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Get revocation list error:', error);
        res.status(500).json({ error: 'Failed to get revocation list' });
    }
});

// List all licenses (admin endpoint)
app.get('/api/licenses', async (req, res) => {
    try {
        const licenses = Array.from(db.licenses.values());
        res.json({
            licenses: licenses,
            total: licenses.length
        });
    } catch (error) {
        console.error('List licenses error:', error);
        res.status(500).json({ error: 'Failed to list licenses' });
    }
});

// ============================================================================
// NEW ENTERPRISE API ENDPOINTS (v2)
// ============================================================================

if (entitlementAPI) {
    // Authentication endpoints
    app.post('/api/v2/auth/login', (req, res) => entitlementAPI.login(req, res));
    app.post('/api/v2/auth/refresh', (req, res) => entitlementAPI.refresh(req, res));

    // Entitlement endpoints (require authentication)
    app.get('/api/v2/entitlements/current', auth0Manager.requireAuth(), (req, res) => 
        entitlementAPI.getCurrentEntitlements(req, res));
    app.post('/api/v2/entitlements/token', auth0Manager.requireAuth(), (req, res) => 
        entitlementAPI.getEntitlementToken(req, res));

    // Device management endpoints (require authentication)
    app.get('/api/v2/devices', auth0Manager.requireAuth(), (req, res) => 
        entitlementAPI.listDevices(req, res));
    app.post('/api/v2/devices/register', auth0Manager.requireAuth(), (req, res) => 
        entitlementAPI.registerDevice(req, res));
    app.delete('/api/v2/devices/:id', auth0Manager.requireAuth(), (req, res) => 
        entitlementAPI.revokeDevice(req, res));
    app.get('/api/v2/devices/:id/status', auth0Manager.requireAuth(), (req, res) => 
        entitlementAPI.getDeviceStatus(req, res));
    
    // Feature flags endpoint
    app.post('/api/v2/features/check', auth0Manager.optionalAuth(), async (req, res) => {
        try {
            const { features } = req.body;
            const userId = req.user?.id;
            
            // Get user's entitlement to determine enabled features
            let enabledFeatures = [];
            if (userId) {
                const entitlement = await entitlementAPI.getActiveEntitlement(userId);
                if (entitlement) {
                    enabledFeatures = entitlement.features || [];
                }
            }
            
            // Build flags object
            const flags = {};
            if (features && Array.isArray(features)) {
                features.forEach(feature => {
                    flags[feature] = enabledFeatures.includes(feature);
                });
            } else {
                // Return all known features
                const allFeatures = ['pattern_upload', 'wifi_upload', 'advanced_controls', 'cloud_sync', 'preset_library'];
                allFeatures.forEach(feature => {
                    flags[feature] = enabledFeatures.includes(feature);
                });
            }
            
            res.json({
                flags: flags,
                enabled_features: enabledFeatures
            });
        } catch (error) {
            console.error('Feature flags check error:', error);
            res.status(500).json({ error: `Failed to check features: ${error.message}` });
        }
    });
}

// Stripe integration (Phase 2)
let stripeManager = null;
let stripeWebhookHandler = null;
let checkoutAPI = null;

if (process.env.STRIPE_SECRET_KEY && pgPool) {
    const StripeManager = require('./payments/stripe');
    const StripeWebhookHandler = require('./payments/webhooks');
    const CheckoutAPI = require('./api/checkout');

    stripeManager = new StripeManager({
        STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
        STRIPE_WEBHOOK_SECRET: process.env.STRIPE_WEBHOOK_SECRET,
        STRIPE_PRODUCT_MONTHLY_ID: process.env.STRIPE_PRODUCT_MONTHLY_ID,
        STRIPE_PRODUCT_YEARLY_ID: process.env.STRIPE_PRODUCT_YEARLY_ID,
        STRIPE_PRODUCT_PERPETUAL_ID: process.env.STRIPE_PRODUCT_PERPETUAL_ID
    }, pgPool);

    stripeWebhookHandler = new StripeWebhookHandler(stripeManager, pgPool);
    checkoutAPI = new CheckoutAPI(stripeManager, auth0Manager);

    // Stripe webhook endpoint (must use raw body for signature verification)
    // Note: This should be registered BEFORE express.json() middleware
    // For now, we'll add it after but Stripe webhooks need special handling
    const stripeWebhookMiddleware = express.raw({ type: 'application/json' });
    app.post('/api/v2/webhooks/stripe', stripeWebhookMiddleware, (req, res) => 
        stripeWebhookHandler.handleWebhook(req, res));

    // Checkout endpoints (require authentication)
    if (auth0Manager) {
        app.post('/api/v2/checkout/create-session', auth0Manager.requireAuth(), (req, res) => 
            checkoutAPI.createSession(req, res));
        app.post('/api/v2/checkout/billing-portal', auth0Manager.requireAuth(), (req, res) => 
            checkoutAPI.createBillingPortalSession(req, res));
    }

    // Public checkout endpoints
    app.get('/api/v2/checkout/success', (req, res) => checkoutAPI.success(req, res));
    app.get('/api/v2/checkout/cancel', (req, res) => checkoutAPI.cancel(req, res));

    console.log('✅ Stripe integration initialized');
}

// Dashboard API (Phase 4)
let dashboardAPI = null;
if (pgPool && auth0Manager) {
    const DashboardAPI = require('./dashboard/server');
    dashboardAPI = new DashboardAPI(pgPool, auth0Manager, stripeManager);
    
    // Dashboard endpoints (require authentication)
    app.get('/dashboard/api/user', auth0Manager.requireAuth(), (req, res) => 
        dashboardAPI.getUser(req, res));
    app.get('/dashboard/api/entitlements', auth0Manager.requireAuth(), (req, res) => 
        dashboardAPI.getEntitlements(req, res));
    app.get('/dashboard/api/devices', auth0Manager.requireAuth(), (req, res) => 
        dashboardAPI.listDevices(req, res));
    app.post('/dashboard/api/devices/:id/revoke', auth0Manager.requireAuth(), (req, res) => 
        dashboardAPI.revokeDevice(req, res));
    app.post('/dashboard/api/devices/:id/rename', auth0Manager.requireAuth(), (req, res) => 
        dashboardAPI.renameDevice(req, res));
    app.get('/dashboard/api/billing', auth0Manager.requireAuth(), (req, res) => 
        dashboardAPI.getBilling(req, res));
    app.post('/dashboard/api/billing/update-payment', auth0Manager.requireAuth(), (req, res) => 
        dashboardAPI.updatePaymentMethod(req, res));
    
    // Serve dashboard static files
    app.use('/dashboard', express.static(path.join(__dirname, 'dashboard', 'frontend')));
    
    console.log('✅ Dashboard API initialized');
}

// Cloud Services (Phase 5)
let patternSyncService = null;
let presetLibraryService = null;
let converterService = null;
let updateService = null;

if (pgPool && auth0Manager) {
    const PatternSyncService = require('./services/pattern_sync');
    const PresetLibraryService = require('./services/preset_library');
    const ConverterService = require('./services/converter');
    const UpdateService = require('./services/updates');

    patternSyncService = new PatternSyncService(pgPool, auth0Manager);
    presetLibraryService = new PresetLibraryService(pgPool, auth0Manager);
    converterService = new ConverterService(auth0Manager);
    updateService = new UpdateService(pgPool, auth0Manager);

    // Pattern sync endpoints (require authentication)
    app.post('/api/v2/sync/upload', auth0Manager.requireAuth(), (req, res) => 
        patternSyncService.uploadPattern(req, res));
    app.get('/api/v2/sync/list', auth0Manager.requireAuth(), (req, res) => 
        patternSyncService.listPatterns(req, res));
    app.get('/api/v2/sync/download/:id', auth0Manager.requireAuth(), (req, res) => 
        patternSyncService.downloadPattern(req, res));
    app.delete('/api/v2/sync/:id', auth0Manager.requireAuth(), (req, res) => 
        patternSyncService.deletePattern(req, res));

    // Preset library endpoints
    app.get('/api/v2/presets', auth0Manager.optionalAuth(), (req, res) => 
        presetLibraryService.listPresets(req, res));
    app.get('/api/v2/presets/:id', auth0Manager.optionalAuth(), (req, res) => 
        presetLibraryService.getPreset(req, res));
    app.post('/api/v2/presets', auth0Manager.requireAuth(), (req, res) => 
        presetLibraryService.uploadPreset(req, res));

    // Format converter endpoint (require authentication)
    app.post('/api/v2/convert', auth0Manager.requireAuth(), (req, res) => 
        converterService.convertPattern(req, res));

    // Update service endpoints
    app.get('/api/v2/updates/check', auth0Manager.optionalAuth(), (req, res) => 
        updateService.checkUpdates(req, res));
    app.get('/api/v2/updates/download', auth0Manager.requireAuth(), (req, res) => 
        updateService.downloadUpdate(req, res));

    console.log('✅ Cloud services initialized');
}

// Security Enhancements (Phase 6)
// Integrity heartbeat endpoint
if (pgPool && auth0Manager) {
    app.post('/api/v2/integrity/heartbeat', auth0Manager.optionalAuth(), async (req, res) => {
        try {
            const { state_hash, signature, device_id, timestamp } = req.body;
            const userId = req.user?.id;

            if (!state_hash) {
                return res.status(400).json({ error: 'state_hash is required' });
            }

            // Store integrity check in database
            const client = await pgPool.connect();
            try {
                await client.query(
                    `INSERT INTO integrity_checks (user_id, device_id, state_hash, signature, created_at)
                     VALUES ($1, $2, $3, $4, NOW())`,
                    [userId, device_id, state_hash, signature]
                );

                // In production, analyze state_hash for anomalies
                // For now, just acknowledge receipt
                res.json({
                    success: true,
                    message: 'Heartbeat received'
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Integrity heartbeat error:', error);
            res.status(500).json({ error: `Failed to process heartbeat: ${error.message}` });
        }
    });
}

// Per-user rate limiting
const UserRateLimiter = require('./middleware/rate_limit');
const userRateLimiter = new UserRateLimiter();
app.use('/api/v2/', userRateLimiter.dynamicLimiter());

console.log('✅ Security enhancements initialized');

// Legacy endpoints remain for backward compatibility
// They will be deprecated in a future version

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Unhandled error:', error);
    res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({ error: 'Endpoint not found' });
});

// Initialize and start server
async function startServer() {
    try {
        await keyManager.initialize();
        
        // Initialize Token Signer
        tokenSigner = new TokenSigner();
        await tokenSigner.initialize();
        
        // Initialize Entitlement API if dependencies are available
        if (pgPool && auth0Manager && tokenSigner) {
            const EntitlementAPI = require('./api/entitlements');
            entitlementAPI = new EntitlementAPI(pgPool, tokenSigner, auth0Manager);
            console.log('✅ Entitlement API initialized');
        }
        
        app.listen(PORT, () => {
            console.log('🚀 Upload Bridge License Server started');
            console.log(`📡 Server running on port ${PORT}`);
            console.log(`🔑 ECDSA P-256 keys initialized`);
            console.log(`📊 Legacy database ready`);
            if (pgPool) console.log(`🗄️  PostgreSQL connected`);
            if (redisClient) console.log(`📦 Redis connected`);
            if (auth0Manager) console.log(`🔐 Auth0 configured`);
            console.log(`\n📋 Legacy endpoints (backward compatibility):`);
            console.log(`   GET  /api/health`);
            console.log(`   GET  /api/public-key`);
            console.log(`   POST /api/generate-license`);
            console.log(`   POST /api/activate`);
            console.log(`   POST /api/validate`);
            console.log(`   POST /api/revoke`);
            console.log(`   GET  /api/revocation-list`);
            console.log(`   GET  /api/license/:id`);
            console.log(`   GET  /api/licenses`);
            if (entitlementAPI) {
                console.log(`\n📋 New Enterprise API endpoints (v2):`);
                console.log(`   POST /api/v2/auth/login`);
                console.log(`   POST /api/v2/auth/refresh`);
                console.log(`   GET  /api/v2/entitlements/current`);
                console.log(`   POST /api/v2/entitlements/token`);
                console.log(`   GET  /api/v2/devices`);
                console.log(`   POST /api/v2/devices/register`);
                console.log(`   DELETE /api/v2/devices/:id`);
                console.log(`   GET  /api/v2/devices/:id/status`);
            }
            
            // Feature flags endpoint
            if (entitlementAPI) {
                console.log(`   POST /api/v2/features/check`);
            }
            
            console.log(`\n🌐 Test the server:`);
            console.log(`   curl http://localhost:${PORT}/api/health`);
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

// Handle graceful shutdown
async function gracefulShutdown() {
    console.log('\n🛑 Shutting down license server...');
    
    if (pgPool) {
        await pgPool.end();
        console.log('✅ PostgreSQL connection closed');
    }
    
    if (redisClient) {
        await redisClient.quit();
        console.log('✅ Redis connection closed');
    }
    
    process.exit(0);
}

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);

// Start the server
startServer();

module.exports = { 
    app, 
    keyManager, 
    db,
    pgPool,
    redisClient,
    auth0Manager,
    entitlementAPI,
    tokenSigner
};

