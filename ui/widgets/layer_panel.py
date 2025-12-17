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
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QSpinBox,
)
from domain.layers import LayerManager, Layer
from domain.layer_animation import (
    LayerAnimation,
    AnimationType,
    create_scroll_animation,
    create_fade_animation,
    create_pulse_animation,
)


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
        # Store original visibility for solo mode (per layer track, per frame)
        self._solo_original_visibility: Dict[Tuple[int, int], bool] = {}  # (layer_index, frame_index) -> original_visible
        
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
        
        # Visibility and Lock
        visibility_layout = QHBoxLayout()
        self.layer_visible_checkbox = QCheckBox("Visible")
        self.layer_visible_checkbox.toggled.connect(self._on_visibility_changed)
        visibility_layout.addWidget(self.layer_visible_checkbox)
        
        self.layer_locked_checkbox = QCheckBox("Locked")
        self.layer_locked_checkbox.setToolTip("Lock layer to prevent editing")
        self.layer_locked_checkbox.toggled.connect(self._on_lock_changed)
        visibility_layout.addWidget(self.layer_locked_checkbox)
        
        visibility_layout.addStretch()
        props_layout.addLayout(visibility_layout)
        
        # Solo mode toggle
        solo_layout = QHBoxLayout()
        self.solo_mode_checkbox = QCheckBox("Solo Mode (Show Only Active Layer)")
        self.solo_mode_checkbox.setToolTip("When enabled, only the active layer is visible. Other layers are temporarily hidden.")
        self.solo_mode_checkbox.toggled.connect(self._on_solo_mode_changed)
        solo_layout.addWidget(self.solo_mode_checkbox)
        solo_layout.addStretch()
        props_layout.addLayout(solo_layout)
        
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
        
        # Layer Timing (CapCut-like: start/end frames)
        timing_group = QGroupBox("Layer Timing")
        timing_layout = QVBoxLayout()
        
        start_frame_layout = QHBoxLayout()
        start_frame_layout.addWidget(QLabel("Start Frame:"))
        self.start_frame_spin = QSpinBox()
        self.start_frame_spin.setMinimum(0)
        self.start_frame_spin.setMaximum(9999)
        self.start_frame_spin.setSpecialValueText("Frame 0")
        self.start_frame_spin.setToolTip("Frame where this layer starts appearing (0 = from beginning)")
        self.start_frame_spin.valueChanged.connect(self._on_start_frame_changed)
        start_frame_layout.addWidget(self.start_frame_spin)
        start_frame_layout.addStretch()
        timing_layout.addLayout(start_frame_layout)
        
        end_frame_layout = QHBoxLayout()
        end_frame_layout.addWidget(QLabel("End Frame:"))
        self.end_frame_spin = QSpinBox()
        self.end_frame_spin.setMinimum(-1)
        self.end_frame_spin.setMaximum(9999)
        self.end_frame_spin.setSpecialValueText("End of Pattern")
        self.end_frame_spin.setValue(-1)  # -1 = end of pattern
        self.end_frame_spin.setToolTip("Frame where this layer stops appearing (-1 = until end)")
        self.end_frame_spin.valueChanged.connect(self._on_end_frame_changed)
        end_frame_layout.addWidget(self.end_frame_spin)
        end_frame_layout.addStretch()
        timing_layout.addLayout(end_frame_layout)
        
        timing_group.setLayout(timing_layout)
        props_layout.addWidget(timing_group)
        
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
        
        # Animation controls
        animation_group = QGroupBox("Animation")
        animation_layout = QVBoxLayout()
        
        # Animation type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.animation_type_combo = QComboBox()
        self.animation_type_combo.addItems(["None", "Scroll", "Fade", "Pulse"])
        self.animation_type_combo.currentTextChanged.connect(self._on_animation_type_changed)
        type_layout.addWidget(self.animation_type_combo)
        animation_layout.addLayout(type_layout)
        
        # Direction (shown only for Scroll)
        self.direction_widget = QWidget()
        self.direction_layout = QHBoxLayout(self.direction_widget)
        self.direction_layout.setContentsMargins(0, 0, 0, 0)
        self.direction_layout.addWidget(QLabel("Direction:"))
        self.animation_direction_combo = QComboBox()
        self.animation_direction_combo.addItems(["Right", "Left", "Up", "Down"])
        self.direction_layout.addWidget(self.animation_direction_combo)
        self.direction_widget.setVisible(False)  # Hidden by default
        animation_layout.addWidget(self.direction_widget)
        
        # Speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.animation_speed_slider = QSlider(Qt.Horizontal)
        self.animation_speed_slider.setRange(1, 50)  # 0.1x to 5.0x (divide by 10)
        self.animation_speed_slider.setValue(10)  # 1.0x default
        self.animation_speed_label = QLabel("1.0x")
        self.animation_speed_slider.valueChanged.connect(self._on_animation_speed_changed)
        speed_layout.addWidget(self.animation_speed_slider)
        speed_layout.addWidget(self.animation_speed_label)
        animation_layout.addLayout(speed_layout)
        
        # Apply and Remove buttons
        button_layout = QHBoxLayout()
        self.apply_animation_btn = QPushButton("Apply Animation")
        self.apply_animation_btn.clicked.connect(self._on_apply_animation)
        button_layout.addWidget(self.apply_animation_btn)
        
        self.remove_animation_btn = QPushButton("Remove Animation")
        self.remove_animation_btn.clicked.connect(self._on_remove_animation)
        self.remove_animation_btn.setEnabled(False)
        button_layout.addWidget(self.remove_animation_btn)
        animation_layout.addLayout(button_layout)
        
        animation_group.setLayout(animation_layout)
        layout.addWidget(animation_group)
        
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

    def refresh(self):
        """Public method to refresh layer panel display."""
        self._refresh_layer_list()
        self._update_properties()
    
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
            
            # Check for animation
            animation_manager = self.layer_manager.get_animation_manager()
            animation = animation_manager.get_animation(idx)
            if animation and animation.animation_type != AnimationType.NONE:
                anim_type = animation.animation_type.value.capitalize()
                if anim_type == "Scroll":
                    # Try to get direction
                    direction = "Right"  # Default
                    if animation.keyframes:
                        first_kf = animation.keyframes[0]
                        last_kf = animation.keyframes[-1] if len(animation.keyframes) > 1 else first_kf
                        if hasattr(first_kf, 'offset_x') and hasattr(last_kf, 'offset_x'):
                            if last_kf.offset_x > first_kf.offset_x:
                                direction = "Right"
                            elif last_kf.offset_x < first_kf.offset_x:
                                direction = "Left"
                        elif hasattr(first_kf, 'offset_y') and hasattr(last_kf, 'offset_y'):
                            if last_kf.offset_y > first_kf.offset_y:
                                direction = "Down"
                            elif last_kf.offset_y < first_kf.offset_y:
                                direction = "Up"
                        else:
                            direction = "Right"
                    item_text += f" [{anim_type} {direction}]"
                else:
                    item_text += f" [{anim_type}]"
            
            if not layer.visible:
                item_text += " (hidden)"
            if getattr(layer, 'locked', False):
                item_text += " [Locked]"
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
            self.layer_locked_checkbox.setChecked(getattr(layer, 'locked', False))
            self.layer_opacity_slider.setValue(int(layer.opacity * 100))
            self.layer_opacity_label.setText(f"{int(layer.opacity * 100)}%")
            
            # Update timing controls (get from layer track)
            tracks = self.layer_manager.get_layer_tracks()
            if self._active_layer_index < len(tracks):
                track = tracks[self._active_layer_index]
                # Set start frame (None = 0, so show 0 in UI)
                start_val = track.start_frame if track.start_frame is not None else 0
                self.start_frame_spin.setValue(start_val)
                # Set end frame (None = end of pattern, so show -1 in UI)
                end_val = track.end_frame if track.end_frame is not None else -1
                self.end_frame_spin.setValue(end_val)
            
            # Enable controls
            self.layer_name_edit.setEnabled(True)
            self.layer_visible_checkbox.setEnabled(True)
            self.layer_locked_checkbox.setEnabled(True)
            self.layer_opacity_slider.setEnabled(True)
            self.start_frame_spin.setEnabled(True)
            self.end_frame_spin.setEnabled(True)
            self.delete_layer_btn.setEnabled(len(layers) > 1)
            self.move_up_btn.setEnabled(self._active_layer_index > 0)
            self.move_down_btn.setEnabled(self._active_layer_index < len(layers) - 1)
            
            # Enable animation controls
            self.animation_type_combo.setEnabled(True)
            self.animation_direction_combo.setEnabled(True)
            self.animation_speed_slider.setEnabled(True)
            self.apply_animation_btn.setEnabled(True)
            
            # Update animation controls
            self._update_animation_controls()
        else:
            # Disable controls
            self.layer_name_edit.setEnabled(False)
            self.layer_visible_checkbox.setEnabled(False)
            self.layer_opacity_slider.setEnabled(False)
            self.start_frame_spin.setEnabled(False)
            self.end_frame_spin.setEnabled(False)
            self.delete_layer_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            
            # Disable animation controls
            self.animation_type_combo.setEnabled(False)
            self.animation_direction_combo.setEnabled(False)
            self.animation_speed_slider.setEnabled(False)
            self.apply_animation_btn.setEnabled(False)
            self.remove_animation_btn.setEnabled(False)
        
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
    
    def _on_copy_layer_to_frame(self, layer_index: int):
        """Copy layer to other frames."""
        # Get pattern from parent (DesignToolsTab)
        parent = self.parent()
        while parent and not hasattr(parent, '_pattern'):
            parent = parent.parent()
        
        if not parent or not hasattr(parent, '_pattern') or not parent._pattern:
            QMessageBox.warning(self, "No Pattern", "No pattern loaded.")
            return
        
        pattern = parent._pattern
        total_frames = len(pattern.frames)
        
        if total_frames <= 1:
            QMessageBox.information(self, "No Target Frames", "Need at least 2 frames to copy layers.")
            return
        
        # Create dialog to select target frames
        dialog = QDialog(self)
        dialog.setWindowTitle("Copy Layer to Frames")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"Select target frames for layer '{layer_index + 1}':"))
        
        frame_list = QListWidget()
        frame_list.setSelectionMode(QListWidget.MultiSelection)
        for i in range(total_frames):
            if i != self._current_frame_index:  # Exclude current frame
                item_text = f"Frame {i + 1}"
                frame_list.addItem(item_text)
                frame_list.item(i if i < self._current_frame_index else i - 1).setData(Qt.UserRole, i)
        layout.addWidget(frame_list)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            selected_items = frame_list.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "No Selection", "Please select at least one target frame.")
                return
            
            target_frames = [item.data(Qt.UserRole) for item in selected_items]
            
            # Copy layer to target frames
            self.layer_manager.copy_layer_to_frames(self._current_frame_index, layer_index, target_frames)
            
            QMessageBox.information(
                self,
                "Layer Copied",
                f"Layer copied to {len(target_frames)} frame(s)."
            )
            
            # Refresh if parent has refresh method
            if hasattr(parent, '_refresh_timeline'):
                parent._refresh_timeline()
            if hasattr(parent, '_load_current_frame_into_canvas'):
                parent._load_current_frame_into_canvas()

    def _on_name_changed(self):
        """Handle layer name change."""
        if self._updating:
            return
        
        name = self.layer_name_edit.text().strip()
        if name:
            self.layer_manager.set_layer_name(self._current_frame_index, self._active_layer_index, name)
            self._refresh_layer_list()

    def _on_visibility_changed(self, checked: bool):
        """
        Handle visibility toggle.
        
        With LayerTracks, this sets per-frame visibility override if different
        from global, or removes override if same as global.
        """
        if self._updating:
            return
        
        # Get current layer to check if we're setting to global value
        layers = self.layer_manager.get_layers(self._current_frame_index)
        if self._active_layer_index < len(layers):
            current_visible = layers[self._active_layer_index].visible
            # If toggling to same as current, it will remove override (use global)
            # If toggling to different, it will set per-frame override
            self.layer_manager.set_layer_visible(self._current_frame_index, self._active_layer_index, checked)
            self._refresh_layer_list()

    def _on_opacity_changed(self, value: int):
        """Handle opacity change."""
        if self._updating:
            return
        
        opacity = value / 100.0
        self.layer_opacity_label.setText(f"{value}%")
        self.layer_manager.set_layer_opacity(self._current_frame_index, self._active_layer_index, opacity)
    
    def _on_lock_changed(self, checked: bool):
        """Handle lock toggle."""
        if self._updating:
            return
        
        tracks = self.layer_manager.get_layer_tracks()
        if self._active_layer_index < len(tracks):
            track = tracks[self._active_layer_index]
            track.locked = checked
            self.layer_manager.layers_changed.emit(-1)

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
        
        # Copy to Frame
        copy_to_frame_action = menu.addAction("Copy Layer to Frame...")
        copy_to_frame_action.triggered.connect(lambda: self._on_copy_layer_to_frame(layer_index))
        
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
        """
        Handle solo mode toggle.
        
        Solo mode shows only the active layer track. Since layers span frames,
        we need to handle visibility per-frame but store original state properly.
        """
        self._solo_mode = enabled
        self.solo_mode_changed.emit(enabled)
        
        if enabled:
            # Temporarily hide all layer tracks except active for current frame
            layers = self.layer_manager.get_layers(self._current_frame_index)
            for idx, layer in enumerate(layers):
                if idx != self._active_layer_index:
                    # Store original visibility state
                    key = (idx, self._current_frame_index)
                    if key not in self._solo_original_visibility:
                        self._solo_original_visibility[key] = layer.visible
                    # Hide layer for current frame
                    self.layer_manager.set_layer_visible(self._current_frame_index, idx, False)
        else:
            # Restore original visibility for all frames
            for (layer_idx, frame_idx), original_visible in self._solo_original_visibility.items():
                self.layer_manager.set_layer_visible(frame_idx, layer_idx, original_visible)
            self._solo_original_visibility.clear()
        
        # Refresh display
        self._refresh_layer_list()
    
    def is_solo_mode(self) -> bool:
        """Check if solo mode is enabled."""
        return self._solo_mode
    
    def clear_thumbnail_cache(self):
        """Clear the thumbnail cache (call when layer pixels change)."""
        self._layer_thumbnails.clear()
    
    # Animation handlers
    def _on_animation_type_changed(self, text: str):
        """Handle animation type selection change."""
        if self._updating:
            return
        
        # Show/hide direction controls based on animation type
        is_scroll = text == "Scroll"
        self.direction_widget.setVisible(is_scroll)
    
    def _on_animation_speed_changed(self, value: int):
        """Handle animation speed slider change."""
        if self._updating:
            return
        
        speed = value / 10.0  # Convert to 0.1x to 5.0x
        self.animation_speed_label.setText(f"{speed:.1f}x")
    
    def _on_apply_animation(self):
        """
        Apply animation to the active layer.
        
        Note: Each layer can have one animation. Applying a new animation
        replaces any existing animation for that layer.
        """
        if self._updating:
            return
        
        animation_type = self.animation_type_combo.currentText()
        if animation_type == "None":
            QMessageBox.information(self, "No Animation", "Please select an animation type.")
            return
        
        speed = self.animation_speed_slider.value() / 10.0
        
        try:
            if animation_type == "Scroll":
                direction = self.animation_direction_combo.currentText().lower()
                animation = create_scroll_animation(
                    direction=direction,
                    speed=speed,
                    start_frame=0,
                    end_frame=None  # All frames
                )
            elif animation_type == "Fade":
                animation = create_fade_animation(
                    fade_in=True,
                    duration_frames=10,
                    start_frame=0
                )
                animation.speed = speed
            elif animation_type == "Pulse":
                animation = create_pulse_animation(
                    min_opacity=0.5,
                    max_opacity=1.0,
                    period_frames=20,
                    start_frame=0,
                    end_frame=None
                )
                animation.speed = speed
            else:
                return
            
            # Apply animation to active layer
            self.layer_manager.set_layer_animation(self._active_layer_index, animation)
            
            # Update UI
            self._update_animation_controls()
            self._refresh_layer_list()
            
            QMessageBox.information(
                self,
                "Animation Applied",
                f"{animation_type} animation applied to layer."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to apply animation: {str(e)}"
            )
    
    def _on_remove_animation(self):
        """Remove animation from the active layer."""
        if self._updating:
            return
        
        try:
            animation_manager = self.layer_manager.get_animation_manager()
            animation_manager.remove_animation(self._active_layer_index)
            
            # Emit signal to update UI
            self.layer_manager.layers_changed.emit(-1)
            
            # Update UI
            self._update_animation_controls()
            self._refresh_layer_list()
            
            QMessageBox.information(
                self,
                "Animation Removed",
                "Animation removed from layer."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to remove animation: {str(e)}"
            )
    
    def _update_animation_controls(self):
        """Update animation controls based on current layer's animation."""
        if self._updating:
            return
        
        self._updating = True
        
        try:
            animation_manager = self.layer_manager.get_animation_manager()
            animation = animation_manager.get_animation(self._active_layer_index)
            
            if animation and animation.animation_type != AnimationType.NONE:
                # Layer has animation
                anim_type_name = animation.animation_type.value.capitalize()
                if anim_type_name == "Scroll":
                    anim_type_name = "Scroll"
                
                # Set animation type in combo
                index = self.animation_type_combo.findText(anim_type_name)
                if index >= 0:
                    self.animation_type_combo.setCurrentIndex(index)
                
                # Set speed
                speed_value = int(animation.speed * 10)
                self.animation_speed_slider.setValue(speed_value)
                
                # Set direction if scroll
                if animation.animation_type == AnimationType.SCROLL:
                    # Try to determine direction from keyframes
                    if animation.keyframes:
                        first_kf = animation.keyframes[0]
                        last_kf = animation.keyframes[-1] if len(animation.keyframes) > 1 else first_kf
                        
                        if hasattr(first_kf, 'offset_x') and hasattr(last_kf, 'offset_x'):
                            if last_kf.offset_x > first_kf.offset_x:
                                direction = "Right"
                            elif last_kf.offset_x < first_kf.offset_x:
                                direction = "Left"
                            else:
                                direction = "Right"  # Default
                        elif hasattr(first_kf, 'offset_y') and hasattr(last_kf, 'offset_y'):
                            if last_kf.offset_y > first_kf.offset_y:
                                direction = "Down"
                            elif last_kf.offset_y < first_kf.offset_y:
                                direction = "Up"
                            else:
                                direction = "Down"  # Default
                        else:
                            direction = "Right"  # Default
                        
                        index = self.animation_direction_combo.findText(direction)
                        if index >= 0:
                            self.animation_direction_combo.setCurrentIndex(index)
                    
                    self.direction_widget.setVisible(True)
                
                # Enable remove button
                self.remove_animation_btn.setEnabled(True)
            else:
                # No animation
                self.animation_type_combo.setCurrentIndex(0)  # "None"
                self.animation_speed_slider.setValue(10)  # 1.0x
                self.direction_widget.setVisible(False)
                self.remove_animation_btn.setEnabled(False)
        except Exception:
            # If error, reset to defaults
            self.animation_type_combo.setCurrentIndex(0)
            self.animation_speed_slider.setValue(10)
            self.direction_layout.setVisible(False)
            self.remove_animation_btn.setEnabled(False)
        finally:
            self._updating = False
    
    def _on_layers_reordered(self, parent, start, end, destination, row):
        """
        Handle layer reordering via drag-and-drop.
        
        With LayerTracks, reordering affects all frames since layers span frames.
        """
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
        
        # Verify we have the right number of layers
        tracks = self.layer_manager.get_layer_tracks()
        if len(new_order) != len(tracks):
            # Something went wrong, refresh
            self._updating = False
            self._refresh_layer_list()
            return
        
        # Store old active layer index
        old_active_idx = self._active_layer_index
        
        # Reorder by rebuilding tracks list in new order
        # This is simpler and more reliable than multiple move operations
        reordered_tracks = [tracks[idx] for idx in new_order]
        
        # Update the layer manager's tracks list directly
        self.layer_manager._layer_tracks = reordered_tracks
        
        # Update z_index for all tracks to match new order
        for i, track in enumerate(self.layer_manager._layer_tracks):
            track.z_index = i
        
        # Find new position of active layer
        # The active layer's old index should now be at its new position in new_order
        if old_active_idx < len(new_order):
            try:
                new_active_idx = new_order.index(old_active_idx)
                self._active_layer_index = new_active_idx
            except ValueError:
                # Fallback: keep same index if valid
                if old_active_idx < len(reordered_tracks):
                    self._active_layer_index = old_active_idx
                else:
                    self._active_layer_index = 0
        
        self._updating = False
        
        # Emit signal to update UI (affects all frames)
        self.layer_manager.layers_changed.emit(-1)  # -1 = all frames
        self._refresh_layer_list()

