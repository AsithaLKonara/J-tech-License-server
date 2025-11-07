"""
Media Preview Widget - Preview images, GIFs, and videos before conversion
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
import numpy as np
from PIL import Image, ImageSequence
import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSlider, QSpinBox, QComboBox,
                               QGroupBox, QFileDialog, QMessageBox, QProgressBar,
                               QTextEdit, QSplitter)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QPixmap, QImage, QFont

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.media_converter import MediaConverter, MediaInfo
from core.pattern import Pattern


class MediaPreviewWidget(QWidget):
    """Widget for previewing and converting media files"""
    
    # Signals
    pattern_created = Signal(object)  # Emits Pattern object
    conversion_progress = Signal(int)  # Progress percentage
    conversion_status = Signal(str)  # Status message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.media_converter = MediaConverter()
        self.current_file: Optional[str] = None
        self.media_info: Optional[MediaInfo] = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        
        # File selection
        file_group = QGroupBox("Media File")
        file_layout = QVBoxLayout(file_group)
        
        # File selection button
        self.file_button = QPushButton("Select Media File")
        self.file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_button)
        
        # File info display
        self.file_info = QTextEdit()
        self.file_info.setMaximumHeight(100)
        self.file_info.setReadOnly(True)
        file_layout.addWidget(self.file_info)
        
        layout.addWidget(file_group)
        
        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Media preview
        self.preview_label = QLabel("No media selected")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("border: 1px solid gray; background-color: black; color: white;")
        preview_layout.addWidget(self.preview_label)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶")
        self.play_button.clicked.connect(self.toggle_preview)
        self.play_button.setEnabled(False)
        controls_layout.addWidget(self.play_button)
        
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.valueChanged.connect(self.seek_frame)
        self.frame_slider.setEnabled(False)
        controls_layout.addWidget(self.frame_slider)
        
        self.frame_label = QLabel("Frame: 0/0")
        controls_layout.addWidget(self.frame_label)
        
        preview_layout.addLayout(controls_layout)
        layout.addWidget(preview_group)
        
        # Conversion settings
        settings_group = QGroupBox("Conversion Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Dimensions
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setValue(64)
        dim_layout.addWidget(self.width_spin)
        
        dim_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 1000)
        self.height_spin.setValue(32)
        dim_layout.addWidget(self.height_spin)
        
        settings_layout.addLayout(dim_layout)
        
        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        fps_layout.addWidget(self.fps_spin)
        settings_layout.addLayout(fps_layout)
        
        # Brightness
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_label = QLabel("100%")
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_label.setText(f"{v}%")
        )
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_label)
        settings_layout.addLayout(brightness_layout)
        
        # Color order
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color Order:"))
        self.color_order_combo = QComboBox()
        self.color_order_combo.addItems(['RGB', 'GRB', 'BRG', 'BGR', 'RBG', 'GBR'])
        color_layout.addWidget(self.color_order_combo)
        settings_layout.addLayout(color_layout)
        
        layout.addWidget(settings_group)
        
        # Conversion
        convert_group = QGroupBox("Convert to LED Pattern")
        convert_layout = QVBoxLayout(convert_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        convert_layout.addWidget(self.progress_bar)
        
        # Convert button
        self.convert_button = QPushButton("Convert to LED Pattern")
        self.convert_button.clicked.connect(self.convert_media)
        self.convert_button.setEnabled(False)
        convert_layout.addWidget(self.convert_button)
        
        layout.addWidget(convert_group)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def select_file(self):
        """Select media file"""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter(
            "Media Files (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.avi *.mov *.mkv *.webm);;"
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;"
            "Videos (*.mp4 *.avi *.mov *.mkv *.webm);;"
            "All Files (*)"
        )
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.load_media(file_path)
    
    def load_media(self, file_path: str):
        """Load media file for preview"""
        try:
            self.current_file = file_path
            self.media_info = self.media_converter.get_media_info(file_path)
            
            # Update file info
            info_text = f"""
