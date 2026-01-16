/**
 * Test Teardown Utilities
 * Cleans up after test execution
 */

const TestEnvironment = require('../helpers/test-environment');
const TestData = require('../helpers/test-data');
const TestDataSetup = require('./setup-test-data');

class TestTeardown {
    /**
     * Complete teardown
     */
    static async teardown() {
        console.log('[TestTeardown] Starting teardown...');
        
        try {
            // Cleanup test data
            await TestDataSetup.cleanup();
            
            // Cleanup test environment
            TestEnvironment.cleanupIsolation();
            
            // Teardown database if needed
            // await TestEnvironment.teardownDatabase();
            
            console.log('[TestTeardown] Teardown complete');
            return true;
        } catch (error) {
            console.error('[TestTeardown] Teardown failed:', error.message);
            return false;
        }
    }
}

module.exports = TestTeardown;

// CLI usage
if (require.main === module) {
    TestTeardown.teardown().then(success => process.exit(success ? 0 : 1));
}
