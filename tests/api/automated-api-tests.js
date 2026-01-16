/**
 * Automated API Endpoint Tests
 * Comprehensive test suite for all license server API endpoints
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Automated API Endpoint Tests', () => {
    let apiClient;
    let testUser = {
        email: 'test@example.com',
        password: 'testpassword123',
        deviceId: 'AUTO_TEST_DEVICE',
        deviceName: 'Automated Test Device'
    };

    beforeAll(() => {
        apiClient = new ApiClient(process.env.LICENSE_SERVER_URL || 'http://localhost:8000');
    });

    afterAll(() => {
        apiClient.clearSession();
    });

    describe('Health Check Endpoint', () => {
        test('GET /api/v2/health should return 200', async () => {
            const response = await apiClient.health();
            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('status');
            expect(response.data.status).toBe('ok');
        });

        test('Health check should include timestamp', async () => {
            const response = await apiClient.health();
            expect(response.data).toHaveProperty('timestamp');
            expect(typeof response.data.timestamp).toBe('string');
        });
    });

    describe('Authentication Endpoints', () => {
        test('POST /api/v2/auth/login with email/password should succeed', async () => {
            const response = await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );

            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('session_token');
            expect(response.data).toHaveProperty('entitlement_token');
            expect(response.data).toHaveProperty('user');
            expect(response.data.session_token).toBeTruthy();
        });

        test('POST /api/v2/auth/login with invalid credentials should return 401', async () => {
            const response = await apiClient.login(
                'invalid@example.com',
                'wrongpassword',
                'INVALID_DEVICE',
                'Invalid Device'
            );

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
        });

        test('POST /api/v2/auth/login with missing fields should return 400', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: testUser.email
                // Missing password
            });

            expect(response.status).toBe(400);
            expect(response.data).toHaveProperty('error');
        });

        test('POST /api/v2/auth/refresh should refresh token', async () => {
            // First login
            const loginResponse = await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );

            expect(loginResponse.status).toBe(200);
            const originalToken = apiClient.sessionToken;

            // Refresh token
            const refreshResponse = await apiClient.refresh(testUser.deviceId);

            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data).toHaveProperty('session_token');
            expect(refreshResponse.data.session_token).not.toBe(originalToken);
        });

        test('POST /api/v2/auth/logout should revoke token', async () => {
            // Login first
            await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );

            expect(apiClient.sessionToken).toBeTruthy();

            // Logout
            const logoutResponse = await apiClient.logout();

            expect(logoutResponse.status).toBe(200);
            expect(apiClient.sessionToken).toBeNull();
        });

        test('POST /api/v2/auth/logout without token should fail', async () => {
            apiClient.clearSession();
            
            try {
                await apiClient.logout();
                fail('Should have thrown an error');
            } catch (error) {
                expect(error.message).toContain('No session token available');
            }
        });
    });

    describe('License Endpoints', () => {
        beforeEach(async () => {
            // Ensure we're logged in
            await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );
        });

        test('GET /api/v2/license/info should return license information', async () => {
            const response = await apiClient.getLicenseInfo();

            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('entitlement');
            expect(response.data.entitlement).toHaveProperty('plan');
            expect(response.data.entitlement).toHaveProperty('features');
            expect(response.data.entitlement).toHaveProperty('max_devices');
            expect(response.data.entitlement).toHaveProperty('is_active');
        });

        test('GET /api/v2/license/validate should validate entitlement token', async () => {
            // Get entitlement token from login
            const loginResponse = await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );

            const entitlementToken = loginResponse.data.entitlement_token;

            const validateResponse = await apiClient.validateLicense(entitlementToken);

            expect(validateResponse.status).toBe(200);
            expect(validateResponse.data).toHaveProperty('valid');
            expect(validateResponse.data.valid).toBe(true);
        });

        test('GET /api/v2/license/info without authentication should return 401', async () => {
            apiClient.clearSession();

            try {
                await apiClient.getLicenseInfo();
                fail('Should have thrown an error');
            } catch (error) {
                expect(error.message).toContain('No session token available');
            }
        });
    });

    describe('Device Management Endpoints', () => {
        beforeEach(async () => {
            // Ensure we're logged in
            await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );
        });

        test('POST /api/v2/devices/register should register device', async () => {
            const newDeviceId = `AUTO_TEST_DEVICE_${Date.now()}`;
            const response = await apiClient.registerDevice(newDeviceId, 'New Test Device');

            expect([200, 403]).toContain(response.status);
            if (response.status === 200) {
                expect(response.data).toHaveProperty('device');
                expect(response.data.device).toHaveProperty('device_id');
            }
        });

        test('GET /api/v2/devices should list all devices', async () => {
            const response = await apiClient.listDevices();

            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('devices');
            expect(Array.isArray(response.data.devices)).toBe(true);
        });

        test('DELETE /api/v2/devices/{id} should delete device', async () => {
            // First get list of devices
            const listResponse = await apiClient.listDevices();
            expect(listResponse.status).toBe(200);

            const devices = listResponse.data.devices;
            if (devices.length > 0) {
                const deviceToDelete = devices[0];
                const deleteResponse = await apiClient.deleteDevice(deviceToDelete.id);

                expect([200, 404]).toContain(deleteResponse.status);
                if (deleteResponse.status === 200) {
                    expect(deleteResponse.data).toHaveProperty('message');
                }
            }
        });

        test('Device registration should enforce device limits', async () => {
            // Try to register multiple devices
            const deviceIds = Array.from({ length: 5 }, (_, i) => 
                `AUTO_TEST_DEVICE_LIMIT_${i}_${Date.now()}`
            );

            const responses = await Promise.all(
                deviceIds.map(deviceId => 
                    apiClient.registerDevice(deviceId, `Limit Test Device ${deviceId}`)
                )
            );

            // Some may succeed, but eventually should hit limit
            const statusCodes = responses.map(r => r.status);
            expect(statusCodes).toContain(200); // At least one should succeed

            // If limit reached, some should return 403
            if (statusCodes.includes(403)) {
                const failedResponse = responses.find(r => r.status === 403);
                expect(failedResponse.data).toHaveProperty('error');
                expect(failedResponse.data.error).toContain('device');
            }
        });
    });

    describe('Error Handling', () => {
        test('Invalid endpoint should return 404', async () => {
            const response = await apiClient.get('/api/v2/invalid-endpoint');
            expect(response.status).toBe(404);
        });

        test('Malformed request should return 400', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                invalid: 'data'
            });
            expect([400, 422]).toContain(response.status);
        });

        test('Unauthorized request should return 401', async () => {
            apiClient.clearSession();
            const response = await apiClient.get('/api/v2/license/info', {
                'Authorization': 'Bearer invalid_token'
            });
            expect(response.status).toBe(401);
        });
    });

    describe('CORS Headers', () => {
        test('API responses should include CORS headers', async () => {
            const response = await apiClient.health();
            expect(response.headers).toHaveProperty('access-control-allow-origin');
        });

        test('POST requests should include CORS headers', async () => {
            const response = await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );
            expect(response.headers).toHaveProperty('access-control-allow-origin');
        });
    });

    describe('Performance Tests', () => {
        test('Health check should respond quickly', async () => {
            const startTime = Date.now();
            await apiClient.health();
            const duration = Date.now() - startTime;

            expect(duration).toBeLessThan(1000); // Should respond within 1 second
        });

        test('Login should complete within reasonable time', async () => {
            const startTime = Date.now();
            await apiClient.login(
                testUser.email,
                testUser.password,
                testUser.deviceId,
                testUser.deviceName
            );
            const duration = Date.now() - startTime;

            expect(duration).toBeLessThan(5000); // Should complete within 5 seconds
        });
    });
});
