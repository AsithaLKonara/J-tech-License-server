#!/usr/bin/env node
/**
 * Run Automated Tests
 * Runs all automated API and upload-bridge verification tests
 */

const { spawn } = require('child_process');
const path = require('path');

const SERVER_URL = process.env.LICENSE_SERVER_URL || 'http://localhost:8000';

console.log('========================================');
console.log('Upload Bridge - Automated Tests');
console.log('========================================');
console.log('');
console.log(`Server URL: ${SERVER_URL}`);
console.log('');

// Check if server is accessible
async function checkServer() {
    try {
        const fetch = require('node-fetch');
        const response = await fetch(`${SERVER_URL}/api/v2/health`);
        if (response.ok) {
            console.log('✅ Server is accessible');
            return true;
        } else {
            console.log('⚠️  Server returned non-200 status');
            return false;
        }
    } catch (error) {
        console.log('❌ Server is not accessible');
        console.log(`   Error: ${error.message}`);
        console.log('');
        console.log('Please ensure the web dashboard is running:');
        console.log('  cd apps/web-dashboard');
        console.log('  php artisan serve');
        console.log('');
        return false;
    }
}

// Run tests
async function runTests() {
    const serverAvailable = await checkServer();
    
    if (!serverAvailable) {
        console.log('⚠️  Continuing with tests anyway (some may fail)');
        console.log('');
    }

    console.log('Running API endpoint tests...');
    console.log('');

    return new Promise((resolve, reject) => {
        const jest = spawn('npx', ['jest', '--testPathPattern=automated', '--verbose'], {
            stdio: 'inherit',
            shell: true,
            cwd: __dirname
        });

        jest.on('close', (code) => {
            console.log('');
            console.log('========================================');
            if (code === 0) {
                console.log('✅ All tests passed!');
                resolve(0);
            } else {
                console.log(`⚠️  Tests completed with exit code ${code}`);
                console.log('Some tests may have failed (this is OK if server is not running)');
                resolve(code);
            }
            console.log('========================================');
        });

        jest.on('error', (error) => {
            console.error('Error running tests:', error);
            reject(error);
        });
    });
}

// Main
(async () => {
    try {
        const exitCode = await runTests();
        process.exit(exitCode);
    } catch (error) {
        console.error('Fatal error:', error);
        process.exit(1);
    }
})();
