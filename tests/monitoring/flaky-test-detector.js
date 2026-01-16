/**
 * Flaky Test Detector
 * Identifies flaky tests by tracking pass/fail patterns
 */

class FlakyTestDetector {
    constructor() {
        this.testHistory = new Map();
    }
    
    /**
     * Record test result
     */
    recordResult(testName, status, runId) {
        if (!this.testHistory.has(testName)) {
            this.testHistory.set(testName, []);
        }
        
        this.testHistory.get(testName).push({
            status,
            runId,
            timestamp: Date.now(),
        });
    }
    
    /**
     * Detect flaky tests
     */
    detectFlakyTests() {
        const flakyTests = [];
        
        for (const [testName, history] of this.testHistory.entries()) {
            if (history.length < 3) {
                continue; // Need at least 3 runs to detect flakiness
            }
            
            const recentHistory = history.slice(-10); // Last 10 runs
            const passCount = recentHistory.filter(h => h.status === 'passed').length;
            const failCount = recentHistory.filter(h => h.status === 'failed').length;
            
            // Test is flaky if it has both passes and failures
            if (passCount > 0 && failCount > 0) {
                const flakinessRate = Math.min(passCount, failCount) / recentHistory.length;
                
                if (flakinessRate > 0.2) { // More than 20% inconsistency
                    flakyTests.push({
                        name: testName,
                        passCount,
                        failCount,
                        flakinessRate: (flakinessRate * 100).toFixed(1) + '%',
                        recentHistory,
                    });
                }
            }
        }
        
        return flakyTests.sort((a, b) => b.flakinessRate - a.flakinessRate);
    }
    
    /**
     * Print flaky test report
     */
    printReport() {
        const flakyTests = this.detectFlakyTests();
        
        if (flakyTests.length === 0) {
            console.log('\n[FlakyTestDetector] No flaky tests detected');
            return;
        }
        
        console.log('\n[FlakyTestDetector] Flaky Tests Detected:');
        flakyTests.forEach((test, index) => {
            console.log(`  ${index + 1}. ${test.name}`);
            console.log(`     Pass: ${test.passCount}, Fail: ${test.failCount}, Flakiness: ${test.flakinessRate}`);
        });
    }
}

module.exports = FlakyTestDetector;
