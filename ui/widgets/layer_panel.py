"""
Layer Panel Widget - UI for managing layers in LED matrix patterns.

This widget provides a visual interface for managing multiple layers
per frame, including visibility, opacity, ordering, and editing.
"""

from __future__ import annotations
from typing import Optional, Dict
from PySide6.QtCore import Qt, Signal, QSize, QMimeData
from PySide6.QtGui import QPixmap, QPainter, QColor, QDrag, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QLabel,
    QLineEdit,
    QCheckBox,
    QGroupBox,
    QMessageBox,
    QMenu,
)
from domain.layers import LayerManager, Layer


class LayerPanelWidget(QWidget):
    """Widget for managing layers in a frame."""
    
    layer_selected = Signal(int)  # layer_index
    active_layer_changed = Signal(int)  # layer_index
    solo_mode_changed = Signal(bool)  # solo_mode enabled/disabled

    def __init__(self, layer_manager: LayerManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.layer_manager = layer_manager
        self._current_frame_index = 0
        self._active_layer_index = 0
        self._updating = False
        self._solo_mode = False  # Show only active layer
        self._layer_thumbnails: Dict[int, QPixmap] = {}  # Cache for layer thumbnails
        
        self._setup_ui()
        self._connect_signals()
        self._setup_keyboard_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Layer list
        list_group = QGroupBox("Layers")
        list_layout = QVBoxLayout()
        
        self.layer_list = QListWidget()
        self.layer_list.setMaximumHeight(200)
        self.layer_list.setDragDropMode(QListWidget.InternalMove)  # Enable drag-and-drop
        self.layer_list.setDefaultDropAction(Qt.MoveAction)
        self.layer_list.itemSelectionChanged.connect(self._on_layer_selected)
        self.layer_list.itemDoubleClicked.connect(self._on_layer_double_clicked)
        self.layer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self._on_context_menu)
        # Handle drag-and-drop completion
        self.layer_list.model().rowsMoved.connect(self._on_layers_reordered)
        list_layout.addWidget(self.layer_list)
        
        # Layer controls
        controls_layout = QHBoxLayout()
        self.add_layer_btn = QPushButton("+ Add")
        self.add_layer_btn.clicked.connect(self._on_add_layer)
        controls_layout.addWidget(self.add_layer_btn)
        
        self.delete_layer_btn = QPushButton("- Delete")
        self.delete_layer_btn.clicked.connect(self._on_delete_layer)
        controls_layout.addWidget(self.delete_layer_btn)
        
        self.duplicate_layer_btn = QPushButton("Duplicate")
        self.duplicate_layer_btn.clicked.connect(self._on_duplicate_layer)
        controls_layout.addWidget(self.duplicate_layer_btn)
        
        controls_layout.addStretch()
        list_layout.addLayout(controls_layout)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Layer properties
        props_group = QGroupBox("Layer Properties")
        props_layout = QVBoxLayout()
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.layer_name_edit = QLineEdit()
        self.layer_name_edit.editingFinished.connect(self._on_name_changed)
        name_layout.addWidget(self.layer_name_edit)
        props_layout.addLayout(name_layout)
        
        # Visibility
        visibility_layout = QHBoxLayout()
        self.layer_visible_checkbox = QCheckBox("Visible")
        self.layer_visible_checkbox.toggled.connect(self._on_visibility_changed)
        visibility_layout.addWidget(self.layer_visible_checkbox)
        
        # Solo mode toggle
        self.solo_mode_checkbox = QCheckBox("Solo Mode (Show Only Active Layer)")
        self.solo_mode_checkbox.setToolTip("When enabled, only the active layer is visible. Other layers are temporarily hidden.")
        self.solo_mode_checkbox.toggled.connect(self._on_solo_mode_changed)
        visibility_layout.addWidget(self.solo_mode_checkbox)
        visibility_layout.addStretch()
        props_layout.addLayout(visibility_layout)
        
        # Opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.layer_opacity_slider = QSlider(Qt.Horizontal)
        self.layer_opacity_slider.setRange(0, 100)
        self.layer_opacity_slider.setValue(100)
        self.layer_opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.layer_opacity_slider)
        self.layer_opacity_label = QLabel("100%")
        self.layer_opacity_label.setMinimumWidth(40)
        opacity_layout.addWidget(self.layer_opacity_label)
        props_layout.addLayout(opacity_layout)
        
        # Move buttons
        move_layout = QHBoxLayout()
        self.move_up_btn = QPushButton("↑ Move Up")
        self.move_up_btn.clicked.connect(self._on_move_up)
        move_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓ Move Down")
        self.move_down_btn.clicked.connect(self._on_move_down)
        move_layout.addWidget(self.move_down_btn)
        move_layout.addStretch()
        props_layout.addLayout(move_layout)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        layout.addStretch()

    def _connect_signals(self):
        """Connect to layer manager signals."""
        self.layer_manager.layers_changed.connect(self._on_layers_changed)
        self.layer_manager.layer_added.connect(self._on_layer_added)
        self.layer_manager.layer_removed.connect(self._on_layer_removed)

    def set_frame_index(self, frame_index: int):
        """Set the current frame index."""
        self._current_frame_index = frame_index
        self._refresh_layer_list()

    def set_active_layer(self, layer_index: int):
        """Set the active layer for editing."""
        self._active_layer_index = layer_index
        if layer_index < self.layer_list.count():
            self.layer_list.setCurrentRow(layer_index)
        self._update_properties()

    def get_active_layer_index(self) -> int:
        """Get the currently active layer index."""
        return self._active_layer_index

    def _refresh_layer_list(self):
        """Refresh the layer list display."""
        self._updating = True
        self.layer_list.clear()
        
        layers = self.layer_manager.get_layers(self._current_frame_index)
        width = self.layer_manager._state.width()
        height = self.layer_manager._state.height()
        
        for idx, layer in enumerate(layers):
            # Create item with thumbnail
            item = QListWidgetItem()
            
            # Generate or get cached thumbnail
            thumbnail = self._get_layer_thumbnail(idx, layer, width, height)
            if thumbnail:
                item.setIcon(QIcon(thumbnail))
            
            # Build item text
            item_text = f"{layer.name}"
            if not layer.visible:
                item_text += " (hidden)"
            if layer.opacity < 1.0:
                item_text += f" [{int(layer.opacity * 100)}%]"
            
            item.setText(item_text)
            item.setData(Qt.UserRole, idx)
            
            # Highlight active layer
            if idx == self._active_layer_index:
                item.setBackground(QColor(76, 139, 245, 80))  # Blue highlight
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            # Show warning if layer is hidden
            if not layer.visible and idx == self._active_layer_index:
                item.setForeground(QColor(255, 165, 0))  # Orange warning color
            
            self.layer_list.addItem(item)
        
        # Select active layer
        if self._active_layer_index < len(layers):
            self.layer_list.setCurrentRow(self._active_layer_index)
        
        self._updating = False
        self._update_properties()
    
    def _get_layer_thumbnail(self, layer_index: int, layer: Layer, width: int, height: int) -> Optional[QPixmap]:
        """Generate a small thumbnail preview of the layer."""
        if width == 0 or height == 0:
            return None
        
        # Check cache first
        cache_key = (self._current_frame_index, layer_index)
        if cache_key in self._layer_thumbnails:
            return self._layer_thumbnails[cache_key]
        
        # Generate thumbnail (32x32 pixels)
        thumb_size = 32
        thumbnail = QPixmap(thumb_size, thumb_size)
        thumbnail.fill(QColor(0, 0, 0))
        
        painter = QPainter(thumbnail)
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        # Scale factor
        scale_x = thumb_size / width
        scale_y = thumb_size / height
        
        # Draw layer pixels
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if idx < len(layer.pixels):
                    r, g, b = layer.pixels[idx]
                    color = QColor(r, g, b)
                    
                    # Scale pixel position
                    px = int(x * scale_x)
                    py = int(y * scale_y)
                    pw = max(1, int(scale_x))
                    ph = max(1, int(scale_y))
                    
                    painter.fillRect(px, py, pw, ph, color)
        
        painter.end()
        
        # Cache thumbnail
        self._layer_thumbnails[cache_key] = thumbnail
        return thumbnail

    def _update_properties(self):
        """Update property controls for selected layer."""
        self._updating = True
        
        layers = self.layer_manager.get_layers(self._current_frame_index)
        if self._active_layer_index < len(layers):
            layer = layers[self._active_layer_index]
            self.layer_name_edit.setText(layer.name)
            self.layer_visible_checkbox.setChecked(layer.visible)
            self.layer_opacity_slider.setValue(int(layer.opacity * 100))
            self.layer_opacity_label.setText(f"{int(layer.opacity * 100)}%")
            
            # Enable controls
            self.layer_name_edit.setEnabled(True)
            self.layer_visible_checkbox.setEnabled(True)
            self.layer_opacity_slider.setEnabled(True)
            self.delete_layer_btn.setEnabled(len(layers) > 1)
            self.move_up_btn.setEnabled(self._active_layer_index > 0)
            self.move_down_btn.setEnabled(self._active_layer_index < len(layers) - 1)
        else:
            # Disable controls
            self.layer_name_edit.setEnabled(False)
            self.layer_visible_checkbox.setEnabled(False)
            self.layer_opacity_slider.setEnabled(False)
            self.delete_layer_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
        
        self._updating = False

    def _on_layer_selected(self):
        """Handle layer selection."""
        if self._updating:
            return
        
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_index = current_item.data(Qt.UserRole)
            self._active_layer_index = layer_index
            self._update_properties()
            self.active_layer_changed.emit(layer_index)

    def _on_layer_double_clicked(self, item: QListWidgetItem):
        """Handle layer double-click (rename)."""
        self.layer_name_edit.setFocus()
        self.layer_name_edit.selectAll()

    def _on_add_layer(self):
        """Add a new layer."""
        self.layer_manager.add_layer(self._current_frame_index)
        self._refresh_layer_list()
        # Select the new layer
        layers = self.layer_manager.get_layers(self._current_frame_index)
        self.set_active_layer(len(layers) - 1)

    def _on_delete_layer(self):
        """Delete the selected layer."""
        layers = self.layer_manager.get_layers(self._current_frame_index)
        if len(layers) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "At least one layer is required.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Layer",
            f"Delete layer '{layers[self._active_layer_index].name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.layer_manager.remove_layer(self._current_frame_index, self._active_layer_index)
            # Adjust active layer index
            if self._active_layer_index >= len(layers) - 1:
                self._active_layer_index = len(layers) - 2
            self._refresh_layer_list()

    def _on_duplicate_layer(self):
        """Duplicate the selected layer."""
        layers = self.layer_manager.get_layers(self._current_frame_index)
        if self._active_layer_index < len(layers):
            source_layer = layers[self._active_layer_index]
            new_index = self.layer_manager.add_layer(
                self._current_frame_index,
                name=f"{source_layer.name} Copy"
            )
            # Copy pixels
            new_layer = layers[new_index]
            new_layer.pixels = list(source_layer.pixels)
            new_layer.opacity = source_layer.opacity
            new_layer.visible = source_layer.visible
            self._refresh_layer_list()
            self.set_active_layer(new_index)

    def _on_name_changed(self):
        """Handle layer name change."""
        if self._updating:
            return
        
        name = self.layer_name_edit.text().strip()
        if name:
            self.layer_manager.set_layer_name(self._current_frame_index, self._active_layer_index, name)
            self._refresh_layer_list()

    def _on_visibility_changed(self, checked: bool):
        """Handle visibility toggle."""
        if self._updating:
            return
        
        self.layer_manager.set_layer_visible(self._current_frame_index, self._active_layer_index, checked)
        self._refresh_layer_list()

    def _on_opacity_changed(self, value: int):
        """Handle opacity change."""
        if self._updating:
            return
        
        opacity = value / 100.0
        self.layer_opacity_label.setText(f"{value}%")
        self.layer_manager.set_layer_opacity(self._current_frame_index, self._active_layer_index, opacity)

    def _on_move_up(self):
        """Move layer up."""
        if self._active_layer_index > 0:
            self.layer_manager.move_layer(self._current_frame_index, self._active_layer_index, self._active_layer_index - 1)
            self._active_layer_index -= 1
            self._refresh_layer_list()

    def _on_move_down(self):
        """Move layer down."""
        layers = self.layer_manager.get_layers(self._current_frame_index)
        if self._active_layer_index < len(layers) - 1:
            self.layer_manager.move_layer(self._current_frame_index, self._active_layer_index, self._active_layer_index + 1)
            self._active_layer_index += 1
            self._refresh_layer_list()

    def _on_layers_changed(self, frame_index: int):
        """Handle layers changed signal."""
        if frame_index == self._current_frame_index or frame_index == -1:
            self._refresh_layer_list()

    def _on_layer_added(self, frame_index: int, layer_index: int):
        """Handle layer added signal."""
        if frame_index == self._current_frame_index:
            self._refresh_layer_list()

    def _on_layer_removed(self, frame_index: int, layer_index: int):
        """Handle layer removed signal."""
        if frame_index == self._current_frame_index:
            if self._active_layer_index >= layer_index:
                self._active_layer_index = max(0, self._active_layer_index - 1)
            # Clear thumbnail cache for removed layer
            cache_key = (frame_index, layer_index)
            if cache_key in self._layer_thumbnails:
                del self._layer_thumbnails[cache_key]
            self._refresh_layer_list()
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for layer operations."""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # F2: Rename layer
        rename_shortcut = QShortcut(QKeySequence("F2"), self)
        rename_shortcut.activated.connect(self._on_rename_shortcut)
        
        # Ctrl+D: Duplicate layer
        duplicate_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        duplicate_shortcut.activated.connect(self._on_duplicate_shortcut)
        
        # Delete: Delete layer (with confirmation)
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._on_delete_shortcut)
    
    def _on_rename_shortcut(self):
        """Handle F2 shortcut for renaming."""
        if self.layer_name_edit.isEnabled():
            self.layer_name_edit.setFocus()
            self.layer_name_edit.selectAll()
    
    def _on_duplicate_shortcut(self):
        """Handle Ctrl+D shortcut for duplicating."""
        if self.duplicate_layer_btn.isEnabled():
            self._on_duplicate_layer()
    
    def _on_delete_shortcut(self):
        """Handle Delete shortcut for deleting."""
        if self.delete_layer_btn.isEnabled():
            self._on_delete_layer()
    
    def _on_context_menu(self, position):
        """Show context menu for layer operations."""
        item = self.layer_list.itemAt(position)
        if not item:
            return
        
        layer_index = item.data(Qt.UserRole)
        layers = self.layer_manager.get_layers(self._current_frame_index)
        if layer_index >= len(layers):
            return
        
        menu = QMenu(self)
        
        # Rename
        rename_action = menu.addAction("Rename (F2)")
        rename_action.triggered.connect(lambda: self._on_rename_shortcut())
        
        menu.addSeparator()
        
        # Duplicate
        duplicate_action = menu.addAction("Duplicate (Ctrl+D)")
        duplicate_action.triggered.connect(self._on_duplicate_layer)
        
        menu.addSeparator()
        
        # Move up
        move_up_action = menu.addAction("Move Up")
        move_up_action.setEnabled(layer_index > 0)
        move_up_action.triggered.connect(self._on_move_up)
        
        # Move down
        move_down_action = menu.addAction("Move Down")
        move_down_action.setEnabled(layer_index < len(layers) - 1)
        move_down_action.triggered.connect(self._on_move_down)
        
        menu.addSeparator()
        
        # Delete
        delete_action = menu.addAction("Delete (Del)")
        delete_action.setEnabled(len(layers) > 1)
        delete_action.triggered.connect(self._on_delete_layer)
        
        menu.exec_(self.layer_list.mapToGlobal(position))
    
    def _on_solo_mode_changed(self, enabled: bool):
        """Handle solo mode toggle."""
        self._solo_mode = enabled
        self.solo_mode_changed.emit(enabled)
        
        if enabled:
            # Temporarily hide all layers except active
            layers = self.layer_manager.get_layers(self._current_frame_index)
            for idx, layer in enumerate(layers):
                if idx != self._active_layer_index:
                    # Store original visibility
                    if not hasattr(layer, '_original_visible'):
                        layer._original_visible = layer.visible
                    self.layer_manager.set_layer_visible(self._current_frame_index, idx, False)
        else:
            # Restore original visibility
            layers = self.layer_manager.get_layers(self._current_frame_index)
            for idx, layer in enumerate(layers):
                if hasattr(layer, '_original_visible'):
                    self.layer_manager.set_layer_visible(self._current_frame_index, idx, layer._original_visible)
                    delattr(layer, '_original_visible')
    
    def is_solo_mode(self) -> bool:
        """Check if solo mode is enabled."""
        return self._solo_mode
    
    def clear_thumbnail_cache(self):
        """Clear the thumbnail cache (call when layer pixels change)."""
        self._layer_thumbnails.clear()
    
    def _on_layers_reordered(self, parent, start, end, destination, row):
        """Handle layer reordering via drag-and-drop."""
        if self._updating:
            return
        
        self._updating = True
        
        # Get the new order from the list widget
        new_order = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item:
                layer_index = item.data(Qt.UserRole)
                new_order.append(layer_index)
        
        # Apply reordering to layer manager
        layers = self.layer_manager.get_layers(self._current_frame_index)
        if len(new_order) != len(layers):
            # Something went wrong, refresh
            self._updating = False
            self._refresh_layer_list()
            return
        
        # Reorder layers in the manager using move_layer calls
        # We need to move layers one by one to maintain proper order
        current_layers = list(layers)
        reordered_layers = [current_layers[i] for i in new_order]
        
        # Update the layer manager's internal list
        self.layer_manager._layers[self._current_frame_index] = reordered_layers
        
        # Find new position of active layer
        old_active_idx = self._active_layer_index
        if old_active_idx in new_order:
            self._active_layer_index = new_order.index(old_active_idx)
        else:
            self._active_layer_index = 0
        
        self._updating = False
        
        # Emit signal to update UI
        self.layer_manager.layers_changed.emit(self._current_frame_index)
        self._refresh_layer_list()

