"""
Report Generator - Creates HTML and JSON test reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from tests.gui.test_types import TestResult, TestStatus


class ReportGenerator:
    """Generates test reports in HTML and JSON formats."""
    
    def export_html(self, test_results: Dict[str, List[TestResult]], file_path: str):
        """Export test results as HTML report."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>Design Tools Tab - Test Report</title>")
        html.append("<style>")
        html.append("""
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background-color: #2196F3;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .summary {
                background-color: white;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .category {
                background-color: white;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .category-header {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
            }
            th {
                background-color: #f0f0f0;
                font-weight: bold;
            }
            .status-pass {
                color: #4CAF50;
                font-weight: bold;
            }
            .status-fail {
                color: #f44336;
                font-weight: bold;
            }
            .status-pending {
                color: #9E9E9E;
            }
            .error {
                color: #f44336;
                font-size: 12px;
                font-style: italic;
            }
        """)
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        
        # Header
        html.append("<div class='header'>")
        html.append("<h1>Design Tools Tab - Test Report</h1>")
        html.append(f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html.append("</div>")
        
        # Summary
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for category, results in test_results.items():
            total_tests += len(results)
            total_passed += sum(1 for r in results if r.status == TestStatus.PASS)
            total_failed += sum(1 for r in results if r.status == TestStatus.FAIL)
        
        html.append("<div class='summary'>")
        html.append("<h2>Summary</h2>")
        html.append(f"<p><strong>Total Tests:</strong> {total_tests}</p>")
        html.append(f"<p><strong>Passed:</strong> <span class='status-pass'>{total_passed}</span></p>")
        html.append(f"<p><strong>Failed:</strong> <span class='status-fail'>{total_failed}</span></p>")
        html.append(f"<p><strong>Pass Rate:</strong> {total_passed*100//total_tests if total_tests > 0 else 0}%</p>")
        html.append("</div>")
        
        # Test results by category
        for category, results in test_results.items():
            passed = sum(1 for r in results if r.status == TestStatus.PASS)
            failed = sum(1 for r in results if r.status == TestStatus.FAIL)
            
            html.append("<div class='category'>")
            html.append(f"<div class='category-header'>{category} ({passed}/{len(results)} passed)</div>")
            html.append("<table>")
            html.append("<tr><th>Feature</th><th>Status</th><th>Message</th></tr>")
            
            for result in results:
                status_class = "status-pass" if result.status == TestStatus.PASS else "status-fail" if result.status == TestStatus.FAIL else "status-pending"
                status_text = result.status.value
                
                html.append("<tr>")
                html.append(f"<td>{result.feature}</td>")
                html.append(f"<td class='{status_class}'>{status_text}</td>")
                html.append(f"<td>{result.message}")
                if result.error:
                    html.append(f"<br><span class='error'>Error: {result.error}</span>")
                html.append("</td>")
                html.append("</tr>")
            
            html.append("</table>")
            html.append("</div>")
        
        html.append("</body>")
        html.append("</html>")
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
    
    def export_json(self, test_results: Dict[str, List[TestResult]], file_path: str):
        """Export test results as JSON report."""
        # Convert test results to dictionary
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "results": {}
        }
        
        # Calculate summary
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for category, results in test_results.items():
            total_tests += len(results)
            total_passed += sum(1 for r in results if r.status == TestStatus.PASS)
            total_failed += sum(1 for r in results if r.status == TestStatus.FAIL)
        
        report["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "pass_rate": total_passed * 100 // total_tests if total_tests > 0 else 0
        }
        
        # Convert results
        for category, results in test_results.items():
            report["results"][category] = []
            for result in results:
                report["results"][category].append({
                    "feature": result.feature,
                    "status": result.status.value,
                    "message": result.message,
                    "error": result.error,
                    "duration": result.duration
                })
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

