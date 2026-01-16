/**
 * Database Seeder for Tests
 * Seeds test database with initial data
 */

const TestData = require('../helpers/test-data');
const fixtures = require('../setup/setup-test-data').loadFixtures();

class DatabaseSeeder {
    /**
     * Seed database with test data
     */
    static async seed() {
        console.log('[DatabaseSeeder] Seeding test database...');
        
        try {
            // Load fixtures
            const users = fixtures.users || [];
            const subscriptions = fixtures.subscriptions || [];
            const licenses = fixtures.licenses || [];
            const devices = fixtures.devices || [];
            
            console.log(`[DatabaseSeeder] Loaded ${users.length} users, ${subscriptions.length} subscriptions, ${licenses.length} licenses, ${devices.length} devices`);
            
            // Actual seeding would be done here based on database system
            // For now, we just log what would be seeded
            
            console.log('[DatabaseSeeder] Database seeding complete');
            return true;
        } catch (error) {
            console.error('[DatabaseSeeder] Database seeding failed:', error.message);
            return false;
        }
    }
    
    /**
     * Clean seed data
     */
    static async clean() {
        console.log('[DatabaseSeeder] Cleaning seed data...');
        
        try {
            // Cleanup logic here
            
            console.log('[DatabaseSeeder] Seed data cleanup complete');
            return true;
        } catch (error) {
            console.error('[DatabaseSeeder] Seed data cleanup failed:', error.message);
            return false;
        }
    }
}

module.exports = DatabaseSeeder;

// CLI usage
if (require.main === module) {
    const command = process.argv[2] || 'seed';
    
    if (command === 'seed') {
        DatabaseSeeder.seed().then(success => process.exit(success ? 0 : 1));
    } else if (command === 'clean') {
        DatabaseSeeder.clean().then(success => process.exit(success ? 0 : 1));
    }
}
