/**
 * API Client for E2E Testing
 * Provides utilities for making API requests to the license server
 */

// Use node-fetch if available, otherwise use global fetch (Node 18+)
let fetch;
try {
    fetch = require('node-fetch');
} catch (e) {
    // Node 18+ has fetch built-in
    if (typeof globalThis.fetch === 'function') {
        fetch = globalThis.fetch;
    } else {
        throw new Error('fetch is not available. Install node-fetch or use Node.js 18+');
    }
}

const BASE_URL = process.env.LICENSE_SERVER_URL || 'http://localhost:8000';

// Logging utility
const log = {
    enabled: process.env.TEST_LOGGING !== 'false',
    request: (method, url, data) => {
        if (log.enabled) {
            console.log(`[API] ${method} ${url}`, data ? JSON.stringify(data, null, 2) : '');
        }
    },
    response: (status, data) => {
        if (log.enabled) {
            console.log(`[API] Response ${status}`, JSON.stringify(data, null, 2));
        }
    },
    error: (error) => {
        if (log.enabled) {
            console.error(`[API] Error:`, error.message);
        }
    }
};

class ApiClient {
    constructor(baseUrl = BASE_URL, options = {}) {
        this.baseUrl = baseUrl;
        this.sessionToken = null;
        this.timeout = options.timeout || 30000; // 30 seconds default
        this.retries = options.retries || 3;
        this.retryDelay = options.retryDelay || 1000; // 1 second
        this.logging = options.logging !== false;
    }

    /**
     * Make a request with retry logic
     */
    async _requestWithRetry(method, endpoint, body = null, headers = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        let lastError;
        
        for (let attempt = 1; attempt <= this.retries; attempt++) {
            try {
                if (this.logging) {
                    log.request(method, url, body);
                }
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                const requestOptions = {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                        ...headers,
                    },
                    signal: controller.signal,
                };
                
                if (body) {
                    requestOptions.body = JSON.stringify(body);
                }
                
                const response = await fetch(url, requestOptions);
                clearTimeout(timeoutId);
                
                const responseData = {
                    status: response.status,
                    data: await response.json().catch(() => ({})),
                    headers: Object.fromEntries(response.headers.entries()),
                };
                
                if (this.logging) {
                    log.response(response.status, responseData.data);
                }
                
                // Retry on 5xx errors or network errors
                if (response.status >= 500 && attempt < this.retries) {
                    await this._delay(this.retryDelay * attempt);
                    continue;
                }
                
                return responseData;
            } catch (error) {
                lastError = error;
                if (this.logging) {
                    log.error(error);
                }
                
                // Retry on network errors
                if (attempt < this.retries && (error.name === 'AbortError' || error.code === 'ECONNREFUSED')) {
                    await this._delay(this.retryDelay * attempt);
                    continue;
                }
                
                throw error;
            }
        }
        
