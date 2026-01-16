/**
 * Security Tests
 * 
 * Tests for security vulnerabilities including:
 * - SQL Injection
 * - XSS Protection
 * - CSRF Protection
 * - Rate Limiting
 * - Authentication Bypass
 */

const BASE_URL = process.env.API_URL || process.env.BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v2`;

// Simple test framework
let tests = [];
let passed = 0;
let failed = 0;

function test(name, fn) {
    tests.push({ name, fn });
}

async function runTests() {
    console.log('Running Security Tests...\n');
    
    for (const { name, fn } of tests) {
        try {
            await fn();
            console.log(`✓ ${name}`);
            passed++;
        } catch (error) {
            console.error(`✗ ${name}`);
            console.error(`  ${error.message}`);
            failed++;
        }
    }
    
    console.log(`\nResults: ${passed} passed, ${failed} failed`);
    process.exit(failed > 0 ? 1 : 0);
}

// Use existing ApiClient helper
const ApiClient = require('../helpers/api-client');

// Helper function to make requests
async function request(path, options = {}) {
    const apiClient = new ApiClient();
    const fullPath = path.startsWith('/') ? path : `/${path}`;
    
    try {
        let response;
        if (options.method === 'POST') {
            response = await apiClient.post(fullPath, options.body || {}, options.headers || {});
        } else {
            response = await apiClient.get(fullPath, options.headers || {});
        }
        
        return {
            status: response.status,
            headers: response.headers || {},
            json: async () => response.data,
            text: async () => JSON.stringify(response.data),
        };
    } catch (error) {
        return {
            status: error.status || 500,
            headers: {},
            json: async () => ({ error: error.message }),
            text: async () => error.message,
        };
    }
}

// SQL Injection Tests
test('SQL Injection - Login Email Field', async () => {
    const payloads = [
        "' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--",
        "1' OR '1'='1",
    ];
    
    for (const payload of payloads) {
        const response = await request('/api/v2/auth/login', {
            method: 'POST',
            body: {
                email: payload,
                password: 'password',
            },
        });
        
        // Should reject with 400 or 401, not 500 (which would indicate SQL error)
        if (response.status === 500) {
            throw new Error(`SQL Injection vulnerability detected with payload: ${payload}`);
        }
        
        // Should not return success
        if (response.status === 200) {
            const data = await response.json();
            if (data.session_token) {
                throw new Error(`SQL Injection successful with payload: ${payload}`);
            }
        }
    }
});

test('SQL Injection - Password Field', async () => {
    const payloads = [
        "' OR '1'='1",
        "' OR '1'='1'--",
        "admin' OR '1'='1",
    ];
    
    for (const payload of payloads) {
        const response = await request('/api/v2/auth/login', {
            method: 'POST',
            body: {
                email: 'test@example.com',
                password: payload,
            },
        });
        
        // Should reject with 400 or 401, not 500
        if (response.status === 500) {
            throw new Error(`SQL Injection vulnerability detected with payload: ${payload}`);
        }
        
        // Should not return success
        if (response.status === 200) {
            const data = await response.json();
            if (data.session_token) {
                throw new Error(`SQL Injection successful with payload: ${payload}`);
            }
        }
    }
});

// XSS Protection Tests
test('XSS Protection - Reflected XSS', async () => {
    const payloads = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        'javascript:alert("XSS")',
        '<svg onload=alert("XSS")>',
    ];
    
    // Test on login endpoint (error messages)
    for (const payload of payloads) {
        const response = await request('/api/v2/auth/login', {
            method: 'POST',
            body: {
                email: payload,
                password: 'password',
            },
        });
        
        const text = await response.text();
        
        // Check if script tags are present (vulnerability)
        if (text.includes('<script>') || text.includes('onerror=') || text.includes('onload=')) {
            throw new Error(`XSS vulnerability detected with payload: ${payload}`);
        }
    }
});

// Rate Limiting Tests
test('Rate Limiting - Authentication Endpoint', async () => {
    const requests = [];
    const requestCount = 70; // Should exceed limit of 60/min
    
    for (let i = 0; i < requestCount; i++) {
        requests.push(
            request('/api/v2/auth/login', {
                method: 'POST',
                body: {
                    email: 'test@example.com',
                    password: 'wrongpassword',
                },
            })
        );
    }
    
    const responses = await Promise.all(requests);
    const rateLimited = responses.filter(r => r.status === 429);
    
    if (rateLimited.length === 0) {
        throw new Error('Rate limiting not enforced on authentication endpoint');
    }
});

test('Rate Limiting - Health Endpoint (should not be rate limited)', async () => {
    const requests = [];
    const requestCount = 100;
    
    for (let i = 0; i < requestCount; i++) {
        requests.push(request('/api/v2/health'));
    }
    
    const responses = await Promise.all(requests);
    const rateLimited = responses.filter(r => r.status === 429);
    
    // Health endpoint should not be rate limited (or have higher limit)
    // This test verifies that not all endpoints are rate limited
    if (rateLimited.length === requestCount) {
        throw new Error('Health endpoint should not be rate limited');
    }
});

// Authentication Bypass Tests
test('Authentication Bypass - Access Protected Endpoint Without Token', async () => {
    const response = await request('/api/v2/license/info');
    
    // Should return 401 Unauthorized
    if (response.status !== 401 && response.status !== 403) {
        throw new Error(`Authentication bypass possible. Status: ${response.status}`);
    }
});

test('Authentication Bypass - Invalid Token', async () => {
    const response = await request('/api/v2/license/info', {
        headers: {
            'Authorization': 'Bearer invalid_token_12345',
        },
    });
    
    // Should return 401 Unauthorized
    if (response.status !== 401 && response.status !== 403) {
        throw new Error(`Invalid token accepted. Status: ${response.status}`);
    }
});

test('Authentication Bypass - Malformed Token', async () => {
    const malformedTokens = [
        'Bearer',
        'Bearer ',
        'InvalidBearer token',
        'token',
        '',
    ];
    
    for (const token of malformedTokens) {
        const response = await request('/api/v2/license/info', {
            headers: {
                'Authorization': token,
            },
        });
        
        // Should return 401 Unauthorized
        if (response.status !== 401 && response.status !== 403) {
            throw new Error(`Malformed token accepted: ${token}`);
        }
    }
});

// Input Validation Tests
test('Input Validation - Email Format', async () => {
    const invalidEmails = [
        'not-an-email',
        '@example.com',
        'test@',
        'test@example',
        'test..test@example.com',
    ];
    
    for (const email of invalidEmails) {
        const response = await request('/api/v2/auth/login', {
            method: 'POST',
            body: {
                email: email,
                password: 'password',
            },
        });
        
        // Should return 400 Bad Request
        if (response.status !== 400) {
            throw new Error(`Invalid email accepted: ${email}. Status: ${response.status}`);
        }
    }
});

test('Input Validation - Required Fields', async () => {
    const response = await request('/api/v2/auth/login', {
        method: 'POST',
        body: {},
    });
    
    // Should return 400 Bad Request
    if (response.status !== 400) {
        throw new Error('Request without required fields should return 400');
    }
});

// Security Headers Tests
test('Security Headers - X-Frame-Options', async () => {
    const response = await request('/api/v2/health');
    
    const headers = response.headers;
    const xFrameOptions = headers['x-frame-options'] || headers['X-Frame-Options'];
    if (!xFrameOptions) {
        throw new Error('X-Frame-Options header missing');
    }
    
    const value = typeof xFrameOptions === 'string' ? xFrameOptions : xFrameOptions[0];
    if (!value.toLowerCase().includes('deny') && !value.toLowerCase().includes('sameorigin')) {
        throw new Error(`X-Frame-Options header has invalid value: ${value}`);
    }
});

test('Security Headers - X-Content-Type-Options', async () => {
    const response = await request('/api/v2/health');
    
    const headers = response.headers;
    const xContentTypeOptions = headers['x-content-type-options'] || headers['X-Content-Type-Options'];
    if (!xContentTypeOptions) {
        throw new Error('X-Content-Type-Options header missing');
    }
    
    const value = typeof xContentTypeOptions === 'string' ? xContentTypeOptions : xContentTypeOptions[0];
    if (value.toLowerCase() !== 'nosniff') {
        throw new Error(`X-Content-Type-Options header has invalid value: ${value}`);
    }
});

test('Security Headers - X-XSS-Protection', async () => {
    const response = await request('/api/v2/health');
    
    const headers = response.headers;
    const xXssProtection = headers['x-xss-protection'] || headers['X-XSS-Protection'];
    if (!xXssProtection) {
        throw new Error('X-XSS-Protection header missing');
    }
});

// Run tests
if (require.main === module) {
    runTests().catch(error => {
        console.error('Test execution error:', error);
        process.exit(1);
    });
}

module.exports = { test, runTests };
