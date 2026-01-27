"""
Splash Screen Widget - Premium loading screen for Upload Bridge.
"""

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QColor, QFont, QLinearGradient, QPainter, QBrush, QPen
from PySide6.QtWidgets import QSplashScreen, QApplication, QVBoxLayout, QLabel, QProgressBar, QFrame, QWidget
from pathlib import Path

class PremiumSplashScreen(QSplashScreen):
    """A premium splash screen with progress bar and status messages."""
    
    def __init__(self, icon_path: str = None):
        # Create a base pixmap
        width, height = 500, 300
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # UI Elements
        self.container = QFrame(self)
        self.container.setFixedSize(width, height)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 15px;
                border: 1px solid #333333;
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 40, 30, 30)
        layout.setSpacing(10)
        
        # Logo placeholder or Icon
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        if icon_path and Path(icon_path).exists():
            logo_pix = QPixmap(icon_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(logo_pix)
        else:
            self.logo_label.setText("🚀")
            self.logo_label.setStyleSheet("font-size: 60px;")
        layout.addWidget(self.logo_label)
        
        # Title
        self.title_label = QLabel("UPLOAD BRIDGE")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-family: 'Segoe UI', Arial;
                font-size: 24px;
                font-weight: bold;
                letter-spacing: 2px;
                background: transparent;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel("UNIVERSAL LED PATTERN DESIGNER")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-family: 'Segoe UI', Arial;
                font-size: 10px;
                font-weight: normal;
                letter-spacing: 4px;
                background: transparent;
            }
        """)
        layout.addWidget(self.subtitle_label)
        
        layout.addStretch()
        
        # Status Label
        self.status_label = QLabel("Initializing systems...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #BBBBBB;
                font-family: 'Segoe UI', Arial;
                font-size: 12px;
                background: transparent;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2D2D2D;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4A90E2, stop:1 #50E3C2);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Version
        self.version_label = QLabel("v2.5.0 Professional")
        self.version_label.setAlignment(Qt.AlignRight)
        self.version_label.setStyleSheet("color: #555555; font-size: 10px; background: transparent;")
        layout.addWidget(self.version_label)

    def show_message(self, message: str, progress: int = -1):
        """Update the status message and progress bar."""
        self.status_label.setText(message)
        if progress >= 0:
            self.progress_bar.setValue(progress)
        
        # Ensure UI updates
        QApplication.processEvents()
    
    def finish(self, main_window):
        """Fade out and close."""
        super().finish(main_window)
