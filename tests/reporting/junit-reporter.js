/**
 * JUnit XML Test Reporter
 * Generates JUnit XML format for CI/CD integration
 */

const fs = require('fs');
const path = require('path');

class JUnitReporter {
    constructor(options = {}) {
        this.options = {
            outputDir: options.outputDir || path.join(__dirname, '..', '..', 'test-results'),
            outputFile: options.outputFile || 'junit.xml',
            ...options,
        };
    }
    
    /**
     * Generate JUnit XML report
     */
    generate(results) {
        const xml = this._buildXml(results);
        const outputPath = path.join(this.options.outputDir, this.options.outputFile);
        
        // Ensure output directory exists
        if (!fs.existsSync(this.options.outputDir)) {
            fs.mkdirSync(this.options.outputDir, { recursive: true });
        }
        
        fs.writeFileSync(outputPath, xml, 'utf8');
        return outputPath;
    }
    
    /**
     * Build JUnit XML
     */
    _buildXml(results) {
        const duration = (results.endTime - results.startTime) / 1000;
        const timestamp = new Date(results.startTime).toISOString();
        
        let testCases = '';
        
        if (results.suites) {
            testCases = results.suites.map(suite => {
                const testDuration = (suite.duration || 0) / 1000;
                const className = suite.file.replace(/\\/g, '/').replace(/\.(js|ts)$/, '');
                
                if (suite.status === 'passed') {
                    return `    <testcase classname="${this._escapeXml(className)}" name="${this._escapeXml(suite.file)}" time="${testDuration.toFixed(3)}" />`;
                } else {
                    const failureMessage = suite.error || suite.stderr || 'Test failed';
                    return `    <testcase classname="${this._escapeXml(className)}" name="${this._escapeXml(suite.file)}" time="${testDuration.toFixed(3)}">
      <failure message="${this._escapeXml(failureMessage)}">${this._escapeXml(suite.stdout || '')}</failure>
    </testcase>`;
                }
            }).join('\n');
        }
        
        return `<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="E2E Tests" tests="${results.total}" failures="${results.failed}" skipped="${results.skipped}" errors="0" time="${duration.toFixed(3)}" timestamp="${timestamp}">
${testCases}
  </testsuite>
</testsuites>`;
    }
    
    /**
     * Escape XML
     */
    _escapeXml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&apos;');
    }
}

module.exports = JUnitReporter;
