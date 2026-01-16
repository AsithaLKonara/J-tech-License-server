/**
 * Performance Monitor
 * Tracks test performance and identifies slow tests
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            tests: [],
            slowTests: [],
            averageDuration: 0,
            totalDuration: 0,
        };
    }
    
    /**
     * Record test performance
     */
    recordTest(testName, duration) {
        this.metrics.tests.push({
            name: testName,
            duration,
            timestamp: Date.now(),
        });
        
        this.metrics.totalDuration += duration;
        this.metrics.averageDuration = this.metrics.totalDuration / this.metrics.tests.length;
        
        // Track slow tests (over 5 seconds)
        if (duration > 5000) {
            this.metrics.slowTests.push({
                name: testName,
                duration,
            });
        }
    }
    
    /**
     * Get performance report
     */
    getReport() {
        return {
            totalTests: this.metrics.tests.length,
            totalDuration: this.metrics.totalDuration,
            averageDuration: this.metrics.averageDuration,
            slowTests: this.metrics.slowTests.sort((a, b) => b.duration - a.duration),
            slowestTest: this.metrics.tests.reduce((max, test) => 
                test.duration > max.duration ? test : max, 
                { duration: 0 }
            ),
        };
    }
    
    /**
     * Print performance report
     */
    printReport() {
        const report = this.getReport();
        
        console.log('\n[PerformanceMonitor] Performance Report:');
        console.log(`  Total Tests: ${report.totalTests}`);
        console.log(`  Total Duration: ${(report.totalDuration / 1000).toFixed(2)}s`);
        console.log(`  Average Duration: ${(report.averageDuration / 1000).toFixed(2)}s`);
        console.log(`  Slow Tests (>5s): ${report.slowTests.length}`);
        
        if (report.slowTests.length > 0) {
            console.log('\n  Slowest Tests:');
            report.slowTests.slice(0, 10).forEach((test, index) => {
                console.log(`    ${index + 1}. ${test.name}: ${(test.duration / 1000).toFixed(2)}s`);
            });
        }
    }
}

module.exports = PerformanceMonitor;
