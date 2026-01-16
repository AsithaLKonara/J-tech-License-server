/**
 * JSON Test Reporter
 * Generates JSON test reports
 */

const fs = require('fs');
const path = require('path');

class JsonReporter {
    constructor(options = {}) {
        this.options = {
            outputDir: options.outputDir || path.join(__dirname, '..', '..', 'test-results'),
            outputFile: options.outputFile || `test-report-${Date.now()}.json`,
            ...options,
        };
    }
    
    /**
     * Generate JSON report
     */
    generate(results) {
        const json = JSON.stringify(results, null, 2);
        const outputPath = path.join(this.options.outputDir, this.options.outputFile);
        
        // Ensure output directory exists
        if (!fs.existsSync(this.options.outputDir)) {
            fs.mkdirSync(this.options.outputDir, { recursive: true });
        }
        
        fs.writeFileSync(outputPath, json, 'utf8');
        return outputPath;
    }
}

module.exports = JsonReporter;
