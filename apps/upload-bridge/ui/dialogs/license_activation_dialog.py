"""
License Activation Dialog - Account-Based License Activation
Allows users to activate their license by logging in with email/password or magic link.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from core.auth_manager import AuthManager
from core.license_manager import LicenseManager
from ui.dialogs.login_dialog import AuthWorker


class LicenseActivationDialog(QDialog):
    """Dialog for activating license via account login"""
    
    # Signal emitted when activation is successful
    activation_successful = Signal()
    
    def __init__(self, parent=None, auth_manager: Optional[AuthManager] = None, 
                 license_manager: Optional[LicenseManager] = None, config: dict = None):
        super().__init__(parent)
        self.config = config or {}
        self.server_url = self.config.get("auth_server_url") or os.environ.get("LICENSE_SERVER_URL") or os.environ.get("AUTH_SERVER_URL") or "https://j-tech-license-server.up.railway.app"
        self.auth_manager = auth_manager or AuthManager(server_url=self.server_url)
        self.license_manager = license_manager or LicenseManager(server_url=self.server_url)
        self.auth_worker = None
        
        self.setWindowTitle("Activate License - Upload Bridge")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Activate Your License")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Info label
        info = QLabel(
            "Sign in with your account to activate Upload Bridge.\n"
            "You can use email/password or magic link."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Tabs for different login methods
        tabs = QTabWidget()
        
        # Email/Password tab
        email_tab = self._build_email_tab()
        tabs.addTab(email_tab, "Email/Password")
        
        # Magic Link tab
        magic_link_tab = self._build_magic_link_tab()
        tabs.addTab(magic_link_tab, "Magic Link")
        
        layout.addWidget(tabs)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        # Buttons
        buttons = QHBoxLayout()
        self.activate_btn = QPushButton("Activate")
        self.activate_btn.setDefault(True)
        self.close_btn = QPushButton("Close")
        buttons.addWidget(self.activate_btn)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)
        
        self.activate_btn.clicked.connect(self.on_activate)
        self.close_btn.clicked.connect(self.reject)  # Close without activation should reject
        
        # Initially disable activate button until login method is selected
        self.activate_btn.setEnabled(False)
    
    def _build_email_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your@email.com")
        self.email_input.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.email_input)
        
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.password_input)
        
        layout.addStretch()
        
        return widget
    
    def _build_magic_link_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Email:"))
        self.magic_email_input = QLineEdit()
        self.magic_email_input.setPlaceholderText("your@email.com")
        self.magic_email_input.textChanged.connect(self._on_magic_input_changed)
        layout.addWidget(self.magic_email_input)
        
        self.send_link_btn = QPushButton("Send Magic Link")
        self.send_link_btn.clicked.connect(self.on_send_magic_link)
        layout.addWidget(self.send_link_btn)
        
        self.magic_status_label = QLabel("")
        self.magic_status_label.setWordWrap(True)
        self.magic_status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.magic_status_label)
        
        info = QLabel(
            "We'll send you a login link via email.\n"
            "Click the link to complete authentication."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        return widget
    
    def _on_input_changed(self):
        """Enable activate button if email and password are filled"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        self.activate_btn.setEnabled(bool(email and password))
    
    def _on_magic_input_changed(self):
        """Enable send link button if email is filled"""
        email = self.magic_email_input.text().strip()
        self.send_link_btn.setEnabled(bool(email))
    
    def on_activate(self):
        """Handle email/password activation"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Activation", "Please enter both email and password.")
            return
        
        device_name = f"{sys.platform} Device"
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("Authenticating...")
        self.activate_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        
        self.auth_worker = AuthWorker(
            self.auth_manager,
            email=email,
            password=password,
            device_name=device_name
        )
        self.auth_worker.progress.connect(self.status_label.setText)
        self.auth_worker.finished.connect(self.on_auth_complete)
        self.auth_worker.start()
    
    def on_send_magic_link(self):
        """Handle magic link request"""
        email = self.magic_email_input.text().strip()
        
        if not email:
            QMessageBox.warning(self, "Magic Link", "Please enter your email address.")
            return
        
        # Request magic link from server
        import requests
        try:
            self.send_link_btn.setEnabled(False)
            self.magic_status_label.setText("Sending magic link...")
            
            response = requests.post(
                f"{self.server_url}/magic-link",
                json={'email': email},
                timeout=10
            )
            
            if response.status_code == 200:
                self.magic_status_label.setText(f"Magic link sent to {email}. Please check your email and click the link.")
                QMessageBox.information(
                    self,
                    "Magic Link Sent",
                    f"Magic link sent to {email}.\n\n"
                    "Please check your email and click the link to complete activation."
                )
            else:
                error_msg = response.text if response.text else f"Server returned status {response.status_code}"
                self.magic_status_label.setText(f"Failed to send magic link: {error_msg}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to send magic link:\n{error_msg}"
                )
        except Exception as e:
            self.magic_status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to send magic link:\n{str(e)}"
            )
        finally:
            self.send_link_btn.setEnabled(True)
    
    def authenticate_with_magic_link_token(self, magic_link_token: str):
        """Authenticate with magic link token (called after user clicks email link)"""
        device_name = f"{sys.platform} Device"
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("Authenticating...")
        self.activate_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        
        self.auth_worker = AuthWorker(
            self.auth_manager,
            magic_link_token=magic_link_token,
            device_name=device_name
        )
        self.auth_worker.progress.connect(self.status_label.setText)
        self.auth_worker.finished.connect(self.on_auth_complete)
        self.auth_worker.start()
    
    def on_auth_complete(self, success: bool, message: str):
        """Handle authentication completion and validate license"""
        if not success:
            self.progress_bar.setVisible(False)
            self.activate_btn.setEnabled(True)
            self.close_btn.setEnabled(True)
            self.status_label.setText(f"Authentication failed: {message}")
            QMessageBox.critical(self, "Activation Failed", f"Authentication failed:\n{message}")
            return
        
        # Authentication successful, now validate license
        self.status_label.setText("Validating license...")
        
        try:
            is_valid, license_message, license_info = self.license_manager.validate_license(force_online=True)
            
            # Check both is_valid and status is ACTIVE
            license_status = license_info.get('status', '').upper() if license_info else ''
            
            if is_valid and license_status == 'ACTIVE':
                # Get license details for display
                plan = license_info.get('plan', 'unknown') if license_info else 'unknown'
                expires_at = license_info.get('expires_at') if license_info else None
                
                status_text = f"License activated successfully!\nPlan: {plan}"
                if expires_at:
                    status_text += f"\nExpires: {expires_at}"
                
                self.status_label.setText(status_text)
                self.progress_bar.setVisible(False)
                
                QMessageBox.information(
                    self,
                    "Activation Successful",
                    f"License activated successfully!\n\n"
                    f"Plan: {plan}\n"
                    + (f"Expires: {expires_at}\n" if expires_at else "")
                    + "\nYou can now use all features of Upload Bridge."
                )
                
                # Emit signal for parent to handle
                self.activation_successful.emit()
                self.accept()
            else:
                self.progress_bar.setVisible(False)
                self.activate_btn.setEnabled(True)
                self.close_btn.setEnabled(True)
                error_msg = f"License validation failed: {license_message}"
                if license_status and license_status != 'ACTIVE':
                    error_msg = f"License status is not ACTIVE: {license_status}\n\n{license_message}"
                self.status_label.setText(error_msg)
                QMessageBox.critical(
                    self,
                    "License Validation Failed",
                    f"License validation failed:\n\nStatus: {license_status or 'UNKNOWN'}\n"
                    f"Message: {license_message}\n\n"
                    "Please ensure you have an active paid plan."
                )
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.activate_btn.setEnabled(True)
            self.close_btn.setEnabled(True)
            self.status_label.setText(f"Error validating license: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error validating license:\n{str(e)}"
            )
