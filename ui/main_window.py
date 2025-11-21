"""
Main Window - Upload Bridge Application
Complete PySide6 implementation
"""

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QMenuBar, QMenu, 
                                QStatusBar, QFileDialog, QMessageBox,
                                QToolBar, QApplication, QSplitter, QDockWidget,
                                QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
                                QPushButton, QLabel, QWidget, QComboBox)
from PySide6.QtCore import Qt, QSettings, Signal
from typing import Optional
from PySide6.QtGui import QIcon, QAction
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
import logging

from core.pattern import Pattern
from parsers.parser_registry import parse_pattern_file, ParserRegistry
from core.pattern_clipboard import PatternClipboard
from core.tab_state_manager import TabStateManager
from core.undo_redo_manager import SharedUndoRedoManager
from core.workspace_manager import WorkspaceManager
from ui.tabs.preview_tab import PreviewTab
from ui.tabs.flash_tab import FlashTab
from ui.tabs.batch_flash_tab import BatchFlashTab
from ui.tabs.pattern_library_tab import PatternLibraryTab
from ui.tabs.audio_reactive_tab import AudioReactiveTab
from ui.tabs.wifi_upload_tab import WiFiUploadTab
from ui.tabs.media_upload_tab import MediaUploadTab
from ui.tabs.arduino_ide_tab import ArduinoIDETab
from ui.tabs.design_tools_tab import DesignToolsTab
try:
    from ui.dialogs.activation_dialog import ensure_activation_or_exit, ACTIVATION_FILE
except Exception:
    ensure_activation_or_exit = None
    ACTIVATION_FILE = None
from ui.dialogs.media_import_dialog import MediaImportDialog


