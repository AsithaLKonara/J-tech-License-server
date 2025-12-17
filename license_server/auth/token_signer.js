/**
 * Token Signer for Entitlement Tokens
 * Signs entitlement tokens with ECDSA P-256 for security
 */

const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

class TokenSigner {
    constructor(keyPath = null) {
        this.keyPath = keyPath || path.join(__dirname, '..', 'keys');
        this.privateKey = null;
        this.publicKey = null;
    }

    /**
     * Initialize keys (load or generate)
     */
    async initialize() {
        try {
            const privateKeyPath = path.join(this.keyPath, 'private.pem');
            const publicKeyPath = path.join(this.keyPath, 'public.pem');

            // Try to load existing keys
            const privateKeyPem = await fs.readFile(privateKeyPath, 'utf8');
            const publicKeyPem = await fs.readFile(publicKeyPath, 'utf8');

            this.privateKey = crypto.createPrivateKey(privateKeyPem);
            this.publicKey = crypto.createPublicKey(publicKeyPem);

            console.log('✅ Loaded existing ECDSA P-256 keys for token signing');
        } catch (error) {
            // Generate new keys if they don't exist
            console.log('🔑 Generating new ECDSA P-256 key pair for token signing...');
            await this.generateKeys();
        }
    }

    /**
     * Generate new ECDSA P-256 key pair
     */
    async generateKeys() {
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

        console.log('✅ Generated new ECDSA P-256 key pair for token signing');
    }

    /**
     * Sign data with private key
     */
    sign(data) {
        if (!this.privateKey) {
            throw new Error('Private key not initialized');
        }

        const sign = crypto.createSign('SHA256');
        sign.update(data);
        return sign.sign(this.privateKey, 'base64');
    }

    /**
     * Verify signature with public key
     */
    verify(data, signature) {
        if (!this.publicKey) {
            throw new Error('Public key not initialized');
        }

        const verify = crypto.createVerify('SHA256');
        verify.update(data);
        return verify.verify(this.publicKey, signature, 'base64');
    }

    /**
     * Get public key in PEM format
     */
    getPublicKeyPem() {
        if (!this.publicKey) {
            throw new Error('Public key not initialized');
        }
        return this.publicKey.export({ type: 'spki', format: 'pem' });
    }

    /**
     * Generate nonce for token security
     */
    generateNonce() {
        return crypto.randomBytes(16).toString('hex');
    }

    /**
     * Sign entitlement token payload
     */
    signEntitlementToken(payload) {
        // Create payload JSON
        const payloadJson = JSON.stringify(payload, null, 2);
        
        // Generate nonce if not present (prevents replay attacks)
        if (!payload.nonce) {
            payload.nonce = this.generateNonce();
        }

        // Ensure device_id is included (device binding)
        if (!payload.device_id) {
            payload.device_id = null; // Will be set by client
        }

        // Sign the payload
        const signature = this.sign(payloadJson);

        return {
            ...payload,
            sig: signature,
            issued_at: Math.floor(Date.now() / 1000),
            jti: this.generateNonce() // JWT ID for revocation tracking
        };
    }

    /**
     * Verify entitlement token signature
     */
    verifyEntitlementToken(token) {
        if (!token.sig) {
            return false;
        }

        // Create payload copy without signature
        const payload = { ...token };
        delete payload.sig;

        const payloadJson = JSON.stringify(payload, null, 2);
        return this.verify(payloadJson, token.sig);
    }
}

module.exports = TokenSigner;