File: {Path(file_path).name}
Type: {self.media_info.format.upper()}
Dimensions: {self.media_info.width} x {self.media_info.height}
Frames: {self.media_info.frame_count}
Duration: {self.media_info.duration_ms / 1000:.1f}s
FPS: {self.media_info.fps:.1f}
Size: {self.media_info.file_size / 1024:.1f} KB
            """.strip()
            
            self.file_info.setText(info_text)
            
            # Update conversion settings
            self.width_spin.setValue(min(self.media_info.width, 1000))
            self.height_spin.setValue(min(self.media_info.height, 1000))
            self.fps_spin.setValue(int(self.media_info.fps))
            
            # Enable controls
            self.convert_button.setEnabled(True)
            self.play_button.setEnabled(True)
            self.frame_slider.setEnabled(True)
            
            # Setup preview
            self.setup_preview()
            
            self.status_label.setText(f"Loaded: {Path(file_path).name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load media file:\n{str(e)}")
            self.status_label.setText("Error loading file")
    
    def setup_preview(self):
        """Setup preview based on media type"""
        if not self.media_info:
            return
        
        # Setup frame slider
        self.frame_slider.setRange(0, max(0, self.media_info.frame_count - 1))
        self.frame_slider.setValue(0)
        
        # Show first frame
        self.update_preview()
    
    def update_preview(self):
        """Update preview display"""
        if not self.current_file or not self.media_info:
            return
        
        try:
            frame_index = self.frame_slider.value()
            
            if self.media_info.format == 'image':
                self.update_image_preview(frame_index)
            elif self.media_info.format == 'video':
                self.update_video_preview(frame_index)
            
            self.frame_label.setText(f"Frame: {frame_index + 1}/{self.media_info.frame_count}")
            
        except Exception as e:
            self.status_label.setText(f"Preview error: {str(e)}")
    
    def update_image_preview(self, frame_index: int):
        """Update image preview"""
        with Image.open(self.current_file) as img:
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                # Animated GIF
                img.seek(frame_index)
            
            # Convert to QPixmap
            img_rgb = img.convert('RGB')
            img_array = np.array(img_rgb)
            
            # Resize for preview
            preview_size = (400, 300)
            img_resized = img.resize(preview_size, Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            qimg = QImage(img_resized.tobytes(), img_resized.width, img_resized.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.preview_label.setPixmap(pixmap)
    
    def update_video_preview(self, frame_index: int):
        """Update video preview"""
        cap = cv2.VideoCapture(self.current_file)
        
        if not cap.isOpened():
            return
        
        # Seek to frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize for preview
            preview_size = (400, 300)
            frame_resized = cv2.resize(frame_rgb, preview_size)
            
            # Convert to QPixmap
            height, width, channel = frame_resized.shape
            bytes_per_line = 3 * width
            qimg = QImage(frame_resized.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.preview_label.setPixmap(pixmap)
        
        cap.release()
    
    def toggle_preview(self):
        """Toggle preview playback"""
        if self.preview_timer.isActive():
            self.preview_timer.stop()
            self.play_button.setText("▶")
        else:
            if self.media_info and self.media_info.frame_count > 1:
                # Calculate timer interval based on FPS
                interval = int(1000 / self.media_info.fps) if self.media_info.fps > 0 else 100
                self.preview_timer.start(interval)
                self.play_button.setText("⏸")
    
    def seek_frame(self, frame_index: int):
        """Seek to specific frame"""
        self.update_preview()
    
    def convert_media(self):
        """Convert media to LED pattern"""
        if not self.current_file:
            return
        
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.convert_button.setEnabled(False)
            
            # Get conversion settings
            target_width = self.width_spin.value()
            target_height = self.height_spin.value()
            fps = self.fps_spin.value()
            brightness = self.brightness_slider.value() / 100.0
            color_order = self.color_order_combo.currentText()
            
            self.status_label.setText("Converting media...")
            
            # Convert in a separate thread to avoid blocking UI
            self.conversion_thread = ConversionThread(
                self.media_converter,
                self.current_file,
                target_width,
                target_height,
                fps,
                brightness,
                color_order
            )
            
            self.conversion_thread.progress_updated.connect(self.progress_bar.setValue)
            self.conversion_thread.status_updated.connect(self.status_label.setText)
            self.conversion_thread.pattern_created.connect(self.on_pattern_created)
            self.conversion_thread.finished.connect(self.on_conversion_finished)
            
            self.conversion_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Conversion failed:\n{str(e)}")
            self.status_label.setText("Conversion failed")
            self.progress_bar.setVisible(False)
            self.convert_button.setEnabled(True)
    
    def on_pattern_created(self, pattern: Pattern):
        """Handle pattern creation"""
        self.pattern_created.emit(pattern)
    
    def on_conversion_finished(self):
        """Handle conversion completion"""
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        self.status_label.setText("Conversion completed!")


class ConversionThread(QThread):
    """Thread for media conversion"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    pattern_created = Signal(object)
    
    def __init__(self, converter, file_path, width, height, fps, brightness, color_order):
        super().__init__()
        self.converter = converter
        self.file_path = file_path
        self.width = width
        self.height = height
        self.fps = fps
        self.brightness = brightness
        self.color_order = color_order
    
    def run(self):
        """Run conversion"""
        try:
            self.status_updated.emit("Converting media...")
            self.progress_updated.emit(10)
            
            # Convert media to pattern
            pattern = self.converter.convert_to_pattern(
                self.file_path,
                self.width,
                self.height,
                self.fps,
                self.brightness,
                self.color_order
            )
            
            self.progress_updated.emit(90)
            self.status_updated.emit("Finalizing pattern...")
            
            # Emit pattern
            self.pattern_created.emit(pattern)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Conversion completed!")
            
        except Exception as e:
            self.status_updated.emit(f"Conversion failed: {str(e)}")
            self.progress_updated.emit(0)
