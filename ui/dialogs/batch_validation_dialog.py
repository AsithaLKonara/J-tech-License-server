"""
Batch Validation Dialog - UI for batch pattern validation
"""

import logging
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal

from core.batch_validator import BatchValidator, ValidationResult

logger = logging.getLogger(__name__)


class ValidationWorker(QThread):
    """Worker thread for batch validation"""
    progress = Signal(int, int)  # current, total
    finished = Signal(list)  # results
    
    def __init__(self, file_paths: List[str]):
        super().__init__()
        self.file_paths = file_paths
        self.validator = BatchValidator()
    
    def run(self):
        """Run validation in background thread"""
        def progress_callback(current, total):
            self.progress.emit(current, total)
        
        results = self.validator.validate_patterns(self.file_paths, progress_callback)
        self.finished.emit(results)


class BatchValidationDialog(QDialog):
    """Dialog for batch pattern validation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Pattern Validation")
        self.setMinimumSize(800, 600)
        
        self.validator = BatchValidator()
        self.results: List[ValidationResult] = []
        self.worker: Optional[ValidationWorker] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        
        # File selection
        file_group = QGroupBox("Pattern Files")
        file_layout = QVBoxLayout()
        
        file_button_layout = QHBoxLayout()
        self.select_files_button = QPushButton("Select Pattern Files...")
        self.select_files_button.clicked.connect(self.select_files)
        file_button_layout.addWidget(self.select_files_button)
        
        self.file_count_label = QLabel("No files selected")
        file_button_layout.addWidget(self.file_count_label)
        file_button_layout.addStretch()
        
        file_layout.addLayout(file_button_layout)
        
        self.file_list = QTextEdit()
        self.file_list.setReadOnly(True)
        self.file_list.setMaximumHeight(100)
        file_layout.addWidget(self.file_list)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Results table
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "File", "Status", "Errors", "Warnings", "Dimensions"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group, stretch=1)
        
        # Summary
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.validate_button = QPushButton("Validate")
        self.validate_button.clicked.connect(self.start_validation)
        self.validate_button.setEnabled(False)
        button_layout.addWidget(self.validate_button)
        
        self.export_csv_button = QPushButton("Export CSV Report")
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_csv_button.setEnabled(False)
        button_layout.addWidget(self.export_csv_button)
        
        self.export_json_button = QPushButton("Export JSON Report")
        self.export_json_button.clicked.connect(self.export_json)
        self.export_json_button.setEnabled(False)
        button_layout.addWidget(self.export_json_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def select_files(self):
        """Select pattern files for validation"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Pattern Files",
            "",
            "Pattern Files (*.bin *.hex *.dat *.leds *.json *.ledproj);;All Files (*.*)"
        )
        
        if files:
            self.file_paths = files
            self.file_count_label.setText(f"{len(files)} file(s) selected")
            self.file_list.setPlainText("\n".join(files))
            self.validate_button.setEnabled(True)
            self.results_table.setRowCount(0)
            self.summary_label.setText("")
    
    def start_validation(self):
        """Start batch validation"""
        if not hasattr(self, 'file_paths') or not self.file_paths:
            QMessageBox.warning(self, "No Files", "Please select files to validate.")
            return
        
        # Disable button during validation
        self.validate_button.setEnabled(False)
        self.progress_bar.setMaximum(len(self.file_paths))
        self.progress_bar.setValue(0)
        self.status_label.setText("Validating...")
        self.results_table.setRowCount(0)
        
        # Create and start worker thread
        self.worker = ValidationWorker(self.file_paths)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_validation_finished)
        self.worker.start()
    
    def on_progress(self, current: int, total: int):
        """Update progress bar"""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Validating {current}/{total}...")
    
    def on_validation_finished(self, results: List[ValidationResult]):
        """Handle validation completion"""
        self.results = results
        self.validate_button.setEnabled(True)
        self.status_label.setText("Validation complete")
        self.progress_bar.setValue(self.progress_bar.maximum())
        
        # Populate results table
        self.populate_results_table()
        
        # Show summary
        summary = self.validator.get_summary()
        self.summary_label.setText(
            f"Summary: {summary['valid']}/{summary['total']} valid, "
            f"{summary['invalid']} invalid, "
            f"{summary['total_errors']} errors, "
            f"{summary['total_warnings']} warnings"
        )
        
        # Enable export buttons
        self.export_csv_button.setEnabled(True)
        self.export_json_button.setEnabled(True)
    
    def populate_results_table(self):
        """Populate results table with validation results"""
        self.results_table.setRowCount(len(self.results))
        
        for row, result in enumerate(self.results):
            # File path
            file_item = QTableWidgetItem(Path(result.file_path).name)
            self.results_table.setItem(row, 0, file_item)
            
            # Status
            status_text = "✓ Valid" if result.valid else "✗ Invalid"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.GlobalColor.green if result.valid else Qt.GlobalColor.red)
            self.results_table.setItem(row, 1, status_item)
            
            # Errors
            errors_text = str(len(result.errors))
            if result.errors:
                errors_text += f": {result.errors[0][:50]}"
            errors_item = QTableWidgetItem(errors_text)
            self.results_table.setItem(row, 2, errors_item)
            
            # Warnings
            warnings_text = str(len(result.warnings))
            if result.warnings:
                warnings_text += f": {result.warnings[0][:50]}"
            warnings_item = QTableWidgetItem(warnings_text)
            self.results_table.setItem(row, 3, warnings_item)
            
            # Dimensions
            if result.metadata:
                dims_text = f"{result.metadata.get('width', '?')}×{result.metadata.get('height', '?')}"
            else:
                dims_text = "N/A"
            dims_item = QTableWidgetItem(dims_text)
            self.results_table.setItem(row, 4, dims_item)
        
        # Resize columns
        self.results_table.resizeColumnsToContents()
    
    def export_csv(self):
        """Export validation report as CSV"""
        if not self.results:
            QMessageBox.warning(self, "No Results", "No validation results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Report",
            "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if file_path:
            self.validator.results = self.results
            self.validator.generate_report_csv(file_path)
            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{file_path}")
    
    def export_json(self):
        """Export validation report as JSON"""
        if not self.results:
            QMessageBox.warning(self, "No Results", "No validation results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON Report",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if file_path:
            self.validator.results = self.results
            self.validator.generate_report_json(file_path)
            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{file_path}")

