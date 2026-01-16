/**
 * Service Setup for Tests
 * Checks service health and waits for services to be ready
 */

const TestEnvironment = require('../helpers/test-environment');

class ServiceSetup {
    /**
     * Check all required services
     */
    static async checkServices() {
        console.log('[ServiceSetup] Checking services...');
        
        const baseUrl = TestEnvironment.getBaseURL();
        const isHealthy = await TestEnvironment.checkServiceHealth(baseUrl);
        
        if (isHealthy) {
            console.log(`[ServiceSetup] Service at ${baseUrl} is healthy`);
            return true;
        } else {
            console.warn(`[ServiceSetup] Service at ${baseUrl} is not healthy`);
            return false;
        }
    }
    
    /**
     * Wait for services to be ready
     */
    static async waitForServices(maxAttempts = 30, delay = 1000) {
        console.log('[ServiceSetup] Waiting for services to be ready...');
        
        const baseUrl = TestEnvironment.getBaseURL();
        const isReady = await TestEnvironment.waitForService(baseUrl, maxAttempts, delay);
        
        if (isReady) {
            console.log('[ServiceSetup] Services are ready');
            return true;
        } else {
            console.error('[ServiceSetup] Services are not ready');
            return false;
        }
    }
}

module.exports = ServiceSetup;

// CLI usage
if (require.main === module) {
    const command = process.argv[2] || 'check';
    
    if (command === 'check') {
        ServiceSetup.checkServices().then(success => process.exit(success ? 0 : 1));
    } else if (command === 'wait') {
        ServiceSetup.waitForServices().then(success => process.exit(success ? 0 : 1));
    }
}
