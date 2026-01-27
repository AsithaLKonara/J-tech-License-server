"""
Setup Wizard Dialog - Guided setup for dependencies and shortcuts.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QCheckBox, QStackedWidget, QWidget,
    QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from core.dependencies import DependencyManager, create_desktop_shortcut, create_start_menu_shortcut
from core.runtime import get_resource_path
from pathlib import Path

class SetupWizardDialog(QDialog):
    """Wizard to guide user through first-time setup."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Bridge - Professional Setup")
        self.setFixedSize(600, 450)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.dep_manager = DependencyManager()
        self._setup_ui()
        self._show_welcome()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #1a1a1a; border-bottom: 2px solid #4C8BF5;")
        header_layout = QHBoxLayout(header)
        
        title_label = QLabel("Welcome to Upload Bridge")
        title_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        layout.addWidget(header)
        
        # Stacked pages
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Page 0: Welcome / Check
        self.page_welcome = self._create_welcome_page()
        self.stack.addWidget(self.page_welcome)
        
        # Page 1: Install Process
        self.page_install = self._create_install_page()
        self.stack.addWidget(self.page_install)
        
        # Page 2: Finish
        self.page_finish = self._create_finish_page()
        self.stack.addWidget(self.page_finish)
        
        # Footer
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("background-color: #242424; border-top: 1px solid #333;")
        footer_layout = QHBoxLayout(footer)
        
        self.btn_back = QPushButton("Back")
        self.btn_back.setFixedWidth(100)
        self.btn_back.setEnabled(False)
        self.btn_back.clicked.connect(self._go_back)
        footer_layout.addWidget(self.btn_back)
        
        footer_layout.addStretch()
        
        self.btn_next = QPushButton("Next")
        self.btn_next.setFixedWidth(100)
        self.btn_next.setStyleSheet("background-color: #4C8BF5; color: white;")
        self.btn_next.clicked.connect(self._go_next)
        footer_layout.addWidget(self.btn_next)
        
        layout.addWidget(footer)

    def _create_welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        
        label = QLabel(
            "Upload Bridge requires some system components for full functionality, \n"
            "including AI pattern generation and optimized rendering.\n\n"
            "We will now check your system and help you install missing components."
        )
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 14px; line-height: 1.5;")
        layout.addWidget(label)
        
        self.dep_list_label = QLabel("Checking dependencies...")
        self.dep_list_label.setStyleSheet("color: #aaa; margin-top: 20px;")
        layout.addWidget(self.dep_list_label)
        
        layout.addStretch()
        
        self.shortcut_group = QFrame()
        shortcut_layout = QVBoxLayout(self.shortcut_group)
        self.check_desktop = QCheckBox("Create Desktop Shortcut")
        self.check_desktop.setChecked(True)
        self.check_start = QCheckBox("Create Start Menu Shortcut")
        self.check_start.setChecked(True)
        shortcut_layout.addWidget(self.check_desktop)
        shortcut_layout.addWidget(self.check_start)
        layout.addWidget(self.shortcut_group)
        
        return page

    def _create_install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 20, 40, 20)
        
        self.install_label = QLabel("Ready to install...")
        layout.addWidget(self.install_label)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet("background-color: #000; color: #0f0; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.log_edit)
        
        return page

    def _create_finish_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        label = QLabel("Setup Complete!")
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        sub = QLabel("Upload Bridge is now ready for use. Enjoy designing your LED patterns!")
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)
        
        layout.addStretch()
        return page

    def _show_welcome(self):
        deps = self.dep_manager.check_all()
        text = "System Check Results:\n"
        all_ok = True
        for dep in deps:
            status = "✓ Installed" if dep.installed else "✗ Missing"
            text += f"• {dep.name}: {status}\n"
            if not dep.installed and dep.critical:
                all_ok = False
        
        self.dep_list_label.setText(text)
        if not all_ok:
             self.dep_list_label.setText(text + "\n⚠️ Note: Critical dependencies like Node.js must be installed manually.")

    def _go_next(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self.stack.setCurrentIndex(1)
            self.btn_back.setEnabled(True)
            self.btn_next.setEnabled(False)
            self._start_installation()
        elif idx == 1:
            self.stack.setCurrentIndex(2)
            self.btn_next.setText("Finish")
        elif idx == 2:
            self.accept()

    def _go_back(self):
        idx = self.stack.currentIndex()
        if idx == 1:
            self.stack.setCurrentIndex(0)
            self.btn_back.setEnabled(False)
            self.btn_next.setEnabled(True)

    def _start_installation(self):
        self.dep_manager.progress_updated.connect(self._on_progress)
        self.dep_manager.log_received.connect(self._on_log)
        self.dep_manager.finished.connect(self._on_finished)
        self.dep_manager.install_missing()

    def _on_progress(self, val, msg):
        self.progress.setValue(val)
        self.install_label.setText(msg)

    def _on_log(self, text):
        self.log_edit.append(text.strip())

    def _on_finished(self, success, msg):
        if self.check_desktop.isChecked():
            create_desktop_shortcut()
        if self.check_start.isChecked():
            create_start_menu_shortcut()
            
        self.btn_next.setEnabled(True)
        if success:
            self.install_label.setText("Installation Successful!")
            self._go_next()
        else:
            self.install_label.setText(f"Installation failed: {msg}")
            QMessageBox.critical(self, "Setup Error", f"An error occurred during setup:\n\n{msg}")
            self.btn_back.setEnabled(True)
