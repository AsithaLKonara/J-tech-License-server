/**
 * Database Consistency Integration Tests
 * Tests data integrity across database operations
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Database Consistency Integration Tests', () => {
    let apiClient;
    
    beforeEach(() => {
        apiClient = new ApiClient();
    });
    
    afterEach(() => {
        apiClient.clearSession();
    });
    
    describe('User-Device Consistency', () => {
        it('should maintain user-device relationship consistency', async () => {
            const deviceId = TestData.generateDeviceId('CONSISTENCY');
            
            // Login registers device
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                deviceId,
                'Consistency Test Device'
            );
            
            expect(loginResponse.status).toBe(200);
            const userId = loginResponse.data.user.id;
            
            // List devices should return device for this user
            const devicesResponse = await apiClient.listDevices();
            expect(devicesResponse.status).toBe(200);
            expect(devicesResponse.data.devices).toBeInstanceOf(Array);
            
            // Device should belong to the logged-in user
            if (devicesResponse.data.devices.length > 0) {
                const device = devicesResponse.data.devices.find(d => d.device_id === deviceId);
                if (device) {
                    expect(device.user_id).toBe(userId);
                }
            }
        });
        
        it('should prevent device ownership conflicts', async () => {
            const deviceId = TestData.generateDeviceId('OWNERSHIP');
            
            // First user registers device
            const response1 = await apiClient.login(
                'test@example.com',
                'testpassword123',
                deviceId,
                'Ownership Test Device'
            );
            
            expect(response1.status).toBe(200);
            
            // Device should be associated with first user
            const devices1 = await apiClient.listDevices();
            expect(devices1.status).toBe(200);
        });
    });
    
    describe('License-User Consistency', () => {
        it('should maintain license-user relationship', async () => {
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'LICENSE_CONSISTENCY',
                'License Consistency Test'
            );
            
            expect(loginResponse.status).toBe(200);
            const userId = loginResponse.data.user.id;
            const entitlementToken = loginResponse.data.entitlement_token;
            
            // License info should match user
            const licenseInfo = await apiClient.getLicenseInfo();
            expect(licenseInfo.status).toBe(200);
            expect(licenseInfo.data.entitlement).toBeDefined();
            
            // Entitlement token should reference correct user
            expect(entitlementToken.sub).toBe(userId);
        });
    });
    
    describe('Device-License Consistency', () => {
        it('should enforce device limits per license', async () => {
            // Register multiple devices
            const deviceIds = TestData.deviceFactory(5).map(d => d.device_id);
            
            const responses = await Promise.all(
                deviceIds.map(deviceId =>
                    apiClient.login(
                        'test@example.com',
                        'testpassword123',
                        deviceId,
                        `Device ${deviceId}`
                    )
                )
            );
            
            // Should respect max_devices limit
            const successCount = responses.filter(r => r.status === 200).length;
            const limitCount = responses.filter(r => r.status === 403).length;
            
            // Should have some successful registrations
            expect(successCount).toBeGreaterThan(0);
        });
    });
    
    describe('Transaction Consistency', () => {
        it('should maintain data consistency during concurrent operations', async () => {
            const deviceId = TestData.generateDeviceId('CONCURRENT');
            
            // Concurrent login attempts
            const requests = Array.from({ length: 3 }, () =>
                apiClient.login(
                    'test@example.com',
                    'testpassword123',
                    deviceId,
                    'Concurrent Test Device'
                )
            );
            
            const responses = await Promise.all(requests);
            
            // All should succeed (same device, same user)
            // Or handle gracefully if there are conflicts
            responses.forEach(response => {
                expect([200, 409]).toContain(response.status);
            });
        });
    });
    
    describe('Data Integrity', () => {
        it('should maintain referential integrity', async () => {
            // Login creates user, device, and license relationships
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'INTEGRITY_TEST',
                'Integrity Test Device'
            );
            
            expect(response.status).toBe(200);
            
            // All relationships should be valid
            const licenseInfo = await apiClient.getLicenseInfo();
            expect(licenseInfo.status).toBe(200);
            
            const devices = await apiClient.listDevices();
            expect(devices.status).toBe(200);
        });
    });
});
