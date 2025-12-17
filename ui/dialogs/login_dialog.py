"""
Login Dialog - Account-Based Authentication
Replaces file-based activation with Auth0 account login
"""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QCheckBox,
    QTabWidget,
    QWidget,
    QTextEdit,
    QProgressBar,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from core.auth_manager import AuthManager


class AuthWorker(QThread):
    """Background worker for authentication"""
    finished = Signal(bool, str)
    progress = Signal(str)
    
    def __init__(self, auth_manager: AuthManager, auth0_token: str, device_name: str):
        super().__init__()
        self.auth_manager = auth_manager
        self.auth0_token = auth0_token
        self.device_name = device_name
    
    def run(self):
        try:
            self.progress.emit("Authenticating...")
            success, message = self.auth_manager.login(self.auth0_token, self.device_name)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, str(e))


class LoginDialog(QDialog):
    """Account-based login dialog with Auth0 integration"""
    
    def __init__(self, parent=None, auth_manager: Optional[AuthManager] = None, server_url: str = "http://localhost:3000"):
        super().__init__(parent)
        self.auth_manager = auth_manager or AuthManager(server_url=server_url)
        self.server_url = server_url
        self.auth_worker = None
        
        self.setWindowTitle("Login Required")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Upload Bridge - Account Login")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Info label
        info = QLabel(
            "Please log in with your account to continue.\n"
            "You can use email/password, magic link, or social login."
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
        
        # SSO tab
        sso_tab = self._build_sso_tab()
        tabs.addTab(sso_tab, "Social Login")
        
        layout.addWidget(tabs)
        
        # Remember me checkbox
        self.remember_me = QCheckBox("Remember me")
        self.remember_me.setChecked(True)
        layout.addWidget(self.remember_me)
        
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
        self.login_btn = QPushButton("Login")
        self.login_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel")
        buttons.addWidget(self.login_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)
        
        self.login_btn.clicked.connect(self.on_login)
        self.cancel_btn.clicked.connect(self.reject)
    
    def _build_email_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your@email.com")
        layout.addWidget(self.email_input)
        
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        layout.addWidget(self.password_input)
        
        create_account_btn = QPushButton("Create Account")
        create_account_btn.clicked.connect(self.on_create_account)
        layout.addWidget(create_account_btn)
        
        layout.addStretch()
        
        return widget
    
    def _build_magic_link_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Email:"))
        self.magic_email_input = QLineEdit()
        self.magic_email_input.setPlaceholderText("your@email.com")
        layout.addWidget(self.magic_email_input)
        
        send_link_btn = QPushButton("Send Magic Link")
        send_link_btn.clicked.connect(self.on_send_magic_link)
        layout.addWidget(send_link_btn)
        
        info = QLabel(
            "We'll send you a login link via email.\n"
            "Click the link to complete authentication."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        return widget
    
    def _build_sso_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("Login with your social account:")
        layout.addWidget(info)
        
        google_btn = QPushButton("Login with Google")
        google_btn.clicked.connect(lambda: self.on_sso_login('google'))
        layout.addWidget(google_btn)
        
        github_btn = QPushButton("Login with GitHub")
        github_btn.clicked.connect(lambda: self.on_sso_login('github'))
        layout.addWidget(github_btn)
        
        layout.addStretch()
        
        return widget
    
    def on_login(self):
        """Handle email/password login"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email:
            QMessageBox.warning(self, "Login", "Please enter your email address.")
            return
        
        if not password:
            QMessageBox.warning(self, "Login", "Please enter your password.")
            return
        
        # In a real implementation, you would:
        # 1. Use Auth0 SDK to authenticate
        # 2. Get Auth0 JWT token
        # 3. Exchange for session token
        
        # For now, show a message that Auth0 integration is needed
        QMessageBox.information(
            self,
            "Auth0 Integration Required",
            "Email/password login requires Auth0 SDK integration.\n\n"
            "Please use the Auth0 Lock widget or Auth0 SPA SDK.\n"
            "See: https://auth0.com/docs/quickstart/spa"
        )
    
    def on_send_magic_link(self):
        """Handle magic link request"""
        email = self.magic_email_input.text().strip()
        
        if not email:
            QMessageBox.warning(self, "Magic Link", "Please enter your email address.")
            return
        
        # In a real implementation, you would:
        # 1. Call Auth0 Passwordless API
        # 2. Send magic link email
        # 3. Poll for authentication completion
        
        QMessageBox.information(
            self,
            "Auth0 Integration Required",
            "Magic link requires Auth0 Passwordless API integration.\n\n"
            "See: https://auth0.com/docs/authenticate/passwordless"
        )
    
    def on_sso_login(self, provider: str):
        """Handle SSO login"""
        # In a real implementation, you would:
        # 1. Open Auth0 Universal Login
        # 2. Handle OAuth callback
        # 3. Get Auth0 JWT token
        # 4. Exchange for session token
        
        auth_url = f"{self.server_url}/auth/{provider}"
        QMessageBox.information(
            self,
            "SSO Login",
            f"Opening {provider} login in browser...\n\n"
            f"After logging in, return to this application."
        )
        webbrowser.open(auth_url)
    
    def on_create_account(self):
        """Open account creation page"""
        signup_url = f"{self.server_url}/signup"
        webbrowser.open(signup_url)
    
    def authenticate_with_token(self, auth0_token: str):
        """Authenticate with Auth0 token (called after OAuth flow)"""
        device_name = f"{sys.platform} Device"
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("Authenticating...")
        self.login_btn.setEnabled(False)
        
        self.auth_worker = AuthWorker(self.auth_manager, auth0_token, device_name)
        self.auth_worker.progress.connect(self.status_label.setText)
        self.auth_worker.finished.connect(self.on_auth_complete)
        self.auth_worker.start()
    
    def on_auth_complete(self, success: bool, message: str):
        """Handle authentication completion"""
        self.progress_bar.setVisible(False)
        self.login_btn.setEnabled(True)
        
        if success:
            self.status_label.setText("Login successful!")
            QMessageBox.information(self, "Success", "Login successful!")
            self.accept()
        else:
            self.status_label.setText(f"Login failed: {message}")
            QMessageBox.critical(self, "Login Failed", f"Login failed:\n{message}")


def ensure_authenticated_or_exit(parent=None, auth_manager: Optional[AuthManager] = None, server_url: str = "http://localhost:3000") -> None:
    """
    Show login dialog if not authenticated. Exit on cancel.
    
    Args:
        parent: Parent widget
        auth_manager: Optional AuthManager instance
        server_url: License server URL
    """
    if auth_manager is None:
        auth_manager = AuthManager(server_url=server_url)
    
    # Check if already authenticated
    if auth_manager.has_valid_token():
        return
    
    # Show login dialog
    dlg = LoginDialog(parent, auth_manager, server_url)
    if dlg.exec() != QDialog.Accepted:
        # User cancelled or login failed
        sys.exit(0)
