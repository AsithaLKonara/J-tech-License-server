"""
Login Dialog - Account-Based Authentication
Replaces file-based activation with Auth0 account login
"""

from __future__ import annotations

import os
import sys
import webbrowser
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont

from core.auth_manager import AuthManager
from core.oauth_handler import OAuthConfig, run_oauth_flow, OAuthResult


class OAuthWorker(QThread):
    """Background worker for OAuth flow"""
    finished = Signal(object)

    def __init__(self, oauth_config: OAuthConfig):
        super().__init__()
        self.oauth_config = oauth_config

    def run(self):
        try:
            result = run_oauth_flow(self.oauth_config)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(e)


class AuthWorker(QThread):
    """Background worker for authentication"""
    finished = Signal(bool, str)
    progress = Signal(str)
    
    def __init__(self, auth_manager: AuthManager, email: Optional[str] = None, 
                 password: Optional[str] = None, magic_link_token: Optional[str] = None, 
                 device_name: Optional[str] = None):
        super().__init__()
        self.auth_manager = auth_manager
        self.email = email
        self.password = password
        self.magic_link_token = magic_link_token
        self.device_name = device_name
    
    def run(self):
        try:
            self.progress.emit("Authenticating...")
            success, message = self.auth_manager.login(
                email=self.email,
                password=self.password,
                magic_link_token=self.magic_link_token,
                device_name=self.device_name
            )
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, str(e))


class LoginDialog(QDialog):
    """Account-based login dialog with Auth0 integration"""
    
    def __init__(self, parent=None, auth_manager: Optional[AuthManager] = None, config: dict = None):
        super().__init__(parent)
        self.config = config or {}
        self.server_url = self.config.get("auth_server_url") or os.environ.get("LICENSE_SERVER_URL") or os.environ.get("AUTH_SERVER_URL") or "https://j-tech-license-server.up.railway.app"
        self.auth_manager = auth_manager or AuthManager(server_url=self.server_url)
        self.auth_worker = None
        self.oauth_worker = None # New attribute for OAuth worker
        
        self.setWindowTitle("Login Required - Upload Bridge")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        # Make dialog modal and non-dismissible
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        
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
        
        if not email or not password:
            QMessageBox.warning(self, "Login", "Please enter both email and password.")
            return
        
        device_name = f"{sys.platform} Device"
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("Authenticating...")
        self.login_btn.setEnabled(False)
        
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
            response = requests.post(
                f"{self.server_url}/magic-link",
                json={'email': email},
                timeout=10
            )
            
            if response.status_code == 200:
                QMessageBox.information(
                    self,
                    "Magic Link Sent",
                    f"Magic link sent to {email}.\n\n"
                    "Please check your email and click the link to login."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to send magic link: {response.text}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to send magic link: {str(e)}"
            )
    
    def authenticate_with_magic_link_token(self, magic_link_token: str):
        """Authenticate with magic link token"""
        device_name = f"{sys.platform} Device"
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("Authenticating...")
        self.login_btn.setEnabled(False)
        
        self.auth_worker = AuthWorker(
            self.auth_manager,
            magic_link_token=magic_link_token,
            device_name=device_name
        )
        self.auth_worker.progress.connect(self.status_label.setText)
        self.auth_worker.finished.connect(self.on_auth_complete)
        self.auth_worker.start()
    
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
        signup_url = f"{self.server_url}/register"
        webbrowser.open(signup_url)

    def on_oauth_flow_complete(self, result: OAuthResult):
        """Handle completion of the OAuth flow from the worker thread."""
        self.progress_bar.setVisible(False)

        if isinstance(result, Exception):
            self.status_label.setText(f"OAuth flow failed: {result}")
            QMessageBox.critical(self, "Login Failed", f"OAuth flow failed:\n{result}")
            return

        if not result.success:
            self.status_label.setText(f"Login failed: {result.message}")
            QMessageBox.critical(self, "Login Failed", result.message)
            return

        tokens = result.tokens
        id_token = tokens.get("id_token")
        if not id_token:
            self.status_label.setText("Login failed: No id_token in Auth0 response")
            QMessageBox.critical(
                self,
                "Login Failed",
                "Auth0 response did not contain an id_token. Check Auth0 configuration."
            )
            return
        
        # Delegate to existing helper that uses AuthManager + background thread
        self.authenticate_with_token(id_token)

    def authenticate_with_token(self, auth0_token: str):
        """Authenticate with Auth0 token (called after OAuth flow) - kept for backward compatibility"""
        # For OAuth flow, we can still use auth0_token if needed
        # But for now, this is kept for compatibility
        device_name = f"{sys.platform} Device"
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("Authenticating...")
        self.login_btn.setEnabled(False)
        
        # Note: This would need to be updated if we want to support Auth0 tokens
        # For now, email/password and magic link are the primary methods
        QMessageBox.warning(
            self,
            "OAuth Not Supported",
            "OAuth login is not yet implemented. Please use email/password or magic link."
        )
        self.progress_bar.setVisible(False)
        self.login_btn.setEnabled(True)
    
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


from core.config import get_config
def ensure_authenticated_or_exit(parent=None, auth_manager: Optional[AuthManager] = None, config: dict = None) -> None:
    """
    Show login dialog if not authenticated. Exit on cancel.
    Login is MANDATORY - app cannot be used without authentication.
    
    Args:
        parent: Parent widget
        auth_manager: Optional AuthManager instance
        config: Application configuration dictionary
    """
    if config is None:
        config = get_config()

    server_url = config.get("auth_server_url", "https://j-tech-license-server.up.railway.app")

    if auth_manager is None:
        auth_manager = AuthManager(server_url=server_url)
    
    # Check if already authenticated
    if auth_manager.has_valid_token():
        return
    
    # Show login dialog (non-dismissible)
    dlg = LoginDialog(parent, auth_manager, config)
    result = dlg.exec()
    
    if result != QDialog.Accepted:
        # User cancelled or login failed - exit app
        QMessageBox.warning(
            parent,
            "Login Required",
            "Login is required to use Upload Bridge.\n\nApplication will now exit."
        )
        sys.exit(0)
