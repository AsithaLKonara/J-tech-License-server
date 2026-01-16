/**
 * Cross-System Authentication Integration Tests
 * Tests authentication flow between web dashboard and license server API
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Authentication Integration Tests', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    afterEach(() => {
        apiClient.clearSession();
    });

    describe('Web Dashboard to API Token Generation', () => {
        it('should generate API token after web dashboard login', async () => {
            // Simulate: User logs into web dashboard, then needs API token
            // In real flow: Web dashboard would call API to get token for user
            
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_DASHBOARD_INTEGRATION',
                'Dashboard Integration Device'
            );

            expect(response.status).toBe(200);
            expect(response.data.session_token).toBeTruthy();
            expect(response.data.entitlement_token).toBeDefined();
            
            // Token should be usable for API calls
            const token = response.data.session_token;
            expect(token).toBeTruthy();
        });

        it('should maintain session consistency across systems', async () => {
            // Login via API
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_SESSION_CONSISTENCY',
                'Session Consistency Device'
            );

            expect(loginResponse.status).toBe(200);
            const sessionToken = loginResponse.data.session_token;
            const userId = loginResponse.data.user.id;

            // Refresh token should work with same session
            const refreshResponse = await apiClient.refresh('DEVICE_SESSION_CONSISTENCY');
            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data.user.id).toBe(userId);
        });
    });

    describe('API Login to Web Dashboard Session', () => {
        it('should allow API login to create web dashboard session', async () => {
            // In real flow: API login returns token that web dashboard uses
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_API_TO_DASHBOARD',
                'API to Dashboard Device'
            );

            expect(response.status).toBe(200);
            // Session token can be used by web dashboard
            expect(response.data.session_token).toBeTruthy();
            // User info is available for dashboard
            expect(response.data.user).toBeDefined();
            expect(response.data.user.email).toBe('test@example.com');
        });

        it('should provide user information for dashboard display', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_USER_INFO',
                'User Info Device'
            );

            expect(response.status).toBe(200);
            expect(response.data.user).toHaveProperty('id');
            expect(response.data.user).toHaveProperty('email');
            // Dashboard can use this info to display user details
        });
    });

    describe('Token Refresh Across Systems', () => {
        it('should refresh token that works across systems', async () => {
            // Initial login
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_REFRESH_CROSS',
                'Refresh Cross System Device'
            );

            expect(loginResponse.status).toBe(200);
            const initialToken = loginResponse.data.session_token;

            // Refresh token
            const refreshResponse = await apiClient.refresh('DEVICE_REFRESH_CROSS');
            expect(refreshResponse.status).toBe(200);
            const refreshedToken = refreshResponse.data.session_token;

            // New token should be different but valid
            expect(refreshedToken).toBeTruthy();
            expect(refreshedToken).not.toBe(initialToken);
            
            // Refreshed token should work for API calls
            apiClient.sessionToken = refreshedToken;
            const secondRefresh = await apiClient.refresh('DEVICE_REFRESH_CROSS');
            expect(secondRefresh.status).toBe(200);
        });

        it('should maintain user context after token refresh', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_CONTEXT_REFRESH',
                'Context Refresh Device'
            );

            const userId = loginResponse.data.user.id;
            const userEmail = loginResponse.data.user.email;

            const refreshResponse = await apiClient.refresh('DEVICE_CONTEXT_REFRESH');
            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data.user.id).toBe(userId);
            expect(refreshResponse.data.user.email).toBe(userEmail);
        });
    });

    describe('Concurrent Session Management', () => {
        it('should handle multiple concurrent logins', async () => {
            const deviceIds = Array.from({ length: 5 }, (_, i) =>
                `DEVICE_CONCURRENT_${i}`
            );

            const loginPromises = deviceIds.map(deviceId =>
                apiClient.login(
                    'test@example.com',
                    'testpassword123',
                    deviceId,
                    `Concurrent Device ${deviceId}`
                )
            );

            const responses = await Promise.all(loginPromises);
            
            // All should succeed (or handle limits gracefully)
            responses.forEach(response => {
                expect([200, 403]).toContain(response.status);
            });

            // Each should have unique session token
            const tokens = responses
                .filter(r => r.status === 200)
                .map(r => r.data.session_token);
            const uniqueTokens = new Set(tokens);
            expect(uniqueTokens.size).toBe(tokens.length);
        });

        it('should allow multiple devices per user', async () => {
            const deviceIds = [
                'DEVICE_MULTI_1',
                'DEVICE_MULTI_2',
                'DEVICE_MULTI_3',
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

            // Should allow multiple devices (within license limits)
            const successCount = responses.filter(r => r.status === 200).length;
            expect(successCount).toBeGreaterThan(0);
        });

        it('should handle session expiration gracefully', async () => {
            // Login to get session
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_EXPIRATION_TEST',
                'Expiration Test Device'
            );

            expect(loginResponse.status).toBe(200);
            
            // Wait and try to refresh (would need actual expiration time)
            // For now, we test that refresh works with valid token
            const refreshResponse = await apiClient.refresh('DEVICE_EXPIRATION_TEST');
            expect(refreshResponse.status).toBe(200);
        });
    });

    describe('Error Handling Across Systems', () => {
        it('should propagate authentication errors correctly', async () => {
            // Invalid credentials
            const response = await apiClient.login(
                'test@example.com',
                'wrongpassword',
                'DEVICE_ERROR_PROPAGATION',
                'Error Propagation Device'
            );

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
            // Error should be clear and actionable
        });

        it('should handle network errors gracefully', async () => {
            // This would require simulating network failure
            // For now, we test that API returns proper error format
            const response = await apiClient.post('/api/v2/auth/login', {
                email: 'test@example.com',
                // Missing password to trigger validation error
            });

            expect(response.status).toBe(400);
            expect(response.data).toHaveProperty('error');
        });
    });
});
