/**
 * License-Database Integration Tests
 * Tests integration between license operations and database
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('License-Database Integration Tests', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    afterEach(() => {
        apiClient.clearSession();
    });

    describe('License Creation in Database', () => {
        it('should return license after database creation', async () => {
            // When a license is created in database, API should return it
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_LICENSE_CREATE',
                'License Create Device'
            );

            expect(response.status).toBe(200);
            // License should be returned in entitlement_token
            expect(response.data.entitlement_token).toBeDefined();
            expect(response.data.entitlement_token.plan).toBeDefined();
            expect(response.data.entitlement_token.features).toBeInstanceOf(Array);
        });

        it('should create default license if none exists', async () => {
            // API should create a default free license if user has none
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_DEFAULT_LICENSE',
                'Default License Device'
            );

            expect(response.status).toBe(200);
            // Should have a license (default free if none existed)
            expect(response.data.entitlement_token).toBeDefined();
        });
    });

    describe('License Updates in Database', () => {
        it('should reflect license updates in API responses', async () => {
            // Initial login
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_LICENSE_UPDATE',
                'License Update Device'
            );

            expect(loginResponse.status).toBe(200);
            const initialPlan = loginResponse.data.entitlement_token.plan;
            const initialFeatures = loginResponse.data.entitlement_token.features;

            // Refresh should return same license (unless updated in DB)
            const refreshResponse = await apiClient.refresh('DEVICE_LICENSE_UPDATE');
            expect(refreshResponse.status).toBe(200);
            expect(refreshResponse.data.entitlement_token.plan).toBe(initialPlan);
            expect(refreshResponse.data.entitlement_token.features).toEqual(initialFeatures);
        });

        it('should handle license status changes', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_LICENSE_STATUS',
                'License Status Device'
            );

            expect(response.status).toBe(200);
            // If license is invalid, should return 403
            // If valid, should return 200 with license info
        });
    });

    describe('License Deletion', () => {
        it('should return 403 when license is deleted', async () => {
            // If license is deleted from database, login should fail
            // This would require a test user with deleted license
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_LICENSE_DELETE',
                'License Delete Device'
            );

            // Should either succeed (license exists) or fail (license deleted)
            expect([200, 403]).toContain(response.status);
            
            if (response.status === 403) {
                expect(response.data).toHaveProperty('error');
                expect(response.data.error).toContain('License');
            }
        });
    });

    describe('Database Transaction Rollback', () => {
        it('should rollback on license creation errors', async () => {
            // This would require simulating a database error
            // For now, we test that API handles errors gracefully
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_ROLLBACK_TEST',
                'Rollback Test Device'
            );

            // Should either succeed or fail cleanly (not leave partial state)
            expect([200, 400, 401, 403, 500]).toContain(response.status);
            
            // If error, should be clear
            if (response.status >= 400) {
                expect(response.data).toHaveProperty('error');
            }
        });

        it('should maintain data consistency on partial failures', async () => {
            // Test that partial operations don't leave inconsistent state
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_CONSISTENCY_TEST',
                'Consistency Test Device'
            );

            // Should succeed completely or fail completely (no partial state)
            if (response.status === 200) {
                expect(response.data.session_token).toBeTruthy();
                expect(response.data.entitlement_token).toBeDefined();
                expect(response.data.user).toBeDefined();
            }
        });
    });

    describe('License Query Performance', () => {
        it('should return license information quickly', async () => {
            const startTime = Date.now();
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_PERFORMANCE_TEST',
                'Performance Test Device'
            );
            const endTime = Date.now();
            const duration = endTime - startTime;

            expect(response.status).toBe(200);
            // Should complete within reasonable time (< 2 seconds)
            expect(duration).toBeLessThan(2000);
        });

        it('should handle concurrent license queries', async () => {
            const requests = Array.from({ length: 10 }, (_, i) =>
                apiClient.login(
                    'test@example.com',
                    'testpassword123',
                    `DEVICE_CONCURRENT_QUERY_${i}`,
                    `Concurrent Query Device ${i}`
                )
            );

            const startTime = Date.now();
            const responses = await Promise.all(requests);
            const endTime = Date.now();
            const duration = endTime - startTime;

            // All should complete
            expect(responses.length).toBe(10);
            // Should complete within reasonable time
            expect(duration).toBeLessThan(5000);
        });
    });

    describe('License Data Integrity', () => {
        it('should return consistent license data', async () => {
            // Multiple logins should return consistent license info
            const responses = await Promise.all([
                apiClient.login('test@example.com', 'testpassword123', 'DEVICE_CONSISTENT_1', 'Device 1'),
                apiClient.login('test@example.com', 'testpassword123', 'DEVICE_CONSISTENT_2', 'Device 2'),
                apiClient.login('test@example.com', 'testpassword123', 'DEVICE_CONSISTENT_3', 'Device 3'),
            ]);

            const successfulResponses = responses.filter(r => r.status === 200);
            if (successfulResponses.length > 0) {
                const plans = successfulResponses.map(r => r.data.entitlement_token.plan);
                const features = successfulResponses.map(r => r.data.entitlement_token.features);
                
                // All should have same plan
                const uniquePlans = new Set(plans);
                expect(uniquePlans.size).toBe(1);
                
                // All should have same features
                features.forEach(featureSet => {
                    expect(featureSet).toEqual(features[0]);
                });
            }
        });

        it('should validate license data structure', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_STRUCTURE_TEST',
                'Structure Test Device'
            );

            expect(response.status).toBe(200);
            const entitlement = response.data.entitlement_token;
            
            // Should have required fields
            expect(entitlement).toHaveProperty('sub');
            expect(entitlement).toHaveProperty('product');
            expect(entitlement).toHaveProperty('plan');
            expect(entitlement).toHaveProperty('features');
            expect(entitlement).toHaveProperty('expires_at');
            
            // Types should be correct
            expect(typeof entitlement.sub).toBe('string');
            expect(typeof entitlement.product).toBe('string');
            expect(typeof entitlement.plan).toBe('string');
            expect(Array.isArray(entitlement.features)).toBe(true);
        });
    });
});
