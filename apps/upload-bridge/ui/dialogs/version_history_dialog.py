"""
Version History Dialog - View and restore pattern versions
"""

from __future__ import annotations

from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QTextEdit,
    QMessageBox,
    QGroupBox,
)
from PySide6.QtCore import Qt, Signal
from datetime import datetime

from core.pattern import Pattern
from core.pattern_versioning import PatternVersion, PatternVersionManager


class VersionHistoryDialog(QDialog):
    """Dialog for viewing and restoring pattern versions."""
    
    version_restored = Signal(Pattern)  # Emitted when a version is restored
    
    def __init__(self, version_manager: PatternVersionManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Version History")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self._version_manager = version_manager
        
        self._setup_ui()
        self._load_versions()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Pattern Version History")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Version list
        list_group = QGroupBox("Versions")
        list_layout = QVBoxLayout()
        
        self.version_list = QListWidget()
        self.version_list.itemSelectionChanged.connect(self._on_version_selected)
        list_layout.addWidget(self.version_list)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group, 1)
        
        # Version details
        details_group = QGroupBox("Version Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        restore_btn = QPushButton("Restore This Version")
        restore_btn.clicked.connect(self._on_restore_clicked)
        buttons_layout.addWidget(restore_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_versions(self):
        """Load versions into list."""
        self.version_list.clear()
        versions = self._version_manager.get_versions()
        
        # Sort by timestamp (newest first)
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        
        for version in versions:
            # Format timestamp
            try:
                dt = datetime.fromisoformat(version.timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = version.timestamp
            
            item_text = f"{version.version_id} - {time_str}"
            if version.description:
                item_text += f" - {version.description}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, version.version_id)
            self.version_list.addItem(item)
    
    def _on_version_selected(self):
        """Handle version selection."""
        current_item = self.version_list.currentItem()
        if current_item is None:
            self.details_text.clear()
            return
        
        version_id = current_item.data(Qt.UserRole)
        version = self._version_manager.get_version(version_id)
        
        if version is None:
            self.details_text.clear()
            return
        
        # Format details
        details = []
        details.append(f"Version ID: {version.version_id}")
        details.append(f"Timestamp: {version.timestamp}")
        details.append(f"Description: {version.description}")
        
        if version.metadata:
            details.append("\nMetadata:")
            for key, value in version.metadata.items():
                details.append(f"  {key}: {value}")
        
        if version.pattern_snapshot:
            details.append("\nPattern Snapshot:")
            details.append(f"  Name: {version.pattern_snapshot.get('name', 'N/A')}")
            if 'metadata' in version.pattern_snapshot:
                meta = version.pattern_snapshot['metadata']
                details.append(f"  Size: {meta.get('width', '?')}×{meta.get('height', '?')}")
                # Show dimension detection info if available
                dim_source = meta.get('dimension_source')
                dim_confidence = meta.get('dimension_confidence', 0.0)
                if dim_source and dim_source != 'unknown':
                    details.append(f"  Dimension Source: {dim_source} (confidence: {dim_confidence:.1%})")
                # Show wiring hints if available
                wiring_hint = meta.get('wiring_mode_hint')
                if wiring_hint:
                    hint_conf = meta.get('hint_confidence', 0.0)
                    details.append(f"  Wiring Hint: {wiring_hint} (confidence: {hint_conf:.1%})")
            # Count frames from snapshot
            frames_data = version.pattern_snapshot.get('frames', [])
            details.append(f"  Frames: {len(frames_data)}")
        
        self.details_text.setText("\n".join(details))
    
    def _on_restore_clicked(self):
        """Handle restore button click."""
        current_item = self.version_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "No Selection", "Please select a version to restore.")
            return
        
        version_id = current_item.data(Qt.UserRole)
        version = self._version_manager.get_version(version_id)
        
        if version is None:
            QMessageBox.warning(self, "Error", "Version not found.")
            return
        
        reply = QMessageBox.question(
            self,
            "Restore Version",
            f"Restore version '{version.version_id}'?\n\n"
            f"This will replace the current pattern with this version.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Restore pattern
        pattern = self._version_manager.restore_version(version_id)
        if pattern is None:
            QMessageBox.warning(
                self,
                "Restore Failed",
                "Could not restore pattern. The version data may be corrupted or incomplete."
            )
            return
        
        # Verify critical metadata was preserved
        if not hasattr(pattern, 'metadata'):
            QMessageBox.warning(
                self,
                "Restore Warning",
                "Pattern restored but metadata may be incomplete."
            )
        
        # Verify dimension metadata
        if hasattr(pattern.metadata, 'dimension_source'):
            source = pattern.metadata.dimension_source
            confidence = getattr(pattern.metadata, 'dimension_confidence', 0.0)
            if source == 'unknown' and confidence == 0.0:
                # This is okay - might be a new pattern
                pass
        
        self.version_restored.emit(pattern)
        self.accept()

