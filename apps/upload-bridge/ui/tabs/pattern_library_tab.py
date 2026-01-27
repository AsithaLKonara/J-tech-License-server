"""
Pattern Library Tab - Browse and manage local pattern library
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, QGroupBox,
    QScrollArea, QTextEdit, QMessageBox, QFileDialog, QDialog,
    QDialogButtonBox, QFormLayout, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QPixmap, QImage, QFont
import sys
import os
from pathlib import Path
from typing import List, Tuple
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern, load_pattern_from_file
from core.pattern_library import PatternLibrary, PatternEntry
import logging

logger = logging.getLogger(__name__)


class PatternLibraryTab(QWidget):
    """
    Pattern Library Tab for browsing and managing patterns
    
    Features:
    - Pattern browser with thumbnails
    - Search and filtering
    - Category and tag management
    - Pattern details
    - Add/remove patterns
    """
    
    # Signals
    pattern_selected = Signal(Pattern, str)  # pattern, file_path
    pattern_added = Signal(Pattern)  # pattern
    pattern_removed = Signal(str)  # pattern_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.library = PatternLibrary()
        self.current_pattern: Pattern = None
        
        self.setup_ui()
        self.refresh_library()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Search and filters
        search_group = QGroupBox("Search & Filters")
        search_layout = QVBoxLayout()
        
        # Search bar
        search_bar_layout = QHBoxLayout()
        search_bar_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search patterns by name or description...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_bar_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("🔍 Search")
        self.search_button.clicked.connect(self.perform_search)
        search_bar_layout.addWidget(self.search_button)
        
        search_layout.addLayout(search_bar_layout)
        
        # Filters
        filters_layout = QHBoxLayout()
        
        # Category filter
        filters_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self.on_filter_changed)
        filters_layout.addWidget(self.category_combo)
        
        # Tag filter
        filters_layout.addWidget(QLabel("Tag:"))
        self.tag_combo = QComboBox()
        self.tag_combo.addItem("All Tags")
        self.tag_combo.currentTextChanged.connect(self.on_filter_changed)
        filters_layout.addWidget(self.tag_combo)
        
        # LED count filter
        filters_layout.addWidget(QLabel("LEDs:"))
        self.min_leds_spin = QSpinBox()
        self.min_leds_spin.setMinimum(0)
        self.min_leds_spin.setMaximum(10000)
        self.min_leds_spin.setValue(0)
        self.min_leds_spin.setPrefix("Min: ")
        self.min_leds_spin.valueChanged.connect(self.on_filter_changed)
        filters_layout.addWidget(self.min_leds_spin)
        
        self.max_leds_spin = QSpinBox()
        self.max_leds_spin.setMinimum(0)
        self.max_leds_spin.setMaximum(10000)
        self.max_leds_spin.setValue(10000)
        self.max_leds_spin.setPrefix("Max: ")
        self.max_leds_spin.valueChanged.connect(self.on_filter_changed)
        filters_layout.addWidget(self.max_leds_spin)
        
        filters_layout.addStretch()
        
        search_layout.addLayout(filters_layout)
        
        search_group.setLayout(search_layout)
        content_layout.addWidget(search_group)
        
        # Pattern list
        list_group = QGroupBox("Patterns")
        list_layout = QVBoxLayout()
        
        # List widget
        self.pattern_list = QListWidget()
        self.pattern_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.pattern_list.setIconSize(QSize(128, 128))
        self.pattern_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.pattern_list.itemDoubleClicked.connect(self.on_pattern_double_clicked)
        self.pattern_list.itemSelectionChanged.connect(self.on_pattern_selected)
        list_layout.addWidget(self.pattern_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("➕ Add Pattern...")
        self.add_button.clicked.connect(self.add_pattern)
        buttons_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("➖ Remove")
        self.remove_button.clicked.connect(self.remove_pattern)
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.remove_button)
        
        self.edit_button = QPushButton("✏️ Edit Metadata...")
        self.edit_button.clicked.connect(self.edit_pattern_metadata)
        self.edit_button.setEnabled(False)
        buttons_layout.addWidget(self.edit_button)
        
        self.load_button = QPushButton("📂 Load Pattern")
        self.load_button.clicked.connect(self.load_selected_pattern)
        self.load_button.setEnabled(False)
        buttons_layout.addWidget(self.load_button)
        
        buttons_layout.addStretch()
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_library)
        buttons_layout.addWidget(self.refresh_button)
        
        list_layout.addLayout(buttons_layout)
        
        list_group.setLayout(list_layout)
        content_layout.addWidget(list_group, stretch=1)
        
        # Pattern details
        details_group = QGroupBox("Pattern Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def refresh_library(self):
        """Refresh pattern library display"""
        # Update category and tag combos
        categories = self.library.get_categories()
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        for cat in categories:
            self.category_combo.addItem(cat)
        
        tags = self.library.get_tags()
        self.tag_combo.clear()
        self.tag_combo.addItem("All Tags")
        for tag in tags:
            self.tag_combo.addItem(tag)
        
        # Perform search to refresh list
        self.perform_search()
    
    def perform_search(self):
        """Perform search with current filters"""
        query = self.search_input.text().strip() or None
        
        category = None
        if self.category_combo.currentIndex() > 0:
            category = self.category_combo.currentText()
        
        tags = None
        if self.tag_combo.currentIndex() > 0:
            tags = [self.tag_combo.currentText()]
        
        min_leds = self.min_leds_spin.value() if self.min_leds_spin.value() > 0 else None
        max_leds = self.max_leds_spin.value() if self.max_leds_spin.value() < 10000 else None
        
        entries = self.library.search_patterns(
            query=query,
            category=category,
            tags=tags,
            min_leds=min_leds,
            max_leds=max_leds
        )
        
        self.populate_pattern_list(entries)
    
    def on_search_changed(self):
        """Handle search input change (debounced search)"""
        # Could add debouncing here if needed
        pass
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.perform_search()
    
    def populate_pattern_list(self, entries: List[PatternEntry]):
        """Populate pattern list with entries"""
        self.pattern_list.clear()
        
        for entry in entries:
            item = QListWidgetItem(entry.name)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            
            # Try to load thumbnail
            if entry.thumbnail_path and Path(entry.thumbnail_path).exists():
                pixmap = QPixmap(entry.thumbnail_path)
                if not pixmap.isNull():
                    item.setIcon(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio))
            
            # Add metadata as tooltip
            tooltip = f"{entry.name}\n"
            tooltip += f"LEDs: {entry.led_count} ({entry.width}×{entry.height})\n"
            tooltip += f"Frames: {entry.frame_count}\n"
            tooltip += f"Category: {entry.category}\n"
            if entry.tags:
                tooltip += f"Tags: {', '.join(entry.tags)}"
            item.setToolTip(tooltip)
            
            self.pattern_list.addItem(item)
    
    def on_pattern_selected(self):
        """Handle pattern selection"""
        selected_items = self.pattern_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.remove_button.setEnabled(has_selection)
        self.edit_button.setEnabled(has_selection)
        self.load_button.setEnabled(has_selection)
        
        if has_selection:
            item = selected_items[0]
            entry: PatternEntry = item.data(Qt.ItemDataRole.UserRole)
            self.show_pattern_details(entry)
        else:
            self.details_text.clear()
    
    def on_pattern_double_clicked(self, item: QListWidgetItem):
        """Handle pattern double-click (load pattern)"""
        self.load_selected_pattern()
    
    def show_pattern_details(self, entry: PatternEntry):
        """Show pattern details"""
        details = f"<b>{entry.name}</b><br><br>"
        details += f"<b>File:</b> {Path(entry.file_path).name}<br>"
        details += f"<b>Dimensions:</b> {entry.width}×{entry.height}<br>"
        details += f"<b>LEDs:</b> {entry.led_count}<br>"
        details += f"<b>Frames:</b> {entry.frame_count}<br>"
        details += f"<b>Duration:</b> {entry.duration_ms / 1000:.1f}s<br>"
        details += f"<b>Category:</b> {entry.category}<br>"
        if entry.tags:
            details += f"<b>Tags:</b> {', '.join(entry.tags)}<br>"
        if entry.description:
            details += f"<b>Description:</b> {entry.description}<br>"
        if entry.author:
            details += f"<b>Author:</b> {entry.author}<br>"
        details += f"<b>Access Count:</b> {entry.access_count}<br>"
        details += f"<b>Last Accessed:</b> {entry.last_accessed}<br>"
        
        self.details_text.setHtml(details)
    
    def add_pattern(self):
        """Add pattern to library"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Add Pattern to Library",
            "",
            "Pattern Files (*.bin *.hex *.dat *.leds *.json *.ledproj);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Load pattern
            pattern = load_pattern_from_file(file_path)
            
            # Show metadata dialog
            dialog = PatternMetadataDialog(self, pattern, file_path)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                category, tags, description, author = dialog.get_metadata()
                
                # Add to library
                pattern_id = self.library.add_pattern(
                    pattern,
                    file_path,
                    category=category,
                    tags=tags,
                    description=description,
                    author=author
                )
                
                # Generate thumbnail
                thumbnail_dir = Path.home() / ".upload_bridge" / "thumbnails"
                thumbnail_dir.mkdir(exist_ok=True)
                thumbnail_path = thumbnail_dir / f"{pattern_id}.png"
                self.library.generate_thumbnail(pattern, str(thumbnail_path))
                
                # Update thumbnail path
                self.library.update_pattern(pattern_id, thumbnail_path=str(thumbnail_path))
                
                QMessageBox.information(
                    self,
                    "Pattern Added",
                    f"Pattern '{pattern.name}' added to library!"
                )
                
                # Emit pattern added signal
                self.pattern_added.emit(pattern)
                
                self.refresh_library()
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Add Pattern Failed",
                f"Failed to add pattern:\n\n{str(e)}"
            )
            logger.error(f"Failed to add pattern: {e}", exc_info=True)
    
    def add_pattern_programmatic(self, pattern: Pattern, file_path: str = None, 
                                 category: str = "Uncategorized", tags: List[str] = None,
                                 description: str = "", author: str = ""):
        """Add pattern to library programmatically (without file dialog)"""
        try:
            if tags is None:
                tags = []
            
            # If no file path provided, save to managed library directory
            if not file_path:
                import uuid
                library_dir = Path.home() / ".upload_bridge" / "patterns"
                library_dir.mkdir(parents=True, exist_ok=True)
                
                # Create a safe filename
                safe_name = "".join(c for c in pattern.name if c.isalnum() or c in (' ', '-', '_')).strip()
                if not safe_name:
                    safe_name = "pattern"
                    
                # Use UUID to avoid collisions
                filename = f"{safe_name}_{uuid.uuid4().hex[:8]}.ledproj"
                file_path = str(library_dir / filename)
                
                # Save pattern to this managed path
                pattern.save_to_file(file_path)
                logger.info(f"Saved generated pattern to library: {file_path}")
            
            # Add to library
            pattern_id = self.library.add_pattern(
                pattern,
                file_path,
                category=category,
                tags=tags,
                description=description,
                author=author
            )
            
            # Generate thumbnail
            thumbnail_dir = Path.home() / ".upload_bridge" / "thumbnails"
            thumbnail_dir.mkdir(exist_ok=True)
            thumbnail_path = thumbnail_dir / f"{pattern_id}.png"
            self.library.generate_thumbnail(pattern, str(thumbnail_path))
            
            # Update thumbnail path
            self.library.update_pattern(pattern_id, thumbnail_path=str(thumbnail_path))
            
            # Emit pattern added signal
            self.pattern_added.emit(pattern)
            
            self.refresh_library()
            
            return pattern_id
        
        except Exception as e:
            logger.error(f"Failed to add pattern programmatically: {e}", exc_info=True)
            raise
    
    def remove_pattern(self):
        """Remove selected pattern from library"""
        selected_items = self.pattern_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        entry: PatternEntry = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Remove Pattern",
            f"Remove '{entry.name}' from library?\n\n"
            "The pattern file will not be deleted, only removed from the library.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            pattern_id = entry.id
            self.library.remove_pattern(pattern_id)
            # Emit pattern removed signal
            self.pattern_removed.emit(pattern_id)
            self.refresh_library()
    
    def edit_pattern_metadata(self):
        """Edit pattern metadata"""
        selected_items = self.pattern_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        entry: PatternEntry = item.data(Qt.ItemDataRole.UserRole)
        
        # Load pattern
        try:
            if not entry.file_path or not os.path.exists(entry.file_path):
                 QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"The pattern file could not be found:\n{entry.file_path}"
                )
                 return

            pattern = load_pattern_from_file(entry.file_path)
            
            dialog = PatternMetadataDialog(self, pattern, entry.file_path, entry)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                category, tags, description, author = dialog.get_metadata()
                
                self.library.update_pattern(
                    entry.id,
                    pattern=pattern,
                    category=category,
                    tags=tags,
                    description=description,
                    author=author
                )
                
                QMessageBox.information(
                    self,
                    "Metadata Updated",
                    "Pattern metadata updated!"
                )
                
                self.refresh_library()
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Edit Failed",
                f"Failed to edit pattern:\n\n{str(e)}"
            )
    
    def load_selected_pattern(self):
        """Load selected pattern"""
        selected_items = self.pattern_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        entry: PatternEntry = item.data(Qt.ItemDataRole.UserRole)
        
        try:
            if not entry.file_path or not os.path.exists(entry.file_path):
                 QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"The pattern file could not be found:\n{entry.file_path}"
                )
                 return

            # Load pattern
            pattern = load_pattern_from_file(entry.file_path)
            
            # Record access
            self.library.record_access(entry.id)
            
            # Emit signal
            self.pattern_selected.emit(pattern, entry.file_path)
            
            QMessageBox.information(
                self,
                "Pattern Loaded",
                f"Pattern '{pattern.name}' loaded!"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Failed",
                f"Failed to load pattern:\n\n{str(e)}"
            )


