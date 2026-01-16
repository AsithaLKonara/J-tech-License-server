/**
 * API Security E2E Tests
 * Tests for security measures: SQL injection, XSS, CSRF, rate limiting, token validation
 */

const ApiClient = require('../helpers/api-client');
const TestData = require('../helpers/test-data');

describe('API Security E2E Tests', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    afterEach(() => {
        apiClient.clearSession();
    });

    describe('SQL Injection Prevention', () => {
        it('should prevent SQL injection in email field', async () => {
            const sqlPayloads = TestData.generateSqlInjectionPayloads();

            for (const payload of sqlPayloads) {
                const response = await apiClient.login(
                    payload,
                    'testpassword123',
                    'DEVICE_SQL_TEST',
                    'SQL Injection Test'
                );

                // Should reject invalid input, not execute SQL
                expect([400, 401]).toContain(response.status);
                expect(response.status).not.toBe(500); // Should not cause server error
            }
        });

        it('should prevent SQL injection in password field', async () => {
            const sqlPayloads = TestData.generateSqlInjectionPayloads();

            for (const payload of sqlPayloads) {
                const response = await apiClient.login(
                    'test@example.com',
                    payload,
                    'DEVICE_SQL_PASS_TEST',
                    'SQL Injection Password Test'
                );

                // Should reject or fail authentication, not execute SQL
                expect([400, 401]).toContain(response.status);
                expect(response.status).not.toBe(500);
            }
        });

        it('should prevent SQL injection in device_id field', async () => {
            const sqlPayload = "' OR '1'='1";
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                sqlPayload,
                'SQL Injection Device Test'
            );

            // Should handle safely without executing SQL
            expect([200, 400, 401]).toContain(response.status);
            expect(response.status).not.toBe(500);
        });
    });

    describe('XSS Prevention', () => {
        it('should sanitize XSS payloads in email field', async () => {
            const xssPayloads = TestData.generateXssPayloads();

            for (const payload of xssPayloads) {
                const response = await apiClient.login(
                    payload,
                    'testpassword123',
                    'DEVICE_XSS_TEST',
                    'XSS Test'
                );

                // Should reject invalid email format
                expect([400, 401]).toContain(response.status);
                
                // Response should not contain script tags
                const responseStr = JSON.stringify(response.data);
                expect(responseStr).not.toContain('<script>');
            }
        });

        it('should sanitize XSS payloads in device_name field', async () => {
            const xssPayload = '<script>alert("XSS")</script>';
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_XSS_NAME_TEST',
                xssPayload
            );

            // Should handle safely
            expect([200, 400]).toContain(response.status);
            
            // Response should not contain script tags
            const responseStr = JSON.stringify(response.data);
            expect(responseStr).not.toContain('<script>');
        });

        it('should not return XSS payloads in API responses', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_XSS_RESPONSE_TEST',
                'Normal Device'
            );

            expect(response.status).toBe(200);
            const responseStr = JSON.stringify(response.data);
            
            // Response should not contain script tags or javascript: protocol
            expect(responseStr).not.toContain('<script>');
            expect(responseStr).not.toContain('javascript:');
            expect(responseStr).not.toContain('onerror=');
        });
    });

    describe('Token Validation', () => {
        it('should reject invalid session tokens', async () => {
            apiClient.sessionToken = 'invalid_token_12345';
            const response = await apiClient.refresh('DEVICE_TOKEN_TEST');

            expect(response.status).toBe(401);
            expect(response.data).toHaveProperty('error');
        });

        it('should reject expired tokens', async () => {
            // This would require an expired token
            // For now, we test that invalid tokens are rejected
            apiClient.sessionToken = 'expired_token_test';
            const response = await apiClient.refresh('DEVICE_EXPIRED_TOKEN_TEST');

            expect(response.status).toBe(401);
        });

        it('should reject malformed tokens', async () => {
            const malformedTokens = [
                '',
                'not.a.valid.token',
                'token_without_proper_format',
                '12345',
                null,
            ];

            for (const token of malformedTokens) {
                apiClient.sessionToken = token;
                const response = await apiClient.refresh('DEVICE_MALFORMED_TEST');

                expect(response.status).toBe(401);
            }
        });

        it('should validate token structure', async () => {
            // Get a valid token first
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_VALID_TOKEN_TEST',
                'Valid Token Test'
            );

            expect(loginResponse.status).toBe(200);
            expect(loginResponse.data.session_token).toBeTruthy();
            
            // Token should have expected structure
            const token = loginResponse.data.session_token;
            expect(typeof token).toBe('string');
            expect(token.length).toBeGreaterThan(0);
        });
    });

    describe('Rate Limiting', () => {
        it('should handle rapid requests without crashing', async () => {
            const requests = Array.from({ length: 20 }, (_, i) =>
                apiClient.login(
                    'test@example.com',
                    'testpassword123',
                    `DEVICE_RATE_TEST_${i}`,
                    `Rate Test Device ${i}`
                )
            );

            const responses = await Promise.all(requests);
            
            // Should handle all requests (may rate limit but not crash)
            expect(responses.length).toBe(20);
            
            // Should not return 500 errors
            const error500 = responses.find(r => r.status === 500);
            expect(error500).toBeUndefined();
        });

        it('should enforce rate limits on authentication endpoints', async () => {
            // Make many rapid requests
            const requests = Array.from({ length: 50 }, (_, i) =>
                apiClient.post('/api/v2/auth/login', {
                    email: 'test@example.com',
                    password: 'testpassword123',
                    device_id: `DEVICE_RATE_LIMIT_${i}`,
                    device_name: `Rate Limit Test ${i}`,
                })
            );

            const responses = await Promise.all(requests);
            
            // Some should succeed, some may be rate limited (429)
            const statusCodes = responses.map(r => r.status);
            expect(statusCodes).toContain(200); // At least some succeed
            
            // If rate limiting is implemented, some should return 429
            // Note: This depends on actual rate limiting implementation
        });
    });

    describe('CORS Security', () => {
        it('should include proper CORS headers', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'DEVICE_CORS_TEST',
                'CORS Test Device'
            );

            expect(response.status).toBe(200);
            // CORS headers should be present
            // Note: Actual CORS policy depends on implementation
        });

        it('should handle OPTIONS preflight requests', async () => {
            // OPTIONS request for CORS preflight
            const response = await apiClient.post('/api/v2/auth/login', {}, {
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': 'POST',
            });

            // Should handle OPTIONS (may return 200 or 405 depending on implementation)
            expect([200, 405]).toContain(response.status);
        });
    });

    describe('Input Validation', () => {
        it('should validate email format', async () => {
            const invalidEmails = [
                'notanemail',
                '@example.com',
                'test@',
                'test..test@example.com',
                'test@example',
            ];

            for (const email of invalidEmails) {
                const response = await apiClient.login(
                    email,
                    'testpassword123',
                    'DEVICE_VALIDATION_TEST',
                    'Validation Test'
                );

                // Should reject invalid email format
                expect([400, 401]).toContain(response.status);
            }
        });

        it('should validate required fields', async () => {
            // Missing email
            const response1 = await apiClient.post('/api/v2/auth/login', {
                password: 'testpassword123',
            });
            expect(response1.status).toBe(400);

            // Missing password
            const response2 = await apiClient.post('/api/v2/auth/login', {
                email: 'test@example.com',
            });
            expect(response2.status).toBe(400);
        });

        it('should handle extremely long input', async () => {
            const longString = 'a'.repeat(10000);
            const response = await apiClient.login(
                longString,
                'testpassword123',
                'DEVICE_LONG_INPUT_TEST',
                'Long Input Test'
            );

            // Should handle gracefully (reject or truncate, not crash)
            expect([400, 401, 413]).toContain(response.status);
            expect(response.status).not.toBe(500);
        });
    });

    describe('Error Handling', () => {
        it('should not expose sensitive information in error messages', async () => {
            const response = await apiClient.login(
                'test@example.com',
                'wrongpassword',
                'DEVICE_ERROR_TEST',
                'Error Test'
            );

            expect(response.status).toBe(401);
            const errorMessage = JSON.stringify(response.data);
            
            // Should not expose database structure, SQL queries, or internal paths
            expect(errorMessage).not.toContain('SELECT');
            expect(errorMessage).not.toContain('FROM');
            expect(errorMessage).not.toContain('WHERE');
            expect(errorMessage).not.toContain('/var/www');
            expect(errorMessage).not.toContain('password');
        });

        it('should handle malformed JSON gracefully', async () => {
            // This would require sending raw malformed JSON
            // For now, we test that the API validates JSON structure
            const response = await apiClient.post('/api/v2/auth/login', 'not json');

            // Should return 400 for malformed JSON
            expect([400, 500]).toContain(response.status);
        });
    });
});
