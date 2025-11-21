"""
Design Tools Tab - LED matrix pattern authoring environment.

This tab provides an interactive workspace for crafting LED matrix animations.
Users can paint frames, manage palettes, queue automation actions (scroll,
mirror, rotate, etc.), and preview the resulting animation.
"""

from __future__ import annotations

import os
import sys
import copy
import hashlib
import json
import random
from functools import partial
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, QTimer, QSize, QUrl
from PySide6.QtGui import QColor, QCursor, QDesktopServices, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QFrame,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QDoubleSpinBox,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QLabel,
    QSlider,
    QSpinBox,
    QButtonGroup,
    QProgressDialog,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QPlainTextEdit,
)
from pathlib import Path
import shutil
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pattern import Pattern, Frame, PatternMetadata  # noqa: E402
from core.automation import (
    KNOWN_LMS_ACTIONS,
    LayerBinding,
    LMSInstruction,
    PatternInstruction,
    PatternInstructionSequence,
    PreviewSimulator,
)  # noqa: E402
from core.image_importer import ImageImporter  # noqa: E402
from core.image_exporter import ImageExporter  # noqa: E402
from core.export import (
    generate_export_preview,
    ExportValidationError,
    ExportPreview,
)  # noqa: E402
from core.export_templates import available_templates, render_template  # noqa: E402
from core.io import (
    LMSFormatError,
    parse_bin_stream,
    parse_dat_file,
    parse_hex_file,
    parse_leds_file,
    write_leds_file,
)  # noqa: E402
from ui.widgets.matrix_design_canvas import (  # noqa: E402
    MatrixDesignCanvas,
    DrawingMode,
    PixelShape,
    GeometryOverlay,
)
from ui.widgets.layer_panel import LayerPanelWidget  # noqa: E402
from ui.widgets.timeline_widget import (
    TimelineWidget,
    TimelineMarker,
    TimelineOverlay,
    TimelineLayerTrack,
)  # noqa: E402
from domain.actions import DesignAction  # noqa: E402
from domain.pattern_state import PatternState  # noqa: E402
from domain.frames import FrameManager  # noqa: E402
from domain.layers import LayerManager, Layer  # noqa: E402
from domain.scratchpads import ScratchpadManager  # noqa: E402
from domain.canvas import CanvasController  # noqa: E402
from domain.automation.queue import AutomationQueueManager  # noqa: E402
from domain.history import HistoryManager, FrameStateCommand  # noqa: E402
from domain.automation.presets import PresetRepository  # noqa: E402
from domain.effects import EffectDefinition, EffectLibrary, apply_effect_to_frames  # noqa: E402
from domain.text.bitmap_font import BitmapFontRepository, BitmapFont  # noqa: E402
from ui.icons import get_icon
from ui.widgets.effects_library_widget import EffectsLibraryWidget
from ui.dialogs.detached_preview_dialog import DetachedPreviewDialog
from ui.dialogs.font_designer_dialog import FontDesignerDialog
from ui.dialogs.automation_wizard_dialog import AutomationWizardDialog


