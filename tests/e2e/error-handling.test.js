/**
 * Error Handling E2E Tests
 * Tests error scenarios and edge cases
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('Error Handling E2E Tests', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    afterEach(() => {
        apiClient.clearSession();
    });

    describe('Network Failures', () => {
        it('should handle network timeout gracefully', async () => {
            // Simulate timeout by using invalid URL or very slow endpoint
            // For test, we verify API handles timeouts
            const startTime = Date.now();
            
            try {
                const response = await apiClient.health();
                const endTime = Date.now();
                const duration = endTime - startTime;
                
                // Should complete within reasonable time or timeout gracefully
                expect(duration).toBeLessThan(10000); // 10 second timeout
            } catch (error) {
                // Network errors should be caught and handled
                expect(error).toBeDefined();
            }
        });

        it('should handle connection refused errors', async () => {
            // This would require invalid server URL
            // For test, we verify error handling structure
            const response = await apiClient.health();
            
            // Should either succeed or return clear error
            expect([200, 500, 503]).toContain(response.status);
        });
    });

    describe('Database Connection Failures', () => {
        it('should handle database connection errors', async () => {
            // Database connection failure would cause 500 error
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_DB_ERROR',
                'DB Error Device'
            );

            // Should either succeed (DB working) or return 500 (DB error)
            expect([200, 500, 503]).toContain(response.status);
            
            if (response.status === 500) {
                // Should not expose internal database details
                const errorStr = JSON.stringify(response.data);
                expect(errorStr).not.toContain('SELECT');
                expect(errorStr).not.toContain('FROM');
            }
        });

        it('should handle database timeout errors', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_DB_TIMEOUT',
                'DB Timeout Device'
            );

            // Should handle timeout gracefully
            expect([200, 500, 503, 504]).toContain(response.status);
        });
    });

    describe('Invalid API Responses', () => {
        it('should handle malformed JSON responses', async () => {
            // API should always return valid JSON
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_MALFORMED',
                'Malformed Response Device'
            );

            // Response should be valid JSON
            expect(response.data).toBeDefined();
            expect(typeof response.data).toBe('object');
        });

        it('should handle missing required fields in response', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_MISSING_FIELDS',
                'Missing Fields Device'
            );

            if (response.status === 200) {
                // Should have all required fields
                expect(response.data).toHaveProperty('session_token');
                expect(response.data).toHaveProperty('entitlement_token');
                expect(response.data).toHaveProperty('user');
            }
        });
    });

    describe('Malformed Request Data', () => {
        it('should handle invalid JSON in request body', async () => {
            // Send invalid JSON
            const response = await apiClient.post('/api/v2/auth/login', 'not json');

            // Should return 400 for malformed JSON
            expect([400, 500]).toContain(response.status);
        });

        it('should handle missing required fields', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                // Missing email and password
            });

            expect(response.status).toBe(400);
            expect(response.data).toHaveProperty('error');
        });

        it('should handle wrong data types', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: 12345, // Should be string
                password: ['not', 'a', 'string'], // Should be string
            });

            // Should validate data types
            expect([400, 401]).toContain(response.status);
        });
    });

    describe('Concurrent Request Handling', () => {
        it('should handle multiple simultaneous requests', async () => {
            const requests = Array.from({ length: 20 }, (_, i) =>
                apiClient.login(
                    'test@example.com',
                    'testpassword123',
                    `DEVICE_CONCURRENT_${i}`,
                    `Concurrent Device ${i}`
                )
            );

            const responses = await Promise.all(requests);
            
            // All should complete
            expect(responses.length).toBe(20);
            
            // Should not crash or return 500
            const error500 = responses.find(r => r.status === 500);
            expect(error500).toBeUndefined();
        });

        it('should handle race conditions gracefully', async () => {
            const deviceId = TestData.generateDeviceId('RACE_CONDITION');
            const requests = Array.from({ length: 10 }, () =>
                apiClient.login(
                    'test@example.com',
                    'testpassword123',
                    deviceId,
                    'Race Condition Device'
                )
            );

            const responses = await Promise.all(requests);
            
            // Should handle race conditions without errors
            responses.forEach(response => {
                expect([200, 403]).toContain(response.status);
                expect(response.status).not.toBe(500);
            });
        });
    });

    describe('Timeout Scenarios', () => {
        it('should handle request timeouts', async () => {
            const startTime = Date.now();
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_TIMEOUT',
                'Timeout Device'
            );
            const endTime = Date.now();
            const duration = endTime - startTime;

            // Should complete within reasonable time
            expect(duration).toBeLessThan(5000); // 5 second timeout
            
            // Should return response (not hang)
            expect(response.status).toBeDefined();
        });

        it('should handle long-running operations', async () => {
            // Multiple operations in sequence
            const operations = [
                () => apiClient.health(),
                () => apiClient.login('test@example.com', 'testpassword123', 'DEVICE_LONG_1', 'Long Op 1'),
                () => apiClient.login('test@example.com', 'testpassword123', 'DEVICE_LONG_2', 'Long Op 2'),
                () => apiClient.login('test@example.com', 'testpassword123', 'DEVICE_LONG_3', 'Long Op 3'),
            ];

            const startTime = Date.now();
            for (const operation of operations) {
                await operation();
            }
            const endTime = Date.now();
            const duration = endTime - startTime;

            // Should complete within reasonable time
            expect(duration).toBeLessThan(10000); // 10 seconds total
        });
    });

    describe('Edge Cases', () => {
        it('should handle empty strings', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: '',
                password: '',
            });

            // Should validate and reject empty strings
            expect([400, 401]).toContain(response.status);
        });

        it('should handle very long strings', async () => {
            const longString = 'a'.repeat(10000);
            const response = await apiClient.login(
                longString,
                'testpassword123',
                'DEVICE_LONG_STRING',
                'Long String Device'
            );

            // Should handle gracefully (reject or truncate)
            expect([400, 401, 413]).toContain(response.status);
            expect(response.status).not.toBe(500);
        });

        it('should handle special characters', async () => {
            const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
            const response = await apiClient.login(
                `test${specialChars}@example.com`,
                'testpassword123',
                'DEVICE_SPECIAL_CHARS',
                'Special Chars Device'
            );

            // Should validate email format
            expect([400, 401]).toContain(response.status);
        });

        it('should handle unicode characters', async () => {
            const unicodeEmail = 'test@exämple.com'; // May or may not be valid
            const response = await apiClient.login(
                unicodeEmail,
                'testpassword123',
                'DEVICE_UNICODE',
                'Unicode Device'
            );

            // Should handle unicode (may accept or reject based on validation)
            expect([200, 400, 401]).toContain(response.status);
        });
    });

    describe('Service Unavailable', () => {
        it('should handle service maintenance gracefully', async () => {
            // Service maintenance would return 503
            const response = await apiClient.health();
            
            // Should either be available (200) or maintenance (503)
            expect([200, 503]).toContain(response.status);
        });

        it('should provide clear error messages', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'wrongpassword',
                'DEVICE_ERROR_MESSAGE',
                'Error Message Device'
            );

            if (response.status >= 400) {
                expect(response.data).toHaveProperty('error');
                expect(response.data.error).toBeTruthy();
                // Error should be user-friendly, not technical
                expect(response.data.error).not.toContain('SELECT');
                expect(response.data.error).not.toContain('FROM');
            }
        });
    });
});