        throw lastError || new Error('Request failed after retries');
    }
    
    /**
     * Delay helper for retries
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Make a GET request
     */
    async get(endpoint, headers = {}) {
        return this._requestWithRetry('GET', endpoint, null, headers);
    }

    /**
     * Make a POST request
     */
    async post(endpoint, body = {}, headers = {}) {
        return this._requestWithRetry('POST', endpoint, body, headers);
    }
    
    /**
     * Make a DELETE request
     */
    async delete(endpoint, headers = {}) {
        return this._requestWithRetry('DELETE', endpoint, null, headers);
    }
    
    /**
     * Make a PUT request
     */
    async put(endpoint, body = {}, headers = {}) {
        return this._requestWithRetry('PUT', endpoint, body, headers);
    }
    
    /**
     * Make parallel requests
     */
    async parallel(requests) {
        return Promise.all(requests.map(req => {
            if (req.method === 'GET') {
                return this.get(req.endpoint, req.headers);
            } else if (req.method === 'POST') {
                return this.post(req.endpoint, req.body, req.headers);
            } else if (req.method === 'DELETE') {
                return this.delete(req.endpoint, req.headers);
            } else if (req.method === 'PUT') {
                return this.put(req.endpoint, req.body, req.headers);
            }
            throw new Error(`Unsupported method: ${req.method}`);
        }));
    }

    /**
     * Login with email/password and store session token
     */
    async login(email, password, deviceId = 'TEST_DEVICE', deviceName = 'Test Device') {
        const response = await this.post('/api/v2/auth/login', {
            email,
            password,
            device_id: deviceId,
            device_name: deviceName,
        });
        if (response.status === 200 && response.data.session_token) {
            this.sessionToken = response.data.session_token;
        }
        return response;
    }

    /**
     * Login with magic link token
     */
    async loginWithMagicLink(magicLinkToken, deviceId = 'TEST_DEVICE', deviceName = 'Test Device') {
        const response = await this.post('/api/v2/auth/login', {
            magic_link_token: magicLinkToken,
            device_id: deviceId,
            device_name: deviceName,
        });
        if (response.status === 200 && response.data.session_token) {
            this.sessionToken = response.data.session_token;
        }
        return response;
    }

    /**
     * Verify magic link token (alternative endpoint)
     */
    async verifyMagicLink(magicLinkToken, deviceId = 'TEST_DEVICE', deviceName = 'Test Device') {
        return this.loginWithMagicLink(magicLinkToken, deviceId, deviceName);
    }

    /**
     * Refresh session token
     */
    async refresh(deviceId = 'TEST_DEVICE') {
        if (!this.sessionToken) {
            throw new Error('No session token available. Login first.');
        }
        const response = await this.post('/api/v2/auth/refresh', {
            session_token: this.sessionToken,
            device_id: deviceId,
        });
        if (response.status === 200 && response.data.session_token) {
            this.sessionToken = response.data.session_token;
        }
        return response;
    }

    /**
     * Logout (revoke session token)
     */
    async logout() {
        if (!this.sessionToken) {
            throw new Error('No session token available. Login first.');
        }
        const response = await this.post('/api/v2/auth/logout', {
            session_token: this.sessionToken,
        });
        if (response.status === 200) {
            this.sessionToken = null;
        }
        return response;
    }

    /**
     * Health check
     */
    async health() {
        return await this.get('/api/v2/health');
    }

    /**
     * Get license info (requires authentication)
     */
    async getLicenseInfo() {
        if (!this.sessionToken) {
            throw new Error('No session token available. Login first.');
        }
        return await this.get('/api/v2/license/info', {
            'Authorization': `Bearer ${this.sessionToken}`,
        });
    }

    /**
     * Validate license (requires authentication)
     */
    async validateLicense(entitlementToken) {
        if (!this.sessionToken) {
            throw new Error('No session token available. Login first.');
        }
        return await this.post('/api/v2/license/validate', {
            entitlement_token: entitlementToken,
        }, {
            'Authorization': `Bearer ${this.sessionToken}`,
        });
    }

    /**
     * Register device (requires authentication)
     */
    async registerDevice(deviceId, deviceName = 'Test Device') {
        if (!this.sessionToken) {
            throw new Error('No session token available. Login first.');
        }
        return await this.post('/api/v2/devices/register', {
            device_id: deviceId,
            device_name: deviceName,
        }, {
            'Authorization': `Bearer ${this.sessionToken}`,
        });
    }

    /**
     * List devices (requires authentication)
     */
    async listDevices() {
        if (!this.sessionToken) {
            throw new Error('No session token available. Login first.');
        }
        return await this.get('/api/v2/devices', {
            'Authorization': `Bearer ${this.sessionToken}`,
        });
    }

    /**
     * Delete device (requires authentication)
     */
    async deleteDevice(deviceId) {
        if (!this.sessionToken) {
            throw new Error('No session token available. Login first.');
        }
        return this.delete(`/api/v2/devices/${deviceId}`, {
            'Authorization': `Bearer ${this.sessionToken}`,
        });
    }

    /**
     * Clear session
     */
    clearSession() {
        this.sessionToken = null;
    }
}

module.exports = ApiClient;
