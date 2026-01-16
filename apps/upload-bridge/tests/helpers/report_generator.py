"""
Report Generator for Comprehensive Test Suite

Generates HTML and JSON reports from test results.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class TestResult:
    """Individual test result."""
    name: str
    suite: str
    passed: bool
    skipped: bool = False
    error_message: Optional[str] = None
    execution_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuiteResult:
    """Test suite result summary."""
    name: str
    total: int
    passed: int
    failed: int
    skipped: int
    execution_time: float
    tests: List[TestResult] = field(default_factory=list)


class ReportGenerator:
    """Generates comprehensive test reports."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize report generator."""
        if output_dir is None:
            # Default to tests/reports
            base_dir = Path(__file__).parent.parent
            output_dir = base_dir / "reports"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.suite_results: List[TestSuiteResult] = []
    
    def add_suite_result(self, suite_result: TestSuiteResult):
        """Add a test suite result."""
        self.suite_results.append(suite_result)
    
    def generate_all(self) -> Dict[str, Path]:
        """Generate both HTML and JSON reports."""
        return {
            'html': self.generate_html(),
            'json': self.generate_json(),
        }
    
    def generate_json(self) -> Path:
        """Generate JSON report."""
        report_data = {
            'timestamp': self.timestamp,
            'total_suites': len(self.suite_results),
            'suites': [asdict(suite) for suite in self.suite_results],
            'summary': self._calculate_summary(),
        }
        
        json_file = self.output_dir / f"comprehensive_test_report_{self.timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return json_file
    
    def generate_html(self) -> Path:
        """Generate HTML report."""
        html_file = self.output_dir / f"comprehensive_test_report_{self.timestamp}.html"
        
        summary = self._calculate_summary()
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Test Report - {self.timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card.total {{ background: #e3f2fd; }}
        .summary-card.passed {{ background: #e8f5e9; }}
        .summary-card.failed {{ background: #ffebee; }}
        .summary-card.skipped {{ background: #fff3e0; }}
        .summary-card h2 {{
            margin: 0;
            font-size: 2.5em;
            color: #333;
        }}
        .summary-card p {{
            margin: 5px 0 0 0;
            color: #666;
            font-weight: 500;
        }}
        .suite {{
            margin: 30px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }}
        .suite-header {{
            background: #f5f5f5;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #ddd;
        }}
        .suite-header h2 {{
            margin: 0;
            color: #333;
        }}
        .suite-stats {{
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            color: #666;
        }}
        .test-list {{
            padding: 0;
            margin: 0;
        }}
        .test-item {{
            padding: 12px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-item:last-child {{
            border-bottom: none;
        }}
        .test-item.passed {{
            background: #f1f8f4;
        }}
        .test-item.failed {{
            background: #fff5f5;
        }}
        .test-item.skipped {{
            background: #fffbf0;
        }}
        .test-name {{
            flex: 1;
            font-weight: 500;
        }}
        .test-status {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .test-status.passed {{
            background: #4CAF50;
            color: white;
        }}
        .test-status.failed {{
            background: #f44336;
            color: white;
        }}
        .test-status.skipped {{
            background: #ff9800;
            color: white;
        }}
        .test-time {{
            margin-left: 15px;
            color: #666;
            font-size: 0.9em;
        }}
        .error-message {{
            margin-top: 10px;
            padding: 10px;
            background: #fff5f5;
            border-left: 4px solid #f44336;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .timestamp {{
            text-align: center;
            color: #999;
            margin-top: 30px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Comprehensive Test Report</h1>
        
        <div class="summary">
            <div class="summary-card total">
                <h2>{summary['total_tests']}</h2>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h2>{summary['total_passed']}</h2>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h2>{summary['total_failed']}</h2>
                <p>Failed</p>
            </div>
            <div class="summary-card skipped">
                <h2>{summary['total_skipped']}</h2>
                <p>Skipped</p>
            </div>
        </div>
        
        <div class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        
        {self._generate_suite_html()}
    </div>
</body>
</html>
"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total_tests = sum(suite.total for suite in self.suite_results)
        total_passed = sum(suite.passed for suite in self.suite_results)
        total_failed = sum(suite.failed for suite in self.suite_results)
        total_skipped = sum(suite.skipped for suite in self.suite_results)
        total_time = sum(suite.execution_time for suite in self.suite_results)
        
        return {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'total_execution_time': total_time,
            'pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
        }
    
    def _generate_suite_html(self) -> str:
        """Generate HTML for all test suites."""
        html_parts = []
        
        for suite in self.suite_results:
            suite_html = f"""
        <div class="suite">
            <div class="suite-header">
                <h2>{suite.name}</h2>
                <div class="suite-stats">
                    <span>Total: {suite.total}</span>
                    <span style="color: #4CAF50;">Passed: {suite.passed}</span>
                    <span style="color: #f44336;">Failed: {suite.failed}</span>
                    <span style="color: #ff9800;">Skipped: {suite.skipped}</span>
                    <span>Time: {suite.execution_time:.2f}s</span>
                </div>
            </div>
            <div class="test-list">
"""
            
            for test in suite.tests:
                status_class = 'passed' if test.passed else ('skipped' if test.skipped else 'failed')
                status_text = 'PASS' if test.passed else ('SKIP' if test.skipped else 'FAIL')
                
                test_html = f"""
                <div class="test-item {status_class}">
                    <div class="test-name">{test.name}</div>
                    <div>
                        <span class="test-status {status_class}">{status_text}</span>
                        <span class="test-time">{test.execution_time:.3f}s</span>
                    </div>
                </div>
"""
                
                if test.error_message:
                    test_html += f"""
                <div class="error-message">{test.error_message}</div>
"""
                
                suite_html += test_html
            
            suite_html += """
            </div>
        </div>
"""
            html_parts.append(suite_html)
        
        return '\n'.join(html_parts)