class UploadBridgeMainWindow(QMainWindow):
    """
    Main application window for Upload Bridge
    
    Features:
    - Tab navigation (Preview, Flash, Settings)
    - Menu bar with file operations
    - Toolbar with quick actions
    - Status bar
    - Project management
    """
    
    # Signals for cross-tab communication
    pattern_changed = Signal(Pattern)
    save_state_changed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        
        self.pattern: Pattern = None
        self.current_file: str = None
        self.is_dirty: bool = False
        self.settings = QSettings("UploadBridge", "UploadBridge")
        self.clipboard = PatternClipboard()  # Pattern clipboard manager
        self.tab_state_manager = TabStateManager(self.settings)  # Tab state persistence
        self.undo_redo_manager = SharedUndoRedoManager(max_history=50)  # Cross-tab undo/redo
        self.workspace = WorkspaceManager()  # Multi-pattern workspace
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Create UI elements"""
        self.setWindowTitle("Upload Bridge - Universal LED Pattern Flasher")
        
        # Get screen geometry and set appropriate window size
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        
        # Set window size to 80% of screen size, but with reasonable limits
        width = min(max(int(screen.width() * 0.8), 800), 1400)
        height = min(max(int(screen.height() * 0.8), 600), 1000)
        
        # Center the window
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        
        self.setGeometry(x, y, width, height)
        self.setMinimumSize(800, 600)
        
        # Ensure window is properly sized
        self.resize(width, height)
        
        # Create menus
        self.create_menus()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create workspace dock widget
        self.workspace_dock = QDockWidget("Workspace", self)
        self.workspace_dock.setObjectName("WorkspaceDock")
        workspace_widget = QWidget()
        workspace_layout = QVBoxLayout(workspace_widget)
        
        # Pattern list
        self.workspace_list = QListWidget()
        self.workspace_list.itemDoubleClicked.connect(self._on_workspace_pattern_double_clicked)
        self.workspace_list.itemSelectionChanged.connect(self._on_workspace_pattern_selected)
        workspace_layout.addWidget(QLabel("Patterns:"))
        workspace_layout.addWidget(self.workspace_list)
        
        # Workspace buttons
        workspace_buttons = QHBoxLayout()
        self.new_pattern_btn = QPushButton("New")
        self.new_pattern_btn.clicked.connect(self._new_workspace_pattern)
        workspace_buttons.addWidget(self.new_pattern_btn)
        
        self.duplicate_pattern_btn = QPushButton("Duplicate")
        self.duplicate_pattern_btn.clicked.connect(self._duplicate_workspace_pattern)
        workspace_buttons.addWidget(self.duplicate_pattern_btn)
        
        self.remove_pattern_btn = QPushButton("Remove")
        self.remove_pattern_btn.clicked.connect(self._remove_workspace_pattern)
        workspace_buttons.addWidget(self.remove_pattern_btn)
        
        workspace_layout.addLayout(workspace_buttons)
        workspace_widget.setLayout(workspace_layout)
        self.workspace_dock.setWidget(workspace_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.workspace_dock)
        self.workspace_dock.setVisible(False)  # Hidden by default, can be toggled via View menu
        
        # Connect workspace signals
        self.workspace.pattern_added.connect(self._on_workspace_pattern_added)
        self.workspace.pattern_removed.connect(self._on_workspace_pattern_removed)
        self.workspace.active_pattern_changed.connect(self._on_workspace_active_changed)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Lazy tab initialization - tabs created on first access
        self._tabs_initialized = {
            'media_upload': False,
            'design_tools': False,
            'preview': False,
            'flash': False,
            'batch_flash': False,
            'pattern_library': False,
            'audio_reactive': False,
            'wifi_upload': False,
            'arduino_ide': False
        }
        
        # Store tab references
        self.media_upload_tab = None
        self.design_tab = None
        self.preview_tab = None
        self.flash_tab = None
        self.batch_flash_tab = None
        self.pattern_library_tab = None
        self.audio_reactive_tab = None
        self.wifi_upload_tab = None
        self.arduino_ide_tab = None
        
        # Add placeholder tabs with lazy initialization
        self.tabs.addTab(self.create_placeholder_tab("🎬 Media Upload"), "🎬 Media Upload")
        self.tabs.addTab(self.create_placeholder_tab("🎨 Design Tools"), "🎨 Design Tools")
        self.tabs.addTab(self.create_placeholder_tab("👁️ Preview"), "👁️ Preview")
        self.tabs.addTab(self.create_placeholder_tab("⚡ Flash"), "⚡ Flash")
        self.tabs.addTab(self.create_placeholder_tab("🚀 Batch Flash"), "🚀 Batch Flash")
        self.tabs.addTab(self.create_placeholder_tab("📚 Pattern Library"), "📚 Pattern Library")
        self.tabs.addTab(self.create_placeholder_tab("🎵 Audio Reactive"), "🎵 Audio Reactive")
        self.tabs.addTab(self.create_placeholder_tab("📡 WiFi Upload"), "📡 WiFi Upload")
        self.tabs.addTab(self.create_placeholder_tab("🔧 Arduino IDE"), "🔧 Arduino IDE")
        
        # Connect to tab change signal for lazy initialization
        self.tabs.currentChanged.connect(self.on_tab_changed)
        # Also update undo/redo states when tab changes
        self.tabs.currentChanged.connect(lambda: self._update_undo_redo_states())
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a pattern to get started")

    def load_file(self, file_path: str):
        """Load a pattern file passed via command-line or file association.
        Supports: .bin, .dat, .leds (pattern formats)."""
        try:
            if not file_path:
                return
            lower = file_path.lower()
            if not any(lower.endswith(ext) for ext in (".bin", ".dat", ".leds", ".hex")):
                QMessageBox.information(self, "Open", f"Unsupported file type: {os.path.basename(file_path)}")
                return
            # Parse with registry to also capture format name for diagnostics
            registry = ParserRegistry()
            pattern, format_name = registry.parse_file(file_path)
            try:
                print(f"[DEBUG] Parsed {file_path} as {format_name}: leds={pattern.led_count}, frames={pattern.frame_count}, {pattern.metadata.width}x{pattern.metadata.height}")
            except Exception:
                pass
            self.load_pattern_to_all_tabs(pattern, file_path)
        except Exception as e:
            QMessageBox.critical(self, "Open", f"Failed to open {os.path.basename(file_path)}:\n{e}")
    
    def create_placeholder_tab(self, title: str):
        """Create a lightweight placeholder widget for lazy-loaded tabs"""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        label = QLabel(f"Initializing {title}...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 14px; padding: 50px;")
        layout.addWidget(label)
        return placeholder
    
    def on_tab_changed(self, index: int):
        """Handle tab change - initialize tab if not already initialized"""
        tab_names = ['media_upload', 'design_tools', 'preview', 'flash', 'batch_flash', 'pattern_library', 'audio_reactive', 'wifi_upload', 'arduino_ide']
        
        if 0 <= index < len(tab_names):
            tab_name = tab_names[index]
            
            # Initialize tab if not already initialized
            if not self._tabs_initialized[tab_name]:
                self.initialize_tab(tab_name)
    
    def initialize_tab(self, tab_name: str):
        """Initialize a specific tab (lazy loading)"""
        try:
            self.status_bar.showMessage(f"Initializing {tab_name.replace('_', ' ').title()}...")
            
            if tab_name == 'media_upload' and self.media_upload_tab is None:
                self.media_upload_tab = MediaUploadTab()
                self.tabs.removeTab(0)
                self.tabs.insertTab(0, self.media_upload_tab, "🎬 Media Upload")
                self.media_upload_tab.pattern_loaded.connect(self.load_pattern_from_media)
                self._tabs_initialized['media_upload'] = True
                
            elif tab_name == 'design_tools' and self.design_tab is None:
                self.design_tab = DesignToolsTab()
                self.tabs.removeTab(1)
                self.tabs.insertTab(1, self.design_tab, "🎨 Design Tools")
                self.design_tab.pattern_modified.connect(self.on_pattern_modified)
                self.design_tab.pattern_created.connect(self._on_design_pattern_created)
                # Connect pattern_changed signal for live updates
                self.pattern_changed.connect(self.design_tab.update_pattern)
                # Connect playback sync signals
                self._connect_playback_signals()
                self._tabs_initialized['design_tools'] = True
                
            elif tab_name == 'preview' and self.preview_tab is None:
                self.preview_tab = PreviewTab()
                self.tabs.removeTab(2)
                self.tabs.insertTab(2, self.preview_tab, "👁️ Preview")
                self.preview_tab.pattern_modified.connect(self.on_pattern_modified)
                # Connect pattern_changed signal for live preview updates
                self.pattern_changed.connect(self.preview_tab.update_pattern)
                # Connect playback sync signals (will be connected to DesignToolsTab when it's initialized)
                self._connect_playback_signals()
                self._tabs_initialized['preview'] = True
                
            elif tab_name == 'flash' and self.flash_tab is None:
                self.flash_tab = FlashTab()
                self.tabs.removeTab(3)
                self.tabs.insertTab(3, self.flash_tab, "⚡ Flash")
                self.flash_tab.flash_complete.connect(self.on_flash_complete)
                # Connect pattern_changed signal for live preview updates
                self.pattern_changed.connect(self.flash_tab.refresh_preview)
                # Connect firmware signals
                self.flash_tab.firmware_building.connect(self.on_firmware_building)
                self.flash_tab.firmware_built.connect(self.on_firmware_built)
                self._tabs_initialized['flash'] = True
                
            elif tab_name == 'batch_flash' and self.batch_flash_tab is None:
                self.batch_flash_tab = BatchFlashTab()
                self.tabs.removeTab(4)
                self.tabs.insertTab(4, self.batch_flash_tab, "🚀 Batch Flash")
                # Connect pattern_changed signal for live updates
                self.pattern_changed.connect(self.batch_flash_tab.update_pattern)
                # Connect batch flash signals
                self.batch_flash_tab.batch_flash_complete.connect(self.on_batch_flash_complete)
                self._tabs_initialized['batch_flash'] = True
                
            elif tab_name == 'pattern_library' and self.pattern_library_tab is None:
                self.pattern_library_tab = PatternLibraryTab()
                self.tabs.removeTab(5)
                self.tabs.insertTab(5, self.pattern_library_tab, "📚 Pattern Library")
                self.pattern_library_tab.pattern_selected.connect(self.on_pattern_library_selected)
                # Connect pattern_added signal for notifications
                self.pattern_library_tab.pattern_added.connect(self.on_pattern_added_to_library)
                self._tabs_initialized['pattern_library'] = True
                
            elif tab_name == 'audio_reactive' and self.audio_reactive_tab is None:
                self.audio_reactive_tab = AudioReactiveTab()
                self.tabs.removeTab(6)
                self.tabs.insertTab(6, self.audio_reactive_tab, "🎵 Audio Reactive")
                self.audio_reactive_tab.pattern_generated.connect(self.on_audio_pattern_generated)
                self._tabs_initialized['audio_reactive'] = True
                
            elif tab_name == 'wifi_upload' and self.wifi_upload_tab is None:
                self.wifi_upload_tab = WiFiUploadTab()
                self.tabs.removeTab(7)
                self.tabs.insertTab(7, self.wifi_upload_tab, "📡 WiFi Upload")
                # Connect pattern_changed signal for live preview updates
                self.pattern_changed.connect(self.wifi_upload_tab.refresh_preview)
                # Connect WiFi upload signals
                self.wifi_upload_tab.upload_started.connect(self.on_wifi_upload_started)
                self.wifi_upload_tab.upload_progress.connect(self.on_wifi_upload_progress)
                self.wifi_upload_tab.upload_complete.connect(self.on_wifi_upload_complete)
                self.wifi_upload_tab.brightness_changed.connect(self.on_brightness_changed)
                self.wifi_upload_tab.schedule_updated.connect(self.on_schedule_updated)
                self._tabs_initialized['wifi_upload'] = True
                
            elif tab_name == 'arduino_ide' and self.arduino_ide_tab is None:
                self.arduino_ide_tab = ArduinoIDETab()
                self.tabs.removeTab(8)
                self.tabs.insertTab(8, self.arduino_ide_tab, "🔧 Arduino IDE")
                # Connect code generation signal
                if hasattr(self.arduino_ide_tab, 'code_generated'):
                    self.arduino_ide_tab.code_generated.connect(self.on_code_generated)
                self._tabs_initialized['arduino_ide'] = True
            
            # Get the tab reference (already initialized above)
            tab = None
            if tab_name == 'media_upload':
                tab = self.media_upload_tab
            elif tab_name == 'design_tools':
                tab = self.design_tab
            elif tab_name == 'preview':
                tab = self.preview_tab
            elif tab_name == 'flash':
                tab = self.flash_tab
            elif tab_name == 'batch_flash':
                tab = self.batch_flash_tab
            elif tab_name == 'pattern_library':
                tab = self.pattern_library_tab
            elif tab_name == 'audio_reactive':
                tab = self.audio_reactive_tab
            elif tab_name == 'wifi_upload':
                tab = self.wifi_upload_tab
            elif tab_name == 'arduino_ide':
                tab = self.arduino_ide_tab
            
            # Load pattern if one is already loaded (avoid recursion by calling load_pattern directly)
            if self.pattern and tab and hasattr(tab, 'load_pattern'):
                try:
                    tab.load_pattern(self.pattern, self.current_file)
                except Exception:
                    pass  # Tab may not support load_pattern
            
            # Restore tab state
            if tab:
                self._restore_tab_state(tab_name, tab)
                
            self.status_bar.showMessage("Ready")
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Tab Initialization Error",
                f"Failed to initialize {tab_name} tab:\n{str(e)}"
            )
            self.status_bar.showMessage("Tab initialization failed")
    
    def _connect_playback_signals(self):
        """Connect playback synchronization signals between PreviewTab and DesignToolsTab"""
        if self.preview_tab and self.design_tab:
            # Connect PreviewTab → DesignToolsTab
            if not hasattr(self, '_playback_signals_connected'):
                self.preview_tab.playback_state_changed.connect(self.design_tab.sync_playback_state)
                self.preview_tab.frame_changed.connect(self.design_tab.sync_frame_selection)
                # Connect DesignToolsTab → PreviewTab
                self.design_tab.playback_state_changed.connect(self.preview_tab.sync_playback_state)
                self.design_tab.frame_changed.connect(self.preview_tab.sync_frame_selection)
                self._playback_signals_connected = True
    
    def get_tab(self, tab_name: str):
        """Get a tab, initializing it if necessary"""
        tab_map = {
            'media_upload': (self.media_upload_tab, 'media_upload'),
            'design_tools': (self.design_tab, 'design_tools'),
            'preview': (self.preview_tab, 'preview'),
            'flash': (self.flash_tab, 'flash'),
            'batch_flash': (self.batch_flash_tab, 'batch_flash'),
            'pattern_library': (self.pattern_library_tab, 'pattern_library'),
            'audio_reactive': (self.audio_reactive_tab, 'audio_reactive'),
            'wifi_upload': (self.wifi_upload_tab, 'wifi_upload'),
            'arduino_ide': (self.arduino_ide_tab, 'arduino_ide')
        }
        
        if tab_name in tab_map:
            tab, key = tab_map[tab_name]
            if tab is None or not self._tabs_initialized[key]:
                self.initialize_tab(key)
                return tab_map[tab_name][0]
            return tab
        
        return None
    
    def load_pattern_to_tab(self, tab_name: str, pattern: Pattern, file_path: str = None):
        """Load pattern to a specific tab"""
        tab = self.get_tab(tab_name)
        if tab:
            if hasattr(tab, 'load_pattern'):
                try:
                    tab.load_pattern(pattern, file_path)
                except Exception as e:
                    logging.getLogger(__name__).warning("Failed to load pattern to %s: %s", tab_name, e)
            elif hasattr(tab, 'set_pattern'):
                try:
                    tab.set_pattern(pattern)
                except Exception as e:
                    logging.getLogger(__name__).warning("Failed to set pattern to %s: %s", tab_name, e)
    
    def switch_to_tab(self, tab_name: str):
        """Switch to a tab, initializing it if necessary"""
        tab = self.get_tab(tab_name)
        if tab:
            index = self.tabs.indexOf(tab)
            if index >= 0:
                self.tabs.setCurrentIndex(index)
    
    def refresh_ports(self):
        """Refresh serial ports (lazy initialization)"""
        flash_tab = self.get_tab('flash')
        if flash_tab and hasattr(flash_tab, 'refresh_ports'):
            flash_tab.refresh_ports()
        else:
            QMessageBox.information(
                self,
                "Refresh Ports",
                "Flash tab must be initialized first. Please switch to the Flash tab."
            )
    
    def apply_responsive_styling(self):
        """Apply responsive styling based on screen size"""
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Determine styling based on screen size
        if screen_width >= 1920 and screen_height >= 1080:
            font_size = 12
            tab_padding = "10px 20px"
            margin = 15
        elif screen_width >= 1366 and screen_height >= 768:
            font_size = 11
            tab_padding = "8px 16px"
            margin = 12
        else:
            font_size = 10
            tab_padding = "6px 12px"
            margin = 10
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #2b2b2b;
                font-size: {font_size}px;
            }}
            QTabWidget::pane {{
                border: 1px solid #3d3d3d;
                background-color: #2b2b2b;
            }}
            QTabBar::tab {{
                background-color: #3d3d3d;
                color: #ffffff;
                padding: {tab_padding};
                margin-right: 2px;
                border-radius: 4px 4px 0 0;
            }}
            QTabBar::tab:selected {{
                background-color: #4CAF50;
            }}
            QTabBar::tab:hover {{
                background-color: #5a5a5a;
            }}
            QGroupBox {{
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                margin-top: {margin}px;
                padding-top: {margin}px;
                color: #ffffff;
                background-color: #3b3b3b;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00ff88;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: {font_size}px;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QPushButton:pressed {{
                background-color: #3d8b40;
            }}
            QPushButton:disabled {{
                background-color: #666666;
                color: #999999;
            }}
            QLineEdit {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: {font_size}px;
            }}
            QLineEdit:focus {{
                border: 2px solid #4CAF50;
            }}
            QComboBox {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: {font_size}px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                selection-background-color: #4CAF50;
            }}
            QSpinBox {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: {font_size}px;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #555555;
                height: 8px;
                background: #3d3d3d;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #4CAF50;
                border: 1px solid #555555;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #45a049;
            }}
            QProgressBar {{
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
                background-color: #3d3d3d;
                font-size: {font_size}px;
            }}
            QProgressBar::chunk {{
                background-color: #4CAF50;
                border-radius: 3px;
            }}
            QTextEdit {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: {font_size}px;
            }}
            QLabel {{
                color: #ffffff;
                font-size: {font_size}px;
            }}
            QMenuBar {{
                background-color: #3d3d3d;
                color: #ffffff;
                border-bottom: 1px solid #555555;
                font-size: {font_size}px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background-color: #4CAF50;
            }}
            QMenu {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                font-size: {font_size}px;
            }}
            QMenu::item:selected {{
                background-color: #4CAF50;
            }}
            QStatusBar {{
                background-color: #3d3d3d;
                color: #ffffff;
                border-top: 1px solid #555555;
                font-size: {font_size}px;
            }}
            QToolBar {{
                background-color: #3d3d3d;
                border: 1px solid #555555;
                spacing: 3px;
            }}
            QToolBar::separator {{
                background-color: #555555;
                width: 1px;
                margin: 4px;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: #3b3b3b;
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #5a5a5a;
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #7a7a7a;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar:horizontal {{
                background-color: #3b3b3b;
                height: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #5a5a5a;
                border-radius: 6px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: #7a7a7a;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
        """)
    
    def create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Pattern...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pattern)
        file_menu.addAction(open_action)
        
        save_project_action = QAction("&Save Project", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)
        
        save_project_as_action = QAction("Save Project &As...", self)
        save_project_as_action.setShortcut("Ctrl+Shift+S")
        save_project_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_project_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        copy_pattern_action = QAction("Copy &Pattern", self)
        copy_pattern_action.setShortcut("Ctrl+C")
        copy_pattern_action.triggered.connect(self.copy_pattern)
        edit_menu.addAction(copy_pattern_action)
        
        paste_pattern_action = QAction("&Paste Pattern", self)
        paste_pattern_action.setShortcut("Ctrl+V")
        paste_pattern_action.triggered.connect(self.paste_pattern)
        edit_menu.addAction(paste_pattern_action)
        
        # Update paste action state based on clipboard
        self.clipboard.clipboard_changed.connect(lambda has_pattern: paste_pattern_action.setEnabled(has_pattern))
        paste_pattern_action.setEnabled(self.clipboard.has_pattern())
        
        edit_menu.addSeparator()
        
        # Undo/Redo actions
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_action)
        edit_menu.addAction(undo_action)
        self.undo_action = undo_action  # Store reference for state updates
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_action)
        edit_menu.addAction(redo_action)
        self.redo_action = redo_action  # Store reference for state updates
        
        # Connect undo/redo manager signals to update menu states
        self.undo_redo_manager.undo_available_changed.connect(self._on_undo_available_changed)
        self.undo_redo_manager.redo_available_changed.connect(self._on_redo_available_changed)
        
        # Initialize menu states
        self._update_undo_redo_states()
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_workspace_action = QAction("&Workspace", self)
        toggle_workspace_action.setCheckable(True)
        toggle_workspace_action.setChecked(False)
        toggle_workspace_action.triggered.connect(lambda checked: self.workspace_dock.setVisible(checked))
        view_menu.addAction(toggle_workspace_action)
        
        # Add workspace actions to File menu
        file_menu.insertSeparator(file_menu.actions()[-1])  # Before Exit
        
        new_pattern_action = QAction("&New Pattern", self)
        new_pattern_action.setShortcut("Ctrl+N")
        new_pattern_action.triggered.connect(self._new_workspace_pattern)
        file_menu.insertAction(file_menu.actions()[-1], new_pattern_action)
        
        duplicate_pattern_action = QAction("&Duplicate Pattern", self)
        duplicate_pattern_action.setShortcut("Ctrl+Shift+D")
        duplicate_pattern_action.triggered.connect(self._duplicate_workspace_pattern)
        file_menu.insertAction(file_menu.actions()[-1], duplicate_pattern_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        refresh_ports_action = QAction("&Refresh Ports", self)
        refresh_ports_action.setShortcut("F5")
        refresh_ports_action.triggered.connect(self.refresh_ports)
        tools_menu.addAction(refresh_ports_action)

        # Force dimensions (manual override)
        force_dims_action = QAction("Force Dimensions...", self)
        force_dims_action.setShortcut("Ctrl+D")
        force_dims_action.triggered.connect(self.force_dimensions_override)
        tools_menu.addAction(force_dims_action)
        
        # License menu
        license_menu = menubar.addMenu("&License")
        
        activate_license_action = QAction("🔐 &Activate / Manage License...", self)
        activate_license_action.triggered.connect(self.show_license_activation)
        license_menu.addAction(activate_license_action)

        deactivate_action = QAction("🔓 &Deactivate (this device)", self)
        deactivate_action.triggered.connect(self.deactivate_license)
        license_menu.addAction(deactivate_action)
        
        license_status_action = QAction("📊 License &Status", self)
        license_status_action.triggered.connect(self.show_license_status)
        license_menu.addAction(license_status_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(self.show_docs)
        help_menu.addAction(docs_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Open button
        open_btn = QAction("📁 Open", self)
        open_btn.triggered.connect(self.open_pattern)
        toolbar.addAction(open_btn)
        
        toolbar.addSeparator()
        
        # Pattern switcher
        toolbar.addWidget(QLabel("Pattern:"))
        self.pattern_switcher = QComboBox()
        self.pattern_switcher.setMinimumWidth(150)
        self.pattern_switcher.currentTextChanged.connect(self._on_pattern_switcher_changed)
        toolbar.addWidget(self.pattern_switcher)
        
        # Connect workspace signals to update switcher
        self.workspace.pattern_added.connect(self._update_pattern_switcher)
        self.workspace.pattern_removed.connect(self._update_pattern_switcher)
        self.workspace.active_pattern_changed.connect(self._update_pattern_switcher)
        
        toolbar.addSeparator()
        
        # Preview button
        preview_btn = QAction("👁️ Preview", self)
        preview_btn.triggered.connect(lambda: self.switch_to_tab('preview'))
        toolbar.addAction(preview_btn)
        
        # Flash button
        flash_btn = QAction("⚡ Flash", self)
        flash_btn.triggered.connect(lambda: self.switch_to_tab('flash'))
        toolbar.addAction(flash_btn)
    
    def open_pattern(self):
        """Open pattern file or media file dialog"""
        # Check if already loading
        if hasattr(self, '_is_loading') and self._is_loading:
            QMessageBox.information(
                self,
                "Loading in Progress",
                "A file is currently being loaded. Please wait for it to complete."
            )
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Pattern or Media File",
            self.settings.value("last_directory", ""),
            "All Supported (*.bin *.hex *.dat *.leds *.ledadmin *.ledproj *.mp4 *.avi *.mov *.mkv *.webm *.gif *.jpg *.jpeg *.png *.bmp);;"
            "Pattern Files (*.bin *.hex *.dat *.leds);;"
            "Media Files (*.mp4 *.avi *.mov *.mkv *.webm *.gif *.jpg *.jpeg *.png *.bmp);;"
            "Project Files (*.ledproj);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        # Check if pattern is modified and warn user
        if self.is_dirty and self.pattern:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes to the current pattern.\n\n"
                "Do you want to save before opening a new file?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Save:
                self.save_project()
        
        # Check file size and warn if large
        import os
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 10:
            reply = QMessageBox.question(
                self,
                "Large File Warning",
                f"This file is large ({file_size_mb:.1f} MB).\n\n"
                "Loading may take some time and use significant memory.\n\n"
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.No:
                return
        
        # Set loading flag
        self._is_loading = True
        
        # Save directory
        self.settings.setValue("last_directory", os.path.dirname(file_path))
        
        # Check if it's a media file
        media_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.gif', '.jpg', '.jpeg', '.png', '.bmp']
        is_media_file = any(file_path.lower().endswith(ext) for ext in media_extensions)
        
        # Load pattern
        try:
            self.status_bar.showMessage(f"Loading {os.path.basename(file_path)}...")
            
            if is_media_file:
                # Show importing dialog (non-blocking UI) with progress
                width_default = 64
                height_default = 32
                fps_default = 20.0
                dlg = MediaImportDialog(self, file_path, width_default, height_default, fps_default)
                if dlg.exec():
                    pattern = dlg.result_pattern()
                    if pattern:
                        self.status_bar.showMessage(f"Converted media: {pattern.name}")
                        self.load_pattern_to_all_tabs(pattern, file_path)
                    else:
                        self.status_bar.showMessage("Media conversion cancelled")
                else:
                    self.status_bar.showMessage("Media import cancelled")
                
            elif file_path.endswith('.ledproj'):
                pattern = Pattern.load_from_file(file_path)
                try:
                    pattern.metadata.source_format = "project"
                    pattern.metadata.source_path = file_path
                except Exception:
                    pass
                self.status_bar.showMessage(f"Loaded project: {pattern.name}")
                
                # Load into ALL tabs
                self.load_pattern_to_all_tabs(pattern, file_path)
            else:
                # Ask for LED and frame count if needed
                from PySide6.QtWidgets import QInputDialog
                
                # Try auto-detection first
                from parsers.parser_registry import ParserRegistry
                registry = ParserRegistry()
                
                is_valid, message, info = registry.validate_file(file_path)
                
                if is_valid:
                    # Always parse using the registry to also know which parser was used
                    pattern, format_name = registry.parse_file(file_path)
                    try:
                        pattern.metadata.source_format = format_name
                        pattern.metadata.source_path = file_path
                    except Exception:
                        pass
                    self.status_bar.showMessage(
                        f"Loaded ({format_name}): {pattern.led_count} LEDs, {pattern.frame_count} frames")
                    # Load into ALL tabs
                    self.load_pattern_to_all_tabs(pattern, file_path)
                else:
                    # Need manual input
                    led_count, ok1 = QInputDialog.getInt(
                        self, "LED Count", 
                        "Enter number of LEDs:",
                        76, 1, 10000, 1
                    )
                    
                    if not ok1:
                        return
                    
                    frame_count, ok2 = QInputDialog.getInt(
                        self, "Frame Count",
                        "Enter number of frames:",
                        400, 1, 100000, 1
                    )
                    
                    if not ok2:
                        return
                    
                    pattern = parse_pattern_file(file_path, led_count, frame_count)
                    try:
                        pattern.metadata.source_format = "manual"
                        pattern.metadata.source_path = file_path
                        pattern.metadata.dimension_source = "manual"
                        pattern.metadata.dimension_confidence = 1.0
                    except Exception:
                        pass
                    self.status_bar.showMessage(f"Loaded: {led_count} LEDs, {frame_count} frames")
                    
                    # Load into ALL tabs
                    self.load_pattern_to_all_tabs(pattern, file_path)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load file:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Load failed")
        finally:
            # Clear loading flag
            if hasattr(self, '_is_loading'):
                self._is_loading = False

    def force_dimensions_override(self):
        """Allow user to force width/height and frames for current file and reload."""
        try:
            if not self.current_file or not os.path.exists(self.current_file):
                QMessageBox.information(self, "Force Dimensions", "Open a pattern file first.")
                return
            from PySide6.QtWidgets import QInputDialog
            # Pre-fill from current pattern if available
            cur_w = self.pattern.metadata.width if self.pattern else 72
            cur_h = self.pattern.metadata.height if self.pattern else 1
            cur_frames = self.pattern.frame_count if self.pattern else 18
            w, ok1 = QInputDialog.getInt(self, "Width", "LEDs wide:", int(cur_w), 1, 10000, 1)
            if not ok1: return
            h, ok2 = QInputDialog.getInt(self, "Height", "LEDs high:", int(cur_h), 1, 10000, 1)
            if not ok2: return
            fcount, ok3 = QInputDialog.getInt(self, "Frames", "Frame count:", int(cur_frames), 1, 100000, 1)
            if not ok3: return
            # Reload with suggested values
            from parsers.parser_registry import ParserRegistry
            registry = ParserRegistry()
            leds = int(w) * int(h)
            pattern, format_name = registry.parse_file(self.current_file, suggested_leds=leds, suggested_frames=int(fcount))
            try:
                pattern.metadata.source_format = format_name
                pattern.metadata.source_path = self.current_file
            except Exception:
                pass
            # Ensure metadata matches grid
            try:
                pattern.metadata.width = int(w)
                pattern.metadata.height = int(h)
            except Exception:
                pass
            self.status_bar.showMessage(f"Loaded (override): {pattern.led_count} LEDs, {pattern.frame_count} frames, {w}x{h}")
            self.load_pattern_to_all_tabs(pattern, self.current_file)
        except Exception as e:
            QMessageBox.critical(self, "Force Dimensions", f"Failed to apply override:\n{e}")
    
    def save_project(self):
        """Save current project"""
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern", "No pattern to save!")
            return
        
        if self.current_file and self.current_file.endswith('.ledproj'):
            # Save to existing project file
            try:
                old_dirty = self.is_dirty
                self.pattern.save_to_file(self.current_file)
                self.is_dirty = False  # Clear dirty flag after save
                self.status_bar.showMessage(f"Saved: {self.current_file}")
                # Remove * from window title
                base_name = os.path.basename(self.current_file)
                self.setWindowTitle(f"Upload Bridge - {base_name}")
                QMessageBox.information(self, "Saved", "Project saved successfully!")
                # Emit save state change
                if old_dirty != self.is_dirty:
                    self.save_state_changed.emit(self.is_dirty)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save:\n\n{str(e)}")
        else:
            # Save as new project
            self.save_project_as()
    
    def save_project_as(self):
        """Save project as new file"""
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern", "No pattern to save!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            self.settings.value("last_directory", ""),
            "LED Project (*.ledproj)"
        )
        
        if not file_path:
            return
        
        try:
            old_dirty = self.is_dirty
            self.pattern.save_to_file(file_path)
            self.current_file = file_path
            self.is_dirty = False  # Clear dirty flag after save
            self.status_bar.showMessage(f"Saved: {file_path}")
            # Update window title
            base_name = os.path.basename(file_path)
            self.setWindowTitle(f"Upload Bridge - {base_name}")
            QMessageBox.information(self, "Saved", "Project saved successfully!")
            # Emit save state change
            if old_dirty != self.is_dirty:
                self.save_state_changed.emit(self.is_dirty)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n\n{str(e)}")
    
    def on_pattern_modified(self):
        """Pattern was modified in preview"""
        old_dirty = self.is_dirty
        self.is_dirty = True
        self.status_bar.showMessage("Pattern modified")
        # Update window title to show unsaved changes
        if self.current_file:
            base_name = os.path.basename(self.current_file)
            if not self.windowTitle().endswith('*'):
                self.setWindowTitle(f"Upload Bridge - {base_name} *")
        # Emit signals for cross-tab synchronization
        if self.pattern:
            self.pattern_changed.emit(self.pattern)
        if old_dirty != self.is_dirty:
            self.save_state_changed.emit(self.is_dirty)
    
    def on_flash_complete(self, success: bool, message: str):
        """Flash operation completed"""
        if success:
            self.status_bar.showMessage("✅ Flash successful!")
        else:
            self.status_bar.showMessage("❌ Flash failed")
    
    def on_firmware_building(self):
        """Firmware build started"""
        self.status_bar.showMessage("Building firmware...")
    
    def on_firmware_built(self, firmware_path: str):
        """Firmware build completed - share with BatchFlashTab if available"""
        self.status_bar.showMessage(f"Firmware built: {os.path.basename(firmware_path)}")
        # Share firmware with BatchFlashTab if it exists
        if self.batch_flash_tab and hasattr(self.batch_flash_tab, 'use_firmware'):
            try:
                self.batch_flash_tab.use_firmware(firmware_path)
            except Exception as e:
                logging.getLogger(__name__).warning("Failed to share firmware with BatchFlashTab: %s", e)
    
    def on_batch_flash_complete(self, results: dict):
        """Batch flash operation completed"""
        # results format: {port: (success, message), ...}
        total = len(results)
        successful = sum(1 for success, _ in results.values() if success)
        failed = total - successful
        
        message = f"Batch flash complete: {successful}/{total} successful"
        if failed > 0:
            message += f", {failed} failed"
        
        self.status_bar.showMessage(message)
        
        # Show summary dialog
        summary_text = f"Batch Flash Summary:\n\n"
        summary_text += f"Total: {total}\n"
        summary_text += f"Successful: {successful}\n"
        summary_text += f"Failed: {failed}\n\n"
        summary_text += "Details:\n"
        for port, (success, msg) in results.items():
            status = "✅" if success else "❌"
            summary_text += f"{status} {port}: {msg}\n"
        
        QMessageBox.information(self, "Batch Flash Complete", summary_text)
    
    def on_wifi_upload_started(self):
        """WiFi upload started"""
        self.status_bar.showMessage("Uploading pattern over WiFi...")
    
    def on_wifi_upload_progress(self, percent: int):
        """WiFi upload progress update"""
        self.status_bar.showMessage(f"Uploading pattern over WiFi... {percent}%")
    
    def on_wifi_upload_complete(self, success: bool, message: str):
        """WiFi upload completed"""
        if success:
            self.status_bar.showMessage(f"✅ WiFi upload successful: {message}")
        else:
            self.status_bar.showMessage(f"❌ WiFi upload failed: {message}")
    
    def on_brightness_changed(self, value: int):
        """Brightness changed on WiFi device"""
        self.status_bar.showMessage(f"Brightness set to {value}/255")
    
    def on_schedule_updated(self, schedule: dict):
        """Schedule updated on WiFi device"""
        self.status_bar.showMessage("Schedule updated on WiFi device")
    
    def on_code_generated(self, code: str, file_path: str):
        """Arduino code generated"""
        self.status_bar.showMessage(f"Code generated: {os.path.basename(file_path)}")
        # Optionally open in Arduino IDE
        reply = QMessageBox.question(
            self,
            "Code Generated",
            f"Code has been generated and saved to:\n{file_path}\n\nOpen in Arduino IDE?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                import subprocess
                import platform
                if platform.system() == "Windows":
                    subprocess.Popen(["arduino", file_path], shell=True)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", "-a", "Arduino", file_path])
                else:  # Linux
                    subprocess.Popen(["arduino", file_path])
            except Exception as e:
                QMessageBox.warning(self, "Open Failed", f"Could not open Arduino IDE:\n{e}")
    
    def _offer_add_to_library(self, pattern: Pattern, source: str):
        """Offer to add pattern to library after creation"""
        reply = QMessageBox.question(
            self,
            "Add to Pattern Library?",
            f"Pattern '{pattern.name}' was created from {source}.\n\n"
            "Would you like to add it to your Pattern Library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                pattern_library_tab = self.get_tab('pattern_library')
                if pattern_library_tab and hasattr(pattern_library_tab, 'add_pattern_programmatic'):
                    pattern_library_tab.add_pattern_programmatic(
                        pattern,
                        file_path=None,
                        category="Uncategorized",
                        tags=[],
                        description=f"Created from {source}",
                        author=""
                    )
                    self.status_bar.showMessage(f"Pattern '{pattern.name}' added to library")
                else:
                    QMessageBox.warning(
                        self,
                        "Library Unavailable",
                        "Pattern Library tab is not available. Please try again later."
                    )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Add to Library Failed",
                    f"Failed to add pattern to library:\n{str(e)}"
                )
                logging.getLogger(__name__).error("Failed to add pattern to library: %s", e, exc_info=True)
    
    def on_pattern_added_to_library(self, pattern: Pattern):
        """Handle pattern added to library notification"""
        self.status_bar.showMessage(f"Pattern '{pattern.name}' added to library")
    
    def copy_pattern(self):
        """Copy current pattern to clipboard"""
        if self.pattern:
            self.clipboard.copy_pattern(self.pattern)
            self.status_bar.showMessage(f"Pattern '{self.pattern.name}' copied to clipboard")
        else:
            QMessageBox.information(self, "No Pattern", "No pattern loaded to copy.")
    
    def paste_pattern(self):
        """Paste pattern from clipboard"""
        if not self.clipboard.has_pattern():
            QMessageBox.information(self, "Clipboard Empty", "No pattern in clipboard.")
            return
        
        pattern = self.clipboard.paste_pattern()
        if pattern:
            # Ask user if they want to replace current pattern
            if self.pattern and self.is_dirty:
                reply = QMessageBox.question(
                    self,
                    "Replace Pattern?",
                    "You have unsaved changes. Replace current pattern with clipboard pattern?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            self.load_pattern_to_all_tabs(pattern, None)
            self.is_dirty = True
            self.status_bar.showMessage(f"Pattern '{pattern.name}' pasted from clipboard")
        else:
            QMessageBox.warning(self, "Paste Failed", "Failed to paste pattern from clipboard.")
    
    def undo_action(self):
        """Undo last action in current tab"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            tab_name = self._get_tab_name(current_tab)
            if tab_name and self.undo_redo_manager.can_undo(tab_name):
                self.undo_redo_manager.undo(tab_name)
                self.status_bar.showMessage("Undo")
            else:
                # Try design_tools tab (most common for undo)
                if self.design_tab and hasattr(self.design_tab, 'history_manager'):
                    # Use design tab's internal undo if available
                    if hasattr(self.design_tab.history_manager, 'undo'):
                        self.design_tab.history_manager.undo()
                        self.status_bar.showMessage("Undo")
    
    def redo_action(self):
        """Redo last undone action in current tab"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            tab_name = self._get_tab_name(current_tab)
            if tab_name and self.undo_redo_manager.can_redo(tab_name):
                self.undo_redo_manager.redo(tab_name)
                self.status_bar.showMessage("Redo")
            else:
                # Try design_tools tab (most common for redo)
                if self.design_tab and hasattr(self.design_tab, 'history_manager'):
                    # Use design tab's internal redo if available
                    if hasattr(self.design_tab.history_manager, 'redo'):
                        self.design_tab.history_manager.redo()
                        self.status_bar.showMessage("Redo")
    
    def _get_tab_name(self, tab_widget) -> Optional[str]:
        """Get tab name from widget"""
        tab_map = {
            self.media_upload_tab: 'media_upload',
            self.design_tab: 'design_tools',
            self.preview_tab: 'preview',
            self.flash_tab: 'flash',
            self.batch_flash_tab: 'batch_flash',
            self.pattern_library_tab: 'pattern_library',
            self.audio_reactive_tab: 'audio_reactive',
            self.wifi_upload_tab: 'wifi_upload',
            self.arduino_ide_tab: 'arduino_ide',
        }
        return tab_map.get(tab_widget)
    
    def _on_undo_available_changed(self, tab_name: str, available: bool):
        """Handle undo availability change"""
        # Update menu if current tab matches
        current_tab = self.tabs.currentWidget()
        current_tab_name = self._get_tab_name(current_tab)
        if current_tab_name == tab_name:
            self._update_undo_redo_states()
    
    def _on_redo_available_changed(self, tab_name: str, available: bool):
        """Handle redo availability change"""
        # Update menu if current tab matches
        current_tab = self.tabs.currentWidget()
        current_tab_name = self._get_tab_name(current_tab)
        if current_tab_name == tab_name:
            self._update_undo_redo_states()
    
    def _update_undo_redo_states(self):
        """Update undo/redo menu item states based on current tab"""
        if not hasattr(self, 'tabs') or not self.tabs:
            if hasattr(self, 'undo_action'):
                self.undo_action.setEnabled(False)
            if hasattr(self, 'redo_action'):
                self.redo_action.setEnabled(False)
            return
        
        current_tab = self.tabs.currentWidget()
        if not current_tab:
            if hasattr(self, 'undo_action'):
                self.undo_action.setEnabled(False)
            if hasattr(self, 'redo_action'):
                self.redo_action.setEnabled(False)
            return
        
        tab_name = self._get_tab_name(current_tab)
        if tab_name:
            can_undo = self.undo_redo_manager.can_undo(tab_name)
            can_redo = self.undo_redo_manager.can_redo(tab_name)
            
            # Also check design_tools internal history
            if tab_name == 'design_tools' and self.design_tab:
                if hasattr(self.design_tab, 'history_manager'):
                    if hasattr(self.design_tab.history_manager, 'can_undo'):
                        can_undo = can_undo or self.design_tab.history_manager.can_undo()
                    if hasattr(self.design_tab.history_manager, 'can_redo'):
                        can_redo = can_redo or self.design_tab.history_manager.can_redo()
            
            self.undo_action.setEnabled(can_undo)
            self.redo_action.setEnabled(can_redo)
        else:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)
    
    def on_pattern_library_selected(self, pattern: Pattern, file_path: str):
        """Handle pattern selection from library"""
        self.load_pattern_to_all_tabs(pattern, file_path)
    
    def on_audio_pattern_generated(self, pattern: Pattern):
        """Handle audio-reactive pattern generation"""
        self.load_pattern_to_all_tabs(pattern, None)
        # Offer to add to library
        self._offer_add_to_library(pattern, "audio reactive")
    
    def load_pattern_to_all_tabs(self, pattern: Pattern, file_path: str = None):
        """Load pattern into all relevant tabs with error recovery (lazy initialization)"""
        # Store pattern first (so it's available even if tabs fail)
        old_dirty = self.is_dirty
        self.pattern = pattern
        if file_path:
            self.current_file = file_path
        self.is_dirty = False  # Reset dirty flag on load
        
        # Load into ALL tabs with error recovery (tabs will be initialized on access)
        tabs_loaded = []
        tabs_failed = []
        
        # Preview Tab (initialize and load)
        try:
            preview = self.get_tab('preview')
            if preview and hasattr(preview, 'load_pattern'):
                preview.load_pattern(pattern)
                tabs_loaded.append("Preview")
        except Exception as e:
            tabs_failed.append(f"Preview: {str(e)}")
            logging.getLogger(__name__).error("Preview tab load failed: %s", e, exc_info=True)
            # Show error to user
            QMessageBox.warning(
                self,
                "Preview Load Failed",
                f"Failed to load pattern in preview:\n{str(e)}\n\nCheck console for details."
            )
        
        # Design Tools Tab (initialize and load)
        try:
            design_tab = self.get_tab('design_tools')
            if design_tab and hasattr(design_tab, 'load_pattern'):
                design_tab.load_pattern(pattern, file_path)
                tabs_loaded.append("Design Tools")
        except Exception as e:
            tabs_failed.append(f"Design Tools: {str(e)}")
            logging.getLogger(__name__).warning("Design Tools tab load failed: %s", e, exc_info=True)
        
        # Flash Tab (initialize and load)
        try:
            flash = self.get_tab('flash')
            if flash and hasattr(flash, 'load_pattern'):
                flash.load_pattern(pattern)
                tabs_loaded.append("Flash")
        except Exception as e:
            tabs_failed.append(f"Flash: {str(e)}")
            logging.getLogger(__name__).warning("Flash tab load failed: %s", e)
        
        # Batch Flash Tab (initialize and load)
        try:
            batch_flash = self.get_tab('batch_flash')
            if batch_flash and hasattr(batch_flash, 'load_pattern'):
                batch_flash.load_pattern(pattern)
                tabs_loaded.append("Batch Flash")
        except Exception as e:
            tabs_failed.append(f"Batch Flash: {str(e)}")
            logging.getLogger(__name__).warning("Batch Flash tab load failed: %s", e)
        
        # WiFi Upload Tab (initialize and load)
        try:
            wifi = self.get_tab('wifi_upload')
            if wifi and hasattr(wifi, 'set_pattern'):
                wifi.set_pattern(pattern)
                tabs_loaded.append("WiFi Upload")
        except Exception as e:
            tabs_failed.append(f"WiFi Upload: {str(e)}")
            logging.getLogger(__name__).warning("WiFi Upload tab load failed: %s", e)
        
        # Pattern Library Tab (initialize and load - for awareness, not active loading)
        try:
            pattern_library = self.get_tab('pattern_library')
            # Pattern library doesn't need to load the pattern, but we ensure it's aware
            # The library is for browsing, not displaying patterns
            tabs_loaded.append("Pattern Library")
        except Exception as e:
            tabs_failed.append(f"Pattern Library: {str(e)}")
            logging.getLogger(__name__).warning("Pattern Library tab load failed: %s", e)
        
        # Report if any tabs failed
        if tabs_failed:
            self.status_bar.showMessage(
                f"Pattern loaded to {len(tabs_loaded)}/{len(tabs_loaded) + len(tabs_failed)} tabs. "
                f"Some tabs failed to load."
            )
        
        # Switch to preview tab to show the result (will auto-initialize if needed)
        preview_tab = self.get_tab('preview')
        if preview_tab:
            self.tabs.setCurrentWidget(preview_tab)
        else:
            design_tab = self.get_tab('design_tools')
            if design_tab:
                self.tabs.setCurrentWidget(design_tab)
        
        # Update window title
        if file_path:
            self.setWindowTitle(f"Upload Bridge - {os.path.basename(file_path)}")
        else:
            self.setWindowTitle(f"Upload Bridge - {pattern.name}")
        
        # Show success message
        pattern_info = f"Name: {pattern.name}\n"
        pattern_info += f"Dimensions: {pattern.metadata.width}x{pattern.metadata.height}\n"
        pattern_info += f"Frames: {pattern.frame_count}\n"
        if pattern.metadata.total_ms:
            pattern_info += f"Duration: {(pattern.metadata.total_ms / 1000.0):.2f}s\n"
        if pattern.metadata.fps:
            pattern_info += f"FPS: {pattern.metadata.fps:.1f}"
        
        QMessageBox.information(
            self,
            "Pattern Loaded",
            f"Successfully loaded pattern:\n\n{pattern_info}"
        )
        
        # Emit signals for cross-tab synchronization
        self.pattern_changed.emit(pattern)
        if old_dirty != self.is_dirty:
            self.save_state_changed.emit(self.is_dirty)

    def _on_design_pattern_created(self, pattern: Pattern):
        """Handle pattern exports from design tab."""
        # When design tools emits a pattern, load it everywhere.
        self.load_pattern_to_all_tabs(pattern, None)
        # Offer to add to library
        self._offer_add_to_library(pattern, "design tools")
    
    def load_pattern_from_media(self, pattern: Pattern):
        """Load pattern created from media conversion"""
        # Use the unified loading method
        self.load_pattern_to_all_tabs(pattern, None)
        self.is_dirty = True  # Media patterns are unsaved
        self.status_bar.showMessage(f"Pattern loaded from media: {pattern.name}")
        # Offer to add to library
        self._offer_add_to_library(pattern, "media upload")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Upload Bridge v3.0</h2>
        <p><b>Universal LED Pattern Flasher</b></p>
        <p>A professional tool for flashing LED animation patterns to microcontrollers.</p>
        
        <p><b>Supported Chips:</b></p>
        <ul>
        <li>ESP8266 / ESP32</li>
        <li>Arduino (ATmega328P, ATmega2560)</li>
        <li>STM32 (F0, F1, F4 series)</li>
        <li>PIC (16F, 18F series)</li>
        <li>Nuvoton NuMicro</li>
        <li>ATtiny (via UPDI)</li>
        </ul>
        
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time pattern preview</li>
        <li>Multi-format support (.bin, .hex, .dat, .leds)</li>
        <li>FPS and brightness control</li>
        <li>One-click firmware compilation and upload</li>
        </ul>
        
        <p>Built with PySide6 and Python</p>
        <p>© 2024 Upload Bridge Project</p>
        """
        
        QMessageBox.about(self, "About Upload Bridge", about_text)
    
    def show_license_activation(self):
        """Show license activation dialog (offline)."""
        if ensure_activation_or_exit:
            try:
                ensure_activation_or_exit(self)
                self.status_bar.showMessage("✅ License OK")
            except SystemExit:
                # ensure_activation_or_exit may exit; ignore here
                pass
            except Exception as e:
                QMessageBox.warning(self, "Activation", f"Activation failed: {e}")
        else:
            QMessageBox.information(self, "Activation", "Activation module not available.")
    
    def show_license_status(self):
        """Show current license status (offline file)."""
        try:
            import json
            lf = ACTIVATION_FILE if ACTIVATION_FILE else None
            if not lf or not os.path.exists(lf):
                QMessageBox.information(self, "License Status", "No activation found on this device.")
                return
            data = json.loads(Path(lf).read_text(encoding="utf-8"))
            key = data.get("key", "N/A")
            msg = f"<b>Status:</b> Active<br><b>Key:</b> {key}"
            QMessageBox.information(self, "License Status", msg)
        except Exception as e:
            QMessageBox.warning(self, "License Status", f"Failed to read activation: {e}")

    def deactivate_license(self):
        """Remove the local activation file."""
        try:
            lf = ACTIVATION_FILE if ACTIVATION_FILE else None
            if lf and os.path.exists(lf):
                os.remove(lf)
                QMessageBox.information(self, "Deactivate", "License deactivated on this device.")
            else:
                QMessageBox.information(self, "Deactivate", "No activation found.")
        except Exception as e:
            QMessageBox.warning(self, "Deactivate", f"Failed to deactivate: {e}")
    
    def show_docs(self):
        """Show documentation"""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is available in the docs/ directory.\n\n"
            "Quick Start:\n"
            "1. Load a pattern file (File > Open)\n"
            "2. Preview it in the Preview tab\n"
            "3. Adjust FPS/brightness if needed\n"
            "4. Select chip and port in Flash tab\n"
            "5. Click 'Flash to Device'\n\n"
            "For more help, see README.md"
        )
    
    def load_settings(self):
        """Load application settings"""
        # Restore window geometry only if it's valid
        geometry = self.settings.value("geometry")
        if geometry:
            # Check if the saved geometry is still valid for current screen
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            self.restoreGeometry(geometry)
            
            # Ensure window is still visible on screen
            window_geom = self.geometry()
            if (window_geom.x() < 0 or window_geom.y() < 0 or 
                window_geom.right() > screen.width() or 
                window_geom.bottom() > screen.height()):
                # Reset to default centered position
                self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        window_geom = self.geometry()
        
        x = (screen.width() - window_geom.width()) // 2
        y = (screen.height() - window_geom.height()) // 2
        
        self.move(x, y)
    
    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        # Ensure window is properly positioned and sized
        self.adjustSize()
    
    def resizeEvent(self, event):
        """Handle window resize event"""
        super().resizeEvent(event)
        # Update any size-dependent UI elements if needed
    
    def closeEvent(self, event):
        """Handle window close"""
        # Save tab states before closing
        self._save_all_tab_states()
        
        # Check if pattern modified and ask to save
        if self.is_dirty and self.pattern:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "The pattern has been modified but not saved.\n\nDo you want to save your changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                # Try to save
                if self.current_file and self.current_file.endswith('.ledproj'):
                    self.pattern.save_to_file(self.current_file)
                    self.is_dirty = False
                else:
                    # Save as new project
                    file_path, _ = QFileDialog.getSaveFileName(
                        self,
                        "Save Project",
                        self.settings.value("last_directory", ""),
                        "LED Project (*.ledproj)"
                    )
                    if file_path:
                        self.pattern.save_to_file(file_path)
                        self.current_file = file_path
                        self.is_dirty = False
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        # Save settings
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()
    
    def _save_all_tab_states(self):
        """Save state for all initialized tabs"""
        tab_map = {
            'flash': self.flash_tab,
            'design_tools': self.design_tab,
            'wifi_upload': self.wifi_upload_tab,
            'batch_flash': self.batch_flash_tab,
            'preview': self.preview_tab,
            'pattern_library': self.pattern_library_tab,
        }
        
        for tab_name, tab in tab_map.items():
            if tab and hasattr(tab, 'get_state'):
                try:
                    state = tab.get_state()
                    if state:
                        self.tab_state_manager.save_tab_state(tab_name, state)
                except Exception as e:
                    logging.getLogger(__name__).warning(f"Failed to save state for {tab_name}: {e}")
    
    def _restore_tab_state(self, tab_name: str, tab):
        """Restore state for a tab if it has restore_state method"""
        if tab and hasattr(tab, 'restore_state'):
            try:
                state = self.tab_state_manager.load_tab_state(tab_name)
                if state:
                    tab.restore_state(state)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to restore state for {tab_name}: {e}")
    
    def _new_workspace_pattern(self):
        """Create a new pattern in workspace"""
        from core.pattern import Pattern, PatternMetadata
        
        # Create empty pattern
        metadata = PatternMetadata(width=72, height=1)
        new_pattern = Pattern(name="New Pattern", metadata=metadata, frames=[])
        
        # Add to workspace
        pattern_name = self.workspace.add_pattern(new_pattern)
        self.workspace.set_active_pattern(pattern_name)
        
        # Load it
        self.load_pattern_to_all_tabs(new_pattern, None)
        self.status_bar.showMessage(f"Created new pattern: {pattern_name}")
    
    def _duplicate_workspace_pattern(self):
        """Duplicate current pattern in workspace"""
        if not self.pattern:
            QMessageBox.information(self, "No Pattern", "No pattern to duplicate.")
            return
        
        active_name = self.workspace.get_active_pattern_name()
        if not active_name:
            QMessageBox.information(self, "No Active Pattern", "No active pattern to duplicate.")
            return
        
        new_name = self.workspace.duplicate_pattern(active_name)
        if new_name:
            # Load the duplicated pattern
            new_pattern = self.workspace.get_pattern(new_name)
            if new_pattern:
                self.workspace.set_active_pattern(new_name)
                self.load_pattern_to_all_tabs(new_pattern, None)
                self.status_bar.showMessage(f"Duplicated pattern: {new_name}")
        else:
            QMessageBox.warning(self, "Duplicate Failed", "Failed to duplicate pattern.")
    
    def _remove_workspace_pattern(self):
        """Remove current pattern from workspace"""
        active_name = self.workspace.get_active_pattern_name()
        if not active_name:
            QMessageBox.information(self, "No Pattern", "No pattern to remove.")
            return
        
        if self.workspace.count() <= 1:
            QMessageBox.information(self, "Cannot Remove", "Cannot remove the last pattern in workspace.")
            return
        
        reply = QMessageBox.question(
            self,
            "Remove Pattern?",
            f"Remove pattern '{active_name}' from workspace?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.workspace.remove_pattern(active_name)
            # Switch to another pattern
            remaining = self.workspace.list_patterns()
            if remaining:
                new_active = remaining[0]
                self.workspace.set_active_pattern(new_active)
                pattern = self.workspace.get_pattern(new_active)
                if pattern:
                    self.load_pattern_to_all_tabs(pattern, None)
    
    def _on_workspace_pattern_added(self, pattern_name: str):
        """Handle pattern added to workspace"""
        item = QListWidgetItem(pattern_name)
        item.setData(Qt.ItemDataRole.UserRole, pattern_name)
        self.workspace_list.addItem(item)
        self._update_workspace_selection()
    
    def _on_workspace_pattern_removed(self, pattern_name: str):
        """Handle pattern removed from workspace"""
        for i in range(self.workspace_list.count()):
            item = self.workspace_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == pattern_name:
                self.workspace_list.takeItem(i)
                break
        self._update_workspace_selection()
    
    def _on_workspace_active_changed(self, pattern_name: str):
        """Handle active pattern change"""
        self._update_workspace_selection()
        if pattern_name:
            pattern = self.workspace.get_pattern(pattern_name)
            if pattern and pattern != self.pattern:
                self.load_pattern_to_all_tabs(pattern, None)
    
    def _on_workspace_pattern_selected(self):
        """Handle workspace pattern selection"""
        selected_items = self.workspace_list.selectedItems()
        if selected_items:
            pattern_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
            if pattern_name:
                self.workspace.set_active_pattern(pattern_name)
    
    def _on_workspace_pattern_double_clicked(self, item: QListWidgetItem):
        """Handle workspace pattern double-click"""
        pattern_name = item.data(Qt.ItemDataRole.UserRole)
        if pattern_name:
            self.workspace.set_active_pattern(pattern_name)
    
    def _update_workspace_selection(self):
        """Update workspace list selection to match active pattern"""
        active_name = self.workspace.get_active_pattern_name()
        for i in range(self.workspace_list.count()):
            item = self.workspace_list.item(i)
            if item:
                pattern_name = item.data(Qt.ItemDataRole.UserRole)
                if pattern_name == active_name:
                    self.workspace_list.setCurrentItem(item)
                    break
    
    def _update_pattern_switcher(self, pattern_name: str = None):
        """Update pattern switcher combo box"""
        if not hasattr(self, 'pattern_switcher'):
            return
        
        self.pattern_switcher.blockSignals(True)
        self.pattern_switcher.clear()
        
        patterns = self.workspace.list_patterns()
        for name in patterns:
            self.pattern_switcher.addItem(name)
        
        # Set current to active pattern
        active_name = self.workspace.get_active_pattern_name()
        if active_name:
            index = self.pattern_switcher.findText(active_name)
            if index >= 0:
                self.pattern_switcher.setCurrentIndex(index)
        
        self.pattern_switcher.blockSignals(False)
    
    def _on_pattern_switcher_changed(self, pattern_name: str):
        """Handle pattern switcher selection change"""
        if pattern_name and pattern_name in self.workspace.list_patterns():
            self.workspace.set_active_pattern(pattern_name)

