"""
Accessibility Manager - Screen reader support, keyboard navigation, high contrast

Provides accessibility features for all UI components.
"""

from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QPalette, QColor


class AccessibilityManager(QObject):
    """
    Manages accessibility features: screen reader labels, keyboard navigation,
    high contrast mode, and accessibility settings.
    """
    
    accessibility_changed = Signal()  # Emitted when settings change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._high_contrast = False
        self._screen_reader_enabled = True
        self._keyboard_navigation_enabled = True
        self._settings: Dict[str, bool] = {
            "high_contrast": False,
            "screen_reader": True,
            "keyboard_navigation": True,
            "tooltips": True,
            "aria_labels": True
        }
    
    def set_high_contrast(self, enabled: bool) -> None:
        """Enable/disable high contrast mode"""
        self._high_contrast = enabled
        self._settings["high_contrast"] = enabled
        self.accessibility_changed.emit()
    
    def is_high_contrast(self) -> bool:
        """Check if high contrast mode is enabled"""
        return self._high_contrast
    
    def set_screen_reader_enabled(self, enabled: bool) -> None:
        """Enable/disable screen reader support"""
        self._screen_reader_enabled = enabled
        self._settings["screen_reader"] = enabled
        self.accessibility_changed.emit()
    
    def is_screen_reader_enabled(self) -> bool:
        """Check if screen reader is enabled"""
        return self._screen_reader_enabled
    
    def set_keyboard_navigation_enabled(self, enabled: bool) -> None:
        """Enable/disable keyboard navigation"""
        self._keyboard_navigation_enabled = enabled
        self._settings["keyboard_navigation"] = enabled
        self.accessibility_changed.emit()
    
    def is_keyboard_navigation_enabled(self) -> bool:
        """Check if keyboard navigation is enabled"""
        return self._keyboard_navigation_enabled
    
    def set_accessible_name(self, widget: QWidget, name: str) -> None:
        """
        Set accessible name for widget (for screen readers).
        
        Args:
            widget: Widget to label
            name: Accessible name
        """
        widget.setAccessibleName(name)
        if self._screen_reader_enabled:
            widget.setToolTip(name)
    
    def set_accessible_description(self, widget: QWidget, description: str) -> None:
        """
        Set accessible description for widget.
        
        Args:
            widget: Widget to describe
            description: Accessible description
        """
        widget.setAccessibleDescription(description)
    
    def apply_high_contrast_palette(self, widget: QWidget) -> None:
        """
        Apply high contrast palette to widget.
        
        Args:
            widget: Widget to apply palette to
        """
        if not self._high_contrast:
            return
        
        palette = QPalette()
        # High contrast colors
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.AlternateBase, QColor(20, 20, 20))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(0, 0, 0))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(0, 162, 232))
        palette.setColor(QPalette.Highlight, QColor(0, 162, 232))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        widget.setPalette(palette)
    
    def setup_keyboard_shortcuts(self, widget: QWidget, shortcuts: Dict[str, str]) -> None:
        """
        Setup keyboard shortcuts for widget.
        
        Args:
            widget: Widget to setup shortcuts for
            shortcuts: Dictionary of action -> shortcut key
        """
        if not self._keyboard_navigation_enabled:
            return
        
        # Shortcuts should be set up in the widget's parent or action system
        # This is a placeholder for the interface
        pass
    
    def get_settings(self) -> Dict[str, bool]:
        """Get current accessibility settings"""
        return self._settings.copy()
    
    def set_settings(self, settings: Dict[str, bool]) -> None:
        """Set accessibility settings"""
        self._settings.update(settings)
        self._high_contrast = settings.get("high_contrast", False)
        self._screen_reader_enabled = settings.get("screen_reader", True)
        self._keyboard_navigation_enabled = settings.get("keyboard_navigation", True)
        self.accessibility_changed.emit()

