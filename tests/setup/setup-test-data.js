/**
 * Test Data Setup
 * Prepares test data before test execution
 */

const TestData = require('../helpers/test-data');
const fs = require('fs');
const path = require('path');

class TestDataSetup {
    /**
     * Load fixtures
     */
    static loadFixtures() {
        const fixturesDir = path.join(__dirname, '..', 'fixtures');
        const fixtures = {};
        
        const fixtureFiles = ['users.json', 'subscriptions.json', 'licenses.json', 'devices.json'];
        
        for (const file of fixtureFiles) {
            const filePath = path.join(fixturesDir, file);
            if (fs.existsSync(filePath)) {
                const content = fs.readFileSync(filePath, 'utf8');
                const key = file.replace('.json', '');
                fixtures[key] = JSON.parse(content);
            }
        }
        
        return fixtures;
    }
    
    /**
     * Setup test data
     */
    static async setup() {
        console.log('[TestDataSetup] Setting up test data...');
        
        try {
            const fixtures = this.loadFixtures();
            console.log('[TestDataSetup] Loaded fixtures:', Object.keys(fixtures));
            
            // Additional setup can be done here
            // For example, seeding database with test data
            
            console.log('[TestDataSetup] Test data setup complete');
            return true;
        } catch (error) {
            console.error('[TestDataSetup] Test data setup failed:', error.message);
            return false;
        }
    }
    
    /**
     * Cleanup test data
     */
    static async cleanup() {
        console.log('[TestDataSetup] Cleaning up test data...');
        
        try {
            // Cleanup logic here
            // For example, delete test users, devices, etc.
            
            console.log('[TestDataSetup] Test data cleanup complete');
            return true;
        } catch (error) {
            console.error('[TestDataSetup] Test data cleanup failed:', error.message);
            return false;
        }
    }
}

module.exports = TestDataSetup;

// CLI usage
if (require.main === module) {
    const command = process.argv[2] || 'setup';
    
    if (command === 'setup') {
        TestDataSetup.setup().then(success => process.exit(success ? 0 : 1));
    } else if (command === 'cleanup') {
        TestDataSetup.cleanup().then(success => process.exit(success ? 0 : 1));
    }
}
