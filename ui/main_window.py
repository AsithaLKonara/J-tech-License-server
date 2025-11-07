"""
Main Window - Upload Bridge Application
Complete PySide6 implementation
"""

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QMenuBar, QMenu, 
                                QStatusBar, QFileDialog, QMessageBox,
                                QToolBar, QApplication, QSplitter)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QAction
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
import logging

from core.pattern import Pattern
from parsers.parser_registry import parse_pattern_file, ParserRegistry
from ui.tabs.preview_tab import PreviewTab
from ui.tabs.flash_tab import FlashTab
from ui.tabs.wifi_upload_tab import WiFiUploadTab
from ui.tabs.media_upload_tab import MediaUploadTab
from ui.tabs.arduino_ide_tab import ArduinoIDETab
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
    
    def __init__(self):
        super().__init__()
        
        self.pattern: Pattern = None
        self.current_file: str = None
        self.is_dirty: bool = False
        self.settings = QSettings("UploadBridge", "UploadBridge")
        
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
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Lazy tab initialization - tabs created on first access
        self._tabs_initialized = {
            'media_upload': False,
            'preview': False,
            'flash': False,
            'wifi_upload': False,
            'arduino_ide': False
        }
        
        # Store tab references
        self.media_upload_tab = None
        self.preview_tab = None
        self.flash_tab = None
        self.wifi_upload_tab = None
        self.arduino_ide_tab = None
        
        # Add placeholder tabs with lazy initialization
        self.tabs.addTab(self.create_placeholder_tab("🎬 Media Upload"), "🎬 Media Upload")
        self.tabs.addTab(self.create_placeholder_tab("👁️ Preview"), "👁️ Preview")
        self.tabs.addTab(self.create_placeholder_tab("⚡ Flash"), "⚡ Flash")
        self.tabs.addTab(self.create_placeholder_tab("📡 WiFi Upload"), "📡 WiFi Upload")
        self.tabs.addTab(self.create_placeholder_tab("🔧 Arduino IDE"), "🔧 Arduino IDE")
        
        # Connect to tab change signal for lazy initialization
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
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
        tab_names = ['media_upload', 'preview', 'flash', 'wifi_upload', 'arduino_ide']
        
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
                
            elif tab_name == 'preview' and self.preview_tab is None:
                self.preview_tab = PreviewTab()
                self.tabs.removeTab(1)
                self.tabs.insertTab(1, self.preview_tab, "👁️ Preview")
                self.preview_tab.pattern_modified.connect(self.on_pattern_modified)
                self._tabs_initialized['preview'] = True
                
            elif tab_name == 'flash' and self.flash_tab is None:
                self.flash_tab = FlashTab()
                self.tabs.removeTab(2)
                self.tabs.insertTab(2, self.flash_tab, "⚡ Flash")
                self.flash_tab.flash_complete.connect(self.on_flash_complete)
                self._tabs_initialized['flash'] = True
                
            elif tab_name == 'wifi_upload' and self.wifi_upload_tab is None:
                self.wifi_upload_tab = WiFiUploadTab()
                self.tabs.removeTab(3)
                self.tabs.insertTab(3, self.wifi_upload_tab, "📡 WiFi Upload")
                self._tabs_initialized['wifi_upload'] = True
                
            elif tab_name == 'arduino_ide' and self.arduino_ide_tab is None:
                self.arduino_ide_tab = ArduinoIDETab()
                self.tabs.removeTab(4)
                self.tabs.insertTab(4, self.arduino_ide_tab, "🔧 Arduino IDE")
                self._tabs_initialized['arduino_ide'] = True
            
            # Load pattern if one is already loaded
            if self.pattern:
                self.load_pattern_to_tab(tab_name, self.pattern, self.current_file)
                
            self.status_bar.showMessage("Ready")
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Tab Initialization Error",
                f"Failed to initialize {tab_name} tab:\n{str(e)}"
            )
            self.status_bar.showMessage("Tab initialization failed")
    
    def get_tab(self, tab_name: str):
        """Get a tab, initializing it if necessary"""
        tab_map = {
            'media_upload': (self.media_upload_tab, 'media_upload'),
            'preview': (self.preview_tab, 'preview'),
            'flash': (self.flash_tab, 'flash'),
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
                self.pattern.save_to_file(self.current_file)
                self.is_dirty = False  # Clear dirty flag after save
                self.status_bar.showMessage(f"Saved: {self.current_file}")
                # Remove * from window title
                base_name = os.path.basename(self.current_file)
                self.setWindowTitle(f"Upload Bridge - {base_name}")
                QMessageBox.information(self, "Saved", "Project saved successfully!")
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
            self.pattern.save_to_file(file_path)
            self.current_file = file_path
            self.is_dirty = False  # Clear dirty flag after save
            self.status_bar.showMessage(f"Saved: {file_path}")
            # Update window title
            base_name = os.path.basename(file_path)
            self.setWindowTitle(f"Upload Bridge - {base_name}")
            QMessageBox.information(self, "Saved", "Project saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n\n{str(e)}")
    
    def on_pattern_modified(self):
        """Pattern was modified in preview"""
        self.is_dirty = True
        self.status_bar.showMessage("Pattern modified")
        # Update window title to show unsaved changes
        if self.current_file:
            base_name = os.path.basename(self.current_file)
            if not self.windowTitle().endswith('*'):
                self.setWindowTitle(f"Upload Bridge - {base_name} *")
    
    def on_flash_complete(self, success: bool, message: str):
        """Flash operation completed"""
        if success:
            self.status_bar.showMessage("✅ Flash successful!")
        else:
            self.status_bar.showMessage("❌ Flash failed")
    
    def load_pattern_to_all_tabs(self, pattern: Pattern, file_path: str = None):
        """Load pattern into all relevant tabs with error recovery (lazy initialization)"""
        # Store pattern first (so it's available even if tabs fail)
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
        
        # Flash Tab (initialize and load)
        try:
            flash = self.get_tab('flash')
            if flash and hasattr(flash, 'load_pattern'):
                flash.load_pattern(pattern)
                tabs_loaded.append("Flash")
        except Exception as e:
            tabs_failed.append(f"Flash: {str(e)}")
            logging.getLogger(__name__).warning("Flash tab load failed: %s", e)
        
        # WiFi Upload Tab (initialize and load)
        try:
            wifi = self.get_tab('wifi_upload')
            if wifi and hasattr(wifi, 'set_pattern'):
                wifi.set_pattern(pattern)
                tabs_loaded.append("WiFi Upload")
        except Exception as e:
            tabs_failed.append(f"WiFi Upload: {str(e)}")
            logging.getLogger(__name__).warning("WiFi Upload tab load failed: %s", e)
        
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
    
    def load_pattern_from_media(self, pattern: Pattern):
        """Load pattern created from media conversion"""
        # Use the unified loading method
        self.load_pattern_to_all_tabs(pattern, None)
        self.is_dirty = True  # Media patterns are unsaved
        self.status_bar.showMessage(f"Pattern loaded from media: {pattern.name}")
    
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

