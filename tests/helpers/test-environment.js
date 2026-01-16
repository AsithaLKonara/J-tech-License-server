/**
 * Test Environment Utilities
 * Environment detection, service health checks, and test isolation
 */

const ApiClient = require('./api-client');

class TestEnvironment {
    /**
     * Detect if running in CI environment
     */
    static isCI() {
        return !!(
            process.env.CI ||
            process.env.CONTINUOUS_INTEGRATION ||
            process.env.GITHUB_ACTIONS ||
            process.env.GITLAB_CI ||
            process.env.JENKINS_URL
        );
    }
    
    /**
     * Detect if running locally
     */
    static isLocal() {
        return !this.isCI();
    }
    
    /**
     * Get test environment name
     */
    static getEnvironment() {
        if (this.isCI()) {
            return process.env.CI_ENVIRONMENT || 'ci';
        }
        return process.env.NODE_ENV || 'local';
    }
    
    /**
     * Get base URL for API
     */
    static getBaseURL() {
        return process.env.LICENSE_SERVER_URL || 
               process.env.API_URL || 
               'http://localhost:8000';
    }
    
    /**
     * Check if service is healthy
     */
    static async checkServiceHealth(baseUrl = null) {
        const url = baseUrl || this.getBaseURL();
        const client = new ApiClient(url, { retries: 1, timeout: 5000 });
        
        try {
            const response = await client.health();
            return response.status === 200;
        } catch (error) {
            console.warn(`[TestEnvironment] Service health check failed: ${error.message}`);
            return false;
        }
    }
    
    /**
     * Wait for service to be ready
     */
    static async waitForService(baseUrl = null, maxAttempts = 30, delay = 1000) {
        const url = baseUrl || this.getBaseURL();
        console.log(`[TestEnvironment] Waiting for service at ${url}...`);
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            const isHealthy = await this.checkServiceHealth(url);
            if (isHealthy) {
                console.log(`[TestEnvironment] Service is ready after ${attempt} attempts`);
                return true;
            }
            
            if (attempt < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        
        console.error(`[TestEnvironment] Service not ready after ${maxAttempts} attempts`);
        return false;
    }
    
    /**
     * Setup test database (placeholder - implement based on your database)
     */
    static async setupDatabase() {
        // This should be implemented to setup test database
        // For example: create tables, seed initial data, etc.
        console.log('[TestEnvironment] Setting up test database...');
        // Implementation depends on database system
    }
    
    /**
     * Teardown test database (placeholder - implement based on your database)
     */
    static async teardownDatabase() {
        // This should be implemented to cleanup test database
        console.log('[TestEnvironment] Tearing down test database...');
        // Implementation depends on database system
    }
    
    /**
     * Reset test database (placeholder - implement based on your database)
     */
    static async resetDatabase() {
        // This should be implemented to reset test database
        console.log('[TestEnvironment] Resetting test database...');
        // Implementation depends on database system
    }
    
    /**
     * Get test configuration
     */
    static getConfig() {
        return {
            environment: this.getEnvironment(),
            isCI: this.isCI(),
            isLocal: this.isLocal(),
            baseURL: this.getBaseURL(),
            timeout: parseInt(process.env.TEST_TIMEOUT || '30000'),
            retries: parseInt(process.env.TEST_RETRIES || '3'),
            logging: process.env.TEST_LOGGING !== 'false',
        };
    }
    
    /**
     * Setup test isolation
     */
    static setupIsolation() {
        // Set unique test run ID
        process.env.TEST_RUN_ID = `test_${Date.now()}_${Math.random().toString(36).substring(7)}`;
        
        // Set test environment variables
        process.env.TEST_MODE = 'true';
        
        console.log(`[TestEnvironment] Test isolation setup with ID: ${process.env.TEST_RUN_ID}`);
    }
    
    /**
     * Cleanup test isolation
     */
    static cleanupIsolation() {
        delete process.env.TEST_RUN_ID;
        delete process.env.TEST_MODE;
        console.log('[TestEnvironment] Test isolation cleaned up');
    }
    
    /**
     * Get test run ID
     */
    static getTestRunId() {
        return process.env.TEST_RUN_ID || `test_${Date.now()}`;
    }
}

module.exports = TestEnvironment;
