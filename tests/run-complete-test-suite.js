#!/usr/bin/env node
/**
 * Complete Test Suite Runner
 * Orchestrates all test phases: setup, execution, reporting, teardown
 */

const TestSuiteRunner = require('./orchestration/test-suite-runner');
const HtmlReporter = require('./reporting/html-reporter');
const JsonReporter = require('./reporting/json-reporter');
const JUnitReporter = require('./reporting/junit-reporter');
const PerformanceMonitor = require('./monitoring/performance-monitor');
const FlakyTestDetector = require('./monitoring/flaky-test-detector');
const TestEnvironment = require('./helpers/test-environment');
const ServiceSetup = require('./setup/setup-services');
const TestDataSetup = require('./setup/setup-test-data');
const TestTeardown = require('./setup/teardown');
const path = require('path');
const fs = require('fs');

class CompleteTestSuite {
    constructor(options = {}) {
        this.options = {
            parallel: options.parallel !== false,
            maxConcurrency: options.maxConcurrency || 4,
            testTimeout: options.testTimeout || 30000,
            outputDir: options.outputDir || path.join(__dirname, '..', 'test-results'),
            ...options,
        };
        this.performanceMonitor = new PerformanceMonitor();
        this.flakyDetector = new FlakyTestDetector();
    }
    
    /**
     * Setup phase
     */
    async setup() {
        console.log('\n========================================');
        console.log('Phase 1: Setup');
        console.log('========================================\n');
        
        // Setup test environment
        TestEnvironment.setupIsolation();
        
        // Check services
        const servicesReady = await ServiceSetup.waitForServices(30, 1000);
        if (!servicesReady) {
            console.warn('[CompleteTestSuite] Services not ready, continuing anyway...');
        }
        
        // Setup test data
        await TestDataSetup.setup();
        
        console.log('\n[CompleteTestSuite] Setup complete\n');
    }
    
    /**
     * Execution phase
     */
    async execute() {
        console.log('========================================');
        console.log('Phase 2: Test Execution');
        console.log('========================================\n');
        
        const runner = new TestSuiteRunner({
            parallel: this.options.parallel,
            maxConcurrency: this.options.maxConcurrency,
            testTimeout: this.options.testTimeout,
            outputDir: this.options.outputDir,
        });
        
        const results = await runner.run();
        
        // Record performance metrics
        if (results.suites) {
            results.suites.forEach(suite => {
                this.performanceMonitor.recordTest(suite.file, suite.duration || 0);
                this.flakyDetector.recordResult(suite.file, suite.status, TestEnvironment.getTestRunId());
            });
        }
        
        return results;
    }
    
    /**
     * Reporting phase
     */
    async report(results) {
        console.log('\n========================================');
        console.log('Phase 3: Generate Reports');
        console.log('========================================\n');
        
        // Ensure output directory exists
        if (!fs.existsSync(this.options.outputDir)) {
            fs.mkdirSync(this.options.outputDir, { recursive: true });
        }
        
        // Generate HTML report
        const htmlReporter = new HtmlReporter({
            outputDir: this.options.outputDir,
            outputFile: `test-report-${Date.now()}.html`,
        });
        const htmlPath = htmlReporter.generate(results);
        console.log(`[CompleteTestSuite] HTML report: ${htmlPath}`);
        
        // Generate JSON report
        const jsonReporter = new JsonReporter({
            outputDir: this.options.outputDir,
            outputFile: `test-report-${Date.now()}.json`,
        });
        const jsonPath = jsonReporter.generate(results);
        console.log(`[CompleteTestSuite] JSON report: ${jsonPath}`);
        
        // Generate JUnit XML report
        const junitReporter = new JUnitReporter({
            outputDir: this.options.outputDir,
            outputFile: 'junit.xml',
        });
        const junitPath = junitReporter.generate(results);
        console.log(`[CompleteTestSuite] JUnit report: ${junitPath}`);
        
        // Print performance report
        this.performanceMonitor.printReport();
        
        // Print flaky test report
        this.flakyDetector.printReport();
        
        return { htmlPath, jsonPath, junitPath };
    }
    
    /**
     * Teardown phase
     */
    async teardown() {
        console.log('\n========================================');
        console.log('Phase 4: Teardown');
        console.log('========================================\n');
        
        await TestTeardown.teardown();
        
        console.log('\n[CompleteTestSuite] Teardown complete\n');
    }
    
    /**
     * Run complete test suite
     */
    async run() {
        const startTime = Date.now();
        
        try {
            // Setup
            await this.setup();
            
            // Execute
            const results = await this.execute();
            
            // Report
            const reportPaths = await this.report(results);
            
            // Teardown
            await this.teardown();
            
            // Summary
            const duration = Date.now() - startTime;
            console.log('========================================');
            console.log('Test Suite Summary');
            console.log('========================================');
            console.log(`Total: ${results.total}`);
            console.log(`Passed: ${results.passed}`);
            console.log(`Failed: ${results.failed}`);
            console.log(`Skipped: ${results.skipped}`);
            console.log(`Duration: ${(duration / 1000).toFixed(2)}s`);
            console.log(`Reports: ${Object.values(reportPaths).join(', ')}`);
            console.log('========================================\n');
            
            return {
                success: results.failed === 0,
                results,
                reportPaths,
                duration,
            };
        } catch (error) {
            console.error('\n[CompleteTestSuite] Fatal error:', error);
            await this.teardown();
            throw error;
        }
    }
}

// CLI usage
if (require.main === module) {
    const args = process.argv.slice(2);
    const options = {
        parallel: !args.includes('--sequential'),
        maxConcurrency: parseInt(process.env.MAX_CONCURRENCY || '4'),
    };
    
    const suite = new CompleteTestSuite(options);
    
    suite.run().then((summary) => {
        process.exit(summary.success ? 0 : 1);
    }).catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = CompleteTestSuite;
