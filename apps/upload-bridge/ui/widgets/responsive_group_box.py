"""
Responsive Group Box - Enhanced group box with responsive design
"""

from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QWidget, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont


class ResponsiveGroupBox(QGroupBox):
    """Responsive group box with adaptive sizing and styling"""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 20, 15, 15)
        self.layout.setSpacing(10)
        
        # Apply responsive styling
        self.apply_responsive_styling()
    
    def apply_responsive_styling(self):
        """Apply responsive styling based on screen size"""
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Determine styling based on screen size
        if screen_width >= 1920 and screen_height >= 1080:
            font_size = 12
            padding = 15
            margin = 20
        elif screen_width >= 1366 and screen_height >= 768:
            font_size = 11
            padding = 12
            margin = 15
        else:
            font_size = 10
            padding = 10
            margin = 10
        
        # Apply styling
        self.setStyleSheet(f"""
            ResponsiveGroupBox {{
                font-size: {font_size}px;
                font-weight: bold;
                color: #ffffff;
                background-color: #3b3b3b;
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                margin: {margin}px;
                padding: {padding}px;
            }}
            
            ResponsiveGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00ff88;
                font-weight: bold;
            }}
            
            ResponsiveGroupBox:hover {{
                border-color: #7a7a7a;
                background-color: #404040;
            }}
        """)
    
    def add_widget(self, widget):
        """Add widget to layout"""
        self.layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to group box"""
        self.layout.addLayout(layout)
    
    def add_stretch(self, stretch=0):
        """Add stretch to layout"""
        self.layout.addStretch(stretch)
    
    def set_content_margins(self, left, top, right, bottom):
        """Set content margins"""
        self.layout.setContentsMargins(left, top, right, bottom)
    
    def set_spacing(self, spacing):
        """Set spacing between widgets"""
        self.layout.setSpacing(spacing)


class ResponsiveGridGroupBox(ResponsiveGroupBox):
    """Responsive group box with grid layout"""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        
        # Replace layout with grid layout
        self.layout.deleteLater()
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(15, 20, 15, 15)
        self.layout.setSpacing(10)
    
    def add_widget(self, widget, row, col, rowspan=1, colspan=1):
        """Add widget to grid layout"""
        self.layout.addWidget(widget, row, col, rowspan, colspan)
    
    def add_label(self, text, row, col, rowspan=1, colspan=1):
        """Add label to grid layout"""
        from PySide6.QtWidgets import QLabel
        label = QLabel(text)
        label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.layout.addWidget(label, row, col, rowspan, colspan)
        return label


class ResponsiveHorizontalGroupBox(ResponsiveGroupBox):
    """Responsive group box with horizontal layout"""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        
        # Replace layout with horizontal layout
        self.layout.deleteLater()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 20, 15, 15)
        self.layout.setSpacing(10)
    
    def add_widget(self, widget, stretch=0):
        """Add widget to horizontal layout"""
        self.layout.addWidget(widget, stretch)
    
    def add_stretch(self, stretch=0):
        """Add stretch to horizontal layout"""
        self.layout.addStretch(stretch)

