/**
 * All APIs Test
 * Tests for various API endpoints
 */

const ApiClient = require('../helpers/api-client');

describe('All APIs Tests', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    describe('Device Registration', () => {
        it('should register device', async () => {
            // First login to get session token
            const loginResponse = await apiClient.login('test@example.com', 'testpassword123', 'device_desktop_001', 'Updated Desktop PC');
            
            expect(loginResponse.status).toBe(200);
            expect(loginResponse.data).toHaveProperty('session_token');
            expect(loginResponse.data).toHaveProperty('entitlement_token');
            expect(loginResponse.data).toHaveProperty('user');
        });
    });
});