class PatternMetadataDialog(QDialog):
    """Dialog for editing pattern metadata"""
    
    def __init__(self, parent, pattern: Pattern, file_path: str, entry: PatternEntry = None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Metadata")
        self.setMinimumWidth(400)
        
        self.pattern = pattern
        self.file_path = file_path
        self.entry = entry
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Category
        self.category_input = QLineEdit()
        if self.entry:
            self.category_input.setText(self.entry.category)
        else:
            self.category_input.setText("Uncategorized")
        form.addRow("Category:", self.category_input)
        
        # Tags
        self.tags_input = QLineEdit()
        if self.entry:
            self.tags_input.setText(", ".join(self.entry.tags))
        self.tags_input.setPlaceholderText("tag1, tag2, tag3")
        form.addRow("Tags (comma-separated):", self.tags_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if self.entry and self.entry.description:
            self.description_input.setPlainText(self.entry.description)
        form.addRow("Description:", self.description_input)
        
        # Author
        self.author_input = QLineEdit()
        if self.entry and self.entry.author:
            self.author_input.setText(self.entry.author)
        form.addRow("Author:", self.author_input)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_metadata(self) -> Tuple[str, List[str], str, str]:
        """Get metadata from dialog"""
        category = self.category_input.text().strip() or "Uncategorized"
        tags_str = self.tags_input.text().strip()
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        description = self.description_input.toPlainText().strip() or None
        author = self.author_input.text().strip() or None
        
        return category, tags, description, author

