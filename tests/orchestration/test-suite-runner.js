/**
 * Test Suite Runner
 * Orchestrates test execution with discovery, grouping, parallel execution, and result aggregation
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class TestSuiteRunner {
    constructor(options = {}) {
        this.options = {
            parallel: options.parallel !== false,
            maxConcurrency: options.maxConcurrency || 4,
            testTimeout: options.testTimeout || 30000,
            testDir: options.testDir || path.join(__dirname, '..'),
            outputDir: options.outputDir || path.join(__dirname, '..', '..', 'test-results'),
            ...options,
        };
        this.results = {
            suites: [],
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0,
            duration: 0,
            startTime: null,
            endTime: null,
        };
    }
    
    /**
     * Discover test files
     */
    discoverTests(directory = null) {
        const testDir = directory || this.options.testDir;
        const testFiles = [];
        
        const discover = (dir) => {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                
                if (entry.isDirectory()) {
                    // Skip node_modules and other ignored directories
                    if (!['node_modules', '.git', 'vendor'].includes(entry.name)) {
                        discover(fullPath);
                    }
                } else if (entry.isFile()) {
                    // Match test files
                    if (entry.name.match(/\.test\.(js|ts)$/i) || 
                        entry.name.match(/\.spec\.(js|ts)$/i)) {
                        testFiles.push(fullPath);
                    }
                }
            }
        };
        
        discover(testDir);
        return testFiles;
    }
    
    /**
     * Group tests by category
     */
    groupTests(testFiles) {
        const groups = {
            api: [],
            integration: [],
            security: [],
            e2e: [],
            desktopApp: [],
            other: [],
        };
        
        for (const file of testFiles) {
            const relativePath = path.relative(this.options.testDir, file);
            
            if (relativePath.includes('api/')) {
                groups.api.push(file);
            } else if (relativePath.includes('integration/')) {
                groups.integration.push(file);
            } else if (relativePath.includes('security/')) {
                groups.security.push(file);
            } else if (relativePath.includes('e2e/')) {
                groups.e2e.push(file);
            } else if (relativePath.includes('desktop-app/')) {
                groups.desktopApp.push(file);
            } else {
                groups.other.push(file);
            }
        }
        
        return groups;
    }
    
    /**
     * Run a single test file
     */
    async runTestFile(testFile) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const relativePath = path.relative(this.options.testDir, testFile);
            
            console.log(`[TestRunner] Running: ${relativePath}`);
            
            // Use the test runner wrapper to execute tests
            const runTestScript = path.join(this.options.testDir, 'run-test.js');
            const child = spawn('node', [runTestScript, testFile], {
                cwd: this.options.testDir,
                env: { ...process.env, NODE_ENV: 'test' },
                stdio: ['pipe', 'pipe', 'pipe'],
            });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            const timeout = setTimeout(() => {
                child.kill();
                resolve({
                    file: relativePath,
                    status: 'timeout',
                    duration: this.options.testTimeout,
                    stdout,
                    stderr,
                    error: 'Test timeout',
                });
            }, this.options.testTimeout);
            
            child.on('close', (code) => {
                clearTimeout(timeout);
                const duration = Date.now() - startTime;
                
                resolve({
                    file: relativePath,
                    status: code === 0 ? 'passed' : 'failed',
                    exitCode: code,
                    duration,
                    stdout,
                    stderr,
                });
            });
        });
    }
    
    /**
     * Run tests in parallel with concurrency limit
     */
    async runTestsParallel(testFiles) {
        const results = [];
        const queue = [...testFiles];
        const running = [];
        
        const runNext = async () => {
            if (queue.length === 0 && running.length === 0) {
                return;
            }
            
            if (queue.length === 0 || running.length >= this.options.maxConcurrency) {
                await Promise.race(running);
                return runNext();
            }
            
            const testFile = queue.shift();
            const promise = this.runTestFile(testFile).then((result) => {
                results.push(result);
                const index = running.indexOf(promise);
                if (index > -1) {
                    running.splice(index, 1);
                }
            });
            
            running.push(promise);
            return runNext();
        };
        
        await runNext();
        return results;
    }
    
    /**
     * Run tests sequentially
     */
    async runTestsSequential(testFiles) {
        const results = [];
        
        for (const testFile of testFiles) {
            const result = await this.runTestFile(testFile);
            results.push(result);
        }
        
        return results;
    }
    
    /**
     * Aggregate test results
     */
    aggregateResults(results) {
        this.results.suites = results;
        this.results.total = results.length;
        this.results.passed = results.filter(r => r.status === 'passed').length;
        this.results.failed = results.filter(r => r.status === 'failed').length;
        this.results.skipped = results.filter(r => r.status === 'skipped').length;
        this.results.duration = results.reduce((sum, r) => sum + (r.duration || 0), 0);
    }
    
    /**
     * Run all tests
     */
    async run() {
        this.results.startTime = Date.now();
        console.log('[TestRunner] Starting test suite...');
        console.log(`[TestRunner] Test directory: ${this.options.testDir}`);
        
        // Discover tests
        const testFiles = this.discoverTests();
        console.log(`[TestRunner] Found ${testFiles.length} test files`);
        
        if (testFiles.length === 0) {
            console.warn('[TestRunner] No test files found');
            return this.results;
        }
        
        // Group tests
        const groups = this.groupTests(testFiles);
        console.log('[TestRunner] Test groups:');
        Object.entries(groups).forEach(([group, files]) => {
            if (files.length > 0) {
                console.log(`  ${group}: ${files.length} files`);
            }
        });
        
        // Run tests
        let allResults = [];
        
        if (this.options.parallel) {
            console.log(`[TestRunner] Running tests in parallel (max ${this.options.maxConcurrency} concurrent)`);
            allResults = await this.runTestsParallel(testFiles);
        } else {
            console.log('[TestRunner] Running tests sequentially');
            allResults = await this.runTestsSequential(testFiles);
        }
        
        // Aggregate results
        this.aggregateResults(allResults);
        this.results.endTime = Date.now();
        
        // Print summary
        console.log('\n[TestRunner] Test Summary:');
        console.log(`  Total: ${this.results.total}`);
        console.log(`  Passed: ${this.results.passed}`);
        console.log(`  Failed: ${this.results.failed}`);
        console.log(`  Skipped: ${this.results.skipped}`);
        console.log(`  Duration: ${(this.results.duration / 1000).toFixed(2)}s`);
        
        return this.results;
    }
    
    /**
     * Get results
     */
    getResults() {
        return this.results;
    }
}

module.exports = TestSuiteRunner;

// CLI usage
if (require.main === module) {
    const runner = new TestSuiteRunner({
        parallel: process.argv.includes('--parallel'),
        maxConcurrency: parseInt(process.env.MAX_CONCURRENCY || '4'),
    });
    
    runner.run().then((results) => {
        process.exit(results.failed > 0 ? 1 : 0);
    }).catch((error) => {
        console.error('[TestRunner] Error:', error);
        process.exit(1);
    });
}
