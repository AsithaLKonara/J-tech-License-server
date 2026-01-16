/**
 * Test Runner Wrapper
 * Executes test files with the test runner
 */

const testRunner = require('./helpers/test-runner');

// Set up globals for test files
global.describe = testRunner.describe.bind(testRunner);
global.it = testRunner.it.bind(testRunner);
global.beforeEach = testRunner.beforeEach.bind(testRunner);
global.afterEach = testRunner.afterEach.bind(testRunner);
global.beforeAll = testRunner.beforeAll.bind(testRunner);
global.afterAll = testRunner.afterAll.bind(testRunner);
global.expect = testRunner.expect;

// Load and execute test file
const path = require('path');
const fs = require('fs');

let testFile = process.argv[2];

if (!testFile) {
    console.error('Usage: node run-test.js <test-file>');
    process.exit(1);
}

// Resolve path relative to project root
if (!path.isAbsolute(testFile)) {
    // If relative, resolve from project root
    const projectRoot = path.resolve(__dirname, '..');
    testFile = path.resolve(projectRoot, testFile);
}

// Check if file exists
if (!fs.existsSync(testFile)) {
    console.error(`Test file not found: ${testFile}`);
    process.exit(1);
}

// Load test file (it will register tests with describe/it)
require(testFile);

// Run all registered tests
(async () => {
    const exitCode = await testRunner.run();
    process.exit(exitCode);
})();
