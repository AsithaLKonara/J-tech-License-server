"""
License Status Dialog - Display current license information
Shows license status, plan, expiry, and provides reactivate/logout options.
"""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.auth_manager import AuthManager
from core.license_manager import LicenseManager


class LicenseStatusDialog(QDialog):
    """Dialog for displaying license status and managing account"""
    
    def __init__(self, parent=None, auth_manager: Optional[AuthManager] = None,
                 license_manager: Optional[LicenseManager] = None, config: dict = None):
        super().__init__(parent)
        self.config = config or {}
        self.server_url = self.config.get("auth_server_url") or os.environ.get("LICENSE_SERVER_URL") or os.environ.get("AUTH_SERVER_URL") or "http://localhost:8000"
        self.auth_manager = auth_manager or AuthManager(server_url=self.server_url)
        self.license_manager = license_manager or LicenseManager(server_url=self.server_url)
        
        self.setWindowTitle("License Status - Upload Bridge")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self._build_ui()
        self._load_license_status()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("License Information")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Status section
        status_group = QVBoxLayout()
        status_group.addWidget(QLabel("License Type:"))
        self.license_type_label = QLabel("Account-Based")
        self.license_type_label.setStyleSheet("font-weight: bold;")
        status_group.addWidget(self.license_type_label)
        
        status_group.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Checking...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        status_group.addWidget(self.status_label)
        
        status_group.addWidget(QLabel("Plan:"))
        self.plan_label = QLabel("—")
        status_group.addWidget(self.plan_label)
        
        status_group.addWidget(QLabel("Expires:"))
        self.expires_label = QLabel("—")
        status_group.addWidget(self.expires_label)
        
        layout.addLayout(status_group)
        
        # Features section (if available)
        layout.addWidget(QLabel("Features:"))
        self.features_label = QLabel("—")
        self.features_label.setWordWrap(True)
        layout.addWidget(self.features_label)
        
        layout.addStretch()
        
        # Buttons
        buttons = QHBoxLayout()
        self.reactivate_btn = QPushButton("Reactivate Account")
        self.reactivate_btn.clicked.connect(self.on_reactivate)
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.on_logout)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        buttons.addWidget(self.reactivate_btn)
        buttons.addWidget(self.logout_btn)
        buttons.addStretch()
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)
    
    def _load_license_status(self):
        """Load and display current license status"""
        try:
            # Check if authenticated
            if not self.auth_manager.has_valid_token():
                self.status_label.setText("NOT AUTHENTICATED")
                self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")
                self.plan_label.setText("Please login to view license information")
                self.expires_label.setText("—")
                self.features_label.setText("—")
                return
            
            # Validate license
            is_valid, message, license_info = self.license_manager.validate_license(force_online=False)
            
            if is_valid and license_info:
                status = license_info.get('status', 'UNKNOWN').upper()
                
                # Set status with color
                if status == 'ACTIVE':
                    self.status_label.setText("ACTIVE")
                    self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
                elif status == 'EXPIRED':
                    self.status_label.setText("EXPIRED")
                    self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")
                else:
                    self.status_label.setText(status)
                    self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: orange;")
                
                # Set plan
                plan = license_info.get('plan', 'unknown')
                self.plan_label.setText(plan.title() if plan else "—")
                
                # Set expiry
                expires_at = license_info.get('expires_at')
                if expires_at:
                    self.expires_label.setText(expires_at)
                else:
                    self.expires_label.setText("Never (perpetual)")
                
                # Set features (if available)
                features = license_info.get('features', [])
                if features:
                    self.features_label.setText(", ".join(features))
                else:
                    self.features_label.setText("All standard features")
            else:
                # License invalid or not found
                self.status_label.setText("INVALID")
                self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")
                self.plan_label.setText("—")
                self.expires_label.setText("—")
                self.features_label.setText("—")
                
                if message:
                    self.plan_label.setText(f"Error: {message}")
        
        except Exception as e:
            self.status_label.setText("ERROR")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")
            self.plan_label.setText(f"Failed to load license status: {str(e)}")
            self.expires_label.setText("—")
            self.features_label.setText("—")
    
    def on_reactivate(self):
        """Open reactivation dialog"""
        from ui.dialogs.license_activation_dialog import LicenseActivationDialog
        
        dialog = LicenseActivationDialog(
            self,
            auth_manager=self.auth_manager,
            license_manager=self.license_manager,
            config=self.config
        )
        dialog.activation_successful.connect(self._on_activation_successful)
        dialog.exec()
    
    def _on_activation_successful(self):
        """Handle successful reactivation"""
        self._load_license_status()
        QMessageBox.information(
            self,
            "Reactivation Successful",
            "License reactivated successfully!"
        )
    
    def on_logout(self):
        """Logout and clear session"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?\n\n"
            "You will need to login again to use Upload Bridge.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear auth session
                self.auth_manager.logout()
                
                # Clear license cache
                if self.license_manager.cache_file.exists():
                    self.license_manager.cache_file.unlink()
                if self.license_manager.encrypted_license_file.exists():
                    self.license_manager.encrypted_license_file.unlink()
                
                QMessageBox.information(
                    self,
                    "Logged Out",
                    "You have been logged out successfully.\n\n"
                    "Please login again to use Upload Bridge."
                )
                
                self.accept()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Logout Error",
                    f"Failed to logout:\n{str(e)}"
                )
