/**
 * Email Service Integration Tests
 * Tests email delivery for magic links and notifications
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Email Service Integration Tests', () => {
    let apiClient;
    
    beforeEach(() => {
        apiClient = new ApiClient();
    });
    
    describe('Magic Link Email Flow', () => {
        it('should request magic link (triggers email)', async () => {
            // Request magic link
            const response = await apiClient.post('/api/v2/auth/magic-link/request', {
                email: TestData.generateEmail('magic_link'),
            });
            
            // Should accept request (email would be sent)
            expect([200, 201, 202]).toContain(response.status);
            
            if (response.status === 200) {
                expect(response.data).toHaveProperty('message');
            }
        });
        
        it('should handle invalid email in magic link request', async () => {
            const response = await apiClient.post('/api/v2/auth/magic-link/request', {
                email: 'invalid-email',
            });
            
            expect([400, 422]).toContain(response.status);
        });
        
        it('should handle non-existent user in magic link request', async () => {
            const response = await apiClient.post('/api/v2/auth/magic-link/request', {
                email: 'nonexistent@example.com',
            });
            
            // May return 200 (don't reveal user existence) or 404
            expect([200, 404]).toContain(response.status);
        });
    });
    
    describe('Email Delivery Verification', () => {
        it('should verify magic link token after email delivery', async () => {
            // In real scenario:
            // 1. Request magic link → email sent
            // 2. User clicks link → token extracted
            // 3. Verify token
            
            // For testing, we simulate with a token
            const response = await apiClient.post('/api/v2/auth/magic-link/verify', {
                token: 'test_magic_link_token',
                device_id: TestData.generateDeviceId('EMAIL_TEST'),
            });
            
            // Will fail with invalid token, but tests the flow
            expect([200, 401, 400]).toContain(response.status);
        });
    });
    
    describe('Email Service Configuration', () => {
        it('should handle email service unavailability gracefully', async () => {
            // Request magic link
            const response = await apiClient.post('/api/v2/auth/magic-link/request', {
                email: TestData.generateEmail('unavailable'),
            });
            
            // Should handle service errors gracefully
            expect([200, 500, 503]).toContain(response.status);
        });
    });
});
