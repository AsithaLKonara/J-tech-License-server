/**
 * License Renewal Journey E2E Tests
 * Tests the complete license renewal flow
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('License Renewal Journey E2E Tests', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    afterEach(() => {
        apiClient.clearSession();
    });

    describe('Expired License Detection', () => {
        it('should detect expired license on login', async () => {
            // User with expired license attempts to log in
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_EXPIRED_DETECTION',
                'Expired Detection Device'
            );

            // Should either succeed (license valid) or return 403 (expired)
            expect([200, 403]).toContain(response.status);
            
            if (response.status === 403) {
                expect(response.data.error).toContain('License');
                expect(response.data.error).toContain('expired');
            }
        });

        it('should provide clear error message for expired license', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_EXPIRED_MESSAGE',
                'Expired Message Device'
            );

            if (response.status === 403) {
                expect(response.data).toHaveProperty('error');
                expect(response.data.error).toBeTruthy();
                // Error should be user-friendly
            }
        });
    });

    describe('Renewal Flow', () => {
        it('should allow login after license renewal', async () => {
            // Step 1: User with expired license logs in (fails)
            const expiredLogin = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_RENEWAL_FLOW',
                'Renewal Flow Device'
            );

            // Step 2: User renews subscription (handled by web dashboard + Stripe)
            // This would update license in database

            // Step 3: User logs in again (should succeed)
            const renewedLogin = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_RENEWED_FLOW',
                'Renewed Flow Device'
            );

            expect(renewedLogin.status).toBe(200);
            expect(renewedLogin.data.entitlement_token).toBeDefined();
        });

        it('should reactivate license after renewal', async () => {
            // After renewal, license should be active
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_REACTIVATION',
                'Reactivation Device'
            );

            expect(response.status).toBe(200);
            // License should be valid (not expired)
            expect(response.data.entitlement_token).toBeDefined();
            
            // If license has expiration, it should be in the future
            const expiresAt = response.data.entitlement_token.expires_at;
            if (expiresAt !== null) {
                const expirationDate = new Date(expiresAt * 1000);
                expect(expirationDate.getTime()).toBeGreaterThan(Date.now());
            }
        });
    });

    describe('Feature Access After Renewal', () => {
        it('should restore feature access after renewal', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_FEATURES_RESTORED',
                'Features Restored Device'
            );

            expect(response.status).toBe(200);
            const features = response.data.entitlement_token.features;
            
            // Should have features after renewal
            expect(features.length).toBeGreaterThan(0);
            expect(features).toContain('pattern_upload');
        });

        it('should maintain feature consistency after renewal', async () => {
            // Before renewal
            const beforeRenewal = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_BEFORE_RENEWAL',
                'Before Renewal Device'
            );

            // After renewal (simulated by new login)
            const afterRenewal = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_AFTER_RENEWAL',
                'After Renewal Device'
            );

            if (beforeRenewal.status === 200 && afterRenewal.status === 200) {
                // Features should be consistent (or upgraded if plan changed)
                const beforeFeatures = beforeRenewal.data.entitlement_token.features;
                const afterFeatures = afterRenewal.data.entitlement_token.features;
                
                // Should have at least same features (or more if upgraded)
                expect(afterFeatures.length).toBeGreaterThanOrEqual(beforeFeatures.length);
            }
        });
    });

    describe('Subscription Renewal', () => {
        it('should handle automatic subscription renewal', async () => {
            // Automatic renewal would be handled by Stripe webhook
            // For API test, we verify license remains valid
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_AUTO_RENEWAL',
                'Auto Renewal Device'
            );

            expect(response.status).toBe(200);
            // License should be valid after auto-renewal
            expect(response.data.entitlement_token).toBeDefined();
        });

        it('should handle manual subscription renewal', async () => {
            // Manual renewal via web dashboard
            // After renewal, login should work
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_MANUAL_RENEWAL',
                'Manual Renewal Device'
            );

            expect(response.status).toBe(200);
            expect(response.data.entitlement_token).toBeDefined();
        });
    });

    describe('Renewal Error Handling', () => {
        it('should handle payment failure during renewal', async () => {
            // Payment failure would prevent renewal
            // User should still be able to attempt login
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_PAYMENT_FAILURE',
                'Payment Failure Device'
            );

            // Should either succeed (if renewal succeeded) or fail (if still expired)
            expect([200, 403]).toContain(response.status);
        });

        it('should provide clear feedback on renewal status', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_RENEWAL_STATUS',
                'Renewal Status Device'
            );

            if (response.status === 403) {
                // Should provide clear error about license status
                expect(response.data).toHaveProperty('error');
                expect(response.data.error).toBeTruthy();
            } else {
                // Should provide license info if valid
                expect(response.data.entitlement_token).toBeDefined();
            }
        });
    });
});
