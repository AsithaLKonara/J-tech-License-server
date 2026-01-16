"""
Pattern Marketplace Dialog - Browse and download shared Budurasmala patterns.
"""

from __future__ import annotations

import sys
import os
from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QTextEdit, QGroupBox, QFormLayout, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.services.pattern_sharing import PatternSharingService, SharedPattern
from core.pattern import Pattern
from core.project import save_project


class PatternMarketplaceDialog(QDialog):
    """Dialog for browsing and downloading shared patterns."""
    
    def __init__(self, parent=None, sharing_service: Optional[PatternSharingService] = None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Marketplace")
        self.setModal(True)
        self.resize(800, 600)
        
        self.sharing_service = sharing_service or PatternSharingService()
        self.selected_pattern: Optional[SharedPattern] = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Search and filters
        search_group = QGroupBox("Search & Filters")
        search_layout = QVBoxLayout()
        
        # Search bar
        search_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search patterns...")
        self.search_input.textChanged.connect(self._on_search)
        search_bar_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search)
        search_bar_layout.addWidget(search_btn)
        
        search_layout.addLayout(search_bar_layout)
        
        # Filters
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Vesak", "Buddhist", "Festival", "Custom"])
        self.category_combo.currentTextChanged.connect(self._on_search)
        filters_layout.addWidget(self.category_combo)
        
        filters_layout.addWidget(QLabel("Min Rating:"))
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(0, 5)
        self.rating_spin.setSuffix(" stars")
        self.rating_spin.valueChanged.connect(self._on_search)
        filters_layout.addWidget(self.rating_spin)
        
        filters_layout.addStretch()
        
        search_layout.addLayout(filters_layout)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Pattern list and details
        content_layout = QHBoxLayout()
        
        # Pattern list
        list_group = QGroupBox("Patterns")
        list_layout = QVBoxLayout()
        
        self.pattern_list = QListWidget()
        self.pattern_list.itemClicked.connect(self._on_pattern_selected)
        list_layout.addWidget(self.pattern_list)
        
        # List buttons
        list_buttons = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_list)
        list_buttons.addWidget(refresh_btn)
        
        popular_btn = QPushButton("Popular")
        popular_btn.clicked.connect(self._show_popular)
        list_buttons.addWidget(popular_btn)
        
        recent_btn = QPushButton("Recent")
        recent_btn.clicked.connect(self._show_recent)
        list_buttons.addWidget(recent_btn)
        
        list_buttons.addStretch()
        list_layout.addLayout(list_buttons)
        
        list_group.setLayout(list_layout)
        content_layout.addWidget(list_group, 1)
        
        # Pattern details
        details_group = QGroupBox("Pattern Details")
        details_layout = QVBoxLayout()
        
        self.pattern_name_label = QLabel("Select a pattern")
        self.pattern_name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        details_layout.addWidget(self.pattern_name_label)
        
        self.pattern_author_label = QLabel("")
        details_layout.addWidget(self.pattern_author_label)
        
        self.pattern_description = QTextEdit()
        self.pattern_description.setReadOnly(True)
        self.pattern_description.setMaximumHeight(100)
        details_layout.addWidget(self.pattern_description)
        
        # Pattern stats
        stats_layout = QHBoxLayout()
        self.pattern_rating_label = QLabel("")
        stats_layout.addWidget(self.pattern_rating_label)
        
        self.pattern_downloads_label = QLabel("")
        stats_layout.addWidget(self.pattern_downloads_label)
        
        stats_layout.addStretch()
        details_layout.addLayout(stats_layout)
        
        # Tags
        self.pattern_tags_label = QLabel("")
        details_layout.addWidget(self.pattern_tags_label)
        
        # Rating
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("Rate this pattern:"))
        
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["1", "2", "3", "4", "5"])
        self.rating_combo.setCurrentText("5")
        rating_layout.addWidget(self.rating_combo)
        
        rate_btn = QPushButton("Rate")
        rate_btn.clicked.connect(self._on_rate)
        rating_layout.addWidget(rate_btn)
        
        rating_layout.addStretch()
        details_layout.addLayout(rating_layout)
        
        # Download button
        download_btn = QPushButton("Download Pattern")
        download_btn.clicked.connect(self._on_download)
        download_btn.setEnabled(False)
        details_layout.addWidget(download_btn)
        self.download_btn = download_btn
        
        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group, 1)
        
        layout.addLayout(content_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        upload_btn = QPushButton("Upload Pattern...")
        upload_btn.clicked.connect(self._on_upload)
        button_layout.addWidget(upload_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Initial load
        self._refresh_list()
    
    def _refresh_list(self):
        """Refresh pattern list."""
        self.pattern_list.clear()
        patterns = self.sharing_service.search_patterns()
        self._populate_list(patterns)
    
    def _show_popular(self):
        """Show popular patterns."""
        self.pattern_list.clear()
        patterns = self.sharing_service.get_popular_patterns(20)
        self._populate_list(patterns)
    
    def _show_recent(self):
        """Show recent patterns."""
        self.pattern_list.clear()
        patterns = self.sharing_service.get_recent_patterns(20)
        self._populate_list(patterns)
    
    def _populate_list(self, patterns: List[SharedPattern]):
        """Populate pattern list widget."""
        for pattern in patterns:
            item = QListWidgetItem(f"{pattern.name} by {pattern.author}")
            item.setData(Qt.UserRole, pattern.pattern_id)
            
            # Add rating info
            if pattern.rating > 0:
                item.setText(f"{pattern.name} ⭐ {pattern.rating:.1f} ({pattern.rating_count})")
            
            self.pattern_list.addItem(item)
    
    def _on_search(self):
        """Perform search."""
        query = self.search_input.text() if self.search_input.text() else None
        category = self.category_combo.currentText() if self.category_combo.currentText() != "All" else None
        min_rating = self.rating_spin.value()
        
        patterns = self.sharing_service.search_patterns(
            query=query,
            category=category,
            min_rating=min_rating
        )
        
        self.pattern_list.clear()
        self._populate_list(patterns)
    
    def _on_pattern_selected(self, item: QListWidgetItem):
        """Handle pattern selection."""
        pattern_id = item.data(Qt.UserRole)
        pattern = self.sharing_service.download_pattern(pattern_id)  # This increments downloads
        
        if pattern:
            self.selected_pattern = pattern
            self._update_details(pattern)
            self.download_btn.setEnabled(True)
    
    def _update_details(self, pattern: SharedPattern):
        """Update pattern details display."""
        self.pattern_name_label.setText(pattern.name)
        self.pattern_author_label.setText(f"By: {pattern.author}")
        self.pattern_description.setText(pattern.description)
        
        # Stats
        rating_text = f"⭐ {pattern.rating:.1f} ({pattern.rating_count} ratings)" if pattern.rating > 0 else "No ratings yet"
        self.pattern_rating_label.setText(rating_text)
        self.pattern_downloads_label.setText(f"📥 {pattern.downloads} downloads")
        
        # Tags
        if pattern.tags:
            tags_text = "Tags: " + ", ".join(pattern.tags)
            self.pattern_tags_label.setText(tags_text)
        else:
            self.pattern_tags_label.setText("")
    
    def _on_rate(self):
        """Rate selected pattern."""
        if not self.selected_pattern:
            QMessageBox.warning(self, "No Pattern", "Please select a pattern to rate")
            return
        
        rating = float(self.rating_combo.currentText())
        if self.sharing_service.rate_pattern(self.selected_pattern.pattern_id, rating):
            QMessageBox.information(self, "Rated", f"Thank you for rating this pattern!")
            # Refresh details
            pattern = self.sharing_service.download_pattern(self.selected_pattern.pattern_id)
            if pattern:
                self._update_details(pattern)
        else:
            QMessageBox.warning(self, "Error", "Failed to rate pattern")
    
    def _on_download(self):
        """Download selected pattern."""
        if not self.selected_pattern:
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Pattern",
            f"{self.selected_pattern.name}.ledproj",
            "LED Project Files (*.ledproj);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # Convert pattern data to Pattern object and save
                # This is simplified - would need actual pattern loading from bytes
                from core.pattern import Pattern, PatternMetadata, Frame
                from datetime import datetime
                
                # Create pattern from data (simplified)
                metadata = PatternMetadata(
                    width=12,  # Would parse from data
                    height=6,
                    name=self.selected_pattern.name
                )
                
                pattern = Pattern(
                    name=self.selected_pattern.name,
                    metadata=metadata,
                    frames=[]  # Would load from data
                )
                
                save_project(pattern, file_path)
                
                QMessageBox.information(
                    self,
                    "Downloaded",
                    f"Pattern '{self.selected_pattern.name}' saved successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save pattern: {e}")
    
    def _on_upload(self):
        """Upload a pattern."""
        from PySide6.QtWidgets import QInputDialog, QFileDialog
        from core.project import load_project
        
        # Select pattern file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Pattern to Upload",
            "",
            "LED Project Files (*.ledproj);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            pattern = load_project(file_path)
            
            # Get author name
            author, ok = QInputDialog.getText(
                self,
                "Author Name",
                "Enter your name:"
            )
            
            if not ok or not author:
                return
            
            # Get description
            description, ok = QInputDialog.getMultiLineText(
                self,
                "Pattern Description",
                "Enter pattern description:"
            )
            
            if not ok:
                description = ""
            
            # Get category
            category, ok = QInputDialog.getItem(
                self,
                "Category",
                "Select category:",
                ["Vesak", "Buddhist", "Festival", "Custom"],
                0,
                False
            )
            
            if not ok:
                return
            
            # Export pattern to bytes
            from core.export.exporters import PatternExporter
            from pathlib import Path
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
                temp_path = Path(f.name)
            
            exporter = PatternExporter()
            exporter.export_binary(pattern, temp_path)
            pattern_data = temp_path.read_bytes()
            temp_path.unlink()
            
            # Upload
            pattern_id = self.sharing_service.upload_pattern(
                pattern_data=pattern_data,
                name=pattern.name or "Unnamed Pattern",
                author=author,
                description=description,
                category=category
            )
            
            QMessageBox.information(
                self,
                "Uploaded",
                f"Pattern uploaded successfully!\nPattern ID: {pattern_id}"
            )
            
            self._refresh_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload pattern: {e}")

