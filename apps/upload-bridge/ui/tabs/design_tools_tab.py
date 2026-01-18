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
import logging
from functools import partial, wraps
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

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

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
from core.services.export_service import ExportService
from core.services.pattern_service import PatternService
from core.repositories.pattern_repository import PatternRepository
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
from core.gradient import GradientType, PRESET_GRADIENTS  # noqa: E402
from ui.widgets.gradient_editor import GradientEditorWidget  # noqa: E402
from ui.widgets.circular_preview_canvas import CircularPreviewCanvas  # noqa: E402
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
from domain.layers import LayerManager, Layer, LayerFrame, ACTION_PRIORITY  # noqa: E402
from domain.automation.layer_action import LayerAction, get_action_step  # noqa: E402
from domain.layer_animation import (
    create_scroll_animation,
    create_fade_animation,
    AnimationType,
)  # noqa: E402
from domain.scratchpads import ScratchpadManager  # noqa: E402
from domain.canvas import CanvasController  # noqa: E402
from domain.automation.queue import AutomationQueueManager  # noqa: E402
from domain.history import HistoryManager, FrameStateCommand  # noqa: E402
from domain.automation.presets import PresetRepository  # noqa: E402
from domain.effects import EffectDefinition, EffectLibrary, apply_effect_to_frames  # noqa: E402
from domain.text.bitmap_font import BitmapFontRepository, BitmapFont  # noqa: E402
from domain.text.glyph_provider import GlyphProvider  # noqa: E402
from domain.text.text_renderer import TextRenderer, TextRenderOptions, TextScrollOptions  # noqa: E402
from ui.icons import get_icon
from ui.widgets.effects_library_widget import EffectsLibraryWidget
from ui.dialogs.detached_preview_dialog import DetachedPreviewDialog
from ui.dialogs.font_designer_dialog import FontDesignerDialog
from ui.dialogs.automation_wizard_dialog import AutomationWizardDialog
from ui.dialogs.ai_generate_dialog import AIGenerateDialog


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

    # Logging helper functions
    @staticmethod
    def _log_click(button_name: str, context: Optional[Dict] = None):
        """Log a button click with context"""
        frame_count = 0
        current_frame = -1
        if hasattr(DesignToolsTab, '_current_instance') and DesignToolsTab._current_instance:
            instance = DesignToolsTab._current_instance
            if instance._pattern:
                frame_count = len(instance._pattern.frames)
                current_frame = instance._current_frame_index
        context_str = f" | Context: {context}" if context else ""
        logging.info(
            f"[CLICK] {button_name} | "
            f"Frames: {frame_count} | "
            f"Current Frame: {current_frame + 1 if current_frame >= 0 else 'N/A'}"
            f"{context_str}"
        )

    @staticmethod
    def _log_action(action_name: str, details: Optional[Dict] = None):
        """Log an automation action with details"""
        details_str = f" | Details: {details}" if details else ""
        logging.info(f"[ACTION] {action_name}{details_str}")

    @staticmethod
    def _log_frame_generation(step: str, frame_count: int, details: Optional[Dict] = None):
        """Log frame generation steps"""
        details_str = f" | {details}" if details else ""
        logging.info(f"[FRAME_GEN] {step} | Frame Count: {frame_count}{details_str}")

    @staticmethod
    def _frames_are_identical(frame1: Frame, frame2: Frame) -> bool:
        """Check if two frames have identical pixel content"""
        if len(frame1.pixels) != len(frame2.pixels):
            return False
        for i, (p1, p2) in enumerate(zip(frame1.pixels, frame2.pixels)):
            if isinstance(p1, (list, tuple)) and isinstance(p2, (list, tuple)):
                if len(p1) >= 3 and len(p2) >= 3:
                    if p1[0] != p2[0] or p1[1] != p2[1] or p1[2] != p2[2]:
                        return False
                else:
                    return False
            else:
                return False
        return True

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("DesignToolsTab")
        self._theme = self._resolve_initial_theme()
        self._current_ui_palette: Dict[str, str] = self.THEME_DEFINITIONS[self._theme]["ui"]
        self._pattern: Optional[Pattern] = None
        
        # Set instance reference for logging
        DesignToolsTab._current_instance = self
        
        # Initialize services
        self.export_service = ExportService()
        self.pattern_service = PatternService()
        self.repository = PatternRepository.instance()
        
        # Pattern versioning
        from core.pattern_versioning import PatternVersionManager, AutoVersionManager
        self._version_manager = PatternVersionManager(max_versions=50)
        self._auto_version_manager = AutoVersionManager(self._version_manager, auto_save_interval_seconds=300)
        
        # Connect pattern modified signal to auto-versioning
        self.pattern_modified.connect(self._on_pattern_modified_for_versioning)
        self._current_frame_index: int = 0
        self._frame_duration_ms: int = 50
        self._current_color: Tuple[int, int, int] = (255, 255, 255)
        self._frame_switch_locked: bool = False  # Prevent frame switching during operations
        # Onion skinning state
        self._onion_skin_enabled: bool = False
        self._onion_skin_prev_count: int = 1
        self._onion_skin_next_count: int = 1
        self._onion_skin_prev_opacity: float = 0.5
        self._onion_skin_next_opacity: float = 0.3
        self._start_gradient_color: Tuple[int, int, int] = (255, 0, 0)
        self._end_gradient_color: Tuple[int, int, int] = (0, 0, 255)
        self._has_unsaved_changes: bool = False
        self._current_file: Optional[str] = None  # Track current file path
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
        self._pending_pixel_updates: List[Tuple[int, int, int, Tuple[int, int, int]]] = []  # (frame_index, x, y, color) for batch updates
        self._is_painting: bool = False  # Track if currently painting (mouse pressed)
        self._pending_broadcast_states: Optional[Dict[int, List[Tuple[int, int, int]]]] = None  # Track states for all frames in broadcast mode
        self._preview_cache: Dict[str, Pattern] = {}  # Cache for preview patterns
        self._preview_cache_key: Optional[str] = None  # Current cache key
        self._lms_sequence = PatternInstructionSequence()
        self._lms_preview_snapshot: Optional[Pattern] = None
        self._brush_broadcast_warning_shown = False  # Track if user has seen broadcast warning
        self._brush_broadcast_banner: Optional[QWidget] = None  # Warning banner widget
        self._hidden_layer_banner: Optional[QWidget] = None  # Hidden layer warning banner
        # Layer sync banner removed - syncing is now automatic
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
        self.text_renderer = TextRenderer()
        self._glyph_provider = GlyphProvider()
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
        self.frame_manager.frames_changed.connect(self._update_frame_range_spinboxes)
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
        self.led_color_panel: Optional[object] = None  # LED Color Panel widget
        self._selected_frames: List[int] = []  # Multi-frame selection

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
        
        # Prominent Create Animation button
        create_anim_button = QPushButton("✨ Create Animation")
        create_anim_button.setToolTip("Create animation from templates or automation")
        create_anim_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        create_anim_button.clicked.connect(self._on_create_animation_clicked)
        layout.addWidget(create_anim_button)
        
        # AI Generate button
        ai_generate_button = QPushButton("🤖 AI Generate")
        ai_generate_button.setToolTip("Generate pattern from text prompt using AI")
        ai_generate_button.clicked.connect(self._on_ai_generate_clicked)
        layout.addWidget(ai_generate_button)
        
        # Templates button
        templates_button = QPushButton("📋 Templates")
        templates_button.setToolTip("Browse and apply pattern templates")
        templates_button.clicked.connect(self._on_templates_clicked)
        layout.addWidget(templates_button)

        open_button = QPushButton("Open")
        open_button.setToolTip("Open an existing pattern file")
        open_button.clicked.connect(self._on_open_pattern_clicked)
        layout.addWidget(open_button)
        
        # Version History button
        version_history_btn = QPushButton("📜 Versions")
        version_history_btn.setToolTip("View pattern version history")
        version_history_btn.clicked.connect(self._on_version_history_clicked)
        layout.addWidget(version_history_btn)

        layout.addSpacing(8)

        # Quick Matrix Size Buttons
        quick_matrix_label = QLabel("Quick Size:")
        quick_matrix_label.setObjectName("designToolsQuickMatrix")
        layout.addWidget(quick_matrix_label)
        
        quick_matrix_layout = QHBoxLayout()
        quick_matrix_layout.setSpacing(4)
        quick_matrix_layout.setContentsMargins(0, 0, 0, 0)
        
        for width, height in [(8, 8), (16, 16), (32, 32), (64, 32)]:
            btn = QPushButton(f"{width}×{height}")
            btn.setToolTip(f"Set matrix size to {width}×{height}")
            btn.clicked.connect(lambda checked, w=width, h=height: self._on_quick_matrix_clicked(w, h))
            quick_matrix_layout.addWidget(btn)
        
        custom_btn = QPushButton("Custom...")
        custom_btn.setToolTip("Open matrix configuration dialog")
        custom_btn.clicked.connect(self._on_custom_matrix_clicked)
        quick_matrix_layout.addWidget(custom_btn)
        
        quick_matrix_widget = QWidget()
        quick_matrix_widget.setLayout(quick_matrix_layout)
        layout.addWidget(quick_matrix_widget)

        layout.addSpacing(8)

        # Quick Actions Toolbar
        quick_actions_label = QLabel("Quick Actions:")
        quick_actions_label.setObjectName("designToolsQuickActions")
        layout.addWidget(quick_actions_label)
        
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setSpacing(4)
        quick_actions_layout.setContentsMargins(0, 0, 0, 0)
        
        # Clear Frame button (icon-only with minimum size)
        clear_btn = QPushButton()
        clear_btn.clicked.connect(self._on_clear_frame)
        self._apply_button_icon(clear_btn, "delete", tooltip="Clear current frame (Delete)", icon_only=True)
        clear_btn.setMinimumSize(24, 24)
        quick_actions_layout.addWidget(clear_btn)
        
        # Invert button (icon-only with minimum size)
        invert_btn = QPushButton()
        invert_btn.clicked.connect(self._on_invert_frame)
        self._apply_button_icon(invert_btn, "refresh", tooltip="Invert colors (Ctrl+I)", icon_only=True)
        invert_btn.setMinimumSize(24, 24)
        quick_actions_layout.addWidget(invert_btn)
        
        # Flip H button (icon-only with minimum size)
        flip_h_btn = QPushButton()
        flip_h_btn.clicked.connect(self._on_flip_horizontal)
        self._apply_button_icon(flip_h_btn, "arrow-left", tooltip="Flip horizontal (Ctrl+H)", icon_only=True)
        flip_h_btn.setMinimumSize(24, 24)
        quick_actions_layout.addWidget(flip_h_btn)
        
        # Flip V button (icon-only with minimum size)
        flip_v_btn = QPushButton()
        flip_v_btn.clicked.connect(self._on_flip_vertical)
        self._apply_button_icon(flip_v_btn, "arrow-up", tooltip="Flip vertical (Ctrl+V)", icon_only=True)
        flip_v_btn.setMinimumSize(24, 24)
        quick_actions_layout.addWidget(flip_v_btn)
        
        # Rotate 90° button (icon-only with minimum size)
        rotate_btn = QPushButton()
        rotate_btn.clicked.connect(self._on_rotate_90)
        self._apply_button_icon(rotate_btn, "refresh", tooltip="Rotate 90 degrees clockwise", icon_only=True)
        rotate_btn.setMinimumSize(24, 24)
        quick_actions_layout.addWidget(rotate_btn)
        
        quick_actions_widget = QWidget()
        quick_actions_widget.setLayout(quick_actions_layout)
        layout.addWidget(quick_actions_widget)

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
        self.memory_status_label.setToolTip("Pattern memory usage (bytes)")
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
        
        # Broadcast mode warning banner (initially hidden)
        self._brush_broadcast_banner = self._create_broadcast_warning_banner()
        layout.addWidget(self._brush_broadcast_banner)
        self._brush_broadcast_banner.setVisible(False)
        
        # Hidden layer warning banner (initially hidden)
        self._hidden_layer_banner = self._create_hidden_layer_warning_banner()
        layout.addWidget(self._hidden_layer_banner)
        self._hidden_layer_banner.setVisible(False)
        
        # Layer sync banner removed - syncing is now automatic

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
            ("LED Colors", "colors", self._create_led_colors_tab()),
            ("Pixel Mapping", "mapping", self._create_pixel_mapping_tab()),
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
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
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
        self.timeline.framesSelected.connect(self._on_frames_selected)  # Multi-select
        self.timeline.playheadDragged.connect(self._on_timeline_playhead_dragged)
        self.timeline.contextMenuRequested.connect(self._on_timeline_context_menu)
        self.timeline.overlayActivated.connect(self._on_timeline_overlay_activated)
        self.timeline.overlayContextMenuRequested.connect(self._on_timeline_overlay_context_menu)
        self.timeline.layerTrackSelected.connect(self._on_timeline_layer_selected)
        
        # Enable CapCut-style grid mode
        self.timeline.enable_grid_mode(True)
        
        # Connect to managers for drag-and-drop
        self.timeline.set_frame_manager(self.frame_manager)
        self.timeline.set_layer_manager(self.layer_manager)
        
        # Connect layer visibility toggle
        self.timeline.layerVisibilityToggled.connect(self._on_timeline_layer_visibility_toggled)
        
        # Wrap timeline in scroll area for horizontal scrolling
        from PySide6.QtWidgets import QScrollArea
        timeline_scroll = QScrollArea()
        timeline_scroll.setWidget(self.timeline)
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        timeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        timeline_scroll.setFrameShape(QScrollArea.Shape.NoFrame)  # Remove border
        
        layout.addWidget(timeline_scroll, 1)

        # Simple timeline mode toggle
        simple_mode_label = QLabel("Simple Mode:")
        layout.addWidget(simple_mode_label)
        
        self.simple_timeline_checkbox = QCheckBox("Hide layers (simple animations)")
        self.simple_timeline_checkbox.setToolTip("Hide layer tracks for simpler timeline view")
        self.simple_timeline_checkbox.toggled.connect(self._on_simple_timeline_toggled)
        layout.addWidget(self.simple_timeline_checkbox)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(12)

        frame_ops = QHBoxLayout()
        frame_ops.setSpacing(6)
        self.add_frame_btn = QPushButton("Add")
        self._apply_button_icon(self.add_frame_btn, "add", tooltip="Add new frame (Ctrl+Shift+A)")
        self.add_frame_btn.clicked.connect(self._on_add_frame)
        frame_ops.addWidget(self.add_frame_btn)

        self.bulk_add_frame_btn = QPushButton("Bulk Add")
        self._apply_button_icon(self.bulk_add_frame_btn, "add", tooltip="Add multiple frames at once")
        self.bulk_add_frame_btn.clicked.connect(self._on_bulk_add_frames)
        frame_ops.addWidget(self.bulk_add_frame_btn)

        self.duplicate_frame_btn = QPushButton("Duplicate")
        self._apply_button_icon(self.duplicate_frame_btn, "duplicate", tooltip="Duplicate selected frame")
        self.duplicate_frame_btn.clicked.connect(self._on_duplicate_frame)
        frame_ops.addWidget(self.duplicate_frame_btn)

        self.delete_frame_btn = QPushButton("Delete")
        self._apply_button_icon(self.delete_frame_btn, "delete", tooltip="Delete selected frame (Del)")
        self.delete_frame_btn.clicked.connect(self._on_delete_frame)
        frame_ops.addWidget(self.delete_frame_btn)

        self.bulk_delete_frame_btn = QPushButton("Bulk Delete")
        self._apply_button_icon(self.bulk_delete_frame_btn, "delete", tooltip="Delete frame range")
        self.bulk_delete_frame_btn.clicked.connect(self._on_bulk_delete_frames)
        frame_ops.addWidget(self.bulk_delete_frame_btn)
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

    def _on_ai_generate_clicked(self) -> None:
        """Handle AI Generate button click - show AI generation dialog."""
        if not self._confirm_discard_changes():
            return
        
        from ui.dialogs.ai_generate_dialog import AIGenerateDialog
        
        current_width = self.width_spin.value() if hasattr(self, "width_spin") else 16
        current_height = self.height_spin.value() if hasattr(self, "height_spin") else 16
        
        dialog = AIGenerateDialog(self, current_width, current_height)
        dialog.pattern_generated.connect(self._on_ai_pattern_generated)
        dialog.exec()
    
    def _on_ai_pattern_generated(self, pattern: Pattern) -> None:
        """Handle AI-generated pattern - load it into the editor."""
        self.load_pattern(pattern)
        self.pattern_created.emit(pattern)
        QMessageBox.information(
            self,
            "Pattern Loaded",
            f"AI-generated pattern loaded successfully!\n\n"
            f"Name: {pattern.name}\n"
            f"Size: {pattern.metadata.width}×{pattern.metadata.height}\n"
            f"Frames: {len(pattern.frames)}\n\n"
            f"You can now edit, export, or further customize this pattern."
        )

    def _on_templates_clicked(self) -> None:
        """Handle Templates button click - show template dialog."""
        if not self._confirm_discard_changes():
            return
        
        from ui.dialogs.pattern_template_dialog import PatternTemplateDialog
        
        current_width = self.width_spin.value() if hasattr(self, "width_spin") else 16
        current_height = self.height_spin.value() if hasattr(self, "height_spin") else 16
        
        dialog = PatternTemplateDialog(self, current_width, current_height)
        dialog.pattern_generated.connect(self._on_template_pattern_generated)
        dialog.exec()
    
    def _on_template_pattern_generated(self, pattern: Pattern) -> None:
        """Handle template-generated pattern - load it into the editor."""
        # Use PatternService to set the pattern
        self.pattern_service.set_current_pattern(pattern, None)
        self.load_pattern(pattern)
        self.pattern_created.emit(pattern)
        self.pattern_modified.emit()
    
    def _on_create_animation_clicked(self) -> None:
        """Handle Create Animation button click - show animation creation dialog."""
        if not self._confirm_discard_changes():
            return
        
        from ui.dialogs.create_animation_dialog import CreateAnimationDialog
        
        current_width = self.width_spin.value() if hasattr(self, "width_spin") else 16
        current_height = self.height_spin.value() if hasattr(self, "height_spin") else 16
        
        dialog = CreateAnimationDialog(self, current_width, current_height)
        dialog.pattern_generated.connect(self._on_template_pattern_generated)
        dialog.exec()
    
    def _on_version_history_clicked(self) -> None:
        """Handle Version History button click - show version history dialog."""
        from ui.dialogs.version_history_dialog import VersionHistoryDialog
        
        dialog = VersionHistoryDialog(self._version_manager, self)
        dialog.version_restored.connect(self._on_version_restored)
        dialog.exec()
    
    def _on_version_restored(self, pattern: Pattern) -> None:
        """Handle version restoration - load restored pattern."""
        self.load_pattern(pattern)
        self.pattern_created.emit(pattern)
        
        # Verify metadata was preserved
        meta_info = []
        if hasattr(pattern.metadata, 'dimension_source') and pattern.metadata.dimension_source != 'unknown':
            meta_info.append(f"Dimension source: {pattern.metadata.dimension_source}")
        if hasattr(pattern.metadata, 'dimension_confidence'):
            meta_info.append(f"Confidence: {pattern.metadata.dimension_confidence:.1%}")
        
        message = "Pattern version restored successfully!"
        if meta_info:
            message += f"\n\nMetadata preserved:\n" + "\n".join(meta_info)
        
        QMessageBox.information(
            self,
            "Version Restored",
            message
        )
    
    def _on_pattern_modified_for_versioning(self) -> None:
        """Handle pattern modification - trigger auto-versioning if needed."""
        if self._pattern and hasattr(self, "_auto_version_manager"):
            # Check if auto-save is needed
            if self._auto_version_manager.should_auto_save(self._pattern):
                version_id = self._auto_version_manager.auto_save(self._pattern)
                if version_id:
                    # Optionally show a subtle notification
                    pass
    
    def _on_new_pattern_clicked(self) -> None:
        """Handle New button click - show new pattern dialog."""
        if not self._confirm_discard_changes():
            return
        from ui.dialogs.new_pattern_dialog import NewPatternDialog
        
        current_width = self.width_spin.value() if hasattr(self, "width_spin") else 12
        current_height = self.height_spin.value() if hasattr(self, "height_spin") else 6
        
        dialog = NewPatternDialog(self, current_width, current_height)
        if dialog.exec() == QDialog.Accepted:
            # Check if preset template is selected
            selected_template = dialog.get_selected_template()
            is_preset = dialog.is_preset_tab_active() and selected_template is not None
            
            if is_preset:
                # Generate pattern from template
                try:
                    from core.pattern_templates import TemplateLibrary
                    template_library = TemplateLibrary()
                    
                    width = dialog.get_width()
                    height = dialog.get_height()
                    template_params = dialog.get_template_parameters()
                    
                    pattern = template_library.generate_pattern(
                        selected_template.name,
                        width,
                        height,
                        **template_params
                    )
                    
                    # Apply dialog options to generated pattern
                    if hasattr(pattern.metadata, 'led_type'):
                        pattern.metadata.led_type = dialog.get_led_type()
                    pattern.metadata.is_single_color = dialog.is_single_color()
                    
                    # Set pixel shape on canvas
                    pixel_shape = dialog.get_pixel_shape()
                    if hasattr(self.canvas, 'set_pixel_shape'):
                        shape_map = {'circle': 'round', 'square': 'square', 'rounded': 'rounded'}
                        canvas_shape = shape_map.get(pixel_shape, 'square')
                        self.canvas.set_pixel_shape(canvas_shape)
                    
                    self.load_pattern(pattern)
                    return
                    
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(
                        self,
                        "Template Generation Error",
                        f"Failed to generate pattern from template:\n{str(e)}"
                    )
                    return
            
            # Custom pattern creation
            width = dialog.get_width()
            height = dialog.get_height()
            led_type = dialog.get_led_type()
            is_single_color = dialog.is_single_color()
            layout_type = dialog.get_layout_type()
            
            # Get additional options from dialog
            initial_frames = dialog.get_initial_frames()
            should_clear = dialog.should_clear_data()
            pixel_shape = dialog.get_pixel_shape()
            background_color = dialog.get_background_color()
            background_mode = dialog.get_background_mode()  # 'common' or 'all'
            border_setting = dialog.get_border()  # 'n/a', '1px', '2px', '3px'
            
            # Create new pattern
            # Use background color for initial frames
            # If "Clear all animation/matrix data" is checked, use background color
            # Otherwise, use black (0, 0, 0) as default
            bg_color = background_color if should_clear else (0, 0, 0)
            
            metadata = PatternMetadata(width=width, height=height)
            # Store LED type in metadata
            if not hasattr(metadata, 'led_type'):
                metadata.led_type = led_type
            else:
                metadata.led_type = led_type
            metadata.is_single_color = is_single_color
            
            # Handle irregular shapes
            if layout_type == "irregular":
                from core.mapping.irregular_shape_mapper import IrregularShapeMapper
                
                metadata.layout_type = "irregular"
                metadata.irregular_shape_enabled = True
                
                # Get active cells from shape editor
                active_cells = dialog.get_irregular_active_cells()
                if active_cells:
                    metadata.active_cell_coordinates = active_cells
                else:
                    # Initialize to all cells active
                    IrregularShapeMapper.ensure_active_cells_initialized(metadata)
                
                # Get background image path if set
                bg_image_path = dialog.get_background_image_path()
                if bg_image_path:
                    metadata.background_image_path = bg_image_path
                    metadata.background_image_scale = 1.0
                    metadata.background_image_offset_x = 0.0
                    metadata.background_image_offset_y = 0.0
            
            # Handle circular layouts (circular, multi_ring, radial_rays)
            elif layout_type != "rectangular":
                from core.mapping.circular_mapper import CircularMapper
                
                # Get actual shape from dialog (may be multi_ring, radial_rays, or circular)
                actual_shape = dialog.get_shape()
                
                if actual_shape == "multi_ring":
                    metadata.layout_type = "multi_ring"
                    metadata.multi_ring_count = dialog.get_multi_ring_count()
                    metadata.ring_led_counts = dialog.get_ring_led_counts()
                    metadata.ring_radii = dialog.get_ring_radii()
                    metadata.ring_spacing = dialog.get_ring_spacing()
                elif actual_shape == "radial_rays":
                    metadata.layout_type = "radial_rays"
                    # Auto-set from width/height: ray_count = width (columns), leds_per_ray = height (rows)
                    metadata.ray_count = metadata.width  # columns = ray count
                    metadata.leds_per_ray = metadata.height  # rows = LEDs per ray
                    metadata.ray_spacing_angle = dialog.get_ray_spacing_angle()
                elif actual_shape == "custom_positions":
                    metadata.layout_type = "custom_positions"
                    metadata.custom_led_positions = dialog.get_custom_led_positions()
                    metadata.led_position_units = dialog.get_led_position_units()
                else:
                    # Standard circular layout (circle, ring, arc, radial)
                    metadata.layout_type = dialog.get_circular_layout_type()
                    metadata.circular_led_count = dialog.get_circular_led_count()
                    metadata.circular_radius = dialog.get_circular_radius()
                    metadata.circular_inner_radius = dialog.get_circular_inner_radius()
                    metadata.circular_start_angle = dialog.get_circular_start_angle()
                    metadata.circular_end_angle = dialog.get_circular_end_angle()
                
                # Generate mapping table (single source of truth for circular layout)
                # This table will be used by preview and export - no live calculations
                try:
                    metadata.circular_mapping_table = CircularMapper.generate_mapping_table(metadata)
                    
                    # Validate the generated mapping table
                    is_valid, error_msg = CircularMapper.validate_mapping_table(metadata)
                    if not is_valid:
                        raise ValueError(f"Generated mapping table is invalid: {error_msg}")
                    
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "Circular Layout Error",
                        f"Failed to generate circular mapping table:\n{str(e)}\n\n"
                        "This usually means:\n"
                        "- LED count doesn't fit the grid size\n"
                        "- Invalid radius or angle settings\n"
                        "- Grid too small for the circular layout\n\n"
                        "Falling back to rectangular layout."
                    )
                    metadata.layout_type = "rectangular"
                    metadata.circular_led_count = None
                    metadata.circular_mapping_table = None
            
            # Create frames based on initial_frames count
            # Background mode: 'common' = apply to first frame only, 'all' = apply to all frames
            frames = []
            for i in range(initial_frames):
                # Apply background color based on mode
                if background_mode == "all" or (background_mode == "common" and i == 0):
                    frame_color = bg_color
                else:
                    frame_color = (0, 0, 0)  # Black for other frames in "common" mode
                
                frame = self._create_blank_frame(width, height, default_color=frame_color)
                frames.append(frame)
            
            pattern = Pattern(name="New Design", metadata=metadata, frames=frames)
            self.load_pattern(pattern)
            
            # Set pixel shape on canvas
            if hasattr(self.canvas, 'set_pixel_shape'):
                # Map dialog pixel shape to canvas pixel shape
                # Dialog returns: 'square', 'circle', 'rounded'
                # Canvas expects: 'square', 'round', 'rounded'
                shape_map = {'circle': 'round', 'square': 'square', 'rounded': 'rounded'}
                canvas_shape = shape_map.get(pixel_shape, 'square')
                self.canvas.set_pixel_shape(canvas_shape)
            
            # Set border setting on canvas
            if hasattr(self.canvas, 'set_border_width'):
                # Parse border setting: 'n/a' = 0, '1px' = 1, '2px' = 2, '3px' = 3
                border_width = 0
                if border_setting != "n/a":
                    try:
                        border_width = int(border_setting.replace("px", ""))
                    except ValueError:
                        border_width = 0
                self.canvas.set_border_width(border_width)
            
            # Store background mode and border in metadata (for future use)
            # Background mode: 'common' means apply to first frame only, 'all' means apply to all frames
            if hasattr(metadata, 'background_mode'):
                metadata.background_mode = background_mode
            if hasattr(metadata, 'border_setting'):
                metadata.border_setting = border_setting
            
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
            
            # Validate file before parsing
            import os
            from pathlib import Path
            
            # Check file exists
            if not os.path.exists(file_path):
                QMessageBox.critical(
                    self,
                    "File Not Found",
                    f"The file does not exist:\n{file_path}\n\nPlease check the file path and try again."
                )
                return
            
            # Check file is readable
            if not os.access(file_path, os.R_OK):
                QMessageBox.critical(
                    self,
                    "Permission Denied",
                    f"Cannot read file:\n{file_path}\n\nPlease check file permissions."
                )
                return
            
            # Check file size
            try:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    QMessageBox.critical(
                        self,
                        "Empty File",
                        f"The file is empty:\n{file_path}\n\nPlease select a valid pattern file."
                    )
                    return
                
                # Warn if file is very large (>100MB)
                if file_size > 100 * 1024 * 1024:
                    reply = QMessageBox.question(
                        self,
                        "Large File Warning",
                        f"This file is very large ({file_size / (1024*1024):.1f} MB).\n\n"
                        "Loading may take a long time and use significant memory.\n\n"
                        "Do you want to continue?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
            except OSError as e:
                QMessageBox.critical(
                    self,
                    "File Access Error",
                    f"Cannot access file:\n{file_path}\n\nError: {str(e)}"
                )
                return
            
            # Parse file with comprehensive error handling
            try:
                from pathlib import Path
                file_ext = Path(file_path).suffix.lower()
                
                # Handle JSON/LEDPROJ files directly
                if file_ext in ['.json', '.ledproj']:
                    try:
                        pattern = Pattern.load_from_file(file_path)
                        format_name = "JSON Project"
                    except Exception as json_error:
                        QMessageBox.critical(
                            self,
                            "JSON Parse Failed",
                            f"Failed to load JSON pattern file:\n{file_path}\n\n"
                            f"Error: {str(json_error)}\n\n"
                            "The file may be corrupted or in an invalid format."
                        )
                        return
                else:
                    # Use parser registry for binary formats
                    from parsers.parser_registry import ParserRegistry
                    registry = ParserRegistry()
                    pattern, format_name = registry.parse_file(file_path)
                    
                    if not pattern:
                        QMessageBox.critical(
                            self,
                            "Parse Failed",
                            f"Failed to parse pattern file:\n{file_path}\n\n"
                            "The file format may be invalid or corrupted."
                        )
                        return
                
                # Validate pattern before loading
                if not isinstance(pattern, Pattern):
                    QMessageBox.critical(
                        self,
                        "Invalid Pattern",
                        f"Parsed file did not produce a valid pattern:\n{file_path}\n\n"
                        "The file may be in an unsupported format."
                    )
                    return
                
                # Validate pattern has frames - create default frame if missing
                if not hasattr(pattern, 'frames') or not pattern.frames:
                    # Create a blank frame with correct dimensions
                    width = pattern.metadata.width if pattern.metadata else 16
                    height = pattern.metadata.height if pattern.metadata else 16
                    pixel_count = width * height
                    blank_frame = Frame(
                        pixels=[(0, 0, 0)] * pixel_count,
                        duration_ms=100
                    )
                    pattern.frames = [blank_frame]
                    # Inform user that a blank frame was created (non-blocking in tests)
                    QMessageBox.information(
                        self,
                        "Empty Pattern",
                        f"Pattern file contains no frames. Created a blank frame ({width}x{height})."
                    )
                
                # Validate dimensions
                if hasattr(pattern, 'metadata') and pattern.metadata:
                    width = getattr(pattern.metadata, 'width', 0)
                    height = getattr(pattern.metadata, 'height', 0)
                    if width <= 0 or height <= 0:
                        QMessageBox.warning(
                            self,
                            "Invalid Dimensions",
                            f"Pattern has invalid dimensions ({width}x{height}):\n{file_path}\n\n"
                            "The pattern may need manual dimension specification."
                        )
                        # Still allow loading, user can fix dimensions later
                
                # Load pattern
                self.load_pattern(pattern, file_path)
                
            except FileNotFoundError as e:
                QMessageBox.critical(
                    self,
                    "File Not Found",
                    f"File not found:\n{str(e)}\n\nPlease check the file path and try again."
                )
            except PermissionError as e:
                QMessageBox.critical(
                    self,
                    "Permission Denied",
                    f"Cannot access file:\n{str(e)}\n\nPlease check file permissions."
                )
            except ValueError as e:
                error_msg = str(e)
                if "empty" in error_msg.lower():
                    QMessageBox.critical(
                        self,
                        "Empty File",
                        f"The file is empty:\n{file_path}\n\nPlease select a valid pattern file."
                    )
                elif "unknown format" in error_msg.lower() or "cannot be parsed" in error_msg.lower():
                    QMessageBox.critical(
                        self,
                        "Unsupported Format",
                        f"Cannot parse file format:\n{file_path}\n\n{error_msg}\n\n"
                        "Try specifying LED count and frame count manually using Tools > Force Dimensions."
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Parse Error",
                        f"Failed to parse pattern file:\n{file_path}\n\n{error_msg}\n\n"
                        "The file may be corrupted or in an unsupported format."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Unexpected Error",
                    f"An unexpected error occurred while opening the file:\n{file_path}\n\n"
                    f"Error: {str(e)}\n\n"
                    "Please try again or report this issue if it persists."
                )
                import logging
                logging.getLogger(__name__).error("Unexpected error opening pattern file", exc_info=True)

    def _apply_button_icon(
        self,
        button: QWidget,
        icon_name: str,
        tooltip: Optional[str] = None,
        icon_only: bool = False,
    ) -> None:
        """Configure a button or tool button with a themed icon."""
        # Auto-detect DPI from button's widget hierarchy
        icon = get_icon(icon_name, size=20, widget=button)
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
                # Ensure minimum size for visibility
                if hasattr(button, "setMinimumWidth"):
                    button.setMinimumWidth(24)
                if hasattr(button, "setMinimumHeight"):
                    button.setMinimumHeight(24)
                # Ensure icon is visible
                if hasattr(button, "setIconSize"):
                    button.setIconSize(QSize(20, 20))

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

        # Create horizontal splitter for split-view canvas
        canvas_splitter = QSplitter(Qt.Horizontal)
        canvas_splitter.setChildrenCollapsible(False)
        
        # Left side: Editable rectangular grid
        self.canvas = MatrixDesignCanvas(width=12, height=6, pixel_size=28)
        self.canvas.pixel_updated.connect(self._on_canvas_pixel_updated)
        self.canvas.painting_finished.connect(self._commit_paint_operation)
        # Eyedropper tool removed - color_picked signal no longer needed
        self.canvas.set_random_palette(self.DEFAULT_COLORS)
        self.canvas.set_gradient_brush(self._start_gradient_color, self._end_gradient_color, 32)
        canvas_splitter.addWidget(self.canvas)
        
        # Right side: Read-only circular preview
        self.circular_preview = CircularPreviewCanvas()
        canvas_splitter.addWidget(self.circular_preview)
        
        # Set stretch factors (left gets more space)
        canvas_splitter.setStretchFactor(0, 3)
        canvas_splitter.setStretchFactor(1, 2)
        
        # Set initial sizes (60% left, 40% right)
        canvas_splitter.setSizes([600, 400])
        
        layout.addWidget(canvas_splitter, 1)

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

        # Onion skinning controls
        onion_skin_group = QGroupBox("Onion Skinning")
        onion_layout = QVBoxLayout()
        
        self.onion_skin_checkbox = QCheckBox("Enable Onion Skin")
        self.onion_skin_checkbox.setChecked(False)
        self.onion_skin_checkbox.toggled.connect(self._on_onion_skin_toggled)
        onion_layout.addWidget(self.onion_skin_checkbox)
        
        onion_config_row = QHBoxLayout()
        onion_config_row.addWidget(QLabel("Previous:"))
        self.onion_skin_prev_count_spin = QSpinBox()
        self.onion_skin_prev_count_spin.setRange(0, 5)
        self.onion_skin_prev_count_spin.setValue(1)
        self.onion_skin_prev_count_spin.setEnabled(False)
        self.onion_skin_prev_count_spin.valueChanged.connect(self._on_onion_skin_settings_changed)
        onion_config_row.addWidget(self.onion_skin_prev_count_spin)
        
        onion_config_row.addWidget(QLabel("Opacity:"))
        self.onion_skin_prev_opacity_slider = QSlider(Qt.Horizontal)
        self.onion_skin_prev_opacity_slider.setRange(0, 100)
        self.onion_skin_prev_opacity_slider.setValue(50)
        self.onion_skin_prev_opacity_slider.setEnabled(False)
        self.onion_skin_prev_opacity_slider.valueChanged.connect(self._on_onion_skin_settings_changed)
        onion_config_row.addWidget(self.onion_skin_prev_opacity_slider)
        onion_layout.addLayout(onion_config_row)
        
        onion_config_row2 = QHBoxLayout()
        onion_config_row2.addWidget(QLabel("Next:"))
        self.onion_skin_next_count_spin = QSpinBox()
        self.onion_skin_next_count_spin.setRange(0, 5)
        self.onion_skin_next_count_spin.setValue(1)
        self.onion_skin_next_count_spin.setEnabled(False)
        self.onion_skin_next_count_spin.valueChanged.connect(self._on_onion_skin_settings_changed)
        onion_config_row2.addWidget(self.onion_skin_next_count_spin)
        
        onion_config_row2.addWidget(QLabel("Opacity:"))
        self.onion_skin_next_opacity_slider = QSlider(Qt.Horizontal)
        self.onion_skin_next_opacity_slider.setRange(0, 100)
        self.onion_skin_next_opacity_slider.setValue(30)
        self.onion_skin_next_opacity_slider.setEnabled(False)
        self.onion_skin_next_opacity_slider.valueChanged.connect(self._on_onion_skin_settings_changed)
        onion_config_row2.addWidget(self.onion_skin_next_opacity_slider)
        onion_layout.addLayout(onion_config_row2)
        
        onion_skin_group.setLayout(onion_layout)
        layout.addWidget(onion_skin_group)

        geometry_row = QHBoxLayout()
        geometry_row.addWidget(QLabel("Geometry Overlay:"))
        self.canvas_geometry_combo = QComboBox()
        overlay_options = [
            ("Rectangular", GeometryOverlay.MATRIX.value),
            ("Radial Rings", GeometryOverlay.RING.value),
            ("Irregular", GeometryOverlay.IRREGULAR.value),
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

    def _create_led_colors_tab(self) -> QWidget:
        """Create LED Colors tab with LED Color Panel."""
        from ui.widgets.led_color_panel import LEDColorPanel
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create LED Color Panel
        self.led_color_panel = LEDColorPanel(self)
        
        # Connect signals
        self.led_color_panel.brightness_changed.connect(self._on_led_brightness_changed)
        self.led_color_panel.gamma_changed.connect(self._on_led_gamma_changed)
        self.led_color_panel.color_selected.connect(self._on_led_palette_color_selected)
        self.led_color_panel.color_temperature_changed.connect(self._on_led_temp_changed)
        self.led_color_panel.preview_mode_changed.connect(self._on_led_preview_mode_changed)
        
        layout.addWidget(self.led_color_panel)
        layout.addStretch()
        
        return tab
    
    def _create_pixel_mapping_tab(self) -> QWidget:
        """Create Pixel Mapping tab with wiring configuration."""
        from ui.widgets.pixel_mapping_widget import PixelMappingWidget
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create Pixel Mapping Widget
        self.pixel_mapping_widget = PixelMappingWidget(self)
        
        # Connect signals
        self.pixel_mapping_widget.mapping_changed.connect(self._on_pixel_mapping_changed)
        
        layout.addWidget(self.pixel_mapping_widget)
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
            self._apply_button_icon(copy_btn, "duplicate", tooltip="Copy the current composite frame into this scratchpad.")
            row.addWidget(copy_btn)

            paste_btn = QPushButton("Paste")
            paste_btn.setToolTip("Paste scratchpad contents into the active frame.")
            paste_btn.setEnabled(False)
            paste_btn.clicked.connect(lambda _=False, s=slot: self._paste_from_scratchpad(s))
            self._apply_button_icon(paste_btn, "add", tooltip="Paste scratchpad contents into the active frame.")
            row.addWidget(paste_btn)

            clear_btn = QToolButton()
            clear_btn.setText("Clear")
            clear_btn.setToolTip("Remove stored pixels from this slot.")
            clear_btn.clicked.connect(lambda _=False, s=slot: self._clear_scratchpad_slot(s))
            self._apply_button_icon(clear_btn, "delete", tooltip="Remove stored pixels from this slot.", icon_only=True)
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
        # NOTE: Do NOT sync_frame_from_layers() here - composite is derived via render_frame()
        # Only sync when explicitly needed (export, preview generation)
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
                # Add tooltip to indicate slot state
                if filled:
                    paste_btn.setToolTip("Paste scratchpad contents into the active frame.")
                    paste_btn.setStyleSheet("")
                else:
                    paste_btn.setToolTip("Slot empty - nothing to paste. Copy a frame first.")
                    paste_btn.setStyleSheet("color: #888; background-color: #2a2a2a;")

    def _set_canvas_status(self, message: str) -> None:
        label = getattr(self, "canvas_status_label", None)
        if label:
            label.setText(message)

    def _mark_dirty(self):
        self._has_unsaved_changes = True

    def _mark_clean(self):
        self._has_unsaved_changes = False

    def _confirm_discard_changes(self) -> bool:
        """Confirm discard changes, offering save option."""
        if not self._has_unsaved_changes:
            return True
        
        # Create custom dialog with three options
        msg = QMessageBox(self)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("You have unsaved changes. What would you like to do?")
        msg.setIcon(QMessageBox.Question)
        
        save_btn = msg.addButton("Save and Continue", QMessageBox.AcceptRole)
        discard_btn = msg.addButton("Discard and Continue", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.setDefaultButton(cancel_btn)
        
        msg.exec()
        
        if msg.clickedButton() == save_btn:
            # Show export/save dialog
            try:
                # Store original unsaved state
                was_unsaved = self._has_unsaved_changes
                self._on_open_export_dialog()
                # Check if save was successful (unsaved flag cleared)
                if not self._has_unsaved_changes:
                    return True
                else:
                    # User cancelled save dialog or save failed
                    if was_unsaved:
                        # Still unsaved, user may have cancelled
                        return False
                    return True
            except Exception as e:
                QMessageBox.critical(
            self,
                    "Save Failed",
                    f"Failed to save pattern:\n{str(e)}"
                )
                return False
        elif msg.clickedButton() == discard_btn:
            return True
        else:
            # Cancel
            return False

    def _create_layers_tab(self) -> QWidget:
        """Create the Layers tab with layer panel widget."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scroll area for layer panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create layer panel widget
        self.layer_panel = LayerPanelWidget(self.layer_manager, self)
        self.layer_panel.active_layer_changed.connect(self._on_active_layer_changed)
        self.layer_panel.solo_mode_changed.connect(self._on_solo_mode_changed)
        scroll.setWidget(self.layer_panel)
        
        layout.addWidget(scroll)
        return tab

    def _create_effects_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create scroll area for effects widget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.effects_widget = EffectsLibraryWidget()
        self.effects_widget.effectSelected.connect(self._on_effect_selection_changed)
        self.effects_widget.previewRequested.connect(self._on_effect_preview_requested)
        self.effects_widget.applyRequested.connect(self._on_effect_apply_requested)
        self.effects_widget.refreshRequested.connect(self._on_effects_refresh_requested)
        self.effects_widget.openFolderRequested.connect(self._on_effects_open_folder)
        scroll.setWidget(self.effects_widget)
        layout.addWidget(scroll)

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
        # Update canvas to show composite or active layer
        self._load_current_frame_into_canvas()
        if hasattr(self, "timeline"):
            self.timeline.set_selected_layer(layer_index)
        self._update_status_labels()  # Update layer status display
        # Update the active layer status label in automation UI if it exists
        if hasattr(self, '_update_active_layer_status'):
            self._update_active_layer_status()
    
    def _on_solo_mode_changed(self, enabled: bool):
        """Handle solo mode toggle."""
        # Reload canvas to show only active layer when solo mode is on
        self._load_current_frame_into_canvas()
        self._update_status_labels()

    def _on_timeline_layer_visibility_toggled(self, layer_index: int):
        """Handle layer visibility toggle from timeline eye icon."""
        if not self._pattern:
            return
        
        # Get current frame
        current_frame = self._current_frame_index
        
        # Get layer visibility state
        layers = self.layer_manager.get_layers(current_frame)
        if layer_index < len(layers):
            layer = layers[layer_index]
            new_visible = not layer.visible
            self.layer_manager.set_layer_visible(current_frame, layer_index, new_visible)
            # Refresh timeline to update eye icon
            self._refresh_timeline()
            # Update canvas
            self._load_current_frame_into_canvas()
    
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
        # Theme selector removed - only dark theme available
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
        self._apply_button_icon(pixel_btn, "brush", tooltip="Pixel brush tool")
        tool_layout.addWidget(pixel_btn, 0, 0)

        # Rectangle tool
        rect_btn = QPushButton("Rectangle")
        rect_btn.setCheckable(True)
        rect_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.RECTANGLE))
        self.tool_button_group.addButton(rect_btn, 1)
        self._apply_button_icon(rect_btn, "brush", tooltip="Rectangle tool")
        tool_layout.addWidget(rect_btn, 0, 1)

        # Circle tool
        circle_btn = QPushButton("Circle")
        circle_btn.setCheckable(True)
        circle_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.CIRCLE))
        self.tool_button_group.addButton(circle_btn, 2)
        self._apply_button_icon(circle_btn, "brush", tooltip="Circle tool")
        tool_layout.addWidget(circle_btn, 1, 0)

        # Line tool
        line_btn = QPushButton("Line")
        line_btn.setCheckable(True)
        line_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.LINE))
        self.tool_button_group.addButton(line_btn, 3)
        self._apply_button_icon(line_btn, "brush", tooltip="Line tool")
        tool_layout.addWidget(line_btn, 1, 1)

        random_btn = QPushButton("Random Spray")
        random_btn.setCheckable(True)
        random_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.RANDOM))
        self.tool_button_group.addButton(random_btn, 4)
        self._apply_button_icon(random_btn, "brush", tooltip="Random spray tool")
        tool_layout.addWidget(random_btn, 2, 0)

        gradient_btn = QPushButton("Gradient Brush")
        gradient_btn.setCheckable(True)
        gradient_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.GRADIENT))
        self.tool_button_group.addButton(gradient_btn, 5)
        self._apply_button_icon(gradient_btn, "brush", tooltip="Gradient brush tool")
        tool_layout.addWidget(gradient_btn, 2, 1)

        # Bucket fill tool
        bucket_btn = QPushButton("Bucket Fill")
        bucket_btn.setCheckable(True)
        bucket_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.BUCKET_FILL))
        self.tool_button_group.addButton(bucket_btn, 6)
        self._apply_button_icon(bucket_btn, "brush", tooltip="Bucket fill tool")
        tool_layout.addWidget(bucket_btn, 2, 2)

        # Eraser tool
        eraser_btn = QPushButton("Eraser")
        eraser_btn.setCheckable(True)
        eraser_btn.clicked.connect(lambda: self._on_tool_selected(DrawingMode.ERASER))
        self.tool_button_group.addButton(eraser_btn, 7)
        self._apply_button_icon(eraser_btn, "brush", tooltip="Eraser tool")
        tool_layout.addWidget(eraser_btn, 0, 2)

        layout.addLayout(tool_layout)

        # Shape fill option
        self.shape_filled_checkbox = QCheckBox("Filled shapes")
        self.shape_filled_checkbox.setChecked(True)
        self.shape_filled_checkbox.setEnabled(False)  # Enabled when shape tool selected
        self.shape_filled_checkbox.toggled.connect(self._on_shape_filled_changed)
        layout.addWidget(self.shape_filled_checkbox)

        # Bucket fill tolerance row (visible only when bucket tool selected)
        tolerance_row = QHBoxLayout()
        tolerance_row.setContentsMargins(0, 0, 0, 0)
        
        self.bucket_fill_tolerance_spin = QSpinBox()
        self.bucket_fill_tolerance_spin.setRange(0, 255)
        self.bucket_fill_tolerance_spin.setValue(0)
        self.bucket_fill_tolerance_spin.setSuffix(" tol")
        self.bucket_fill_tolerance_spin.setToolTip("Color tolerance for bucket fill (0-255)")
        self.bucket_fill_tolerance_spin.setEnabled(False)
        self.bucket_fill_tolerance_spin.valueChanged.connect(self._on_bucket_fill_tolerance_changed)

        tolerance_row.addWidget(self.bucket_fill_tolerance_spin)
        
        # Bucket fill contiguous option
        self.bucket_fill_contiguous_checkbox = QCheckBox("Contiguous")
        self.bucket_fill_contiguous_checkbox.setChecked(True)
        self.bucket_fill_contiguous_checkbox.setToolTip("Only fill connected pixels of same color. Uncheck for global replacement.")
        self.bucket_fill_contiguous_checkbox.setEnabled(False)
        self.bucket_fill_contiguous_checkbox.toggled.connect(self._on_bucket_fill_contiguous_changed)
        tolerance_row.addWidget(self.bucket_fill_contiguous_checkbox)
        
        tolerance_row.addStretch()
        layout.addLayout(tolerance_row)

        # Gradient Settings Group (visible only when gradient tool selected)
        self.gradient_settings_group = QGroupBox("Gradient Settings")
        grad_layout = QVBoxLayout()
        
        # Gradient Type
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self.gradient_type_combo = QComboBox()
        self.gradient_type_combo.addItem("Linear", GradientType.LINEAR)
        self.gradient_type_combo.addItem("Radial", GradientType.RADIAL)
        self.gradient_type_combo.currentIndexChanged.connect(self._on_gradient_type_changed)
        type_row.addWidget(self.gradient_type_combo)
        grad_layout.addLayout(type_row)
        
        # Gradient Editor
        self.gradient_editor = GradientEditorWidget()
        self.gradient_editor.gradient_changed.connect(self._on_gradient_changed)
        grad_layout.addWidget(self.gradient_editor)
        
        # Presets
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Presets:"))
        self.gradient_preset_combo = QComboBox()
        self.gradient_preset_combo.addItem("Custom")
        for preset_name in PRESET_GRADIENTS.keys():
            self.gradient_preset_combo.addItem(preset_name.capitalize(), preset_name)
        self.gradient_preset_combo.currentIndexChanged.connect(self._on_gradient_preset_selected)
        preset_row.addWidget(self.gradient_preset_combo)
        grad_layout.addLayout(preset_row)
        
        self.gradient_settings_group.setLayout(grad_layout)
        self.gradient_settings_group.setVisible(False) # Hidden by default
        layout.addWidget(self.gradient_settings_group)

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

        # Brush propagation combo box
        brush_propagation_label = QLabel("Apply to:")
        layout.addWidget(brush_propagation_label)

        self.brush_propagation_combo = QComboBox()
        self.brush_propagation_combo.addItem("Current frame only", "current")
        self.brush_propagation_combo.addItem("First frame only", "first")
        self.brush_propagation_combo.addItem("All frames", "all")
        self.brush_propagation_combo.setCurrentIndex(0)  # Default: current frame
        self.brush_propagation_combo.setToolTip(
            "Select which frames to apply brush strokes to:\n"
            "- Current frame only: Apply only to current frame (default)\n"
            "- First frame only: Apply to first frame (for backgrounds)\n"
            "- All frames: Apply to all frames in pattern (warning: destructive)"
        )
        self.brush_propagation_combo.currentIndexChanged.connect(self._on_brush_propagation_changed)
        layout.addWidget(self.brush_propagation_combo)

        group.setLayout(layout)
        return group

    def _on_tool_selected(self, mode: DrawingMode):
        """Handle tool selection."""
        if self.canvas:
            self.canvas.set_drawing_mode(mode)
            # Enable/disable filled checkbox based on tool
            self.shape_filled_checkbox.setEnabled(mode != DrawingMode.PIXEL and mode != DrawingMode.LINE and mode != DrawingMode.BUCKET_FILL)
            # Enable/disable tolerance control and contiguous checkbox based on tool
            if hasattr(self, 'bucket_fill_tolerance_spin'):
                self.bucket_fill_tolerance_spin.setEnabled(mode == DrawingMode.BUCKET_FILL)
            if hasattr(self, 'bucket_fill_contiguous_checkbox'):
                self.bucket_fill_contiguous_checkbox.setEnabled(mode == DrawingMode.BUCKET_FILL)
            
            # Sync gradient brush settings when gradient tool is selected
            if mode == DrawingMode.GRADIENT:
                self.gradient_settings_group.setVisible(True)
                self._sync_gradient_brush_settings()
            else:
                if hasattr(self, 'gradient_settings_group'):
                    self.gradient_settings_group.setVisible(False)

    def _on_gradient_type_changed(self, index: int):
        """Handle gradient type change."""
        if not self.canvas:
            return
        grad_type = self.gradient_type_combo.currentData()
        self.canvas.set_gradient_type(grad_type)
        # Update current gradient in editor if exists
        grad = self.canvas._gradient
        if grad:
            grad.type = grad_type
            self.gradient_editor.update()

    def _on_gradient_changed(self, gradient):
        """Handle gradient modification from editor."""
        if self.canvas:
            self.canvas.set_gradient(gradient)

    def _on_gradient_preset_selected(self, index: int):
        """Handle preset selection."""
        preset_name = self.gradient_preset_combo.currentData()
        if preset_name and self.canvas:
            if self.canvas.load_preset_gradient(preset_name):
                # Update editor with new gradient
                self.gradient_editor.set_gradient(self.canvas._gradient)
                # Update type combo if preset has different type
                grad_type = self.canvas._gradient.type
                idx = self.gradient_type_combo.findData(grad_type)
                if idx >= 0:
                    self.gradient_type_combo.blockSignals(True)
                    self.gradient_type_combo.setCurrentIndex(idx)
                    self.gradient_type_combo.blockSignals(False)

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
    
    def _sync_gradient_brush_settings(self):
        """Sync the gradient settings UI with the current canvas gradient state."""
        if not self.canvas:
            return
        
        grad = self.canvas._gradient
        if not grad:
            # Create a default gradient if none exists
            from core.gradient import create_simple_gradient
            grad = create_simple_gradient(self._current_color, (0, 0, 0), self.canvas._gradient_type)
            self.canvas.set_gradient(grad)
        
        # Update gradient editor
        self.gradient_editor.set_gradient(grad)
        
        # Update type combo
        reg_type = grad.type
        idx = self.gradient_type_combo.findData(reg_type)
        if idx >= 0:
            self.gradient_type_combo.blockSignals(True)
            self.gradient_type_combo.setCurrentIndex(idx)
            self.gradient_type_combo.blockSignals(False)
        
        # Reset preset combo to "Custom"
        self.gradient_preset_combo.blockSignals(True)
        self.gradient_preset_combo.setCurrentIndex(0)
        self.gradient_preset_combo.blockSignals(False)

    def _create_broadcast_warning_banner(self) -> QWidget:
        """Create warning banner for broadcast mode."""
        banner = QFrame()
        banner.setObjectName("broadcastWarningBanner")
        banner.setStyleSheet("""
            QFrame#broadcastWarningBanner {
                background-color: #ff4444;
                border: 2px solid #cc0000;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(warning_icon)
        
        warning_text = QLabel("Broadcast Mode Active - Changes apply to ALL frames")
        warning_text.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        layout.addWidget(warning_text)
        
        layout.addStretch()
        
        disable_btn = QPushButton("Disable Broadcast")
        disable_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #cc0000;
                border: 1px solid white;
                border-radius: 3px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffeeee;
            }
        """)
        disable_btn.clicked.connect(lambda: self.brush_propagation_combo.setCurrentIndex(0))
        layout.addWidget(disable_btn)
        
        return banner
    
    def _create_hidden_layer_warning_banner(self) -> QWidget:
        """Create warning banner for hidden layer painting."""
        banner = QFrame()
        banner.setObjectName("hiddenLayerWarningBanner")
        banner.setStyleSheet("""
            QFrame#hiddenLayerWarningBanner {
                background-color: #ff8800;
                border: 2px solid #cc6600;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        warning_icon = QLabel("👁️‍🗨️")
        warning_icon.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(warning_icon)
        
        self._hidden_layer_warning_label = QLabel("Painting on hidden layer - changes won't be visible")
        self._hidden_layer_warning_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        layout.addWidget(self._hidden_layer_warning_label)
        
        layout.addStretch()
        
        return banner
    
    # Layer sync warning banner removed - syncing is now automatic with new architecture
    
    def _on_brush_propagation_changed(self, index: int):
        """Handle brush propagation mode change."""
        mode = self.brush_propagation_combo.currentData()
        
        if mode == "all":
            # Show confirmation dialog on first enable
            if not hasattr(self, '_brush_broadcast_warning_shown'):
                self._brush_broadcast_warning_shown = False
            
            if not self._brush_broadcast_warning_shown:
                reply = QMessageBox.question(
                    self,
                    "Enable Broadcast Mode?",
                    "⚠️ WARNING: Broadcast Mode will apply ALL brush strokes to EVERY frame in your pattern.\n\n"
                    "This is a destructive operation that affects the entire pattern.\n\n"
                    "Do you want to enable Broadcast Mode?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    # User cancelled, reset to "current frame only"
                    self.brush_propagation_combo.blockSignals(True)
                    self.brush_propagation_combo.setCurrentIndex(0)
                    self.brush_propagation_combo.blockSignals(False)
                    return
                
                self._brush_broadcast_warning_shown = True
            
            # Show warning banner for "all frames" mode
            if not hasattr(self, '_brush_broadcast_banner') or not self._brush_broadcast_banner:
                self._brush_broadcast_banner = self._create_broadcast_warning_banner()
                # Try to add banner to layout (insert before the combo box area)
                if hasattr(self, 'drawing_tools_layout'):
                    self.drawing_tools_layout.insertWidget(0, self._brush_broadcast_banner)
            if hasattr(self, '_brush_broadcast_banner') and self._brush_broadcast_banner:
                self._brush_broadcast_banner.setVisible(True)
            
            # Update timeline highlights to show all frames affected
            if hasattr(self, "timeline") and self.timeline and self._pattern and self._pattern.frames:
                all_indices = list(range(len(self._pattern.frames)))
                highlight_color = QColor(255, 200, 0, 100)  # Yellow with transparency
                self.timeline.highlight_frames(all_indices, highlight_color)
        else:
            # Hide warning for "current" and "first" modes
            if hasattr(self, '_brush_broadcast_banner') and self._brush_broadcast_banner:
                self._brush_broadcast_banner.setVisible(False)
            
            # Clear timeline highlights
            if hasattr(self, "timeline") and self.timeline:
                self.timeline.clear_highlights()

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
        from ui.widgets.enhanced_text_tool import EnhancedTextToolWidget
        
        group = QGroupBox("Text Animation")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Use enhanced text tool widget
        self.enhanced_text_tool = EnhancedTextToolWidget(
            self,
            self.font_repo,
            dimension_provider=lambda: (self.width_spin.value(), self.height_spin.value()),
        )
        self.enhanced_text_tool.set_font_designer_callback(self._open_font_designer)
        self.enhanced_text_tool.set_primary_color(self._current_color)
        self.enhanced_text_tool.generate_requested.connect(self._on_generate_text_animation)
        self.enhanced_text_tool.text_changed.connect(self._on_enhanced_text_changed)
        layout.addWidget(self.enhanced_text_tool)
        
        # Keep legacy text input for backward compatibility (hidden by default)
        text_input_row = QHBoxLayout()
        text_input_row.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text to animate...")
        self.text_input.textChanged.connect(self._on_text_input_changed)
        self.text_input.setVisible(False)  # Hide legacy input
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
            if hasattr(self, "enhanced_text_tool") and self.enhanced_text_tool:
                self.enhanced_text_tool.set_primary_color(self._current_color)

    def _on_enhanced_text_changed(self, text: str):
        """Handle enhanced text tool text change - update legacy input for compatibility."""
        if hasattr(self, "text_input"):
            self.text_input.setText(text)

    def _on_generate_text_animation(self):
        """Generate animated text frames based on current settings."""
        # Use enhanced text tool if available, otherwise fall back to legacy
        if hasattr(self, "enhanced_text_tool") and self.enhanced_text_tool:
            text = self.enhanced_text_tool.get_text().strip()
        else:
            text = self.text_input.text().strip() if hasattr(self, "text_input") else ""
        
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text to animate.")
            return

        if not self._pattern:
            self._create_default_pattern()

        anim_type = self.text_animation_type_combo.currentText() if hasattr(self, "text_animation_type_combo") else "Typed (Character by Character)"
        frames_per_char = self.text_frames_per_char_spin.value() if hasattr(self, "text_frames_per_char_spin") else 2
        font_size = self.text_font_size_spin.value() if hasattr(self, "text_font_size_spin") else 8
        text_color = self._current_color

        frames = self._generate_text_frames(text, anim_type, frames_per_char, text_color)
        
        if frames:
            # Auto-append frames (no dialog - automatic)
            if not self._pattern.frames:
                self._pattern.frames = frames
            else:
                # Auto-append to existing frames
                self._pattern.frames.extend(frames)

            # NOTE: Do NOT sync_frame_from_layers() here - composite is derived via render_frame()
            # Only sync when explicitly needed (export, preview generation)

            # Update frame manager with new pattern state
            self.frame_manager.set_pattern(self._pattern)
            # Update layer manager so it knows about new frames
            if hasattr(self, 'layer_manager') and self.layer_manager:
                self.layer_manager.set_pattern(self._pattern)
            self.history_manager.set_frame_count(len(self._pattern.frames))
            self._current_frame_index = len(self._pattern.frames) - len(frames)  # Set to first new frame
            self.frame_manager.select(self._current_frame_index)
            self._load_current_frame_into_canvas()
            self._refresh_timeline()
            self._update_status_labels()
            self.pattern_modified.emit()
            # Removed success dialog - automatic operation

    def _build_text_render_options(
        self,
        width: int,
        height: int,
        text_color: Tuple[int, int, int],
    ) -> TextRenderOptions:
        if hasattr(self, "enhanced_text_tool") and self.enhanced_text_tool:
            return self.enhanced_text_tool.build_render_options(width, height, text_color)
        return TextRenderOptions(
            width=width,
            height=height,
            color=text_color,
            background=(0, 0, 0),
            alignment="center",
            spacing=0,
            line_spacing=1,
            multiline=True,
            font_size=self._current_font_metrics()[1],
        )

    def _build_text_scroll_options(self, direction: str) -> TextScrollOptions:
        if hasattr(self, "enhanced_text_tool") and self.enhanced_text_tool:
            return self.enhanced_text_tool.get_scroll_options(direction)
        return TextScrollOptions(direction=direction)

    def _generate_text_frames(
        self,
        text: str,
        anim_type: str,
        frames_per_char: int,
        text_color: Tuple[int, int, int],
    ) -> List[Frame]:
        """Generate frames for text animation using the shared text renderer."""
        # Validate and sanitize text
        if not isinstance(text, str):
            text = str(text)
        text = text.strip()
        
        if not text:
            return []
        
        # Log text for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Generating text frames for: {repr(text)}")
        
        # Ensure text is properly encoded
        try:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            text = str(text)
        
        width = self.width_spin.value() if hasattr(self, "width_spin") else self._pattern.metadata.width
        height = self.height_spin.value() if hasattr(self, "height_spin") else self._pattern.metadata.height
        render_opts = self._build_text_render_options(width, height, text_color)

        if "Scrolling" in anim_type:
            direction = anim_type.split()[-1].lower()
            scroll_opts = self._build_text_scroll_options(direction)
            pixel_frames = self.text_renderer.render_scroll_frames(text, render_opts, scroll_opts)
        else:
            pixel_frames = self.text_renderer.render_typing_frames(text, render_opts, frames_per_char, self._frame_duration_ms)

        frames: List[Frame] = []
        for pixels in pixel_frames:
            frames.append(Frame(duration_ms=self._frame_duration_ms, pixels=list(pixels)))
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
        width, height = self._current_font_metrics()
        provider = self._glyph_provider
        if getattr(self, "_active_bitmap_font", None):
            provider = GlyphProvider(bitmap_font=self._active_bitmap_font)
        return provider.with_size(width, height).glyph(char)
        # Legacy fallback maintained below for reference and to preserve historical
        # glyph definitions. Execution never reaches this path because we return
        # early using the shared GlyphProvider.
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

        preview_controls.addWidget(QLabel("Max frames:"))
        self.lms_preview_limit_spin = QSpinBox()
        self.lms_preview_limit_spin.setRange(1, 240)
        self.lms_preview_limit_spin.setValue(60)
        preview_controls.addWidget(self.lms_preview_limit_spin)
        preview_controls.addStretch()
        preview_layout.addLayout(preview_controls)

        # Preview mode banner (initially hidden)
        self.lms_preview_banner = QFrame()
        self.lms_preview_banner.setObjectName("lmsPreviewBanner")
        self.lms_preview_banner.setStyleSheet("""
            QFrame#lmsPreviewBanner {
                background-color: #4444ff;
                border: 2px solid #0000cc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        banner_layout = QHBoxLayout(self.lms_preview_banner)
        banner_layout.setContentsMargins(8, 8, 8, 8)
        banner_layout.setSpacing(8)
        
        preview_icon = QLabel("👁️")
        preview_icon.setStyleSheet("font-size: 18px; font-weight: bold;")
        banner_layout.addWidget(preview_icon)
        
        preview_mode_text = QLabel("PREVIEW MODE")
        preview_mode_text.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        banner_layout.addWidget(preview_mode_text)
        
        banner_layout.addStretch()
        
        # Apply Preview button
        self.lms_apply_preview_btn = QPushButton("Apply Preview Changes")
        self.lms_apply_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #00cc00;
                color: white;
                border: 1px solid white;
                border-radius: 3px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ee00;
            }
        """)
        self.lms_apply_preview_btn.clicked.connect(self._on_lms_apply_preview)
        banner_layout.addWidget(self.lms_apply_preview_btn)
        
        # Restore Original button
        self.lms_restore_original_btn = QPushButton("Restore Original (Ctrl+R)")
        self.lms_restore_original_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #0000cc;
                border: 1px solid white;
                border-radius: 3px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eeeeff;
            }
        """)
        self.lms_restore_original_btn.clicked.connect(self._on_lms_exit_preview)
        banner_layout.addWidget(self.lms_restore_original_btn)
        
        self.lms_preview_banner.setVisible(False)
        preview_layout.addWidget(self.lms_preview_banner)

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
        
        # Show preview banner and update status
        if hasattr(self, 'lms_preview_banner') and self.lms_preview_banner:
            self.lms_preview_banner.setVisible(True)
        if self.lms_preview_status_label:
            self.lms_preview_status_label.setText(
                f"⚠️ PREVIEW MODE: Previewing {len(preview_frames)} frame(s). "
                "Use 'Apply Preview Changes' to keep the preview, or 'Restore Original' to discard it."
            )
            self.lms_preview_status_label.setStyleSheet("""
                color: #ff4444;
                font-weight: bold;
                background-color: #ffeeee;
                padding: 8px;
                border: 1px solid #ffaaaa;
                border-radius: 4px;
            """)

    def _on_lms_exit_preview(self):
        """Restore original pattern from preview."""
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
        
        # Hide preview banner and reset status
        if hasattr(self, 'lms_preview_banner') and self.lms_preview_banner:
            self.lms_preview_banner.setVisible(False)
        if self.lms_preview_status_label:
            self.lms_preview_status_label.setText("Preview closed. Restored original pattern frames.")
            self.lms_preview_status_label.setStyleSheet("color: #888;")
    
    def _on_lms_apply_preview(self):
        """Apply preview changes to pattern permanently."""
        if not self._lms_preview_snapshot:
            QMessageBox.information(self, "No Preview", "No preview is active.")
            return
        
        reply = QMessageBox.question(
            self,
            "Apply Preview Changes?",
            "This will replace the original pattern with the preview.\n\n"
            "The original pattern will be lost. Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Keep the preview pattern, discard the snapshot
            self._lms_preview_snapshot = None
            self.pattern_modified.emit()
            
            # Hide preview banner and reset status
            if hasattr(self, 'lms_preview_banner') and self.lms_preview_banner:
                self.lms_preview_banner.setVisible(False)
            if self.lms_preview_status_label:
                self.lms_preview_status_label.setText("Preview applied. Original pattern has been replaced.")
                self.lms_preview_status_label.setStyleSheet("color: #008800; font-weight: bold;")

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
        use_first = QRadioButton("Use first frame (Frame 0) as source")
        each_frame = QRadioButton("Use selected frame as source")
        increment_frame = QRadioButton("Increment parameters per frame")
        each_frame.setChecked(True)
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
        
        # Select Range button
        select_range_btn = QPushButton("Select Range")
        select_range_btn.setToolTip("Select frames in the specified range on timeline")
        select_range_btn.clicked.connect(self._on_select_range_clicked)
        self._apply_button_icon(select_range_btn, "target", tooltip="Select frames in the specified range on timeline")
        range_row.addWidget(select_range_btn)
        
        # Select All button
        select_all_btn = QPushButton("Select All")
        select_all_btn.setToolTip("Select all frames")
        select_all_btn.clicked.connect(self._on_select_all_frames_clicked)
        self._apply_button_icon(select_all_btn, "target", tooltip="Select all frames")
        range_row.addWidget(select_all_btn)
        
        range_row.addStretch()
        layout.addLayout(range_row)
        
        # Range operations
        range_ops_row = QHBoxLayout()
        range_ops_row.addWidget(QLabel("Range Operations:"))
        
        # Clear range button
        clear_range_btn = QPushButton("Clear Range")
        clear_range_btn.setToolTip("Clear all pixels in selected range")
        clear_range_btn.clicked.connect(self._on_clear_range_clicked)
        self._apply_button_icon(clear_range_btn, "delete", tooltip="Clear all pixels in selected range")
        range_ops_row.addWidget(clear_range_btn)
        
        # Invert range button
        invert_range_btn = QPushButton("Invert Range")
        invert_range_btn.setToolTip("Invert colors in selected range")
        invert_range_btn.clicked.connect(self._on_invert_range_clicked)
        self._apply_button_icon(invert_range_btn, "refresh", tooltip="Invert colors in selected range")
        range_ops_row.addWidget(invert_range_btn)
        
        # Delete range button
        delete_range_btn = QPushButton("Delete Range")
        delete_range_btn.setToolTip("Delete frames in selected range")
        delete_range_btn.clicked.connect(self._on_delete_range_clicked)
        self._apply_button_icon(delete_range_btn, "delete", tooltip="Delete frames in selected range")
        range_ops_row.addWidget(delete_range_btn)
        
        range_ops_row.addStretch()
        layout.addLayout(range_ops_row)

        # Frame generation options - removed (auto-detection now)
        # Automation now auto-detects when to generate frames vs apply to existing frames
        # Frame count is auto-calculated from action parameters

        group.setLayout(layout)
        return group

    def _create_automation_actions_group(self) -> QGroupBox:
        group = QGroupBox("Automation Actions")
        layout = QVBoxLayout()

        wizard_row = QHBoxLayout()
        wizard_btn = QPushButton("Automation Wizard…")
        wizard_btn.setToolTip("Open guided wizard to stack actions and apply fades/overlays.")
        wizard_btn.clicked.connect(self._open_automation_wizard)
        self._apply_button_icon(wizard_btn, "automation", tooltip="Open guided wizard to stack actions and apply fades/overlays.")
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
        self._apply_button_icon(invert_btn, "automation", tooltip="Invert colours")
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
        self._apply_button_icon(add_btn, "add", tooltip=f"Add {label} action")
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
        
        # Get active layer or default to layer 0
        active_layer = 0
        if hasattr(self, 'layer_panel') and self.layer_panel:
            active_layer = self.layer_panel.get_active_layer_index()
            if active_layer < 0:
                active_layer = 0
        
        # Update layer pixels instead of frame.pixels directly
        for idx, frame in enumerate(self._pattern.frames):
            t = idx / denom
            factor = t if fade_in else (1.0 - t)
            factor = max(0.05, min(1.0, factor))
            
            # Get current pixels from layer or frame
            if hasattr(self, 'layer_manager') and self.layer_manager:
                # Get pixels from layer
                layer_frame = self.layer_manager.get_layer_track(active_layer).get_frame(idx)
                if layer_frame:
                    current_pixels = layer_frame.pixels
                else:
                    # Fallback to frame pixels
                    current_pixels = frame.pixels
            else:
                current_pixels = frame.pixels
            
            new_pixels = [
                (
                    int(max(0, min(255, pixel[0] * factor))),
                    int(max(0, min(255, pixel[1] * factor))),
                    int(max(0, min(255, pixel[2] * factor))),
                )
                for pixel in current_pixels
            ]
            
            # Update layer if using layer manager
            if hasattr(self, 'layer_manager') and self.layer_manager:
                self.layer_manager.replace_pixels(idx, new_pixels, active_layer)
            else:
                # Fallback: update frame directly (legacy mode)
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
        
        # Apply to Active Layer option
        self.apply_to_layer_checkbox = QCheckBox("Apply to Active Layer (Creates Animation)")
        self.apply_to_layer_checkbox.setToolTip(
            "When enabled, automation actions will be applied only to the currently active layer, "
            "creating both layer animations (for runtime playback) and baked frames (for preview/export). "
            "This allows multiple layers to have independent animations. "
            "If no valid layer is selected, a warning will be shown."
        )
        layout.addWidget(self.apply_to_layer_checkbox)
        
        # Active layer status label
        self.active_layer_status_label = QLabel()
        self.active_layer_status_label.setStyleSheet("color: #888; font-size: 9pt; padding-left: 20px;")
        self.active_layer_status_label.setWordWrap(True)
        layout.addWidget(self.active_layer_status_label)
        
        # Connect checkbox signal to update status
        self.apply_to_layer_checkbox.stateChanged.connect(self._on_apply_to_layer_changed)

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

        # Apply, Cancel, and Finalize buttons
        apply_row = QHBoxLayout()
        self.apply_effect_btn = QPushButton("✓ Apply Effect")
        self.apply_effect_btn.setEnabled(False)
        self.apply_effect_btn.clicked.connect(self._on_apply_effect)
        apply_row.addWidget(self.apply_effect_btn)
        
        self.cancel_effect_btn = QPushButton("✗ Cancel Preview")
        self.cancel_effect_btn.setEnabled(False)
        self.cancel_effect_btn.setToolTip("Discard preview and return to original pattern")
        self.cancel_effect_btn.clicked.connect(self._on_cancel_effect_preview)
        apply_row.addWidget(self.cancel_effect_btn)
        
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
        # Initialize active layer status label
        if hasattr(self, '_update_active_layer_status'):
            self._update_active_layer_status()
        return group

    def _on_effect_type_changed(self, effect_type: str):
        """Handle effect type selection change."""
        self._update_effect_description()
        self.apply_effect_btn.setEnabled(False)
        self.cancel_effect_btn.setEnabled(False)
        self.effect_preview_status.hide()
    
    def _on_apply_to_layer_changed(self, state: int):
        """Handle 'Apply to Active Layer' checkbox state change."""
        if state == Qt.Checked:
            # Validate active layer when checkbox is checked
            if not hasattr(self, 'layer_panel') or not self.layer_panel:
                QMessageBox.warning(
                    self,
                    "Layer Panel Not Available",
                    "Layer panel is not initialized. The checkbox has been unchecked."
                )
                self.apply_to_layer_checkbox.setChecked(False)
                self._update_active_layer_status()
                return
            
            tracks = self.layer_manager.get_layer_tracks()
            active_layer = self.layer_panel.get_active_layer_index()
            
            if not tracks:
                QMessageBox.warning(
                    self,
                    "No Layers",
                    "No layers exist. Please create at least one layer first. The checkbox has been unchecked."
                )
                self.apply_to_layer_checkbox.setChecked(False)
                self._update_active_layer_status()
                return
            
            if active_layer < 0 or active_layer >= len(tracks):
                QMessageBox.warning(
                    self,
                    "Invalid Layer",
                    f"Active layer index {active_layer} is out of bounds (0-{len(tracks)-1}). "
                    "Please select a valid layer. The checkbox has been unchecked."
                )
                self.apply_to_layer_checkbox.setChecked(False)
                self._update_active_layer_status()
                return
        
        # Update status label
        self._update_active_layer_status()
    
    def _update_active_layer_status(self):
        """Update the active layer status label with current layer information."""
        if not hasattr(self, 'active_layer_status_label'):
            return
        
        # Check if checkbox is checked
        if not hasattr(self, 'apply_to_layer_checkbox') or not self.apply_to_layer_checkbox.isChecked():
            self.active_layer_status_label.setText("")
            return
        
        # Validate layer panel exists
        if not hasattr(self, 'layer_panel') or not self.layer_panel:
            self.active_layer_status_label.setText("⚠ Layer panel not available")
            return
        
        # Get active layer info
        tracks = self.layer_manager.get_layer_tracks()
        active_layer = self.layer_panel.get_active_layer_index()
        
        if not tracks:
            self.active_layer_status_label.setText("⚠ No layers exist")
            return
        
        if active_layer < 0 or active_layer >= len(tracks):
            self.active_layer_status_label.setText(f"⚠ Invalid layer index: {active_layer}")
            return
        
        # Valid layer - show layer name and info
        track = tracks[active_layer]
        frame_count = track.get_frame_count()
        self.active_layer_status_label.setText(
            f"Active Layer: <b>{track.name}</b> (Index: {active_layer}, Frames: {frame_count})"
        )
    
    def _on_cancel_effect_preview(self):
        """Cancel effect preview and restore original pattern."""
        effect_type = self.effect_type_combo.currentText()
        
        # Restore pattern from backup if available
        if hasattr(self, "_effects_preview_backup"):
            if isinstance(self._effects_preview_backup, Pattern):
                self._pattern = self._effects_preview_backup
                self._current_frame_index = 0
                self._load_current_frame_into_canvas()
                self._refresh_timeline()
                self._update_status_labels()
                # Clean up backup
                delattr(self, "_effects_preview_backup")
        
        # Clean up pending custom effect
        if hasattr(self, '_pending_custom_effect'):
            delattr(self, '_pending_custom_effect')
        
        # Hide preview status and disable buttons
        self.effect_preview_status.hide()
        self.apply_effect_btn.setEnabled(False)
        self.cancel_effect_btn.setEnabled(False)
        
        # Update status message
        if hasattr(self, "_set_canvas_status"):
            self._set_canvas_status("Preview cancelled. Original pattern restored.")

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
            self.cancel_effect_btn.setEnabled(True)
            self.finalize_automation_btn.setEnabled(True)
            
        elif effect_type == "Animated Text":
            if not hasattr(self, "text_input") or not self.text_input.text().strip():
                QMessageBox.information(self, "No Text", "Enter text in the Text Animation section first.")
                return
            
            text = self.text_input.text().strip()
            self.effect_preview_status.setText(f"Preview: Will generate animated text frames for '{text}'. Click 'Apply Effect' to generate.")
            self.effect_preview_status.show()
            self.apply_effect_btn.setEnabled(True)
            self.cancel_effect_btn.setEnabled(True)
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
                # Create backup before preview
                if not hasattr(self, "_effects_preview_backup"):
                    self._effects_preview_backup = copy.deepcopy(self._pattern)
                self._preview_custom_effect(effect_name, intensity)
                self._pending_custom_effect = (effect_name, intensity)
                self.effect_preview_status.setText(f"Preview: Custom effect '{effect_name}' (intensity: {intensity}%). Click 'Apply Effect' to commit.")
                self.effect_preview_status.show()
                self.apply_effect_btn.setEnabled(True)
                self.cancel_effect_btn.setEnabled(True)

    def _on_apply_effect(self):
        """Apply the effect to the pattern."""
        effect_type = self.effect_type_combo.currentText()
        
        if effect_type == "Automation Actions":
            self._apply_actions_to_frames(finalize=False)
            self.effect_preview_status.hide()
            self.apply_effect_btn.setEnabled(False)
            self.cancel_effect_btn.setEnabled(False)
        elif effect_type == "Animated Text":
            self._on_generate_text_animation()
            self.effect_preview_status.hide()
            self.apply_effect_btn.setEnabled(False)
            self.cancel_effect_btn.setEnabled(False)
        elif effect_type == "Custom Effect":
            # Apply custom effect that was previewed
            if hasattr(self, '_pending_custom_effect'):
                effect_name, intensity = self._pending_custom_effect
                self._apply_custom_effect(effect_name, intensity)
                delattr(self, '_pending_custom_effect')
                self.effect_preview_status.hide()
                self.apply_effect_btn.setEnabled(False)
                self.cancel_effect_btn.setEnabled(False)
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
        
        # Debug: Log frame range being processed
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Applying effect '{effect.name}' to frames {start+1}-{end+1} (indices {start}-{end}, total: {len(frame_indices)} frames)")

        before_states: Dict[int, List[Tuple[int, int, int]]] = {
            idx: list(self._pattern.frames[idx].pixels)
            for idx in frame_indices
        }

        # Add progress callback for effect application
        if len(frame_indices) > 10:
            from PySide6.QtWidgets import QProgressDialog
            progress = QProgressDialog(f"Applying effect to {len(frame_indices)} frames...", "Cancel", 0, len(frame_indices), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            def progress_callback(completed: int, total: int):
                progress.setValue(completed)
                QApplication.processEvents()
                return not progress.wasCanceled()
            
            apply_effect_to_frames(self._pattern, effect, frame_indices, intensity, progress_callback=progress_callback)
            progress.close()
        else:
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
            # NOTE: Do NOT sync_frame_from_layers() here - composite is derived via render_frame()
            # Only sync when explicitly needed (export, preview generation)
            # Ensure frame manager is updated after effects
            if hasattr(self, 'frame_manager') and self.frame_manager:
                self.frame_manager.set_pattern(self._pattern)
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
        self._apply_button_icon(remove_btn, "delete", tooltip="Remove selected action")
        button_row.addWidget(remove_btn)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_actions)
        self._apply_button_icon(clear_btn, "delete", tooltip="Clear all actions")
        button_row.addWidget(clear_btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.apply_actions_btn = QPushButton("▶ Apply Actions")
        self.apply_actions_btn.clicked.connect(lambda: self._apply_actions_to_frames(finalize=False))
        self._apply_button_icon(self.apply_actions_btn, "play", tooltip="Apply actions to frames")
        self.apply_actions_btn.setEnabled(False)
        layout.addWidget(self.apply_actions_btn)

        self.finalize_actions_btn = QPushButton("✓ Finalize Playlist")
        self.finalize_actions_btn.setToolTip("Commit actions to frames, clear the queue, and lock in timing")
        self.finalize_actions_btn.clicked.connect(lambda: self._apply_actions_to_frames(finalize=True))
        self._apply_button_icon(self.finalize_actions_btn, "automation", tooltip="Commit actions to frames, clear the queue, and lock in timing")
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
        
        export_sprite_btn = QPushButton("🖼️ Export Sprite Sheet")
        export_sprite_btn.setToolTip("Export all frames as PNG sprite sheet")
        export_sprite_btn.clicked.connect(self._on_export_sprite_sheet)
        export_image_row.addWidget(export_sprite_btn)
        
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

        # Validate file before processing
        import os
        from pathlib import Path
        
        # Check file exists
        if not os.path.exists(filepath):
            QMessageBox.critical(
                self,
                "File Not Found",
                f"The file does not exist:\n{filepath}\n\nPlease check the file path and try again."
            )
            return
        
        # Check file is readable
        if not os.access(filepath, os.R_OK):
            QMessageBox.critical(
                self,
                "Permission Denied",
                f"Cannot read file:\n{filepath}\n\nPlease check file permissions."
            )
            return
        
        # Check file size
        try:
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                QMessageBox.critical(
                    self,
                    "Empty File",
                    f"The file is empty:\n{filepath}\n\nPlease select a valid image file."
                )
                return
            
            # Warn if file is very large (>100MB)
            if file_size > 100 * 1024 * 1024:
                reply = QMessageBox.question(
                    self,
                    "Large File Warning",
                    f"This file is very large ({file_size / (1024*1024):.1f} MB).\n\n"
                    "Importing may take a long time and use significant memory.\n\n"
                    "Do you want to continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        except OSError as e:
            QMessageBox.critical(
                self,
                "File Access Error",
                f"Cannot access file:\n{filepath}\n\nError: {str(e)}"
            )
            return
        
        # Validate file format
        file_ext = Path(filepath).suffix.lower()
        supported_formats = [f".{fmt.lower()}" for fmt in ImageImporter.get_supported_formats()]
        if file_ext not in supported_formats:
            QMessageBox.critical(
                self,
                "Unsupported Format",
                f"Unsupported file format: {file_ext}\n\n"
                f"Supported formats: {', '.join([fmt.replace('.', '').upper() for fmt in supported_formats])}\n\n"
                "Please select a supported image file."
            )
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
            
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "File Not Found",
                f"The image file was not found:\n{filepath}\n\nPlease check the file path and try again."
            )
        except PermissionError:
            QMessageBox.critical(
                self,
                "Permission Denied",
                f"Cannot read the image file:\n{filepath}\n\nPlease check file permissions."
            )
        except OSError as e:
            error_msg = str(e).lower()
            if "cannot identify" in error_msg or "not a valid" in error_msg:
                QMessageBox.critical(
                    self,
                    "Invalid File Format",
                    f"The file is not a valid image:\n{filepath}\n\n"
                    "The file may be corrupted or in an unsupported format.\n\n"
                    "Supported formats: PNG, JPG, JPEG, BMP, GIF"
                )
            elif "truncated" in error_msg or "corrupt" in error_msg:
                QMessageBox.critical(
                    self,
                    "Corrupted File",
                    f"The image file appears to be corrupted:\n{filepath}\n\n"
                    "The file may be incomplete or damaged. Please try a different file."
                )
            else:
                QMessageBox.critical(
                    self,
                    "File Error",
                    f"Failed to read the image file:\n{filepath}\n\nError: {str(e)}\n\n"
                    "Please check that the file is a valid image and try again."
                )
        except ValueError as e:
            error_msg = str(e).lower()
            if "too large" in error_msg or "dimensions" in error_msg:
                QMessageBox.critical(
                    self,
                    "Image Too Large",
                    f"The image dimensions are too large:\n{filepath}\n\n"
                    f"Error: {str(e)}\n\n"
                    "Please use a smaller image or reduce the target matrix size."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Invalid Image Data",
                    f"The image file contains invalid data:\n{filepath}\n\n"
                    f"Error: {str(e)}\n\n"
                    "The file may be corrupted or in an unsupported format."
                )
        except Exception as e:
            error_msg = str(e)
            if "Failed to import" in error_msg:
                # Extract the underlying error from ImageImporter
                underlying_error = error_msg.replace("Failed to import image: ", "")
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Failed to import image:\n{filepath}\n\n{underlying_error}\n\n"
                    "The file may be corrupted, in an unsupported format, or too large."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Unexpected Error",
                    f"An unexpected error occurred while importing the image:\n{filepath}\n\n"
                    f"Error: {error_msg}\n\n"
                    "Please try again or report this issue if it persists."
                )
                import logging
                logging.getLogger(__name__).error("Unexpected error importing image", exc_info=True)

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
        time_display = datetime.now().strftime("%I:%M %p")
        target = autosave_dir / f"{slug}_{timestamp}.json"
        try:
            self._pattern.save_to_file(str(target))
            # Update memory status label
            if hasattr(self, "memory_status_label"):
                self.memory_status_label.setText(f"Autosaved at {time_display}")
                self.memory_status_label.setStyleSheet("color: #4CAF50;")
            # Show subtle status bar notification
            if hasattr(self, "_set_canvas_status"):
                self._set_canvas_status(f"Autosaved at {time_display} → {target.name}")
            # Clear the success message after 3 seconds
            if hasattr(self, "memory_status_label"):
                def clear_style():
                    try:
                        if hasattr(self, "memory_status_label") and self.memory_status_label:
                            self.memory_status_label.setStyleSheet("")
                    except (RuntimeError, AttributeError):
                        pass  # Widget was deleted
                QTimer.singleShot(3000, clear_style)
        except Exception as exc:
            # Show error notification
            if hasattr(self, "memory_status_label"):
                self.memory_status_label.setText(f"Autosave failed: {exc}")
                self.memory_status_label.setStyleSheet("color: #f44336;")
            if hasattr(self, "_set_canvas_status"):
                self._set_canvas_status(f"Autosave failed: {str(exc)}")
            # Show error message box for autosave failures
            QMessageBox.warning(
                self,
                "Autosave Failed",
                f"Autosave failed at {time_display}:\n\n{str(exc)}\n\n"
                f"Your work is not automatically saved. Please save manually."
            )

    def _on_preview_mode_changed(self, mode: str) -> None:
        preview_widget = getattr(self, "preview_widget", None)
        if preview_widget and hasattr(preview_widget, "set_display_layout"):
            layout_map = {
                "Matrix": "Matrix",
                "Radial": "Circle",
                "Matrix + Circle": "Matrix + Circle",
            }
            preview_widget.set_display_layout(layout_map.get(mode, "Matrix"))

    def _update_frame_range_spinboxes(self):
        """Update frame range spin boxes when frame count changes."""
        if not hasattr(self, "frame_start_spin") or not hasattr(self, "frame_end_spin"):
            return
        
        if not self._pattern:
            return
        
        frame_count = len(self._pattern.frames) if self._pattern.frames else 1
        
        # Update maximum values
        self.frame_start_spin.setMaximum(frame_count)
        self.frame_end_spin.setMaximum(frame_count)
        
        # Ensure values are within valid range
        if self.frame_start_spin.value() > frame_count:
            self.frame_start_spin.setValue(1)
        if self.frame_end_spin.value() > frame_count:
            self.frame_end_spin.setValue(frame_count)
        if self.frame_end_spin.value() < self.frame_start_spin.value():
            self.frame_end_spin.setValue(self.frame_start_spin.value())
    
    def _update_status_labels(self) -> None:
        if not hasattr(self, "matrix_status_label"):
            return
        width = getattr(self, "width_spin", None)
        height = getattr(self, "height_spin", None)
        # Safely get widget values - handle case where widget might be deleted
        try:
            width_value = width.value() if width and hasattr(width, 'value') else (self._pattern.metadata.width if self._pattern else 0)
            height_value = height.value() if height and hasattr(height, 'value') else (self._pattern.metadata.height if self._pattern else 0)
        except (RuntimeError, AttributeError):
            # Widget was deleted (e.g., during test cleanup)
            width_value = self._pattern.metadata.width if self._pattern else 0
            height_value = self._pattern.metadata.height if self._pattern else 0
        # Safely get colour mode - handle case where widget might be deleted
        colour_mode = getattr(self, "color_mode_combo", None)
        try:
            colour_text = colour_mode.currentText() if colour_mode and hasattr(colour_mode, 'currentText') else "RGB"
        except (RuntimeError, AttributeError):
            # Widget was deleted (e.g., during test cleanup)
            colour_text = "RGB"
        try:
            if hasattr(self, 'matrix_status_label') and self.matrix_status_label:
                self.matrix_status_label.setText(f"Matrix: {width_value} × {height_value} ({colour_text})")
        except (RuntimeError, AttributeError):
            # Widget was deleted, skip update
            pass

        total_frames = len(self._pattern.frames) if self._pattern and self._pattern.frames else 0
        current_index = self.frame_manager.current_index() if hasattr(self.frame_manager, "current_index") else 0
        frame_text = f"Frame: {current_index + 1}/{max(1, total_frames)} • {self._frame_duration_ms} ms"
        
        # Calculate and display memory usage
        if self._pattern:
            memory_bytes = self._calculate_pattern_size()
            memory_kb = memory_bytes / 1024.0
            memory_mb = memory_kb / 1024.0
            
            if memory_mb >= 1.0:
                memory_text = f"Memory: {memory_mb:.2f} MB"
            elif memory_kb >= 1.0:
                memory_text = f"Memory: {memory_kb:.2f} KB"
            else:
                memory_text = f"Memory: {memory_bytes} B"
            
            # Add warning if approaching limits
            try:
                if memory_bytes > 24576:  # >24KB (80% of 32KB)
                    memory_text += " ⚠"
                    self.memory_status_label.setStyleSheet("color: #ff4444;")
                elif memory_bytes > 16384:  # >16KB (50% of 32KB)
                    memory_text += " ⚡"
                    self.memory_status_label.setStyleSheet("color: #ffaa00;")
                else:
                    self.memory_status_label.setStyleSheet("")
            except Exception:
                pass  # Ignore errors in memory status update
            
            try:
                self.memory_status_label.setText(memory_text)
                self.memory_status_label.setToolTip(
                    f"Pattern size: {memory_bytes} bytes ({memory_kb:.2f} KB)\n"
                    f"Per frame: ~{memory_bytes // max(1, total_frames)} bytes\n"
                )
            except (RuntimeError, AttributeError):
                # Widget was deleted (e.g., during test cleanup)
                pass
        else:
            self.memory_status_label.setText("Memory: –")
            self.memory_status_label.setToolTip("No pattern loaded")
        
        # Update delete frame button state
        self._update_delete_frame_button_state()
        
        # Update undo/redo button states
        self._update_undo_redo_states()
        
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

    def _validate_before_export(self) -> tuple[bool, str]:
        """Validate pattern before export. Returns (is_valid, error_message)."""
        if not self._pattern:
            return False, "No pattern to export. Create or load a pattern first."
        
        if not hasattr(self._pattern, 'frames') or not self._pattern.frames:
            return False, "Pattern has no frames. Add frames before exporting."
        
        # Check frames have pixels
        has_pixels = False
        for frame in self._pattern.frames:
            if hasattr(frame, 'pixels') and frame.pixels and len(frame.pixels) > 0:
                has_pixels = True
                break
        
        if not has_pixels:
            return False, "All frames are empty. Add some content before exporting."
        
        # Validate dimensions
        if hasattr(self._pattern, 'metadata') and self._pattern.metadata:
            width = getattr(self._pattern.metadata, 'width', 0)
            height = getattr(self._pattern.metadata, 'height', 0)
            if width <= 0 or height <= 0:
                return False, f"Invalid pattern dimensions ({width}x{height}). Fix dimensions before exporting."
            
            # Validate circular layout mapping table if needed
            layout_type = getattr(self._pattern.metadata, 'layout_type', 'rectangular')
            if layout_type != "rectangular":
                from core.mapping.circular_mapper import CircularMapper
                if not getattr(self._pattern.metadata, 'circular_mapping_table', None):
                    # Try to regenerate mapping table
                    try:
                        CircularMapper.ensure_mapping_table(self._pattern.metadata)
                    except Exception as e:
                        return False, f"Circular layout mapping table is missing and could not be regenerated: {str(e)}"
                else:
                    # Validate existing mapping table
                    is_valid, error = CircularMapper.validate_mapping_table(self._pattern.metadata)
                    if not is_valid:
                        # Try to regenerate
                        try:
                            CircularMapper.ensure_mapping_table(self._pattern.metadata)
                        except Exception as e:
                            return False, f"Circular layout mapping table is invalid and could not be regenerated: {str(e)}"
        
        return True, ""

    def _on_open_export_dialog(self) -> None:
        """Open enhanced export dialog with format selection and metadata options."""
        # Validate before showing dialog
        is_valid, error_msg = self._validate_before_export()
        if not is_valid:
            QMessageBox.warning(self, "Cannot Export", error_msg)
            return
        
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
        # Get formats from ExportService
        formats = self.export_service.get_available_formats()
        format_extensions = {
            'bin': '*.bin',
            'hex': '*.hex',
            'dat': '*.dat',
            'leds': '*.leds',
            'json': '*.json',
            'csv': '*.csv',
            'txt': '*.txt',
            'ledproj': '*.ledproj',
            'h': '*.h',
            'wled': '*.json'  # WLED uses JSON format
        }
        for fmt in formats:
            ext = format_extensions.get(fmt, f"*.{fmt}")
            self.export_format_combo.addItem(f"{fmt.upper()} ({ext})")
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
        self.export_rgb_order_combo.addItems(["RGB", "BGR", "GRB", "BRG", "RBG", "GBR"])
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
        
        # Hardware Preview
        hardware_preview_group = QGroupBox("Hardware Preview")
        hardware_preview_layout = QVBoxLayout()
        hardware_preview_label = QLabel("This is how your pattern will look on hardware:")
        hardware_preview_layout.addWidget(hardware_preview_label)
        
        # Add LED simulator widget
        from ui.widgets.led_simulator import LEDSimulatorWidget
        self.export_hardware_preview = LEDSimulatorWidget()
        self.export_hardware_preview.setMinimumHeight(200)
        if self._pattern:
            self.export_hardware_preview.load_pattern(self._pattern)
        hardware_preview_layout.addWidget(self.export_hardware_preview)
        
        hardware_preview_group.setLayout(hardware_preview_layout)
        layout.addWidget(hardware_preview_group)

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
        
        # Update hardware preview when options change
        def _update_hardware_preview():
            if hasattr(self, "export_hardware_preview") and self._pattern:
                self.export_hardware_preview.load_pattern(self._pattern)
        
        self.export_format_combo.currentIndexChanged.connect(_update_hardware_preview)
        self.export_rgb_order_combo.currentTextChanged.connect(_update_hardware_preview)
        self.export_color_space_combo.currentTextChanged.connect(_update_hardware_preview)
        self.export_bytes_per_line_spin.valueChanged.connect(lambda _value: _update_preview())
        self.export_number_format_combo.currentTextChanged.connect(_update_preview)

        _update_preview()
        
        if dialog.exec() == QDialog.Accepted:
            selected_idx = self.export_format_combo.currentIndex()
            if selected_idx < len(formats):
                format_name = formats[selected_idx]
                extension = format_extensions.get(format_name, f"*.{format_name}")
                
                # Open save dialog
                filter_string = f"{format_name.upper()} ({extension})"
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
                        
                        # Update ExportService with options
                        self.export_service.set_export_options(options)
                        
                        # Validate export first
                        is_valid, error, preview = self.export_service.validate_export(self._pattern, format_name)
                        if not is_valid:
                            QMessageBox.warning(
                                self,
                                "Export Validation Failed",
                                f"Cannot export pattern in {format_name} format:\n\n{error or 'Unknown error'}"
                            )
                            return
                        
                        # Export using ExportService
                        output_path = self.export_service.export_pattern(
                            self._pattern,
                            filepath,
                            format_name,
                            generate_manifest=self.include_metadata_checkbox.isChecked()
                        )
                        
                        # Add timestamp if requested
                        if self.include_timestamp_checkbox.isChecked():
                            import datetime
                            timestamp = datetime.datetime.now().isoformat()
                            # For text formats, append comment
                            if format_name in ['leds', 'json', 'txt']:
                                with open(output_path, 'a', encoding='utf-8') as f:
                                    f.write(f"\n# Exported: {timestamp}\n")
                        
                        # Track file path and mark as saved
                        self._current_file = str(output_path)
                        self._mark_clean()
                        
                        QMessageBox.information(
                            self,
                            "Export Successful",
                            f"Pattern exported successfully to:\n{output_path}"
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
        # Eyedropper tool removed - color_picked signal no longer needed
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
        
        # Wrap timeline in scroll area for horizontal scrolling
        from PySide6.QtWidgets import QScrollArea
        timeline_scroll = QScrollArea()
        timeline_scroll.setWidget(self.timeline)
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        timeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        timeline_scroll.setFrameShape(QScrollArea.Shape.NoFrame)  # Remove border
        
        frame_layout.addWidget(timeline_scroll, stretch=1)

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
        # Theme selector removed - only dark theme available
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
        # Only dark theme is available
        return "dark"
        for candidate in candidates:
            if isinstance(candidate, str):
                normalized = candidate.strip().lower()
                if normalized in self.THEME_DEFINITIONS:
                    return normalized
        return self.DEFAULT_THEME

    def _on_theme_changed(self, text: str):
        # Theme changing disabled - only dark theme available
        # Keep method for compatibility but do nothing
        pass

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

        # Theme combo removed - only dark theme available

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
            # Use PatternService to create pattern
            pattern = self.pattern_service.create_pattern(
                name="New Design",
                width=width,
                height=height
            )
            # Store in repository and sync legacy reference
            self.repository.set_current_pattern(pattern)
            self._pattern = pattern  # Legacy reference for backward compatibility
            # Flag pattern as Design Order (unwrapped) so Preview Tab doesn't scramble it
            if not hasattr(self._pattern.metadata, 'already_unwrapped'):
                self._pattern.metadata.already_unwrapped = True
            
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

    def _create_blank_frame(self, width: int, height: int, default_color: tuple = (0, 0, 0)) -> Frame:
        pixels = [default_color] * (width * height)
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
            error_msg = f"load_pattern expects Pattern object, got {type(pattern).__name__}"
            QMessageBox.critical(
                self,
                "Invalid Pattern",
                f"Invalid pattern object provided:\n{error_msg}"
            )
            return
        
        # Auto-create a blank frame if pattern has no frames
        if not hasattr(pattern, 'frames') or not pattern.frames:
            # Create a blank frame with correct dimensions
            width = pattern.metadata.width if pattern.metadata else 16
            height = pattern.metadata.height if pattern.metadata else 16
            pixel_count = width * height
            blank_frame = Frame(
                pixels=[(0, 0, 0)] * pixel_count,
                duration_ms=100
            )
            pattern.frames = [blank_frame]
            # Inform user that a blank frame was created
            QMessageBox.information(
                self,
                "Empty Pattern",
                f"Pattern had no frames. Created a blank frame ({width}x{height})."
            )
        
        # Validate dimensions
        if hasattr(pattern, 'metadata') and pattern.metadata:
            width = getattr(pattern.metadata, 'width', 0)
            height = getattr(pattern.metadata, 'height', 0)
            if width <= 0 or height <= 0:
                QMessageBox.warning(
                    self,
                    "Invalid Dimensions",
                    f"Pattern has invalid dimensions ({width}x{height}).\n\n"
                    "The pattern may not display correctly. You can fix dimensions using Tools > Force Dimensions."
                )
                # Still allow loading, user can fix dimensions later
        
        self._suspend_timeline_refresh = True
        try:
            try:
                pattern_copy = Pattern.from_dict(pattern.to_dict()) if hasattr(pattern, "to_dict") else pattern
            except Exception:
                pattern_copy = pattern

            # Validate pattern_copy is Pattern object before assignment
            if not isinstance(pattern_copy, Pattern):
                raise TypeError(f"Pattern copy is not a Pattern object, got {type(pattern_copy).__name__}")
            
            # Store in repository and sync legacy reference
            self.repository.set_current_pattern(pattern_copy, file_path)
            self._pattern = pattern_copy  # Legacy reference for backward compatibility
            # Flag pattern as Design Order (unwrapped) so Preview Tab doesn't scramble it
            if not hasattr(self._pattern.metadata, 'already_unwrapped'):
                self._pattern.metadata.already_unwrapped = True
            
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
            
            # Validate and regenerate circular mapping table (always regenerate to pick up latest logic)
            if hasattr(pattern_copy.metadata, 'layout_type') and pattern_copy.metadata.layout_type != "rectangular":
                from core.mapping.circular_mapper import CircularMapper
                try:
                    # Always regenerate - don't check if exists, just regenerate
                    pattern_copy.metadata.circular_mapping_table = CircularMapper.generate_mapping_table(pattern_copy.metadata)
                    # Validate after generation
                    is_valid, error_msg = CircularMapper.validate_mapping_table(pattern_copy.metadata)
                    if not is_valid:
                        raise ValueError(f"Generated mapping table is invalid: {error_msg}")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to regenerate circular mapping table: {e}")
            
            # Update pixel mapping widget if it exists
            if hasattr(self, "pixel_mapping_widget") and self.pixel_mapping_widget:
                self.pixel_mapping_widget.set_matrix_size(width, height)
                # Restore pixel mapping config from pattern metadata if available
                if hasattr(pattern_copy.metadata, 'wiring_mode'):
                    config = {
                        "wiring_mode": getattr(pattern_copy.metadata, 'wiring_mode', 'Row-major'),
                        "data_in_corner": getattr(pattern_copy.metadata, 'data_in_corner', 'LT'),
                        "flip_x": getattr(pattern_copy.metadata, 'flip_x', False),
                        "flip_y": getattr(pattern_copy.metadata, 'flip_y', False),
                    }
                    self.pixel_mapping_widget.set_config(config)
            
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
            # Set pattern metadata for circular layout support
            # This enables the canvas overlay to show circular bounds and active cells
            if hasattr(self.canvas, 'set_pattern_metadata'):
                self.canvas.set_pattern_metadata(pattern_copy.metadata)
            
            # Update circular preview metadata
            # Always regenerate mapping table for circular layouts to ensure latest logic
            if hasattr(self, 'circular_preview'):
                if (hasattr(pattern_copy.metadata, 'layout_type') and 
                    pattern_copy.metadata.layout_type in ["circle", "ring", "radial", "multi_ring", "radial_rays"]):
                    from core.mapping.circular_mapper import CircularMapper
                    try:
                        # Force regeneration before setting metadata to ensure latest mapping logic
                        pattern_copy.metadata.circular_mapping_table = CircularMapper.generate_mapping_table(pattern_copy.metadata)
                    except Exception as e:
                        import logging
                        logging.warning(f"Failed to regenerate mapping table: {e}")
                self.circular_preview.set_pattern_metadata(pattern_copy.metadata)
                self._update_circular_preview()
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
            # Update history manager current frame
            self.history_manager.set_current_frame(self._current_frame_index)
            
            # Update frame range spin boxes
            if hasattr(self, "frame_start_spin") and hasattr(self, "frame_end_spin"):
                frame_count = len(self._pattern.frames) if self._pattern.frames else 1
                self.frame_start_spin.setMaximum(frame_count)
                self.frame_end_spin.setMaximum(frame_count)
                # Ensure values are within valid range
                if self.frame_start_spin.value() > frame_count:
                    self.frame_start_spin.setValue(1)
                if self.frame_end_spin.value() > frame_count:
                    self.frame_end_spin.setValue(frame_count)
                if self.frame_end_spin.value() < self.frame_start_spin.value():
                    self.frame_end_spin.setValue(self.frame_start_spin.value())
        finally:
            self._suspend_timeline_refresh = False
        self._mark_clean()
        self._update_single_color_ui_state()
        self._update_undo_redo_states()  # Update undo/redo states after loading pattern
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

        # Lock frame switching during painting operations
        self._frame_switch_locked = True

        # Update circular preview in real-time
        if hasattr(self, 'circular_preview') and hasattr(self.canvas, 'get_grid_data'):
            grid_data = self.canvas.get_grid_data()
            self.circular_preview.set_grid_data(grid_data)
        
        # Get brush propagation mode from combo box (with fallback for backward compatibility)
        propagation_mode = self.brush_propagation_combo.currentData() if hasattr(self, 'brush_propagation_combo') else "current"
        apply_to_all = propagation_mode == "all"
        apply_to_first = propagation_mode == "first"
        
        # Save state before first pixel change in a paint operation
        if apply_to_all:
            # For broadcast mode, save state of all frames
            if self._pending_broadcast_states is None:
                self._pending_broadcast_states = {}
                for idx in range(len(self._pattern.frames)):
                    frame = self._pattern.frames[idx]
                    self._pending_broadcast_states[idx] = list(frame.pixels)
        elif apply_to_first:
            # For "first frame only" mode, save state of first frame
            if self._pending_broadcast_states is None:
                self._pending_broadcast_states = {}
                if self._pattern.frames:
                    frame = self._pattern.frames[0]
                    self._pending_broadcast_states[0] = list(frame.pixels)
        else:
            # For single frame mode, save state of current frame only
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
                
                # Prevent painting on hidden layers
                if not layer_visible:
                    # Show dialog asking to show layer
                    reply = QMessageBox.question(
                        self,
                        "Cannot Paint on Hidden Layer",
                        f"⚠️ You are trying to paint on layer '{layer_name}' which is currently hidden.\n\n"
                        "Would you like to show this layer to continue painting?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Show the layer
                        self.layer_manager.set_layer_visible(self._current_frame_index, active_layer, True)
                        if hasattr(self, "layer_panel"):
                            self.layer_panel.refresh()
                    else:
                        # User cancelled - don't paint
                        return
                    
                    # Hide banner if it was showing
                    if hasattr(self, '_hidden_layer_banner') and self._hidden_layer_banner:
                        self._hidden_layer_banner.setVisible(False)
                
                # Prevent painting on locked layers
                if self.layer_manager.is_layer_locked(self._current_frame_index, active_layer):
                    QMessageBox.warning(
                        self,
                        "Cannot Paint on Locked Layer",
                        f"⚠️ Layer '{layer_name}' is locked and cannot be edited.\n\n"
                        "Unlock the layer to continue painting."
                    )
                    return
                
                if layer_visible:
                    # Hide banner if painting on visible layer
                    if hasattr(self, '_hidden_layer_banner') and self._hidden_layer_banner:
                        self._hidden_layer_banner.setVisible(False)
        
        target_frames = [self._current_frame_index]
        if apply_to_all:
            target_frames = list(range(len(self._pattern.frames)))
        elif apply_to_first:
            target_frames = [0]  # Apply to first frame only

        # Track that we're painting
        self._is_painting = True
        
        # Apply pixel updates (but defer sync for batch optimization)
        frames_to_sync = set()
        for frame_index in target_frames:
            self.layer_manager.apply_pixel(frame_index, x, y, color, width, height, active_layer)
            # Don't sync immediately - batch sync at end of paint operation
            frames_to_sync.add(frame_index)
        
        # Store frames that need syncing (will be synced on paint finish)
        if not hasattr(self, '_frames_to_sync'):
            self._frames_to_sync = set()
        self._frames_to_sync.update(frames_to_sync)
        
        # Clear thumbnail cache when pixels change
        if hasattr(self, "layer_panel"):
            self.layer_panel.clear_thumbnail_cache()
        
        self.pattern_modified.emit()
        self._maybe_autosync_preview()
        self._update_status_labels()

    def _commit_paint_operation(self):
        """Commit a paint operation to history."""
        # NOTE: Do NOT sync_frame_from_layers() here - composite is derived via render_frame()
        # Only sync when explicitly needed (export, preview generation)
        # Clear frames to sync list (no longer needed)
        if hasattr(self, '_frames_to_sync') and self._frames_to_sync:
            self._frames_to_sync.clear()

        self._is_painting = False
        
        # Unlock frame switching after paint operation completes
        self._frame_switch_locked = False
        
        # Update circular preview after paint operation
        self._update_circular_preview()
        
        if not self._pattern or not self._pattern.frames:
            self._pending_paint_state = None
            self._pending_broadcast_states = None
            return
        
        # Check if this was a broadcast operation
        is_broadcast = (self._pending_broadcast_states is not None)
        
        if is_broadcast:
            # Commit broadcast operation - save state for all affected frames
            if not self._pending_broadcast_states:
                self._pending_broadcast_states = None
                return
            
            # Check if any frames actually changed
            frames_changed = False
            for frame_index, old_pixels in self._pending_broadcast_states.items():
                if frame_index < len(self._pattern.frames):
                    frame = self._pattern.frames[frame_index]
                    new_pixels = list(frame.pixels)
                    if new_pixels != old_pixels:
                        frames_changed = True
                        # Create undo command for this frame
                        command = FrameStateCommand(
                            frame_index,
                            old_pixels,
                            new_pixels,
                            f"Paint pixels (broadcast to frame {frame_index + 1})"
                        )
                        self.history_manager.push_command(command, frame_index)
            
            # Update undo/redo states after broadcast operation
            if frames_changed:
                self._update_undo_redo_states()
            
            if frames_changed:
                # Show notification that broadcast undo is available
                if hasattr(self, 'canvas_status_label') and self.canvas_status_label:
                    self.canvas_status_label.setText("Broadcast paint applied to all frames. Use Undo to revert.")
                    # Reset after 3 seconds
                    def safe_update():
                        try:
                            self._update_status_labels()
                        except (RuntimeError, AttributeError):
                            pass  # Widget was deleted
                    QTimer.singleShot(3000, safe_update)
            
            self._pending_broadcast_states = None
        else:
            # Commit single frame operation
            if self._pending_paint_state is None:
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
            self._update_undo_redo_states()  # Update button states after paint operation
        
        self._pending_paint_state = None

    def _update_undo_redo_states(self):
        """Update undo/redo button states based on history availability."""
        if not self._pattern or not self._pattern.frames:
            # Disable buttons if no pattern
            if hasattr(self, 'canvas_undo_btn') and self.canvas_undo_btn:
                self.canvas_undo_btn.setEnabled(False)
                self.canvas_undo_btn.setToolTip("Nothing to undo")
            if hasattr(self, 'canvas_redo_btn') and self.canvas_redo_btn:
                self.canvas_redo_btn.setEnabled(False)
                self.canvas_redo_btn.setToolTip("Nothing to redo")
            return
        
        # Check undo availability
        can_undo = self.history_manager.can_undo(self._current_frame_index)
        if hasattr(self, 'canvas_undo_btn') and self.canvas_undo_btn:
            self.canvas_undo_btn.setEnabled(can_undo)
            if can_undo:
                # Get history depth for tooltip
                undo_count = len(self.history_manager._history[self._current_frame_index]) if self._current_frame_index < len(self.history_manager._history) else 0
                self.canvas_undo_btn.setToolTip(f"Undo (Ctrl+Z) - {undo_count} action(s) available")
            else:
                self.canvas_undo_btn.setToolTip("Nothing to undo")
        
        # Check redo availability
        can_redo = self.history_manager.can_redo(self._current_frame_index)
        if hasattr(self, 'canvas_redo_btn') and self.canvas_redo_btn:
            self.canvas_redo_btn.setEnabled(can_redo)
            if can_redo:
                # Get redo depth for tooltip
                redo_count = len(self.history_manager._redo_stacks[self._current_frame_index]) if self._current_frame_index < len(self.history_manager._redo_stacks) else 0
                self.canvas_redo_btn.setToolTip(f"Redo (Ctrl+Y) - {redo_count} action(s) available")
            else:
                self.canvas_redo_btn.setToolTip("Nothing to redo")

    def _on_undo(self):
        """Handle undo action."""
        if not self._pattern or not self._pattern.frames:
            return
        
        if not self.history_manager.can_undo(self._current_frame_index):
            # Show feedback when nothing to undo
            if hasattr(self, 'canvas_status_label') and self.canvas_status_label:
                self.canvas_status_label.setText("Nothing to undo")
                # Use a closure that checks if widget still exists
                def safe_update():
                    try:
                        if hasattr(self, '_update_status_labels'):
                            self._update_status_labels()
                    except (RuntimeError, AttributeError):
                        pass  # Widget was deleted, ignore
                QTimer.singleShot(2000, safe_update)
            return
        
        command = self.history_manager.undo(self._current_frame_index)
        if command:
            frame = self._pattern.frames[self._current_frame_index]
            frame.pixels = command.undo()
            self._load_current_frame_into_canvas()
            # Don't emit pattern_modified for undo/redo - these are restoring previous states,
            # not creating new modifications. This prevents marking pattern as dirty when
            # user is just exploring history.
            # UI updates still happen via _load_current_frame_into_canvas and other refresh methods
            self._maybe_autosync_preview()
            self._sync_detached_preview()  # Sync detached preview without marking as dirty
            self._update_status_labels()
            self._update_undo_redo_states()  # Update button states after undo

    def _on_redo(self):
        """Handle redo action."""
        if not self._pattern or not self._pattern.frames:
            return
        
        if not self.history_manager.can_redo(self._current_frame_index):
            # Show feedback when nothing to redo
            if hasattr(self, 'canvas_status_label') and self.canvas_status_label:
                self.canvas_status_label.setText("Nothing to redo")
                def safe_update():
                    try:
                        self._update_status_labels()
                    except (RuntimeError, AttributeError):
                        pass  # Widget was deleted
                QTimer.singleShot(2000, safe_update)
            return
        
        command = self.history_manager.redo(self._current_frame_index)
        if command:
            frame = self._pattern.frames[self._current_frame_index]
            frame.pixels = command.execute()
            self._load_current_frame_into_canvas()
            # Don't emit pattern_modified for undo/redo - these are restoring previous states,
            # not creating new modifications. This prevents marking pattern as dirty when
            # user is just exploring history.
            # UI updates still happen via _load_current_frame_into_canvas and other refresh methods
            self._maybe_autosync_preview()
            self._sync_detached_preview()  # Sync detached preview without marking as dirty
            self._update_status_labels()
            self._update_undo_redo_states()  # Update button states after redo

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Quick action shortcuts
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_D:  # Ctrl+D: Duplicate frame
                self._on_duplicate_frame()
                event.accept()
                return
            # Eyedropper tool removed
            elif event.key() == Qt.Key_N:  # Ctrl+N: Invert colors (moved from Ctrl+I)
                self._on_invert_frame()
                event.accept()
                return
            elif event.key() == Qt.Key_H:  # Ctrl+H: Flip horizontal
                self._on_flip_horizontal()
                event.accept()
                return
            elif event.key() == Qt.Key_V:  # Ctrl+V: Flip vertical
                self._on_flip_vertical()
                event.accept()
                return
            elif event.key() == Qt.Key_0:  # Ctrl+0: Reset zoom (handled by canvas)
                if hasattr(self, "canvas"):
                    # Canvas will handle this
                    pass
            elif event.key() == Qt.Key_1:  # Ctrl+1: Fit to window (handled by canvas)
                if hasattr(self, "canvas"):
                    # Canvas will handle this
                    pass
        
        # Delete key: Clear selected pixels or frame
        if event.key() == Qt.Key_Delete:
            # Check if canvas has selection, otherwise clear frame
            self._on_clear_frame()
            event.accept()
            return
        
        # E key: Eyedropper tool removed
        
        # Space: Play/pause
        if event.key() == Qt.Key_Space:
            if hasattr(self, "_playback_timer") and self._playback_timer.isActive():
                self._on_transport_pause()
            else:
                self._on_transport_play()
            event.accept()
            return
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self._on_undo()
                event.accept()
                return
            elif event.key() == Qt.Key_Y:
                self._on_redo()
                event.accept()
                return
            elif event.key() == Qt.Key_R:
                # Handle Ctrl+R to restore LMS preview
                if self._lms_preview_snapshot is not None:
                    self._on_lms_exit_preview()
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

    def _on_quick_matrix_clicked(self, width: int, height: int):
        """Handle quick matrix size button click."""
        if not hasattr(self, "width_spin") or not hasattr(self, "height_spin"):
            # If spinboxes don't exist yet, create a new pattern with the specified size
            if not self._confirm_discard_changes():
                return
            blank_frame = self._create_blank_frame(width, height)
            metadata = PatternMetadata(width=width, height=height)
            pattern = Pattern(name="New Design", metadata=metadata, frames=[blank_frame])
            self.load_pattern(pattern)
            return
        
        # Update existing spinboxes
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        
        # Reset preset combo to "Custom"
        if hasattr(self, "matrix_preset_combo"):
            self.matrix_preset_combo.blockSignals(True)
            self.matrix_preset_combo.setCurrentIndex(0)
            self.matrix_preset_combo.blockSignals(False)
        
        self._on_matrix_dimension_changed()

    def _on_custom_matrix_clicked(self):
        """Open matrix configuration dialog or scroll to matrix config panel."""
        # Scroll to matrix configuration group if it exists in toolbox
        if hasattr(self, "toolbox_container"):
            # Try to find and show the matrix configuration group
            # This is a simple implementation - could be enhanced to scroll to the panel
            QMessageBox.information(
                self,
                "Matrix Configuration",
                "Use the Matrix & Colour Configuration panel in the toolbox to set custom dimensions."
            )

    def _on_pixel_mapping_changed(self):
        """Handle pixel mapping configuration change."""
        if hasattr(self, "pixel_mapping_widget") and self._pattern:
            # Update pattern metadata with mapping configuration
            config = self.pixel_mapping_widget.get_config()
            if hasattr(self._pattern.metadata, "wiring_mode"):
                self._pattern.metadata.wiring_mode = config.get("wiring_mode", "Row-major")
            if hasattr(self._pattern.metadata, "data_in_corner"):
                self._pattern.metadata.data_in_corner = config.get("data_in_corner", "LT")
            if hasattr(self._pattern.metadata, "flip_x"):
                self._pattern.metadata.flip_x = config.get("flip_x", False)
            if hasattr(self._pattern.metadata, "flip_y"):
                self._pattern.metadata.flip_y = config.get("flip_y", False)
            
            self.pattern_modified.emit()
    
    def _on_led_brightness_changed(self, value: int):
        """Handle LED brightness change - refresh canvas if preview mode is on."""
        if hasattr(self, "led_color_panel") and self.led_color_panel and self.led_color_panel.is_preview_mode():
            self._load_current_frame_into_canvas()

    def _on_led_gamma_changed(self, gamma: float):
        """Handle LED gamma change - refresh canvas if preview mode is on."""
        if hasattr(self, "led_color_panel") and self.led_color_panel and self.led_color_panel.is_preview_mode():
            self._load_current_frame_into_canvas()

    def _on_led_palette_color_selected(self, color: Tuple[int, int, int]):
        """Handle LED-safe palette color selection - set as current color."""
        self._current_color = color
        self._sync_channel_controls(self._current_color)
        if hasattr(self, "canvas"):
            self.canvas.set_current_color(self._current_color)

    def _on_led_temp_changed(self, temp: float):
        """Handle LED color temperature change - refresh canvas if preview mode is on."""
        if hasattr(self, "led_color_panel") and self.led_color_panel and self.led_color_panel.is_preview_mode():
            self._load_current_frame_into_canvas()

    def _on_led_preview_mode_changed(self, enabled: bool):
        """Handle LED preview mode toggle - refresh canvas to show/hide LED transforms."""
        self._load_current_frame_into_canvas()

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
        
        # Update pixel mapping widget if it exists
        if hasattr(self, "pixel_mapping_widget") and self.pixel_mapping_widget:
            self.pixel_mapping_widget.set_matrix_size(width, height)
        
        # Update canvas size to match new dimensions
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
        # Prevent frame switching during locked operations (e.g., painting)
        if self._frame_switch_locked:
            return  # Ignore frame switch during locked operations
        
        self.frame_manager.select(index)
        self._current_frame_index = index
        self.history_manager.set_current_frame(index)
        
        # Update layer panel
        if hasattr(self, "layer_panel"):
            self.layer_panel.set_frame_index(index)
        
        self._update_status_labels()
        self._update_undo_redo_states()  # Update undo/redo states when frame changes

    # Layer sync warning and manual sync removed - syncing is now automatic
    # With the new architecture, composite pixels are derived via render_frame(),
    # so manual syncing is no longer needed

    def _on_add_frame(self):
        """Add a new blank frame after the current frame."""
        self._log_click("Add Frame", {
            "before_frames": len(self._pattern.frames) if self._pattern else 0,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        
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
        self._log_click("Add Frame - Complete", {
            "after_frames": len(self._pattern.frames) if self._pattern else 0,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        self.pattern_modified.emit()
        self._update_status_labels()
        self._update_delete_frame_button_state()  # Update button state after adding frame
        self._maybe_autosync_preview()

    def _on_bulk_add_frames(self):
        """Add multiple blank frames at once."""
        self._log_click("Bulk Add Frames", {
            "before_frames": len(self._pattern.frames) if self._pattern else 0,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        if not self._pattern:
            QMessageBox.information(self, "No Pattern", "Create a pattern first before adding frames.")
            return

        from PySide6.QtWidgets import QInputDialog
        
        # Get number of frames to add
        count, ok = QInputDialog.getInt(
            self,
            "Bulk Add Frames",
            "Number of frames to add:",
            10,  # default value
            1,   # minimum
            100, # maximum
            1    # step
        )
        
        if not ok or count <= 0:
            return

        # Validate frame count limit
        max_frames = 1000
        current_count = len(self._pattern.frames)
        if current_count + count > max_frames:
            QMessageBox.warning(
                self,
                "Frame Limit Exceeded",
                f"Cannot add {count} frames. Current: {current_count}, Maximum: {max_frames}.\n\n"
                f"Maximum additional frames: {max_frames - current_count}"
            )
            return

        duration_ms = self._frame_duration_ms if hasattr(self, "_frame_duration_ms") else 50
        
        # Add frames one by one after current position
        for i in range(count):
            self.frame_manager.add_blank_after_current(duration_ms)

        self._log_click("Bulk Add Frames - Complete", {
            "after_frames": len(self._pattern.frames) if self._pattern else 0,
            "frames_added": count,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        self.pattern_modified.emit()
        self._update_status_labels()
        self._update_delete_frame_button_state()
        self._maybe_autosync_preview()
        self._refresh_timeline()
        
        if hasattr(self, "_set_canvas_status"):
            self._set_canvas_status(f"Added {count} frame(s). Total: {len(self._pattern.frames)} frames")

    def _on_duplicate_frame(self):
        """Duplicate the current frame."""
        self._log_click("Duplicate Frame", {
            "before_frames": len(self._pattern.frames) if self._pattern else 0,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        
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
        
        # Show progress feedback for large patterns
        total_pixels = self._pattern.metadata.width * self._pattern.metadata.height
        if total_pixels > 500:  # Large pattern threshold
            # Show status message
            if hasattr(self, "_set_canvas_status"):
                self._set_canvas_status("Duplicating frame...")
            # Use QApplication.processEvents to update UI
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
        
        self.frame_manager.duplicate()
        self._log_click("Duplicate Frame - Complete", {
            "after_frames": len(self._pattern.frames) if self._pattern else 0,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        self.pattern_modified.emit()
        self._update_status_labels()
        self._update_delete_frame_button_state()  # Update button state after duplicating frame
        self._maybe_autosync_preview()
        
        # Show success message for large patterns
        if total_pixels > 500:
            if hasattr(self, "_set_canvas_status"):
                self._set_canvas_status(f"Frame duplicated successfully. Frame {self._current_frame_index + 1} of {len(self._pattern.frames)}")

    def _update_delete_frame_button_state(self):
        """Update delete frame button state based on frame count."""
        if not hasattr(self, 'delete_frame_btn') or not self.delete_frame_btn:
            return
        
        can_delete = (self._pattern is not None and self.state.frame_count() > 1)
        self.delete_frame_btn.setEnabled(can_delete)
        
        if can_delete:
            self.delete_frame_btn.setToolTip("Delete selected frame (Del)")
        else:
            self.delete_frame_btn.setToolTip("Cannot delete - at least one frame required. Add more frames first, then you can delete this one.")

    def _on_delete_frame(self):
        """Delete the current frame."""
        self._log_click("Delete Frame", {
            "before_frames": len(self._pattern.frames) if self._pattern else 0,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        if not self._pattern or self.state.frame_count() <= 1:
            QMessageBox.warning(
                self,
                "Cannot Delete Frame",
                "At least one frame is required.\n\n"
                "Add more frames first, then you can delete this one.\n\n"
                "Use 'Add Frame' or 'Duplicate Frame' to create additional frames."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Frame",
            f"Delete frame {self._current_frame_index + 1} of {self.state.frame_count()}?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.frame_manager.delete()
            self._log_click("Delete Frame - Complete", {
                "after_frames": len(self._pattern.frames) if self._pattern else 0,
                "current_frame": self._current_frame_index + 1 if self._pattern else 0
            })
            self.pattern_modified.emit()
            self._update_status_labels()
            self._update_delete_frame_button_state()  # Update button state after deletion
            self._maybe_autosync_preview()

    def _calculate_pattern_size(self) -> int:
        """Calculate total pattern size in bytes."""
        if not self._pattern:
            return 0
        
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        bytes_per_pixel = 3  # RGB
        bytes_per_frame = width * height * bytes_per_pixel
        
        total_frames = len(self._pattern.frames)
        total_bytes = bytes_per_frame * total_frames
        
        # Add metadata overhead (rough estimate)
        metadata_bytes = 100  # Pattern name, metadata, etc.
        
        return total_bytes + metadata_bytes

    def _on_simple_timeline_toggled(self, enabled: bool):
        """Handle simple timeline mode toggle."""
        if hasattr(self, "timeline"):
            # Simple mode: hide layer tracks if enabled
            if enabled:
                # Temporarily clear layer tracks
                self.timeline.set_layer_tracks([])
            else:
                # Restore layer tracks
                self._refresh_timeline()

    def _on_frames_selected(self, frame_indices: List[int]):
        """Handle multi-frame selection from timeline."""
        self._selected_frames = frame_indices
        # If only one frame selected, make it current
        if len(frame_indices) == 1:
            self.frame_manager.select(frame_indices[0])
        # Update frame range spinboxes to match selection
        if frame_indices:
            if hasattr(self, "frame_start_spin"):
                self.frame_start_spin.setValue(min(frame_indices) + 1)  # 1-indexed
            if hasattr(self, "frame_end_spin"):
                self.frame_end_spin.setValue(max(frame_indices) + 1)  # 1-indexed

    def _on_clear_frame(self):
        """Clear current frame - set all pixels to black."""
        # Use selected frames if available, otherwise current frame
        frames_to_clear = self._selected_frames if self._selected_frames else [self._current_frame_index]
        
        if not self._pattern:
            return
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Clear selected frames
        self.frame_manager.clear_selected_frames(frames_to_clear)
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        total_pixels = width * height
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Clear all pixels - update layers first, then frame
        if hasattr(self, "layer_manager") and self.layer_manager:
            # Clear all layer tracks
            tracks = self.layer_manager.get_layer_tracks()
            for track_idx in range(len(tracks)):
                self.layer_manager.replace_pixels(
                    self._current_frame_index,
                    [(0, 0, 0)] * total_pixels,
                    track_idx
                )
        else:
            # Fallback: update frame directly (legacy mode)
            frame.pixels = [(0, 0, 0)] * total_pixels
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()

    def _on_invert_frame(self):
        """Invert colors of selected frames."""
        # Use selected frames if available, otherwise current frame
        frames_to_invert = self._selected_frames if self._selected_frames else [self._current_frame_index]
        
        if not self._pattern:
            return
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Invert selected frames
        self.frame_manager.invert_selected_frames(frames_to_invert)
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()
        
        # Update layers if using layer manager
        if hasattr(self, "layer_manager"):
            layers = self.layer_manager.get_layers(self._current_frame_index)
            for layer in layers:
                layer_inverted = []
                for pixel in layer.pixels:
                    if isinstance(pixel, (list, tuple)) and len(pixel) >= 3:
                        r, g, b = pixel[0], pixel[1], pixel[2]
                        layer_inverted.append((255 - r, 255 - g, 255 - b))
                    else:
                        layer_inverted.append((255, 255, 255))
                layer.pixels = layer_inverted
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()

    def _on_select_range_clicked(self):
        """Select frames in the specified range."""
        if not self._pattern or not hasattr(self, "frame_start_spin") or not hasattr(self, "frame_end_spin"):
            return
        
        start = self.frame_start_spin.value() - 1  # Convert to 0-indexed
        end = self.frame_end_spin.value() - 1  # Convert to 0-indexed
        
        if start < 0 or end < 0 or start >= len(self._pattern.frames) or end >= len(self._pattern.frames):
            QMessageBox.warning(self, "Invalid Range", f"Frame range {start+1}-{end+1} is out of bounds (1-{len(self._pattern.frames)}).")
            return
        
        if start > end:
            start, end = end, start
        
        # Select range on timeline
        frame_indices = list(range(start, end + 1))
        self._selected_frames = frame_indices
        
        # Update timeline selection
        if hasattr(self, "timeline") and hasattr(self.timeline, "_selected_indices"):
            self.timeline._selected_indices = set(frame_indices)
            self.timeline.framesSelected.emit(frame_indices)
            self.timeline.update()
        
        self._refresh_timeline()
    
    def _on_select_all_frames_clicked(self):
        """Select all frames."""
        if not self._pattern:
            return
        
        frame_indices = list(range(len(self._pattern.frames)))
        self._selected_frames = frame_indices
        
        # Update spinboxes
        if hasattr(self, "frame_start_spin"):
            self.frame_start_spin.setValue(1)
        if hasattr(self, "frame_end_spin"):
            self.frame_end_spin.setValue(len(self._pattern.frames))
        
        # Update timeline selection
        if hasattr(self, "timeline") and hasattr(self.timeline, "_selected_indices"):
            self.timeline._selected_indices = set(frame_indices)
            self.timeline.framesSelected.emit(frame_indices)
            self.timeline.update()
        
        self._refresh_timeline()
    
    def _on_clear_range_clicked(self):
        """Clear all pixels in the selected frame range."""
        if not self._pattern or not hasattr(self, "frame_start_spin") or not hasattr(self, "frame_end_spin"):
            return
        
        start = self.frame_start_spin.value() - 1  # Convert to 0-indexed
        end = self.frame_end_spin.value() - 1  # Convert to 0-indexed
        
        if start < 0 or end < 0 or start >= len(self._pattern.frames) or end >= len(self._pattern.frames):
            QMessageBox.warning(self, "Invalid Range", f"Frame range {start+1}-{end+1} is out of bounds.")
            return
        
        if start > end:
            start, end = end, start
        
        frames_to_clear = list(range(start, end + 1))
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Clear frames
        self.frame_manager.clear_selected_frames(frames_to_clear)
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()
    
    def _on_invert_range_clicked(self):
        """Invert colors in the selected frame range."""
        if not self._pattern or not hasattr(self, "frame_start_spin") or not hasattr(self, "frame_end_spin"):
            return
        
        start = self.frame_start_spin.value() - 1  # Convert to 0-indexed
        end = self.frame_end_spin.value() - 1  # Convert to 0-indexed
        
        if start < 0 or end < 0 or start >= len(self._pattern.frames) or end >= len(self._pattern.frames):
            QMessageBox.warning(self, "Invalid Range", f"Frame range {start+1}-{end+1} is out of bounds.")
            return
        
        if start > end:
            start, end = end, start
        
        frames_to_invert = list(range(start, end + 1))
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Invert frames
        self.frame_manager.invert_selected_frames(frames_to_invert)
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()
    
    def _on_bulk_delete_frames(self):
        """Bulk delete frames using frame range spinboxes."""
        # Use the existing delete range functionality
        self._on_delete_range_clicked()

    def _on_delete_range_clicked(self):
        """Delete frames in the selected range."""
        if not self._pattern or not hasattr(self, "frame_start_spin") or not hasattr(self, "frame_end_spin"):
            return
        
        start = self.frame_start_spin.value() - 1  # Convert to 0-indexed
        end = self.frame_end_spin.value() - 1  # Convert to 0-indexed
        
        initial_frame_count = len(self._pattern.frames) if self._pattern else 0
        self._log_click("Delete Range", {
            "before_frames": initial_frame_count,
            "range": f"{start+1}-{end+1}" if start <= end else f"{end+1}-{start+1}",
            "frames_to_delete": abs(end - start) + 1
        })
        
        if start < 0 or end < 0 or start >= len(self._pattern.frames) or end >= len(self._pattern.frames):
            QMessageBox.warning(self, "Invalid Range", f"Frame range {start+1}-{end+1} is out of bounds.")
            return
        
        if start > end:
            start, end = end, start
        
        # Confirm deletion
        count = end - start + 1
        reply = QMessageBox.question(
            self,
            "Delete Frames",
            f"Delete {count} frame(s) ({start+1}-{end+1})? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        frames_to_delete = list(range(start, end + 1))
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Delete frames
        self.frame_manager.delete_selected_frames(frames_to_delete)
        
        # Clear selection
        self._selected_frames = []
        
        # Update current frame index
        if self._current_frame_index >= len(self._pattern.frames):
            self._current_frame_index = len(self._pattern.frames) - 1
        if self._current_frame_index < 0:
            self._current_frame_index = 0
        
        final_frame_count = len(self._pattern.frames) if self._pattern else 0
        self._log_click("Delete Range - Complete", {
            "after_frames": final_frame_count,
            "frames_deleted": initial_frame_count - final_frame_count,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()
    
    def _on_flip_horizontal(self):
        """Flip current frame horizontally."""
        if not self._pattern or self._current_frame_index >= len(self._pattern.frames):
            return
        
        frame = self._pattern.frames[self._current_frame_index]
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Flip horizontally
        flipped_pixels = []
        for y in range(height):
            for x in range(width):
                # Flip x coordinate
                flipped_x = width - 1 - x
                idx = y * width + flipped_x
                if idx < len(frame.pixels):
                    flipped_pixels.append(frame.pixels[idx])
        
        # Update layers if using layer manager
        if hasattr(self, "layer_manager") and self.layer_manager:
            tracks = self.layer_manager.get_layer_tracks()
            for track_idx in range(len(tracks)):
                track = tracks[track_idx]
                layer_frame = track.get_frame(self._current_frame_index)
                if layer_frame:
                    layer_pixels = layer_frame.pixels
                    layer_flipped = []
                    for y in range(height):
                        for x in range(width):
                            flipped_x = width - 1 - x
                            idx = y * width + flipped_x
                            if idx < len(layer_pixels):
                                layer_flipped.append(layer_pixels[idx])
                            else:
                                layer_flipped.append((0, 0, 0))
                    self.layer_manager.replace_pixels(
                        self._current_frame_index,
                        layer_flipped,
                        track_idx
                    )
        else:
            # Fallback: update frame directly (legacy mode)
            frame.pixels = flipped_pixels
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()

    def _on_flip_vertical(self):
        """Flip current frame vertically."""
        if not self._pattern or self._current_frame_index >= len(self._pattern.frames):
            return
        
        frame = self._pattern.frames[self._current_frame_index]
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Flip vertically
        flipped_pixels = []
        for y in range(height):
            flipped_y = height - 1 - y
            for x in range(width):
                idx = flipped_y * width + x
                if idx < len(frame.pixels):
                    flipped_pixels.append(frame.pixels[idx])
        
        # Update layers if using layer manager
        if hasattr(self, "layer_manager") and self.layer_manager:
            tracks = self.layer_manager.get_layer_tracks()
            for track_idx in range(len(tracks)):
                track = tracks[track_idx]
                layer_frame = track.get_frame(self._current_frame_index)
                if layer_frame:
                    layer_pixels = layer_frame.pixels
                    layer_flipped = []
                    for y in range(height):
                        flipped_y = height - 1 - y
                        for x in range(width):
                            idx = flipped_y * width + x
                            if idx < len(layer_pixels):
                                layer_flipped.append(layer_pixels[idx])
                            else:
                                layer_flipped.append((0, 0, 0))
                    self.layer_manager.replace_pixels(
                        self._current_frame_index,
                        layer_flipped,
                        track_idx
                    )
        else:
            # Fallback: update frame directly (legacy mode)
            frame.pixels = flipped_pixels
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()

    def _on_rotate_90(self):
        """Rotate current frame 90 degrees clockwise."""
        if not self._pattern or self._current_frame_index >= len(self._pattern.frames):
            return
        
        frame = self._pattern.frames[self._current_frame_index]
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        
        # Save state for undo
        if hasattr(self, "history_manager"):
            self.history_manager.save_state()
        
        # Rotate 90 degrees clockwise (transpose and reverse rows)
        rotated_pixels = []
        for x in range(width):
            for y in range(height - 1, -1, -1):  # Reverse y order
                idx = y * width + x
                if idx < len(frame.pixels):
                    rotated_pixels.append(frame.pixels[idx])
        
        # Update layers if using layer manager
        if hasattr(self, "layer_manager") and self.layer_manager:
            tracks = self.layer_manager.get_layer_tracks()
            for track_idx in range(len(tracks)):
                track = tracks[track_idx]
                layer_frame = track.get_frame(self._current_frame_index)
                if layer_frame:
                    layer_pixels = layer_frame.pixels
                    layer_rotated = []
                    for x in range(width):
                        for y in range(height - 1, -1, -1):
                            idx = y * width + x
                            if idx < len(layer_pixels):
                                layer_rotated.append(layer_pixels[idx])
                            else:
                                layer_rotated.append((0, 0, 0))
                    self.layer_manager.replace_pixels(
                        self._current_frame_index,
                        layer_rotated,
                        track_idx
                    )
        else:
            # Fallback: update frame directly (legacy mode)
            frame.pixels = rotated_pixels
        
        # Swap width and height in metadata (if square, no change needed)
        # Note: For non-square matrices, rotation changes dimensions
        # For simplicity, we'll keep the same dimensions and rotate in place
        
        self._load_current_frame_into_canvas()
        self.pattern_modified.emit()
        self._refresh_timeline()

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
        them in the pattern. If finalize=False:
        - Auto-detects when to generate frames vs apply to existing frames
        - Generates new frames incrementally for animation actions (scroll, rotate, etc.)
        - Applies to existing frames for static transformations
        """
        initial_frame_count = len(self._pattern.frames) if self._pattern else 0
        self._log_click("Apply Actions", {
            "finalize": finalize,
            "initial_frames": initial_frame_count,
            "current_frame": self._current_frame_index + 1 if self._pattern else 0
        })
        
        actions = self.automation_manager.actions()
        if not self._pattern or not actions:
            self._log_action("Apply Actions - No Actions", {"pattern_exists": self._pattern is not None, "actions_count": len(actions) if actions else 0})
            QMessageBox.information(self, "No Actions", "Add actions to the queue first.")
            return
        
        self._log_action("Apply Actions - Starting", {
            "action_count": len(actions),
            "action_types": [getattr(a, 'action_type', 'unknown') for a in actions],
            "finalize": finalize
        })

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

        # Auto-determine if we should generate frames or apply to existing frames
        # If no frames exist or actions would benefit from incremental generation, auto-generate
        should_generate_frames = False
        
        if not self._pattern.frames:
            # No frames exist - auto-generate
            should_generate_frames = True
        else:
            # Check if actions would benefit from frame generation (scroll, rotate, etc.)
            # Actions that create animation sequences benefit from incremental frame generation
            animation_actions = {"scroll", "rotate", "wipe", "reveal", "bounce", "radial", "colour_cycle"}
            for action in actions:
                action_type = getattr(action, 'action_type', '').lower() if hasattr(action, 'action_type') else ''
                if action_type in animation_actions:
                    should_generate_frames = True
                    break
            
            # Auto-detection: if actions benefit from incremental generation, generate frames
            # (Checkbox removed - always auto-detect)
        
        # Check if "Apply to Active Layer" is enabled (before frame generation)
        if hasattr(self, 'apply_to_layer_checkbox') and self.apply_to_layer_checkbox.isChecked():
            # Validate layer panel exists and is initialized
            if not hasattr(self, 'layer_panel') or not self.layer_panel:
                QMessageBox.warning(
                    self,
                    "Layer Panel Not Available",
                    "Layer panel is not initialized. Please ensure the design tools tab is fully loaded."
                )
                return
            
            # Get active layer index
            active_layer = self.layer_panel.get_active_layer_index()
            
            # Validate layer tracks exist
            tracks = self.layer_manager.get_layer_tracks()
            if not tracks:
                QMessageBox.warning(
                    self,
                    "No Layers",
                    "No layers exist. Please create at least one layer before applying automation to a layer."
                )
                return
            
            # Validate active layer index is within bounds
            if active_layer < 0 or active_layer >= len(tracks):
                QMessageBox.warning(
                    self,
                    "Invalid Layer",
                    f"Active layer index {active_layer} is out of bounds (0-{len(tracks)-1}).\n"
                    "Please select a valid layer in the layer panel."
                )
                return
            
            # Layer is valid, proceed with application
            try:
                # NEW: Attach automation actions to layer (render-time, non-destructive)
                from domain.automation.layer_action import LayerAction
                
                # Get frame range
                start_frame = max(0, self.frame_start_spin.value() - 1 if hasattr(self, "frame_start_spin") else 0)
                end_frame = min(len(self._pattern.frames) - 1, self.frame_end_spin.value() - 1 if hasattr(self, "frame_end_spin") else len(self._pattern.frames) - 1) if self._pattern.frames else 0
                
                # Convert DesignAction to LayerAction and attach to layer
                layer_actions = []
                for action in actions:
                    layer_action = self._convert_to_layer_action(action, start_frame, end_frame, finalized=finalize)
                    if layer_action:
                        layer_actions.append(layer_action)
                
                if layer_actions:
                    if finalize:
                        # Finalize: Bake into frames, then clear automation
                        self._bake_automation_to_layer(active_layer, layer_actions, start_frame, end_frame)
                        # Clear automation after baking
                        self.layer_manager.set_layer_automation(active_layer, [])
                    else:
                        # Non-finalized: Attach to layer for render-time evaluation
                        self.layer_manager.set_layer_automation(active_layer, layer_actions)
                    
                    track = tracks[active_layer]
                    action_text = "finalized and baked" if finalize else "attached (render-time)"
                    QMessageBox.information(
                        self,
                        "Automation Applied",
                        f"Applied {len(layer_actions)} automation action(s) to layer '{track.name}'.\n"
                        f"Actions are {action_text}."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "No Actions Converted",
                        "Could not convert actions to layer automation."
                    )
                
                self._load_current_frame_into_canvas()
                if hasattr(self, 'timeline'):
                    self._refresh_timeline()
                return
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Applying to Layer",
                    f"Failed to apply automation to layer:\n\n{str(e)}\n\nPlease check the layer and try again."
                )
                import logging
                logging.exception("Error applying automation to layer")
                return
        
        if should_generate_frames:
            # Auto-generate frames (automatic, no user dialog needed)
            self._generate_frames_with_actions(actions)
            return

        # Apply to existing frames in range
        # Note: At this point, frames must exist since should_generate_frames would be True if they didn't
        if not self._pattern.frames:
            QMessageBox.information(self, "No Frames", "Create frames before applying automation.")
            return

        # Get frame range with validation
        try:
            start = max(0, self.frame_start_spin.value() - 1 if hasattr(self, "frame_start_spin") else 0)
            end = min(len(self._pattern.frames) - 1, self.frame_end_spin.value() - 1 if hasattr(self, "frame_end_spin") else len(self._pattern.frames) - 1)
            
            # Enhanced validation
            if start < 0:
                start = 0
            if end >= len(self._pattern.frames):
                end = len(self._pattern.frames) - 1
            if end < 0:
                end = 0
            
            if start > end:
                QMessageBox.warning(
                    self,
                    "Invalid Range",
                    f"Frame range is invalid: Frame {start + 1} to Frame {end + 1}.\n"
                    f"Please select a valid frame range."
                )
                return

            frame_indices = list(range(start, end + 1))
            
            if not frame_indices:
                QMessageBox.warning(self, "No Frames Selected", "No frames in the selected range.")
                return

            # NEW: Apply automation to active layer instead of mutating frame.pixels directly
            # If no active layer, apply to layer 0 (default)
            active_layer = 0
            if hasattr(self, 'layer_panel') and self.layer_panel:
                active_layer = self.layer_panel.get_active_layer_index()
                if active_layer < 0:
                    active_layer = 0
            
            from domain.automation.layer_action import LayerAction
            
            # Convert DesignAction to LayerAction
            layer_actions = []
            for action in actions:
                layer_action = self._convert_to_layer_action(action, start, end, finalized=finalize)
                if layer_action:
                    layer_actions.append(layer_action)
            
            if layer_actions:
                if finalize:
                    # Finalize: Bake into frames
                    self._bake_automation_to_layer(active_layer, layer_actions, start, end)
                    # Clear automation after baking
                    self.layer_manager.set_layer_automation(active_layer, [])
                else:
                    # Non-finalized: Attach to layer for render-time evaluation
                    self.layer_manager.set_layer_automation(active_layer, layer_actions)
            
            # NOTE: Do NOT sync_frame_from_layers() here - composite is derived via render_frame()
            # Only sync when explicitly needed (export, preview generation)
            
            # Update UI and notify
            self._refresh_timeline()
            self._load_current_frame_into_canvas()
            self.pattern_modified.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Automation Error",
                f"An error occurred while applying automation actions:\n\n{str(e)}\n\nPlease check your pattern and try again."
            )
            import logging
            logging.exception("Error in _apply_actions_to_frames")
        
        final_frame_count = len(self._pattern.frames) if self._pattern else 0
        self._log_action("Apply Actions - Complete", {
            "initial_frames": initial_frame_count,
            "final_frames": final_frame_count,
            "frames_added": final_frame_count - initial_frame_count,
            "finalize": finalize
        })
        
        # Removed dialog - automation is now automatic and silent

    def _convert_to_layer_action(self, action, start_frame: int, end_frame: int, finalized: bool = False):
        """
        Convert a DesignAction to a LayerAction.
        
        Args:
            action: DesignAction object from automation queue
            start_frame: Start frame index for the action
            end_frame: End frame index for the action
            finalized: Whether the action should be marked as finalized
            
        Returns:
            LayerAction object or None if action cannot be converted
        """
        try:
            from domain.automation.layer_action import LayerAction
        except ImportError:
            return None
        
        if not hasattr(action, 'action_type'):
            return None
        
        action_type = action.action_type.lower()
        params = getattr(action, 'params', {}) or {}
        name = getattr(action, 'name', None) or f"{action_type.title()} Action"
        
        return LayerAction(
            type=action_type,
            start_frame=start_frame,
            end_frame=end_frame,
            params=params,
            finalized=finalized,
            name=name
        )
    
    def _bake_automation_to_layer(self, layer_index: int, layer_actions: List, start_frame: int, end_frame: int):
        """
        Bake automation actions into layer frames (finalize mode).
        
        This applies the automation transformations directly to the layer's frame pixels,
        making them permanent. After baking, the automation is cleared.
        
        Args:
            layer_index: Index of the layer track
            layer_actions: List of LayerAction objects to bake
            start_frame: Start frame index
            end_frame: End frame index
        """
        if not self._pattern or layer_index < 0:
            return
        
        tracks = self.layer_manager.get_layer_tracks()
        if layer_index >= len(tracks):
            return
        
        track = tracks[layer_index]
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        
        # Apply each action to each frame in range
        for frame_idx in range(start_frame, end_frame + 1):
            layer_frame = track.get_or_create_frame(frame_idx, width, height)
            pixels = list(layer_frame.pixels)
            
            # Apply all actions for this frame
            for action in layer_actions:
                if action.start_frame <= frame_idx <= action.end_frame:
                    step = action.get_step(frame_idx)
                    # Create a temporary DesignAction for transformation
                    from domain.actions import DesignAction
                    temp_action = DesignAction(
                        name=action.name or action.type,
                        action_type=action.type,
                        params=action.params
                    )
                    # Use existing _transform_pixels method with step-based frame_index
                    transformed = self._transform_pixels(pixels, temp_action, width, height, step)
                    if transformed:
                        pixels = transformed
            
            # Update layer frame with baked pixels
            layer_frame.pixels = pixels
        
        # Emit signal to update UI
        self.layer_manager.layers_changed.emit(-1)
    
    def _create_layer_animation_from_action(self, action) -> Optional[object]:
        """
        Convert an automation action to a layer animation (backward compatibility).
        
        Args:
            action: DesignAction object from automation queue
            
        Returns:
            LayerAnimation object or None if action cannot be converted
        """
        if not hasattr(action, 'action_type'):
            return None
        
        action_type = action.action_type.lower()
        params = getattr(action, 'params', {}) or {}
        
        try:
            if action_type == "scroll":
                # Convert scroll action to scroll animation
                direction = params.get("direction", "right").lower()
                speed = params.get("speed", 1.0)
                if isinstance(speed, (int, float)):
                    speed = float(speed)
                else:
                    speed = 1.0
                
                return create_scroll_animation(
                    direction=direction,
                    speed=speed,
                    start_frame=0,
                    end_frame=None  # All frames
                )
            
            elif action_type == "wipe":
                # Convert wipe to scroll animation (wipe is essentially a scroll with fade)
                mode = params.get("mode", "Left to Right").lower()
                speed = params.get("speed", 1.0)
                if isinstance(speed, (int, float)):
                    speed = float(speed)
                else:
                    speed = 1.0
                
                # Map wipe modes to scroll directions
                direction_map = {
                    "left to right": "right",
                    "right to left": "left",
                    "top to bottom": "down",
                    "bottom to top": "up",
                }
                direction = direction_map.get(mode, "right")
                
                return create_scroll_animation(
                    direction=direction,
                    speed=speed,
                    start_frame=0,
                    end_frame=None
                )
            
            elif action_type == "reveal":
                # Convert reveal to fade animation
                direction = params.get("direction", "left").lower()
                speed = params.get("speed", 1.0)
                if isinstance(speed, (int, float)):
                    speed = float(speed)
                else:
                    speed = 1.0
                
                # Reveal is essentially a fade in
                return create_fade_animation(
                    fade_in=True,
                    duration_frames=10,
                    start_frame=0
                )
            
            # Other action types don't have direct animation equivalents yet
            return None
            
        except Exception as e:
            import logging
            logging.exception(f"Error converting action {action_type} to animation")
            return None

    def _generate_frames_with_actions(self, actions):
        """Generate new frames by applying actions incrementally."""
        initial_frame_count = len(self._pattern.frames) if self._pattern else 0
        self._log_frame_generation("START", initial_frame_count, {
            "action_count": len(actions),
            "action_types": [getattr(a, 'action_type', 'unknown') for a in actions]
        })
        
        if not self._pattern:
            self._log_frame_generation("ERROR - No Pattern", 0)
            QMessageBox.warning(self, "No Pattern", "No pattern loaded.")
            return
        
        # If no frames exist, create a blank frame as source
        if not self._pattern.frames:
            expected_pixel_count = self._pattern.metadata.width * self._pattern.metadata.height
            blank_frame = Frame(
                pixels=[(0, 0, 0)] * expected_pixel_count,
                duration_ms=100
            )
            self._pattern.frames = [blank_frame]
            self._current_frame_index = 0
        
        # LMS-correct frame count calculation: UI-only suggestion, not semantic enforcement
        # LMS does NOT auto-truncate animations - frame count is user-specified or uses end_frame
        # This calculation is only a suggestion for UI purposes
        
        # Check if any action has an end_frame (for LayerActions)
        # For DesignActions in frame generation, we default to suggesting a count
        frame_count = 10  # Default minimum suggestion
        
        # Calculate suggested frame count based on action parameters (UI-only, not enforced)
        # User can override this or specify their own count
        max_frames_suggestion = 0
        
        for action in actions:
            params = action.params or {}
            action_type = getattr(action, 'action_type', '').lower()
            repeat = max(1, int(params.get("repeat", 1)))
            
            # UI-only suggestions (LMS doesn't enforce these limits)
            if action_type == "scroll":
                # Suggest frames based on scroll direction
                direction = params.get("direction", "Right").lower()
                if direction in ["left", "right"]:
                    frames_suggestion = self._pattern.metadata.width
                else:
                    frames_suggestion = self._pattern.metadata.height
                max_frames_suggestion = max(max_frames_suggestion, frames_suggestion * repeat)
            elif action_type == "rotate":
                # Suggest 4 frames for one full rotation cycle
                max_frames_suggestion = max(max_frames_suggestion, 4 * repeat)
            elif action_type in ["wipe", "reveal"]:
                # Suggest frames based on wipe/reveal direction
                direction = params.get("direction", "Left").lower() if action_type == "reveal" else params.get("mode", "Left to Right").lower()
                if "left" in direction or "right" in direction:
                    frames_suggestion = self._pattern.metadata.width
                else:
                    frames_suggestion = self._pattern.metadata.height
                max_frames_suggestion = max(max_frames_suggestion, frames_suggestion * repeat)
            else:
                # Other actions: suggest based on repeat count
                max_frames_suggestion = max(max_frames_suggestion, repeat * 5)
        
        # Use suggestion as default (can be overridden by user or action.end_frame)
        frame_count = max(1, max_frames_suggestion)
        
        # Get source frame (use first frame or current frame)
        if hasattr(self, 'source_button_group'):
            source_mode = self.source_button_group.checkedId()
            if source_mode == 0:  # Use first frame
                source_frame_idx = 0
            else:  # Use current frame
                source_frame_idx = self._current_frame_index
        else:
            # Default to first frame if button group doesn't exist
            source_frame_idx = 0
        
        if source_frame_idx >= len(self._pattern.frames):
            source_frame_idx = 0
        
        source_frame = self._pattern.frames[source_frame_idx]
        
        # Validate source frame
        expected_pixel_count = self._pattern.metadata.width * self._pattern.metadata.height
        if len(source_frame.pixels) != expected_pixel_count:
            QMessageBox.warning(
                self,
                "Source Frame Issue",
                f"Source frame has {len(source_frame.pixels)} pixels, expected {expected_pixel_count}.\n"
                f"This may cause issues with frame generation."
            )
            # Fix source frame if possible
            if len(source_frame.pixels) < expected_pixel_count:
                source_frame.pixels.extend([(0, 0, 0)] * (expected_pixel_count - len(source_frame.pixels)))
            else:
                source_frame.pixels = source_frame.pixels[:expected_pixel_count]
        
        # Auto-create frames - append if frames exist, otherwise create new
        # No user dialog needed - automation should be automatic
        
        # Frame count already calculated above, no need to recalculate
        
        # Generate frames with progressive transformations (LED Matrix Studio style)
        # Each frame applies transformations to the ORIGINAL source frame with progressive offsets
        new_frames = []
        # Store original source pixels (never modify this)
        original_pixels = [tuple(pixel) for pixel in source_frame.pixels]
        total_gap = 0
        
        # Calculate total gap from all actions (for reporting)
        for action in actions:
            params = action.params or {}
            gap_ms = max(0, int(params.get("gap_ms", 0)))
            total_gap += gap_ms
        
        # Use batch processing for large frame counts
        if frame_count > 50:
            progress = QProgressDialog("Generating frames...", "Cancel", 0, frame_count, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
        
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        
        # Calculate starting frame index for progressive transformations
        # When appending to existing frames, use absolute frame index (not relative to batch)
        # This ensures each frame gets a unique transformation based on its position in the pattern
        # Example: If we have 3 existing frames (indices 0,1,2) and generate 4 new frames:
        #   - First new frame should use frame_index=3 (not 0)
        #   - Second new frame should use frame_index=4 (not 1)
        #   - etc.
        # This prevents duplicates when the first generated frame (i=0) would be identical to source
        starting_frame_index = initial_frame_count
        
        # For rotation actions, ensure we start from a rotation step that avoids immediate duplicates
        # If starting_frame_index % 4 == 0 and source is frame 0, the first generated frame would
        # be a 0° rotation (duplicate). Skip to next rotation step to avoid this.
        has_rotate = any(getattr(a, 'action_type', '').lower() == 'rotate' for a in actions)
        if has_rotate and initial_frame_count > 0 and starting_frame_index % 4 == 0:
            # Offset by 1 to avoid starting with 0° rotation when appending
            # This ensures the first generated frame is unique (90° instead of 0°)
            starting_frame_index += 1
        
        for i in range(frame_count):
            if frame_count > 50:
                if progress.wasCanceled():
                    break
                progress.setValue(i)
                QApplication.processEvents()
            
            # Start with ORIGINAL source frame pixels for each frame (progressive transformation)
            # This ensures each frame shows progressive movement from the original, not cumulative
            frame_pixels = [tuple(pixel) for pixel in original_pixels]
            temp_frame = Frame(pixels=frame_pixels, duration_ms=source_frame.duration_ms)
            
            # Calculate gap for this frame from all actions
            frame_gap = 0
            for action in actions:
                params = action.params or {}
                gap_ms = max(0, int(params.get("gap_ms", 0)))
                frame_gap += gap_ms
            
            # Use absolute frame index for progressive transformations
            # This ensures frames are unique even when appending to existing frames
            absolute_frame_index = starting_frame_index + i
            
            # ONE unified pipeline - all actions applied in priority order
            # Rotate/mirror/flip operate on the result of earlier actions in the same frame
            # They do NOT accumulate across frames (use base-frame time logic), but they DO
            # participate in the same-frame pipeline
            
            # Convert DesignActions to LayerActions and collect active actions with steps
            active_actions_with_steps = []
            
            for design_action in actions:
                # Convert DesignAction to LayerAction for LMS-style step calculation
                layer_action = LayerAction(
                    type=design_action.action_type.lower(),
                    start_frame=starting_frame_index - 1 if initial_frame_count > 0 else starting_frame_index,  # Bias step to avoid static first frame
                    end_frame=None,  # No end frame - continues for all generated frames
                    params=design_action.params or {},
                    finalized=False,
                    name=design_action.name
                )
                
                # Check if action is active at this frame (LMS-style)
                if not layer_action.is_active_at_frame(absolute_frame_index):
                    continue
                
                # Calculate local step (frame-relative, LMS-style)
                local_step = get_action_step(layer_action, absolute_frame_index)
                if local_step is None:
                    continue
                
                # Get repeat parameter for step wrapping
                params = design_action.params or {}
                repeat = max(1, int(params.get("repeat", 1)))
                
                active_actions_with_steps.append((design_action, layer_action, local_step, repeat))
            
            # Sort by ACTION_PRIORITY (LMS fixed order)
            active_actions_with_steps.sort(
                key=lambda x: ACTION_PRIORITY.get(x[0].action_type.lower(), 100)
            )
            
            # Apply all actions in priority order in ONE unified pipeline
            frame_pixels = [tuple(pixel) for pixel in original_pixels]
            for design_action, layer_action, local_step, repeat in active_actions_with_steps:
                # FIXED: Do not modulo by repeat count (default 1) as it creates 0 step (static)
                # Pass full local_step to allow progressive animation (scroll/rotate handle wrapping internally)
                effective_step = local_step
                transformed = self._transform_pixels(frame_pixels, design_action, width, height, effective_step)
                if transformed:
                    frame_pixels = transformed
            
            # Final result from unified pipeline
            temp_frame.pixels = frame_pixels
            
            # Apply gap as delay between frames (adds to frame duration)
            if frame_gap > 0:
                temp_frame.duration_ms = max(1, int(temp_frame.duration_ms) + frame_gap)
            
            # Mark frame as baked (generated from automation, should not be re-automated)
            temp_frame.is_baked = True
            temp_frame.source_frame_id = source_frame_idx
            
            # Add generated frame
            new_frames.append(temp_frame)
        
        if frame_count > 50:
            progress.close()
        
        # Validate generated frames
        if not new_frames:
            QMessageBox.warning(self, "No Frames Generated", "No frames were generated. Please check your settings.")
            return
        
        # Ensure all frames have correct pixel count
        expected_pixel_count = self._pattern.metadata.width * self._pattern.metadata.height
        for i, frame in enumerate(new_frames):
            if len(frame.pixels) != expected_pixel_count:
                QMessageBox.warning(
                    self,
                    "Frame Size Mismatch",
                    f"Frame {i} has {len(frame.pixels)} pixels, expected {expected_pixel_count}.\n"
                    f"This may indicate an issue with frame generation."
                )
                # Fix the frame by padding or truncating
                if len(frame.pixels) < expected_pixel_count:
                    frame.pixels.extend([(0, 0, 0)] * (expected_pixel_count - len(frame.pixels)))
                else:
                    frame.pixels = frame.pixels[:expected_pixel_count]
        
        # Check for duplicate frames before appending and filter them out
        # Validate that we're not creating duplicates
        unique_new_frames = []
        duplicate_count = 0
        
        # Check if actions are cyclic (Scroll/Rotate) to enable smart trimming
        is_cyclic = any(a.action_type.lower() in ['scroll', 'rotate'] for a in actions)
        source_frame = self._pattern.frames[source_frame_idx] if self._pattern.frames else None

        for i, new_frame in enumerate(new_frames):
            # Disable standard duplicate filtering to allow blank canvas animation.
            # BUT: If Appending, Cyclic, and Frame == Source, drop it to prevent loop stutter (e.g. F12==F0).
            drop_cyclic_duplicate = False
            if is_cyclic and initial_frame_count > 0 and source_frame:
                 if self._frames_are_identical(new_frame, source_frame):
                     drop_cyclic_duplicate = True
                     self._log_frame_generation("CYCLIC_DUPLICATE_TRIMMED", len(unique_new_frames), {"index": i})
            
            if not drop_cyclic_duplicate:
                unique_new_frames.append(new_frame)
        
        if duplicate_count > 0:
            self._log_frame_generation("WARNING - Duplicates Filtered", len(self._pattern.frames), {
                "duplicate_count": duplicate_count,
                "total_new_frames": len(new_frames),
                "unique_new_frames": len(unique_new_frames)
            })
        
        # Only proceed if we have unique frames to add
        if not unique_new_frames:
            self._log_frame_generation("ERROR - All Frames Duplicate", len(self._pattern.frames), {
                "total_generated": len(new_frames)
            })
            QMessageBox.warning(
                self,
                "No Unique Frames",
                f"All {len(new_frames)} generated frame(s) were duplicates of existing frames.\n"
                "No new frames were added."
            )
            return
        
        # Auto-append frames (automation should be automatic)
        if not self._pattern.frames:
            # If no frames exist, create new ones
            self._pattern.frames = unique_new_frames
            self._current_frame_index = 0
            new_frame_start_idx = 0
        else:
            # Append to existing frames (only unique ones)
            self._pattern.frames.extend(unique_new_frames)
            self._current_frame_index = len(self._pattern.frames) - len(unique_new_frames)
            new_frame_start_idx = len(self._pattern.frames) - len(unique_new_frames)
        
        # Copy layer structure from source frame to all new frames
        # This preserves layer content and animations in the generated frames
        try:
            tracks = self.layer_manager.get_layer_tracks()
            
            # Sort actions by priority once (for consistency)
            sorted_actions = sorted(actions, key=lambda x: ACTION_PRIORITY.get(x.action_type.lower(), 100))
            
            for i, new_frame in enumerate(unique_new_frames):
                new_frame_idx = new_frame_start_idx + i
                # Step correlates to index i. If appending (initial > 0), bias by 1 to skip static Step 0.
                current_step = i + 1 if initial_frame_count > 0 else i
                
                # For each track, apply TRANSFORMATION to source frame
                for track in tracks:
                    source_layer_frame = track.get_frame(source_frame_idx)
                    if source_layer_frame:
                        # Start with source pixels
                        layer_pixels = [tuple(p) for p in source_layer_frame.pixels]
                        
                        # Apply all actions to this layer's pixels
                        for action in sorted_actions:
                            transformed = self._transform_pixels(layer_pixels, action, width, height, current_step)
                            if transformed:
                                layer_pixels = transformed
                                
                        # Save transformed frame to track
                        new_layer_frame = source_layer_frame.copy()
                        new_layer_frame.pixels = layer_pixels
                        track.set_frame(new_frame_idx, new_layer_frame)
            
            # NOTE: Do NOT sync_frame_from_layers() here - composite is derived via render_frame()
            # Only sync when explicitly needed (export, preview generation)
            # Frames will be rendered on-demand using render_frame()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to preserve layers in generated frames: {e}")
            # NOTE: Do NOT sync_frame_from_layers() here - composite is derived via render_frame()
        
        # Update UI
        final_frame_count = len(self._pattern.frames)
        self._log_frame_generation("COMPLETE", final_frame_count, {
            "frames_generated": len(new_frames),
            "unique_frames_added": len(unique_new_frames),
            "duplicates_filtered": duplicate_count,
            "initial_frames": initial_frame_count,
            "final_frames": final_frame_count
        })
        
        self.history_manager.set_frame_count(len(self._pattern.frames))
        self.history_manager.set_current_frame(self._current_frame_index)
        self.frame_manager.set_pattern(self._pattern)
        self._load_current_frame_into_canvas()
        self._refresh_timeline()
        self._update_status_labels()
        self._maybe_autosync_preview()
        self.pattern_modified.emit()
        
        # Removed dialog - frame generation is now automatic and silent

    def _generate_layer_frames_with_actions(self, layer_index: int, actions: List[DesignAction]):
        """
        Generate frames for a specific layer by applying actions incrementally.
        
        This creates baked frames in the layer track, while also allowing
        layer animations to be applied at runtime.
        
        Args:
            layer_index: Index of the layer track to generate frames for
            actions: List of automation actions to apply
        """
        try:
            if not self._pattern:
                QMessageBox.warning(self, "No Pattern", "No pattern loaded.")
                return
            
            if not actions:
                QMessageBox.warning(self, "No Actions", "No actions to apply.")
                return
            
            # Get the layer track
            tracks = self.layer_manager.get_layer_tracks()
            if layer_index < 0 or layer_index >= len(tracks):
                QMessageBox.warning(self, "Invalid Layer", f"Layer index {layer_index} is out of bounds.")
                return
            
            track = tracks[layer_index]
            
            # Get source frame from the layer (use frame 0 if exists, otherwise create blank)
            width = self._pattern.metadata.width
            height = self._pattern.metadata.height
            expected_pixel_count = width * height
            
            # Get source frame (prefer frame 0, or first available frame)
            source_layer_frame = track.get_frame(0)
            if not source_layer_frame:
                # Create blank source frame
                blank_pixels = [(0, 0, 0)] * expected_pixel_count
                source_layer_frame = LayerFrame(pixels=blank_pixels)
            
            original_pixels = [tuple(pixel) for pixel in source_layer_frame.pixels]
            
            # LMS-correct frame count calculation: UI-only suggestion, not semantic enforcement
            # Calculate suggested frame count based on action parameters (UI-only)
            frame_count = 10  # Default minimum suggestion
            max_frames_suggestion = 10
            
            for action in actions:
                params = action.params or {}
                action_type = getattr(action, 'action_type', '').lower()
                repeat = max(1, int(params.get("repeat", 1)))
                
                # UI-only suggestions (LMS doesn't enforce these limits)
                if action_type == "scroll":
                    direction = params.get("direction", "Right").lower()
                    if direction in ["left", "right"]:
                        frames_suggestion = width
                    else:
                        frames_suggestion = height
                    max_frames_suggestion = max(max_frames_suggestion, frames_suggestion * repeat)
                elif action_type == "rotate":
                    max_frames_suggestion = max(max_frames_suggestion, 4 * repeat)
                elif action_type in ["wipe", "reveal"]:
                    direction = params.get("direction", "Left").lower() if action_type == "reveal" else params.get("mode", "Left to Right").lower()
                    if "left" in direction or "right" in direction:
                        frames_suggestion = width
                    else:
                        frames_suggestion = height
                    max_frames_suggestion = max(max_frames_suggestion, frames_suggestion * repeat)
                else:
                    max_frames_suggestion = max(max_frames_suggestion, repeat * 5)
            
            # Use suggestion as default (can be overridden)
            frame_count = max(10, max_frames_suggestion)
            
            # Get current frame count for this layer
            current_layer_frame_count = track.get_frame_count()
            start_frame_index = current_layer_frame_count
            
            # Generate frames with progressive transformations
            progress = None
            if frame_count > 50:
                progress = QProgressDialog(f"Generating {frame_count} frames for layer '{track.name}'...", "Cancel", 0, frame_count, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
            
            for i in range(frame_count):
                if progress and progress.wasCanceled():
                    break
                if progress:
                    progress.setValue(i)
                    QApplication.processEvents()
                
                # Calculate absolute frame index in pattern
                absolute_frame_index = start_frame_index + i
                
                # Check layer window (LMS-style: skip if layer inactive at this frame)
                if not self.layer_manager.is_layer_active(track, absolute_frame_index):
                    # Layer is inactive - create empty frame or skip
                    layer_frame = LayerFrame(pixels=[(0, 0, 0)] * expected_pixel_count)
                    track.set_frame(absolute_frame_index, layer_frame)
                    continue
                
                # ONE unified pipeline - all actions applied in priority order
                # Rotate/mirror/flip operate on the result of earlier actions in the same frame
                # They do NOT accumulate across frames (use base-frame time logic), but they DO
                # participate in the same-frame pipeline
                
                # Convert DesignActions to LayerActions and collect active actions with steps
                active_actions_with_steps = []
                
                for design_action in actions:
                    # Convert DesignAction to LayerAction for LMS-style step calculation
                    layer_action = LayerAction(
                        type=design_action.action_type.lower(),
                        start_frame=start_frame_index,  # Action starts at generation start
                        end_frame=None,  # No end frame - continues for all generated frames
                        params=design_action.params or {},
                        finalized=False,
                        name=design_action.name
                    )
                    
                    # Check if action is active at this frame (LMS-style)
                    if not layer_action.is_active_at_frame(absolute_frame_index):
                        continue
                    
                    # Calculate local step (frame-relative, LMS-style)
                    local_step = get_action_step(layer_action, absolute_frame_index)
                    if local_step is None:
                        continue
                    
                    # Handle repeat parameter (apply action multiple times if needed)
                    params = design_action.params or {}
                    repeat = max(1, int(params.get("repeat", 1)))
                    
                    active_actions_with_steps.append((design_action, layer_action, local_step, repeat))
                
                # Sort by ACTION_PRIORITY (LMS fixed order)
                active_actions_with_steps.sort(
                    key=lambda x: ACTION_PRIORITY.get(x[0].action_type.lower(), 100)
                )
                
                # Apply all actions in priority order in ONE unified pipeline
                frame_pixels = [tuple(pixel) for pixel in original_pixels]
                for design_action, layer_action, local_step, repeat in active_actions_with_steps:
                    # Repeat wraps step (modulo), never multiplies it
                    # effective_step = step % action_length (where action_length = repeat)
                    effective_step = local_step % repeat if repeat > 0 else local_step
                    transformed = self._transform_pixels(frame_pixels, design_action, width, height, effective_step)
                    if transformed:
                        frame_pixels = transformed
                
                # Create layer frame for this frame index
                layer_frame = LayerFrame(pixels=list(frame_pixels))
                track.set_frame(absolute_frame_index, layer_frame)
            
            if progress:
                progress.close()
            
            # Emit signal to update UI
            self.layer_manager.layers_changed.emit(-1)
            self._load_current_frame_into_canvas()
            self._refresh_timeline()
            self.pattern_modified.emit()
            
            QMessageBox.information(
                self,
                "Frames Generated",
                f"Generated {frame_count} frames for layer '{track.name}'.\n"
                f"Layer now has {track.get_frame_count()} total frames."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Frame Generation Error",
                f"Failed to generate frames for layer:\n\n{str(e)}\n\nPlease check your pattern and try again."
            )
            import logging
            logging.exception(f"Error generating frames for layer {layer_index}")
            raise  # Re-raise to prevent silent failure

    def _apply_action_with_schedule(self, frame: Frame, action: DesignAction, apply_gap: bool = True, frame_index: Optional[int] = None) -> int:
        """
        Apply action to frame with repeat and gap scheduling.
        
        Args:
            frame: Frame to apply action to
            action: Action to apply
            apply_gap: If True, apply gap to frame duration. If False, gap is handled externally.
            frame_index: Optional frame index for frame generation (for incremental transformations)
        
        Returns:
            Number of times action was successfully applied
        """
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
            if self._perform_action(frame, action, frame_index=frame_index):
                changes += 1

        # Apply gap only if requested (for existing frame application)
        # During frame generation, gap is applied between frames, not here
        if apply_gap and gap_ms > 0:
            frame.duration_ms = max(1, int(frame.duration_ms) + gap_ms)

        return changes

    
    def _is_sequential_transform(self, action_type: str) -> bool:
        """
        Check if action operates on transformed pixels (scroll, wipe, reveal, etc.).
        
        Sequential transforms operate on pixels in the order they appear in the
        transform pipeline, building on previous transformations.
        
        Args:
            action_type: Action type string (e.g., "scroll", "wipe")
            
        Returns:
            True if action is a sequential transform, False otherwise
        """
        sequential_actions = {"scroll", "wipe", "reveal", "bounce", "radial", "colour_cycle", "invert"}
        return action_type.lower() in sequential_actions
    
    def _transform_pixels(self, pixels: List[Tuple[int, int, int]], action: DesignAction, width: int, height: int, step: int) -> Optional[List[Tuple[int, int, int]]]:
        """
        Transform a list of pixels based on action type.
        
        LMS-CORRECT STATELESS MODEL:
        - All transformations are stateless functions: transform(pixels, step, params)
        - step is the local step number (frame_index - action.start_frame)
        - Progressive actions multiply: effective_value = base_value * step
        - Each frame calculates its transform independently from base pixels
        - No state accumulation - same base pixels + step always = same result
        - Step 0: no transformation (offset=0), Step N: offset = base_offset * N
        
        Examples:
        - Scroll: Step 0=0px, Step 1=1px, Step 2=2px (offset * step)
        - Rotate: Step 0=0°, Step 1=90°, Step 2=180°, Step 3=270° (step % 4)
        - Wipe: Step 0=0px, Step 1=1px wipe position, Step 2=2px (offset * step)
        
        Args:
            pixels: List of RGB tuples in row-major order (base pixels, unchanged)
            action: DesignAction to apply
            width: Matrix width
            height: Matrix height
            step: Local step number (frame_index - action.start_frame, LMS-style)
            
        Returns:
            Transformed pixel list or None if action not supported
        """
        try:
            # Validate inputs
            if not pixels:
                return None
            
            if width <= 0 or height <= 0:
                return None
            
            expected_count = width * height
            if len(pixels) != expected_count:
                return None
            
            if not action or not hasattr(action, 'action_type'):
                return None
            
            action_type = action.action_type
            
            if action_type == "scroll":
                direction = action.params.get("direction", "Right")
                base_offset = max(1, int(action.params.get("offset", 1)))
                # LMS-correct: multiply offset by step (not frame_index)
                # Step 0: no scroll (offset=0), Step 1: scroll by base_offset, Step 2: scroll by 2*base_offset, etc.
                offset = base_offset * step
                return self._transform_scroll(pixels, width, height, direction, offset)
            elif action_type == "rotate":
                mode = action.params.get("mode", "90° Clockwise")
                # LMS-correct: rotate by step * 90 degrees
                # Step 0: no rotation, Step 1: 90°, Step 2: 180°, Step 3: 270°, Step 4: 360° (0°), etc.
                rotations = step % 4  # 0-3 rotations (cycles every 4 steps)
                result = pixels
                for _ in range(rotations):
                    result = self._transform_rotate(result, width, height, mode)
                return result
            elif action_type == "mirror":
                axis = action.params.get("axis", "horizontal")
                return self._transform_mirror(pixels, width, height, axis)
            elif action_type == "flip":
                axis = action.params.get("axis", "vertical")
                return self._transform_flip(pixels, width, height, axis)
            elif action_type == "invert":
                return self._transform_invert(pixels)
            elif action_type == "wipe":
                mode = action.params.get("mode", "Left to Right")
                base_offset = max(1, int(action.params.get("offset", 1)))
                # LMS-correct: multiply offset by step (not frame_index)
                # Step 0: no wipe (offset=0), Step 1: wipe by base_offset, Step 2: wipe by 2*base_offset, etc.
                offset = base_offset * step
                return self._transform_wipe(pixels, width, height, mode, offset)
            elif action_type == "reveal":
                direction = action.params.get("direction", "Left")
                base_offset = max(1, int(action.params.get("offset", 1)))
                # LMS-correct: multiply offset by step (not frame_index)
                # Step 0: no reveal (offset=0), Step 1: reveal by base_offset, Step 2: reveal by 2*base_offset, etc.
                offset = base_offset * step
                return self._transform_reveal(pixels, width, height, direction, offset)
            elif action_type == "bounce":
                axis = action.params.get("axis", "Horizontal")
                # LMS-correct: bounce direction alternates based on step
                # Even steps: normal, odd steps: bounced
                if step % 2 == 1:
                    return self._transform_bounce(pixels, width, height, axis)
                else:
                    return pixels  # Return original for even steps
            elif action_type == "colour_cycle":
                mode = action.params.get("mode", "RGB")
                return self._transform_colour_cycle(pixels, mode)
            elif action_type == "radial":
                type_str = action.params.get("type", "Spiral")
                return self._transform_radial(pixels, width, height, type_str)
            else:
                return None
        except Exception as e:
            import logging
            logging.exception(f"Error in _transform_pixels for action {action_type}")
            return None

    def _perform_action(self, frame: Frame, action: DesignAction, frame_index: Optional[int] = None) -> bool:
        """
        Apply automation action to frame using layer system.
        
        Instead of modifying frame.pixels directly, this method:
        1. Gets composite pixels from all visible layers
        2. Transforms the composite pixels
        3. Creates a new layer with the transformed result
        4. Syncs frame from layers
        
        This preserves original layers and makes automation non-destructive.
        
        Args:
            frame: Frame to transform
            action: Action to apply
            frame_index: Optional frame index (for frame generation, bypasses frame lookup)
        """
        try:
            # Validate pattern and frames
            if not self._pattern or not self._pattern.frames:
                QMessageBox.warning(self, "No Pattern", "No pattern loaded. Create or load a pattern first.")
                return False
            
            # Find frame index if not provided
            if frame_index is None:
                for idx, f in enumerate(self._pattern.frames):
                    if f is frame:
                        frame_index = idx
                        break
                
                if frame_index is None:
                    # Fallback: use current frame index
                    frame_index = self._current_frame_index
            
            # Validate frame index
            if frame_index < 0 or frame_index >= len(self._pattern.frames):
                QMessageBox.warning(self, "Invalid Frame", f"Frame index {frame_index} is out of bounds.")
                return False
            
            # Validate layer manager
            if not hasattr(self, 'layer_manager') or self.layer_manager is None:
                QMessageBox.warning(self, "Layer Manager Error", "Layer manager is not initialized.")
                return False
            
            # Validate metadata
            if not hasattr(self._pattern, 'metadata') or self._pattern.metadata is None:
                QMessageBox.warning(self, "Pattern Error", "Pattern metadata is missing.")
                return False
            
            width = self._pattern.metadata.width
            height = self._pattern.metadata.height
            
            if width <= 0 or height <= 0:
                QMessageBox.warning(self, "Invalid Dimensions", f"Pattern dimensions are invalid: {width}x{height}")
                return False
            
            # Get current composite (what user sees)
            composite = self.layer_manager.get_composite_pixels(frame_index)
            
            # Validate composite pixels
            if composite is None:
                QMessageBox.warning(self, "Layer Error", "Failed to get composite pixels from layers.")
                return False
            
            expected_pixel_count = width * height
            if len(composite) != expected_pixel_count:
                QMessageBox.warning(
                    self, 
                    "Pixel Count Mismatch", 
                    f"Composite pixel count ({len(composite)}) doesn't match pattern dimensions ({expected_pixel_count})."
                )
                return False
            
            # Transform composite pixels
            # For immediate action application, step is always 0 (no progressive offset)
            # Frame generation uses local step calculation separately
            step = 0
            transformed = self._transform_pixels(composite, action, width, height, step)
            
            if transformed is None:
                self._show_not_implemented(action.name)
                return False
            
            # Validate transformed pixels
            if len(transformed) != expected_pixel_count:
                QMessageBox.warning(
                    self,
                    "Transformation Error",
                    f"Transformed pixel count ({len(transformed)}) doesn't match expected count ({expected_pixel_count})."
                )
                return False
            
            # Create new layer for automation result
            layer_name = f"Auto: {action.name}"
            layer_index = self.layer_manager.add_layer(frame_index, layer_name)
            self.layer_manager.replace_pixels(frame_index, transformed, layer_index)
            
            # Sync frame from layers
            self.layer_manager.sync_frame_from_layers(frame_index)
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Automation Error",
                f"An error occurred while applying automation action '{action.name}':\n\n{str(e)}\n\nPlease check your pattern and try again."
            )
            import logging
            logging.exception("Error in _perform_action")
            return False

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

    def _grid_to_frame(self, grid: List[List[Tuple[int, int, int]]], frame: Frame, frame_index: Optional[int] = None, update_layer: bool = True):
        """
        Convert grid to frame pixels, optionally updating active layer.
        
        Args:
            grid: 2D grid of pixels
            frame: Frame object to update
            frame_index: Frame index (auto-detected if None and update_layer=True)
            update_layer: If True, update active layer instead of frame.pixels directly
        """
        pixels = [tuple(pixel) for row in grid for pixel in row]
        
        # Auto-detect frame index if not provided
        if update_layer and frame_index is None and hasattr(self, '_pattern') and self._pattern:
            try:
                frame_index = self._pattern.frames.index(frame)
            except (ValueError, AttributeError):
                frame_index = getattr(self, '_current_frame_index', None)
        
        if update_layer and frame_index is not None and hasattr(self, 'layer_manager') and self.layer_manager:
            # Get active layer or default to layer 0
            active_layer = 0
            if hasattr(self, 'layer_panel') and self.layer_panel:
                active_layer = self.layer_panel.get_active_layer_index()
                if active_layer < 0:
                    active_layer = 0
            
            # Update layer
            self.layer_manager.replace_pixels(frame_index, pixels, active_layer)
        else:
            # Fallback: update frame directly (legacy mode or when explicitly requested)
            frame.pixels = pixels

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
        # Get frame index
        frame_index = None
        if hasattr(self, '_pattern') and self._pattern:
            try:
                frame_index = self._pattern.frames.index(frame)
            except (ValueError, AttributeError):
                frame_index = getattr(self, '_current_frame_index', None)
        
        inverted_pixels = [(255 - r, 255 - g, 255 - b) for r, g, b in frame.pixels]
        
        # Update layer if using layer manager
        if frame_index is not None and hasattr(self, 'layer_manager') and self.layer_manager:
            active_layer = 0
            if hasattr(self, 'layer_panel') and self.layer_panel:
                active_layer = self.layer_panel.get_active_layer_index()
                if active_layer < 0:
                    active_layer = 0
            self.layer_manager.replace_pixels(frame_index, inverted_pixels, active_layer)
        else:
            # Fallback: update frame directly (legacy mode)
            frame.pixels = inverted_pixels
        
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
        
        # Get frame index and active layer for layer updates
        frame_index = None
        if hasattr(self, '_pattern') and self._pattern:
            try:
                frame_index = self._pattern.frames.index(frame)
            except (ValueError, AttributeError):
                frame_index = getattr(self, '_current_frame_index', None)
        
        active_layer = 0
        if hasattr(self, 'layer_panel') and self.layer_panel:
            active_layer = self.layer_panel.get_active_layer_index()
            if active_layer < 0:
                active_layer = 0
        
        # Get current pixels from layer or frame
        current_pixels = frame.pixels
        if frame_index is not None and hasattr(self, 'layer_manager') and self.layer_manager:
            layer_frame = self.layer_manager.get_layer_track(active_layer).get_frame(frame_index)
            if layer_frame:
                current_pixels = layer_frame.pixels
        
        if mode == "rgb":
            # Cycle RGB channels
            new_pixels = []
            for r, g, b in current_pixels:
                new_pixels.append((g, b, r))  # Shift RGB -> GBR
        elif mode == "ryb":
            # Cycle RYB (Red-Yellow-Blue)
            new_pixels = []
            for r, g, b in current_pixels:
                # Convert to RYB-like cycle
                new_pixels.append((b, r, g))
        else:  # custom or default
            # Simple hue shift
            new_pixels = []
            for r, g, b in current_pixels:
                new_pixels.append((b, r, g))
        
        # Update layer or frame
        if frame_index is not None and hasattr(self, 'layer_manager') and self.layer_manager:
            self.layer_manager.replace_pixels(frame_index, new_pixels, active_layer)
        else:
            # Fallback: update frame directly (legacy mode)
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

    # ------------------------------------------------------------------
    # Pixel-based transformation methods (for layer integration)
    # ------------------------------------------------------------------
    
    def _pixels_to_grid(self, pixels: List[Tuple[int, int, int]], width: int, height: int) -> List[List[Tuple[int, int, int]]]:
        """Convert pixel list to 2D grid."""
        grid = []
        idx = 0
        for _ in range(height):
            row = pixels[idx:idx + width]
            if len(row) < width:
                row += [(0, 0, 0)] * (width - len(row))
            grid.append(row)
            idx += width
        return grid
    
    def _grid_to_pixels(self, grid: List[List[Tuple[int, int, int]]]) -> List[Tuple[int, int, int]]:
        """Convert 2D grid to pixel list."""
        return [tuple(pixel) for row in grid for pixel in row]
    
    def _transform_scroll(self, pixels: List[Tuple[int, int, int]], width: int, height: int, direction: str, offset: int = 1) -> List[Tuple[int, int, int]]:
        """Transform pixels by scrolling."""
        grid = self._pixels_to_grid(pixels, width, height)
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
                # Use modulo for wrapping behavior (standard LED matrix scroll)
                src_x = (x - dx) % width
                src_y = (y - dy) % height
                new_grid[y][x] = grid[src_y][src_x]
        return self._grid_to_pixels(new_grid)
    
    def _transform_rotate(self, pixels: List[Tuple[int, int, int]], width: int, height: int, mode: str) -> List[Tuple[int, int, int]]:
        """Transform pixels by rotation (90 degrees)."""
        grid = self._pixels_to_grid(pixels, width, height)
        orig_height = len(grid)
        orig_width = len(grid[0])
        clockwise = "clockwise" in mode.lower()
        
        # Create rotated grid (swapped dimensions)
        rotated = []
        if clockwise:
            # 90° clockwise: (x, y) -> (height-1-y, x)
            for x in range(orig_width):
                new_row = []
                for y in range(orig_height - 1, -1, -1):
                    new_row.append(grid[y][x])
                rotated.append(new_row)
        else:
            # 90° counter-clockwise: (x, y) -> (y, width-1-x)
            for x in range(orig_width - 1, -1, -1):
                new_row = []
                for y in range(orig_height):
                    new_row.append(grid[y][x])
                rotated.append(new_row)
        
        # Note: Rotation swaps width/height, but we maintain original dimensions
        # by padding or cropping. For proper rotation, pattern dimensions should be updated.
        # For now, we'll pad/crop to maintain pixel count
        result_pixels = self._grid_to_pixels(rotated)
        
        # If dimensions changed, we need to adjust
        if len(rotated) != height or (rotated and len(rotated[0]) != width):
            # Resize to original dimensions
            expected_count = width * height
            if len(result_pixels) < expected_count:
                result_pixels += [(0, 0, 0)] * (expected_count - len(result_pixels))
            else:
                result_pixels = result_pixels[:expected_count]
        
        return result_pixels
    
    def _transform_mirror(self, pixels: List[Tuple[int, int, int]], width: int, height: int, axis: str) -> List[Tuple[int, int, int]]:
        """Transform pixels by mirroring."""
        grid = self._pixels_to_grid(pixels, width, height)
        axis = axis.lower()
        if axis == "horizontal":
            new_grid = [list(reversed(row)) for row in grid]
        elif axis == "vertical":
            new_grid = list(reversed(grid))
        else:
            return pixels
        return self._grid_to_pixels(new_grid)
    
    def _transform_flip(self, pixels: List[Tuple[int, int, int]], width: int, height: int, axis: str) -> List[Tuple[int, int, int]]:
        """Transform pixels by flipping."""
        return self._transform_mirror(pixels, width, height, axis)
    
    def _transform_invert(self, pixels: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Transform pixels by inverting colors."""
        return [(255 - r, 255 - g, 255 - b) for r, g, b in pixels]
    
    def _transform_wipe(self, pixels: List[Tuple[int, int, int]], width: int, height: int, mode: str, offset: int = 1) -> List[Tuple[int, int, int]]:
        """Transform pixels with wipe effect."""
        grid = self._pixels_to_grid(pixels, width, height)
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
            wipe_pos = min(offset, height)
            for idx, row in enumerate(ordered_rows):
                fade = 1.0 if idx < wipe_pos else max(0.0, 1.0 - (idx - wipe_pos) / max(1, height - wipe_pos))
                ordered_rows[idx] = [(int(r * fade), int(g * fade), int(b * fade)) for r, g, b in row]
            if not forward:
                ordered_rows.reverse()
            grid = ordered_rows
        
        return self._grid_to_pixels(grid)
    
    def _transform_reveal(self, pixels: List[Tuple[int, int, int]], width: int, height: int, direction: str, offset: int = 1) -> List[Tuple[int, int, int]]:
        """Transform pixels with reveal effect."""
        grid = self._pixels_to_grid(pixels, width, height)
        direction = direction.lower()
        
        mask_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        if direction == "left":
            reveal_width = min(offset, width)
            for y in range(height):
                for x in range(reveal_width):
                    mask_grid[y][x] = grid[y][x]
        elif direction == "right":
            reveal_width = min(offset, width)
            for y in range(height):
                for x in range(width - reveal_width, width):
                    mask_grid[y][x] = grid[y][x]
        elif direction == "top":
            reveal_height = min(offset, height)
            for y in range(reveal_height):
                mask_grid[y] = list(grid[y])
        elif direction == "bottom":
            reveal_height = min(offset, height)
            for y in range(height - reveal_height, height):
                mask_grid[y] = list(grid[y])
        else:
            return pixels
        
        return self._grid_to_pixels(mask_grid)
    
    def _transform_bounce(self, pixels: List[Tuple[int, int, int]], width: int, height: int, axis: str) -> List[Tuple[int, int, int]]:
        """Transform pixels with bounce effect."""
        grid = self._pixels_to_grid(pixels, width, height)
        axis = axis.lower()
        
        if axis == "horizontal":
            new_grid = [list(reversed(row)) for row in grid]
        else:  # vertical
            new_grid = list(reversed(grid))
        
        return self._grid_to_pixels(new_grid)
    
    def _transform_colour_cycle(self, pixels: List[Tuple[int, int, int]], mode: str) -> List[Tuple[int, int, int]]:
        """Transform pixels with color cycling."""
        mode = mode.lower()
        
        if mode == "rgb":
            return [(g, b, r) for r, g, b in pixels]
        elif mode == "ryb":
            return [(b, r, g) for r, g, b in pixels]
        else:
            return [(b, r, g) for r, g, b in pixels]
    
    def _transform_radial(self, pixels: List[Tuple[int, int, int]], width: int, height: int, type_str: str) -> List[Tuple[int, int, int]]:
        """Transform pixels with radial effect."""
        grid = self._pixels_to_grid(pixels, width, height)
        type_str = type_str.lower()
        
        center_x = width / 2.0
        center_y = height / 2.0
        max_dist = ((center_x) ** 2 + (center_y) ** 2) ** 0.5
        
        new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        if type_str == "spiral":
            for y in range(height):
                for x in range(width):
                    dx = x - center_x
                    dy = y - center_y
                    angle = (dx ** 2 + dy ** 2) ** 0.5 * 0.5
                    new_x = int(center_x + dx * 0.9 - dy * 0.1)
                    new_y = int(center_y + dy * 0.9 + dx * 0.1)
                    if 0 <= new_x < width and 0 <= new_y < height:
                        new_grid[new_y][new_x] = grid[y][x]
        elif type_str == "pulse":
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
            for y in range(height):
                for x in range(width):
                    dx = x - center_x
                    dy = y - center_y
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    if dist < max_dist * 0.7:
                        new_grid[y][x] = grid[y][x]
        
        return self._grid_to_pixels(new_grid)

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
        
        # Get frame index and active layer for layer updates
        frame_index = None
        if hasattr(self, '_pattern') and self._pattern:
            try:
                frame_index = self._pattern.frames.index(frame)
            except (ValueError, AttributeError):
                frame_index = getattr(self, '_current_frame_index', None)
        
        active_layer = 0
        if hasattr(self, 'layer_panel') and self.layer_panel:
            active_layer = self.layer_panel.get_active_layer_index()
            if active_layer < 0:
                active_layer = 0
        
        # Helper to get current pixels from layer or frame
        def get_current_pixels():
            if frame_index is not None and hasattr(self, 'layer_manager') and self.layer_manager:
                layer_frame = self.layer_manager.get_layer_track(active_layer).get_frame(frame_index)
                if layer_frame:
                    return layer_frame.pixels
            return frame.pixels
        
        # Helper to update pixels (layer or frame)
        def update_pixels(new_pixels):
            if frame_index is not None and hasattr(self, 'layer_manager') and self.layer_manager:
                # Update layer
                self.layer_manager.replace_pixels(frame_index, new_pixels, active_layer)
            else:
                # Fallback: update frame directly (legacy mode)
                frame.pixels = new_pixels
        
        if effect_name == "Fade In/Out":
            current_pixels = get_current_pixels()
            
            new_pixels = []
            for r, g, b in current_pixels:
                fade = factor
                new_pixels.append((
                    int(r * fade),
                    int(g * fade),
                    int(b * fade)
                ))
            update_pixels(new_pixels)
            
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
            current_pixels = get_current_pixels()
            
            brightness_delta = int((factor - 0.5) * 255)
            new_pixels = []
            for r, g, b in current_pixels:
                new_pixels.append((
                    max(0, min(255, r + brightness_delta)),
                    max(0, min(255, g + brightness_delta)),
                    max(0, min(255, b + brightness_delta))
                ))
            update_pixels(new_pixels)
            
        elif effect_name == "Contrast Adjust":
            current_pixels = get_current_pixels()
            
            contrast_factor = (factor - 0.5) * 2.0
            new_pixels = []
            for r, g, b in current_pixels:
                r_new = int(128 + (r - 128) * (1 + contrast_factor))
                g_new = int(128 + (g - 128) * (1 + contrast_factor))
                b_new = int(128 + (b - 128) * (1 + contrast_factor))
                new_pixels.append((
                    max(0, min(255, r_new)),
                    max(0, min(255, g_new)),
                    max(0, min(255, b_new))
                ))
            update_pixels(new_pixels)
            
        elif effect_name == "Color Shift":
            current_pixels = get_current_pixels()
            
            shift_amount = int(factor * 360)
            new_pixels = []
            for r, g, b in current_pixels:
                if shift_amount < 120:
                    new_pixels.append((g, b, r))
                elif shift_amount < 240:
                    new_pixels.append((b, r, g))
                else:
                    new_pixels.append((r, g, b))
            update_pixels(new_pixels)
            
        elif effect_name == "Noise":
            current_pixels = get_current_pixels()
            
            import random
            noise_amount = int(factor * 50)
            new_pixels = []
            for r, g, b in current_pixels:
                noise_r = random.randint(-noise_amount, noise_amount)
                noise_g = random.randint(-noise_amount, noise_amount)
                noise_b = random.randint(-noise_amount, noise_amount)
                new_pixels.append((
                    max(0, min(255, r + noise_r)),
                    max(0, min(255, g + noise_g)),
                    max(0, min(255, b + noise_b))
                ))
            update_pixels(new_pixels)
            
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
            
        self._frame_switch_locked = True
        try:
            if not self._pattern:
                self.timeline.set_frames([])
                self.timeline.set_markers([])
                self.timeline.set_overlays([])
                self.timeline.set_layer_tracks([])
                self.timeline.set_frame_durations([])
                return

            frames_data: List[Tuple[str, Optional[QPixmap]]] = []
            frame_durations: List[int] = []
            
            for idx, frame in enumerate(self._pattern.frames):
                pixel_count = len(frame.pixels) if frame.pixels else 0
                display = f"Frame {idx + 1:02d}  •  {frame.duration_ms} ms  •  {pixel_count} px"
                
                # Generate composite thumbnail from layers
                composite_thumbnail = self._make_composite_frame_thumbnail(idx)
                frames_data.append((display, composite_thumbnail))
                frame_durations.append(frame.duration_ms)
            
            self.timeline.set_frames(frames_data)
            self.timeline.set_frame_durations(frame_durations)
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
        finally:
            self._frame_switch_locked = False
    
    def _make_composite_frame_thumbnail(self, frame_idx: int) -> Optional[QPixmap]:
        """
        Generate composite thumbnail from all visible layers for a frame.
        
        NEW: Uses render_frame() to get composite pixels (derived, not stored).
        """
        if not self._pattern or frame_idx >= len(self._pattern.frames):
            return None
        
        # Use render_frame() to get composite pixels (order-only rendering)
        composite_pixels = self.layer_manager.render_frame(frame_idx)
        
        if not composite_pixels:
            return None
        
        # Create thumbnail image
        if self._pattern and self._pattern.metadata:
            width = max(1, self._pattern.metadata.width)
            height = max(1, self._pattern.metadata.height)
        else:
            width = max(1, int(len(composite_pixels) ** 0.5))
            height = max(1, len(composite_pixels) // width)
        
        image = QImage(width, height, QImage.Format_RGB32)
        image.fill(QColor(0, 0, 0))
        limit = width * height
        
        for idx, pixel in enumerate(composite_pixels[:limit]):
            if pixel is None:
                continue
            x = idx % width
            y = idx // width
            r, g, b = pixel[:3] if isinstance(pixel, (list, tuple)) and len(pixel) >= 3 else (0, 0, 0)
            image.setPixel(x, y, QColor(r, g, b).rgb())
        
        # Convert to pixmap and scale to thumbnail size
        pixmap = QPixmap.fromImage(image)
        thumbnail_size = self._thumbnail_size
        scaled = pixmap.scaled(thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return scaled

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
        """
        Load the current frame into the canvas.
        
        NEW: Uses render_frame() to get composite pixels (derived, not stored).
        This ensures the canvas shows the correct composite with all layers and automation.
        """
        if not self._pattern:
            return
        
        # Get composite pixels from layers
        if hasattr(self, "layer_panel"):
            composite = self.layer_manager.get_composite_pixels(self._current_frame_index)
        else:
            # Fallback to direct frame loading
            frame = self._pattern.frames[self._current_frame_index] if self._current_frame_index < len(self._pattern.frames) else None
            if frame:
                composite = frame.pixels
            else:
                composite = []
        
        # Apply LED transforms if preview mode is enabled
        if hasattr(self, "led_color_panel") and self.led_color_panel and self.led_color_panel.is_preview_mode():
            transformed_pixels = []
            for pixel in composite:
                if isinstance(pixel, (list, tuple)) and len(pixel) >= 3:
                    r, g, b = pixel[0], pixel[1], pixel[2]
                    transformed = self.led_color_panel.apply_led_transform(r, g, b)
                    transformed_pixels.append(transformed)
                else:
                    transformed_pixels.append(pixel)
            composite = transformed_pixels
        
        self.canvas.set_frame_pixels(composite)
        
        # Update onion skins if enabled
        if self._onion_skin_enabled:
            self._update_onion_skins()
        
        self._update_status_labels()

    def _update_onion_skins(self):
        """Update onion skin overlays for canvas."""
        if not self._pattern or not self.canvas:
            return
        
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        total_frames = len(self._pattern.frames)
        
        # Get previous frames
        prev_frames = []
        prev_opacities = []
        for i in range(1, self._onion_skin_prev_count + 1):
            frame_idx = self._current_frame_index - i
            if 0 <= frame_idx < total_frames:
                # Get composite pixels for previous frame using render_frame()
                pixels = self.layer_manager.render_frame(frame_idx)
                
                # Convert linear pixels to 2D grid
                grid = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        idx = y * width + x
                        if idx < len(pixels):
                            row.append(pixels[idx] if isinstance(pixels[idx], tuple) else tuple(pixels[idx][:3]))
                        else:
                            row.append((0, 0, 0))
                    grid.append(row)
                prev_frames.append(grid)
                # Opacity decreases for older frames
                opacity = self._onion_skin_prev_opacity * (1.0 - (i - 1) * 0.2)
                prev_opacities.append(max(0.1, opacity))
        
        # Get next frames
        next_frames = []
        next_opacities = []
        for i in range(1, self._onion_skin_next_count + 1):
            frame_idx = self._current_frame_index + i
            if 0 <= frame_idx < total_frames:
                # Get composite pixels for next frame using render_frame()
                pixels = self.layer_manager.render_frame(frame_idx)
                
                # Convert linear pixels to 2D grid
                grid = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        idx = y * width + x
                        if idx < len(pixels):
                            row.append(pixels[idx] if isinstance(pixels[idx], tuple) else tuple(pixels[idx][:3]))
                        else:
                            row.append((0, 0, 0))
                    grid.append(row)
                next_frames.append(grid)
                # Opacity decreases for further frames
                opacity = self._onion_skin_next_opacity * (1.0 - (i - 1) * 0.2)
                next_opacities.append(max(0.1, opacity))
        
        # Set onion skins in canvas
        self.canvas.set_onion_skin_frames(prev_frames, next_frames, prev_opacities, next_opacities)

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

        # Get layer tracks directly (new architecture)
        layer_tracks = self.layer_manager.get_layer_tracks()
        if not layer_tracks:
            return []

        palette = self._layer_track_palette()
        tracks: List[TimelineLayerTrack] = []
        
        for track_idx, track in enumerate(layer_tracks):
            states: List[int] = []
            layer_name = track.name
            
            # Determine layer timing range
            start_frame = track.start_frame if track.start_frame is not None else 0
            end_frame = track.end_frame if track.end_frame is not None else total_frames - 1
            
            for frame_idx in range(total_frames):
                # Check if frame is outside layer's timing range
                if frame_idx < start_frame or frame_idx > end_frame:
                    states.append(0)  # Layer doesn't exist in this frame
                    continue
                
                # Get layer frame data
                layer_frame = track.get_frame(frame_idx)
                if layer_frame:
                    has_pixels = self._layer_has_content_from_frame(layer_frame)
                    if not has_pixels:
                        states.append(3)  # Empty
                    else:
                        # Check effective visibility
                        visible = track.get_effective_visibility(frame_idx)
                        states.append(2 if visible else 1)  # 2 = visible, 1 = hidden
                else:
                    states.append(0)  # No frame data
            
            color = QColor(palette[track_idx % len(palette)])
            tracks.append(
                TimelineLayerTrack(
                    name=layer_name or f"Layer {track_idx + 1}",
                    states=states,
                    color=color,
                )
            )
        return tracks
    
    def _layer_has_content_from_frame(self, layer_frame) -> bool:
        """Check if layer frame has non-black pixels."""
        pixels = getattr(layer_frame, "pixels", [])
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
        self.duration_spin.blockSignals(False)
        self.timeline.set_playhead(index)
        self.history_manager.set_current_frame(index)
        
        # Update layer panel to show layers for current frame
        if hasattr(self, "layer_panel"):
            self.layer_panel.set_frame_index(index)
        
        self._load_current_frame_into_canvas()
        self._update_transport_controls()

    def _on_manager_duration_changed(self, index: int, duration: int):
        if index == self._current_frame_index:
            self._frame_duration_ms = duration
            self.duration_spin.blockSignals(True)
            self.duration_spin.setValue(duration)
            self.duration_spin.blockSignals(False)
        # Update timeline durations
        if self._pattern and index < len(self._pattern.frames):
            self._pattern.frames[index].duration_ms = duration
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
        
        # Update circular preview with grid data
        self._update_circular_preview()
    
    def _update_circular_preview(self):
        """Update circular preview with current canvas grid data."""
        if not hasattr(self, 'circular_preview'):
            return
        
        # Get grid data from canvas
        if hasattr(self.canvas, 'get_grid_data'):
            grid_data = self.canvas.get_grid_data()
            self.circular_preview.set_grid_data(grid_data)
        else:
            # Fallback: convert frame pixels to grid
            if self._pattern and self._pattern.frames and self._current_frame_index < len(self._pattern.frames):
                frame = self._pattern.frames[self._current_frame_index]
                width = self.state.width()
                height = self.state.height()
                grid_data = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        idx = y * width + x
                        if idx < len(frame.pixels):
                            row.append(frame.pixels[idx])
                        else:
                            row.append((0, 0, 0))
                    grid_data.append(row)
                self.circular_preview.set_grid_data(grid_data)

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
    
    def _on_export_sprite_sheet(self):
        """Export pattern as PNG sprite sheet."""
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
            "Export Sprite Sheet",
            "",
            "PNG Images (*.png);;All Files (*.*)"
        )
        
        if not filepath:
            return
        
        if not filepath.endswith(".png"):
            filepath += ".png"
        
        try:
            from PySide6.QtWidgets import QInputDialog
            from pathlib import Path
            
            # Ask for scale factor
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
            
            # Ask for orientation
            orientation, ok2 = QInputDialog.getItem(
                self,
                "Sprite Sheet Layout",
                "Orientation:",
                ["Horizontal", "Vertical"],
                0,
                False
            )
            
            if not ok2:
                return
            
            orientation = orientation.lower()
            
            # Ask for spacing
            spacing, ok3 = QInputDialog.getInt(
                self,
                "Frame Spacing",
                "Pixels spacing between frames:",
                0,
                0,
                100,
                1
            )
            
            if not ok3:
                return
            
            # Export sprite sheet
            from core.export.exporters import PatternExporter
            exporter = PatternExporter()
            output_path = exporter.export_sprite_sheet(
                self._pattern,
                Path(filepath),
                orientation=orientation,
                spacing=spacing,
                scale_factor=scale_factor,
                generate_manifest=False
            )
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Sprite sheet exported successfully to:\n{filepath}\n\n"
                f"Frames: {len(self._pattern.frames)}\n"
                f"Scale: {scale_factor}x\n"
                f"Layout: {orientation.capitalize()}\n"
                f"Spacing: {spacing}px"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export sprite sheet:\n\n{str(e)}"
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

    # Eyedropper tool removed - _on_color_picked handler no longer needed

    def _on_bucket_fill_tolerance_changed(self, value: int):
        """Handle bucket fill tolerance change."""
        if self.canvas:
            self.canvas.set_bucket_fill_tolerance(value)

    def _on_bucket_fill_contiguous_changed(self, checked: bool):
        """Handle bucket fill contiguous toggle."""
        if self.canvas:
            self.canvas.set_bucket_fill_contiguous(checked)

    def _on_onion_skin_toggled(self, enabled: bool):
        """Handle onion skin enable/disable."""
        self._onion_skin_enabled = enabled
        if hasattr(self, 'onion_skin_prev_count_spin'):
            self.onion_skin_prev_count_spin.setEnabled(enabled)
            self.onion_skin_next_count_spin.setEnabled(enabled)
            self.onion_skin_prev_opacity_slider.setEnabled(enabled)
            self.onion_skin_next_opacity_slider.setEnabled(enabled)
        if enabled:
            self._update_onion_skins()
        else:
            # Clear onion skins
            if self.canvas:
                self.canvas.set_onion_skin_frames([], [], [], [])

    def _on_onion_skin_settings_changed(self):
        """Handle onion skin settings change."""
        if not self._onion_skin_enabled:
            return
        
        if hasattr(self, 'onion_skin_prev_count_spin'):
            self._onion_skin_prev_count = self.onion_skin_prev_count_spin.value()
            self._onion_skin_next_count = self.onion_skin_next_count_spin.value()
            self._onion_skin_prev_opacity = self.onion_skin_prev_opacity_slider.value() / 100.0
            self._onion_skin_next_opacity = self.onion_skin_next_opacity_slider.value() / 100.0
        
        self._update_onion_skins()

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
        
        # Get frame index
        frame_index = None
        if hasattr(self, '_pattern') and self._pattern:
            try:
                frame_index = self._pattern.frames.index(frame)
            except (ValueError, AttributeError):
                frame_index = getattr(self, '_current_frame_index', None)

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

        # Update layer if using layer manager
        if frame_index is not None and hasattr(self, 'layer_manager') and self.layer_manager:
            active_layer = 0
            if hasattr(self, 'layer_panel') and self.layer_panel:
                active_layer = self.layer_panel.get_active_layer_index()
                if active_layer < 0:
                    active_layer = 0
            self.layer_manager.replace_pixels(frame_index, gradient_pixels, active_layer)
        else:
            # Fallback: update frame directly (legacy mode)
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


