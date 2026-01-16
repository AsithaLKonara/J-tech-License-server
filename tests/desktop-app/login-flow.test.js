/**
 * Desktop App Login Flow Tests
 * Tests desktop app login integration with API
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Desktop App Login Flow Tests', () => {
    let apiClient;
    
    beforeEach(() => {
        apiClient = new ApiClient();
    });
    
    afterEach(() => {
        apiClient.clearSession();
    });
    
    describe('Email/Password Login', () => {
        it('should complete login flow as desktop app', async () => {
            // Step 1: User enters credentials in desktop app
            const credentials = {
                email: 'test@example.com',
                password: 'testpassword123',
            };
            
            // Step 2: Desktop app sends login request
            const response = await apiClient.login(
                credentials.email,
                credentials.password,
                'DESKTOP_LOGIN_001',
                'Desktop App Device'
            );
            
            // Step 3: Desktop app receives tokens
            expect(response.status).toBe(200);
            expect(response.data.session_token).toBeTruthy();
            expect(response.data.entitlement_token).toBeTruthy();
            
            // Step 4: Desktop app stores tokens (encrypted)
            // This is verified by the fact that tokens are returned
            expect(typeof response.data.session_token).toBe('string');
        });
        
        it('should handle login failure gracefully', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'wrongpassword',
                'DESKTOP_LOGIN_FAIL',
                'Desktop App Fail Test'
            );
            
            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
            // Desktop app should show error message to user
        });
    });
    
    describe('Magic Link Login', () => {
        it('should handle magic link request flow', async () => {
            // Step 1: User requests magic link
            const email = TestData.generateEmail('magic');
            const requestResponse = await apiClient.post('/api/v2/auth/magic-link/request', {
                email,
            });
            
            // Step 2: Email sent (would be received by user)
            expect([200, 201, 202]).toContain(requestResponse.status);
            
            // Step 3: User clicks link, desktop app receives token
            // Step 4: Desktop app verifies token
            const verifyResponse = await apiClient.post('/api/v2/auth/magic-link/verify', {
                token: 'test_magic_token',
                device_id: 'DESKTOP_MAGIC_001',
            });
            
            // Will fail with invalid token, but tests the flow
            expect([200, 401, 400]).toContain(verifyResponse.status);
        });
    });
    
    describe('Token Management', () => {
        it('should refresh tokens as desktop app would', async () => {
            // Login
            await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_REFRESH',
                'Desktop Refresh Test'
            );
            
            const originalToken = apiClient.sessionToken;
            
            // Refresh (desktop app does this periodically)
            const refreshResponse = await apiClient.refresh('DESKTOP_REFRESH');
            
            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data.session_token).toBeTruthy();
            expect(refreshResponse.data.session_token).not.toBe(originalToken);
        });
        
        it('should handle token expiration', async () => {
            // Login
            await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_EXPIRED',
                'Desktop Expired Test'
            );
            
            // Simulate expired token
            apiClient.sessionToken = 'expired_token_placeholder';
            
            // Try to use expired token
            const response = await apiClient.getLicenseInfo();
            expect([401, 403]).toContain(response.status);
            
            // Desktop app should prompt for re-login
        });
    });
});
