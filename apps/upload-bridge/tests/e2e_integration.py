# apps/upload-bridge/tests/e2e_integration.py
import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel
from PySide6.QtCore import Qt, QTimer
import os
import time
import requests # For direct API calls to the local license server

# Assume QApplication instance is managed by pytest-qt fixture
# You might need to import your actual main application window and components
# For this example, we'll mock a very basic UI with login elements

# Global variable to store the local license server URL
LICENSE_SERVER_URL = "https://j-tech-license-server.vercel.app"

class MockLoginWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mock Upload Bridge Login")
        self.setGeometry(100, 100, 400, 200)

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Email")
        self.email_input.setGeometry(50, 30, 300, 30)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setGeometry(50, 70, 300, 30)

        self.login_button = QPushButton("Login", self)
        self.login_button.setGeometry(150, 110, 100, 30)
        self.login_button.clicked.connect(self.attempt_login)

        self.status_label = QLabel("", self)
        self.status_label.setGeometry(50, 150, 300, 30)

        self.logged_in_label = QLabel("Not Logged In", self) # For testing successful login state
        self.logged_in_label.setVisible(False)

        # In a real app, you'd load your actual main window here
        # For simplicity, we'll just show a success message
        self.main_app_window = QLabel("Main App Content (Licensed Features Visible)", self)
        self.main_app_window.setVisible(False)
        self.main_app_window.setGeometry(50, 50, 300, 100)


    def attempt_login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        login_payload = {
            "email": email,
            "password": password,
            "device_id": "PY_E2E_TEST",
            "device_name": "PyTest E2E"
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(f"{LICENSE_SERVER_URL}/api/v2/auth/login", json=login_payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.status_label.setText("Login Successful!")
                self.status_label.setStyleSheet("color: green")
                self.logged_in_label.setText(f"Logged In: {data['user']['email']}, Plan: {data['entitlement_token']['plan']}")
                self.logged_in_label.setVisible(True)
                self.main_app_window.setVisible(True)
                self.email_input.setVisible(False)
                self.password_input.setVisible(False)
                self.login_button.setVisible(False)
            else:
                self.status_label.setText(f"Login Failed: {response.json().get('message', 'Unknown error')}")
                self.status_label.setStyleSheet("color: red")
        except requests.exceptions.ConnectionError:
            self.status_label.setText("Connection Error: Could not reach license server.")
            self.status_label.setStyleSheet("color: red")
        except Exception as e:
            self.status_label.setText(f"An error occurred: {e}")
            self.status_label.setStyleSheet("color: red")

@pytest.fixture
def desktop_app(qtbot):
    """Fixture to set up and tear down the desktop application for testing."""
    app = MockLoginWindow()
    app.show()
    qtbot.addWidget(app) # Ensure the widget is managed by qtbot
    yield app
    app.close()

def test_desktop_app_login_pro_user(desktop_app, qtbot):
    """Test successful login for a 'pro' user."""
    qtbot.keyClicks(desktop_app.email_input, "test@example.com")
    qtbot.keyClicks(desktop_app.password_input, "testpassword123")
    qtbot.mouseClick(desktop_app.login_button, Qt.LeftButton)

    # Wait for the UI to update after the login attempt (network request)
    qtbot.waitUntil(lambda: "Login Successful!" in desktop_app.status_label.text(), timeout=10000)
    assert "Login Successful!" in desktop_app.status_label.text()
    assert "Logged In: test@example.com, Plan: pro" in desktop_app.logged_in_label.text()
    assert desktop_app.main_app_window.isVisible() # Licensed features should be visible

def test_desktop_app_login_basic_user(desktop_app, qtbot):
    """Test successful login for a 'basic' user and verify features (simplified)."""
    qtbot.keyClicks(desktop_app.email_input, "demo@example.com")
    qtbot.keyClicks(desktop_app.password_input, "demo123")
    qtbot.mouseClick(desktop_app.login_button, Qt.LeftButton)

    qtbot.waitUntil(lambda: "Login Successful!" in desktop_app.status_label.text(), timeout=10000)
    assert "Login Successful!" in desktop_app.status_label.text()
    assert "Logged In: demo@example.com, Plan: basic" in desktop_app.logged_in_label.text()
    assert desktop_app.main_app_window.isVisible() # Main content still visible, but specific features would be disabled in a real app

def test_desktop_app_login_invalid_credentials(desktop_app, qtbot):
    """Test login with invalid credentials."""
    qtbot.keyClicks(desktop_app.email_input, "invalid@example.com")
    qtbot.keyClicks(desktop_app.password_input, "wrongpassword")
    qtbot.mouseClick(desktop_app.login_button, Qt.LeftButton)

    qtbot.waitUntil(lambda: "Login Failed:" in desktop_app.status_label.text(), timeout=10000)
    assert "Login Failed:" in desktop_app.status_label.text()
    assert not desktop_app.main_app_window.isVisible() # Main app content should not be visible

# In a real application, you would extend this with tests for:
# - Pattern creation
# - Media import
# - Flashing (requires mocking hardware or dedicated hardware test setup)
# - UI element interactions
# - Feature gating based on license plan
