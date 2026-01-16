"""
Responsive Scrollable Widget - Base class for responsive UI components
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                               QFrame, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont


class ResponsiveScrollableWidget(QWidget):
    """Base widget with responsive design and scrollbars"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(20)
        
        # Set up scroll area
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        # Apply responsive styling
        self.apply_responsive_styling()
    
    def apply_responsive_styling(self):
        """Apply responsive styling based on screen size"""
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Determine screen size category
        if screen_width >= 1920 and screen_height >= 1080:
            self.font_size = 12
            self.spacing = 20
            self.margins = 20
        elif screen_width >= 1366 and screen_height >= 768:
            self.font_size = 11
            self.spacing = 15
            self.margins = 15
        else:
            self.font_size = 10
            self.spacing = 10
            self.margins = 10
        
        # Apply styling
        self.setStyleSheet(f"""
            ResponsiveScrollableWidget {{
                background-color: #2b2b2b;
                color: #ffffff;
                font-size: {self.font_size}px;
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                background-color: #3b3b3b;
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #5a5a5a;
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: #7a7a7a;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: #3b3b3b;
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: #5a5a5a;
                border-radius: 6px;
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: #7a7a7a;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
        """)
        
        # Update layout margins and spacing
        self.content_layout.setContentsMargins(self.margins, self.margins, self.margins, self.margins)
        self.content_layout.setSpacing(self.spacing)
    
    def add_widget(self, widget):
        """Add widget to content layout"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to content layout"""
        self.content_layout.addLayout(layout)
    
    def add_stretch(self, stretch=0):
        """Add stretch to content layout"""
        self.content_layout.addStretch(stretch)
    
    def clear_content(self):
        """Clear all content"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def resizeEvent(self, event):
        """Handle resize events for responsive design"""
        super().resizeEvent(event)
        
        # Adjust content based on new size
        width = event.size().width()
        height = event.size().height()
        
        # Update scrollbar policies based on content size
        if width < 800:
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        if height < 600:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

