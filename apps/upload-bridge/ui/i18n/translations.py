"""
Internationalization (i18n) System - Externalized strings for translation

Provides translation support for all UI strings.
"""

from typing import Dict, Optional
from PySide6.QtCore import QObject, QTranslator, QLocale, Signal
from PySide6.QtWidgets import QApplication


class TranslationManager(QObject):
    """
    Manages translations and externalized strings.
    """
    
    language_changed = Signal(str)  # Emitted when language changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._translator = QTranslator()
        self._current_language = "en"
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_default_translations()
    
    def _load_default_translations(self) -> None:
        """Load default English translations"""
        self._translations["en"] = {
            # Design Tools Tab
            "design_tools": "Design Tools",
            "new_pattern": "New Pattern",
            "open_pattern": "Open Pattern",
            "save_pattern": "Save Pattern",
            "export_pattern": "Export Pattern",
            "frame": "Frame",
            "layer": "Layer",
            "drawing_tool": "Drawing Tool",
            "pixel_tool": "Pixel Tool",
            "rectangle_tool": "Rectangle Tool",
            "circle_tool": "Circle Tool",
            "line_tool": "Line Tool",
            "fill_tool": "Fill Tool",
            "gradient_tool": "Gradient Tool",
            "random_spray_tool": "Random Spray Tool",
            "text_tool": "Text Tool",
            "undo": "Undo",
            "redo": "Redo",
            "play": "Play",
            "pause": "Pause",
            "stop": "Stop",
            "frame_duration": "Frame Duration",
            "fps": "FPS",
            # Common
            "ok": "OK",
            "cancel": "Cancel",
            "apply": "Apply",
            "close": "Close",
            "save": "Save",
            "load": "Load",
            "delete": "Delete",
            "copy": "Copy",
            "paste": "Paste",
            "cut": "Cut",
        }
    
    def set_language(self, language_code: str) -> bool:
        """
        Set application language.
        
        Args:
            language_code: Language code (e.g., "en", "es", "fr")
            
        Returns:
            True if language changed successfully
        """
        if language_code == self._current_language:
            return True
        
        # Load translation file if available
        translator = QTranslator()
        if translator.load(f"upload_bridge_{language_code}", ":/i18n"):
            QApplication.instance().installTranslator(translator)
            self._translator = translator
            self._current_language = language_code
            self.language_changed.emit(language_code)
            return True
        
        # Fallback to English
        self._current_language = "en"
        return False
    
    def get_language(self) -> str:
        """Get current language code"""
        return self._current_language
    
    def translate(self, key: str, default: Optional[str] = None) -> str:
        """
        Translate a string key.
        
        Args:
            key: Translation key
            default: Default string if key not found
            
        Returns:
            Translated string
        """
        translations = self._translations.get(self._current_language, {})
        return translations.get(key, default or key)
    
    def tr(self, key: str, default: Optional[str] = None) -> str:
        """Alias for translate (convenience method)"""
        return self.translate(key, default)
    
    def add_translation(self, language_code: str, key: str, value: str) -> None:
        """
        Add or update translation.
        
        Args:
            language_code: Language code
            key: Translation key
            value: Translated value
        """
        if language_code not in self._translations:
            self._translations[language_code] = {}
        self._translations[language_code][key] = value
    
    def get_available_languages(self) -> list[str]:
        """Get list of available language codes"""
        return list(self._translations.keys())


# Global translation manager instance
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get global translation manager instance"""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def tr(key: str, default: Optional[str] = None) -> str:
    """Translate string (convenience function)"""
    return get_translation_manager().translate(key, default)

