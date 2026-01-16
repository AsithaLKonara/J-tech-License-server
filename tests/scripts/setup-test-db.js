/**
 * Test Database Setup Script
 * Cleans up test data before running tests
 */

const { execSync } = require('child_process');
const path = require('path');

console.log('Setting up test database...');

const webDashboardPath = path.resolve(__dirname, '../../apps/web-dashboard');
const phpPath = process.env.PHP_PATH || 'php';

try {
    // Change to web-dashboard directory
    process.chdir(webDashboardPath);
    
    // Run artisan command to clean up devices
    console.log('Cleaning up test devices...');
    execSync(`${phpPath} artisan tinker --execute="App\\Models\\Device::where('user_id', 'ebdc276b-c75e-4841-b775-46b148b2a7bf')->delete();"`, {
        stdio: 'inherit',
        cwd: webDashboardPath
    });
    
    console.log('✓ Test database setup complete');
} catch (error) {
    console.error('Error setting up test database:', error.message);
    // Don't fail - tests might still work
    console.log('Continuing with tests...');
}