class DesignToolsTab(QWidget):
    """
    Comprehensive LED matrix design studio.

    Key capabilities:
        - Interactive matrix painting canvas
        - Palette-based color selection
        - Frame management (add, duplicate, delete, reorder)
        - Automation action queue (scroll, rotate, mirror, invert, etc.)
        - Pattern import/export with rest of application
    """

    pattern_modified = Signal()
    pattern_created = Signal(Pattern)
    playback_state_changed = Signal(bool)  # Emitted when playback state changes (True=playing, False=paused/stopped)
    frame_changed = Signal(int)  # Emitted when frame index changes

    DEFAULT_COLORS = [
        (0, 0, 0),
        (255, 255, 255),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
        (255, 128, 0),
        (255, 0, 128),
        (0, 128, 255),
        (128, 0, 255),
        (0, 255, 128),
        (128, 255, 0),
        (128, 128, 128),
        (64, 64, 64),
    ]

    DEFAULT_THEME = "dark"
    ENV_THEME_KEY = "UPLOADBRIDGE_THEME"

    THEME_DEFINITIONS = {
        "dark": {
            "ui": {
                "bg": "#121212",
                "surface": "#1E1E1E",
                "surface_alt": "#242424",
                "border": "#2E2E2E",
                "accent": "#4C8BF5",
                "accent_hover": "#5B99FF",
                "text_primary": "#F5F5F5",
                "text_secondary": "#B5B5B5",
                "text_on_accent": "#FFFFFF",
                "list_bg": "#171717",
                "list_hover": "#242424",
                "control_bg": "#2A2A2A",
                "control_disabled_bg": "#1A1A1A",
                "control_disabled_text": "#666666",
                "slider_groove": "#1F1F1F",
                "slider_handle": "#4C8BF5",
                "danger": "#E55B5B",
            },
            "timeline": {
                "background": "#171717",
                "frame_bg": "#1F1F1F",
                "frame_hover": "#2A2A2A",
                "frame_border": "#2E2E2E",
                "text": "#DDDDDD",
                "secondary_text": "#B5B5B5",
                "no_frames_text": "#777777",
                "overlay_text": "#F5F5F5",
                "playhead": "#4C8BF5",
            },
            "simulator": {
                "background": "#141414",
                "border": "#555555",
                "grid_light": "#343434",
                "grid_dark": "#222222",
                "number": "#111111",
            },
            "canvas": {
                "background": "#222222",
                "grid": "#3C3C3C",
                "hover": "#4CFFB3",
                "pixel_border": "#161616",
            },
        },
        "light": {
            "ui": {
                "bg": "#F4F5F8",
                "surface": "#FFFFFF",
                "surface_alt": "#F1F3F8",
                "border": "#D6D8E0",
                "accent": "#3D6DEB",
                "accent_hover": "#5781F0",
                "text_primary": "#1E1F25",
                "text_secondary": "#4F5565",
                "text_on_accent": "#FFFFFF",
                "list_bg": "#FFFFFF",
                "list_hover": "#E8ECF8",
                "control_bg": "#F7F8FC",
                "control_disabled_bg": "#ECEEF5",
                "control_disabled_text": "#9EA4B5",
                "slider_groove": "#E0E4F1",
                "slider_handle": "#3D6DEB",
                "danger": "#D64545",
            },
            "timeline": {
                "background": "#F5F6FB",
                "frame_bg": "#FFFFFF",
                "frame_hover": "#E8ECF8",
                "frame_border": "#D0D5E6",
                "text": "#2B2F38",
                "secondary_text": "#596072",
                "no_frames_text": "#9AA1B5",
                "overlay_text": "#2B2F38",
                "playhead": "#3D6DEB",
            },
            "simulator": {
                "background": "#FFFFFF",
                "border": "#C5C9D6",
                "grid_light": "#E4E7F2",
                "grid_dark": "#BCC3D6",
                "number": "#1F2230",
            },
            "canvas": {
                "background": "#FFFFFF",
                "grid": "#D8DBE6",
                "hover": "#3D6DEB",
                "pixel_border": "#C8CCDA",
            },
        },
    }

    MATRIX_PRESETS = [
        {"label": "8×8 Mono", "width": 8, "height": 8, "color": "Mono"},
        {"label": "16×16 Bi-colour", "width": 16, "height": 16, "color": "Bi-colour"},
        {"label": "16×32 RGB", "width": 16, "height": 32, "color": "RGB"},
        {"label": "32×32 RGB", "width": 32, "height": 32, "color": "RGB"},
        {"label": "64×32 RGB", "width": 64, "height": 32, "color": "RGB"},
    ]

    ACTION_PARAM_CONFIG = {
        "scroll": {
            "direction": {
                "type": "choice",
                "label": "Direction",
                "choices": ["Up", "Down", "Left", "Right"],
                "default": "Right",
                "required": True,
                "description": "Direction in which the frame content will be shifted.",
            },
            "offset": {
                "type": "int",
                "label": "Offset per Frame",
                "default": 1,
                "min": 1,
                "max": 10,
                "description": "Number of pixels to shift per frame (1-10).",
            },
        },
        "wipe": {
            "mode": {
                "type": "choice",
                "label": "Mode",
                "choices": ["Left to Right", "Right to Left", "Top to Bottom", "Bottom to Top"],
                "default": "Left to Right",
                "required": True,
                "description": "Direction of the wipe animation.",
            },
            "offset": {
                "type": "int",
                "label": "Offset per Frame",
                "default": 1,
                "min": 1,
                "max": 10,
                "description": "Number of pixels to wipe per frame (1-10).",
            },
            "intensity": {
                "type": "float",
                "label": "Intensity",
                "default": 1.0,
                "min": 0.1,
                "max": 5.0,
                "step": 0.1,
                "description": "Multiplier for the wipe fade intensity.",
            },
        },
        "reveal": {
            "direction": {
                "type": "choice",
                "label": "Reveal From",
                "choices": ["Left", "Right", "Top", "Bottom"],
                "default": "Left",
                "required": True,
            },
            "offset": {
                "type": "int",
                "label": "Offset per Frame",
                "default": 1,
                "min": 1,
                "max": 10,
                "description": "Number of pixels to reveal per frame (1-10).",
            },
            "feather": {
                "type": "int",
                "label": "Feather Pixels",
                "default": 0,
                "min": 0,
                "max": 10,
                "description": "Softens the reveal edge by this many pixels.",
            },
        },
        "rotate": {
            "mode": {
                "type": "choice",
                "label": "Rotation",
                "choices": ["90° Clockwise", "90° Counter-clockwise"],
                "default": "90° Clockwise",
                "required": True,
            }
        },
        "mirror": {
            "axis": {
                "type": "choice",
                "label": "Axis",
                "choices": ["horizontal", "vertical"],
                "default": "horizontal",
                "required": True,
            }
        },
        "flip": {
            "axis": {
                "type": "choice",
                "label": "Axis",
                "choices": ["vertical", "horizontal"],
                "default": "vertical",
                "required": True,
            }
        },
        "invert": {},
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("DesignToolsTab")
        self._theme = self._resolve_initial_theme()
        self._current_ui_palette: Dict[str, str] = self.THEME_DEFINITIONS[self._theme]["ui"]
        self._pattern: Optional[Pattern] = None
        self._current_frame_index: int = 0
        self._frame_duration_ms: int = 50
        self._current_color: Tuple[int, int, int] = (255, 255, 255)
        self._start_gradient_color: Tuple[int, int, int] = (255, 0, 0)
        self._end_gradient_color: Tuple[int, int, int] = (0, 0, 255)
        self._has_unsaved_changes: bool = False
        self._suspend_timeline_refresh: bool = False
        self._single_color_mode: bool = False  # Single color mode (white only)
        self.state = PatternState()
        self.frame_manager = FrameManager(self.state)
        self.layer_manager = LayerManager(self.state)
        self.layer_manager.layers_changed.connect(self._on_layers_structure_updated)
        self.layer_manager.layer_added.connect(self._on_layers_structure_updated)
        self.layer_manager.layer_removed.connect(self._on_layers_structure_updated)
        self.layer_manager.layer_moved.connect(self._on_layers_structure_updated)
        self.scratchpad_manager = ScratchpadManager(self.state)
        self.automation_manager = AutomationQueueManager()
        self.canvas_controller = CanvasController(self.state)
        self.history_manager = HistoryManager(max_history=50)
        self._current_action_index = -1
        self._pending_paint_state: Optional[List[Tuple[int, int, int]]] = None  # Track state before paint operations
        self._preview_cache: Dict[str, Pattern] = {}  # Cache for preview patterns
        self._preview_cache_key: Optional[str] = None  # Current cache key
        self._lms_sequence = PatternInstructionSequence()
        self._lms_preview_snapshot: Optional[Pattern] = None
        self.lms_source_combo: Optional[QComboBox] = None
        self.lms_layer2_combo: Optional[QComboBox] = None
        self.lms_mask_combo: Optional[QComboBox] = None
        self.lms_action_combo: Optional[QComboBox] = None
        self.lms_custom_action_edit: Optional[QLineEdit] = None
        self.lms_repeat_spin: Optional[QSpinBox] = None
        self.lms_gap_spin: Optional[QSpinBox] = None
        self.lms_brightness_spin: Optional[QSpinBox] = None
        self.lms_params_edit: Optional[QLineEdit] = None
        self.lms_instruction_list: Optional[QListWidget] = None
        self.lms_sequence_summary_label: Optional[QLabel] = None
        self.lms_preview_limit_spin: Optional[QSpinBox] = None
        self.lms_preview_status_label: Optional[QLabel] = None
        self.lms_export_log: Optional[QPlainTextEdit] = None
        self.lms_builder_status_label: Optional[QLabel] = None
        self.preset_repo = PresetRepository(self._default_preset_path())
        self.effects_library = EffectLibrary(Path("Res/effects"))
        self.effects_widget: Optional[EffectsLibraryWidget] = None
        self._effects_info_default: str = ""
        self.font_repo = BitmapFontRepository(Path("Res/fonts"))
        self._active_bitmap_font: Optional[BitmapFont] = None
        self._scratchpad_status_labels: Dict[int, QLabel] = {}
        self._scratchpad_paste_buttons: Dict[int, QPushButton] = {}
        self._detached_preview: Optional[DetachedPreviewDialog] = None
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(False)
        self._autosave_timer.timeout.connect(self._perform_autosave)
        self._autosave_enabled = False
        self.frame_manager.frames_changed.connect(self._refresh_timeline)
        self.frame_manager.frames_changed.connect(self._refresh_lms_frame_bindings)
        self.frame_manager.frame_index_changed.connect(self._on_manager_frame_selected)
        self.frame_manager.frame_duration_changed.connect(self._on_manager_duration_changed)
        self.automation_manager.queue_changed.connect(self._on_manager_queue_changed)
        self.scratchpad_manager.scratchpad_changed.connect(self._refresh_scratchpad_status)
        self.canvas_controller.set_frame_supplier(self.frame_manager.frame)
        self.canvas_controller.frame_ready.connect(self._apply_frame_to_canvas)
        self._playback_timer = QTimer(self)
        self._playback_timer.setTimerType(Qt.PreciseTimer)
        self._playback_timer.timeout.connect(self._on_playback_tick)
        self._playback_fps_default = 24
        self._thumbnail_size = QSize(72, 72)
        self.canvas_group: Optional[QGroupBox] = None
        self._frame_size_mismatch_indices: List[int] = []
        self._frame_size_warning_shown = False
        self._import_metadata_snapshot: Optional[Dict[str, object]] = None
        self._syncing_playback = False  # Flag to prevent signal loops
        self._syncing_frame = False  # Flag to prevent frame sync loops

        self._setup_ui()
        self._create_default_pattern()
        self._apply_theme()
        self._refresh_preset_combo()
        self.pattern_modified.connect(self._sync_detached_preview)
        self.pattern_modified.connect(self._mark_dirty)
        self.frame_manager.frames_changed.connect(self._sync_detached_preview)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        self.header_bar = self._create_header_toolbar()
        root_layout.addWidget(self.header_bar)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        self.canvas_panel = self._create_canvas_panel()
        self.main_splitter.addWidget(self.canvas_panel)

        self.toolbox_container = self._create_toolbox_column()
        self.main_splitter.addWidget(self.toolbox_container)
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 1)
        root_layout.addWidget(self.main_splitter, 1)

        self.timeline_dock = self._create_timeline_dock()
        root_layout.addWidget(self.timeline_dock)

        self._set_canvas_zoom(100)
        self._update_status_labels()
        self._update_transport_controls()

    def _create_header_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("designToolsHeader")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.header_title_label = QLabel("Design Tools")
        self.header_title_label.setObjectName("designToolsTitle")
        layout.addWidget(self.header_title_label)

        layout.addSpacing(8)

        # New and Open buttons
        new_button = QPushButton("New")
        new_button.setToolTip("Create a new pattern")
        new_button.clicked.connect(self._on_new_pattern_clicked)
        layout.addWidget(new_button)

        open_button = QPushButton("Open")
        open_button.setToolTip("Open an existing pattern file")
        open_button.clicked.connect(self._on_open_pattern_clicked)
        layout.addWidget(open_button)

        layout.addSpacing(8)

        self.matrix_status_label = QLabel("Matrix: –")
        self.matrix_status_label.setObjectName("designToolsMatrix")
        layout.addWidget(self.matrix_status_label)

        self.frame_status_label = QLabel("Frame: –")
        self.frame_status_label.setObjectName("designToolsFrame")
        layout.addWidget(self.frame_status_label)

        self.layer_status_label = QLabel("Layer: –")
        self.layer_status_label.setObjectName("designToolsLayer")
        layout.addWidget(self.layer_status_label)

        layout.addSpacing(8)

        self.playback_status_label = QLabel("Playback: –")
        self.playback_status_label.setObjectName("designToolsPlayback")
        layout.addWidget(self.playback_status_label)

        self.memory_status_label = QLabel("Memory: –")
        self.memory_status_label.setObjectName("designToolsMemory")
        layout.addWidget(self.memory_status_label)

        layout.addStretch(1)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        fps_label = QLabel("FPS:")
        fps_label.setObjectName("designToolsFpsLabel")
        controls_layout.addWidget(fps_label)

        self.header_fps_spin = QSpinBox()
        self.header_fps_spin.setRange(1, 240)
        self.header_fps_spin.setValue(self._playback_fps_default)
        self.header_fps_spin.valueChanged.connect(self._on_playback_fps_changed)
        controls_layout.addWidget(self.header_fps_spin)

        self.header_loop_toggle = QToolButton()
        self.header_loop_toggle.setCheckable(True)
        self.header_loop_toggle.setChecked(True)
        self.header_loop_toggle.setIcon(get_icon("loop"))
        self.header_loop_toggle.setIconSize(QSize(20, 20))
        self.header_loop_toggle.setToolTip("Loop playback")
        self.header_loop_toggle.toggled.connect(self._on_playback_loop_toggled)
        controls_layout.addWidget(self.header_loop_toggle)

        layout.addLayout(controls_layout)

        layout.addSpacing(8)

        save_button = QToolButton()
        save_button.setIcon(get_icon("export"))
        save_button.setIconSize(QSize(20, 20))
        save_button.setToolTip("Quick export")
        save_button.clicked.connect(self._on_header_save_clicked)
        layout.addWidget(save_button)

        settings_button = QToolButton()
        settings_button.setIcon(get_icon("automation"))
        settings_button.setIconSize(QSize(20, 20))
        settings_button.setToolTip("Design settings")
        settings_button.clicked.connect(self._on_header_settings_clicked)
        layout.addWidget(settings_button)

        return bar

    def _create_canvas_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("designCanvasPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)
        title_label = QLabel("Matrix Designer")
        title_label.setObjectName("canvasPanelTitle")
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        hud_row = QHBoxLayout()
        hud_row.setContentsMargins(0, 0, 0, 0)
        hud_row.setSpacing(6)

        self.canvas_undo_btn = QToolButton()
        self.canvas_undo_btn.clicked.connect(self._on_undo)
        self._apply_button_icon(self.canvas_undo_btn, "undo", tooltip="Undo (Ctrl+Z)", icon_only=True)
        hud_row.addWidget(self.canvas_undo_btn)

        self.canvas_redo_btn = QToolButton()
        self.canvas_redo_btn.clicked.connect(self._on_redo)
        self._apply_button_icon(self.canvas_redo_btn, "redo", tooltip="Redo (Ctrl+Y)", icon_only=True)
        hud_row.addWidget(self.canvas_redo_btn)

        layout.addLayout(hud_row)

        canvas_group = self._create_canvas_group()
        canvas_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas_group, 1)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(6)
        self.canvas_status_label = QLabel("Click to paint. Right-click to erase.")
        status_row.addWidget(self.canvas_status_label)
        status_row.addStretch(1)
        layout.addLayout(status_row)

        view_controls = self._create_view_controls_group()
        layout.addWidget(view_controls)

        return panel

    def _create_toolbox_column(self) -> QWidget:
        panels: List[Tuple[str, str, QWidget]] = [
            ("Brushes", "brush", self._create_brushes_tab()),
            ("Scratchpads", "layers", self._create_scratchpad_tab()),
            ("Layers", "layers", self._create_layers_tab()),
            ("Effects", "effects", self._create_effects_tab()),
            ("Automation", "automation", self._create_automation_tab()),
            ("Export", "export", self._create_export_tab()),
        ]

        self.toolbox_tabs = QTabWidget()
        self.toolbox_tabs.setObjectName("toolboxTabs")
        self.toolbox_tabs.setMovable(False)
        self.toolbox_tabs.setDocumentMode(True)
        self.toolbox_tabs.setTabPosition(QTabWidget.North)

        for title, icon_name, panel in panels:
            scroll = QScrollArea()
            scroll.setWidget(panel)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.toolbox_tabs.addTab(scroll, get_icon(icon_name), title)

        self.toolbox_tabs.currentChanged.connect(self._on_toolbox_tab_changed)
        return self.toolbox_tabs

    def _create_timeline_dock(self) -> QWidget:
        dock = QFrame()
        dock.setObjectName("timelineDock")
        layout = QVBoxLayout(dock)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        self.timeline = TimelineWidget()
        self.timeline.frameSelected.connect(self._on_frame_selected)
        self.timeline.playheadDragged.connect(self._on_timeline_playhead_dragged)
        self.timeline.contextMenuRequested.connect(self._on_timeline_context_menu)
        self.timeline.overlayActivated.connect(self._on_timeline_overlay_activated)
        self.timeline.overlayContextMenuRequested.connect(self._on_timeline_overlay_context_menu)
        self.timeline.layerTrackSelected.connect(self._on_timeline_layer_selected)
        layout.addWidget(self.timeline, 1)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(12)

        frame_ops = QHBoxLayout()
        frame_ops.setSpacing(6)
        self.add_frame_btn = QPushButton("Add")
        self._apply_button_icon(self.add_frame_btn, "add", tooltip="Add new frame (Ctrl+Shift+A)")
        self.add_frame_btn.clicked.connect(self._on_add_frame)
        frame_ops.addWidget(self.add_frame_btn)

        self.duplicate_frame_btn = QPushButton("Duplicate")
        self._apply_button_icon(self.duplicate_frame_btn, "duplicate", tooltip="Duplicate selected frame")
        self.duplicate_frame_btn.clicked.connect(self._on_duplicate_frame)
        frame_ops.addWidget(self.duplicate_frame_btn)

        self.delete_frame_btn = QPushButton("Delete")
        self._apply_button_icon(self.delete_frame_btn, "delete", tooltip="Delete selected frame (Del)")
        self.delete_frame_btn.clicked.connect(self._on_delete_frame)
        frame_ops.addWidget(self.delete_frame_btn)
        controls.addLayout(frame_ops)

        controls.addStretch(1)

        playback_ops = QHBoxLayout()
        playback_ops.setSpacing(6)
        self.playback_prev_btn = QToolButton()
        self._apply_button_icon(self.playback_prev_btn, "step-back", tooltip="Step to previous frame", icon_only=True)
        self.playback_prev_btn.clicked.connect(lambda: self._step_frame(-1, wrap=self._loop_enabled()))
        playback_ops.addWidget(self.playback_prev_btn)

        self.playback_play_btn = QToolButton()
        self._apply_button_icon(self.playback_play_btn, "play", tooltip="Play timeline", icon_only=True)
        self.playback_play_btn.clicked.connect(self._on_transport_play)
        playback_ops.addWidget(self.playback_play_btn)

        self.playback_pause_btn = QToolButton()
        self._apply_button_icon(self.playback_pause_btn, "pause", tooltip="Pause playback", icon_only=True)
        self.playback_pause_btn.clicked.connect(self._on_transport_pause)
        playback_ops.addWidget(self.playback_pause_btn)

        self.playback_stop_btn = QToolButton()
        self._apply_button_icon(self.playback_stop_btn, "stop", tooltip="Stop playback", icon_only=True)
        self.playback_stop_btn.clicked.connect(self._on_transport_stop)
        playback_ops.addWidget(self.playback_stop_btn)

        self.playback_next_btn = QToolButton()
        self._apply_button_icon(self.playback_next_btn, "step-forward", tooltip="Step to next frame", icon_only=True)
        self.playback_next_btn.clicked.connect(lambda: self._step_frame(1, wrap=self._loop_enabled()))
        playback_ops.addWidget(self.playback_next_btn)
        controls.addLayout(playback_ops)

        controls.addStretch(1)

        info_ops = QHBoxLayout()
        info_ops.setSpacing(8)
        info_ops.addWidget(QLabel("Frame duration (ms):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 2000)
        self.duration_spin.setValue(self._frame_duration_ms)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        info_ops.addWidget(self.duration_spin)

        info_ops.addSpacing(12)
        info_ops.addWidget(QLabel("Timeline Zoom:"))
        self.timeline_zoom_slider = QSlider(Qt.Horizontal)
        self.timeline_zoom_slider.setRange(25, 400)
        self.timeline_zoom_slider.setValue(100)
        self.timeline_zoom_slider.valueChanged.connect(self._on_timeline_zoom_changed)
        info_ops.addWidget(self.timeline_zoom_slider)

        self.timeline_zoom_label = QLabel("100%")
        info_ops.addWidget(self.timeline_zoom_label)

        info_ops.addSpacing(12)
        self.playback_repeat_label = QLabel("Loop: ∞ • 0 ms/frame")
        info_ops.addWidget(self.playback_repeat_label)
        controls.addLayout(info_ops)

        layout.addLayout(controls)
        self._on_timeline_zoom_changed(self.timeline_zoom_slider.value())
        return dock

    def _on_toolbox_tab_changed(self, index: int) -> None:
        # Reserved for future analytics or contextual help.
        _ = index

    def _on_header_save_clicked(self) -> None:
        try:
            self._on_open_export_dialog()
        except Exception as exc:  # pragma: no cover - defensive fallback
            QMessageBox.information(self, "Export", f"Export dialog unavailable: {exc}")

    def _on_header_settings_clicked(self) -> None:
        QMessageBox.information(
            self,
            "Design Settings",
            "Global editor preferences will be available here in a future update.",
        )

    def _on_new_pattern_clicked(self) -> None:
        """Handle New button click - show new pattern dialog."""
        if not self._confirm_discard_changes():
            return
        from ui.dialogs.new_pattern_dialog import NewPatternDialog
        
        current_width = self.width_spin.value() if hasattr(self, "width_spin") else 12
        current_height = self.height_spin.value() if hasattr(self, "height_spin") else 6
        
        dialog = NewPatternDialog(self, current_width, current_height)
        if dialog.exec() == QDialog.Accepted:
            width = dialog.get_width()
            height = dialog.get_height()
            led_type = dialog.get_led_type()
            is_single_color = dialog.is_single_color()
            
            # Create new pattern
            blank_frame = self._create_blank_frame(width, height)
            metadata = PatternMetadata(width=width, height=height)
            # Store LED type in metadata
            if not hasattr(metadata, 'led_type'):
                metadata.led_type = led_type
            else:
                metadata.led_type = led_type
            metadata.is_single_color = is_single_color
            
            pattern = Pattern(name="New Design", metadata=metadata, frames=[blank_frame])
            self.load_pattern(pattern)
            
            # Update single color mode
            self._single_color_mode = is_single_color
            if is_single_color:
                # Force white color only
                self._current_color = (255, 255, 255)
                self._sync_channel_controls(self._current_color)
                self.canvas.set_current_color(self._current_color)
                # Disable color sliders in single color mode
                if hasattr(self, "channel_sliders"):
                    for ch in ("R", "G", "B"):
                        if ch in self.channel_sliders:
                            slider, spin = self.channel_sliders[ch]
                            slider.setEnabled(False)
                            spin.setEnabled(False)
            else:
                # Enable color sliders in RGB/GRB mode
                if hasattr(self, "channel_sliders"):
                    for ch in ("R", "G", "B"):
                        if ch in self.channel_sliders:
                            slider, spin = self.channel_sliders[ch]
                            slider.setEnabled(True)
                            spin.setEnabled(True)
            self._update_single_color_ui_state()

    def _on_open_pattern_clicked(self) -> None:
        """Handle Open button click - show file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Pattern File",
            "",
            "Pattern Files (*.bin *.dat *.leds *.hex);;All Files (*.*)"
        )
        
        if file_path:
            if not self._confirm_discard_changes():
                return
            try:
                from parsers.parser_registry import ParserRegistry
                registry = ParserRegistry()
                pattern = registry.parse_file(file_path)
                if pattern:
                    self.load_pattern(pattern, file_path)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Open Failed",
                    f"Failed to open pattern file:\n{str(e)}"
                )

    def _apply_button_icon(
        self,
        button: QWidget,
        icon_name: str,
        tooltip: Optional[str] = None,
        icon_only: bool = False,
    ) -> None:
        """Configure a button or tool button with a themed icon."""
        icon = get_icon(icon_name, size=20)
        if hasattr(button, "setIcon"):
            button.setIcon(icon)
        if hasattr(button, "setIconSize"):
            button.setIconSize(QSize(20, 20))
        if tooltip:
            button.setToolTip(tooltip)
        if hasattr(button, "setCursor"):
            button.setCursor(Qt.PointingHandCursor)
        if icon_only:
            if hasattr(button, "setText"):
                button.setText("")
            if isinstance(button, QToolButton):
                button.setToolButtonStyle(Qt.ToolButtonIconOnly)
            else:
                button.setFlat(True)
                button.setMinimumWidth(32)
            if hasattr(button, "setMinimumHeight"):
                button.setMinimumHeight(32)

    def _loop_enabled(self) -> bool:
        toggle = getattr(self, "header_loop_toggle", None)
        if toggle is not None:
            return toggle.isChecked()
        checkbox = getattr(self, "playback_loop_checkbox", None)
        return checkbox.isChecked() if checkbox else False

    def _set_loop_enabled(self, enabled: bool) -> None:
        toggle = getattr(self, "header_loop_toggle", None)
        if toggle is not None:
            toggle.setChecked(enabled)
        elif hasattr(self, "playback_loop_checkbox"):
            self.playback_loop_checkbox.setChecked(enabled)

    def _get_playback_fps(self) -> int:
        spin = getattr(self, "header_fps_spin", None)
        if spin is not None:
            return spin.value()
        spin = getattr(self, "playback_fps_spin", None)
        return spin.value() if spin else self._playback_fps_default

    def _set_playback_fps(self, value: int) -> None:
        spin = getattr(self, "header_fps_spin", None)
        if spin is not None:
            spin.setValue(value)
        elif hasattr(self, "playback_fps_spin"):
            self.playback_fps_spin.setValue(value)

    def _create_canvas_group(self) -> QGroupBox:
        group = QFrame()
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.canvas = MatrixDesignCanvas(width=12, height=6, pixel_size=28)
        self.canvas.pixel_updated.connect(self._on_canvas_pixel_updated)
        self.canvas.painting_finished.connect(self._commit_paint_operation)
        self.canvas.set_random_palette(self.DEFAULT_COLORS)
        self.canvas.set_gradient_brush(self._start_gradient_color, self._end_gradient_color, 32)
        layout.addWidget(self.canvas, 1)

        self.canvas_group = group
        self._update_canvas_group_height()
        return group

    def _create_view_controls_group(self) -> QGroupBox:
        group = QGroupBox("View Controls")
        layout = QVBoxLayout()
        layout.setSpacing(6)

        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Canvas Zoom:"))
        self.canvas_zoom_slider = QSlider(Qt.Horizontal)
        self.canvas_zoom_slider.setRange(25, 300)
        self.canvas_zoom_slider.setValue(100)
        self.canvas_zoom_slider.valueChanged.connect(self._on_canvas_zoom_changed)
        zoom_row.addWidget(self.canvas_zoom_slider)
        self.canvas_zoom_label = QLabel("100%")
        zoom_row.addWidget(self.canvas_zoom_label)
        reset_btn = QToolButton()
        reset_btn.clicked.connect(lambda: self._set_canvas_zoom(100))
        self._apply_button_icon(reset_btn, "target", tooltip="Reset canvas zoom", icon_only=True)
        zoom_row.addWidget(reset_btn)
        layout.addLayout(zoom_row)

        geometry_row = QHBoxLayout()
        geometry_row.addWidget(QLabel("Geometry Overlay:"))
        self.canvas_geometry_combo = QComboBox()
        overlay_options = [
            ("Matrix", GeometryOverlay.MATRIX.value),
            ("Circle", GeometryOverlay.CIRCLE.value),
            ("Ring", GeometryOverlay.RING.value),
            ("Radial", GeometryOverlay.RADIAL.value),
        ]
        for label, value in overlay_options:
            self.canvas_geometry_combo.addItem(label, value)
        self.canvas_geometry_combo.currentIndexChanged.connect(self._on_canvas_geometry_changed)
        geometry_row.addWidget(self.canvas_geometry_combo)

        geometry_row.addWidget(QLabel("Pixel Shape:"))
        self.canvas_pixel_shape_combo = QComboBox()
        pixel_options = [
            ("Square", PixelShape.SQUARE.value),
            ("Round", PixelShape.ROUND.value),
            ("Rounded", PixelShape.ROUNDED.value),
        ]
        for label, value in pixel_options:
            self.canvas_pixel_shape_combo.addItem(label, value)
        self.canvas_pixel_shape_combo.currentIndexChanged.connect(self._on_canvas_pixel_shape_changed)
        geometry_row.addWidget(self.canvas_pixel_shape_combo)

        self.detached_preview_btn = QPushButton("Detached Preview")
        self.detached_preview_btn.clicked.connect(self._open_detached_preview)
        geometry_row.addWidget(self.detached_preview_btn)
        geometry_row.addStretch()
        layout.addLayout(geometry_row)

        group.setLayout(layout)
        return group

    def _create_brushes_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.addWidget(self._create_appearance_group())
        layout.addWidget(self._create_drawing_tools_group())
        layout.addWidget(self._create_palette_group(), stretch=1)
        layout.addWidget(self._create_text_animation_group())
        layout.addStretch()
        return tab

    def _create_scratchpad_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        intro = QLabel(
            "Scratchpads mirror LED Matrix Studio buffers: copy any frame into a slot, then paste it later "
            "without leaving the design workflow. Slots persist with the project file."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #888;")
        layout.addWidget(intro)

        self._scratchpad_status_labels.clear()
        self._scratchpad_paste_buttons.clear()

        for slot in self.scratchpad_manager.slots():
            row = QHBoxLayout()
            row.setSpacing(6)
            slot_label = QLabel(f"Slot {slot:02d}")
            row.addWidget(slot_label)

            status_label = QLabel("Empty")
            status_label.setObjectName(f"scratchpadStatus{slot}")
            status_label.setStyleSheet("color: #888;")
            row.addWidget(status_label)

            copy_btn = QPushButton("Copy")
            copy_btn.setToolTip("Copy the current composite frame into this scratchpad.")
            copy_btn.clicked.connect(lambda _=False, s=slot: self._copy_to_scratchpad(s))
            row.addWidget(copy_btn)

            paste_btn = QPushButton("Paste")
            paste_btn.setToolTip("Paste scratchpad contents into the active frame.")
            paste_btn.setEnabled(False)
            paste_btn.clicked.connect(lambda _=False, s=slot: self._paste_from_scratchpad(s))
            row.addWidget(paste_btn)

            clear_btn = QToolButton()
            clear_btn.setText("Clear")
            clear_btn.setToolTip("Remove stored pixels from this slot.")
            clear_btn.clicked.connect(lambda _=False, s=slot: self._clear_scratchpad_slot(s))
            row.addWidget(clear_btn)

            row.addStretch()
            layout.addLayout(row)

            self._scratchpad_status_labels[slot] = status_label
            self._scratchpad_paste_buttons[slot] = paste_btn

        layout.addStretch()
        self._refresh_scratchpad_status()
        return tab

    def _copy_to_scratchpad(self, slot: int) -> None:
        if not self._pattern:
            return
        pixels = self.layer_manager.get_composite_pixels(self._current_frame_index)
        self.scratchpad_manager.copy_pixels(slot, pixels)
        self._set_canvas_status(f"Scratchpad {slot:02d}: copied current frame.")

    def _paste_from_scratchpad(self, slot: int) -> None:
        if not self._pattern:
            return
        pixels = self.scratchpad_manager.get_pixels(slot)
        if not pixels:
            QMessageBox.information(self, "Scratchpad Empty", f"Slot {slot:02d} has no stored pixels.")
            return

        frame = self._pattern.frames[self._current_frame_index]
        before_pixels = list(frame.pixels)
        expected = self._pattern.metadata.width * self._pattern.metadata.height
        new_pixels = list(pixels[:expected])
        if len(new_pixels) < expected:
            new_pixels += [(0, 0, 0)] * (expected - len(new_pixels))

        self.layer_manager.replace_pixels(self._current_frame_index, new_pixels)
        self.layer_manager.sync_frame_from_layers(self._current_frame_index)
        self.canvas.set_frame_pixels(new_pixels)

        command = FrameStateCommand(
            self._current_frame_index,
            before_pixels,
            new_pixels,
            f"Paste scratchpad {slot:02d}",
        )
        self.history_manager.push_command(command, self._current_frame_index)
        self.pattern_modified.emit()
        self._set_canvas_status(f"Scratchpad {slot:02d}: applied to frame {self._current_frame_index + 1}.")

    def _clear_scratchpad_slot(self, slot: int) -> None:
        if not self.scratchpad_manager.is_slot_filled(slot):
            return
        self.scratchpad_manager.clear_slot(slot)
        self._set_canvas_status(f"Scratchpad {slot:02d}: cleared.")

    def _refresh_scratchpad_status(self, slot: Optional[int] = None) -> None:
        if not self._scratchpad_status_labels:
            return
        slots = [slot] if slot else self.scratchpad_manager.slots()
        for s in slots:
            label = self._scratchpad_status_labels.get(s)
            if not label:
                continue
            filled = self.scratchpad_manager.is_slot_filled(s)
            label.setText("Stored" if filled else "Empty")
            label.setStyleSheet("color: #4CAF50;" if filled else "color: #888;")
            paste_btn = self._scratchpad_paste_buttons.get(s)
            if paste_btn:
                paste_btn.setEnabled(filled)

    def _set_canvas_status(self, message: str) -> None:
        label = getattr(self, "canvas_status_label", None)
        if label:
            label.setText(message)

    def _mark_dirty(self):
        self._has_unsaved_changes = True

    def _mark_clean(self):
        self._has_unsaved_changes = False

    def _confirm_discard_changes(self) -> bool:
        if not self._has_unsaved_changes:
            return True
        response = QMessageBox.question(
            self,
            "Discard Unsaved Changes?",
            "Changes in the current design are unsaved. Do you want to discard them?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return response == QMessageBox.Yes

    def _create_layers_tab(self) -> QWidget:
        """Create the Layers tab with layer panel widget."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        
        # Create layer panel widget
        self.layer_panel = LayerPanelWidget(self.layer_manager, self)
        self.layer_panel.active_layer_changed.connect(self._on_active_layer_changed)
        self.layer_panel.solo_mode_changed.connect(self._on_solo_mode_changed)
        layout.addWidget(self.layer_panel)
        
        layout.addStretch()
        return tab

    def _create_effects_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.effects_widget = EffectsLibraryWidget()
        self.effects_widget.effectSelected.connect(self._on_effect_selection_changed)
        self.effects_widget.previewRequested.connect(self._on_effect_preview_requested)
        self.effects_widget.applyRequested.connect(self._on_effect_apply_requested)
        self.effects_widget.refreshRequested.connect(self._on_effects_refresh_requested)
        self.effects_widget.openFolderRequested.connect(self._on_effects_open_folder)
        layout.addWidget(self.effects_widget)

        self._effects_info_default = self.effects_widget.info_label.text()
        self._refresh_effects_library()
        return tab

    def _refresh_effects_library(self) -> None:
        if not self.effects_widget:
            return
        self.effects_library.reload()
        self.effects_widget.set_effects(self.effects_library.effects(), self.effects_library.categories())
        self._set_effect_info(self._effects_info_default)

    def _refresh_lms_frame_bindings(self) -> None:
        """
        Keep LMS binding combo boxes in sync with the current frame list.

        The LMS instruction builder uses combos such as ``lms_source_combo``,
        ``lms_layer2_combo`` and ``lms_mask_combo`` to let the user pick frame
        slots. These widgets may not exist yet (depending on which tab is open),
        so the method defensively checks for their presence.
        """
        # Defensive check: ensure pattern is Pattern object, not tuple
        if self._pattern and not isinstance(self._pattern, Pattern):
            return  # Pattern state corrupted, skip update
        frame_total = len(self._pattern.frames) if self._pattern and hasattr(self._pattern, 'frames') and self._pattern.frames else 0
        slots = [f"Frame{i + 1}" for i in range(frame_total)] or ["Frame1"]

        def _update_combo(combo: Optional[QComboBox]) -> None:
            if not combo:
                return
            current_text = combo.currentText() if combo.count() > 0 else None
            combo.blockSignals(True)
            combo.clear()
            include_none = bool(combo.property("includeNone"))
            if include_none:
                combo.addItem("None")
            combo.addItems(slots)
            if current_text:
                idx = combo.findText(current_text)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

        combos = [
            getattr(self, "lms_source_combo", None),
            getattr(self, "lms_layer2_combo", None),
            getattr(self, "lms_mask_combo", None),
        ]
        for combo in combos:
            _update_combo(combo)

    # ------------------------------------------------------------------
    # LMS helpers
    # ------------------------------------------------------------------
    def _frame_slot_to_index(self, slot: str) -> Optional[int]:
        try:
            if not slot:
                return None
            if slot.lower() == "none":
                return None
            if slot.lower().startswith("frame"):
                idx = int(slot.replace("Frame", "").strip()) - 1
                if idx >= 0:
                    return idx
        except (ValueError, AttributeError):
            return None
        return None

    def _binding_from_combo(self, combo: Optional[QComboBox], default_slot: str = "Frame1") -> Optional[LayerBinding]:
        if combo is None:
            return None
        text = combo.currentText().strip() if combo.currentText() else default_slot
        if combo.property("includeNone") and text.lower() == "none":
            return None
        frame_index = self._frame_slot_to_index(text)
        return LayerBinding(slot=text or default_slot, frame_index=frame_index)

    def _sync_lms_sequence_from_pattern(self) -> None:
        instructions = []
        if self._pattern and getattr(self._pattern, "lms_pattern_instructions", None):
            instructions = self._pattern.lms_pattern_instructions
        sequence = PatternInstructionSequence.from_list(instructions) if instructions else PatternInstructionSequence()
        self._set_lms_sequence(sequence, persist=False)

    def _set_lms_sequence(self, sequence: PatternInstructionSequence, persist: bool = True) -> None:
        self._lms_sequence = sequence
        self._persist_lms_sequence(emit_signal=persist)

    def _persist_lms_sequence(self, emit_signal: bool = True) -> None:
        if self._pattern is not None:
            self._pattern.lms_pattern_instructions = self._lms_sequence.to_list()
            if emit_signal:
                self.pattern_modified.emit()
        self._refresh_lms_sequence_views()

    def _refresh_lms_sequence_views(self) -> None:
        if self.lms_instruction_list is not None:
            self.lms_instruction_list.blockSignals(True)
            self.lms_instruction_list.clear()
            for instruction in self._lms_sequence:
                item = QListWidgetItem(self._format_lms_instruction(instruction))
                self.lms_instruction_list.addItem(item)
            self.lms_instruction_list.blockSignals(False)

        if self.lms_sequence_summary_label is not None:
            summary = self._lms_sequence.summarize() if self._lms_sequence else {"instruction_count": 0, "total_repeats": 0}
            instructions = summary.get("instruction_count", 0)
            repeats = summary.get("total_repeats", 0)
            unique = summary.get("unique_actions", [])
            self.lms_sequence_summary_label.setText(
                f"{instructions} instruction(s) • {repeats} repeat(s) • actions: {', '.join(unique) if unique else 'n/a'}"
            )

    def _format_lms_instruction(self, instruction: PatternInstruction) -> str:
        source = instruction.source.slot
        code = instruction.instruction.code
        repeat = instruction.instruction.repeat
        gap = instruction.instruction.gap
        parts = [f"{source} → {code}", f"repeat ×{repeat}"]
        if gap:
            parts.append(f"gap {gap}")
        if instruction.layer2:
            parts.append(f"L2 {instruction.layer2.slot}")
        if instruction.mask:
            parts.append(f"Mask {instruction.mask.slot}")
        return " • ".join(parts)

    def _log_lms_message(self, message: str) -> None:
        if self.lms_export_log:
            self.lms_export_log.appendPlainText(message)
        else:
            print(message)

    def _select_combo_text(self, combo: Optional[QComboBox], value: str) -> None:
        if combo is None or not value:
            return
        idx = combo.findText(value)
        if idx >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _set_effect_info(self, message: str) -> None:
        if self.effects_widget:
            self.effects_widget.info_label.setText(message)

    def _on_active_layer_changed(self, layer_index: int):
        """Handle active layer change from layer panel."""
        # Update canvas to show composite or active layer
        self._load_current_frame_into_canvas()
        if hasattr(self, "timeline"):
            self.timeline.set_selected_layer(layer_index)
        self._update_status_labels()  # Update layer status display
    
    def _on_solo_mode_changed(self, enabled: bool):
        """Handle solo mode toggle."""
        # Reload canvas to show only active layer when solo mode is on
        self._load_current_frame_into_canvas()
        self._update_status_labels()

    def _on_timeline_layer_selected(self, layer_index: int):
        """Handle layer row selection from timeline."""
        if not hasattr(self, "layer_panel") or not self.layer_panel:
            return
        layers = self.layer_manager.get_layers(self._current_frame_index) if self._pattern else []
        if not layers:
            return
        layer_index = max(0, min(layer_index, len(layers) - 1))
        self.layer_panel.set_active_layer(layer_index)

    def _create_appearance_group(self) -> QGroupBox:
        group = QGroupBox("Appearance")
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([name.title() for name in self.THEME_DEFINITIONS.keys()])
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(self._theme.title())
        self.theme_combo.blockSignals(False)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        layout.addWidget(self.theme_combo)
        layout.addStretch()

        autosave_row = QHBoxLayout()
        self.autosave_checkbox = QCheckBox("Enable autosave")
        self.autosave_checkbox.toggled.connect(self._on_autosave_toggled)
        autosave_row.addWidget(self.autosave_checkbox)
        autosave_row.addWidget(QLabel("Every"))
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(5)
        self.autosave_interval_spin.valueChanged.connect(self._on_autosave_interval_changed)
        autosave_row.addWidget(self.autosave_interval_spin)
        autosave_row.addWidget(QLabel("min"))
        autosave_row.addStretch()
        layout.addLayout(autosave_row)

        group.setLayout(layout)
        return group

    def _create_drawing_tools_group(self) -> QGroupBox:
        """Create drawing tools selection group."""
        group = QGroupBox("Drawing Tools")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Tool selection buttons
        tool_layout = QGridLayout()
        self.tool_button_group = QButtonGroup()
        
        # Pixel tool (default)
        pixel_btn = QPushButton("Pixel")
        pixel_btn.setCheckable(True)
        pixel_btn.setChecked(True)
        pixel_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.PIXEL))
        self.tool_button_group.addButton(pixel_btn, 0)
        tool_layout.addWidget(pixel_btn, 0, 0)

        # Rectangle tool
        rect_btn = QPushButton("Rectangle")
        rect_btn.setCheckable(True)
        rect_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.RECTANGLE))
        self.tool_button_group.addButton(rect_btn, 1)
        tool_layout.addWidget(rect_btn, 0, 1)

        # Circle tool
        circle_btn = QPushButton("Circle")
        circle_btn.setCheckable(True)
        circle_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.CIRCLE))
        self.tool_button_group.addButton(circle_btn, 2)
        tool_layout.addWidget(circle_btn, 1, 0)

        # Line tool
        line_btn = QPushButton("Line")
        line_btn.setCheckable(True)
        line_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.LINE))
        self.tool_button_group.addButton(line_btn, 3)
        tool_layout.addWidget(line_btn, 1, 1)

        random_btn = QPushButton("Random Spray")
        random_btn.setCheckable(True)
        random_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.RANDOM))
        self.tool_button_group.addButton(random_btn, 4)
        tool_layout.addWidget(random_btn, 2, 0)

        gradient_btn = QPushButton("Gradient Brush")
        gradient_btn.setCheckable(True)
        gradient_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.GRADIENT))
        self.tool_button_group.addButton(gradient_btn, 5)
        tool_layout.addWidget(gradient_btn, 2, 1)

        layout.addLayout(tool_layout)

        # Shape fill option
        self.shape_filled_checkbox = QCheckBox("Filled shapes")
        self.shape_filled_checkbox.setChecked(True)
        self.shape_filled_checkbox.setEnabled(False)  # Enabled when shape tool selected
        self.shape_filled_checkbox.toggled.connect(self._on_shape_filled_changed)
        layout.addWidget(self.shape_filled_checkbox)

        # Brush size selector
        brush_layout = QHBoxLayout()
        brush_layout.addWidget(QLabel("Brush Size:"))
        self.brush_size_spin = QSpinBox()
        self.brush_size_spin.setRange(1, 8)
        self.brush_size_spin.setValue(1)
        self.brush_size_spin.valueChanged.connect(self._on_brush_size_changed)
        brush_layout.addWidget(self.brush_size_spin)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        for size in [1, 2, 3, 4]:
            btn = QPushButton(f"{size}×{size}")
            btn.setFixedSize(40, 25)
            btn.clicked.connect(lambda checked=False, s=size: self._on_brush_preset_selected(s))
            preset_layout.addWidget(btn)
        brush_layout.addLayout(preset_layout)
        brush_layout.addStretch()
        layout.addLayout(brush_layout)

        self.brush_broadcast_checkbox = QCheckBox("Apply brush strokes to all frames")
        layout.addWidget(self.brush_broadcast_checkbox)

        group.setLayout(layout)
        return group

    def _on_tool_selected(self, mode: DrawingMode):
        """Handle tool selection."""
        if self.canvas:
            self.canvas.set_drawing_mode(mode)
            # Enable/disable filled checkbox based on tool
            self.shape_filled_checkbox.setEnabled(mode != DrawingMode.PIXEL and mode != DrawingMode.LINE)

    def _on_shape_filled_changed(self, checked: bool):
        """Handle shape filled toggle."""
        if self.canvas:
            self.canvas.set_shape_filled(checked)

    def _on_brush_size_changed(self, size: int):
        """Handle brush size change."""
        if self.canvas:
            self.canvas.set_brush_size(size)

    def _on_brush_preset_selected(self, size: int):
        """Handle brush preset selection."""
        self.brush_size_spin.setValue(size)

    def _create_palette_group(self) -> QGroupBox:
        group = QGroupBox("Palette & Brushes")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        swatch_grid = QGridLayout()
        for idx, color in enumerate(self.DEFAULT_COLORS):
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"background-color: rgb{color}; border: 1px solid #444;")
            btn.clicked.connect(lambda checked=False, c=color: self._on_palette_selected(c))
            row = idx // 4
            col = idx % 4
            swatch_grid.addWidget(btn, row, col)
        layout.addLayout(swatch_grid)

        current_row = QHBoxLayout()
        current_row.addWidget(QLabel("Current colour:"))
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self.color_preview.setStyleSheet("background-color: rgb(255,255,255); border: 1px solid #666;")
        current_row.addWidget(self.color_preview)
        
        # Color picker button
        self.color_picker_btn = QPushButton("Pick Color")
        self.color_picker_btn.setToolTip("Open color picker dialog")
        self.color_picker_btn.clicked.connect(self._on_color_picker_clicked)
        current_row.addWidget(self.color_picker_btn)
        
        current_row.addStretch()
        layout.addLayout(current_row)

        self.channel_sliders = {}
        for channel, idx in zip(("R", "G", "B"), range(3)):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"{channel}:"))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(self._current_color[idx])
            spin = QSpinBox()
            spin.setRange(0, 255)
            spin.setValue(self._current_color[idx])
            slider.valueChanged.connect(lambda val, ch=channel: self._on_channel_slider_changed(ch, val, source="slider"))
            spin.valueChanged.connect(lambda val, ch=channel: self._on_channel_slider_changed(ch, val, source="spin"))
            row_layout.addWidget(slider)
            row_layout.addWidget(spin)
            layout.addLayout(row_layout)
            self.channel_sliders[channel] = (slider, spin)

        self.gradient_group = self._create_gradient_group()
        layout.addWidget(self.gradient_group)

        self.single_color_notice = QLabel("")
        self.single_color_notice.setStyleSheet("color: #E5A24C; font-size: 11px;")
        self.single_color_notice.setWordWrap(True)
        self.single_color_notice.hide()
        layout.addWidget(self.single_color_notice)

        group.setLayout(layout)
        self._sync_channel_controls(self._current_color)
        self.gradient_start_btn.setStyleSheet(f"background-color: rgb{self._start_gradient_color};")
        self.gradient_end_btn.setStyleSheet(f"background-color: rgb{self._end_gradient_color};")
        self._sync_random_palette()
        self._sync_gradient_brush_settings()
        self._update_single_color_ui_state()
        return group

    def _create_gradient_group(self) -> QGroupBox:
        group = QGroupBox("Gradient")
        layout = QVBoxLayout()
        button_row = QHBoxLayout()
        self.gradient_start_btn = QPushButton("Start colour")
        self.gradient_start_btn.clicked.connect(lambda: self._choose_gradient_colour("start"))
        button_row.addWidget(self.gradient_start_btn)
        self.gradient_end_btn = QPushButton("End colour")
        self.gradient_end_btn.clicked.connect(lambda: self._choose_gradient_colour("end"))
        button_row.addWidget(self.gradient_end_btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Steps:"))
        self.gradient_steps_spin = QSpinBox()
        self.gradient_steps_spin.setRange(1, 512)
        self.gradient_steps_spin.setValue(32)
        self.gradient_steps_spin.valueChanged.connect(lambda _: self._sync_gradient_brush_settings())
        config_row.addWidget(self.gradient_steps_spin)
        config_row.addWidget(QLabel("Orientation:"))
        self.gradient_orientation_combo = QComboBox()
        self.gradient_orientation_combo.addItems(["Horizontal", "Vertical", "Radial"])
        config_row.addWidget(self.gradient_orientation_combo)
        config_row.addStretch()
        layout.addLayout(config_row)

        apply_btn = QPushButton("Apply Gradient To Frame")
        apply_btn.clicked.connect(self._apply_gradient_from_controls)
        layout.addWidget(apply_btn)

        group.setLayout(layout)
        return group

    def _update_single_color_ui_state(self):
        enabled = not self._single_color_mode
        if hasattr(self, "gradient_group"):
            self.gradient_group.setEnabled(enabled)
        if hasattr(self, "single_color_notice"):
            if enabled:
                self.single_color_notice.hide()
            else:
                self.single_color_notice.setText(
                    "Single-color mode is active. Advanced brushes and gradients use white only."
                )
                self.single_color_notice.show()

    def _sync_random_palette(self) -> None:
        if self.canvas:
            if self._single_color_mode:
                palette = [(255, 255, 255)] * 3
            else:
                palette = [self._current_color, self._start_gradient_color, self._end_gradient_color]
            self.canvas.set_random_palette(palette)

    def _sync_gradient_brush_settings(self) -> None:
        if self.canvas and hasattr(self, "gradient_steps_spin"):
            steps = max(2, self.gradient_steps_spin.value())
            self.canvas.set_gradient_brush(self._start_gradient_color, self._end_gradient_color, steps)

    def _create_text_animation_group(self) -> QGroupBox:
        """Create the text animation group for typed and animated text generation."""
        group = QGroupBox("Text Animation")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Text input
        text_input_row = QHBoxLayout()
        text_input_row.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text to animate...")
        self.text_input.textChanged.connect(self._on_text_input_changed)
        text_input_row.addWidget(self.text_input)
        layout.addLayout(text_input_row)

        # Animation type
        anim_type_row = QHBoxLayout()
        anim_type_row.addWidget(QLabel("Animation Type:"))
        self.text_animation_type_combo = QComboBox()
        self.text_animation_type_combo.addItems(["Typed (Character by Character)", "Scrolling Left", "Scrolling Right", "Scrolling Up", "Scrolling Down"])
        anim_type_row.addWidget(self.text_animation_type_combo)
        anim_type_row.addStretch()
        layout.addLayout(anim_type_row)

        # Font size (for simple bitmap font)
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font Size:"))
        self.text_font_size_spin = QSpinBox()
        self.text_font_size_spin.setRange(4, 16)
        self.text_font_size_spin.setValue(8)
        font_row.addWidget(self.text_font_size_spin)

        font_row.addWidget(QLabel("Font:"))
        self.text_font_combo = QComboBox()
        self.text_font_combo.currentIndexChanged.connect(self._on_text_font_changed)
        font_row.addWidget(self.text_font_combo, 1)

        font_designer_btn = QPushButton("Font Designer…")
        font_designer_btn.clicked.connect(self._open_font_designer)
        font_row.addWidget(font_designer_btn)
        layout.addLayout(font_row)
        self._refresh_font_combo()

        # Text color
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Text Color:"))
        self.text_color_btn = QPushButton("Select Color")
        self.text_color_btn.clicked.connect(self._choose_text_color)
        self.text_color_btn.setStyleSheet(f"background-color: rgb{self._current_color};")
        color_row.addWidget(self.text_color_btn)
        color_row.addStretch()
        layout.addLayout(color_row)

        # Speed/duration
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Frames per Character:"))
        self.text_frames_per_char_spin = QSpinBox()
        self.text_frames_per_char_spin.setRange(1, 10)
        self.text_frames_per_char_spin.setValue(2)
        speed_row.addWidget(self.text_frames_per_char_spin)
        speed_row.addStretch()
        layout.addLayout(speed_row)

        # Generate button
        generate_row = QHBoxLayout()
        self.generate_text_btn = QPushButton("Generate Text Frames")
        self.generate_text_btn.clicked.connect(self._on_generate_text_animation)
        self.generate_text_btn.setEnabled(False)
        generate_row.addWidget(self.generate_text_btn)
        generate_row.addStretch()
        layout.addLayout(generate_row)

        group.setLayout(layout)
        return group

    def _refresh_font_combo(self) -> None:
        if not hasattr(self, "text_font_combo"):
            return
        current_name = self.text_font_combo.currentData()
        self.text_font_combo.blockSignals(True)
        self.text_font_combo.clear()
        self.text_font_combo.addItem("Built-in 5×7", None)
        for name in self.font_repo.list_fonts():
            self.text_font_combo.addItem(name, name)
        self.text_font_combo.blockSignals(False)
        if current_name:
            idx = self.text_font_combo.findData(current_name)
            if idx >= 0:
                self.text_font_combo.setCurrentIndex(idx)
        self._on_text_font_changed(self.text_font_combo.currentIndex())

    def _on_text_font_changed(self, index: int) -> None:
        if not hasattr(self, "text_font_combo"):
            return
        font_name = self.text_font_combo.itemData(index)
        if not font_name:
            self._active_bitmap_font = None
            self.text_font_size_spin.setEnabled(True)
            return
        try:
            self._active_bitmap_font = self.font_repo.load_font(font_name)
        except FileNotFoundError:
            self._active_bitmap_font = None
        self.text_font_size_spin.setEnabled(self._active_bitmap_font is None)

    def _open_font_designer(self) -> None:
        dialog = FontDesignerDialog(self.font_repo, self)
        dialog.exec()
        self._refresh_font_combo()

    def _current_font_metrics(self) -> Tuple[int, int]:
        if self._active_bitmap_font:
            return self._active_bitmap_font.width, self._active_bitmap_font.height
        font_size = self.text_font_size_spin.value() if hasattr(self, "text_font_size_spin") else 8
        char_width = max(3, font_size // 2 + 1)
        char_height = max(5, font_size)
        return char_width, char_height

    def _on_text_input_changed(self, text: str):
        """Enable/disable generate button based on text input."""
        if hasattr(self, "generate_text_btn"):
            self.generate_text_btn.setEnabled(bool(text.strip()))

    def _choose_text_color(self):
        """Open color picker for text color."""
        color = QColorDialog.getColor(QColor(*self._current_color), self, "Select Text Color")
        if color.isValid():
            self._current_color = (color.red(), color.green(), color.blue())
            self.text_color_btn.setStyleSheet(f"background-color: rgb{self._current_color};")
            self._sync_channel_controls(self._current_color)

    def _on_generate_text_animation(self):
        """Generate animated text frames based on current settings."""
        text = self.text_input.text().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text to animate.")
            return

        if not self._pattern:
            self._create_default_pattern()

        anim_type = self.text_animation_type_combo.currentText()
        frames_per_char = self.text_frames_per_char_spin.value()
        font_size = self.text_font_size_spin.value()
        text_color = self._current_color

        frames = self._generate_text_frames(text, anim_type, frames_per_char, font_size, text_color)
        
        if frames:
            # Clear existing frames or append based on user preference
            if not self._pattern.frames:
                self._pattern.frames = frames
            else:
                reply = QMessageBox.question(
                    self,
                    "Append or Replace?",
                    "Do you want to append the new text frames to existing frames, or replace them?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self._pattern.frames.extend(frames)
                elif reply == QMessageBox.No:
                    self._pattern.frames = frames
                else:
                    return

            self.frame_manager.select(0)
            self._load_current_frame_into_canvas()
            self._refresh_timeline()
            self._update_status_labels()
            self.pattern_modified.emit()
            QMessageBox.information(self, "Success", f"Generated {len(frames)} text animation frames.")

    def _generate_text_frames(self, text: str, anim_type: str, frames_per_char: int, font_size: int, text_color: Tuple[int, int, int]) -> List[Frame]:
        """Generate frames for text animation."""
        width = self.width_spin.value() if hasattr(self, "width_spin") else self._pattern.metadata.width
        height = self.height_spin.value() if hasattr(self, "height_spin") else self._pattern.metadata.height
        
        frames: List[Frame] = []
        
        if "Typed" in anim_type:
            # Character-by-character typing effect
            for i in range(len(text) + 1):
                for _ in range(frames_per_char):
                    frame = Frame(duration_ms=self._frame_duration_ms, pixels=[])
                    frame.pixels = self._render_text_to_frame(text[:i], width, height, font_size, text_color)
                    frames.append(frame)
        elif "Scrolling" in anim_type:
            # Scrolling text animation
            direction = anim_type.split()[-1].lower()
            char_width = font_size // 2 + 1
            total_width = len(text) * char_width + width  # Extra width for scrolling
            
            if direction in ["left", "right"]:
                num_frames = total_width
                for frame_idx in range(num_frames):
                    frame = Frame(duration_ms=self._frame_duration_ms, pixels=[])
                    offset = frame_idx if direction == "left" else total_width - frame_idx - 1
                    frame.pixels = self._render_scrolling_text(text, width, height, font_size, text_color, offset, direction == "left")
                    frames.append(frame)
            else:  # up or down
                char_height = font_size + 2
                total_height = len(text) * char_height + height
                num_frames = total_height
                for frame_idx in range(num_frames):
                    frame = Frame(duration_ms=self._frame_duration_ms, pixels=[])
                    offset = frame_idx if direction == "down" else total_height - frame_idx - 1
                    frame.pixels = self._render_scrolling_text_vertical(text, width, height, font_size, text_color, offset, direction == "down")
                    frames.append(frame)
        else:
            # Default: simple typing
            for i in range(len(text) + 1):
                frame = Frame(duration_ms=self._frame_duration_ms, pixels=[])
                frame.pixels = self._render_text_to_frame(text[:i], width, height, font_size, text_color)
                frames.append(frame)
        
        return frames

    def _render_text_to_frame(self, text: str, width: int, height: int, font_size: int, color: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """Render text to a frame using simple bitmap font."""
        pixels = [(0, 0, 0)] * (width * height)
        
        if not text:
            return pixels
        
        # Simple 8x8 bitmap font (basic ASCII)
        char_width, char_height = self._current_font_metrics()
        
        # Center text horizontally
        text_width = len(text) * char_width
        start_x = max(0, (width - text_width) // 2)
        start_y = max(0, (height - char_height) // 2)
        
        for char_idx, char in enumerate(text):
            char_x = start_x + char_idx * char_width
            if char_x + char_width > width:
                break
            
            # Render simple character (5x7 pattern for each character)
            char_pattern = self._get_char_pattern(char)
            for py in range(min(char_height, height - start_y)):
                for px in range(min(char_width, width - char_x)):
                    if py < len(char_pattern) and px < len(char_pattern[py]):
                        if char_pattern[py][px]:
                            pixel_idx = (start_y + py) * width + (char_x + px)
                            if 0 <= pixel_idx < len(pixels):
                                pixels[pixel_idx] = color
        
        return pixels

    def _render_scrolling_text(self, text: str, width: int, height: int, font_size: int, color: Tuple[int, int, int], offset: int, scroll_left: bool) -> List[Tuple[int, int, int]]:
        """Render scrolling text horizontally."""
        pixels = [(0, 0, 0)] * (width * height)
        char_width, char_height = self._current_font_metrics()
        start_y = max(0, (height - char_height) // 2)
        
        for char_idx, char in enumerate(text):
            char_x = offset + char_idx * char_width
            if scroll_left:
                char_x = width - char_x - char_width
            
            if char_x + char_width < 0 or char_x >= width:
                continue
            
            char_pattern = self._get_char_pattern(char)
            for py in range(min(char_height, height - start_y)):
                for px in range(char_width):
                    screen_x = char_x + px
                    if 0 <= screen_x < width:
                        if py < len(char_pattern) and px < len(char_pattern[py]):
                            if char_pattern[py][px]:
                                pixel_idx = (start_y + py) * width + screen_x
                                if 0 <= pixel_idx < len(pixels):
                                    pixels[pixel_idx] = color
        
        return pixels

    def _render_scrolling_text_vertical(self, text: str, width: int, height: int, font_size: int, color: Tuple[int, int, int], offset: int, scroll_down: bool) -> List[Tuple[int, int, int]]:
        """Render scrolling text vertically."""
        pixels = [(0, 0, 0)] * (width * height)
        char_width, char_height = self._current_font_metrics()
        start_x = max(0, (width - char_width) // 2)
        
        for char_idx, char in enumerate(text):
            char_y = offset + char_idx * char_height
            if scroll_down:
                char_y = height - char_y - char_height
            
            if char_y + char_height < 0 or char_y >= height:
                continue
            
            char_pattern = self._get_char_pattern(char)
            for py in range(char_height):
                screen_y = char_y + py
                if 0 <= screen_y < height:
                    for px in range(min(char_width, width - start_x)):
                        if py < len(char_pattern) and px < len(char_pattern[py]):
                            if char_pattern[py][px]:
                                pixel_idx = screen_y * width + (start_x + px)
                                if 0 <= pixel_idx < len(pixels):
                                    pixels[pixel_idx] = color
        
        return pixels

    def _get_char_pattern(self, char: str) -> List[List[bool]]:
        """Get bitmap pattern for a character (5x7 grid). Extended ASCII support."""
        if getattr(self, "_active_bitmap_font", None):
            return self._active_bitmap_font.glyph(char)
        char_upper = char.upper()
        
        # Extended 5x7 bitmap font patterns
        patterns = {
            ' ': [[False] * 5 for _ in range(7)],
            '!': [
                [True],
                [True],
                [True],
                [True],
                [False],
                [True],
                [False],
            ],
            '"': [
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '#': [
                [False, True, False, True, False],
                [True, True, True, True, True],
                [False, True, False, True, False],
                [True, True, True, True, True],
                [False, True, False, True, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '$': [
                [False, True, True, True, False],
                [True, False, True, False, False],
                [False, True, True, True, False],
                [False, False, True, False, True],
                [False, True, True, True, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '%': [
                [True, False, False, False, True],
                [False, False, False, True, False],
                [False, False, True, False, False],
                [False, True, False, False, False],
                [True, False, False, False, True],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '&': [
                [False, True, True, False, False],
                [True, False, False, True, False],
                [False, True, True, False, False],
                [True, False, False, True, False],
                [False, True, True, False, True],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            "'": [
                [True],
                [True],
                [False],
                [False],
                [False],
                [False],
                [False],
            ],
            '(': [
                [False, False, True],
                [False, True, False],
                [True, False, False],
                [True, False, False],
                [False, True, False],
                [False, False, True],
                [False, False, False],
            ],
            ')': [
                [True, False, False],
                [False, True, False],
                [False, False, True],
                [False, False, True],
                [False, True, False],
                [True, False, False],
                [False, False, False],
            ],
            '*': [
                [False, False, True, False, False],
                [True, False, True, False, True],
                [False, True, True, True, False],
                [True, False, True, False, True],
                [False, False, True, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '+': [
                [False, False, False, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [True, True, True, True, True],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, False, False, False],
            ],
            ',': [
                [False],
                [False],
                [False],
                [False],
                [False],
                [True],
                [True],
            ],
            '-': [
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [True, True, True, True, True],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '.': [
                [False],
                [False],
                [False],
                [False],
                [False],
                [False],
                [True],
            ],
            '/': [
                [False, False, False, False, True],
                [False, False, False, True, False],
                [False, False, True, False, False],
                [False, True, False, False, False],
                [True, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '0': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, True, True],
                [True, False, True, False, True],
                [True, True, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            '1': [
                [False, False, True, False, False],
                [False, True, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, True, True, True, False],
            ],
            '2': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [False, False, False, False, True],
                [False, False, True, True, False],
                [False, True, False, False, False],
                [True, False, False, False, False],
                [True, True, True, True, True],
            ],
            '3': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [False, False, False, False, True],
                [False, True, True, True, False],
                [False, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            '4': [
                [False, False, False, True, False],
                [False, False, True, True, False],
                [False, True, False, True, False],
                [True, False, False, True, False],
                [True, True, True, True, True],
                [False, False, False, True, False],
                [False, False, False, True, False],
            ],
            '5': [
                [True, True, True, True, True],
                [True, False, False, False, False],
                [True, True, True, True, False],
                [False, False, False, False, True],
                [False, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            '6': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, False],
                [True, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            '7': [
                [True, True, True, True, True],
                [False, False, False, False, True],
                [False, False, False, True, False],
                [False, False, True, False, False],
                [False, True, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
            ],
            '8': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            '9': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, True],
                [False, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            ':': [
                [False],
                [False],
                [True],
                [False],
                [True],
                [False],
                [False],
            ],
            ';': [
                [False],
                [False],
                [True],
                [False],
                [True],
                [True],
                [False],
            ],
            '<': [
                [False, False, False, True],
                [False, False, True, False],
                [False, True, False, False],
                [True, False, False, False],
                [False, True, False, False],
                [False, False, True, False],
                [False, False, False, True],
            ],
            '=': [
                [False, False, False, False, False],
                [False, False, False, False, False],
                [True, True, True, True, True],
                [False, False, False, False, False],
                [True, True, True, True, True],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '>': [
                [True, False, False, False],
                [False, True, False, False],
                [False, False, True, False],
                [False, False, False, True],
                [False, False, True, False],
                [False, True, False, False],
                [True, False, False, False],
            ],
            '?': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [False, False, False, False, True],
                [False, False, True, True, False],
                [False, False, True, False, False],
                [False, False, False, False, False],
                [False, False, True, False, False],
            ],
            '@': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, True, True, True],
                [True, False, True, False, True],
                [True, False, True, True, True],
                [True, False, False, False, False],
                [False, True, True, True, False],
            ],
            'A': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, True, True, True, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
            ],
            'B': [
                [True, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, True, True, True, False],
            ],
            'C': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            'D': [
                [True, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, True, True, True, False],
            ],
            'E': [
                [True, True, True, True, True],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, True, True, True, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, True, True, True, True],
            ],
            'F': [
                [True, True, True, True, True],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, True, True, True, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
            ],
            'G': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, False],
                [True, False, True, True, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            'H': [
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, True, True, True, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
            ],
            'I': [
                [True, True, True],
                [False, True, False],
                [False, True, False],
                [False, True, False],
                [False, True, False],
                [False, True, False],
                [True, True, True],
            ],
            'J': [
                [False, False, True, True, True],
                [False, False, False, True, False],
                [False, False, False, True, False],
                [False, False, False, True, False],
                [True, False, False, True, False],
                [True, False, False, True, False],
                [False, True, True, False, False],
            ],
            'K': [
                [True, False, False, False, True],
                [True, False, False, True, False],
                [True, False, True, False, False],
                [True, True, False, False, False],
                [True, False, True, False, False],
                [True, False, False, True, False],
                [True, False, False, False, True],
            ],
            'L': [
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, True, True, True, True],
            ],
            'M': [
                [True, False, False, False, True],
                [True, True, False, True, True],
                [True, False, True, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
            ],
            'N': [
                [True, False, False, False, True],
                [True, True, False, False, True],
                [True, False, True, False, True],
                [True, False, False, True, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
            ],
            'O': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            'P': [
                [True, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, True, True, True, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
                [True, False, False, False, False],
            ],
            'Q': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, True, False, True],
                [True, False, False, True, False],
                [False, True, True, False, True],
            ],
            'R': [
                [True, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, True, True, True, False],
                [True, False, True, False, False],
                [True, False, False, True, False],
                [True, False, False, False, True],
            ],
            'S': [
                [False, True, True, True, False],
                [True, False, False, False, True],
                [True, False, False, False, False],
                [False, True, True, True, False],
                [False, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            'T': [
                [True, True, True, True, True],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
            ],
            'U': [
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, True, True, False],
            ],
            'V': [
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [False, True, False, True, False],
                [False, True, False, True, False],
                [False, False, True, False, False],
            ],
            'W': [
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, False, False, True],
                [True, False, True, False, True],
                [True, True, False, True, True],
                [True, False, False, False, True],
            ],
            'X': [
                [True, False, False, False, True],
                [False, True, False, True, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, True, False, True, False],
                [True, False, False, False, True],
            ],
            'Y': [
                [True, False, False, False, True],
                [False, True, False, True, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
                [False, False, True, False, False],
            ],
            'Z': [
                [True, True, True, True, True],
                [False, False, False, False, True],
                [False, False, False, True, False],
                [False, False, True, False, False],
                [False, True, False, False, False],
                [True, False, False, False, False],
                [True, True, True, True, True],
            ],
            '[': [
                [True, True, True],
                [True, False, False],
                [True, False, False],
                [True, False, False],
                [True, False, False],
                [True, False, False],
                [True, True, True],
            ],
            '\\': [
                [True, False, False, False, False],
                [False, True, False, False, False],
                [False, False, True, False, False],
                [False, False, False, True, False],
                [False, False, False, False, True],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            ']': [
                [True, True, True],
                [False, False, True],
                [False, False, True],
                [False, False, True],
                [False, False, True],
                [False, False, True],
                [True, True, True],
            ],
            '^': [
                [False, False, True, False, False],
                [False, True, False, True, False],
                [True, False, False, False, True],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
            ],
            '_': [
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [False, False, False, False, False],
                [True, True, True, True, True],
            ],
        }
        
        if char_upper in patterns:
            pattern = patterns[char_upper]
            # Normalize pattern to 5 columns
            normalized = []
            for row in pattern:
                if len(row) < 5:
                    normalized.append(row + [False] * (5 - len(row)))
                else:
                    normalized.append(row[:5])
            return normalized
        
        # Default: simple block pattern for unknown characters
        return [
            [True, True, True, True, True],
            [True, False, False, False, True],
            [True, False, False, False, True],
            [True, True, True, True, True],
            [True, False, False, False, True],
            [True, False, False, False, True],
            [True, True, True, True, True],
        ]

    def _create_automation_tab(self) -> QWidget:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        self.automation_mode_tabs = QTabWidget()
        self.automation_mode_tabs.setObjectName("automationModeTabs")
        self.automation_mode_tabs.addTab(self._create_legacy_automation_panel(), "Canvas Automation")
        self.automation_mode_tabs.addTab(self._create_lms_automation_panel(), "LMS Automation")
        container_layout.addWidget(self.automation_mode_tabs)
        return container

    def _create_legacy_automation_panel(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        self._action_combos: Dict[str, QComboBox] = {}
        layout.addWidget(self._create_automation_actions_group())
        layout.addWidget(self._create_apply_effect_group())
        layout.addWidget(self._create_action_queue_group(), stretch=1)
        layout.addWidget(self._create_action_inspector_group())
        layout.addWidget(self._create_processing_group())
        layout.addWidget(self._create_presets_group())
        layout.addStretch()
        return tab

    def _create_lms_automation_panel(self) -> QWidget:
        tab = QWidget()
        outer_layout = QVBoxLayout(tab)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(8)

        self.lms_feature_tabs = QTabWidget()
        self.lms_feature_tabs.setObjectName("lmsFeatureTabs")
        self.lms_feature_tabs.addTab(self._create_lms_builder_tab(), "Instruction Builder")
        self.lms_feature_tabs.addTab(self._create_lms_queue_tab(), "Queue & Preview")
        self.lms_feature_tabs.addTab(self._create_lms_export_tab(), "Import / Export")
        outer_layout.addWidget(self.lms_feature_tabs)
        return tab

    def _create_lms_builder_tab(self) -> QWidget:
        """Interactive LMS instruction builder UI."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        intro = QLabel(
            "Build MCU-ready LMS instructions without baking frames. Pick source frames, assign optional Layer 2 / mask bindings, "
            "choose an LMS action, then add it to the queue. Repeat controls how many times the MCU executes the instruction; "
            "Gap slows playback by inserting frame spacing."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #888;")
        layout.addWidget(intro)

        binding_group = QGroupBox("Layer Bindings")
        binding_form = QFormLayout()
        self.lms_source_combo = QComboBox()
        self.lms_source_combo.setObjectName("lmsSourceCombo")
        binding_form.addRow("Source (Layer 1)", self.lms_source_combo)

        self.lms_layer2_combo = QComboBox()
        self.lms_layer2_combo.setObjectName("lmsLayer2Combo")
        self.lms_layer2_combo.setProperty("includeNone", True)
        binding_form.addRow("Layer 2 (optional)", self.lms_layer2_combo)

        self.lms_mask_combo = QComboBox()
        self.lms_mask_combo.setObjectName("lmsMaskCombo")
        self.lms_mask_combo.setProperty("includeNone", True)
        binding_form.addRow("Mask (optional)", self.lms_mask_combo)
        binding_group.setLayout(binding_form)
        layout.addWidget(binding_group)

        action_group = QGroupBox("Instruction Parameters")
        action_form = QFormLayout()

        self.lms_action_combo = QComboBox()
        self.lms_action_combo.setObjectName("lmsActionCombo")
        for code, desc in sorted(KNOWN_LMS_ACTIONS.items()):
            self.lms_action_combo.addItem(f"{code} – {desc}", code)
        self.lms_action_combo.addItem("Custom…", None)
        self.lms_action_combo.currentIndexChanged.connect(self._on_lms_action_changed)
        action_form.addRow("Action", self.lms_action_combo)

        self.lms_custom_action_edit = QLineEdit()
        self.lms_custom_action_edit.setPlaceholderText("Enter custom MCU instruction code")
        self.lms_custom_action_edit.setEnabled(False)
        action_form.addRow("Custom code", self.lms_custom_action_edit)

        self.lms_repeat_spin = QSpinBox()
        self.lms_repeat_spin.setRange(1, 999)
        self.lms_repeat_spin.setValue(5)
        action_form.addRow("Repeat count", self.lms_repeat_spin)

        self.lms_gap_spin = QSpinBox()
        self.lms_gap_spin.setRange(0, 120)
        self.lms_gap_spin.setValue(0)
        self.lms_gap_spin.setSuffix(" frame(s)")
        action_form.addRow("Gap spacing", self.lms_gap_spin)

        self.lms_brightness_spin = QSpinBox()
        self.lms_brightness_spin.setRange(-255, 255)
        self.lms_brightness_spin.setValue(0)
        self.lms_brightness_spin.setSuffix(" Δ")
        action_form.addRow("Brightness delta", self.lms_brightness_spin)

        self.lms_params_edit = QLineEdit()
        self.lms_params_edit.setPlaceholderText('Optional JSON dict, e.g. {"speed": 2}')
        action_form.addRow("Extra params", self.lms_params_edit)

        action_group.setLayout(action_form)
        layout.addWidget(action_group)

        button_row = QHBoxLayout()
        add_btn = QPushButton("Add Instruction")
        add_btn.clicked.connect(self._on_lms_add_instruction)
        button_row.addWidget(add_btn)

        clear_btn = QPushButton("Reset Fields")
        clear_btn.clicked.connect(self._on_lms_clear_form)
        button_row.addWidget(clear_btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.lms_builder_status_label = QLabel("Select a source frame and action to begin.")
        self.lms_builder_status_label.setWordWrap(True)
        self.lms_builder_status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.lms_builder_status_label)

        layout.addStretch()
        self._refresh_lms_frame_bindings()
        return tab

    def _create_lms_queue_tab(self) -> QWidget:
        """Manage LMS instruction queue and preview output."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        help_label = QLabel(
            "The LMS queue mirrors the MCU playlist. Reorder instructions, duplicate segments, or preview the runtime animation "
            "without altering baked frames. Final exports pull directly from this list."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888;")
        layout.addWidget(help_label)

        self.lms_instruction_list = QListWidget()
        self.lms_instruction_list.setSelectionMode(QListWidget.SingleSelection)
        self.lms_instruction_list.currentRowChanged.connect(self._on_lms_instruction_selected)
        layout.addWidget(self.lms_instruction_list, stretch=1)

        controls_row = QHBoxLayout()
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._on_lms_remove_instruction)
        controls_row.addWidget(remove_btn)

        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self._on_lms_duplicate_instruction)
        controls_row.addWidget(duplicate_btn)

        up_btn = QPushButton("Move Up")
        up_btn.clicked.connect(lambda: self._on_lms_move_instruction(-1))
        controls_row.addWidget(up_btn)

        down_btn = QPushButton("Move Down")
        down_btn.clicked.connect(lambda: self._on_lms_move_instruction(1))
        controls_row.addWidget(down_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_lms_clear_sequence)
        controls_row.addWidget(clear_btn)
        controls_row.addStretch()
        layout.addLayout(controls_row)

        self.lms_sequence_summary_label = QLabel("No LMS instructions queued.")
        self.lms_sequence_summary_label.setWordWrap(True)
        layout.addWidget(self.lms_sequence_summary_label)

        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        preview_controls = QHBoxLayout()
        preview_btn = QPushButton("Preview Sequence")
        preview_btn.clicked.connect(self._on_lms_preview_sequence)
        preview_controls.addWidget(preview_btn)

        exit_btn = QPushButton("Exit Preview")
        exit_btn.clicked.connect(self._on_lms_exit_preview)
        preview_controls.addWidget(exit_btn)

        preview_controls.addWidget(QLabel("Max frames:"))
        self.lms_preview_limit_spin = QSpinBox()
        self.lms_preview_limit_spin.setRange(1, 240)
        self.lms_preview_limit_spin.setValue(60)
        preview_controls.addWidget(self.lms_preview_limit_spin)
        preview_controls.addStretch()
        preview_layout.addLayout(preview_controls)

        self.lms_preview_status_label = QLabel("Preview uses the current pattern as a source and never overwrites frames.")
        self.lms_preview_status_label.setWordWrap(True)
        self.lms_preview_status_label.setStyleSheet("color: #888;")
        preview_layout.addWidget(self.lms_preview_status_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        layout.addStretch()
        self._refresh_lms_sequence_views()
        return tab

    def _create_lms_export_tab(self) -> QWidget:
        """Provide LMS import/export utilities (LEDS, DAT, HEX, BIN)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        intro = QLabel(
            "Import LED Matrix Studio exports or save the current instruction queue as a .leds file. "
            "DAT/HEX/BIN analyzers inspect metadata so you can verify hardware settings before flashing."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #888;")
        layout.addWidget(intro)

        io_row = QHBoxLayout()
        import_btn = QPushButton("Import LEDS…")
        import_btn.clicked.connect(self._on_lms_import_leds)
        io_row.addWidget(import_btn)

        export_btn = QPushButton("Export LEDS…")
        export_btn.clicked.connect(self._on_lms_export_leds)
        io_row.addWidget(export_btn)
        io_row.addStretch()
        layout.addLayout(io_row)

        analysis_row = QHBoxLayout()
        analyze_dat_btn = QPushButton("Analyze DAT…")
        analyze_dat_btn.setToolTip(
            "Inspect a DAT file exported from LED Matrix Studio.\n"
            "Shows dimensions and basic metadata. Wiring and orientation are inferred\n"
            "later by auto-detect and may still need manual confirmation."
        )
        analyze_dat_btn.clicked.connect(lambda: self._on_lms_analyze_file("DAT"))
        analysis_row.addWidget(analyze_dat_btn)

        analyze_hex_btn = QPushButton("Analyze HEX…")
        analyze_hex_btn.setToolTip(
            "Inspect an Intel HEX file to estimate dimensions and pixel packing.\n"
            "Wiring/orientation are not encoded in HEX and will be treated as unknown."
        )
        analyze_hex_btn.clicked.connect(lambda: self._on_lms_analyze_file("HEX"))
        analysis_row.addWidget(analyze_hex_btn)

        analyze_bin_btn = QPushButton("Analyze BIN…")
        analyze_bin_btn.setToolTip(
            "Inspect a raw BIN file using shared layout heuristics.\n"
            "The reported layout includes a confidence score; low confidence means you\n"
            "should verify the preview carefully against hardware."
        )
        analyze_bin_btn.clicked.connect(lambda: self._on_lms_analyze_file("BIN"))
        analysis_row.addWidget(analyze_bin_btn)
        analysis_row.addStretch()
        layout.addLayout(analysis_row)

        # Quick links to relevant documentation
        help_row = QHBoxLayout()
        open_lms_docs_btn = QPushButton("Open LMS Automation Docs")
        open_lms_docs_btn.setToolTip("Open the LMS Automation reference (import/export, instruction semantics, preview).")
        open_lms_docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path('docs/automation/lms_automation.md').resolve()))))
        help_row.addWidget(open_lms_docs_btn)

        open_io_summary_btn = QPushButton("Open Auto-Detect Summary")
        open_io_summary_btn.setToolTip("Open the file format auto-detection and brightness summary.")
        open_io_summary_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path('AUTO_DETECT_AND_BRIGHTNESS_SUMMARY.md').resolve()))))
        help_row.addWidget(open_io_summary_btn)

        help_row.addStretch()
        layout.addLayout(help_row)

        self.lms_export_log = QPlainTextEdit()
        self.lms_export_log.setReadOnly(True)
        self.lms_export_log.setPlaceholderText("Import/export details and parser output will appear here.")
        layout.addWidget(self.lms_export_log, stretch=1)

        layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # LMS event handlers
    # ------------------------------------------------------------------
    def _on_lms_action_changed(self):
        if not self.lms_action_combo or not self.lms_custom_action_edit:
            return
        is_custom = self.lms_action_combo.currentData() is None
        self.lms_custom_action_edit.setEnabled(is_custom)
        if not is_custom:
            self.lms_custom_action_edit.clear()

    def _on_lms_clear_form(self):
        for combo in (self.lms_source_combo, self.lms_layer2_combo, self.lms_mask_combo):
            if combo and combo.count() > 0:
                combo.setCurrentIndex(0)
        if self.lms_action_combo:
            self.lms_action_combo.setCurrentIndex(0)
        if self.lms_repeat_spin:
            self.lms_repeat_spin.setValue(5)
        if self.lms_gap_spin:
            self.lms_gap_spin.setValue(0)
        if self.lms_brightness_spin:
            self.lms_brightness_spin.setValue(0)
        if self.lms_params_edit:
            self.lms_params_edit.clear()
        if self.lms_builder_status_label:
            self.lms_builder_status_label.setText("Fields reset. Configure a new instruction.")

    def _parse_lms_extra_params(self) -> Optional[Dict[str, object]]:
        if not self.lms_params_edit:
            return {}
        text = self.lms_params_edit.text().strip()
        if not text:
            return {}
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            QMessageBox.warning(self, "Invalid Parameters", f"Extra params must be valid JSON dict.\n{exc}")
            return None
        if not isinstance(payload, dict):
            QMessageBox.warning(self, "Invalid Parameters", "Extra params must decode to an object/dict.")
            return None
        return payload

    def _on_lms_add_instruction(self):
        if not self._pattern or not self._pattern.frames:
            QMessageBox.information(self, "No Frames", "Create or load a pattern before adding LMS instructions.")
            return

        source_binding = self._binding_from_combo(self.lms_source_combo)
        if not source_binding:
            QMessageBox.warning(self, "Source Required", "Select a source frame for Layer 1.")
            return

        layer2_binding = self._binding_from_combo(self.lms_layer2_combo)
        mask_binding = self._binding_from_combo(self.lms_mask_combo)

        action_code = ""
        if self.lms_action_combo:
            action_code = self.lms_action_combo.currentData() or ""
        if not action_code and self.lms_custom_action_edit:
            action_code = self.lms_custom_action_edit.text().strip()
        if not action_code:
            QMessageBox.warning(self, "Action Required", "Select or enter an LMS instruction code.")
            return

        params = self._parse_lms_extra_params()
        if params is None:
            return

        repeat = self.lms_repeat_spin.value() if self.lms_repeat_spin else 1
        gap = self.lms_gap_spin.value() if self.lms_gap_spin else 0
        brightness_delta = None
        if self.lms_brightness_spin:
            value = self.lms_brightness_spin.value()
            if value != 0:
                brightness_delta = value

        instruction = LMSInstruction(
            code=action_code,
            parameters=params or {},
            repeat=max(1, repeat),
            gap=max(0, gap),
            brightness_delta=brightness_delta,
        )
        pattern_instruction = PatternInstruction(
            source=source_binding,
            instruction=instruction,
            layer2=layer2_binding,
            mask=mask_binding,
        )
        self._lms_sequence.add(pattern_instruction)
        self._persist_lms_sequence()
        if self.lms_builder_status_label:
            self.lms_builder_status_label.setText(
                f"Added {action_code} • repeat ×{instruction.repeat} • source {source_binding.slot}"
            )

    def _on_lms_instruction_selected(self, row: int):
        if row < 0 or row >= len(self._lms_sequence):
            return
        instruction = self._lms_sequence[row]
        self._populate_lms_form_from_instruction(instruction)

    def _populate_lms_form_from_instruction(self, instruction: PatternInstruction):
        self._select_combo_text(self.lms_source_combo, instruction.source.slot)
        if instruction.layer2:
            self._select_combo_text(self.lms_layer2_combo, instruction.layer2.slot)
        if instruction.mask:
            self._select_combo_text(self.lms_mask_combo, instruction.mask.slot)
        if self.lms_repeat_spin:
            self.lms_repeat_spin.setValue(instruction.instruction.repeat)
        if self.lms_gap_spin:
            self.lms_gap_spin.setValue(instruction.instruction.gap)
        if self.lms_brightness_spin:
            self.lms_brightness_spin.setValue(instruction.instruction.brightness_delta or 0)
        if self.lms_params_edit:
            params = instruction.instruction.parameters or {}
            self.lms_params_edit.setText(json.dumps(params) if params else "")
        if self.lms_action_combo:
            code = instruction.instruction.code
            idx = self.lms_action_combo.findData(code)
            if idx >= 0:
                self.lms_action_combo.setCurrentIndex(idx)
            else:
                custom_index = self.lms_action_combo.findText("Custom…")
                if custom_index >= 0:
                    self.lms_action_combo.setCurrentIndex(custom_index)
                    if self.lms_custom_action_edit:
                        self.lms_custom_action_edit.setText(code)

    def _on_lms_remove_instruction(self):
        if not self.lms_instruction_list:
            return
        row = self.lms_instruction_list.currentRow()
        if row < 0:
            return
        self._lms_sequence.remove_at(row)
        self._persist_lms_sequence()

    def _on_lms_duplicate_instruction(self):
        if not self.lms_instruction_list:
            return
        row = self.lms_instruction_list.currentRow()
        if row < 0 or row >= len(self._lms_sequence):
            return
        clone = PatternInstruction.from_dict(self._lms_sequence[row].to_dict())
        self._lms_sequence.insert(row + 1, clone)
        self._persist_lms_sequence()
        self.lms_instruction_list.setCurrentRow(row + 1)

    def _on_lms_move_instruction(self, delta: int):
        if not self.lms_instruction_list:
            return
        current = self.lms_instruction_list.currentRow()
        if current < 0:
            return
        new_index = current + delta
        self._lms_sequence.move(current, new_index)
        self._persist_lms_sequence()
        self.lms_instruction_list.setCurrentRow(max(0, min(new_index, len(self._lms_sequence) - 1)))

    def _on_lms_clear_sequence(self):
        if not len(self._lms_sequence):
            return
        reply = QMessageBox.question(
            self,
            "Clear LMS Queue",
            "Remove all LMS instructions?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._lms_sequence.clear()
        self._persist_lms_sequence()

    def _on_lms_preview_sequence(self):
        if not self._pattern or not self._pattern.frames:
            QMessageBox.information(self, "No Pattern", "Load a pattern before previewing LMS instructions.")
            return
        if not len(self._lms_sequence):
            QMessageBox.information(self, "Empty Queue", "Add at least one LMS instruction first.")
            return
        if self._lms_preview_snapshot is not None:
            QMessageBox.information(self, "Preview Active", "Exit the current preview before starting another.")
            return

        limit = self.lms_preview_limit_spin.value() if self.lms_preview_limit_spin else None
        try:
            simulator = PreviewSimulator(self._pattern)
            preview_frames = simulator.simulate_sequence(self._lms_sequence, max_frames=limit)
        except Exception as exc:
            QMessageBox.warning(self, "Preview Failed", f"Unable to simulate instructions:\n{exc}")
            return

        if not preview_frames:
            QMessageBox.information(self, "No Preview Frames", "Simulator did not produce any frames.")
            return

        self._lms_preview_snapshot = self._pattern
        preview_pattern = Pattern(
            id=self._pattern.id,
            name=f"{self._pattern.name} (LMS Preview)",
            metadata=self._pattern.metadata,
            frames=preview_frames,
        )
        # Validate preview_pattern is Pattern object before assignment
        if not isinstance(preview_pattern, Pattern):
            raise TypeError(f"Expected Pattern, got {type(preview_pattern).__name__}: {preview_pattern}")
        self._pattern = preview_pattern
        self._current_frame_index = 0
        self._load_current_frame_into_canvas()
        self._refresh_timeline()
        if self.lms_preview_status_label:
            self.lms_preview_status_label.setText(
                f"Previewing {len(preview_frames)} frame(s). Click 'Exit Preview' to restore the original pattern."
            )

    def _on_lms_exit_preview(self):
        if not self._lms_preview_snapshot:
            if self.lms_preview_status_label:
                self.lms_preview_status_label.setText("No preview is active.")
            return
        # Validate _lms_preview_snapshot is Pattern object before restoring
        if not isinstance(self._lms_preview_snapshot, Pattern):
            raise TypeError(f"Expected Pattern, got {type(self._lms_preview_snapshot).__name__}: {self._lms_preview_snapshot}")
        self._pattern = self._lms_preview_snapshot
        self._lms_preview_snapshot = None
        self._current_frame_index = min(self._current_frame_index, len(self._pattern.frames) - 1)
        self._load_current_frame_into_canvas()
        self._refresh_timeline()
        if self.lms_preview_status_label:
            self.lms_preview_status_label.setText("Preview closed. Restored original pattern frames.")

    def _on_lms_import_leds(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import LEDS File",
            "",
            "LEDS Export (*.leds);;All Files (*)",
        )
        if not filepath:
            return
        path = Path(filepath)
        try:
            parsed = parse_leds_file(path)
        except (OSError, LMSFormatError) as exc:
            QMessageBox.warning(self, "Import Failed", f"Unable to parse LEDS file:\n{exc}")
            return
        sequence: PatternInstructionSequence = parsed.get("sequence", PatternInstructionSequence())
        self._set_lms_sequence(sequence)
        meta = parsed.get("metadata", {})
        message = f"Imported {sequence.summarize().get('instruction_count', 0)} instruction(s) from {path.name}."
        if meta:
            message += f" Metadata: {meta}"
        self._log_lms_message(message)
        QMessageBox.information(self, "LEDS Imported", message)

    def _on_lms_export_leds(self):
        if not len(self._lms_sequence):
            QMessageBox.information(self, "Empty Queue", "Add LMS instructions before exporting.")
            return
        if not self._pattern:
            QMessageBox.warning(self, "No Pattern", "Create or load a pattern before exporting.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export LEDS File",
            "",
            "LEDS Export (*.leds);;All Files (*)",
        )
        if not filepath:
            return
        path = Path(filepath)
        metadata = {
            "width": self._pattern.metadata.width,
            "height": self._pattern.metadata.height,
            "frames": len(self._pattern.frames),
            "format": getattr(self._pattern.metadata, "source_format", "RGB32") or "RGB32",
            "serpentine": getattr(self._pattern.metadata, "serpentine", False),
            "orientation": getattr(self._pattern.metadata, "orientation", "RowLeftToRight"),
            "color_order": getattr(self._pattern.metadata, "color_order", "RGB"),
        }
        try:
            write_leds_file(path, metadata, self._lms_sequence)
        except OSError as exc:
            QMessageBox.warning(self, "Export Failed", f"Unable to write LEDS file:\n{exc}")
            return
        self._log_lms_message(f"Exported LEDS file to {path} ({metadata['width']}×{metadata['height']}, {metadata['frames']} frame(s)).")
        QMessageBox.information(self, "LEDS Exported", f"Saved LMS instructions to {path}")

    def _on_lms_analyze_file(self, fmt: str):
        filters = {
            "DAT": "DAT Files (*.dat *.txt);;All Files (*)",
            "HEX": "HEX Files (*.hex);;All Files (*)",
            "BIN": "Binary Files (*.bin);;All Files (*)",
        }
        caption = f"Analyze {fmt} File"
        filepath, _ = QFileDialog.getOpenFileName(self, caption, "", filters.get(fmt, "All Files (*)"))
        if not filepath:
            return
        path = Path(filepath)
        try:
            if fmt == "DAT":
                parsed = parse_dat_file(path)
            elif fmt == "HEX":
                parsed = parse_hex_file(path)
            elif fmt == "BIN":
                payload = path.read_bytes()
                parsed = parse_bin_stream(payload)
            else:
                QMessageBox.warning(self, "Unsupported Format", f"Unknown analysis format {fmt}")
                return
        except (OSError, LMSFormatError) as exc:
            QMessageBox.warning(self, "Analysis Failed", f"Unable to parse {fmt} file:\n{exc}")
            return

        interesting_keys = [
            "format",
            "width",
            "height",
            "frame_count",
            "frames",
            "color_order",
            "bit_packing",
            "serpentine",
            "orientation",
            "metadata_source",
            "layout_confidence",
        ]
        summary = {k: v for k, v in parsed.items() if k in interesting_keys or isinstance(v, (int, float, str, bool))}
        # Provide a short human-readable note when wiring/orientation is unknown or the
        # layout confidence is low so users know they may need to adjust settings.
        notes: list[str] = []
        if parsed.get("serpentine") is None or parsed.get("orientation") is None:
            notes.append("wiring/orientation not encoded in file; use auto-detect + presets")
        confidence = parsed.get("layout_confidence")
        if isinstance(confidence, (int, float)) and confidence < 0.6:
            notes.append("layout confidence is low; double-check preview against hardware")
        note_text = f" Notes: {'; '.join(notes)}" if notes else ""
        message = f"{fmt} analysis for {path.name}: {summary}{note_text}"
        self._log_lms_message(message)
        QMessageBox.information(self, f"{fmt} Analysis", message)

    def _create_processing_group(self) -> QGroupBox:
        group = QGroupBox("Processing Range")
        layout = QVBoxLayout()

        self.source_button_group = QButtonGroup(self)
        use_first = QRadioButton("Use first frame as source")
        each_frame = QRadioButton("Use each frame independently")
        increment_frame = QRadioButton("Increment parameters per frame")
        use_first.setChecked(True)
        self.source_button_group.addButton(use_first, 0)
        self.source_button_group.addButton(each_frame, 1)
        self.source_button_group.addButton(increment_frame, 2)
        layout.addWidget(use_first)
        layout.addWidget(each_frame)
        layout.addWidget(increment_frame)

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Frame start:"))
        if not hasattr(self, "frame_start_spin"):
            self.frame_start_spin = QSpinBox()
            self.frame_start_spin.setMinimum(1)
            self.frame_start_spin.setValue(1)
            self.frame_start_spin.valueChanged.connect(lambda _: self._refresh_timeline())
        range_row.addWidget(self.frame_start_spin)
        range_row.addWidget(QLabel("Frame end:"))
        if not hasattr(self, "frame_end_spin"):
            self.frame_end_spin = QSpinBox()
            self.frame_end_spin.setMinimum(1)
            self.frame_end_spin.setValue(1)
            self.frame_end_spin.valueChanged.connect(lambda _: self._refresh_timeline())
        range_row.addWidget(self.frame_end_spin)
        range_row.addStretch()
        layout.addLayout(range_row)

        # Frame generation options
        gen_row = QHBoxLayout()
        self.generate_frames_checkbox = QCheckBox("Generate Frames")
        self.generate_frames_checkbox.setToolTip("Generate new frames by applying actions incrementally")
        gen_row.addWidget(self.generate_frames_checkbox)
        gen_row.addWidget(QLabel("Frame Count:"))
        self.generate_frame_count_spin = QSpinBox()
        self.generate_frame_count_spin.setRange(1, 1000)
        self.generate_frame_count_spin.setValue(10)
        self.generate_frame_count_spin.setEnabled(False)
        self.generate_frames_checkbox.toggled.connect(self.generate_frame_count_spin.setEnabled)
        gen_row.addWidget(self.generate_frame_count_spin)
        gen_row.addStretch()
        layout.addLayout(gen_row)

        group.setLayout(layout)
        return group

    def _create_automation_actions_group(self) -> QGroupBox:
        group = QGroupBox("Automation Actions")
        layout = QVBoxLayout()

        wizard_row = QHBoxLayout()
        wizard_btn = QPushButton("Automation Wizard…")
        wizard_btn.setToolTip("Open guided wizard to stack actions and apply fades/overlays.")
        wizard_btn.clicked.connect(self._open_automation_wizard)
        wizard_row.addWidget(wizard_btn)
        wizard_row.addStretch()
        layout.addLayout(wizard_row)

        layout.addLayout(self._make_action_row("Scroll", ["Up", "Down", "Left", "Right"], self._add_scroll_action))
        layout.addLayout(self._make_action_row("Wipe", ["Left to Right", "Right to Left", "Top to Bottom", "Bottom to Top"], self._add_wipe_action))
        layout.addLayout(self._make_action_row("Reveal", ["Left", "Right", "Top", "Bottom"], self._add_reveal_action))
        layout.addLayout(self._make_action_row("Bounce", ["Horizontal", "Vertical"], self._add_bounce_action))
        layout.addLayout(self._make_action_row("Rotate", ["90° Clockwise", "90° Counter-clockwise"], self._add_rotate_action))
        layout.addLayout(self._make_action_row("Mirror", ["Horizontal", "Vertical"], self._add_mirror_action))
        layout.addLayout(self._make_action_row("Colour Cycle", ["RGB", "RYB", "Custom"], self._add_colour_cycle_action))
        layout.addLayout(self._make_action_row("Radial", ["Spiral", "Pulse", "Sweep"], self._add_radial_action))

        invert_row = QHBoxLayout()
        invert_btn = QPushButton("Invert Colours")
        invert_btn.clicked.connect(lambda: self._queue_action("Invert Colours", "invert", {}))
        invert_row.addWidget(invert_btn)
        invert_row.addStretch()
        layout.addLayout(invert_row)

        group.setLayout(layout)
        return group

    def _make_action_row(self, label: str, options: List[str], callback):
        row = QHBoxLayout()
        row.addWidget(QLabel(f"{label}:"))
        combo = QComboBox()
        combo.addItems(options)
        row.addWidget(combo)
        add_btn = QPushButton("Add")
        row.addWidget(add_btn)
        add_btn.clicked.connect(lambda: callback(combo.currentText()))
        row.addStretch()
        self._action_combos[label] = combo
        return row

    def _add_scroll_action(self, direction: str):
        """Add scroll action to queue."""
        self._queue_action(f"Scroll {direction}", "scroll", {"direction": direction, "offset": 1})

    def _add_wipe_action(self, mode: str):
        """Add wipe action to queue."""
        self._queue_action(f"Wipe {mode}", "wipe", {"mode": mode, "offset": 1})

    def _add_reveal_action(self, direction: str):
        """Add reveal action to queue."""
        self._queue_action(f"Reveal {direction}", "reveal", {"direction": direction, "offset": 1})

    def _add_bounce_action(self, axis: str):
        """Add bounce action to queue."""
        self._queue_action(f"Bounce {axis}", "bounce", {"axis": axis})

    def _add_rotate_action(self, mode: str):
        """Add rotate action to queue."""
        self._queue_action(f"Rotate {mode}", "rotate", {"mode": mode})

    def _add_mirror_action(self, axis: str):
        """Add mirror action to queue."""
        self._queue_action(f"Mirror {axis}", "mirror", {"axis": axis})

    def _add_colour_cycle_action(self, mode: str):
        """Add colour cycle action to queue."""
        self._queue_action(f"Colour Cycle {mode}", "colour_cycle", {"mode": mode})

    def _add_radial_action(self, type: str):
        """Add radial action to queue."""
        self._queue_action(f"Radial {type}", "radial", {"type": type})

    def _apply_linear_fade(self, fade_in: bool) -> None:
        if not self._pattern or not self._pattern.frames:
            return
        total = len(self._pattern.frames)
        if total == 0:
            return
        denom = max(1, total - 1)
        for idx, frame in enumerate(self._pattern.frames):
            t = idx / denom
            factor = t if fade_in else (1.0 - t)
            factor = max(0.05, min(1.0, factor))
            new_pixels = [
                (
                    int(max(0, min(255, pixel[0] * factor))),
                    int(max(0, min(255, pixel[1] * factor))),
                    int(max(0, min(255, pixel[2] * factor))),
                )
                for pixel in frame.pixels
            ]
            frame.pixels = new_pixels
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._update_status_labels()

    def _duplicate_frames_to_overlay(self) -> None:
        if not self._pattern or not self._pattern.frames:
            return
        for frame_index in range(len(self._pattern.frames)):
            layer_index = self.layer_manager.add_layer(frame_index, name="Overlay")
            pixels = list(self._pattern.frames[frame_index].pixels)
            self.layer_manager.replace_pixels(frame_index, pixels, layer_index=layer_index)
        self.layer_manager.sync_all_frames_from_layers()
        self._refresh_timeline()
        self.pattern_modified.emit()

    def _create_apply_effect_group(self) -> QGroupBox:
        """Create the Apply Effect UI group with preview and commit options."""
        group = QGroupBox("Apply Effect")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Effect type selection
        effect_type_row = QHBoxLayout()
        effect_type_row.addWidget(QLabel("Effect Type:"))
        self.effect_type_combo = QComboBox()
        self.effect_type_combo.addItems(["Automation Actions", "Animated Text", "Custom Effect"])
        self.effect_type_combo.currentTextChanged.connect(self._on_effect_type_changed)
        effect_type_row.addWidget(self.effect_type_combo)
        effect_type_row.addStretch()
        layout.addLayout(effect_type_row)

        # Preview button
        preview_row = QHBoxLayout()
        self.preview_effect_btn = QPushButton("👁 Preview Effect")
        self.preview_effect_btn.clicked.connect(self._on_preview_effect)
        preview_row.addWidget(self.preview_effect_btn)
        preview_row.addStretch()
        layout.addLayout(preview_row)

        # Preview status label
        self.effect_preview_status = QLabel()
        self.effect_preview_status.setWordWrap(True)
        self.effect_preview_status.setStyleSheet("color: #888; font-style: italic;")
        self.effect_preview_status.hide()
        layout.addWidget(self.effect_preview_status)

        # Apply and Finalize buttons
        apply_row = QHBoxLayout()
        self.apply_effect_btn = QPushButton("✓ Apply Effect")
        self.apply_effect_btn.setEnabled(False)
        self.apply_effect_btn.clicked.connect(self._on_apply_effect)
        apply_row.addWidget(self.apply_effect_btn)
        
        self.finalize_automation_btn = QPushButton("✓ Finalize Automation")
        self.finalize_automation_btn.setToolTip("Convert automation actions to LMS pattern instructions for MCU export")
        self.finalize_automation_btn.clicked.connect(lambda: self._apply_actions_to_frames(finalize=True))
        apply_row.addWidget(self.finalize_automation_btn)
        
        apply_row.addStretch()
        layout.addLayout(apply_row)

        # Effect description
        self.effect_description_label = QLabel()
        self.effect_description_label.setWordWrap(True)
        self.effect_description_label.setStyleSheet("color: #AAA; font-size: 9pt;")
        layout.addWidget(self.effect_description_label)

        group.setLayout(layout)
        self._update_effect_description()
        return group

    def _on_effect_type_changed(self, effect_type: str):
        """Handle effect type selection change."""
        self._update_effect_description()
        self.apply_effect_btn.setEnabled(False)
        self.effect_preview_status.hide()

    def _update_effect_description(self):
        """Update the effect description label based on current selection."""
        effect_type = self.effect_type_combo.currentText() if hasattr(self, "effect_type_combo") else "Automation Actions"
        descriptions = {
            "Automation Actions": "Apply queued automation actions (scroll, rotate, mirror, etc.) to selected frame range.",
            "Animated Text": "Generate animated text frames with typing effect or scrolling text animation.",
            "Custom Effect": "Apply custom effect transformations (fade, blur, sharpen, brightness, contrast, color shift, noise, pixelate)."
        }
        if hasattr(self, "effect_description_label"):
            self.effect_description_label.setText(descriptions.get(effect_type, ""))

    # ------------------------------------------------------------------
    # Effects library handlers
    # ------------------------------------------------------------------

    def _on_effect_selection_changed(self, effect: EffectDefinition | None):
        if effect is None:
            self._set_effect_info(self._effects_info_default)
        else:
            self._set_effect_info(f"Selected effect: {effect.name} • {effect.category}")

    def _on_effect_preview_requested(self, effect: EffectDefinition, intensity: float):
        self._preview_effect_definition(effect, intensity)

    def _on_effect_apply_requested(self, effect: EffectDefinition, intensity: float):
        self._apply_effect_definition(effect, intensity)

    def _on_effects_refresh_requested(self):
        self._refresh_effects_library()

    def _on_effects_open_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.effects_library.root.resolve())))

    def _restore_pattern_after_preview(self, original_pattern: Pattern):
        """Restore the original pattern after preview."""
        if hasattr(self, "_pattern") and self._pattern:
            if "(Preview)" in self._pattern.name:
                # Validate pattern is Pattern object before assignment
                if not isinstance(original_pattern, Pattern):
                    raise TypeError(f"Expected Pattern, got {type(original_pattern).__name__}: {original_pattern}")
                self._pattern = original_pattern
                self._current_frame_index = min(self._current_frame_index, len(self._pattern.frames) - 1)
                self._load_current_frame_into_canvas()
                self._refresh_timeline()

    def _on_preview_effect(self):
        """Preview the effect before applying."""
        effect_type = self.effect_type_combo.currentText()
        
        if effect_type == "Automation Actions":
            actions = self.automation_manager.actions()
            if not actions:
                QMessageBox.information(self, "No Actions", "Add actions to the queue first.")
                return
            
            if not self._pattern or not self._pattern.frames:
                QMessageBox.information(self, "No Pattern", "Create or load a pattern first.")
                return
            
            # Convert actions to pattern instructions and simulate
            sequence = PatternInstructionSequence()
            start = self.frame_start_spin.value() - 1 if hasattr(self, "frame_start_spin") else 0
            for action in actions:
                instruction = self._convert_action_to_instruction(action, start)
                sequence.add(instruction)
            
            # Use preview simulator to generate preview frames
            simulator = PreviewSimulator(self._pattern)
            preview_frames = simulator.simulate_sequence(sequence, max_frames=50)
            
            if not preview_frames:
                QMessageBox.information(self, "Preview", "No preview frames generated.")
                return
            
            # Show preview in canvas (temporarily replace pattern)
            original_pattern = self._pattern
            self._pattern = Pattern(
                id=original_pattern.id,
                name=f"{original_pattern.name} (Preview)",
                metadata=original_pattern.metadata,
                frames=preview_frames
            )
            self._current_frame_index = 0
            self._load_current_frame_into_canvas()
            self._refresh_timeline()
            
            # Restore original pattern after showing preview
            QTimer.singleShot(1000, lambda: self._restore_pattern_after_preview(original_pattern))
            
            self.effect_preview_status.setText(
                f"Preview: Generated {len(preview_frames)} frame(s) from {len(actions)} instruction(s). "
                "Click 'Finalize Automation' to convert to pattern instructions."
            )
            self.effect_preview_status.show()
            self.apply_effect_btn.setEnabled(True)
            self.finalize_automation_btn.setEnabled(True)
            
        elif effect_type == "Animated Text":
            if not hasattr(self, "text_input") or not self.text_input.text().strip():
                QMessageBox.information(self, "No Text", "Enter text in the Text Animation section first.")
                return
            
            text = self.text_input.text().strip()
            self.effect_preview_status.setText(f"Preview: Will generate animated text frames for '{text}'. Click 'Apply Effect' to generate.")
            self.effect_preview_status.show()
            self.apply_effect_btn.setEnabled(True)
        elif effect_type == "Custom Effect":
            # Custom effects dialog
            from PySide6.QtWidgets import QDialog, QDialogButtonBox, QComboBox as QCombo
            
            custom_dialog = QDialog(self)
            custom_dialog.setWindowTitle("Custom Effect")
            custom_layout = QVBoxLayout(custom_dialog)
            
            effect_combo = QCombo()
            effect_combo.addItems([
                "Fade In/Out",
                "Blur",
                "Sharpen",
                "Brightness Adjust",
                "Contrast Adjust",
                "Color Shift",
                "Noise",
                "Pixelate"
            ])
            custom_layout.addWidget(QLabel("Effect Type:"))
            custom_layout.addWidget(effect_combo)
            
            intensity_label = QLabel("Intensity:")
            intensity_spin = QSpinBox()
            intensity_spin.setRange(1, 100)
            intensity_spin.setValue(50)
            intensity_row = QHBoxLayout()
            intensity_row.addWidget(intensity_label)
            intensity_row.addWidget(intensity_spin)
            custom_layout.addLayout(intensity_row)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(custom_dialog.accept)
            buttons.rejected.connect(custom_dialog.reject)
            custom_layout.addWidget(buttons)
            
            if custom_dialog.exec() == QDialog.Accepted:
                effect_name = effect_combo.currentText()
                intensity = intensity_spin.value()
                self._preview_custom_effect(effect_name, intensity)
                self._pending_custom_effect = (effect_name, intensity)
                self.effect_preview_status.setText(f"Preview: Custom effect '{effect_name}' (intensity: {intensity}%). Click 'Apply Effect' to commit.")
                self.effect_preview_status.show()
                self.apply_effect_btn.setEnabled(True)

    def _on_apply_effect(self):
        """Apply the effect to the pattern."""
        effect_type = self.effect_type_combo.currentText()
        
        if effect_type == "Automation Actions":
            self._apply_actions_to_frames(finalize=False)
            self.effect_preview_status.hide()
            self.apply_effect_btn.setEnabled(False)
        elif effect_type == "Animated Text":
            self._on_generate_text_animation()
            self.effect_preview_status.hide()
            self.apply_effect_btn.setEnabled(False)
        elif effect_type == "Custom Effect":
            # Apply custom effect that was previewed
            if hasattr(self, '_pending_custom_effect'):
                effect_name, intensity = self._pending_custom_effect
                self._apply_custom_effect(effect_name, intensity)
                delattr(self, '_pending_custom_effect')
                self.effect_preview_status.hide()
                self.apply_effect_btn.setEnabled(False)
                self.pattern_modified.emit()
                self._load_current_frame_into_canvas()
                self._update_status_labels()
                self._refresh_timeline()

    def _preview_effect_definition(self, effect: EffectDefinition, intensity: float):
        """Preview a library effect on the current frame without committing."""
        if not self._pattern or not self._pattern.frames:
            return

        if not hasattr(self, "_effects_preview_backup"):
            self._effects_preview_backup = copy.deepcopy(self._pattern)

        temp_pattern = copy.deepcopy(self._effects_preview_backup)
        frame_index = self._current_frame_index
        apply_effect_to_frames(temp_pattern, effect, [frame_index], intensity)

        original = self._pattern
        # Validate temp_pattern is Pattern object before assignment
        if not isinstance(temp_pattern, Pattern):
            raise TypeError(f"Expected Pattern, got {type(temp_pattern).__name__}: {temp_pattern}")
        self._pattern = temp_pattern
        self._load_current_frame_into_canvas()
        # Validate original is Pattern object before restoring
        if not isinstance(original, Pattern):
            raise TypeError(f"Expected Pattern, got {type(original).__name__}: {original}")
        self._pattern = original
        self._set_effect_info(f"Previewed: {effect.name} on frame {frame_index + 1}")

    def _apply_effect_definition(self, effect: EffectDefinition, intensity: float):
        """Apply an effect to the selected frame range and push to history."""
        if not self._pattern or not self._pattern.frames:
            QMessageBox.information(self, "No Pattern", "Create or load a pattern before applying effects.")
            return

        self._commit_paint_operation()
        total_frames = len(self._pattern.frames)
        start = max(0, self.frame_start_spin.value() - 1)
        end = min(total_frames - 1, self.frame_end_spin.value() - 1)
        if end < start:
            start, end = end, start
        frame_indices = list(range(start, end + 1))
        if not frame_indices:
            return

        before_states: Dict[int, List[Tuple[int, int, int]]] = {
            idx: list(self._pattern.frames[idx].pixels)
            for idx in frame_indices
        }

        apply_effect_to_frames(self._pattern, effect, frame_indices, intensity)

        any_changes = False
        for idx in frame_indices:
            frame = self._pattern.frames[idx]
            after_pixels = list(frame.pixels)
            before_pixels = before_states[idx]
            if after_pixels != before_pixels:
                command = FrameStateCommand(
                    idx,
                    before_pixels,
                    after_pixels,
                    f"Effect: {effect.name}",
                )
                self.history_manager.push_command(command, idx)
                any_changes = True

        if any_changes:
            self.pattern_modified.emit()
            self._load_current_frame_into_canvas()
            self._refresh_timeline()
            self._maybe_autosync_preview()
            self._set_effect_info(
                f"Applied: {effect.name} • frames {start + 1}-{end + 1} at {int(intensity * 100)}%"
            )
        else:
            self._set_effect_info("Effect produced no visible changes.")

        if hasattr(self, "_effects_preview_backup"):
            delattr(self, "_effects_preview_backup")

    def _create_action_queue_group(self) -> QGroupBox:
        group = QGroupBox("Action Queue")
        layout = QVBoxLayout()
        self.action_list = QListWidget()
        self.action_list.currentRowChanged.connect(self._on_action_list_selection)
        layout.addWidget(self.action_list)

        button_row = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._on_remove_action)
        button_row.addWidget(remove_btn)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_actions)
        button_row.addWidget(clear_btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.apply_actions_btn = QPushButton("▶ Apply Actions")
        self.apply_actions_btn.clicked.connect(lambda: self._apply_actions_to_frames(finalize=False))
        self.apply_actions_btn.setEnabled(False)
        layout.addWidget(self.apply_actions_btn)

        self.finalize_actions_btn = QPushButton("✓ Finalize Playlist")
        self.finalize_actions_btn.setToolTip("Commit actions to frames, clear the queue, and lock in timing")
        self.finalize_actions_btn.clicked.connect(lambda: self._apply_actions_to_frames(finalize=True))
        self.finalize_actions_btn.setEnabled(False)
        layout.addWidget(self.finalize_actions_btn)

        group.setLayout(layout)
        return group

    def _create_action_inspector_group(self) -> QGroupBox:
        group = QGroupBox("Action Details")
        layout = QVBoxLayout()

        details_form = QFormLayout()
        details_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.action_name_edit = QLineEdit()
        self.action_name_edit.editingFinished.connect(self._on_action_name_edited)
        details_form.addRow("Name", self.action_name_edit)
        self.action_type_label = QLabel("-")
        self.action_type_label.setObjectName("ActionTypeLabel")
        details_form.addRow("Action Type", self.action_type_label)
        layout.addLayout(details_form)

        self.action_param_container = QWidget()
        self.action_param_layout = QFormLayout()
        self.action_param_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.action_param_container.setLayout(self.action_param_layout)
        layout.addWidget(self.action_param_container)

        self.action_validation_label = QLabel()
        self.action_validation_label.setObjectName("ActionValidationLabel")
        self.action_validation_label.setWordWrap(True)
        self.action_validation_label.hide()
        layout.addWidget(self.action_validation_label)

        self.action_preview_label = QLabel()
        self.action_preview_label.setObjectName("ActionPreviewLabel")
        self.action_preview_label.setWordWrap(True)
        self.action_preview_label.hide()
        layout.addWidget(self.action_preview_label)

        schedule_group = QGroupBox("Schedule")
        schedule_layout = QFormLayout()
        schedule_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.action_repeat_spin = QSpinBox()
        self.action_repeat_spin.setRange(1, 500)
        self.action_repeat_spin.setToolTip("How many times to apply this action per frame")
        self.action_repeat_spin.valueChanged.connect(self._on_action_repeat_changed)
        schedule_layout.addRow("Repeat Count", self.action_repeat_spin)

        self.action_gap_spin = QSpinBox()
        self.action_gap_spin.setRange(0, 5000)
        self.action_gap_spin.setSuffix(" ms")
        self.action_gap_spin.setSingleStep(50)
        self.action_gap_spin.setToolTip("Additional delay (milliseconds) after applying this action")
        self.action_gap_spin.valueChanged.connect(self._on_action_gap_changed)
        schedule_layout.addRow("Gap / Pause", self.action_gap_spin)

        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        self.action_schedule_group = schedule_group

        self.action_parameter_widgets = {}
        self._param_error_labels = {}
        self._param_description_labels = {}
        self._param_error_state = {}
        self._updating_action_inspector = False
        group.setLayout(layout)
        self.action_inspector_group = group
        return group

    def _create_presets_group(self) -> QGroupBox:
        group = QGroupBox("Automation Presets")
        layout = QVBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setEditable(True)
        self.preset_combo.setInsertPolicy(QComboBox.NoInsert)
        self.preset_combo.lineEdit().setPlaceholderText("Preset name")
        layout.addWidget(self.preset_combo)

        button_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save_preset)
        button_row.addWidget(save_btn)
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._on_apply_preset)
        button_row.addWidget(apply_btn)
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._on_preview_preset)
        button_row.addWidget(preview_btn)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._on_delete_preset)
        button_row.addWidget(delete_btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        manage_row = QHBoxLayout()
        duplicate_btn = QToolButton()
        duplicate_btn.setText("Duplicate")
        duplicate_btn.clicked.connect(self._on_duplicate_preset)
        manage_row.addWidget(duplicate_btn)
        rename_btn = QToolButton()
        rename_btn.setText("Rename")
        rename_btn.clicked.connect(self._on_rename_preset)
        manage_row.addWidget(rename_btn)
        export_btn = QToolButton()
        export_btn.setText("Export")
        export_btn.clicked.connect(self._on_export_preset)
        manage_row.addWidget(export_btn)
        import_btn = QToolButton()
        import_btn.setText("Import")
        import_btn.clicked.connect(self._on_import_preset)
        manage_row.addWidget(import_btn)
        manage_row.addStretch()
        layout.addLayout(manage_row)

        group.setLayout(layout)
        return group

    def _create_export_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.addWidget(self._create_import_group())
        layout.addWidget(self._create_matrix_configuration_group())
        layout.addWidget(self._create_pattern_export_group())
        layout.addWidget(self._create_code_template_group())
        layout.addWidget(self._create_export_summary_group())
        layout.addStretch()
        return tab

    def _create_pattern_export_group(self) -> QGroupBox:
        group = QGroupBox("Pattern Export")
        layout = QVBoxLayout()
        self.pattern_name_combo = QComboBox()
        self.pattern_name_combo.setEditable(True)
        self.pattern_name_combo.lineEdit().setPlaceholderText("Pattern name (optional)")
        layout.addWidget(self.pattern_name_combo)

        export_button = QPushButton("💾 Save Design to Pattern")
        export_button.clicked.connect(self._emit_pattern)
        layout.addWidget(export_button)

        optimize_button = QPushButton("⚡ Optimize Pattern")
        optimize_button.setToolTip("Remove duplicate frames and compress colors")
        optimize_button.clicked.connect(self._on_optimize_pattern)
        layout.addWidget(optimize_button)

        # Image export buttons
        export_image_row = QHBoxLayout()
        export_frame_btn = QPushButton("📷 Export Frame as Image")
        export_frame_btn.clicked.connect(self._on_export_frame_as_image)
        export_image_row.addWidget(export_frame_btn)
        
        export_gif_btn = QPushButton("🎬 Export Animation as GIF")
        export_gif_btn.clicked.connect(self._on_export_animation_as_gif)
        export_image_row.addWidget(export_gif_btn)
        layout.addLayout(export_image_row)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def _create_code_template_group(self) -> QGroupBox:
        group = QGroupBox("MCU Code Templates")
        layout = QVBoxLayout()
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("Template:"))
        self.code_template_combo = QComboBox()
        self.code_template_combo.addItems(available_templates())
        template_row.addWidget(self.code_template_combo, 1)
        layout.addLayout(template_row)

        export_btn = QPushButton("🧾 Export Code Template")
        export_btn.clicked.connect(self._on_export_code_template)
        layout.addWidget(export_btn)

        backup_btn = QPushButton("Backup Custom Fonts…")
        backup_btn.clicked.connect(self._backup_custom_fonts)
        layout.addWidget(backup_btn)

        self.code_template_status = QLabel("Generate ready-to-paste code for Arduino, PIC, and more.")
        self.code_template_status.setStyleSheet("color: #888;")
        layout.addWidget(self.code_template_status)
        group.setLayout(layout)
        return group

    def _create_import_group(self) -> QGroupBox:
        """Create image/GIF import group."""
        group = QGroupBox("Import Images/GIFs")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Import button
        import_btn = QPushButton("📁 Import Image/GIF")
        import_btn.clicked.connect(self._on_import_image)
        layout.addWidget(import_btn)

        # Resize mode
        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel("Resize Mode:"))
        self.import_resize_combo = QComboBox()
        self.import_resize_combo.addItems(["Fit (Maintain Aspect)", "Stretch (Fill Matrix)", "Crop (Center)"])
        resize_layout.addWidget(self.import_resize_combo)
        resize_layout.addStretch()
        layout.addLayout(resize_layout)

        # Preview info
        self.import_preview_label = QLabel("No file selected")
        self.import_preview_label.setWordWrap(True)
        self.import_preview_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.import_preview_label)

        group.setLayout(layout)
        return group

    def _on_import_image(self):
        """Handle image/GIF import."""
        if not self._pattern:
            QMessageBox.warning(self, "No Pattern", "Please create or load a pattern first.")
            return

        # Get file filter
        formats = ImageImporter.get_supported_formats()
        filter_str = "Image Files ("
        filter_str += " ".join([f"*.{fmt.lower()}" for fmt in formats])
        filter_str += ");;All Files (*.*)"

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Image or GIF",
            "",
            filter_str
        )

        if not filepath:
            return

        try:
            width = self._pattern.metadata.width
            height = self._pattern.metadata.height
            resize_mode = self.import_resize_combo.currentText()
            
            # Map UI text to resize mode
            resize_map = {
                "Fit (Maintain Aspect)": "fit",
                "Stretch (Fill Matrix)": "stretch",
                "Crop (Center)": "crop"
            }
            resize_mode = resize_map.get(resize_mode, "fit")

            # Check if it's a GIF
            is_gif = ImageImporter.is_gif(filepath)
            
            if is_gif:
                # Import GIF frames
                frames_data = ImageImporter.import_gif(
                    filepath,
                    width,
                    height,
                    resize_mode,
                    extract_all_frames=True
                )
                
                # Ask user if they want to replace or append
                reply = QMessageBox.question(
                    self,
                    "Import GIF",
                    f"Found {len(frames_data)} frames in GIF.\n\n"
                    "Replace current frames or append to existing frames?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Cancel:
                    return
                
                # Create frames
                new_frames = []
                for pixels in frames_data:
                    frame = Frame(pixels=pixels, duration_ms=self._frame_duration_ms)
                    new_frames.append(frame)
                
                if reply == QMessageBox.Yes:  # Replace
                    self._pattern.frames = new_frames
                    self._current_frame_index = 0
                else:  # Append
                    self._pattern.frames.extend(new_frames)
                
                self.import_preview_label.setText(
                    f"Imported {len(frames_data)} frames from GIF"
                )
            else:
                # Import single image
                pixels = ImageImporter.import_image(filepath, width, height, resize_mode)
                
                # Ask user if they want to replace current frame or add as new frame
                reply = QMessageBox.question(
                    self,
                    "Import Image",
                    "Replace current frame or add as new frame?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Cancel:
                    return
                
                frame = Frame(pixels=pixels, duration_ms=self._frame_duration_ms)
                
                if reply == QMessageBox.Yes:  # Replace current frame
                    if self._pattern.frames:
                        self._pattern.frames[self._current_frame_index] = frame
                    else:
                        self._pattern.frames = [frame]
                else:  # Add as new frame
                    if not self._pattern.frames:
                        self._pattern.frames = []
                    self._pattern.frames.append(frame)
                    self._current_frame_index = len(self._pattern.frames) - 1
                
                self.import_preview_label.setText("Image imported successfully")
            
            # Update UI
            self.history_manager.set_frame_count(len(self._pattern.frames))
            self.history_manager.set_current_frame(self._current_frame_index)
            self._load_current_frame_into_canvas()
            self._refresh_timeline()
            self._update_status_labels()
            self._maybe_autosync_preview()
            self.pattern_modified.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import image:\n\n{str(e)}"
            )

    def _create_matrix_configuration_group(self) -> QGroupBox:
        group = QGroupBox("Matrix & Colour Configuration")
        layout = QGridLayout()
        layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 256)
        self.width_spin.setValue(12)
        self.width_spin.setToolTip("Matrix width in pixels (1-256). Total LEDs = width × height (max 10,000)")
        self.width_spin.valueChanged.connect(self._on_matrix_dimension_changed)
        layout.addWidget(self.width_spin, 0, 1)

        layout.addWidget(QLabel("Height:"), 0, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 256)
        self.height_spin.setValue(6)
        self.height_spin.setToolTip("Matrix height in pixels (1-256). Total LEDs = width × height (max 10,000)")
        self.height_spin.valueChanged.connect(self._on_matrix_dimension_changed)
        layout.addWidget(self.height_spin, 0, 3)

        layout.addWidget(QLabel("Colour Mode:"), 1, 0)
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Mono", "Bi-colour", "RGB"])
        self.color_mode_combo.currentTextChanged.connect(self._on_color_mode_changed)
        layout.addWidget(self.color_mode_combo, 1, 1)

        layout.addWidget(QLabel("Background:"), 1, 2)
        self.background_color_btn = QPushButton("Select…")
        self.background_color_btn.clicked.connect(self._choose_background_colour)
        layout.addWidget(self.background_color_btn, 1, 3)

        layout.addWidget(QLabel("Preset:"), 2, 0)
        self.matrix_preset_combo = QComboBox()
        self.matrix_preset_combo.addItem("Custom", None)
        for preset in self.MATRIX_PRESETS:
            self.matrix_preset_combo.addItem(preset["label"], preset)
        self.matrix_preset_combo.currentIndexChanged.connect(self._on_matrix_preset_selected)
        layout.addWidget(self.matrix_preset_combo, 2, 1, 1, 3)

        self.dimension_source_label = QLabel("Dimensions: design session")
        self.dimension_source_label.setObjectName("DimensionSourceLabel")
        self.dimension_source_label.setWordWrap(True)
        layout.addWidget(self.dimension_source_label, 3, 0, 1, 4)

        layout.setColumnStretch(4, 1)
        group.setLayout(layout)
        return group

    def _create_export_summary_group(self) -> QGroupBox:
        group = QGroupBox("Export Summary")
        layout = QVBoxLayout()
        self.export_summary_label = QLabel()
        self.export_summary_label.setWordWrap(True)
        layout.addWidget(self.export_summary_label)
        export_button_row = QHBoxLayout()
        self.open_export_dialog_btn = QPushButton("Open Export Dialog")
        self.open_export_dialog_btn.setToolTip("Open export dialog for binary/HEX/LEDS output")
        self.open_export_dialog_btn.clicked.connect(self._on_open_export_dialog)
        export_button_row.addWidget(self.open_export_dialog_btn)
        export_button_row.addStretch()
        layout.addLayout(export_button_row)
        group.setLayout(layout)
        self._update_export_summary()
        return group

    def _set_canvas_zoom(self, percent: int) -> None:
        percent = max(25, min(percent, 300))
        if self.canvas_zoom_slider.value() != percent:
            self.canvas_zoom_slider.blockSignals(True)
            self.canvas_zoom_slider.setValue(percent)
            self.canvas_zoom_slider.blockSignals(False)
        self.canvas_zoom_label.setText(f"{percent}%")
        factor = percent / 100.0
        if hasattr(self.canvas, "set_zoom_factor"):
            self.canvas.set_zoom_factor(factor)
        self._update_canvas_group_height()

    def _on_canvas_zoom_changed(self, value: int) -> None:
        self._set_canvas_zoom(value)

    def _on_canvas_geometry_changed(self) -> None:
        if not getattr(self, "canvas", None):
            return
        combo = getattr(self, "canvas_geometry_combo", None)
        if not combo:
            return
        mode = combo.currentData()
        if mode:
            self.canvas.set_geometry_overlay(mode)

    def _on_canvas_pixel_shape_changed(self) -> None:
        if not getattr(self, "canvas", None):
            return
        combo = getattr(self, "canvas_pixel_shape_combo", None)
        if not combo:
            return
        shape = combo.currentData()
        if shape:
            self.canvas.set_pixel_shape(shape)

    def _open_detached_preview(self) -> None:
        if self._detached_preview is None:
            self._detached_preview = DetachedPreviewDialog(self)
        self._sync_detached_preview()
        if self._detached_preview:
            self._detached_preview.show()
            self._detached_preview.raise_()
            self._detached_preview.activateWindow()

    def _sync_detached_preview(self) -> None:
        if not self._detached_preview:
            return
        self._detached_preview.load_pattern(self._pattern)

    def _on_preview_zoom_changed(self, value: int) -> None:
        value = max(25, min(value, 400))
        label = getattr(self, "preview_zoom_label", None)
        if label:
            label.setText(f"{value}%")
        preview_widget = getattr(self, "preview_widget", None)
        if preview_widget and hasattr(preview_widget, "set_zoom"):
            preview_widget.set_zoom(value)

    def _on_autosave_toggled(self, checked: bool) -> None:
        self._autosave_enabled = checked
        if checked:
            interval = self.autosave_interval_spin.value()
            self._autosave_timer.start(interval * 60 * 1000)
        else:
            self._autosave_timer.stop()

    def _on_autosave_interval_changed(self, value: int) -> None:
        if self._autosave_enabled:
            self._autosave_timer.start(max(1, value) * 60 * 1000)

    def _perform_autosave(self) -> None:
        if not self._autosave_enabled or not self._pattern:
            return
        autosave_dir = Path("build/autosaves")
        autosave_dir.mkdir(parents=True, exist_ok=True)
        slug = (self._pattern.name or "pattern").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = autosave_dir / f"{slug}_{timestamp}.json"
        try:
            self._pattern.save_to_file(str(target))
            if hasattr(self, "memory_status_label"):
                self.memory_status_label.setText(f"Autosaved {timestamp}")
        except Exception as exc:
            if hasattr(self, "memory_status_label"):
                self.memory_status_label.setText(f"Autosave failed: {exc}")

    def _on_preview_mode_changed(self, mode: str) -> None:
        preview_widget = getattr(self, "preview_widget", None)
        if preview_widget and hasattr(preview_widget, "set_display_layout"):
            layout_map = {
                "Matrix": "Matrix",
                "Radial": "Circle",
                "Matrix + Circle": "Matrix + Circle",
            }
            preview_widget.set_display_layout(layout_map.get(mode, "Matrix"))

    def _update_status_labels(self) -> None:
        if not hasattr(self, "matrix_status_label"):
            return
        width = getattr(self, "width_spin", None)
        height = getattr(self, "height_spin", None)
        width_value = width.value() if width else (self._pattern.metadata.width if self._pattern else 0)
        height_value = height.value() if height else (self._pattern.metadata.height if self._pattern else 0)
        colour_mode = getattr(self, "color_mode_combo", None)
        colour_text = colour_mode.currentText() if colour_mode else "RGB"
        self.matrix_status_label.setText(f"Matrix: {width_value} × {height_value} ({colour_text})")

        total_frames = len(self._pattern.frames) if self._pattern and self._pattern.frames else 0
        current_index = self.frame_manager.current_index() if hasattr(self.frame_manager, "current_index") else 0
        frame_text = f"Frame: {current_index + 1}/{max(1, total_frames)} • {self._frame_duration_ms} ms"
        mismatches = self._validate_frame_dimensions()
        if mismatches:
            frame_text += " ⚠ size mismatch"
            if not self._frame_size_warning_shown:
                snippet = ", ".join(str(idx + 1) for idx in mismatches[:5])
                more = "…" if len(mismatches) > 5 else ""
                QMessageBox.warning(
                    self,
                    "Frame Size Mismatch",
                    f"The following frames do not match {width_value}×{height_value}: {snippet}{more}. "
                    "Apply effects or reimport data to realign them before exporting.",
                )
                self._frame_size_warning_shown = True
        else:
            self._frame_size_warning_shown = False
        self.frame_status_label.setText(frame_text)

        fps = self._get_playback_fps()
        loop_text = "Loop" if self._loop_enabled() else "Once"
        self.playback_status_label.setText(f"Playback: {fps} fps • {loop_text}")
        
        # Update layer status
        if hasattr(self, "layer_panel") and self._pattern:
            active_layer_idx = self.layer_panel.get_active_layer_index()
            layers = self.layer_manager.get_layers(self._current_frame_index)
            if active_layer_idx < len(layers):
                layer = layers[active_layer_idx]
                solo_text = " [Solo]" if self.layer_panel.is_solo_mode() else ""
                hidden_text = " [Hidden]" if not layer.visible else ""
                opacity_text = f" [{int(layer.opacity * 100)}%]" if layer.opacity < 1.0 else ""
                self.layer_status_label.setText(f"Layer: {layer.name}{solo_text}{hidden_text}{opacity_text}")
            else:
                self.layer_status_label.setText("Layer: –")
        else:
            self.layer_status_label.setText("Layer: –")
        
        self._update_dimension_source_label()
        self._update_export_summary()

        if hasattr(self, "memory_status_label") and self._pattern:
            size_kb = self._pattern.estimate_memory_bytes() / 1024.0
            warning = size_kb > 900
            text = f"Memory: {size_kb:.1f} KB"
            if warning:
                text += " ⚠"
                self.memory_status_label.setStyleSheet("color: #E55B5B;")
            else:
                self.memory_status_label.setStyleSheet("")
            self.memory_status_label.setText(text)

    def _on_color_mode_changed(self, mode: str) -> None:
        self._update_status_labels()

    def _validate_frame_dimensions(self) -> List[int]:
        if not self._pattern or not self._pattern.frames:
            self._frame_size_mismatch_indices = []
            return []
        width = self.width_spin.value() if hasattr(self, "width_spin") else self._pattern.metadata.width
        height = self.height_spin.value() if hasattr(self, "height_spin") else self._pattern.metadata.height
        expected = width * height
        mismatches = [idx for idx, frame in enumerate(self._pattern.frames) if len(frame.pixels) != expected]
        self._frame_size_mismatch_indices = mismatches
        return mismatches

    def _update_export_summary(self) -> None:
        if not hasattr(self, "export_summary_label"):
            return
        width = self.width_spin.value() if hasattr(self, "width_spin") else (self._pattern.metadata.width if self._pattern else 0)
        height = self.height_spin.value() if hasattr(self, "height_spin") else (self._pattern.metadata.height if self._pattern else 0)
        frames = len(self._pattern.frames) if self._pattern and self._pattern.frames else 0
        colour_mode = self.color_mode_combo.currentText() if hasattr(self, "color_mode_combo") else "RGB"
        bpp_map = {"Mono": 1, "Bi-colour": 2, "RGB": 3}
        bytes_per_pixel = bpp_map.get(colour_mode, 3)
        bytes_per_frame = width * height * bytes_per_pixel
        total_bytes = frames * bytes_per_frame
        summary_text = (
            f"{frames} frame(s) • {width}×{height} pixels • {bytes_per_pixel} byte(s)/pixel → "
            f"~{total_bytes} bytes total"
        )

        mismatch_frames = getattr(self, "_frame_size_mismatch_indices", [])
        geometry_guard = False
        if self._import_metadata_snapshot:
            original_leds = self._import_metadata_snapshot.get("original_led_count")
            if original_leds:
                geometry_guard = (width * height) != original_leds

        warnings = []
        if geometry_guard:
            warnings.append("Matrix dimensions differ from imported metadata")
        if mismatch_frames:
            warnings.append(f"{len(mismatch_frames)} frame(s) have pixel count mismatches")

        if warnings:
            summary_text = f"{summary_text}\n⚠ " + " • ".join(warnings)

        self.export_summary_label.setText(summary_text)

        if hasattr(self, "open_export_dialog_btn"):
            allow_export = not geometry_guard and not mismatch_frames
            self.open_export_dialog_btn.setEnabled(allow_export)
            if allow_export:
                self.open_export_dialog_btn.setToolTip("Open export dialog for binary/HEX/LEDS output")
            else:
                self.open_export_dialog_btn.setToolTip(
                    "Resolve geometry or frame-size mismatches before exporting."
                )

    def _on_open_export_dialog(self) -> None:
        """Open enhanced export dialog with format selection and metadata options."""
        if not self._pattern:
            QMessageBox.warning(self, "No Pattern", "No pattern to export. Create or load a pattern first.")
            return
        
        from core.pattern_exporter import PatternExporter
        from core.export_options import ExportOptions
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Pattern")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        
        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout()
        self.export_format_combo = QComboBox()
        formats = PatternExporter.get_export_formats()
        for name, ext, _ in formats:
            self.export_format_combo.addItem(f"{name} ({ext})")
        format_layout.addWidget(self.export_format_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Metadata options
        metadata_group = QGroupBox("Metadata Options")
        metadata_layout = QVBoxLayout()
        self.include_metadata_checkbox = QCheckBox("Include metadata header")
        self.include_metadata_checkbox.setChecked(True)
        metadata_layout.addWidget(self.include_metadata_checkbox)
        self.include_timestamp_checkbox = QCheckBox("Include timestamp")
        self.include_timestamp_checkbox.setChecked(True)
        metadata_layout.addWidget(self.include_timestamp_checkbox)
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
        # Advanced export options
        advanced_group = QGroupBox("Advanced Export Options")
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(8)
        
        # Bit ordering
        bit_order_layout = QHBoxLayout()
        bit_order_layout.addWidget(QLabel("Bit Order:"))
        self.export_bit_order_combo = QComboBox()
        self.export_bit_order_combo.addItems(["MSB", "LSB"])
        bit_order_layout.addWidget(self.export_bit_order_combo)
        bit_order_layout.addWidget(QLabel("Position:"))
        self.export_bit_position_combo = QComboBox()
        self.export_bit_position_combo.addItems(["Top", "Bottom"])
        bit_order_layout.addWidget(self.export_bit_position_combo)
        bit_order_layout.addStretch()
        advanced_layout.addLayout(bit_order_layout)
        
        # Scanning direction
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("Scan Direction:"))
        self.export_scan_direction_combo = QComboBox()
        self.export_scan_direction_combo.addItems(["Rows", "Columns"])
        scan_layout.addWidget(self.export_scan_direction_combo)
        scan_layout.addWidget(QLabel("Order:"))
        self.export_scan_order_combo = QComboBox()
        self.export_scan_order_combo.addItems(["LeftToRight", "RightToLeft", "TopToBottom", "BottomToTop", "Alternate"])
        scan_layout.addWidget(self.export_scan_order_combo)
        scan_layout.addStretch()
        advanced_layout.addLayout(scan_layout)
        
        # Serpentine wiring
        serpentine_layout = QHBoxLayout()
        self.export_serpentine_checkbox = QCheckBox("Serpentine wiring (reverse every 2nd row/column)")
        serpentine_layout.addWidget(self.export_serpentine_checkbox)
        serpentine_layout.addStretch()
        advanced_layout.addLayout(serpentine_layout)
        
        # RGB color order
        rgb_layout = QHBoxLayout()
        rgb_layout.addWidget(QLabel("RGB Order:"))
        self.export_rgb_order_combo = QComboBox()
        self.export_rgb_order_combo.addItems(["RGB", "BGR", "GRB"])
        rgb_layout.addWidget(self.export_rgb_order_combo)
        rgb_layout.addStretch()
        advanced_layout.addLayout(rgb_layout)
        
        # Color space
        color_space_layout = QHBoxLayout()
        color_space_layout.addWidget(QLabel("Color Space:"))
        self.export_color_space_combo = QComboBox()
        self.export_color_space_combo.addItems(["RGB888", "RGB565"])
        color_space_layout.addWidget(self.export_color_space_combo)
        color_space_layout.addStretch()
        advanced_layout.addLayout(color_space_layout)
        
        # Bytes per line
        bytes_per_line_layout = QHBoxLayout()
        bytes_per_line_layout.addWidget(QLabel("Bytes per Line:"))
        self.export_bytes_per_line_spin = QSpinBox()
        self.export_bytes_per_line_spin.setRange(0, 32)
        self.export_bytes_per_line_spin.setValue(0)
        self.export_bytes_per_line_spin.setToolTip("0 = no grouping")
        bytes_per_line_layout.addWidget(self.export_bytes_per_line_spin)
        bytes_per_line_layout.addStretch()
        advanced_layout.addLayout(bytes_per_line_layout)
        
        # Number format
        number_format_layout = QHBoxLayout()
        number_format_layout.addWidget(QLabel("Number Format:"))
        self.export_number_format_combo = QComboBox()
        self.export_number_format_combo.addItems(["Hex", "Decimal", "Binary"])
        number_format_layout.addWidget(self.export_number_format_combo)
        number_format_layout.addStretch()
        advanced_layout.addLayout(number_format_layout)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Pattern info
        info_group = QGroupBox("Pattern Information")
        info_layout = QVBoxLayout()
        width = self.width_spin.value() if hasattr(self, "width_spin") else self._pattern.metadata.width
        height = self.height_spin.value() if hasattr(self, "height_spin") else self._pattern.metadata.height
        frames = len(self._pattern.frames)
        info_text = f"Dimensions: {width} × {height}\nFrames: {frames}\nTotal LEDs: {width * height}"
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Preview
        preview_group = QGroupBox("Export Preview")
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Adjust options to preview encoded payload.")
        preview_label.setWordWrap(True)
        preview_layout.addWidget(preview_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        def _collect_options() -> ExportOptions:
            return ExportOptions(
                bit_order_msb_lsb=self.export_bit_order_combo.currentText(),
                bit_order_position=self.export_bit_position_combo.currentText(),
                scan_direction=self.export_scan_direction_combo.currentText(),
                scan_order=self.export_scan_order_combo.currentText(),
                serpentine=self.export_serpentine_checkbox.isChecked(),
                rgb_order=self.export_rgb_order_combo.currentText(),
                color_space=self.export_color_space_combo.currentText(),
                bytes_per_line=self.export_bytes_per_line_spin.value(),
                number_format=self.export_number_format_combo.currentText(),
            )

        def _apply_preview(preview: ExportPreview) -> None:
            lines: List[str] = [
                preview.header_summary,
                f"Payload size: {preview.total_bytes} byte(s)",
            ]
            if preview.detail_lines:
                lines.extend(preview.detail_lines)

            warnings: List[str] = preview.warnings.copy()
            geom = preview.geometry
            if not geom.is_valid:
                snippet = ", ".join(
                    str(idx + 1) for idx in geom.mismatched_frames[:5]
                )
                if len(geom.mismatched_frames) > 5:
                    snippet += ", …"
                warnings.append(
                    f"{len(geom.mismatched_frames)} frame(s) do not match "
                    f"{geom.expected_pixels} pixel layout (frames: {snippet})"
                )

            tooltip_sections = lines.copy()
            if warnings:
                tooltip_sections.append("")
                tooltip_sections.append("Warnings:")
                tooltip_sections.extend(f"- {msg}" for msg in warnings)

            visible_lines = lines.copy()
            if warnings:
                visible_lines.append("")
                visible_lines.append("Warnings:")
                visible_lines.extend(warnings)

            preview_label.setText("\n".join(visible_lines))
            preview_label.setToolTip("\n".join(tooltip_sections))

            if warnings:
                preview_label.setStyleSheet("color: #E55B5B;")
            else:
                preview_label.setStyleSheet("")

            ok_button = buttons.button(QDialogButtonBox.Ok)
            if ok_button:
                ok_button.setEnabled(not preview.blocking_issue)

        def _update_preview() -> None:
            try:
                selected_idx = self.export_format_combo.currentIndex()
                options = _collect_options()
                if 0 <= selected_idx < len(formats):
                    format_name, _, _ = formats[selected_idx]
                    preview = generate_export_preview(
                        self._pattern,
                        format_name,
                        options,
                    )
                    _apply_preview(preview)
                else:
                    preview_label.setText("Select a format to view preview details.")
                    preview_label.setToolTip("")
            except ExportValidationError as exc:
                preview_label.setText(str(exc))
                preview_label.setStyleSheet("color: #E55B5B;")
                ok_button = buttons.button(QDialogButtonBox.Ok)
                if ok_button:
                    ok_button.setEnabled(False)
            except Exception as exc:  # pragma: no cover - defensive safeguard
                preview_label.setText(f"Unable to generate preview: {exc}")
                preview_label.setStyleSheet("color: #E55B5B;")
                ok_button = buttons.button(QDialogButtonBox.Ok)
                if ok_button:
                    ok_button.setEnabled(False)

        # Wire preview updates
        self.export_format_combo.currentIndexChanged.connect(_update_preview)
        self.export_bit_order_combo.currentTextChanged.connect(_update_preview)
        self.export_bit_position_combo.currentTextChanged.connect(_update_preview)
        self.export_scan_direction_combo.currentTextChanged.connect(_update_preview)
        self.export_scan_order_combo.currentTextChanged.connect(_update_preview)
        self.export_serpentine_checkbox.stateChanged.connect(_update_preview)
        self.export_rgb_order_combo.currentTextChanged.connect(_update_preview)
        self.export_color_space_combo.currentTextChanged.connect(_update_preview)
        self.export_bytes_per_line_spin.valueChanged.connect(lambda _value: _update_preview())
        self.export_number_format_combo.currentTextChanged.connect(_update_preview)

        _update_preview()
        
        if dialog.exec() == QDialog.Accepted:
            selected_idx = self.export_format_combo.currentIndex()
            if selected_idx < len(formats):
                format_name, extension, export_func = formats[selected_idx]
                
                # Open save dialog
                filter_string = f"{format_name} ({extension})"
                filepath, _ = QFileDialog.getSaveFileName(
                    self,
                    "Export Pattern",
                    "",
                    f"{filter_string};;All Files (*.*)"
                )
                
                if filepath:
                    # Ensure file extension matches
                    if not filepath.lower().endswith(extension.replace('*', '')):
                        filepath += extension.replace('*', '')
                    
                    try:
                        # Create export options
                        options = ExportOptions(
                            bit_order_msb_lsb=self.export_bit_order_combo.currentText(),
                            bit_order_position=self.export_bit_position_combo.currentText(),
                            scan_direction=self.export_scan_direction_combo.currentText(),
                            scan_order=self.export_scan_order_combo.currentText(),
                            serpentine=self.export_serpentine_checkbox.isChecked(),
                            rgb_order=self.export_rgb_order_combo.currentText(),
                            color_space=self.export_color_space_combo.currentText(),
                            bytes_per_line=self.export_bytes_per_line_spin.value(),
                            number_format=self.export_number_format_combo.currentText()
                        )
                        
                        # Export with metadata if requested
                        if self.include_metadata_checkbox.isChecked():
                            # Enhanced export with metadata
                            export_func(self._pattern, filepath, options)
                            if self.include_timestamp_checkbox.isChecked():
                                # Add timestamp comment if format supports it
                                import os
                                import datetime
                                timestamp = datetime.datetime.now().isoformat()
                                # For text formats, append comment
                                if extension in ['*.leds', '*.json']:
                                    with open(filepath, 'a', encoding='utf-8') as f:
                                        f.write(f"\n# Exported: {timestamp}\n")
                        else:
                            export_func(self._pattern, filepath, options)
                        
                        QMessageBox.information(
                            self,
                            "Export Successful",
                            f"Pattern exported successfully to:\n{filepath}"
                        )
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Export Error",
                            f"Failed to export pattern:\n\n{str(e)}"
                        )

    def _choose_background_colour(self) -> None:
        colour = QColorDialog.getColor(QColor(0, 0, 0), self, "Select background colour")
        if colour.isValid():
            stylesheet = f"background-color: {colour.name()};"
            self.background_color_btn.setStyleSheet(stylesheet)

    def _maybe_autosync_preview(self) -> None:
        checkbox = getattr(self, "preview_autosync_checkbox", None)
        if checkbox and checkbox.isChecked():
            self._refresh_preview(no_message=True)

    def _setup_ui_legacy(self):
        """Legacy layout retained for reference (currently unused)."""
        return
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # Left column: canvas + frames
        left_column = QVBoxLayout()
        left_column.setSpacing(12)

        canvas_group = QGroupBox("Matrix Designer")
        canvas_layout = QVBoxLayout()
        canvas_layout.setSpacing(8)

        self.canvas = MatrixDesignCanvas(width=12, height=6, pixel_size=28)
        self.canvas.pixel_updated.connect(self._on_canvas_pixel_updated)
        canvas_layout.addWidget(self.canvas, stretch=1)

        canvas_status = QLabel("Click to paint. Right-click to erase.")
        canvas_layout.addWidget(canvas_status)
        self.canvas_status_label = canvas_status

        canvas_group.setLayout(canvas_layout)
        self.canvas_group = canvas_group
        self._update_canvas_group_height()
        left_column.addWidget(canvas_group, stretch=3)

        # Frame management
        frame_group = QGroupBox("Frames")
        frame_layout = QVBoxLayout()
        frame_layout.setSpacing(6)

        self.timeline = TimelineWidget()
        self.timeline.frameSelected.connect(self._on_frame_selected)
        self.timeline.playheadDragged.connect(self._on_timeline_playhead_dragged)
        self.timeline.contextMenuRequested.connect(self._on_timeline_context_menu)
        self.timeline.overlayActivated.connect(self._on_timeline_overlay_activated)
        self.timeline.overlayContextMenuRequested.connect(self._on_timeline_overlay_context_menu)
        frame_layout.addWidget(self.timeline, stretch=1)

        frame_button_row = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self._on_add_frame)
        frame_button_row.addWidget(add_btn)

        dup_btn = QPushButton("🧬 Duplicate")
        dup_btn.clicked.connect(self._on_duplicate_frame)
        frame_button_row.addWidget(dup_btn)

        del_btn = QPushButton("🗑 Delete")
        del_btn.clicked.connect(self._on_delete_frame)
        frame_button_row.addWidget(del_btn)

        frame_button_row.addStretch()
        frame_layout.addLayout(frame_button_row)

        frame_move_row = QHBoxLayout()
        up_btn = QPushButton("⬆ Move Up")
        up_btn.clicked.connect(lambda: self._on_move_frame(-1))
        frame_move_row.addWidget(up_btn)

        down_btn = QPushButton("⬇ Move Down")
        down_btn.clicked.connect(lambda: self._on_move_frame(1))
        frame_move_row.addWidget(down_btn)

        frame_move_row.addStretch()
        frame_layout.addLayout(frame_move_row)

        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("Frame duration (ms):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 2000)
        self.duration_spin.setValue(self._frame_duration_ms)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        duration_row.addWidget(self.duration_spin)
        duration_row.addStretch()
        frame_layout.addLayout(duration_row)

        transport_row = QHBoxLayout()
        self.playback_prev_btn = QPushButton("⏮")
        self.playback_prev_btn.setToolTip("Step to previous frame")
        self.playback_prev_btn.clicked.connect(lambda: self._step_frame(-1, wrap=self.playback_loop_checkbox.isChecked()))
        transport_row.addWidget(self.playback_prev_btn)

        self.playback_play_btn = QPushButton("▶")
        self.playback_play_btn.setToolTip("Play timeline")
        self.playback_play_btn.clicked.connect(self._on_transport_play)
        transport_row.addWidget(self.playback_play_btn)

        self.playback_pause_btn = QPushButton("⏸")
        self.playback_pause_btn.setToolTip("Pause playback")
        self.playback_pause_btn.clicked.connect(self._on_transport_pause)
        transport_row.addWidget(self.playback_pause_btn)

        self.playback_stop_btn = QPushButton("■")
        self.playback_stop_btn.setToolTip("Stop playback")
        self.playback_stop_btn.clicked.connect(self._on_transport_stop)
        transport_row.addWidget(self.playback_stop_btn)

        self.playback_next_btn = QPushButton("⏭")
        self.playback_next_btn.setToolTip("Step to next frame")
        self.playback_next_btn.clicked.connect(lambda: self._step_frame(1, wrap=self.playback_loop_checkbox.isChecked()))
        transport_row.addWidget(self.playback_next_btn)

        self.playback_loop_checkbox = QCheckBox("Loop")
        self.playback_loop_checkbox.setChecked(True)
        self.playback_loop_checkbox.stateChanged.connect(self._on_playback_loop_toggled)
        transport_row.addWidget(self.playback_loop_checkbox)

        transport_row.addWidget(QLabel("FPS:"))
        self.playback_fps_spin = QSpinBox()
        self.playback_fps_spin.setRange(1, 120)
        self.playback_fps_spin.setValue(self._playback_fps_default)
        self.playback_fps_spin.valueChanged.connect(self._on_playback_fps_changed)
        transport_row.addWidget(self.playback_fps_spin)

        transport_row.addStretch()
        frame_layout.addLayout(transport_row)

        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Timeline Zoom:"))
        self.timeline_zoom_slider = QSlider(Qt.Horizontal)
        self.timeline_zoom_slider.setRange(25, 400)
        self.timeline_zoom_slider.setValue(100)
        self.timeline_zoom_slider.valueChanged.connect(self._on_timeline_zoom_changed)
        zoom_row.addWidget(self.timeline_zoom_slider)
        self.timeline_zoom_label = QLabel("100%")
        zoom_row.addWidget(self.timeline_zoom_label)
        zoom_row.addStretch()
        frame_layout.addLayout(zoom_row)
        self._on_timeline_zoom_changed(self.timeline_zoom_slider.value())

        frame_group.setLayout(frame_layout)
        left_column.addWidget(frame_group, stretch=2)

        left_column.addStretch()
        root_layout.addLayout(left_column, stretch=2)

        # Right column (scroll area for tools)
        tools_scroll = QScrollArea()
        tools_scroll.setWidgetResizable(True)
        tools_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tools_container = QWidget()
        tools_layout = QVBoxLayout(tools_container)
        tools_layout.setSpacing(12)

        appearance_group = QGroupBox("Appearance")
        appearance_layout = QHBoxLayout()
        appearance_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([name.title() for name in self.THEME_DEFINITIONS.keys()])
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(self._theme.title())
        self.theme_combo.blockSignals(False)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        appearance_layout.addWidget(self.theme_combo)
        appearance_layout.addStretch()
        appearance_group.setLayout(appearance_layout)
        tools_layout.addWidget(appearance_group)

        # Palette section
        palette_group = QGroupBox("Palette")
        palette_layout = QVBoxLayout()
        palette_layout.setSpacing(6)

        palette_buttons_layout = QGridLayout()
        for idx, color in enumerate(self.DEFAULT_COLORS):
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"background-color: rgb{color}; border: 1px solid #444;")
            btn.clicked.connect(lambda checked=False, c=color: self._on_palette_selected(c))
            row = idx // 4
            col = idx % 4
            palette_buttons_layout.addWidget(btn, row, col)
        palette_layout.addLayout(palette_buttons_layout)

        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("Current colour:"))
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self.color_preview.setStyleSheet("background-color: rgb(255,255,255); border: 1px solid #666;")
        preview_row.addWidget(self.color_preview)
        preview_row.addStretch()
        palette_layout.addLayout(preview_row)

        self.channel_sliders: Dict[str, Tuple[QSlider, QSpinBox]] = {}
        for channel, idx in zip(("R", "G", "B"), range(3)):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"{channel}:"))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(self._current_color[idx])
            spin = QSpinBox()
            spin.setRange(0, 255)
            spin.setValue(self._current_color[idx])
            slider.valueChanged.connect(lambda val, ch=channel: self._on_channel_slider_changed(ch, val, source="slider"))
            spin.valueChanged.connect(lambda val, ch=channel: self._on_channel_slider_changed(ch, val, source="spin"))
            row_layout.addWidget(slider)
            row_layout.addWidget(spin)
            palette_layout.addLayout(row_layout)
            self.channel_sliders[channel] = (slider, spin)

        gradient_group = QGroupBox("Gradient")
        gradient_layout = QVBoxLayout()
        gradient_button_row = QHBoxLayout()
        self.gradient_start_btn = QPushButton("Start colour")
        self.gradient_start_btn.clicked.connect(lambda: self._choose_gradient_colour("start"))
        gradient_button_row.addWidget(self.gradient_start_btn)
        self.gradient_end_btn = QPushButton("End colour")
        self.gradient_end_btn.clicked.connect(lambda: self._choose_gradient_colour("end"))
        gradient_button_row.addWidget(self.gradient_end_btn)
        gradient_layout.addLayout(gradient_button_row)

        gradient_config_row = QHBoxLayout()
        gradient_config_row.addWidget(QLabel("Steps:"))
        self.gradient_steps_spin = QSpinBox()
        self.gradient_steps_spin.setRange(1, 256)
        self.gradient_steps_spin.setValue(32)
        gradient_config_row.addWidget(self.gradient_steps_spin)

        gradient_config_row.addWidget(QLabel("Orientation:"))
        self.gradient_orientation_combo = QComboBox()
        self.gradient_orientation_combo.addItems(["Horizontal", "Vertical", "Radial"])
        gradient_config_row.addWidget(self.gradient_orientation_combo)
        gradient_config_row.addStretch()
        gradient_layout.addLayout(gradient_config_row)

        apply_gradient_btn = QPushButton("Apply Gradient To Frame")
        apply_gradient_btn.clicked.connect(self._apply_gradient_from_controls)
        gradient_layout.addWidget(apply_gradient_btn)

        gradient_group.setLayout(gradient_layout)
        palette_layout.addWidget(gradient_group)

        palette_group.setLayout(palette_layout)
        tools_layout.addWidget(palette_group)

        # Ensure UI reflects default colours
        self._sync_channel_controls(self._current_color)
        self.gradient_start_btn.setStyleSheet(f"background-color: rgb{self._start_gradient_color};")
        self.gradient_end_btn.setStyleSheet(f"background-color: rgb{self._end_gradient_color};")

        # Matrix configuration
        matrix_group = QGroupBox("Matrix Configuration")
        matrix_layout = QHBoxLayout()
        matrix_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 64)
        self.width_spin.setValue(12)
        self.width_spin.valueChanged.connect(self._on_matrix_dimension_changed)
        matrix_layout.addWidget(self.width_spin)

        matrix_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 64)
        self.height_spin.setValue(6)
        self.height_spin.valueChanged.connect(self._on_matrix_dimension_changed)
        matrix_layout.addWidget(self.height_spin)
        matrix_group.setLayout(matrix_layout)
        tools_layout.addWidget(matrix_group)

        # Automation controls
        automation_group = QGroupBox("Automation Actions")
        automation_layout = QVBoxLayout()

        wipe_row = QHBoxLayout()
        wipe_row.addWidget(QLabel("Wipe:"))
        self.wipe_combo = QComboBox()
        self.wipe_combo.addItems(["Left to Right", "Right to Left", "Top to Bottom", "Bottom to Top"])
        wipe_row.addWidget(self.wipe_combo)
        wipe_add = QPushButton("Add")
        wipe_add.clicked.connect(lambda: self._queue_action("Wipe", "wipe", {"mode": self.wipe_combo.currentText()}))
        wipe_row.addWidget(wipe_add)
        automation_layout.addLayout(wipe_row)

        reveal_row = QHBoxLayout()
        reveal_row.addWidget(QLabel("Reveal:"))
        self.reveal_combo = QComboBox()
        self.reveal_combo.addItems(["Left", "Right", "Top", "Bottom"])
        reveal_row.addWidget(self.reveal_combo)
        reveal_add = QPushButton("Add")
        reveal_add.clicked.connect(lambda: self._queue_action("Reveal", "reveal", {"direction": self.reveal_combo.currentText()}))
        reveal_row.addWidget(reveal_add)
        automation_layout.addLayout(reveal_row)

        scroll_row = QHBoxLayout()
        scroll_row.addWidget(QLabel("Scroll:"))
        self.scroll_combo = QComboBox()
        self.scroll_combo.addItems(["Up", "Down", "Left", "Right"])
        scroll_row.addWidget(self.scroll_combo)
        scroll_add = QPushButton("Add")
        scroll_add.clicked.connect(lambda: self._queue_action("Scroll", "scroll", {"direction": self.scroll_combo.currentText()}))
        scroll_row.addWidget(scroll_add)
        automation_layout.addLayout(scroll_row)

        rotate_row = QHBoxLayout()
        rotate_row.addWidget(QLabel("Rotate:"))
        self.rotate_combo = QComboBox()
        self.rotate_combo.addItems(["90° Clockwise", "90° Counter-clockwise"])
        rotate_row.addWidget(self.rotate_combo)
        rotate_add = QPushButton("Add")
        rotate_add.clicked.connect(lambda: self._queue_action("Rotate", "rotate", {"mode": self.rotate_combo.currentText()}))
        rotate_row.addWidget(rotate_add)
        automation_layout.addLayout(rotate_row)

        mirror_row = QHBoxLayout()
        mirror_btn = QPushButton("Mirror Horizontal")
        mirror_btn.clicked.connect(lambda: self._queue_action("Mirror Horizontal", "mirror", {"axis": "horizontal"}))
        mirror_row.addWidget(mirror_btn)
        flip_btn = QPushButton("Flip Vertical")
        flip_btn.clicked.connect(lambda: self._queue_action("Flip Vertical", "flip", {"axis": "vertical"}))
        mirror_row.addWidget(flip_btn)
        invert_btn = QPushButton("Invert Colours")
        invert_btn.clicked.connect(lambda: self._queue_action("Invert Colours", "invert", {}))
        mirror_row.addWidget(invert_btn)
        automation_layout.addLayout(mirror_row)

        automation_group.setLayout(automation_layout)
        tools_layout.addWidget(automation_group)

        # Action list
        action_group = QGroupBox("Action Queue")
        action_layout = QVBoxLayout()
        self.action_list = QListWidget()
        self.action_list.currentRowChanged.connect(self._on_action_list_selection)
        action_layout.addWidget(self.action_list)

        action_button_row = QHBoxLayout()
        remove_action_btn = QPushButton("Remove Selected")
        remove_action_btn.clicked.connect(self._on_remove_action)
        action_button_row.addWidget(remove_action_btn)

        clear_actions_btn = QPushButton("Clear All")
        clear_actions_btn.clicked.connect(self._on_clear_actions)
        action_button_row.addWidget(clear_actions_btn)
        action_layout.addLayout(action_button_row)

        apply_actions_btn = QPushButton("▶ Apply Actions")
        apply_actions_btn.clicked.connect(self._apply_actions_to_frames)
        action_layout.addWidget(apply_actions_btn)

        action_group.setLayout(action_layout)
        tools_layout.addWidget(action_group)

        # Action inspector
        self.action_parameter_widgets: Dict[str, Tuple[QWidget, Dict[str, object]]] = {}
        self._param_error_labels: Dict[str, QLabel] = {}
        self._param_description_labels: Dict[str, QLabel] = {}
        self._param_error_state: Dict[str, str] = {}
        self._updating_action_inspector = False
        action_inspector_group = QGroupBox("Action Details")
        inspector_layout = QVBoxLayout()

        details_form = QFormLayout()
        details_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.action_name_edit = QLineEdit()
        self.action_name_edit.editingFinished.connect(self._on_action_name_edited)
        details_form.addRow("Name", self.action_name_edit)
        self.action_type_label = QLabel("-")
        self.action_type_label.setObjectName("ActionTypeLabel")
        details_form.addRow("Action Type", self.action_type_label)
        layout.addLayout(details_form)

        self.action_param_container = QWidget()
        self.action_param_layout = QFormLayout()
        self.action_param_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.action_param_container.setLayout(self.action_param_layout)
        layout.addWidget(self.action_param_container)

        self.action_validation_label = QLabel()
        self.action_validation_label.setObjectName("ActionValidationLabel")
        self.action_validation_label.setWordWrap(True)
        self.action_validation_label.hide()
        layout.addWidget(self.action_validation_label)

        self.action_preview_label = QLabel()
        self.action_preview_label.setObjectName("ActionPreviewLabel")
        self.action_preview_label.setWordWrap(True)
        self.action_preview_label.hide()
        layout.addWidget(self.action_preview_label)

        action_inspector_group.setLayout(inspector_layout)
        action_inspector_group.setEnabled(False)
        self.action_inspector_group = action_inspector_group
        tools_layout.addWidget(action_inspector_group)

        presets_group = QGroupBox("Automation Presets")
        presets_layout = QVBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setEditable(True)
        self.preset_combo.setInsertPolicy(QComboBox.NoInsert)
        self.preset_combo.lineEdit().setPlaceholderText("Preset name")
        presets_layout.addWidget(self.preset_combo)

        preset_buttons = QHBoxLayout()
        save_preset_btn = QPushButton("Save")
        save_preset_btn.clicked.connect(self._on_save_preset)
        preset_buttons.addWidget(save_preset_btn)

        apply_preset_btn = QPushButton("Apply")
        apply_preset_btn.clicked.connect(self._on_apply_preset)
        preset_buttons.addWidget(apply_preset_btn)

        preview_preset_btn = QPushButton("Preview")
        preview_preset_btn.clicked.connect(self._on_preview_preset)
        preset_buttons.addWidget(preview_preset_btn)

        delete_preset_btn = QPushButton("Delete")
        delete_preset_btn.clicked.connect(self._on_delete_preset)
        preset_buttons.addWidget(delete_preset_btn)

        preset_buttons.addStretch()
        presets_layout.addLayout(preset_buttons)

        preset_manage_row = QHBoxLayout()
        duplicate_preset_btn = QToolButton()
        duplicate_preset_btn.setText("Duplicate")
        duplicate_preset_btn.clicked.connect(self._on_duplicate_preset)
        preset_manage_row.addWidget(duplicate_preset_btn)

        rename_preset_btn = QToolButton()
        rename_preset_btn.setText("Rename")
        rename_preset_btn.clicked.connect(self._on_rename_preset)
        preset_manage_row.addWidget(rename_preset_btn)

        export_preset_btn = QToolButton()
        export_preset_btn.setText("Export…")
        export_preset_btn.clicked.connect(self._on_export_preset)
        preset_manage_row.addWidget(export_preset_btn)

        import_preset_btn = QToolButton()
        import_preset_btn.setText("Import…")
        import_preset_btn.clicked.connect(self._on_import_preset)
        preset_manage_row.addWidget(import_preset_btn)

        preset_manage_row.addStretch()
        presets_layout.addLayout(preset_manage_row)
        presets_group.setLayout(presets_layout)
        tools_layout.addWidget(presets_group)

        # Processing options
        processing_group = QGroupBox("Processing Range")
        processing_layout = QVBoxLayout()
        self.source_button_group = QButtonGroup(self)
        use_first = QRadioButton("Use first frame as source")
        each_frame = QRadioButton("Use each frame independently")
        increment_frame = QRadioButton("Increment parameters per frame")
        use_first.setChecked(True)

        self.source_button_group.addButton(use_first, 0)
        self.source_button_group.addButton(each_frame, 1)
        self.source_button_group.addButton(increment_frame, 2)

        processing_layout.addWidget(use_first)
        processing_layout.addWidget(each_frame)
        processing_layout.addWidget(increment_frame)

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Frame start:"))
        self.frame_start_spin = QSpinBox()
        self.frame_start_spin.setMinimum(1)
        self.frame_start_spin.setValue(1)
        self.frame_start_spin.valueChanged.connect(lambda _: self._refresh_timeline())
        range_row.addWidget(self.frame_start_spin)

        range_row.addWidget(QLabel("Frame end:"))
        self.frame_end_spin = QSpinBox()
        self.frame_end_spin.setMinimum(1)
        self.frame_end_spin.setValue(1)
        self.frame_end_spin.valueChanged.connect(lambda _: self._refresh_timeline())
        range_row.addWidget(self.frame_end_spin)
        processing_layout.addLayout(range_row)

        tools_layout.addWidget(processing_group)

        # Export controls
        export_group = QGroupBox("Pattern Export")
        export_layout = QVBoxLayout()
        self.pattern_name_combo = QComboBox()
        self.pattern_name_combo.setEditable(True)
        self.pattern_name_combo.lineEdit().setPlaceholderText("Pattern name (optional)")
        export_layout.addWidget(self.pattern_name_combo)

        export_button = QPushButton("💾 Save Design to Pattern")
        export_button.clicked.connect(self._emit_pattern)
        export_layout.addWidget(export_button)

        tools_layout.addWidget(export_group)
        tools_layout.addStretch()

        tools_scroll.setWidget(tools_container)
        root_layout.addWidget(tools_scroll, stretch=1)
        self._update_transport_controls()

    def _update_canvas_group_height(self):
        if not hasattr(self, "canvas") or not hasattr(self, "canvas_group"):
            return
        hint = self.canvas.minimumSizeHint()
        if hasattr(hint, "height"):
            canvas_height = hint.height()
        elif isinstance(hint, tuple) and len(hint) >= 2:
            canvas_height = hint[1]
        else:
            canvas_height = 0
        if canvas_height <= 0:
            return
        desired_height = max(int(canvas_height * 2), canvas_height + 120)
        self.canvas_group.setMinimumHeight(desired_height)

    def _resolve_initial_theme(self) -> str:
        candidates = []
        env_theme = os.environ.get(self.ENV_THEME_KEY)
        if env_theme:
            candidates.append(env_theme)
        app = QApplication.instance()
        if app:
            for key in ("uploadbridge.theme", "design_theme", "theme_mode", "theme"):
                value = app.property(key)
                if isinstance(value, str):
                    candidates.append(value)
        for candidate in candidates:
            if isinstance(candidate, str):
                normalized = candidate.strip().lower()
                if normalized in self.THEME_DEFINITIONS:
                    return normalized
        return self.DEFAULT_THEME

    def _on_theme_changed(self, text: str):
        key = (text or "").strip().lower()
        if key not in self.THEME_DEFINITIONS:
            return
        if key == self._theme:
            return
        self._theme = key
        app = QApplication.instance()
        if app:
            app.setProperty("uploadbridge.theme", key)
        self._apply_theme()

    def _apply_theme(self):
        theme = self.THEME_DEFINITIONS.get(self._theme, self.THEME_DEFINITIONS[self.DEFAULT_THEME])
        ui = theme["ui"]
        timeline_palette = theme["timeline"]
        canvas_palette = theme["canvas"]
        simulator_palette = theme.get("simulator", {})

        list_bg = ui.get("list_bg", ui["surface"])
        list_hover = ui.get("list_hover", ui["control_bg"])
        text_on_accent = ui.get("text_on_accent", "#FFFFFF")
        slider_groove = ui.get("slider_groove", ui["control_bg"])
        slider_handle = ui.get("slider_handle", ui["accent"])

        self._current_ui_palette = ui

        self.setStyleSheet(
            f"""
            QWidget#DesignToolsTab {{
                background-color: {ui["bg"]};
                color: {ui["text_primary"]};
            }}
            QGroupBox {{
                background-color: {ui["surface"]};
                border: 1px solid {ui["border"]};
                border-radius: 6px;
                margin-top: 12px;
                padding: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: {ui["text_secondary"]};
            }}
            QListWidget {{
                background-color: {list_bg};
                border: 1px solid {ui["border"]};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px;
                color: {ui["text_primary"]};
            }}
            QListWidget::item:hover {{
                background-color: {list_hover};
            }}
            QListWidget::item:selected {{
                background-color: {ui["accent"]};
                color: {text_on_accent};
            }}
            QPushButton {{
                background-color: {ui["control_bg"]};
                border: 1px solid {ui["border"]};
                border-radius: 4px;
                padding: 6px 10px;
                color: {ui["text_primary"]};
            }}
            QToolButton {{
                background-color: {ui["control_bg"]};
                border: 1px solid {ui["border"]};
                border-radius: 4px;
                padding: 6px 10px;
                color: {ui["text_primary"]};
            }}
            QPushButton:hover {{
                background-color: {ui["accent_hover"]};
                border-color: {ui["accent_hover"]};
                color: {text_on_accent};
            }}
            QPushButton:pressed {{
                background-color: {ui["accent"]};
                border-color: {ui["accent"]};
                color: {text_on_accent};
            }}
            QPushButton:disabled {{
                color: {ui["control_disabled_text"]};
                border-color: {ui["border"]};
                background-color: {ui["control_disabled_bg"]};
            }}
            QToolButton:hover {{
                background-color: {ui["accent_hover"]};
                border-color: {ui["accent_hover"]};
                color: {text_on_accent};
            }}
            QToolButton:pressed {{
                background-color: {ui["accent"]};
                border-color: {ui["accent"]};
                color: {text_on_accent};
            }}
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
                background-color: {ui["control_bg"]};
                border: 1px solid {ui["border"]};
                border-radius: 4px;
                padding: 2px 6px;
                color: {ui["text_primary"]};
                selection-background-color: {ui["accent"]};
                selection-color: {text_on_accent};
            }}
            QSpinBox[hasError="true"], QDoubleSpinBox[hasError="true"], QComboBox[hasError="true"], QLineEdit[hasError="true"] {{
                border: 1px solid {ui["danger"]};
            }}
            QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled, QLineEdit:disabled {{
                background-color: {ui["control_disabled_bg"]};
                color: {ui["control_disabled_text"]};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {slider_groove};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {slider_handle};
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QCheckBox, QRadioButton {{
                color: {ui["text_secondary"]};
            }}
            QScrollArea {{
                border: none;
            }}
            QMenu {{
                background-color: {ui["surface"]};
                border: 1px solid {ui["border"]};
                color: {ui["text_primary"]};
            }}
            QMenu::item:selected {{
                background-color: {ui["accent"]};
                color: {text_on_accent};
            }}
            QMessageBox {{
                background-color: {ui["surface"]};
                color: {ui["text_primary"]};
            }}
            QLabel#ActionValidationLabel {{
                color: {ui["danger"]};
                font-weight: 500;
            }}
            QLabel#ActionPreviewLabel {{
                color: {ui["text_secondary"]};
            }}
            QLabel#ActionTypeLabel {{
                color: {ui["text_secondary"]};
            }}
            QLabel#ParamDescriptionLabel {{
                color: {ui["text_secondary"]};
                font-size: 11px;
            }}
            QLabel#ParamErrorLabel {{
                color: {ui["danger"]};
                font-size: 11px;
            }}
            """
        )

        if hasattr(self.canvas, "apply_palette"):
            self.canvas.apply_palette(canvas_palette)
        self.timeline.apply_palette(timeline_palette)
        if hasattr(self, "preview_widget") and hasattr(self.preview_widget, "apply_theme"):
            self.preview_widget.apply_theme(ui, simulator_palette)

        if hasattr(self, "canvas_status_label"):
            self.canvas_status_label.setStyleSheet(f"color: {ui['text_secondary']}; font-size: 11px;")

        border_color = ui.get("border", "#666666")
        if hasattr(self, "gradient_start_btn"):
            self.gradient_start_btn.setStyleSheet(
                f"background-color: rgb{self._start_gradient_color}; border: 1px solid {border_color}; color: {ui['text_primary']};"
            )
        if hasattr(self, "gradient_end_btn"):
            self.gradient_end_btn.setStyleSheet(
                f"background-color: rgb{self._end_gradient_color}; border: 1px solid {border_color}; color: {ui['text_primary']};"
            )

        self.timeline_zoom_label.setStyleSheet(f"color: {ui['text_secondary']};")

        if hasattr(self, "theme_combo"):
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentText(self._theme.title())
            self.theme_combo.blockSignals(False)

        self._sync_channel_controls(self._current_color)

    # ------------------------------------------------------------------
    # Pattern management
    # ------------------------------------------------------------------
    def _create_default_pattern(self):
        self._suspend_timeline_refresh = True
        try:
            self._import_metadata_snapshot = None
            # Get width/height from spinboxes if they exist, otherwise use defaults
            if hasattr(self, "width_spin") and self.width_spin is not None:
                width = self.width_spin.value()
            else:
                width = 12  # Default width
            if hasattr(self, "height_spin") and self.height_spin is not None:
                height = self.height_spin.value()
            else:
                height = 6  # Default height
            blank_frame = self._create_blank_frame(width, height)
            metadata = PatternMetadata(width=width, height=height)
            pattern = Pattern(name="New Design", metadata=metadata, frames=[blank_frame])
            self._pattern = pattern
            self.frame_manager.set_pattern(pattern)
            self.layer_manager.set_pattern(pattern)
            self.automation_manager.clear()
            self.history_manager.set_frame_count(len(pattern.frames))
            self.history_manager.set_current_frame(0)
            self._set_lms_sequence(PatternInstructionSequence(), persist=False)
            
            # Initialize layer panel
            if hasattr(self, "layer_panel"):
                self.layer_panel.set_frame_index(0)
            
            if hasattr(self, "canvas"):
                self.canvas.set_matrix_size(width, height)
            self._load_current_frame_into_canvas()
            self._update_status_labels()
            self._maybe_autosync_preview()
            self._update_transport_controls()
        finally:
            self._suspend_timeline_refresh = False
        self._mark_clean()
        if not self._suspend_timeline_refresh:
            self._refresh_timeline()

    def _create_blank_frame(self, width: int, height: int) -> Frame:
        pixels = [(0, 0, 0)] * (width * height)
        return Frame(pixels=pixels, duration_ms=self._frame_duration_ms)

    def _capture_import_metadata(self, pattern: Pattern, file_path: Optional[str] = None) -> Optional[Dict[str, object]]:
        """Create a snapshot of the metadata from an imported pattern for validation."""
        if not pattern or not getattr(pattern, "metadata", None):
            return None

        metadata = pattern.metadata
        source_format = getattr(metadata, "source_format", None)
        source_path = file_path or getattr(metadata, "source_path", None)
        dimension_source = getattr(metadata, "dimension_source", "unknown")
        dimension_confidence = float(getattr(metadata, "dimension_confidence", 0.0) or 0.0)

        width = getattr(metadata, "width", None)
        height = getattr(metadata, "height", None)
        if not width or not height:
            return None

        led_count = width * height
        frame_count = len(pattern.frames)

        if not (source_format or source_path or dimension_source not in ("unknown", None)):
            return None

        return {
            "source_format": source_format,
            "source_path": source_path,
            "dimension_source": dimension_source,
            "dimension_confidence": dimension_confidence,
            "original_width": width,
            "original_height": height,
            "original_led_count": led_count,
            "original_frames": frame_count,
        }

    def _update_dimension_source_label(self) -> None:
        label = getattr(self, "dimension_source_label", None)
        if label is None:
            return

        if not self._pattern:
            label.setText("No pattern loaded.")
            label.setStyleSheet("")
            return

        snapshot = self._import_metadata_snapshot or {}
        metadata = self._pattern.metadata
        width = self.width_spin.value() if hasattr(self, "width_spin") else metadata.width
        height = self.height_spin.value() if hasattr(self, "height_spin") else metadata.height
        frames = len(self._pattern.frames)

        source_format = snapshot.get("source_format") or getattr(metadata, "source_format", None)
        source_path = snapshot.get("source_path") or getattr(metadata, "source_path", None)
        dimension_source = snapshot.get("dimension_source") or getattr(metadata, "dimension_source", "unknown")
        dimension_confidence = snapshot.get("dimension_confidence", getattr(metadata, "dimension_confidence", 0.0))

        source_labels = {
            "header": "File header",
            "led_count": "LED header",
            "detector": "Auto detector",
            "fallback": "Heuristic fallback",
            "manual": "Manual override",
            "unknown": "Design session",
        }

        source_text = source_labels.get(dimension_source, dimension_source or "Unknown source")
        parts = [f"Source: {source_text}"]

        if source_format:
            parts.append(f"Format {source_format}")
        if source_path:
            try:
                parts.append(Path(str(source_path)).name)
            except Exception:
                parts.append(str(source_path))
        if dimension_confidence:
            parts.append(f"Confidence {int(dimension_confidence * 100):d}%")

        imported_leds = snapshot.get("original_led_count")
        imported_frames = snapshot.get("original_frames")
        if imported_leds:
            parts.append(f"Imported {imported_leds} LEDs")
        if imported_frames is not None:
            parts.append(f"{imported_frames} frame(s)")
        parts.append(f"Current {width}×{height} • {frames} frame(s)")

        text = " • ".join(parts)

        geometry_changed = False
        if imported_leds:
            geometry_changed = (width * height) != imported_leds
        frame_count_changed = False
        if imported_frames is not None:
            frame_count_changed = frames != imported_frames

        pixel_mismatch = bool(getattr(self, "_frame_size_mismatch_indices", []))

        warnings = []
        if geometry_changed:
            warnings.append("matrix size differs from imported metadata")
        if frame_count_changed:
            warnings.append("frame count changed since import")
        if pixel_mismatch:
            warnings.append("frame pixels mismatch matrix dimensions")

        if warnings:
            warning_text = " ⚠ " + "; ".join(warnings)
            text = f"{text}{warning_text}"
            label.setStyleSheet("color: #E55B5B;")
        else:
            label.setStyleSheet("")

        label.setText(text)

    def load_pattern(self, pattern: Pattern, file_path: Optional[str] = None):
        """Load external pattern into design tab."""
        # Validate input pattern
        if not isinstance(pattern, Pattern):
            raise TypeError(f"load_pattern expects Pattern object, got {type(pattern).__name__}")
        
        self._suspend_timeline_refresh = True
        try:
            try:
                pattern_copy = Pattern.from_dict(pattern.to_dict()) if hasattr(pattern, "to_dict") else pattern
            except Exception:
                pattern_copy = pattern

            # Validate pattern_copy is Pattern object before assignment
            if not isinstance(pattern_copy, Pattern):
                raise TypeError(f"Pattern copy is not a Pattern object, got {type(pattern_copy).__name__}")
            
            self._pattern = pattern_copy
            self.frame_manager.set_pattern(pattern_copy)
            self.layer_manager.set_pattern(pattern_copy)
            self.automation_manager.clear()
            self.history_manager.set_frame_count(len(pattern_copy.frames))
            self.history_manager.set_current_frame(0)
            self._current_frame_index = 0
            self._import_metadata_snapshot = self._capture_import_metadata(pattern_copy, file_path)
            if hasattr(self, "_effects_preview_backup"):
                delattr(self, "_effects_preview_backup")

            # Initialize layer panel
            if hasattr(self, "layer_panel"):
                self.layer_panel.set_frame_index(0)

            width = pattern_copy.metadata.width
            height = pattern_copy.metadata.height
            # Only update spinboxes if they exist (might not exist during initialization)
            if hasattr(self, "width_spin") and self.width_spin is not None:
                self.width_spin.blockSignals(True)
                self.width_spin.setValue(width)
                self.width_spin.blockSignals(False)
            if hasattr(self, "height_spin") and self.height_spin is not None:
                self.height_spin.blockSignals(True)
                self.height_spin.setValue(height)
                self.height_spin.blockSignals(False)

            self.canvas.set_matrix_size(width, height)
            if pattern_copy.frames:
                self._frame_duration_ms = pattern_copy.frames[0].duration_ms
            
            # Check for single color mode from metadata
            if hasattr(pattern_copy.metadata, 'is_single_color'):
                self._single_color_mode = pattern_copy.metadata.is_single_color
            else:
                self._single_color_mode = False
            
            # Enforce single color mode if active
            if self._single_color_mode:
                self._current_color = (255, 255, 255)
                self._sync_channel_controls(self._current_color)
                self.canvas.set_current_color(self._current_color)
                # Disable color sliders in single color mode
                if hasattr(self, "channel_sliders"):
                    for ch in ("R", "G", "B"):
                        if ch in self.channel_sliders:
                            slider, spin = self.channel_sliders[ch]
                            slider.setEnabled(False)
                            spin.setEnabled(False)
            else:
                # Enable color sliders in RGB/GRB mode
                if hasattr(self, "channel_sliders"):
                    for ch in ("R", "G", "B"):
                        if ch in self.channel_sliders:
                            slider, spin = self.channel_sliders[ch]
                            slider.setEnabled(True)
                            spin.setEnabled(True)
            
            self._load_current_frame_into_canvas()
            self._update_status_labels()
            self._maybe_autosync_preview()
            self._update_transport_controls()
            self._update_dimension_source_label()
            self._sync_lms_sequence_from_pattern()
        finally:
            self._suspend_timeline_refresh = False
        self._mark_clean()
        self._update_single_color_ui_state()
        self._refresh_timeline()
    
    def update_pattern(self, pattern: Pattern):
        """Update pattern from external source (called from pattern_changed signal).
        This updates the pattern without triggering pattern_modified signal."""
        if pattern:
            # Prevent recursion: only update if we're not already loading a pattern
            if not hasattr(self, '_loading_pattern'):
                self._loading_pattern = True
                try:
                    self.load_pattern(pattern)
                finally:
                    self._loading_pattern = False

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_canvas_pixel_updated(self, x: int, y: int, color: Tuple[int, int, int]):
        if not self._pattern or not self._pattern.frames:
            return
        
        # Save state before first pixel change in a paint operation
        if self._pending_paint_state is None:
            frame = self._pattern.frames[self._current_frame_index]
            self._pending_paint_state = list(frame.pixels)
        
        width = self.state.width()
        height = self.state.height()
        
        # Get active layer index from layer panel
        active_layer = 0
        layer_name = "Layer 1"
        layer_visible = True
        if hasattr(self, "layer_panel"):
            active_layer = self.layer_panel.get_active_layer_index()
            layers = self.layer_manager.get_layers(self._current_frame_index)
            if active_layer < len(layers):
                layer = layers[active_layer]
                layer_name = layer.name
                layer_visible = layer.visible
                
                # Warn if painting on hidden layer (only once per session)
                if not layer_visible and not hasattr(self, "_hidden_layer_warning_shown"):
                    from ui.utils.user_feedback import UserFeedback
                    UserFeedback.warning(
                        self,
                        "Painting on Hidden Layer",
                        f"⚠️ You are painting on layer '{layer_name}' which is currently hidden.\n\n"
                        "The changes will not be visible until you make the layer visible."
                    )
                    self._hidden_layer_warning_shown = True
        
        target_frames = [self._current_frame_index]
        if getattr(self, "brush_broadcast_checkbox", None) and self.brush_broadcast_checkbox.isChecked():
            target_frames = list(range(len(self._pattern.frames)))

        for frame_index in target_frames:
            self.layer_manager.apply_pixel(frame_index, x, y, color, width, height, active_layer)
            self.layer_manager.sync_frame_from_layers(frame_index)
        
        # Clear thumbnail cache when pixels change
        if hasattr(self, "layer_panel"):
            self.layer_panel.clear_thumbnail_cache()
        
        self.pattern_modified.emit()
        self._maybe_autosync_preview()
        self._update_status_labels()

    def _commit_paint_operation(self):
        """Commit a paint operation to history."""
        if self._pending_paint_state is None:
            return
        
        if not self._pattern or not self._pattern.frames:
            self._pending_paint_state = None
            return
        
        frame = self._pattern.frames[self._current_frame_index]
        new_pixels = list(frame.pixels)
        
        # Only save if pixels actually changed
        if new_pixels != self._pending_paint_state:
            command = FrameStateCommand(
                self._current_frame_index,
                self._pending_paint_state,
                new_pixels,
                "Paint pixels"
            )
            self.history_manager.push_command(command, self._current_frame_index)
        
        self._pending_paint_state = None

    def _on_undo(self):
        """Handle undo action."""
        if not self._pattern or not self._pattern.frames:
            return
        
        command = self.history_manager.undo(self._current_frame_index)
        if command:
            frame = self._pattern.frames[self._current_frame_index]
            frame.pixels = command.undo()
            self._load_current_frame_into_canvas()
            self.pattern_modified.emit()
            self._maybe_autosync_preview()
            self._update_status_labels()

    def _on_redo(self):
        """Handle redo action."""
        if not self._pattern or not self._pattern.frames:
            return
        
        command = self.history_manager.redo(self._current_frame_index)
        if command:
            frame = self._pattern.frames[self._current_frame_index]
            frame.pixels = command.execute()
            self._load_current_frame_into_canvas()
            self.pattern_modified.emit()
            self._maybe_autosync_preview()
            self._update_status_labels()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self._on_undo()
                event.accept()
                return
            elif event.key() == Qt.Key_Y:
                self._on_redo()
                event.accept()
                return
        super().keyPressEvent(event)

    def _on_palette_selected(self, color: Tuple[int, int, int]):
        # Enforce single color mode (white only)
        if self._single_color_mode:
            color = (255, 255, 255)
        self._current_color = color
        self.canvas.set_current_color(color)
        self._sync_channel_controls(color)
        self._sync_random_palette()

    def _sync_channel_controls(self, color: Tuple[int, int, int]):
        r, g, b = color
        if hasattr(self, "color_preview"):
            border_color = self._current_ui_palette.get("border", "#666666") if hasattr(self, "_current_ui_palette") else "#666666"
            self.color_preview.setStyleSheet(
                f"background-color: rgb({r},{g},{b}); border: 1px solid {border_color};"
            )
        for channel, value in zip(("R", "G", "B"), (r, g, b)):
            if channel not in getattr(self, "channel_sliders", {}):
                continue
            slider, spin = self.channel_sliders[channel]
            slider.blockSignals(True)
            spin.blockSignals(True)
            slider.setValue(value)
            spin.setValue(value)
            slider.blockSignals(False)
            spin.blockSignals(False)

    def _on_channel_slider_changed(self, channel: str, value: int, source: str):
        # Enforce single color mode (white only) - disable sliders
        if self._single_color_mode:
            # Force all channels to 255 (white)
            for ch in ("R", "G", "B"):
                s, sp = self.channel_sliders[ch]
                s.blockSignals(True)
                sp.blockSignals(True)
                s.setValue(255)
                sp.setValue(255)
                s.blockSignals(False)
                sp.blockSignals(False)
            self._current_color = (255, 255, 255)
            self._sync_channel_controls(self._current_color)
            self.canvas.set_current_color(self._current_color)
            return
        
        slider, spin = self.channel_sliders[channel]
        if source == "slider":
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        else:
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)

        r = self.channel_sliders["R"][0].value()
        g = self.channel_sliders["G"][0].value()
        b = self.channel_sliders["B"][0].value()
        self._current_color = (r, g, b)
        self._sync_channel_controls(self._current_color)
        self.canvas.set_current_color(self._current_color)

    def _on_matrix_preset_selected(self, index: int):
        if index <= 0 or not hasattr(self, "matrix_preset_combo"):
            return
        data = self.matrix_preset_combo.itemData(index)
        if not data:
            return

        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(data.get("width", self.width_spin.value()))
        self.height_spin.setValue(data.get("height", self.height_spin.value()))
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)

        color_value = data.get("color")
        if color_value and hasattr(self, "color_mode_combo"):
            idx = self.color_mode_combo.findText(color_value)
            if idx >= 0:
                self.color_mode_combo.setCurrentIndex(idx)

        # Reset combo back to "Custom" to avoid accidental reapply
        self.matrix_preset_combo.blockSignals(True)
        self.matrix_preset_combo.setCurrentIndex(0)
        self.matrix_preset_combo.blockSignals(False)
        self._on_matrix_dimension_changed()

    def _on_matrix_dimension_changed(self):
        """Handle matrix dimension changes with validation."""
        if not self._pattern:
            return
        
        width = self.width_spin.value()
        height = self.height_spin.value()
        
        # Validate dimensions
        max_leds = 10000  # Reasonable limit
        total_leds = width * height
        
        if total_leds > max_leds:
            QMessageBox.warning(
                self,
                "Dimension Too Large",
                f"Matrix dimensions ({width}×{height} = {total_leds} LEDs) exceed the maximum limit of {max_leds} LEDs.\n\n"
                "Please reduce the dimensions."
            )
            # Revert to previous valid values
            self.width_spin.blockSignals(True)
            self.height_spin.blockSignals(True)
            self.width_spin.setValue(self._pattern.metadata.width)
            self.height_spin.setValue(self._pattern.metadata.height)
            self.width_spin.blockSignals(False)
            self.height_spin.blockSignals(False)
            return
        
        metadata = self._pattern.metadata
        metadata.width = width
        metadata.height = height
        self.canvas.set_matrix_size(width, height)
        self._update_canvas_group_height()

        self.layer_manager.resize_pixels(width, height)
        self._load_current_frame_into_canvas()
        self._refresh_timeline()
        self.pattern_modified.emit()
        self._update_status_labels()
        self._maybe_autosync_preview()

    def _on_frame_selected(self, index: int):
        # Commit any pending paint operation before switching frames
        self._commit_paint_operation()
        
        if not self._pattern:
            return
        self.frame_manager.select(index)
        self._current_frame_index = index
        self.history_manager.set_current_frame(index)
        
        # Update layer panel
        if hasattr(self, "layer_panel"):
            self.layer_panel.set_frame_index(index)
        
        self._update_status_labels()

    def _on_add_frame(self):
        """Add a new blank frame after the current frame."""
        if not self._pattern:
            QMessageBox.information(self, "No Pattern", "Create a pattern first before adding frames.")
            return
        
        # Validate frame count limit
        max_frames = 1000
        if len(self._pattern.frames) >= max_frames:
            QMessageBox.warning(
                self,
                "Frame Limit Reached",
                f"Maximum frame count ({max_frames}) reached. Please delete some frames before adding new ones."
            )
            return
        
        self.frame_manager.add_blank_after_current(self._frame_duration_ms)
        self.pattern_modified.emit()
        self._update_status_labels()
        self._maybe_autosync_preview()

    def _on_duplicate_frame(self):
        """Duplicate the current frame."""
        if not self._pattern:
            QMessageBox.information(self, "No Pattern", "Create a pattern first before duplicating frames.")
            return
        
        # Validate frame count limit
        max_frames = 1000
        if len(self._pattern.frames) >= max_frames:
            QMessageBox.warning(
                self,
                "Frame Limit Reached",
                f"Maximum frame count ({max_frames}) reached. Please delete some frames before duplicating."
            )
            return
        
        self.frame_manager.duplicate()
        self.pattern_modified.emit()
        self._update_status_labels()
        self._maybe_autosync_preview()

    def _on_delete_frame(self):
        """Delete the current frame."""
        if not self._pattern or self.state.frame_count() <= 1:
            QMessageBox.warning(
                self,
                "Cannot Delete Frame",
                "At least one frame is required. Create a new pattern or add frames before deleting."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Frame",
            f"Delete frame {self._current_frame_index + 1}?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.frame_manager.delete()
            self.pattern_modified.emit()
            self._update_status_labels()
            self._maybe_autosync_preview()

    def _on_move_frame(self, delta: int):
        if not self._pattern:
            return
        new_index = self._current_frame_index + delta
        if not (0 <= new_index < self.state.frame_count()):
            return
        self.frame_manager.move(self._current_frame_index, new_index)
        self.pattern_modified.emit()
        self._update_status_labels()
        self._maybe_autosync_preview()

    def _on_duration_changed(self, value: int):
        if not self._pattern:
            return
        self._frame_duration_ms = value
        self.frame_manager.set_duration(self._current_frame_index, value)
        self.pattern_modified.emit()
        self._update_status_labels()
        self._maybe_autosync_preview()
        self._update_transport_controls()

    def _on_transport_play(self):
        if not self._pattern or not self._pattern.frames:
            return
        if not self._syncing_playback:
            self._playback_timer.start(self._compute_playback_interval_ms())
            self._update_transport_controls()
            self.playback_state_changed.emit(True)

    def _on_transport_pause(self):
        if not self._syncing_playback:
            if self._playback_timer.isActive():
                self._playback_timer.stop()
                self._update_transport_controls()
                self.playback_state_changed.emit(False)

    def _on_transport_stop(self):
        if not self._syncing_playback:
            if self._playback_timer.isActive():
                self._playback_timer.stop()
            self._update_transport_controls()
            self.playback_state_changed.emit(False)

    def _on_playback_tick(self):
        if not self._pattern or not self._pattern.frames:
            self._on_transport_stop()
            return
        frame_count = len(self._pattern.frames)
        if frame_count <= 1:
            return
        next_index = self._current_frame_index + 1
        if next_index >= frame_count:
            if self._loop_enabled():
                next_index = 0
            else:
                self._on_transport_stop()
                return
        self._select_frame_safely(next_index)

    def _step_frame(self, delta: int, wrap: bool = False):
        if not self._pattern or not self._pattern.frames:
            return
        frame_count = len(self._pattern.frames)
        next_index = self._current_frame_index + delta
        if wrap:
            next_index %= frame_count
        else:
            next_index = max(0, min(frame_count - 1, next_index))
        if next_index != self._current_frame_index:
            self._select_frame_safely(next_index)

    def sync_playback_state(self, is_playing: bool):
        """Sync playback state from another tab (called from signal)"""
        self._syncing_playback = True
        try:
            if is_playing:
                if not self._playback_timer.isActive():  # Not currently playing
                    self._on_transport_play()
            else:
                if self._playback_timer.isActive():  # Currently playing
                    self._on_transport_pause()
        finally:
            self._syncing_playback = False
    
    def sync_frame_selection(self, frame_idx: int):
        """Sync frame selection from another tab (called from signal)"""
        self._syncing_frame = True
        try:
            if self._pattern and 0 <= frame_idx < len(self._pattern.frames):
                self._select_frame_safely(frame_idx)
        finally:
            self._syncing_frame = False

    def _compute_playback_interval_ms(self) -> int:
        fps = max(1, self._get_playback_fps())
        return max(5, int(1000 / fps))

    def _on_playback_fps_changed(self, value: int):
        if value <= 0:
            self._set_playback_fps(1)
            return
        if self._playback_timer.isActive():
            self._playback_timer.start(self._compute_playback_interval_ms())
        self._update_status_labels()

    def _on_playback_loop_toggled(self, _state: bool):
        self._update_transport_controls()
        self._update_status_labels()

    def _update_transport_controls(self):
        has_frames = bool(self._pattern and self._pattern.frames)
        if not has_frames and self._playback_timer.isActive():
            self._playback_timer.stop()
        playing = self._playback_timer.isActive()
        loop_enabled = self._loop_enabled()

        self.playback_play_btn.setEnabled(has_frames and not playing)
        self.playback_pause_btn.setEnabled(has_frames and playing)
        self.playback_stop_btn.setEnabled(has_frames and playing)
        self.playback_prev_btn.setEnabled(has_frames and (loop_enabled or self._current_frame_index > 0))
        if has_frames and self._pattern:
            at_end = self._current_frame_index >= len(self._pattern.frames) - 1
        else:
            at_end = True
        self.playback_next_btn.setEnabled(has_frames and (loop_enabled or not at_end))
        if hasattr(self, "header_loop_toggle"):
            self.header_loop_toggle.setEnabled(has_frames)
        if hasattr(self, "header_fps_spin"):
            self.header_fps_spin.setEnabled(has_frames)
        if hasattr(self, "playback_repeat_label"):
            loop_text = "Loop: ∞" if loop_enabled else "Loop: once"
            self.playback_repeat_label.setText(f"{loop_text} • {self._frame_duration_ms} ms/frame")
        self._update_status_labels()

    def _on_remove_action(self):
        row = self.action_list.currentRow()
        if row < 0:
            return
        self.automation_manager.remove_at(row)

    def _on_clear_actions(self):
        self.automation_manager.clear()

    # ------------------------------------------------------------------
    # Action queue
    # ------------------------------------------------------------------
    def _queue_action(self, label: str, action_type: str, params: Dict[str, object]):
        merged_params = self._create_action_params(action_type, params)
        try:
            merged_params["repeat"] = int(merged_params.get("repeat", 1))
        except (TypeError, ValueError):
            merged_params["repeat"] = 1
        try:
            merged_params["gap_ms"] = max(0, int(merged_params.get("gap_ms", 0)))
        except (TypeError, ValueError):
            merged_params["gap_ms"] = 0
        action = DesignAction(name=label, action_type=action_type, params=merged_params)
        valid, message, _, _ = self._check_action_params(action, mutate=True)
        self.automation_manager.append(action)
        if not valid:
            QMessageBox.warning(
                self,
                "Action Added With Issues",
                f"The new action has validation problems:\n{message}\n\nPlease adjust the parameters in the inspector.",
            )

    def _open_automation_wizard(self) -> None:
        dialog = AutomationWizardDialog(self.ACTION_PARAM_CONFIG, self)
        if dialog.exec():
            for action in dialog.built_actions():
                self._queue_action(action.name, action.action_type, action.params or {})
            hooks_applied = False
            if dialog.apply_fade_in:
                self._apply_linear_fade(True)
                hooks_applied = True
            if dialog.apply_fade_out:
                self._apply_linear_fade(False)
                hooks_applied = True
            if dialog.duplicate_layer:
                self._duplicate_frames_to_overlay()
                hooks_applied = True
            if hooks_applied:
                QMessageBox.information(
                    self,
                    "Post-processing Applied",
                    "Wizard post-processing hooks were applied to the current pattern.",
                )

    def _convert_action_to_instruction(self, action: DesignAction, frame_index: int = 0) -> PatternInstruction:
        """Convert a DesignAction to a PatternInstruction for LMS export."""
        # Map action types to LMS instruction codes
        action_code_map = {
            "scroll": {
                "Left": "moveLeft1",
                "Right": "moveRight1",
                "Up": "moveUp1",
                "Down": "moveDown1",
            },
            "rotate": "rotate90",
            "mirror": {"horizontal": "mirrorH", "vertical": "mirrorV"},
            "invert": "invert",
        }

        action_type = action.action_type
        params = action.params or {}
        
        # Determine LMS instruction code
        lms_code = None
        if action_type == "scroll":
            direction = params.get("direction", "Right")
            lms_code = action_code_map["scroll"].get(direction, "moveRight1")
        elif action_type == "rotate":
            lms_code = "rotate90"
        elif action_type == "mirror":
            axis = params.get("axis", "horizontal")
            lms_code = action_code_map["mirror"].get(axis, "mirrorH")
        elif action_type == "invert":
            lms_code = "invert"
        else:
            # Default fallback - use action type as code
            lms_code = action_type

        # Extract repeat and gap from params
        repeat = params.get("repeat", 1)
        gap = params.get("gap", 0)  # Gap in LMS is frame spacing, not ms
        if isinstance(gap, (int, float)) and gap > 0:
            # Convert ms gap to frame spacing if needed
            gap = int(gap / (self._frame_duration_ms or 50))  # Approximate frame spacing

        # Create instruction
        instruction = LMSInstruction(
            code=lms_code,
            parameters=params,
            repeat=int(repeat) if repeat else 1,
            gap=int(gap) if gap else 0,
        )

        # Create layer binding
        source_frame_idx = params.get("source_frame_index", frame_index)
        source = LayerBinding(
            slot=f"Frame{source_frame_idx + 1}",
            frame_index=source_frame_idx,
            alias=None,
        )

        return PatternInstruction(
            source=source,
            instruction=instruction,
            layer2=None,
            mask=None,
            )

    def _apply_actions_to_frames(self, finalize: bool = False):
        """
        Apply automation actions to frames.
        
        If finalize=True, converts actions to LMS pattern instructions and stores
        them in the pattern. If finalize=False, previews the effect without
        committing to pattern.
        """
        actions = self.automation_manager.actions()
        if not self._pattern or not actions:
            QMessageBox.information(self, "No Actions", "Add actions to the queue first.")
            return

        # If finalizing, convert to pattern instructions and store
        if finalize:
            sequence = PatternInstructionSequence()
            start = self.frame_start_spin.value() - 1 if hasattr(self, "frame_start_spin") else 0
            for idx, action in enumerate(actions):
                instruction = self._convert_action_to_instruction(action, start)
                sequence.add(instruction)

            existing = PatternInstructionSequence.from_list(
                getattr(self._pattern, "lms_pattern_instructions", [])
            )
            for instruction in sequence:
                existing.add(instruction)
            self._set_lms_sequence(existing)
            self.automation_manager.set_actions([])
            if hasattr(self, "timeline"):
                self.timeline.set_selected_action(None)
            self._refresh_timeline()

            QMessageBox.information(
                self,
                "Automation Finalized",
                f"Converted {len(actions)} action(s) to LMS pattern instructions.\n"
                "Instructions stored in pattern for MCU export."
            )
            return

        # Preview mode: simulate instructions and show preview
        if not self._pattern.frames:
            QMessageBox.information(self, "No Frames", "Create frames before previewing automation.")
            return

        sequence = PatternInstructionSequence()
        start = self.frame_start_spin.value() - 1 if hasattr(self, "frame_start_spin") else 0
        for action in actions:
            instruction = self._convert_action_to_instruction(action, start)
            sequence.add(instruction)

        # Simulate and preview
        simulator = PreviewSimulator(self._pattern)
        preview_frames = simulator.simulate_sequence(sequence, max_frames=50)

        if not preview_frames:
            QMessageBox.information(self, "Preview", "No preview frames generated.")
            return

        # Show preview in canvas (temporarily replace pattern)
        original_pattern = self._pattern
        self._pattern = Pattern(
            id=original_pattern.id,
            name=f"{original_pattern.name} (Preview)",
            metadata=original_pattern.metadata,
            frames=preview_frames
        )
        self._current_frame_index = 0
        self._load_current_frame_into_canvas()
        self._refresh_timeline()

        # Restore original after a short delay or on user action
        # For now, just show message - user can click "Finalize" to commit
        QMessageBox.information(
            self,
            "Preview",
            f"Previewing {len(preview_frames)} frame(s) from {len(actions)} instruction(s).\n"
            "Click 'Finalize' to convert to pattern instructions for export."
        )

        # Restore original pattern
        # Validate original_pattern is Pattern object before restoring
        if not isinstance(original_pattern, Pattern):
            raise TypeError(f"Expected Pattern, got {type(original_pattern).__name__}: {original_pattern}")
        self._pattern = original_pattern
        self._load_current_frame_into_canvas()
        self._refresh_timeline()

    def _generate_frames_with_actions(self, actions):
        """Generate new frames by applying actions incrementally."""
        if not self._pattern or not self._pattern.frames:
            QMessageBox.warning(self, "No Source Frame", "Need at least one frame to generate from.")
            return
        
        frame_count = self.generate_frame_count_spin.value()
        if frame_count < 1:
            QMessageBox.warning(self, "Invalid Count", "Frame count must be at least 1.")
            return
        
        # Get source frame (use first frame or current frame)
        source_mode = self.source_button_group.checkedId()
        if source_mode == 0:  # Use first frame
            source_frame_idx = 0
        else:  # Use current frame
            source_frame_idx = self._current_frame_index
        
        if source_frame_idx >= len(self._pattern.frames):
            source_frame_idx = 0
        
        source_frame = self._pattern.frames[source_frame_idx]
        
        # Ask user if they want to replace or append
        reply = QMessageBox.question(
            self,
            "Generate Frames",
            f"Generate {frame_count} frames?\n\n"
            "Replace existing frames or append to pattern?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        # Generate frames
        new_frames = []
        current_pixels = list(source_frame.pixels)
        
        # Use batch processing for large frame counts
        if frame_count > 50:
            progress = QProgressDialog("Generating frames...", "Cancel", 0, frame_count, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
        
        for i in range(frame_count):
            if frame_count > 50:
                if progress.wasCanceled():
                    break
                progress.setValue(i)
                QApplication.processEvents()
            
            # Create a copy of current state
            frame_pixels = list(current_pixels)
            temp_frame = Frame(pixels=frame_pixels, duration_ms=source_frame.duration_ms)
            
            # Apply all actions to this frame
            for action in actions:
                self._apply_action_with_schedule(temp_frame, action)
            
            # Add generated frame
            new_frames.append(temp_frame)
            
            # Update current state for next iteration
            current_pixels = list(temp_frame.pixels)
        
        if frame_count > 50:
            progress.close()
        
        # Replace or append frames
        if reply == QMessageBox.Yes:  # Replace
            self._pattern.frames = new_frames
            self._current_frame_index = 0
        else:  # Append
            self._pattern.frames.extend(new_frames)
            self._current_frame_index = len(self._pattern.frames) - frame_count
        
        # Update UI
        self.history_manager.set_frame_count(len(self._pattern.frames))
        self.history_manager.set_current_frame(self._current_frame_index)
        self.frame_manager.set_pattern(self._pattern)
        self._load_current_frame_into_canvas()
        self._refresh_timeline()
        self._update_status_labels()
        self._maybe_autosync_preview()
        self.pattern_modified.emit()
        
        QMessageBox.information(
            self,
            "Frames Generated",
            f"Successfully generated {frame_count} frames."
        )

    def _apply_action_with_schedule(self, frame: Frame, action: DesignAction) -> int:
        params = action.params or {}
        try:
            repeat = max(1, int(params.get("repeat", 1)))
        except (TypeError, ValueError):
            repeat = 1
        try:
            gap_ms = max(0, int(params.get("gap_ms", 0)))
        except (TypeError, ValueError):
            gap_ms = 0

        changes = 0
        for _ in range(repeat):
            if self._perform_action(frame, action):
                changes += 1

        if gap_ms > 0:
            frame.duration_ms = max(1, int(frame.duration_ms) + gap_ms)

        return changes

    def _perform_action(self, frame: Frame, action: DesignAction) -> bool:
        handlers = {
            "scroll": lambda: self._apply_scroll(frame, action.params.get("direction", "Right"), action.params.get("offset", 1)),
            "rotate": lambda: self._apply_rotate(frame, action.params.get("mode", "90° Clockwise")),
            "mirror": lambda: self._apply_mirror(frame, action.params.get("axis", "horizontal")),
            "flip": lambda: self._apply_flip(frame, action.params.get("axis", "vertical")),
            "invert": lambda: self._apply_invert(frame),
            "wipe": lambda: self._apply_wipe(frame, action.params.get("mode", "Left to Right"), action.params.get("offset", 1)),
            "reveal": lambda: self._apply_reveal(frame, action.params.get("direction", "Left"), action.params.get("offset", 1)),
            "bounce": lambda: self._apply_bounce(frame, action.params.get("axis", "Horizontal")),
            "colour_cycle": lambda: self._apply_colour_cycle(frame, action.params.get("mode", "RGB")),
            "radial": lambda: self._apply_radial(frame, action.params.get("type", "Spiral")),
        }

        handler = handlers.get(action.action_type)
        if not handler:
            self._show_not_implemented(action.name)
            return False
        return handler()

    def _show_not_implemented(self, feature_name: str):
        QMessageBox.information(
            self,
            "Coming Soon",
            f"The action '{feature_name}' is not implemented yet. "
            "It is queued here so workflow remains consistent, but no changes were applied.",
        )

    # ------------------------------------------------------------------
    # Frame transformation helpers
    # ------------------------------------------------------------------
    def _frame_to_grid(self, frame: Frame) -> List[List[Tuple[int, int, int]]]:
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        pixels = list(frame.pixels)
        grid = []
        idx = 0
        for _ in range(height):
            row = pixels[idx:idx + width]
            if len(row) < width:
                row += [(0, 0, 0)] * (width - len(row))
            grid.append(row)
            idx += width
        return grid

    def _grid_to_frame(self, grid: List[List[Tuple[int, int, int]]], frame: Frame):
        frame.pixels = [tuple(pixel) for row in grid for pixel in row]

    def _apply_scroll(self, frame: Frame, direction: str, offset: int = 1) -> bool:
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]

        offsets = {
            "Up": (0, -offset),
            "Down": (0, offset),
            "Left": (-offset, 0),
            "Right": (offset, 0),
        }
        dx, dy = offsets.get(direction, (offset, 0))
        for y in range(height):
            for x in range(width):
                src_x = x - dx
                src_y = y - dy
                if 0 <= src_x < width and 0 <= src_y < height:
                    new_grid[y][x] = grid[src_y][src_x]
        self._grid_to_frame(new_grid, frame)
        return True

    def _apply_rotate(self, frame: Frame, mode: str) -> bool:
        grid = self._frame_to_grid(frame)
        orig_height = len(grid)
        orig_width = len(grid[0])
        clockwise = "clockwise" in mode.lower()

        rotated = []
        if clockwise:
            for x in range(orig_width):
                new_row = []
                for y in range(orig_height - 1, -1, -1):
                    new_row.append(grid[y][x])
                rotated.append(new_row)
        else:
            for x in range(orig_width - 1, -1, -1):
                new_row = []
                for y in range(orig_height):
                    new_row.append(grid[y][x])
                rotated.append(new_row)

        # After rotation, adjust metadata width/height
        self._pattern.metadata.width = orig_height
        self._pattern.metadata.height = orig_width
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(self._pattern.metadata.width)
        self.height_spin.setValue(self._pattern.metadata.height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self.canvas.set_matrix_size(self._pattern.metadata.width, self._pattern.metadata.height)
        self._grid_to_frame(rotated, frame)
        return True

    def _apply_mirror(self, frame: Frame, axis: str) -> bool:
        grid = self._frame_to_grid(frame)
        axis = axis.lower()
        if axis == "horizontal":
            new_grid = [list(reversed(row)) for row in grid]
        elif axis == "vertical":
            new_grid = list(reversed(grid))
        else:
            return False
        self._grid_to_frame(new_grid, frame)
        return True

    def _apply_flip(self, frame: Frame, axis: str) -> bool:
        grid = self._frame_to_grid(frame)
        axis = axis.lower()
        if axis == "vertical":
            new_grid = list(reversed(grid))
        elif axis == "horizontal":
            new_grid = [list(reversed(row)) for row in grid]
        else:
            return False
        self._grid_to_frame(new_grid, frame)
        return True

    def _apply_invert(self, frame: Frame) -> bool:
        frame.pixels = [(255 - r, 255 - g, 255 - b) for r, g, b in frame.pixels]
        return True

    def _apply_wipe(self, frame: Frame, mode: str, offset: int = 1) -> bool:
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        mode = mode.lower()
        if "left" in mode and "right" in mode:
            direction = "horizontal"
            forward = "left" in mode.split("to")[0]
        elif "top" in mode or "bottom" in mode:
            direction = "vertical"
            forward = "top" in mode.split("to")[0]
        else:
            direction = "horizontal"
            forward = True

        if direction == "horizontal":
            for y in range(height):
                row = grid[y]
                ordered = row if forward else list(reversed(row))
                # Apply offset - wipe progresses by offset pixels
                wipe_pos = min(offset, width)
                for x in range(width):
                    fade = 1.0 if x < wipe_pos else max(0.0, 1.0 - (x - wipe_pos) / max(1, width - wipe_pos))
                    r, g, b = ordered[x]
                    ordered[x] = (int(r * fade), int(g * fade), int(b * fade))
                if not forward:
                    ordered.reverse()
                grid[y] = ordered
        else:
            ordered_rows = grid if forward else list(reversed(grid))
            # Apply offset
            wipe_pos = min(offset, height)
            for idx, row in enumerate(ordered_rows):
                fade = 1.0 if idx < wipe_pos else max(0.0, 1.0 - (idx - wipe_pos) / max(1, height - wipe_pos))
                ordered_rows[idx] = [(int(r * fade), int(g * fade), int(b * fade)) for r, g, b in row]
            if not forward:
                ordered_rows.reverse()
            grid = ordered_rows

        self._grid_to_frame(grid, frame)
        return True

    def _apply_reveal(self, frame: Frame, direction: str, offset: int = 1) -> bool:
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        direction = direction.lower()

        mask_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        if direction == "left":
            # Reveal from left, offset pixels
            reveal_width = min(offset, width)
            for y in range(height):
                for x in range(reveal_width):
                    mask_grid[y][x] = grid[y][x]
        elif direction == "right":
            # Reveal from right, offset pixels
            reveal_width = min(offset, width)
            for y in range(height):
                for x in range(width - reveal_width, width):
                    mask_grid[y][x] = grid[y][x]
        elif direction == "top":
            # Reveal from top, offset pixels
            reveal_height = min(offset, height)
            for y in range(reveal_height):
                mask_grid[y] = list(grid[y])
        elif direction == "bottom":
            # Reveal from bottom, offset pixels
            reveal_height = min(offset, height)
            for y in range(height - reveal_height, height):
                mask_grid[y] = list(grid[y])
        else:
            return False

        self._grid_to_frame(mask_grid, frame)
        return True

    def _apply_bounce(self, frame: Frame, axis: str) -> bool:
        """Apply bounce effect (ping-pong scroll)."""
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        axis = axis.lower()
        
        # Simple bounce: reverse direction at edges
        if axis == "horizontal":
            # Mirror horizontally to simulate bounce
            new_grid = [list(reversed(row)) for row in grid]
        else:  # vertical
            # Mirror vertically to simulate bounce
            new_grid = list(reversed(grid))
        
        self._grid_to_frame(new_grid, frame)
        return True

    def _apply_colour_cycle(self, frame: Frame, mode: str) -> bool:
        """Apply colour cycling effect."""
        mode = mode.lower()
        
        if mode == "rgb":
            # Cycle RGB channels
            new_pixels = []
            for r, g, b in frame.pixels:
                new_pixels.append((g, b, r))  # Shift RGB -> GBR
            frame.pixels = new_pixels
        elif mode == "ryb":
            # Cycle RYB (Red-Yellow-Blue)
            new_pixels = []
            for r, g, b in frame.pixels:
                # Convert to RYB-like cycle
                new_pixels.append((b, r, g))
            frame.pixels = new_pixels
        else:  # custom or default
            # Simple hue shift
            new_pixels = []
            for r, g, b in frame.pixels:
                new_pixels.append((b, r, g))
            frame.pixels = new_pixels
        
        return True

    def _apply_radial(self, frame: Frame, type: str) -> bool:
        """Apply radial effect (spiral, pulse, sweep)."""
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        type = type.lower()
        
        center_x = width / 2.0
        center_y = height / 2.0
        max_dist = ((center_x) ** 2 + (center_y) ** 2) ** 0.5
        
        new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        if type == "spiral":
            # Spiral effect: rotate pixels around center
            for y in range(height):
                for x in range(width):
                    dx = x - center_x
                    dy = y - center_y
                    angle = (dx ** 2 + dy ** 2) ** 0.5 * 0.5  # Spiral angle
                    new_x = int(center_x + dx * 0.9 - dy * 0.1)
                    new_y = int(center_y + dy * 0.9 + dx * 0.1)
                    if 0 <= new_x < width and 0 <= new_y < height:
                        new_grid[new_y][new_x] = grid[y][x]
        elif type == "pulse":
            # Pulse effect: intensity based on distance from center
            for y in range(height):
                for x in range(width):
                    dx = x - center_x
                    dy = y - center_y
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    factor = 1.0 - (dist / max_dist) * 0.5
                    r, g, b = grid[y][x]
                    new_grid[y][x] = (
                        int(r * factor),
                        int(g * factor),
                        int(b * factor)
                    )
        else:  # sweep
            # Sweep effect: radial wipe
            for y in range(height):
                for x in range(width):
                    dx = x - center_x
                    dy = y - center_y
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    if dist < max_dist * 0.7:
                        new_grid[y][x] = grid[y][x]
        
        self._grid_to_frame(new_grid, frame)
        return True

    def _preview_custom_effect(self, effect_name: str, intensity: int):
        """Preview a custom effect on the current frame."""
        if not self._pattern or not self._pattern.frames:
            return
        
        import copy
        if not hasattr(self, '_preview_pattern_backup'):
            self._preview_pattern_backup = copy.deepcopy(self._pattern)
        
        temp_pattern = copy.deepcopy(self._preview_pattern_backup)
        frame = temp_pattern.frames[self._current_frame_index]
        self._apply_custom_effect_to_frame(frame, effect_name, intensity)
        
        # Show preview temporarily
        original_pattern = self._pattern
        # Validate temp_pattern is Pattern object before assignment
        if not isinstance(temp_pattern, Pattern):
            raise TypeError(f"Expected Pattern, got {type(temp_pattern).__name__}: {temp_pattern}")
        self._pattern = temp_pattern
        self._load_current_frame_into_canvas()
        # Validate original_pattern is Pattern object before restoring
        if not isinstance(original_pattern, Pattern):
            raise TypeError(f"Expected Pattern, got {type(original_pattern).__name__}: {original_pattern}")
        self._pattern = original_pattern

    def _apply_custom_effect(self, effect_name: str, intensity: int):
        """Apply custom effect to selected frame range."""
        if not self._pattern or not self._pattern.frames:
            return
        
        start = self.frame_start_spin.value() - 1
        end = self.frame_end_spin.value() - 1
        if start < 0:
            start = 0
        if end >= len(self._pattern.frames):
            end = len(self._pattern.frames) - 1
        
        for idx in range(start, end + 1):
            self._apply_custom_effect_to_frame(self._pattern.frames[idx], effect_name, intensity)

    def _apply_custom_effect_to_frame(self, frame: Frame, effect_name: str, intensity: int):
        """Apply a custom effect to a single frame."""
        factor = intensity / 100.0
        
        if effect_name == "Fade In/Out":
            new_pixels = []
            for r, g, b in frame.pixels:
                fade = factor
                new_pixels.append((
                    int(r * fade),
                    int(g * fade),
                    int(b * fade)
                ))
            frame.pixels = new_pixels
            
        elif effect_name == "Blur":
            grid = self._frame_to_grid(frame)
            width = len(grid[0])
            height = len(grid)
            blur_amount = int(factor * 2) + 1
            
            new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
            for y in range(height):
                for x in range(width):
                    r_sum, g_sum, b_sum = 0, 0, 0
                    count = 0
                    for dy in range(-blur_amount, blur_amount + 1):
                        for dx in range(-blur_amount, blur_amount + 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < height and 0 <= nx < width:
                                r, g, b = grid[ny][nx]
                                r_sum += r
                                g_sum += g
                                b_sum += b
                                count += 1
                    if count > 0:
                        new_grid[y][x] = (
                            int(r_sum / count),
                            int(g_sum / count),
                            int(b_sum / count)
                        )
            self._grid_to_frame(new_grid, frame)
            
        elif effect_name == "Sharpen":
            # Sharpen using unsharp mask technique
            grid = self._frame_to_grid(frame)
            width = len(grid[0])
            height = len(grid)
            sharpen_strength = factor * 2.0  # 0-2.0 range
            
            # Create a blurred copy for unsharp mask
            blur_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
            for y in range(height):
                for x in range(width):
                    r_sum, g_sum, b_sum = 0, 0, 0
                    count = 0
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < height and 0 <= nx < width:
                                r, g, b = grid[ny][nx]
                                r_sum += r
                                g_sum += g
                                b_sum += b
                                count += 1
                    if count > 0:
                        blur_grid[y][x] = (
                            int(r_sum / count),
                            int(g_sum / count),
                            int(b_sum / count)
                        )
            
            # Apply unsharp mask: original + (original - blurred) * strength
            new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
            for y in range(height):
                for x in range(width):
                    orig_r, orig_g, orig_b = grid[y][x]
                    blur_r, blur_g, blur_b = blur_grid[y][x]
                    
                    # Calculate difference and apply sharpening
                    diff_r = orig_r - blur_r
                    diff_g = orig_g - blur_g
                    diff_b = orig_b - blur_b
                    
                    new_r = int(orig_r + diff_r * sharpen_strength)
                    new_g = int(orig_g + diff_g * sharpen_strength)
                    new_b = int(orig_b + diff_b * sharpen_strength)
                    
                    new_grid[y][x] = (
                        max(0, min(255, new_r)),
                        max(0, min(255, new_g)),
                        max(0, min(255, new_b))
                    )
            self._grid_to_frame(new_grid, frame)
            
        elif effect_name == "Brightness Adjust":
            brightness_delta = int((factor - 0.5) * 255)
            new_pixels = []
            for r, g, b in frame.pixels:
                new_pixels.append((
                    max(0, min(255, r + brightness_delta)),
                    max(0, min(255, g + brightness_delta)),
                    max(0, min(255, b + brightness_delta))
                ))
            frame.pixels = new_pixels
            
        elif effect_name == "Contrast Adjust":
            contrast_factor = (factor - 0.5) * 2.0
            new_pixels = []
            for r, g, b in frame.pixels:
                r_new = int(128 + (r - 128) * (1 + contrast_factor))
                g_new = int(128 + (g - 128) * (1 + contrast_factor))
                b_new = int(128 + (b - 128) * (1 + contrast_factor))
                new_pixels.append((
                    max(0, min(255, r_new)),
                    max(0, min(255, g_new)),
                    max(0, min(255, b_new))
                ))
            frame.pixels = new_pixels
            
        elif effect_name == "Color Shift":
            shift_amount = int(factor * 360)
            new_pixels = []
            for r, g, b in frame.pixels:
                if shift_amount < 120:
                    new_pixels.append((g, b, r))
                elif shift_amount < 240:
                    new_pixels.append((b, r, g))
                else:
                    new_pixels.append((r, g, b))
            frame.pixels = new_pixels
            
        elif effect_name == "Noise":
            import random
            noise_amount = int(factor * 50)
            new_pixels = []
            for r, g, b in frame.pixels:
                noise_r = random.randint(-noise_amount, noise_amount)
                noise_g = random.randint(-noise_amount, noise_amount)
                noise_b = random.randint(-noise_amount, noise_amount)
                new_pixels.append((
                    max(0, min(255, r + noise_r)),
                    max(0, min(255, g + noise_g)),
                    max(0, min(255, b + noise_b))
                ))
            frame.pixels = new_pixels
            
        elif effect_name == "Pixelate":
            grid = self._frame_to_grid(frame)
            width = len(grid[0])
            height = len(grid)
            pixel_size = max(1, int((1.0 - factor) * 8) + 1)
            
            new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
            for y in range(0, height, pixel_size):
                for x in range(0, width, pixel_size):
                    r_sum, g_sum, b_sum = 0, 0, 0
                    count = 0
                    for dy in range(pixel_size):
                        for dx in range(pixel_size):
                            ny, nx = y + dy, x + dx
                            if ny < height and nx < width:
                                r, g, b = grid[ny][nx]
                                r_sum += r
                                g_sum += g
                                b_sum += b
                                count += 1
                    if count > 0:
                        avg_color = (
                            int(r_sum / count),
                            int(g_sum / count),
                            int(b_sum / count)
                        )
                        for dy in range(pixel_size):
                            for dx in range(pixel_size):
                                ny, nx = y + dy, x + dx
                                if ny < height and nx < width:
                                    new_grid[ny][nx] = avg_color
            self._grid_to_frame(new_grid, frame)

    def _optimize_rgb_pattern(self, pattern: Pattern) -> Pattern:
        """Optimize RGB pattern by removing duplicate frames and compressing colors."""
        if not pattern or not pattern.frames:
            return pattern
        
        # Remove duplicate consecutive frames
        optimized_frames = []
        last_frame_pixels = None
        for frame in pattern.frames:
            if frame.pixels != last_frame_pixels:
                optimized_frames.append(frame)
                last_frame_pixels = frame.pixels
        
        # Create optimized pattern
        from core.pattern import Pattern as PatternClass
        optimized_pattern = PatternClass(
            name=pattern.name + " (Optimized)",
            metadata=pattern.metadata,
            frames=optimized_frames
        )
        return optimized_pattern

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _refresh_timeline(self):
        if self._suspend_timeline_refresh:
            return
        if not self._pattern:
            self.timeline.set_frames([])
            self.timeline.set_markers([])
            self.timeline.set_overlays([])
            self.timeline.set_layer_tracks([])
            return

        frames_data: List[Tuple[str, Optional[QPixmap]]] = []
        for idx, frame in enumerate(self._pattern.frames):
            pixel_count = len(frame.pixels) if frame.pixels else 0
            display = f"Frame {idx + 1:02d}  •  {frame.duration_ms} ms  •  {pixel_count} px"
            frames_data.append((display, self._make_frame_thumbnail(frame)))
        self.timeline.set_frames(frames_data)
        self.timeline.set_playhead(self._current_frame_index)

        total_frames = len(self._pattern.frames)
        self.frame_start_spin.setMaximum(total_frames)
        self.frame_end_spin.setMaximum(total_frames)
        self.frame_end_spin.setValue(total_frames)

        markers: List[TimelineMarker] = []
        start_idx = self.frame_start_spin.value() - 1
        end_idx = self.frame_end_spin.value() - 1
        if 0 <= start_idx < total_frames:
            markers.append(TimelineMarker(frame_index=start_idx, label="Start"))
        if 0 <= end_idx < total_frames:
            markers.append(TimelineMarker(frame_index=end_idx, label="End", color=QColor("#E55B5B")))
        self.timeline.set_markers(markers)

        overlays = self._build_timeline_overlays(total_frames)
        self.timeline.set_overlays(overlays)

        layer_tracks = self._build_timeline_layer_tracks(total_frames)
        self.timeline.set_layer_tracks(layer_tracks)
        if hasattr(self, "layer_panel") and self.layer_panel:
            self.timeline.set_selected_layer(self.layer_panel.get_active_layer_index())
        self._update_transport_controls()
        self._update_status_labels()

    def _on_layers_structure_updated(self, *args):
        if self._suspend_timeline_refresh:
            return
        self._refresh_timeline()

    def _select_frame_safely(self, index: int):
        if not self._pattern or not self._pattern.frames:
            return
        index = max(0, min(len(self._pattern.frames) - 1, index))
        old_index = self._current_frame_index
        self.frame_manager.select(index)
        self._update_status_labels()
        self._maybe_autosync_preview()
        # Emit frame changed signal (if not syncing to prevent loops)
        if not self._syncing_frame and index != old_index:
            self.frame_changed.emit(index)

    def _load_current_frame_into_canvas(self):
        if not self._pattern:
            return
        
        # Get composite pixels from layers
        if hasattr(self, "layer_panel"):
            composite = self.layer_manager.get_composite_pixels(self._current_frame_index)
            self.canvas.set_frame_pixels(composite)
        else:
            # Fallback to direct frame loading
            self.canvas_controller.render_frame(self._current_frame_index)
        
        self._update_status_labels()

    def _make_frame_thumbnail(self, frame: Frame) -> Optional[QPixmap]:
        if not frame.pixels:
            return None
        if self._pattern and self._pattern.metadata:
            width = max(1, self._pattern.metadata.width)
            height = max(1, self._pattern.metadata.height)
        else:
            width = max(1, int(len(frame.pixels) ** 0.5))
            height = max(1, len(frame.pixels) // width)
        image = QImage(width, height, QImage.Format_RGB32)
        image.fill(QColor(0, 0, 0))
        limit = width * height
        for idx, pixel in enumerate(frame.pixels[:limit]):
            if pixel is None:
                continue
            x = idx % width
            y = idx // width
            r, g, b = pixel
            image.setPixelColor(x, y, QColor(r, g, b))
        return QPixmap.fromImage(image).scaled(
            self._thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    def _build_timeline_overlays(self, total_frames: int) -> List[TimelineOverlay]:
        overlays: List[TimelineOverlay] = []
        actions = self.automation_manager.actions()
        if not actions or total_frames == 0:
            return overlays

        start_idx = max(0, self.frame_start_spin.value() - 1)
        end_idx = min(total_frames - 1, self.frame_end_spin.value() - 1)

        for idx, action in enumerate(actions):
            color = self._timeline_action_color(action.action_type, idx)
            tooltip = self._build_overlay_tooltip(action, start_idx, end_idx)
            overlays.append(
                TimelineOverlay(
                    start_frame=start_idx,
                    end_frame=end_idx,
                    label=action.name,
                    color=color,
                    action_index=idx,
                    tooltip=tooltip,
                )
            )
        return overlays

    def _build_timeline_layer_tracks(self, total_frames: int) -> List[TimelineLayerTrack]:
        if not self._pattern or total_frames <= 0:
            return []

        frame_layers: List[List[Layer]] = []
        max_layers = 0
        for frame_idx in range(total_frames):
            layers = self.layer_manager.get_layers(frame_idx)
            frame_layers.append(layers)
            if len(layers) > max_layers:
                max_layers = len(layers)

        if max_layers == 0:
            return []

        palette = self._layer_track_palette()
        tracks: List[TimelineLayerTrack] = []
        for layer_idx in range(max_layers):
            states: List[int] = []
            layer_name: Optional[str] = None
            for layers in frame_layers:
                if layer_idx < len(layers):
                    layer = layers[layer_idx]
                    if not layer_name and getattr(layer, "name", None):
                        layer_name = layer.name
                    has_pixels = self._layer_has_content(layer)
                    if not has_pixels:
                        states.append(3)
                    else:
                        states.append(2 if layer.visible else 1)
                else:
                    states.append(0)
            color = QColor(palette[layer_idx % len(palette)])
            tracks.append(
                TimelineLayerTrack(
                    name=layer_name or f"Layer {layer_idx + 1}",
                    states=states,
                    color=color,
                )
            )
        return tracks

    def _layer_has_content(self, layer: Layer) -> bool:
        pixels = getattr(layer, "pixels", [])
        for pixel in pixels:
            if not pixel:
                continue
            try:
                r, g, b = pixel
            except Exception:
                continue
            if r or g or b:
                return True
        return False

    def _layer_track_palette(self) -> List[str]:
        return ["#4C8BF5", "#7A7CFF", "#3FB983", "#F3A533", "#E55B5B", "#5BC0DE"]

    def _build_overlay_tooltip(self, action: DesignAction, start_idx: int, end_idx: int) -> str:
        frames_text = (
            f"Frame {start_idx + 1}"
            if start_idx == end_idx
            else f"Frames {start_idx + 1}–{end_idx + 1}"
        )
        params_dict = dict(action.params) if action.params else {}
        repeat = int(params_dict.pop("repeat", 1) or 1)
        gap_ms = int(params_dict.pop("gap_ms", 0) or 0)
        params = ", ".join(f"{key}={value}" for key, value in params_dict.items()) if params_dict else ""
        valid, message, _, _ = self._check_action_params(action, mutate=False)
        prefix = "" if valid else "⚠ "
        schedule_bits = []
        if repeat > 1:
            schedule_bits.append(f"repeat×{repeat}")
        if gap_ms > 0:
            schedule_bits.append(f"gap={gap_ms}ms")
        schedule_suffix = f" • {'; '.join(schedule_bits)}" if schedule_bits else ""
        if params:
            return f"{prefix}{action.name} • {params}{schedule_suffix}"
        return f"{prefix}{action.name}{schedule_suffix}"

    def _timeline_action_color(self, action_type: str, idx: int) -> QColor:
        palette = {
            "scroll": "#4C8BF5",
            "rotate": "#7A7CFF",
            "mirror": "#3FB983",
            "flip": "#F3A533",
            "invert": "#E55B5B",
            "wipe": "#5BC0DE",
            "reveal": "#FF7EB6",
        }
        base = palette.get(action_type, "#888888")
        color = QColor(base)
        color = color.lighter(100 + (idx % 3) * 10)
        return color

    def _on_manager_frame_selected(self, index: int):
        if not self._pattern:
            return
        # Defensive check: ensure pattern is Pattern object, not tuple
        if not isinstance(self._pattern, Pattern):
            return  # Pattern state corrupted, skip update
        
        # Check if pattern has frames before accessing
        if not self._pattern.frames:
            return  # No frames available, skip update
        
        self._current_frame_index = index
        try:
            frame = self.frame_manager.frame(index)
            self._frame_duration_ms = frame.duration_ms
        except RuntimeError:
            # No frames available, skip update
            return
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(self._frame_duration_ms)
        self.duration_spin.blockSignals(False)
        self.timeline.set_playhead(index)
        self._load_current_frame_into_canvas()
        self._update_transport_controls()

    def _on_manager_duration_changed(self, index: int, duration: int):
        if index == self._current_frame_index:
            self._frame_duration_ms = duration
            self.duration_spin.blockSignals(True)
            self.duration_spin.setValue(duration)
            self.duration_spin.blockSignals(False)
        self._refresh_timeline()

    def _on_manager_queue_changed(self, actions: list):
        current_row = self.action_list.currentRow()
        self.action_list.blockSignals(True)
        self.action_list.clear()
        for action in actions:
            summary = self._describe_action_for_list(action)
            self.action_list.addItem(summary)
        self.action_list.blockSignals(False)
        if actions:
            new_row = current_row if 0 <= current_row < len(actions) else min(len(actions) - 1, max(0, current_row))
            self.action_list.setCurrentRow(new_row)
            self._load_action_into_inspector(new_row, actions[new_row])
            self.timeline.set_selected_action(new_row)
        else:
            self.action_list.setCurrentRow(-1)
            self._clear_action_inspector()
            self.timeline.set_selected_action(None)
        self._refresh_timeline()
        has_actions = bool(actions)
        if hasattr(self, "apply_actions_btn"):
            self.apply_actions_btn.setEnabled(has_actions)
        if hasattr(self, "finalize_actions_btn"):
            self.finalize_actions_btn.setEnabled(has_actions)

    def _describe_action_for_list(self, action: DesignAction) -> str:
        params_dict = dict(action.params) if action.params else {}
        repeat = int(params_dict.pop("repeat", 1) or 1)
        gap_ms = int(params_dict.pop("gap_ms", 0) or 0)
        params = ", ".join(f"{key}={value}" for key, value in params_dict.items()) if params_dict else ""
        valid, message, _, _ = self._check_action_params(action, mutate=False)
        prefix = "" if valid else "⚠ "
        schedule_bits = []
        if repeat > 1:
            schedule_bits.append(f"repeat×{repeat}")
        if gap_ms > 0:
            schedule_bits.append(f"gap={gap_ms}ms")
        schedule_suffix = f" • {'; '.join(schedule_bits)}" if schedule_bits else ""
        if params:
            return f"{prefix}{action.name} • {params}{schedule_suffix}"
        return f"{prefix}{action.name}{schedule_suffix}"

    def _on_action_list_selection(self, row: int):
        actions = self.automation_manager.actions()
        if 0 <= row < len(actions):
            self._load_action_into_inspector(row, actions[row])
            self.timeline.set_selected_action(row)
        else:
            self._clear_action_inspector()
            self.timeline.set_selected_action(None)

    def _load_action_into_inspector(self, index: int, action: DesignAction):
        self._current_action_index = index
        self._updating_action_inspector = True
        try:
            self.action_inspector_group.setEnabled(True)
            self.action_name_edit.setText(action.name)
            self.action_type_label.setText(action.action_type.replace("_", " ").title())
            self.action_validation_label.hide()
            self.action_validation_label.clear()
            self.action_preview_label.clear()
            self.action_preview_label.hide()
            # clear existing widgets
            while self.action_param_layout.rowCount():
                self.action_param_layout.removeRow(0)
            self.action_parameter_widgets.clear()
            self._param_error_labels.clear()
            self._param_description_labels.clear()
            self._param_error_state = {}

            param_config = self.ACTION_PARAM_CONFIG.get(action.action_type, {})
            current_params = dict(action.params)
            if param_config:
                for key, cfg in param_config.items():
                    widget, meta = self._create_param_widget(key, cfg, current_params.get(key))
                    self.action_parameter_widgets[key] = (widget, meta)
                    self._add_param_row(key, cfg, widget)

                for key in current_params.keys():
                    if key not in param_config:
                        extra_cfg = {"type": "string", "label": key.title()}
                        widget, meta = self._create_param_widget(key, extra_cfg, current_params[key])
                        self.action_parameter_widgets[key] = (widget, meta)
                        self._add_param_row(key, extra_cfg, widget)
            else:
                for key, value in current_params.items():
                    extra_cfg = {"type": "string", "label": key.title()}
                    widget, meta = self._create_param_widget(key, extra_cfg, value)
                    self.action_parameter_widgets[key] = (widget, meta)
                    self._add_param_row(key, extra_cfg, widget)

            if not self.action_parameter_widgets:
                info_label = QLabel("This action does not expose editable parameters.")
                info_label.setObjectName("ParamDescriptionLabel")
                info_label.setWordWrap(True)
                placeholder = QWidget()
                info_layout = QVBoxLayout(placeholder)
                info_layout.setContentsMargins(0, 0, 0, 0)
                info_layout.addWidget(info_label)
                self.action_param_layout.addRow("", placeholder)

            self._update_action_validation(action)
        finally:
            self._updating_action_inspector = False

    def _clear_action_inspector(self):
        self._current_action_index = -1
        self.action_inspector_group.setEnabled(False)
        self.action_name_edit.clear()
        self.action_type_label.setText("-")
        self.action_validation_label.hide()
        self.action_validation_label.clear()
        self.action_preview_label.clear()
        self.action_preview_label.hide()
        while self.action_param_layout.rowCount():
            self.action_param_layout.removeRow(0)
        self.action_parameter_widgets.clear()
        self._param_error_labels.clear()
        self._param_description_labels.clear()
        self._param_error_state = {}
        self.timeline.set_selected_action(None)

    def _on_action_name_edited(self):
        if self._updating_action_inspector:
            return
        index = getattr(self, "_current_action_index", -1)
        if index < 0:
            return
        name = self.action_name_edit.text().strip() or "Action"
        actions = self.automation_manager.actions()
        if 0 <= index < len(actions):
            actions[index].name = name
            self.automation_manager.set_actions(actions)

    def _on_action_param_changed(self, param: str, value):
        if self._updating_action_inspector:
            return
        index = getattr(self, "_current_action_index", -1)
        if index < 0:
            return
        actions = self.automation_manager.actions()
        if 0 <= index < len(actions):
            actions[index].params[param] = value
            self.automation_manager.set_actions(actions)
            self._update_action_validation(actions[index])

    def _on_param_line_edit_finished(self, param: str, widget: QLineEdit):
        self._on_action_param_changed(param, widget.text())

    def _create_param_widget(self, key: str, cfg: Dict[str, object], current_value):
        field_type = cfg.get("type", "string")
        default = cfg.get("default")
        value = current_value if current_value is not None else default
        meta = dict(cfg)

        try:
            if field_type == "choice":
                widget = QComboBox()
                for choice in cfg.get("choices", []):
                    widget.addItem(str(choice))
                if value in cfg.get("choices", []):
                    widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(partial(self._on_action_param_changed, key))
            elif field_type == "int":
                widget = QSpinBox()
                widget.setRange(int(cfg.get("min", -9999)), int(cfg.get("max", 9999)))
                if "step" in cfg:
                    widget.setSingleStep(int(cfg["step"]))
                if value is None:
                    value = cfg.get("min", 0)
                widget.setValue(int(value))
                widget.valueChanged.connect(partial(self._on_action_param_changed, key))
            elif field_type == "float":
                widget = QDoubleSpinBox()
                widget.setRange(float(cfg.get("min", -9999.0)), float(cfg.get("max", 9999.0)))
                if "step" in cfg:
                    widget.setSingleStep(float(cfg["step"]))
                widget.setDecimals(int(cfg.get("decimals", 2)))
                if value is None:
                    value = cfg.get("min", 0.0)
                widget.setValue(float(value))
                widget.valueChanged.connect(partial(self._on_action_param_changed, key))
            elif field_type == "bool":
                widget = QCheckBox()
                widget.setChecked(bool(value))
                widget.toggled.connect(partial(self._on_action_param_changed, key))
            else:
                widget = QLineEdit(str(value) if value is not None else "")
                widget.editingFinished.connect(partial(self._on_param_line_edit_finished, key, widget))
        except (ValueError, TypeError):
            # Fallback to line edit if conversion fails
            widget = QLineEdit(str(value) if value is not None else "")
            widget.editingFinished.connect(partial(self._on_param_line_edit_finished, key, widget))
            meta["type"] = "string"
        return widget, meta

    def _add_param_row(self, key: str, cfg: Dict[str, object], widget: QWidget):
        label_text = cfg.get("label", key.title())
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(widget)

        desc = cfg.get("description")
        if desc:
            desc_label = QLabel(desc)
            desc_label.setObjectName("ParamDescriptionLabel")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
            self._param_description_labels[key] = desc_label

        error_label = QLabel()
        error_label.setObjectName("ParamErrorLabel")
        error_label.setWordWrap(True)
        error_label.hide()
        layout.addWidget(error_label)
        self._param_error_labels[key] = error_label

        self.action_param_layout.addRow(label_text, container)

    def _set_widget_error_state(self, widget: Optional[QWidget], has_error: bool):
        if widget is None:
            return
        widget.setProperty("hasError", "true" if has_error else "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _set_param_error(self, key: str, message: Optional[str]):
        label = self._param_error_labels.get(key)
        if label:
            if message:
                label.setText(message)
                label.show()
            else:
                label.hide()
                label.clear()
        widget_meta = self.action_parameter_widgets.get(key)
        widget = widget_meta[0] if widget_meta else None
        self._set_widget_error_state(widget, bool(message))

    def _update_action_validation(self, action: DesignAction):
        valid, message = self._validate_action(action)
        for key in self._param_error_labels.keys():
            self._set_param_error(key, self._param_error_state.get(key))
        if valid:
            self.action_validation_label.hide()
            self.action_validation_label.clear()
        else:
            self.action_validation_label.setText(message or "Resolve parameter errors.")
            self.action_validation_label.show()
        preview = self._build_action_preview(action)
        if preview:
            self.action_preview_label.setText(preview)
            self.action_preview_label.show()
        else:
            self.action_preview_label.hide()
        if 0 <= self._current_action_index < self.action_list.count():
            self._refresh_action_list_item(self._current_action_index, action)

    def _build_action_preview(self, action: DesignAction) -> str:
        params = action.params or {}
        if not params:
            return f"{action.action_type.title()} (default settings)"
        return f"{action.action_type.title()}: " + ", ".join(f"{k}={v}" for k, v in params.items())

    def _refresh_action_list_item(self, index: int, action: DesignAction):
        if not (0 <= index < self.action_list.count()):
            return
        self.action_list.blockSignals(True)
        self.action_list.item(index).setText(self._describe_action_for_list(action))
        self.action_list.blockSignals(False)

    def _validate_action(self, action: DesignAction) -> Tuple[bool, str]:
        valid, message, errors, _ = self._check_action_params(action, mutate=True)
        self._param_error_state = errors
        return valid, message

    def _check_action_params(
        self, action: DesignAction, mutate: bool = False
    ) -> Tuple[bool, str, Dict[str, str], Dict[str, object]]:
        config = self.ACTION_PARAM_CONFIG.get(action.action_type, {})
        original_params = dict(action.params or {})
        normalized: Dict[str, object] = dict(original_params)
        errors: Dict[str, str] = {}

        for key, cfg in config.items():
            label = cfg.get("label", key.title())
            value = original_params.get(key)
            default = cfg.get("default")
            if value in (None, ""):
                if cfg.get("required"):
                    errors[key] = f"{label} is required."
                    continue
                if default is not None:
                    normalized[key] = default
                continue

            field_type = cfg.get("type", "string")
            try:
                if field_type == "int":
                    value = int(value)
                    min_value = cfg.get("min")
                    max_value = cfg.get("max")
                    if min_value is not None and value < min_value:
                        errors[key] = f"{label} must be ≥ {min_value}."
                        continue
                    if max_value is not None and value > max_value:
                        errors[key] = f"{label} must be ≤ {max_value}."
                        continue
                elif field_type == "float":
                    value = float(value)
                    min_value = cfg.get("min")
                    max_value = cfg.get("max")
                    if min_value is not None and value < min_value:
                        errors[key] = f"{label} must be ≥ {min_value}."
                        continue
                    if max_value is not None and value > max_value:
                        errors[key] = f"{label} must be ≤ {max_value}."
                        continue
                elif field_type == "choice":
                    choices = cfg.get("choices", [])
                    if value not in choices:
                        errors[key] = f"{label} must be one of {', '.join(map(str, choices))}."
                        continue
                elif field_type == "bool":
                    if isinstance(value, str):
                        value = value.lower() in ("1", "true", "yes", "on")
                    else:
                        value = bool(value)
                else:
                    value = str(value).strip()
                    if cfg.get("required") and not value:
                        errors[key] = f"{label} cannot be empty."
                        continue
            except (ValueError, TypeError):
                errors[key] = f"{label} is not a valid {field_type}."
                continue

            normalized[key] = value

        if mutate:
            action.params = normalized

        valid = not errors
        message = "; ".join(errors.values())
        return valid, message, errors, normalized

    def _validate_all_actions(self, actions: List[DesignAction]) -> Tuple[bool, str]:
        issues = []
        for idx, action in enumerate(actions, start=1):
            valid, message, _, _ = self._check_action_params(action, mutate=True)
            if not valid:
                issues.append(f"Action {idx} ('{action.name}'): {message}")
        return (len(issues) == 0, "\n".join(issues))

    def _create_action_params(self, action_type: str, overrides: Optional[Dict[str, object]]) -> Dict[str, object]:
        params: Dict[str, object] = {}
        config = self.ACTION_PARAM_CONFIG.get(action_type, {})
        for key, cfg in config.items():
            if "default" in cfg:
                params[key] = cfg["default"]
        if overrides:
            params.update(overrides)
        params.setdefault("repeat", 1)
        params.setdefault("gap_ms", 0)
        return params

    def _apply_frame_to_canvas(self, frame: Frame):
        self.canvas.set_frame_pixels(frame.pixels)
        if frame.pixels:
            self._current_color = tuple(frame.pixels[0])
            self.canvas.set_current_color(self._current_color)
            self._sync_channel_controls(self._current_color)

    def _refresh_preset_combo(self):
        if not hasattr(self, "preset_combo"):
            return
        current = self.preset_combo.currentText()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for name in self.preset_repo.names():
            self.preset_combo.addItem(name)
        self.preset_combo.blockSignals(False)
        if current:
            index = self.preset_combo.findText(current)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)
            else:
                self.preset_combo.setEditText(current)

    def _on_save_preset(self):
        name = self.preset_combo.currentText().strip()
        actions = self.automation_manager.actions()
        if not name:
            QMessageBox.information(self, "Preset", "Enter a preset name first.")
            return
        if not actions:
            QMessageBox.information(self, "Preset", "Add actions before saving a preset.")
            return
        valid, message = self._validate_all_actions(actions)
        if not valid:
            QMessageBox.warning(
                self,
                "Preset",
                "Cannot save preset because some actions have invalid parameters:\n"
                f"{message}",
            )
            return
        self.preset_repo.upsert(name, actions)
        self._refresh_preset_combo()
        QMessageBox.information(self, "Preset", f"Preset '{name}' saved.")

    def _on_apply_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name:
            QMessageBox.information(self, "Preset", "Select a preset to apply.")
            return
        actions = self.preset_repo.get(name)
        if not actions:
            QMessageBox.information(self, "Preset", "Preset is empty.")
            return
        valid, message = self._validate_all_actions(actions)
        self.automation_manager.set_actions(actions)
        if valid:
            QMessageBox.information(self, "Preset", f"Preset '{name}' applied to the action queue.")
        else:
            QMessageBox.warning(
                self,
                "Preset Applied With Issues",
                f"Preset '{name}' was applied, but some actions need attention:\n{message}",
            )

    def _on_delete_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name:
            return
        if QMessageBox.question(self, "Delete Preset", f"Remove preset '{name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.preset_repo.delete(name)
            self._refresh_preset_combo()

    def _on_preview_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name:
            return
        actions = self.preset_repo.get(name)
        if not actions:
            QMessageBox.information(self, "Preset", "Preset is empty.")
            return
        summary_lines = []
        for idx, action in enumerate(actions, start=1):
            valid, message, _, _ = self._check_action_params(action, mutate=False)
            marker = "" if valid else "⚠ "
            summary_lines.append(f"{idx:02d}. {marker}{self._describe_action_for_list(action)}")
            if not valid and message:
                summary_lines.append(f"    ↳ {message}")
        summary = "\n".join(summary_lines)
        QMessageBox.information(self, "Preset Preview", summary)

    def _on_duplicate_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name:
            QMessageBox.information(self, "Preset", "Select a preset to duplicate.")
            return
        if not self.preset_repo.exists(name):
            QMessageBox.warning(self, "Preset", f"Preset '{name}' does not exist.")
            return
        new_name, ok = QInputDialog.getText(self, "Duplicate Preset", "Duplicate name:", text=f"{name} Copy")
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(self, "Preset", "Duplicate name cannot be empty.")
            return
        try:
            self.preset_repo.duplicate(name, new_name)
        except ValueError as exc:
            QMessageBox.warning(self, "Preset", str(exc))
            return
        self._refresh_preset_combo()
        self.preset_combo.setCurrentText(new_name)
        QMessageBox.information(self, "Preset", f"Preset duplicated as '{new_name}'.")

    def _on_rename_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name:
            QMessageBox.information(self, "Preset", "Select a preset to rename.")
            return
        if not self.preset_repo.exists(name):
            QMessageBox.warning(self, "Preset", f"Preset '{name}' does not exist.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename Preset", "New name:", text=name)
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(self, "Preset", "New name cannot be empty.")
            return
        try:
            self.preset_repo.rename(name, new_name)
        except ValueError as exc:
            QMessageBox.warning(self, "Preset", str(exc))
            return
        self._refresh_preset_combo()
        self.preset_combo.setCurrentText(new_name)
        QMessageBox.information(self, "Preset", f"Preset renamed to '{new_name}'.")

    def _on_export_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name:
            QMessageBox.information(self, "Preset", "Select a preset to export.")
            return
        if not self.preset_repo.exists(name):
            QMessageBox.warning(self, "Preset", f"Preset '{name}' does not exist.")
            return
        default_path = (self.preset_repo.path.parent / f"{name}.json") if hasattr(self.preset_repo, "path") else Path.home() / f"{name}.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Preset",
            str(default_path),
            "Preset Files (*.json)",
        )
        if not file_path:
            return
        try:
            self.preset_repo.export_to_path(name, Path(file_path))
        except Exception as exc:
            QMessageBox.warning(self, "Preset", f"Failed to export preset: {exc}")
            return
        QMessageBox.information(self, "Preset", f"Preset '{name}' exported to '{file_path}'.")

    def _on_import_preset(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Preset",
            str(self.preset_repo.path.parent if hasattr(self.preset_repo, "path") else Path.home()),
            "Preset Files (*.json)",
        )
        if not file_path:
            return
        path = Path(file_path)
        try:
            imported = self.preset_repo.import_from_path(path, overwrite=False)
        except ValueError as exc:
            if QMessageBox.question(
                self,
                "Import Preset",
                f"{exc}\nDo you want to overwrite the existing preset(s)?",
                QMessageBox.Yes | QMessageBox.No,
            ) == QMessageBox.Yes:
                imported = self.preset_repo.import_from_path(path, overwrite=True)
            else:
                return
        except Exception as exc:
            QMessageBox.warning(self, "Preset", f"Failed to import preset: {exc}")
            return
        self._refresh_preset_combo()
        if imported:
            self.preset_combo.setCurrentText(imported[-1])
            QMessageBox.information(self, "Preset", f"Imported preset(s): {', '.join(imported)}")
        else:
            QMessageBox.information(self, "Preset", "No presets were imported.")

    def _on_timeline_playhead_dragged(self, index: int):
        self._select_frame_safely(index)

    def _on_timeline_zoom_changed(self, value: int):
        zoom = max(25, min(value, 400))
        self.timeline.set_zoom(zoom / 100.0)
        self.timeline_zoom_label.setText(f"{zoom}%")

    def _on_timeline_context_menu(self, index: int):
        menu = QMenu(self)
        add_after = menu.addAction("Add Frame After")
        duplicate = menu.addAction("Duplicate Frame")
        delete = menu.addAction("Delete Frame")
        set_start = menu.addAction("Set as Range Start")
        set_end = menu.addAction("Set as Range End")
        action = menu.exec(QCursor.pos())
        if action is None:
            return
        self.frame_manager.select(index)
        if action == add_after:
            self._on_add_frame()
        elif action == duplicate:
            self._on_duplicate_frame()
        elif action == delete:
            self._on_delete_frame()
        elif action == set_start:
            self.frame_start_spin.setValue(index + 1)
            self._refresh_timeline()
        elif action == set_end:
            self.frame_end_spin.setValue(index + 1)
            self._refresh_timeline()

    def _on_timeline_overlay_activated(self, action_index: int):
        actions = self.automation_manager.actions()
        if not (0 <= action_index < len(actions)):
            return
        self.action_list.setCurrentRow(action_index)
        self.action_list.setFocus()

    def _on_timeline_overlay_context_menu(self, action_index: int, frame_index: int):
        actions = self.automation_manager.actions()
        if not (0 <= action_index < len(actions)):
            return
        menu = QMenu(self)
        focus_action = menu.addAction("Edit Action")
        duplicate_action = menu.addAction("Duplicate Action")
        remove_action = menu.addAction("Remove Action")
        menu.addSeparator()
        clear_action = menu.addAction("Clear All Actions")
        chosen = menu.exec(QCursor.pos())
        if chosen is None:
            return
        if chosen == focus_action:
            self.action_list.setCurrentRow(action_index)
            self.action_list.setFocus()
        elif chosen == duplicate_action:
            action = actions[action_index]
            dup = DesignAction(
                name=f"{action.name} (Copy)",
                action_type=action.action_type,
                params=dict(action.params),
            )
            new_actions = actions[:]
            new_actions.insert(action_index + 1, dup)
            self.automation_manager.set_actions(new_actions)
            self.action_list.setCurrentRow(action_index + 1)
        elif chosen == remove_action:
            self.automation_manager.remove_at(action_index)
        elif chosen == clear_action:
            self._on_clear_actions()

    def _refresh_preview(self, no_message: bool = False):
        if not hasattr(self, "preview_widget") or self.preview_widget is None:
            return
        if not self._pattern:
            return
        
        # Generate cache key from pattern
        cache_key = self._generate_pattern_cache_key(self._pattern)
        
        # Check cache first
        if cache_key in self._preview_cache and cache_key == self._preview_cache_key:
            # Use cached pattern
            cached_pattern = self._preview_cache[cache_key]
            try:
                self.preview_widget.load_pattern(cached_pattern)
                if not no_message:
                    QMessageBox.information(self, "Preview Updated", "Preview synced with current design (cached).")
                return
            except Exception:
                pass  # Fall through to reload
        
        # Load fresh pattern
        try:
            self.preview_widget.load_pattern(self._pattern)
            # Cache the pattern
            import copy
            self._preview_cache[cache_key] = copy.deepcopy(self._pattern)
            self._preview_cache_key = cache_key
            # Limit cache size
            if len(self._preview_cache) > 10:
                # Remove oldest entry
                oldest_key = next(iter(self._preview_cache))
                del self._preview_cache[oldest_key]
            
            if not no_message:
                QMessageBox.information(self, "Preview Updated", "Preview synced with current design.")
        except Exception as exc:
            if not no_message:
                QMessageBox.warning(self, "Preview Error", f"Failed to refresh preview: {exc}")

    def _generate_pattern_cache_key(self, pattern: Pattern) -> str:
        """Generate a cache key for a pattern."""
        if not pattern:
            return ""
        
        # Create hash from pattern metadata and frame count
        data = {
            "name": pattern.name,
            "width": pattern.metadata.width,
            "height": pattern.metadata.height,
            "frame_count": len(pattern.frames),
            "led_count": pattern.metadata.led_count
        }
        # Include first frame hash for quick comparison
        if pattern.frames:
            first_frame_pixels = pattern.frames[0].pixels[:100]  # Sample first 100 pixels
            data["first_frame_sample"] = str(first_frame_pixels)
        
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()

    def _on_optimize_pattern(self):
        """Optimize the current pattern."""
        if not self._pattern or not self._pattern.frames:
            QMessageBox.information(self, "No Pattern", "No pattern to optimize.")
            return
        
        original_frame_count = len(self._pattern.frames)
        optimized = self._optimize_rgb_pattern(self._pattern)
        
        if len(optimized.frames) < original_frame_count:
            reply = QMessageBox.question(
                self,
                "Optimize Pattern",
                f"Optimization will reduce frames from {original_frame_count} to {len(optimized.frames)}.\n"
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                # Validate optimized is Pattern object before assignment
                if not isinstance(optimized, Pattern):
                    raise TypeError(f"Expected Pattern, got {type(optimized).__name__}: {optimized}")
                self._pattern = optimized
                self.frame_manager.select(0)
                self._load_current_frame_into_canvas()
                self._refresh_timeline()
                self._update_status_labels()
                self.pattern_modified.emit()
                QMessageBox.information(
                    self,
                    "Optimization Complete",
                    f"Pattern optimized: {original_frame_count} → {len(optimized.frames)} frames"
                )
        else:
            QMessageBox.information(
                self,
                "No Optimization Needed",
                "Pattern is already optimized (no duplicate frames found)."
            )

    def _on_export_frame_as_image(self):
        """Export current frame as image."""
        if not self._pattern or not self._pattern.frames:
            QMessageBox.warning(self, "No Frame", "No frame to export. Create or load a pattern first.")
            return
        
        if self._current_frame_index >= len(self._pattern.frames):
            QMessageBox.warning(self, "Invalid Frame", "Current frame index is out of range.")
            return
        
        # Get file path
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Frame as Image",
            "",
            "PNG Images (*.png);;BMP Images (*.bmp);;All Files (*.*)"
        )
        
        if not filepath:
            return
        
        # Determine format from extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".bmp":
            format = "BMP"
        else:
            format = "PNG"
            if not filepath.endswith(".png"):
                filepath += ".png"
        
        try:
            frame = self._pattern.frames[self._current_frame_index]
            width = self._pattern.metadata.width
            height = self._pattern.metadata.height
            
            # Ask for scale factor
            scale_factor, ok = QInputDialog.getInt(
                self,
                "Export Scale",
                "Pixel scale factor (1 = 1 pixel per LED, 10 = 10x10 pixels per LED):",
                10,
                1,
                100,
                1
            )
            
            if not ok:
                return
            
            ImageExporter.export_frame_as_image(
                frame,
                filepath,
                width,
                height,
                scale_factor,
                format
            )
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Frame exported successfully to:\n{filepath}"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export frame:\n\n{str(e)}"
            )

    def _on_export_animation_as_gif(self):
        """Export pattern as animated GIF."""
        if not self._pattern or not self._pattern.frames:
            QMessageBox.warning(self, "No Pattern", "No pattern to export. Create or load a pattern first.")
            return
        
        # Validate pattern has frames with pixels
        if len(self._pattern.frames) == 0:
            QMessageBox.warning(self, "Empty Pattern", "Pattern has no frames to export.")
            return
        
        # Check if any frame has pixels
        has_pixels = any(frame.pixels and len(frame.pixels) > 0 for frame in self._pattern.frames)
        if not has_pixels:
            QMessageBox.warning(self, "Empty Frames", "All frames are empty. Add some content before exporting.")
            return
        
        # Get file path
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Animation as GIF",
            "",
            "GIF Images (*.gif);;All Files (*.*)"
        )
        
        if not filepath:
            return
        
        if not filepath.endswith(".gif"):
            filepath += ".gif"
        
        try:
            # Ask for scale factor and loop count
            scale_factor, ok1 = QInputDialog.getInt(
                self,
                "Export Scale",
                "Pixel scale factor (1 = 1 pixel per LED, 10 = 10x10 pixels per LED):",
                10,
                1,
                100,
                1
            )
            
            if not ok1:
                return
            
            loop_count, ok2 = QInputDialog.getInt(
                self,
                "GIF Loop Count",
                "Number of loops (0 = infinite):",
                0,
                0,
                1000,
                1
            )
            
            if not ok2:
                return
            
            ImageExporter.export_animation_as_gif(
                self._pattern,
                filepath,
                scale_factor,
                loop_count
            )
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Animation exported successfully to:\n{filepath}\n\n"
                f"Frames: {len(self._pattern.frames)}\n"
                f"Scale: {scale_factor}x\n"
                f"Loops: {'Infinite' if loop_count == 0 else loop_count}"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export animation:\n\n{str(e)}"
            )

    def _emit_pattern(self):
        if not self._pattern:
            return
        name_text = self.pattern_name_combo.currentText().strip()
        if name_text:
            self._pattern.name = name_text
        self.pattern_created.emit(self._pattern)
        QMessageBox.information(self, "Pattern Saved", "Design exported to application. Check other tabs to use it.")

    def _on_export_code_template(self) -> None:
        if not self._pattern or not self._pattern.frames:
            QMessageBox.warning(self, "No Pattern", "Generate or load a pattern before exporting templates.")
            return
        template_name = self.code_template_combo.currentText()
        try:
            code = render_template(template_name, self._pattern)
        except Exception as exc:
            QMessageBox.critical(self, "Template Error", f"Unable to render template:\n{exc}")
            return
        suggested = (self._pattern.name or "pattern").replace(" ", "_")
        filters = "Source Files (*.h *.c *.ino *.asm *.txt);;All Files (*.*)"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Code Template",
            f"{suggested}.h",
            filters,
        )
        if not filepath:
            return
        Path(filepath).write_text(code, encoding="utf-8")
        if hasattr(self, "code_template_status"):
            self.code_template_status.setText(f"Saved '{template_name}' to {Path(filepath).name}")

    def _backup_custom_fonts(self) -> None:
        source = Path("Res/fonts")
        if not source.exists() or not any(source.iterdir()):
            QMessageBox.information(self, "No Fonts", "No custom fonts found to backup.")
            return
        default = (Path.home() / "upload_bridge_fonts_backup.zip").resolve()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Custom Fonts",
            str(default),
            "Zip Archives (*.zip);;All Files (*.*)",
        )
        if not filepath:
            return
        archive_base = Path(filepath)
        base_name = str(archive_base.with_suffix(""))
        shutil.make_archive(base_name, "zip", source)
        archive_path = archive_base.with_suffix(".zip")
        if hasattr(self, "code_template_status"):
            self.code_template_status.setText(f"Fonts backed up to {archive_path.name}")

    def _on_color_picker_clicked(self):
        """Handle color picker button click."""
        if self._single_color_mode:
            # In single color mode, only white is allowed
            QMessageBox.information(
                self,
                "Single Color Mode",
                "Single color mode is active. Only white (255, 255, 255) is available."
            )
            self._current_color = (255, 255, 255)
            self._sync_channel_controls(self._current_color)
            self.canvas.set_current_color(self._current_color)
            return
        
        initial = QColor(*self._current_color)
        color = QColorDialog.getColor(initial, self, "Select Color")
        if color.isValid():
            rgb = (color.red(), color.green(), color.blue())
            self._current_color = rgb
            self._sync_channel_controls(rgb)
            self.canvas.set_current_color(rgb)

    def _choose_gradient_colour(self, target: str):
        # Enforce single color mode for gradients too
        if self._single_color_mode:
            rgb = (255, 255, 255)
        else:
            initial = QColor(*self._start_gradient_color) if target == "start" else QColor(*self._end_gradient_color)
            color = QColorDialog.getColor(initial, self, "Select colour")
            if not color.isValid():
                return
            rgb = (color.red(), color.green(), color.blue())
        if target == "start":
            self._start_gradient_color = rgb
            border = self._current_ui_palette.get("border", "#666666")
            text_color = self._current_ui_palette.get("text_primary", "#F5F5F5")
            self.gradient_start_btn.setStyleSheet(
                f"background-color: rgb{rgb}; border: 1px solid {border}; color: {text_color};"
            )
        else:
            self._end_gradient_color = rgb
            border = self._current_ui_palette.get("border", "#666666")
            text_color = self._current_ui_palette.get("text_primary", "#F5F5F5")
            self.gradient_end_btn.setStyleSheet(
                f"background-color: rgb{rgb}; border: 1px solid {border}; color: {text_color};"
            )
        self._sync_random_palette()
        self._sync_gradient_brush_settings()

    def _apply_gradient_from_controls(self):
        if not self._pattern or not self._pattern.frames:
            return
        orientation = self.gradient_orientation_combo.currentText()
        steps = self.gradient_steps_spin.value()
        frame = self._pattern.frames[self._current_frame_index]
        self._apply_gradient(frame, orientation, steps)
        self.canvas.set_frame_pixels(frame.pixels)
        self.pattern_modified.emit()
        self._update_status_labels()
        self._maybe_autosync_preview()

    def _apply_gradient(self, frame: Frame, orientation: str, steps: int):
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        start_r, start_g, start_b = self._start_gradient_color
        end_r, end_g, end_b = self._end_gradient_color
        gradient_pixels: List[Tuple[int, int, int]] = []

        def interpolate(t: float) -> Tuple[int, int, int]:
            r = int(start_r + (end_r - start_r) * t)
            g = int(start_g + (end_g - start_g) * t)
            b = int(start_b + (end_b - start_b) * t)
            return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        orientation = orientation.lower()
        if orientation == "horizontal":
            denom = max(1, min(steps - 1, width - 1))
            for y in range(height):
                for x in range(width):
                    t = x / denom
                    gradient_pixels.append(interpolate(min(1.0, t)))
        elif orientation == "vertical":
            denom = max(1, min(steps - 1, height - 1))
            for y in range(height):
                t = y / denom
                for x in range(width):
                    gradient_pixels.append(interpolate(min(1.0, t)))
        else:
            center_x = (width - 1) / 2.0
            center_y = (height - 1) / 2.0
            max_dist = ((center_x) ** 2 + (center_y) ** 2) ** 0.5
            denom = max(1e-6, min(max_dist, float(steps)))
            for y in range(height):
                for x in range(width):
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    t = dist / denom
                    gradient_pixels.append(interpolate(min(1.0, t)))

        frame.pixels = gradient_pixels

    def _default_preset_path(self) -> Path:
        base_dir = Path.home() / ".upload_bridge"
        return base_dir / "automation_presets.json"

    def _on_action_repeat_changed(self, value: int):
        if self._updating_action_inspector:
            return
        index = getattr(self, "_current_action_index", -1)
        if index < 0:
            return
        actions = self.automation_manager.actions()
        if 0 <= index < len(actions):
            actions[index].params["repeat"] = max(1, int(value))
            self.automation_manager.set_actions(actions)
            self._update_action_validation(actions[index])

    def _on_action_gap_changed(self, value: int):
        if self._updating_action_inspector:
            return
        index = getattr(self, "_current_action_index", -1)
        if index < 0:
            return
        actions = self.automation_manager.actions()
        if 0 <= index < len(actions):
            actions[index].params["gap_ms"] = max(0, int(value))
            self.automation_manager.set_actions(actions)
            self._update_action_validation(actions[index])


