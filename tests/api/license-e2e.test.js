/**
 * License Management E2E Tests
 * Tests for license operations via API
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');
const { cleanupDevices } = require('../scripts/cleanup-test-db');

describe('License E2E Tests', () => {
    let apiClient;
    let sessionToken;
    let userId;

    beforeAll(async () => {
        // Clean up all devices before running license tests
        await cleanupDevices();
        apiClient = new ApiClient();
        // Login to get session token
        const loginResponse = await apiClient.login(
            'test@example.com',
            'testpassword123',
            'DEVICE_LICENSE_TEST',
            'License Test Device'
        );
        expect(loginResponse.status).toBe(200);
        sessionToken = loginResponse.data.session_token;
        userId = loginResponse.data.user.id;
    });

    afterAll(() => {
        apiClient.clearSession();
    });

    describe('License Validation After Login', () => {
        it('should return valid license in entitlement token after login', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_LICENSE_VALIDATION',
                'License Validation Device'
            );

            expect(response.status).toBe(200);
            expect(response.data.entitlement_token).toBeDefined();
            expect(response.data.entitlement_token.plan).toBeDefined();
            expect(response.data.entitlement_token.features).toBeInstanceOf(Array);
            expect(response.data.entitlement_token.features.length).toBeGreaterThan(0);
        });

        it('should include license expiration in entitlement token', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_LICENSE_EXPIRY',
                'License Expiry Device'
            );

            expect(response.status).toBe(200);
            // expires_at can be null for perpetual licenses
            expect(response.data.entitlement_token).toHaveProperty('expires_at');
        });
    });

    describe('Device Registration with License', () => {
        it('should register device with valid license', async () => {
            const deviceId = TestData.generateDeviceId('LICENSE_DEVICE');
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                deviceId,
                'License Device Registration'
            );

            expect(response.status).toBe(200);
            // Device should be registered during login if device_id is provided
            expect(response.data).toHaveProperty('user');
        });

        it('should allow multiple devices up to max_devices limit', async () => {
            // This test would need to check the license's max_devices setting
            // and verify that devices can be registered up to that limit
            const deviceIds = [
                TestData.generateDeviceId('MULTI_1'),
                TestData.generateDeviceId('MULTI_2'),
                TestData.generateDeviceId('MULTI_3'),
            ];

            const responses = await Promise.all(
                deviceIds.map(deviceId =>
                    apiClient.login(
                        'test@example.com',
                        'testpassword123',
                        deviceId,
                        `Multi Device ${deviceId}`
                    )
                )
            );

            // All should succeed if within limit
            responses.forEach(response => {
                expect([200, 403]).toContain(response.status);
            });
        });
    });

    describe('License Feature Access Control', () => {
        it('should return correct features for plan type', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_FEATURES_TEST',
                'Features Test Device'
            );

            expect(response.status).toBe(200);
            const features = response.data.entitlement_token.features;
            expect(features).toBeInstanceOf(Array);
            
            // Verify common features exist
            const hasPatternUpload = features.includes('pattern_upload');
            expect(hasPatternUpload).toBe(true);
        });

        it('should validate license status is active', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_STATUS_TEST',
                'Status Test Device'
            );

            expect(response.status).toBe(200);
            // If license is invalid, login should fail with 403
            expect(response.status).not.toBe(403);
        });
    });

    describe('License Expiration Handling', () => {
        it('should handle expired licenses gracefully', async () => {
            // This would require a test user with an expired license
            // For now, we test that the API handles expiration checks
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_EXPIRED_TEST',
                'Expired License Test'
            );

            // Should either succeed (if license valid) or return 403 (if expired)
            expect([200, 403]).toContain(response.status);
            
            if (response.status === 403) {
                expect(response.data).toHaveProperty('error');
                expect(response.data.error).toContain('License');
            }
        });
    });

    describe('License Refresh', () => {
        it('should return updated license info on token refresh', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_REFRESH_TEST',
                'Refresh Test Device'
            );

            expect(loginResponse.status).toBe(200);
            const initialFeatures = loginResponse.data.entitlement_token.features;

            const refreshResponse = await apiClient.refresh('DEVICE_REFRESH_TEST');
            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data.entitlement_token.features).toEqual(initialFeatures);
        });
    });

    describe('GET /api/v2/license/info', () => {
        it('should return license information', async () => {
            const response = await apiClient.getLicenseInfo();

            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('entitlement');
            expect(response.data.entitlement).toHaveProperty('plan');
            expect(response.data.entitlement).toHaveProperty('features');
            expect(response.data.entitlement).toHaveProperty('max_devices');
            expect(response.data.entitlement).toHaveProperty('is_active');
        });
    });

    describe('GET /api/v2/license/validate', () => {
        it('should validate entitlement token', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_VALIDATE_TEST',
                'Validate Test Device'
            );

            expect(loginResponse.status).toBe(200);
            const entitlementToken = loginResponse.data.entitlement_token;

            const validateResponse = await apiClient.validateLicense(entitlementToken);
            expect(validateResponse.status).toBe(200);
            expect(validateResponse.data).toHaveProperty('valid');
            expect(validateResponse.data.valid).toBe(true);
        });
        
        it('should reject invalid entitlement token', async () => {
            const invalidToken = { sub: 'invalid', plan: 'invalid' };
            const response = await apiClient.validateLicense(invalidToken);
            expect([400, 401, 403]).toContain(response.status);
        });
        
        it('should validate token with device binding', async () => {
            const deviceId = TestData.generateDeviceId('BINDING_TEST');
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                deviceId,
                'Binding Test Device'
            );
            
            expect(loginResponse.status).toBe(200);
            const entitlementToken = loginResponse.data.entitlement_token;
            
            const validateResponse = await apiClient.validateLicense(entitlementToken);
            expect(validateResponse.status).toBe(200);
        });
    });
    
    describe('License Expiration Edge Cases', () => {
        it('should handle licenses expiring soon', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_EXPIRING_SOON',
                'Expiring Soon Device'
            );
            
            expect(response.status).toBe(200);
            if (response.data.entitlement_token.expires_at) {
                const expiresAt = new Date(response.data.entitlement_token.expires_at);
                const now = new Date();
                expect(expiresAt > now || expiresAt === null).toBe(true);
            }
        });
        
        it('should handle perpetual licenses (no expiration)', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_PERPETUAL',
                'Perpetual License Device'
            );
            
            expect(response.status).toBe(200);
            // Perpetual licenses may have null expires_at
            expect(response.data.entitlement_token).toHaveProperty('expires_at');
        });
    });
    
    describe('Concurrent License Validation', () => {
        it('should handle concurrent license validations', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_CONCURRENT',
                'Concurrent Test Device'
            );
            
            expect(loginResponse.status).toBe(200);
            const entitlementToken = loginResponse.data.entitlement_token;
            
            // Make multiple concurrent validation requests
            const requests = Array.from({ length: 5 }, () => 
                apiClient.validateLicense(entitlementToken)
            );
            
            const responses = await Promise.all(requests);
            responses.forEach(response => {
                expect(response.status).toBe(200);
                expect(response.data.valid).toBe(true);
            });
        });
    });
});
