/**
 * HTML Test Reporter
 * Generates HTML test reports with screenshots and performance metrics
 */

const fs = require('fs');
const path = require('path');

class HtmlReporter {
    constructor(options = {}) {
        this.options = {
            outputDir: options.outputDir || path.join(__dirname, '..', '..', 'test-results'),
            outputFile: options.outputFile || `test-report-${Date.now()}.html`,
            ...options,
        };
    }
    
    /**
     * Generate HTML report
     */
    generate(results) {
        const html = this._buildHtml(results);
        const outputPath = path.join(this.options.outputDir, this.options.outputFile);
        
        // Ensure output directory exists
        if (!fs.existsSync(this.options.outputDir)) {
            fs.mkdirSync(this.options.outputDir, { recursive: true });
        }
        
        fs.writeFileSync(outputPath, html, 'utf8');
        return outputPath;
    }
    
    /**
     * Build HTML content
     */
    _buildHtml(results) {
        const duration = results.endTime - results.startTime;
        const passRate = results.total > 0 ? ((results.passed / results.total) * 100).toFixed(1) : 0;
        
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - ${new Date(results.startTime).toLocaleString()}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; margin-bottom: 10px; }
        .meta { color: #7f8c8d; margin-bottom: 30px; }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }
        .summary-card.total { background: #ecf0f1; }
        .summary-card.passed { background: #d4edda; color: #155724; }
        .summary-card.failed { background: #f8d7da; color: #721c24; }
        .summary-card.skipped { background: #fff3cd; color: #856404; }
        .summary-card.duration { background: #d1ecf1; color: #0c5460; }
        .summary-card h3 { font-size: 2em; margin-bottom: 5px; }
        .summary-card p { font-size: 0.9em; opacity: 0.8; }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .test-suites { margin-top: 30px; }
        .test-suite {
            margin-bottom: 20px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            overflow: hidden;
        }
        .test-suite-header {
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .test-suite-header h3 { margin: 0; }
        .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .status-badge.passed { background: #d4edda; color: #155724; }
        .status-badge.failed { background: #f8d7da; color: #721c24; }
        .status-badge.timeout { background: #fff3cd; color: #856404; }
        .test-details {
            padding: 15px;
        }
        .test-output {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            max-height: 200px;
            overflow-y: auto;
        }
        .error-output {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        .duration { color: #6c757d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Execution Report</h1>
        <div class="meta">
            <p>Generated: ${new Date(results.startTime).toLocaleString()}</p>
            <p>Duration: ${(duration / 1000).toFixed(2)} seconds</p>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>${results.total}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>${results.passed}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h3>${results.failed}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card skipped">
                <h3>${results.skipped}</h3>
                <p>Skipped</p>
            </div>
            <div class="summary-card duration">
                <h3>${passRate}%</h3>
                <p>Pass Rate</p>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${passRate}%">${passRate}%</div>
        </div>
        
        <div class="test-suites">
            <h2>Test Suites</h2>
            ${this._renderTestSuites(results.suites)}
        </div>
    </div>
</body>
</html>`;
    }
    
    /**
     * Render test suites
     */
    _renderTestSuites(suites) {
        if (!suites || suites.length === 0) {
            return '<p>No test results available.</p>';
        }
        
        return suites.map(suite => `
            <div class="test-suite">
                <div class="test-suite-header">
                    <h3>${this._escapeHtml(suite.file)}</h3>
                    <div>
                        <span class="status-badge ${suite.status}">${suite.status.toUpperCase()}</span>
                        <span class="duration">${(suite.duration / 1000).toFixed(2)}s</span>
                    </div>
                </div>
                <div class="test-details">
                    ${suite.stdout ? `<div class="test-output">${this._escapeHtml(suite.stdout)}</div>` : ''}
                    ${suite.stderr ? `<div class="error-output">${this._escapeHtml(suite.stderr)}</div>` : ''}
                    ${suite.error ? `<div class="error-output">${this._escapeHtml(suite.error)}</div>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    /**
     * Escape HTML
     */
    _escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

module.exports = HtmlReporter;
