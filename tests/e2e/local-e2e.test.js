/**
 * Local E2E Tests for Upload Bridge
 * Tests communication between desktop app and web dashboard running locally
 * 
 * Run with: node run-test.js tests/e2e/local-e2e.test.js
 * Or: npm run test:e2e
 */

const BASE_URL = process.env.LICENSE_SERVER_URL || 'http://localhost:8000';
const API_BASE_URL = `${BASE_URL}/api/v2`;

// Test credentials from TestDataSeeder
const TEST_USER = {
    email: 'user1@test.com',
    password: 'password123'
};

const ADMIN_USER = {
    email: 'admin@test.com',
    password: 'password123'
};

let sessionToken = null;
let entitlementToken = null;

/**
 * Make HTTP request
 */
async function request(method, endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };

    if (options.body) {
        config.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json().catch(() => ({}));
        
        return {
            ok: response.ok,
            status: response.status,
            data,
            headers: response.headers
        };
    } catch (error) {
        return {
            ok: false,
            status: 0,
            error: error.message,
            data: {}
        };
    }
}

/**
 * Test suite
 */
async function runTests() {
    const results = {
        passed: 0,
        failed: 0,
        total: 0,
        details: []
    };

    function test(name, fn) {
        results.total++;
        return async () => {
            try {
                console.log(`\n🧪 Testing: ${name}`);
                await fn();
                console.log(`   ✅ PASSED`);
                results.passed++;
                results.details.push({ test: name, status: 'PASSED' });
            } catch (error) {
                console.log(`   ❌ FAILED: ${error.message}`);
                results.failed++;
                results.details.push({ test: name, status: 'FAILED', error: error.message });
            }
        };
    }

    function assert(condition, message) {
        if (!condition) {
            throw new Error(message || 'Assertion failed');
        }
    }

    // Test 1: Health Check
    await test('Health Check', async () => {
        const response = await request('GET', '/health');
        assert(response.ok, `Expected 200, got ${response.status}`);
        assert(response.data.status === 'ok' || response.data.healthy === true, 'Health check should return ok/healthy');
    })();

    // Test 2: Login
    await test('User Login', async () => {
        const response = await request('POST', '/auth/login', {
            body: {
                email: TEST_USER.email,
                password: TEST_USER.password
            }
        });
        
        assert(response.ok, `Login failed with status ${response.status}`);
        assert(response.data.session_token, 'Missing session_token');
        assert(response.data.entitlement_token, 'Missing entitlement_token');
        
        sessionToken = response.data.session_token;
        entitlementToken = response.data.entitlement_token;
    })();

    // Test 3: License Validation
    await test('License Validation', async () => {
        assert(entitlementToken, 'No entitlement token available');
        
        const response = await request('GET', '/license/validate', {
            headers: {
                'Authorization': `Bearer ${entitlementToken}`
            }
        });
        
        assert(response.ok, `License validation failed with status ${response.status}`);
        assert(response.data.valid !== false, 'License should be valid');
    })();

    // Test 4: License Info
    await test('License Info', async () => {
        assert(entitlementToken, 'No entitlement token available');
        
        const response = await request('GET', '/license/info', {
            headers: {
                'Authorization': `Bearer ${entitlementToken}`
            }
        });
        
        assert(response.ok, `License info failed with status ${response.status}`);
        assert(response.data.user_id || response.data.email, 'Missing user information');
    })();

    // Test 5: Device Registration
    await test('Device Registration', async () => {
        assert(entitlementToken, 'No entitlement token available');
        
        const deviceId = `TEST_DEVICE_${Date.now()}`;
        const response = await request('POST', '/devices/register', {
            headers: {
                'Authorization': `Bearer ${entitlementToken}`
            },
            body: {
                device_id: deviceId,
                device_name: 'Test Device'
            }
        });
        
        assert(response.ok, `Device registration failed with status ${response.status}`);
    })();

    // Test 6: List Devices
    await test('List Devices', async () => {
        assert(entitlementToken, 'No entitlement token available');
        
        const response = await request('GET', '/devices', {
            headers: {
                'Authorization': `Bearer ${entitlementToken}`
            }
        });
        
        assert(response.ok, `List devices failed with status ${response.status}`);
        assert(Array.isArray(response.data.devices || response.data), 'Devices should be an array');
    })();

    // Test 7: Invalid Login
    await test('Invalid Login Rejection', async () => {
        const response = await request('POST', '/auth/login', {
            body: {
                email: 'invalid@test.com',
                password: 'wrongpassword'
            }
        });
        
        assert(!response.ok, 'Should reject invalid credentials');
        assert(response.status === 401 || response.status === 422, `Expected 401/422, got ${response.status}`);
    })();

    // Test 8: Unauthorized Access
    await test('Unauthorized Access Protection', async () => {
        const response = await request('GET', '/license/validate');
        
        assert(!response.ok, 'Should require authentication');
        assert(response.status === 401, `Expected 401, got ${response.status}`);
    })();

    // Test 9: Token Refresh
    await test('Token Refresh', async () => {
        assert(sessionToken, 'No session token available');
        
        const response = await request('POST', '/auth/refresh', {
            headers: {
                'Authorization': `Bearer ${sessionToken}`
            }
        });
        
        // Token refresh might not be implemented, so we accept both success and 404/501
        if (response.status === 404 || response.status === 501) {
            console.log('   ⚠️  Token refresh not implemented (acceptable)');
        } else {
            assert(response.ok, `Token refresh failed with status ${response.status}`);
        }
    })();

    // Summary
    console.log('\n========================================');
    console.log('Test Summary');
    console.log('========================================');
    console.log(`Total Tests: ${results.total}`);
    console.log(`Passed: ${results.passed}`);
    console.log(`Failed: ${results.failed}`);
    console.log('');

    if (results.failed === 0) {
        console.log('✅ All tests passed!');
        process.exit(0);
    } else {
        console.log('❌ Some tests failed. Check the output above for details.');
        process.exit(1);
    }
}

// Run tests
if (require.main === module) {
    console.log('========================================');
    console.log('Local E2E Tests for Upload Bridge');
    console.log('========================================');
    console.log(`Testing against: ${BASE_URL}`);
    console.log('');
    
    runTests().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = { runTests, request, BASE_URL, API_BASE_URL };
