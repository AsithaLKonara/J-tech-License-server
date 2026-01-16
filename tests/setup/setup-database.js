/**
 * Database Setup for Tests
 * Sets up test database before test execution
 */

const TestEnvironment = require('../helpers/test-environment');

class DatabaseSetup {
    /**
     * Setup test database
     */
    static async setup() {
        console.log('[DatabaseSetup] Setting up test database...');
        
        try {
            await TestEnvironment.setupDatabase();
            console.log('[DatabaseSetup] Database setup complete');
            return true;
        } catch (error) {
            console.error('[DatabaseSetup] Database setup failed:', error.message);
            return false;
        }
    }
    
    /**
     * Reset test database
     */
    static async reset() {
        console.log('[DatabaseSetup] Resetting test database...');
        
        try {
            await TestEnvironment.resetDatabase();
            console.log('[DatabaseSetup] Database reset complete');
            return true;
        } catch (error) {
            console.error('[DatabaseSetup] Database reset failed:', error.message);
            return false;
        }
    }
    
    /**
     * Teardown test database
     */
    static async teardown() {
        console.log('[DatabaseSetup] Tearing down test database...');
        
        try {
            await TestEnvironment.teardownDatabase();
            console.log('[DatabaseSetup] Database teardown complete');
            return true;
        } catch (error) {
            console.error('[DatabaseSetup] Database teardown failed:', error.message);
            return false;
        }
    }
}

module.exports = DatabaseSetup;

// CLI usage
if (require.main === module) {
    const command = process.argv[2] || 'setup';
    
    if (command === 'setup') {
        DatabaseSetup.setup().then(success => process.exit(success ? 0 : 1));
    } else if (command === 'reset') {
        DatabaseSetup.reset().then(success => process.exit(success ? 0 : 1));
    } else if (command === 'teardown') {
        DatabaseSetup.teardown().then(success => process.exit(success ? 0 : 1));
    }
}
