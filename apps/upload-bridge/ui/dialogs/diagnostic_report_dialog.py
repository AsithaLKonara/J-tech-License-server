"""
Diagnostic Report Dialog - Export system diagnostic information for support.

Provides functionality to generate and export diagnostic reports containing:
- App version and build information
- OS and hardware information
- Recent logs
- Configuration summary
- License status
"""

import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
import logging

logger = logging.getLogger(__name__)


class DiagnosticReportGenerator(QThread):
    """Background thread for generating diagnostic reports."""
    
    report_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, app_version: Optional[str] = None):
        super().__init__()
        if app_version is None:
            try:
                from core.project.app_version import get_app_version
                app_version = get_app_version()
            except Exception:
                app_version = "Unknown"
        self.app_version = app_version
    
    def run(self):
        """Generate diagnostic report."""
        try:
            report = self._generate_report()
            self.report_ready.emit(report)
        except Exception as e:
            logger.error(f"Error generating diagnostic report: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'app_info': self._get_app_info(),
            'system_info': self._get_system_info(),
            'hardware_info': self._get_hardware_info(),
            'python_info': self._get_python_info(),
            'logs': self._get_recent_logs(),
            'config_summary': self._get_config_summary(),
            'license_status': self._get_license_status(),
        }
        return report
    
    def _get_app_info(self) -> Dict[str, Any]:
        """Get application information."""
        return {
            'version': self.app_version,
            'platform': platform.platform(),
            'architecture': platform.architecture()[0],
            'executable_path': sys.executable,
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get operating system information."""
        try:
            return {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'node': platform.node(),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information."""
        try:
            import psutil
            return {
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': {str(k): v for k, v in psutil.disk_usage('/')._asdict().items()} if hasattr(psutil.disk_usage('/'), '_asdict') else None,
            }
        except ImportError:
            return {'note': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_python_info(self) -> Dict[str, Any]:
        """Get Python environment information."""
        return {
            'version': sys.version,
            'version_info': list(sys.version_info),
            'executable': sys.executable,
            'path': sys.path[:10],  # First 10 entries to avoid huge lists
        }
    
    def _get_recent_logs(self) -> Dict[str, Any]:
        """Get recent log entries."""
        try:
            log_dir = Path.home() / ".upload_bridge" / "logs"
            if not log_dir.exists():
                return {'note': 'Log directory not found'}
            
            # Get most recent log file
            log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not log_files:
                return {'note': 'No log files found'}
            
            recent_file = log_files[0]
            # Read last 500 lines (or entire file if smaller)
            try:
                with open(recent_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_lines = lines[-500:] if len(lines) > 500 else lines
                    return {
                        'log_file': str(recent_file),
                        'total_lines': len(lines),
                        'recent_lines': len(recent_lines),
                        'content': ''.join(recent_lines),
                    }
            except Exception as e:
                return {'error': f'Error reading log file: {e}'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary (non-sensitive)."""
        try:
            from core.config.config_manager import ConfigManager
            config = ConfigManager.instance()
            # Only include non-sensitive config
            return {
                'config_file': str(config.config_path) if hasattr(config, 'config_path') else None,
                'user_data_dir': str(Path.home() / ".upload_bridge"),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_license_status(self) -> Dict[str, Any]:
        """Get license status (non-sensitive)."""
        try:
            from core.license_manager import LicenseManager
            license_mgr = LicenseManager.instance()
            is_valid, message, license_info = license_mgr.validate_license()
            
            # Get non-sensitive license info
            if license_info:
                license_obj = license_info.get('license', {})
                return {
                    'product_id': license_obj.get('product_id'),
                    'expires_at': license_obj.get('expires_at'),
                    'features': license_obj.get('features', []),
                    'is_valid': is_valid,
                    'source': license_info.get('source', 'unknown'),
                }
            else:
                # Fallback to get_license_data if validate_license didn't return info
                license_data = license_mgr.get_license_data()
                if license_data:
                    license_obj = license_data.get('license', {})
                    return {
                        'product_id': license_obj.get('product_id'),
                        'expires_at': license_obj.get('expires_at'),
                        'features': license_obj.get('features', []),
                        'is_valid': is_valid,
                        'source': license_data.get('source', 'unknown'),
                    }
                else:
                    return {'is_valid': False, 'message': message}
            
        except Exception as e:
            return {'error': str(e)}


class DiagnosticReportDialog(QDialog):
    """Dialog for generating and exporting diagnostic reports."""
    
    def __init__(self, parent=None, app_version: Optional[str] = None):
        super().__init__(parent)
        if app_version is None:
            try:
                from core.project.app_version import get_app_version
                app_version = get_app_version()
            except Exception:
                app_version = "Unknown"
        self.app_version = app_version
        self.report_data: Optional[Dict[str, Any]] = None
        self.setWindowTitle("Export Diagnostic Report")
        self.setMinimumSize(700, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Diagnostic Report")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "This report contains system information, recent logs, and configuration details "
            "to help diagnose issues. Sensitive data (license keys, passwords) is excluded."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Preview text area
        preview_label = QLabel("Report Preview:")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Click 'Generate Report' to create diagnostic report...")
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self._on_generate)
        button_layout.addWidget(self.generate_btn)
        
        self.export_btn = QPushButton("Export to File...")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _on_generate(self):
        """Generate diagnostic report."""
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.preview_text.setPlainText("Generating diagnostic report...")
        
        self.generator = DiagnosticReportGenerator(self.app_version)
        self.generator.report_ready.connect(self._on_report_ready)
        self.generator.error_occurred.connect(self._on_error)
        self.generator.start()
    
    def _on_report_ready(self, report: Dict[str, Any]):
        """Handle report generation completion."""
        self.report_data = report
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Format report as JSON for preview
        report_json = json.dumps(report, indent=2, default=str)
        self.preview_text.setPlainText(report_json)
        
        # Also show summary
        summary = self._format_summary(report)
        QMessageBox.information(
            self,
            "Report Generated",
            f"Diagnostic report generated successfully.\n\n{summary}"
        )
    
    def _on_error(self, error_msg: str):
        """Handle report generation error."""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to generate diagnostic report:\n{error_msg}")
        self.preview_text.setPlainText(f"Error: {error_msg}")
    
    def _format_summary(self, report: Dict[str, Any]) -> str:
        """Format report summary."""
        lines = []
        if 'app_info' in report:
            app_info = report['app_info']
            lines.append(f"Version: {app_info.get('version', 'Unknown')}")
        if 'system_info' in report:
            sys_info = report['system_info']
            lines.append(f"OS: {sys_info.get('system', 'Unknown')} {sys_info.get('release', '')}")
        if 'license_status' in report:
            lic_info = report['license_status']
            lines.append(f"License: {'Valid' if lic_info.get('is_valid') else 'Invalid/None'}")
        return "\n".join(lines)
    
    def _on_export(self):
        """Export report to file."""
        if not self.report_data:
            QMessageBox.warning(self, "No Report", "Please generate a report first.")
            return
        
        # Get file path
        default_path = Path.home() / f"upload_bridge_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Diagnostic Report",
            str(default_path),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Write report to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, indent=2, default=str)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Diagnostic report exported to:\n{file_path}"
            )
        except Exception as e:
            logger.error(f"Error exporting diagnostic report: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export diagnostic report:\n{str(e)}"
            )

