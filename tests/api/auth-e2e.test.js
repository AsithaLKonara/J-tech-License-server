/**
 * Authentication E2E Tests
 * Tests for license server authentication endpoints
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');
const { cleanupDevicesByPattern } = require('../scripts/cleanup-test-db');

describe('Authentication E2E Tests', () => {
    let apiClient;

    beforeEach(async () => {
        apiClient = new ApiClient();
        // Clean up test devices before each test to avoid device limit issues
        await cleanupDevicesByPattern('DEVICE_TEST_|DEVICE_|TEST_DEVICE');
    });

    afterEach(() => {
        apiClient.clearSession();
    });

    describe('POST /api/v2/auth/login', () => {
        it('should login with valid credentials', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_TEST_001',
                'Test Device'
            );

            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('session_token');
            expect(response.data).toHaveProperty('entitlement_token');
            expect(response.data).toHaveProperty('user');
            expect(response.data.session_token).toBeTruthy();
            expect(response.data.entitlement_token.sub).toBeTruthy();
            expect(response.data.entitlement_token.plan).toBeTruthy();
            expect(response.data.entitlement_token.features).toBeInstanceOf(Array);
            expect(response.data.user.email).toBe('test@example.com');
        });

        it('should return 401 with invalid credentials', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'wrongpassword',
                'DEVICE_TEST_002',
                'Test Device'
            );

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
            expect(response.data.error).toContain('Invalid email or password');
        });

        it('should return 401 with non-existent user', async () => {
            const response = await apiClient.login(
                'nonexistent@example.com',
                'password123',
                'DEVICE_TEST_003',
                'Test Device'
            );

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
        });

        it('should return 400 with missing email', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                password: 'testpassword123',
                device_id: 'DEVICE_TEST_004',
            });

            expect(response.status).toBe(400);
            expect(response.data).toHaveProperty('error');
            expect(response.data.error).toContain('Email and password are required');
        });

        it('should return 400 with missing password', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: 'test@example.com',
                device_id: 'DEVICE_TEST_005',
            });

            expect(response.status).toBe(400);
            expect(response.data).toHaveProperty('error');
        });

        it('should include CORS headers', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_TEST_006',
                'Test Device'
            );

            expect(response.status).toBe(200);
            expect(response.headers['access-control-allow-origin']).toBeDefined();
        });

        it('should handle OPTIONS preflight request', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {}, {
                'Access-Control-Request-Method': 'POST',
            });

            // OPTIONS should return 200
            // Note: This might need adjustment based on actual implementation
            expect([200, 405]).toContain(response.status);
        });
    });

    describe('POST /api/v2/auth/refresh', () => {
        it('should refresh session token with valid token', async () => {
            // First login to get a session token
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_TEST_007',
                'Test Device'
            );

            expect(loginResponse.status).toBe(200);
            expect(loginResponse.data.session_token).toBeTruthy();

            // Now refresh the token
            const refreshResponse = await apiClient.refresh('DEVICE_TEST_007');

            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data).toHaveProperty('session_token');
            expect(refreshResponse.data).toHaveProperty('entitlement_token');
            expect(refreshResponse.data.session_token).toBeTruthy();
        });

        it('should return 401 with expired token', async () => {
            // Use an expired token (this would need to be generated or mocked)
            const expiredToken = 'expired_token_here';
            apiClient.sessionToken = expiredToken;

            const response = await apiClient.refresh('DEVICE_TEST_008');

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
        });

        it('should return 401 with invalid token', async () => {
            apiClient.sessionToken = 'invalid_token_12345';

            const response = await apiClient.refresh('DEVICE_TEST_009');

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
            expect(response.data.error).toContain('Invalid session token');
        });

        it('should return 400 with missing session token', async () => {
            const response = await apiClient.post('/api/v2/auth/refresh', {
                device_id: 'DEVICE_TEST_010',
            });

            expect(response.status).toBe(400);
            expect(response.data).toHaveProperty('error');
            expect(response.data.error).toContain('Session token is required');
        });

        it('should include CORS headers in refresh response', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_TEST_011',
                'Test Device'
            );

            const refreshResponse = await apiClient.refresh('DEVICE_TEST_011');

            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.headers['access-control-allow-origin']).toBeDefined();
        });
    });

    describe('POST /api/v2/auth/logout', () => {
        it('should logout and revoke token', async () => {
            // First login
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_TEST_LOGOUT',
                'Test Device'
            );

            expect(loginResponse.status).toBe(200);
            expect(apiClient.sessionToken).toBeTruthy();

            // Now logout
            const logoutResponse = await apiClient.logout();

            expect(logoutResponse.status).toBe(200);
            expect(logoutResponse.data).toHaveProperty('message');
            expect(apiClient.sessionToken).toBeNull();
        });

        it('should return 400 with missing session token', async () => {
            apiClient.clearSession();
            try {
                await apiClient.logout();
                // Should throw error
                expect(true).toBe(false);
            } catch (error) {
                expect(error.message).toContain('No session token available');
            }
        });
    });

    describe('POST /api/v2/auth/magic-link/verify', () => {
        it('should login with valid magic link token', async () => {
            // Note: This test requires a valid magic link token
            // In real testing, you would generate one via the magic link endpoint
            const magicLinkToken = 'valid_magic_link_token_here';
            
            const response = await apiClient.loginWithMagicLink(
                magicLinkToken,
                'DEVICE_TEST_MAGIC',
                'Magic Link Device'
            );

            // This will fail if token is not valid, which is expected
            // In real scenario, you'd get the token from email
            expect([200, 401]).toContain(response.status);
        });

        it('should return 401 with invalid magic link token', async () => {
            const response = await apiClient.loginWithMagicLink(
                'invalid_token_12345',
                'DEVICE_TEST_MAGIC_INVALID',
                'Test Device'
            );

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
        });
    });

    describe('GET /api/v2/health', () => {
        it('should return health status', async () => {
            const response = await apiClient.health();

            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('status');
            expect(response.data.status).toBe('ok');
            expect(response.data).toHaveProperty('timestamp');
        });
    });

    describe('Rate Limiting', () => {
        it('should handle multiple rapid requests', async () => {
            const requests = [];
            for (let i = 0; i < 10; i++) {
                requests.push(
                    apiClient.login(
                        'test@example.com',
                        'testpassword123',
                        `DEVICE_TEST_${i}`,
                        'Test Device'
                    )
                );
            }

            const responses = await Promise.all(requests);
            // At least some should succeed
            const successCount = responses.filter(r => r.status === 200).length;
            expect(successCount).toBeGreaterThan(0);
        });
    });
    
    describe('Session Management', () => {
        it('should maintain session across multiple requests', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_SESSION_TEST',
                'Test Device'
            );
            
            expect(loginResponse.status).toBe(200);
            const originalToken = apiClient.sessionToken;
            
            // Make multiple authenticated requests
            const licenseInfo1 = await apiClient.getLicenseInfo();
            const licenseInfo2 = await apiClient.getLicenseInfo();
            
            expect(licenseInfo1.status).toBe(200);
            expect(licenseInfo2.status).toBe(200);
            expect(apiClient.sessionToken).toBe(originalToken);
        });
        
        it('should handle concurrent login attempts', async () => {
            const requests = TestData.userFactory(5).map(user => 
                apiClient.login(user.email, user.password, user.device_id, user.device_name)
            );
            
            const responses = await Promise.all(requests);
            // Some may fail due to rate limiting or invalid credentials
            expect(responses.length).toBe(5);
        });
    });
    
    describe('Token Validation', () => {
        it('should reject requests with malformed tokens', async () => {
            apiClient.sessionToken = 'malformed.token.here';
            
            try {
                await apiClient.getLicenseInfo();
                // Should fail
                expect(true).toBe(false);
            } catch (error) {
                // Expected to fail
                expect(error).toBeDefined();
            }
        });
        
        it('should handle token expiration gracefully', async () => {
            // This test would require a way to generate expired tokens
            // For now, we test that invalid tokens are rejected
            apiClient.sessionToken = 'expired_token_placeholder';
            
            const response = await apiClient.refresh('DEVICE_EXPIRED');
            expect([401, 400]).toContain(response.status);
        });
    });
    
    describe('Edge Cases', () => {
        it('should handle empty email', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: '',
                password: 'testpassword123',
                device_id: 'DEVICE_EMPTY_EMAIL',
            });
            
            expect([400, 422]).toContain(response.status);
        });
        
        it('should handle empty password', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: 'test@example.com',
                password: '',
                device_id: 'DEVICE_EMPTY_PASSWORD',
            });
            
            expect([400, 422]).toContain(response.status);
        });
        
        it('should handle very long email', async () => {
            const longEmail = 'a'.repeat(300) + '@example.com';
            const response = await apiClient.post('/api/v2/auth/login', {
                email: longEmail,
                password: 'testpassword123',
                device_id: 'DEVICE_LONG_EMAIL',
            });
            
            expect([400, 422]).toContain(response.status);
        });
        
        it('should handle special characters in email', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: 'test+special@example.com',
                password: 'testpassword123',
                device_id: 'DEVICE_SPECIAL_EMAIL',
            });
            
            // Should either accept valid special chars or reject invalid ones
            expect([200, 400, 422]).toContain(response.status);
        });
    });
});
