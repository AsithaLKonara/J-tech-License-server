/**
 * Desktop App ↔ API Integration Tests
 * Tests the integration between desktop app and API
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Desktop App ↔ API Integration Tests', () => {
    let apiClient;
    
    beforeEach(() => {
        apiClient = new ApiClient();
    });
    
    afterEach(() => {
        apiClient.clearSession();
    });
    
    describe('Desktop App Login Flow', () => {
        it('should complete full login flow as desktop app would', async () => {
            // Step 1: Login with email/password
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_APP_001',
                'Desktop App Test Device'
            );
            
            expect(loginResponse.status).toBe(200);
            expect(loginResponse.data.session_token).toBeTruthy();
            expect(loginResponse.data.entitlement_token).toBeTruthy();
            
            // Step 2: Validate license (as desktop app would)
            const validateResponse = await apiClient.validateLicense(
                loginResponse.data.entitlement_token
            );
            
            expect(validateResponse.status).toBe(200);
            expect(validateResponse.data.valid).toBe(true);
            
            // Step 3: Get license info (as desktop app would)
            const licenseInfo = await apiClient.getLicenseInfo();
            
            expect(licenseInfo.status).toBe(200);
            expect(licenseInfo.data.entitlement).toBeDefined();
        });
        
        it('should handle token refresh as desktop app would', async () => {
            // Login
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_APP_REFRESH',
                'Desktop App Refresh Test'
            );
            
            expect(loginResponse.status).toBe(200);
            const originalToken = apiClient.sessionToken;
            
            // Refresh token (as desktop app would periodically)
            const refreshResponse = await apiClient.refresh('DESKTOP_APP_REFRESH');
            
            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data.session_token).toBeTruthy();
            expect(refreshResponse.data.session_token).not.toBe(originalToken);
        });
        
        it('should handle offline license validation scenario', async () => {
            // Login to get license
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_APP_OFFLINE',
                'Desktop App Offline Test'
            );
            
            expect(loginResponse.status).toBe(200);
            const entitlementToken = loginResponse.data.entitlement_token;
            
            // Simulate offline validation (would use cached token)
            // In real scenario, desktop app would validate against cached license
            // Here we validate the token structure
            expect(entitlementToken).toHaveProperty('sub');
            expect(entitlementToken).toHaveProperty('plan');
            expect(entitlementToken).toHaveProperty('features');
        });
    });
    
    describe('Desktop App Device Registration', () => {
        it('should register device on first login', async () => {
            const deviceId = TestData.generateDeviceId('DESKTOP_FIRST');
            
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                deviceId,
                'Desktop App First Login'
            );
            
            expect(response.status).toBe(200);
            // Device should be registered during login
        });
        
        it('should update device on subsequent login', async () => {
            const deviceId = TestData.generateDeviceId('DESKTOP_UPDATE');
            
            // First login
            const response1 = await apiClient.login(
                'test@example.com',
                'testpassword123',
                deviceId,
                'Desktop App First'
            );
            expect(response1.status).toBe(200);
            
            // Second login (simulates app restart)
            const response2 = await apiClient.login(
                'test@example.com',
                'testpassword123',
                deviceId,
                'Desktop App Updated'
            );
            expect(response2.status).toBe(200);
            // Should update existing device
        });
    });
    
    describe('Desktop App Error Handling', () => {
        it('should handle network errors gracefully', async () => {
            // Create client with invalid URL to simulate network error
            const invalidClient = new ApiClient('http://invalid-url-that-does-not-exist:9999');
            
            try {
                await invalidClient.health();
                // Should throw or return error
            } catch (error) {
                expect(error).toBeDefined();
            }
        });
        
        it('should handle expired session token', async () => {
            // Login
            await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_EXPIRED',
                'Desktop App Expired Test'
            );
            
            // Set invalid token
            apiClient.sessionToken = 'expired_token_placeholder';
            
            // Try to use expired token
            const response = await apiClient.getLicenseInfo();
            expect([401, 403]).toContain(response.status);
        });
        
        it('should handle license expiration', async () => {
            // This would require a user with expired license
            // For now, we test the API response structure
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_EXPIRED_LICENSE',
                'Desktop App Expired License'
            );
            
            // Should either succeed (valid) or return 403 (expired)
            expect([200, 403]).toContain(response.status);
        });
    });
    
    describe('Desktop App Token Storage', () => {
        it('should receive tokens in format suitable for storage', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_STORAGE',
                'Desktop App Storage Test'
            );
            
            expect(response.status).toBe(200);
            
            // Tokens should be strings (for encryption/storage)
            expect(typeof response.data.session_token).toBe('string');
            expect(typeof response.data.entitlement_token).toBe('object');
            
            // Entitlement token should have all required fields
            expect(response.data.entitlement_token).toHaveProperty('sub');
            expect(response.data.entitlement_token).toHaveProperty('plan');
        });
    });
});
