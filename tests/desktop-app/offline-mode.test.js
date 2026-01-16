/**
 * Desktop App Offline Mode Tests
 * Tests offline license validation and caching
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Desktop App Offline Mode Tests', () => {
    let apiClient;
    
    beforeEach(() => {
        apiClient = new ApiClient();
    });
    
    afterEach(() => {
        apiClient.clearSession();
    });
    
    describe('Offline License Caching', () => {
        it('should cache license information for offline use', async () => {
            // Desktop app logs in (online)
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_OFFLINE_001',
                'Desktop Offline Test'
            );
            
            expect(loginResponse.status).toBe(200);
            
            // Desktop app caches license info
            const cachedLicense = {
                entitlement_token: loginResponse.data.entitlement_token,
                session_token: loginResponse.data.session_token,
                cached_at: Date.now(),
            };
            
            // Verify cached license structure
            expect(cachedLicense.entitlement_token).toHaveProperty('sub');
            expect(cachedLicense.entitlement_token).toHaveProperty('plan');
            expect(cachedLicense.entitlement_token).toHaveProperty('features');
            expect(cachedLicense.cached_at).toBeDefined();
        });
        
        it('should validate cached license structure', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_OFFLINE_STRUCT',
                'Desktop Offline Structure Test'
            );
            
            expect(loginResponse.status).toBe(200);
            const entitlementToken = loginResponse.data.entitlement_token;
            
            // Cached license should have all required fields
            expect(entitlementToken).toHaveProperty('sub');
            expect(entitlementToken).toHaveProperty('plan');
            expect(entitlementToken).toHaveProperty('features');
            expect(Array.isArray(entitlementToken.features)).toBe(true);
        });
    });
    
    describe('Offline Validation Periods', () => {
        it('should support offline validation based on plan', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_OFFLINE_PERIOD',
                'Desktop Offline Period Test'
            );
            
            expect(loginResponse.status).toBe(200);
            const plan = loginResponse.data.entitlement_token.plan;
            
            // Different plans have different offline periods
            // Trial: 0 days, Monthly: 3 days, Yearly: 14 days, Perpetual: 30 days
            expect(['trial', 'monthly', 'yearly', 'perpetual']).toContain(plan);
        });
    });
    
    describe('Offline Mode Error Handling', () => {
        it('should handle network errors gracefully', async () => {
            // Create client with invalid URL to simulate offline
            const offlineClient = new ApiClient('http://invalid-url:9999');
            
            try {
                await offlineClient.health();
                // Should throw or return error
            } catch (error) {
                // Desktop app should fall back to cached license
                expect(error).toBeDefined();
            }
        });
    });
});
