/**
 * Test Data Generators
 * Provides utilities for generating test data, factories, and database seeding
 */

class TestData {
    static _counter = 0;
    
    /**
     * Get unique counter
     */
    static _getCounter() {
        return ++this._counter;
    }
    /**
     * Generate a unique email address
     */
    static generateEmail(prefix = 'test') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(7)}@test.com`;
    }

    /**
     * Generate a unique device ID
     */
    static generateDeviceId(prefix = 'DEVICE') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    }

    /**
     * Generate test user data
     */
    static generateUser(overrides = {}) {
        return {
            email: this.generateEmail(),
            password: 'testpassword123',
            device_id: this.generateDeviceId(),
            device_name: 'Test Device',
            ...overrides,
        };
    }
    
    /**
     * Test user factory - creates multiple users
     */
    static userFactory(count = 1, overrides = {}) {
        return Array.from({ length: count }, () => this.generateUser(overrides));
    }
    
    /**
     * Generate test subscription data
     */
    static generateSubscription(overrides = {}) {
        return {
            plan: 'monthly',
            status: 'active',
            stripe_customer_id: `cus_test_${Date.now()}`,
            stripe_subscription_id: `sub_test_${Date.now()}`,
            expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            ...overrides,
        };
    }
    
    /**
     * Test subscription factory
     */
    static subscriptionFactory(count = 1, overrides = {}) {
        return Array.from({ length: count }, () => this.generateSubscription(overrides));
    }
    
    /**
     * Generate test license/entitlement data
     */
    static generateLicense(overrides = {}) {
        return {
            plan: 'monthly',
            status: 'active',
            features: ['pattern_upload', 'firmware_generation'],
            max_devices: 3,
            expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            ...overrides,
        };
    }
    
    /**
     * Test license factory
     */
    static licenseFactory(count = 1, overrides = {}) {
        return Array.from({ length: count }, () => this.generateLicense(overrides));
    }
    
    /**
     * Generate test device data
     */
    static generateDevice(overrides = {}) {
        return {
            device_id: this.generateDeviceId(),
            device_name: `Test Device ${this._getCounter()}`,
            ...overrides,
        };
    }
    
    /**
     * Test device factory
     */
    static deviceFactory(count = 1, overrides = {}) {
        return Array.from({ length: count }, () => this.generateDevice(overrides));
    }
    
    /**
     * Generate test payment data
     */
    static generatePayment(overrides = {}) {
        return {
            amount: 999,
            currency: 'usd',
            status: 'succeeded',
            stripe_payment_intent_id: `pi_test_${Date.now()}`,
            ...overrides,
        };
    }
    
    /**
     * Test payment factory
     */
    static paymentFactory(count = 1, overrides = {}) {
        return Array.from({ length: count }, () => this.generatePayment(overrides));
    }

    /**
     * Generate test login payload
     */
    static generateLoginPayload(overrides = {}) {
        return {
            email: 'test@example.com',
            password: 'testpassword123',
            device_id: this.generateDeviceId(),
            device_name: 'Test Device',
            ...overrides,
        };
    }

    /**
     * Generate test refresh payload
     */
    static generateRefreshPayload(sessionToken, overrides = {}) {
        return {
            session_token: sessionToken,
            device_id: this.generateDeviceId(),
            ...overrides,
        };
    }

    /**
     * Generate SQL injection test payloads
     */
    static generateSqlInjectionPayloads() {
        return [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1--",
        ];
    }

    /**
     * Generate XSS test payloads
     */
    static generateXssPayloads() {
        return [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')"></iframe>',
        ];
    }
    
    /**
     * Cleanup test data (placeholder - implement based on your needs)
     */
    static async cleanup(testUsers = [], testDevices = []) {
        // This should be implemented to clean up test data
        // For example, delete test users, devices, etc.
        console.log(`[TestData] Cleanup: ${testUsers.length} users, ${testDevices.length} devices`);
    }
    
    /**
     * Generate test data set for complete user scenario
     */
    static generateUserScenario(overrides = {}) {
        const user = this.generateUser(overrides.user);
        const subscription = this.generateSubscription(overrides.subscription);
        const license = this.generateLicense(overrides.license);
        const devices = this.deviceFactory(overrides.deviceCount || 1, overrides.devices);
        
        return {
            user,
            subscription,
            license,
            devices,
        };
    }
}

module.exports = TestData;
