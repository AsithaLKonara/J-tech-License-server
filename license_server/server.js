/**
 * Upload Bridge License Server
 * ECDSA P-256 License Generation & Validation API
 * 
 * Features:
 * - ECDSA P-256 signing for compact, secure licenses
 * - Hardware-bound licensing (chip_id binding)
 * - Online/offline activation support
 * - License revocation and reassignment
 * - Trial license generation
 * - Express REST API with comprehensive endpoints
 */

const express = require('express');
const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

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

// Initialize components
const keyManager = new LicenseKeyManager();
const db = new LicenseDatabase();

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
        version: '1.0.0',
        public_key_available: !!keyManager.publicKey
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
        
        app.listen(PORT, () => {
            console.log('🚀 Upload Bridge License Server started');
            console.log(`📡 Server running on port ${PORT}`);
            console.log(`🔑 ECDSA P-256 keys initialized`);
            console.log(`📊 Database ready`);
            console.log(`\n📋 Available endpoints:`);
            console.log(`   GET  /api/health`);
            console.log(`   GET  /api/public-key`);
            console.log(`   POST /api/generate-license`);
            console.log(`   POST /api/activate`);
            console.log(`   POST /api/validate`);
            console.log(`   POST /api/revoke`);
            console.log(`   GET  /api/revocation-list`);
            console.log(`   GET  /api/license/:id`);
            console.log(`   GET  /api/licenses`);
            console.log(`\n🌐 Test the server:`);
            console.log(`   curl http://localhost:${PORT}/api/health`);
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down license server...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down license server...');
    process.exit(0);
});

// Start the server
startServer();

module.exports = { app, keyManager, db };

