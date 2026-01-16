/**
 * Health Check E2E Tests
 * Tests for API health check endpoint
 */

const ApiClient = require('../helpers/api-client');

describe('Health Check E2E Tests', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    describe('GET /api/v2/health', () => {
        it('should return health status', async () => {
            const response = await apiClient.health();

            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('status');
            expect(response.data.status).toBe('ok');
            expect(response.data).toHaveProperty('timestamp');
        });

        it('should include timestamp in response', async () => {
            const response = await apiClient.health();

            expect(response.status).toBe(200);
            expect(response.data.timestamp).toBeDefined();
            expect(typeof response.data.timestamp).toBe('string');
        });

        it('should include version in response', async () => {
            const response = await apiClient.health();

            expect(response.status).toBe(200);
            // Version is optional but if present should be valid
            if (response.data.version) {
                expect(typeof response.data.version).toBe('string');
            }
        });

        it('should be accessible without authentication', async () => {
            // Health check should be public
            apiClient.clearSession();
            const response = await apiClient.health();

            expect(response.status).toBe(200);
        });

        it('should return quickly', async () => {
            const startTime = Date.now();
            const response = await apiClient.health();
            const endTime = Date.now();
            const duration = endTime - startTime;

            expect(response.status).toBe(200);
            // Should respond within 1 second
            expect(duration).toBeLessThan(1000);
        });
    });
});
