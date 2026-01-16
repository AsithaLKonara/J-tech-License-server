/**
 * Desktop App License Validation Tests
 * Tests license validation from desktop app perspective
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Desktop App License Validation Tests', () => {
    let apiClient;
    
    beforeEach(() => {
        apiClient = new ApiClient();
    });
    
    afterEach(() => {
        apiClient.clearSession();
    });
    
    describe('License Validation Flow', () => {
        it('should validate license after login', async () => {
            // Desktop app logs in
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_LICENSE_001',
                'Desktop License Test'
            );
            
            expect(loginResponse.status).toBe(200);
            const entitlementToken = loginResponse.data.entitlement_token;
            
            // Desktop app validates license
            const validateResponse = await apiClient.validateLicense(entitlementToken);
            
            expect(validateResponse.status).toBe(200);
            expect(validateResponse.data.valid).toBe(true);
        });
        
        it('should get license information', async () => {
            await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_LICENSE_INFO',
                'Desktop License Info Test'
            );
            
            const licenseInfo = await apiClient.getLicenseInfo();
            
            expect(licenseInfo.status).toBe(200);
            expect(licenseInfo.data.entitlement).toBeDefined();
            expect(licenseInfo.data.entitlement).toHaveProperty('plan');
            expect(licenseInfo.data.entitlement).toHaveProperty('features');
        });
    });
    
    describe('License Features', () => {
        it('should check feature access', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_FEATURES',
                'Desktop Features Test'
            );
            
            expect(loginResponse.status).toBe(200);
            const features = loginResponse.data.entitlement_token.features;
            
            expect(Array.isArray(features)).toBe(true);
            expect(features.length).toBeGreaterThan(0);
        });
    });
    
    describe('License Expiration', () => {
        it('should handle license expiration', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DESKTOP_EXPIRATION',
                'Desktop Expiration Test'
            );
            
            expect(response.status).toBe(200);
            
            if (response.data.entitlement_token.expires_at) {
                const expiresAt = new Date(response.data.entitlement_token.expires_at);
                const now = new Date();
                
                // Desktop app should check expiration
                expect(expiresAt > now || expiresAt === null).toBe(true);
            }
        });
    });
});
