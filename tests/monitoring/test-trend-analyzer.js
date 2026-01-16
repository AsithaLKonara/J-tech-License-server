/**
 * Test Trend Analyzer
 * Tracks test trends over time
 */

class TestTrendAnalyzer {
    constructor() {
        this.trends = [];
    }
    
    /**
     * Record test run results
     */
    recordRun(results) {
        this.trends.push({
            timestamp: Date.now(),
            total: results.total || 0,
            passed: results.passed || 0,
            failed: results.failed || 0,
            skipped: results.skipped || 0,
            duration: results.duration || 0,
            passRate: results.total > 0 ? (results.passed / results.total) * 100 : 0,
        });
    }
    
    /**
     * Get trend analysis
     */
    getTrends(days = 7) {
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
        const recentTrends = this.trends.filter(t => t.timestamp > cutoff);
        
        if (recentTrends.length === 0) {
            return null;
        }
        
        const averagePassRate = recentTrends.reduce((sum, t) => sum + t.passRate, 0) / recentTrends.length;
        const averageDuration = recentTrends.reduce((sum, t) => sum + t.duration, 0) / recentTrends.length;
        const totalRuns = recentTrends.length;
        
        return {
            period: `${days} days`,
            totalRuns,
            averagePassRate: averagePassRate.toFixed(1) + '%',
            averageDuration: (averageDuration / 1000).toFixed(2) + 's',
            trend: this._calculateTrend(recentTrends),
        };
    }
    
    /**
     * Calculate trend direction
     */
    _calculateTrend(trends) {
        if (trends.length < 2) {
            return 'insufficient data';
        }
        
        const firstHalf = trends.slice(0, Math.floor(trends.length / 2));
        const secondHalf = trends.slice(Math.floor(trends.length / 2));
        
        const firstAvg = firstHalf.reduce((sum, t) => sum + t.passRate, 0) / firstHalf.length;
        const secondAvg = secondHalf.reduce((sum, t) => sum + t.passRate, 0) / secondHalf.length;
        
        if (secondAvg > firstAvg + 5) {
            return 'improving';
        } else if (secondAvg < firstAvg - 5) {
            return 'declining';
        } else {
            return 'stable';
        }
    }
    
    /**
     * Print trend report
     */
    printReport(days = 7) {
        const trends = this.getTrends(days);
        
        if (!trends) {
            console.log('\n[TestTrendAnalyzer] No trend data available');
            return;
        }
        
        console.log('\n[TestTrendAnalyzer] Trend Analysis:');
        console.log(`  Period: ${trends.period}`);
        console.log(`  Total Runs: ${trends.totalRuns}`);
        console.log(`  Average Pass Rate: ${trends.averagePassRate}`);
        console.log(`  Average Duration: ${trends.averageDuration}`);
        console.log(`  Trend: ${trends.trend}`);
    }
}

module.exports = TestTrendAnalyzer;
