"""
Media Upload Tab - Convert images, GIFs, and videos to LED patterns
"""

import os
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QMessageBox, QSplitter, QGroupBox,
                               QTextEdit, QComboBox, QSpinBox, QSlider, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from core.pattern import Pattern
from ui.widgets.media_preview_widget import MediaPreviewWidget


class MediaUploadTab(QWidget):
    """Tab for uploading and converting media files to LED patterns"""
    
    # Signals
    pattern_loaded = Signal(object)  # Emits Pattern object
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_pattern: Optional[Pattern] = None
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create scroll area for responsive design
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("🎬 Media to LED Converter")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00ff88; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Convert images, GIFs, and videos into LED patterns.\n"
            "Supports PNG, JPG, BMP, GIF, MP4, AVI, MOV formats."
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #cccccc; margin-bottom: 15px; font-size: 11px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter)
        
        # Left side - Media preview
        self.media_preview = MediaPreviewWidget()
        self.media_preview.pattern_created.connect(self.on_pattern_created)
        splitter.addWidget(self.media_preview)
        
        # Right side - Pattern info and controls
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 10, 0)
        right_layout.setSpacing(15)
        
        # Pattern info
        info_group = QGroupBox("Pattern Information")
        info_layout = QVBoxLayout(info_group)
        
        self.pattern_info = QTextEdit()
        self.pattern_info.setMaximumHeight(200)
        self.pattern_info.setReadOnly(True)
        self.pattern_info.setText("No pattern loaded")
        self.pattern_info.setStyleSheet("font-family: monospace; font-size: 10px;")
        info_layout.addWidget(self.pattern_info)
        
        right_layout.addWidget(info_group)
        
        # Quick settings
        settings_group = QGroupBox("Quick Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Preset dimensions
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "8x8 Matrix",
            "16x16 Matrix", 
            "32x16 Strip",
            "64x32 Panel",
            "128x64 Panel"
        ])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)
        settings_layout.addLayout(preset_layout)
        
        # LED count info
        self.led_count_label = QLabel("LEDs: 0")
        self.led_count_label.setStyleSheet("font-weight: bold; color: #00ff88;")
        settings_layout.addWidget(self.led_count_label)
        
        # Frame count info
        self.frame_count_label = QLabel("Frames: 0")
        self.frame_count_label.setStyleSheet("font-weight: bold; color: #00ff88;")
        settings_layout.addWidget(self.frame_count_label)
        
        right_layout.addWidget(settings_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Load pattern button
        self.load_pattern_button = QPushButton("Load Pattern")
        self.load_pattern_button.clicked.connect(self.load_pattern)
        self.load_pattern_button.setEnabled(False)
        self.load_pattern_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        actions_layout.addWidget(self.load_pattern_button)
        
        # Save pattern button
        self.save_pattern_button = QPushButton("Save Pattern")
        self.save_pattern_button.clicked.connect(self.save_pattern)
        self.save_pattern_button.setEnabled(False)
        self.save_pattern_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        actions_layout.addWidget(self.save_pattern_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_pattern)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        actions_layout.addWidget(self.clear_button)
        
        right_layout.addWidget(actions_group)
        
        # Tips
        tips_group = QGroupBox("Tips")
        tips_layout = QVBoxLayout(tips_group)
        
        tips_text = QTextEdit()
        tips_text.setMaximumHeight(150)
        tips_text.setReadOnly(True)
        tips_text.setText("""
💡 Tips for best results:

• Use high contrast images for better LED visibility
• For videos, shorter clips work better (under 10 seconds)
• GIFs with fewer colors convert faster
• Adjust brightness based on your LED strip type
• Test with small dimensions first, then scale up
• RGB color order works for most LED strips
        """.strip())
        tips_text.setStyleSheet("font-size: 10px; line-height: 1.4;")
        tips_layout.addWidget(tips_text)
        
        right_layout.addWidget(tips_group)
        
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (responsive)
        splitter.setSizes([600, 400])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Status
        self.status_label = QLabel("Ready to convert media")
        self.status_label.setStyleSheet("""
            padding: 8px;
            background-color: #3b3b3b;
            border: 1px solid #555555;
            border-radius: 4px;
            color: #ffffff;
            font-size: 11px;
        """)
        main_layout.addWidget(self.status_label)
    
    def apply_preset(self, preset_name: str):
        """Apply dimension preset"""
        if preset_name == "Custom":
            return
        
        presets = {
            "8x8 Matrix": (8, 8),
            "16x16 Matrix": (16, 16),
            "32x16 Strip": (32, 16),
            "64x32 Panel": (64, 32),
            "128x64 Panel": (128, 64)
        }
        
        if preset_name in presets:
            width, height = presets[preset_name]
            self.media_preview.width_spin.setValue(width)
            self.media_preview.height_spin.setValue(height)
    
    def on_pattern_created(self, pattern: Pattern):
        """Handle pattern creation from media - automatically sync to all tabs"""
        self.current_pattern = pattern
        self.update_pattern_info()
        self.load_pattern_button.setEnabled(True)
        self.save_pattern_button.setEnabled(True)
        self.status_label.setText(f"Pattern created: {pattern.name}")
        
        # Automatically sync to all tabs when pattern is created
        # This ensures immediate availability across all tabs
        self.pattern_loaded.emit(pattern)
        self.status_label.setText(f"✅ Pattern created and loaded to all tabs: {pattern.name}")
    
    def update_pattern_info(self):
        """Update pattern information display"""
        if not self.current_pattern:
            self.pattern_info.setText("No pattern loaded")
            self.led_count_label.setText("LEDs: 0")
            self.frame_count_label.setText("Frames: 0")
            return
        
        pattern = self.current_pattern
        metadata = pattern.metadata
        
        info_text = f"""
Name: {pattern.name}
Dimensions: {metadata.width} x {metadata.height}
LEDs: {metadata.width * metadata.height}
Frames: {len(pattern.frames)}
Duration: {sum(frame.duration_ms for frame in pattern.frames) / 1000:.1f}s
FPS: {metadata.fps:.1f}
Color Order: {metadata.color_order}
Brightness: {metadata.brightness:.1f}
        """.strip()
        
        self.pattern_info.setText(info_text)
        self.led_count_label.setText(f"LEDs: {metadata.width * metadata.height}")
        self.frame_count_label.setText(f"Frames: {len(pattern.frames)}")
    
    def load_pattern(self):
        """Load pattern into main application"""
        if self.current_pattern:
            self.pattern_loaded.emit(self.current_pattern)
            self.status_label.setText("Pattern loaded successfully!")
        else:
            QMessageBox.warning(self, "Warning", "No pattern to load")
    
    def save_pattern(self):
        """Save pattern to file"""
        if not self.current_pattern:
            QMessageBox.warning(self, "Warning", "No pattern to save")
            return
        
        # This would integrate with the main application's save functionality
        QMessageBox.information(self, "Info", "Pattern save functionality will be integrated with main application")
    
    def clear_pattern(self):
        """Clear current pattern"""
        self.current_pattern = None
        self.update_pattern_info()
        self.load_pattern_button.setEnabled(False)
        self.save_pattern_button.setEnabled(False)
        self.status_label.setText("Pattern cleared")
    
    def get_current_pattern(self) -> Optional[Pattern]:
        """Get current pattern"""
        return self.current_pattern
    
    def set_pattern(self, pattern: Pattern):
        """Set pattern from external source"""
        self.current_pattern = pattern
        self.update_pattern_info()
        self.load_pattern_button.setEnabled(True)
        self.save_pattern_button.setEnabled(True)
        self.status_label.setText(f"Pattern set: {pattern.name}")
