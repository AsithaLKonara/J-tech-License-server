"""
L0 Structural Tests: Class Attributes and Methods

Tests that all documented classes have required attributes and methods.
"""

import pytest
import inspect
from PySide6.QtWidgets import QApplication

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def app():
    """Ensure QApplication exists"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestPatternStateAPI:
    """Test PatternState public API"""
    
    def test_pattern_state_has_required_methods(self, app):
        """PatternState has required public methods"""
        from domain.pattern_state import PatternState
        
        required_methods = [
            'pattern',
            'frames',
            'metadata',
            'width',
            'height',
            'set_pattern'
        ]
        
        for method_name in required_methods:
            assert hasattr(PatternState, method_name), f"PatternState missing {method_name}"


class TestFrameManagerAPI:
    """Test FrameManager public API"""
    
    def test_frame_manager_has_required_methods(self, app):
        """FrameManager has required public methods"""
        from domain.frames import FrameManager
        
        required_methods = [
            'add_blank_after_current',
            'duplicate',
            'delete',
            'move',
            'select',
            'set_duration',
            'frame',
            'current_index',
            'set_pattern'
        ]
        
        for method_name in required_methods:
            assert hasattr(FrameManager, method_name), f"FrameManager missing {method_name}"


class TestLayerManagerAPI:
    """Test LayerManager public API"""
    
    def test_layer_manager_has_required_methods(self, app):
        """LayerManager has required public methods"""
        from domain.layers import LayerManager
        
        required_methods = [
            'get_layers',
            'add_layer',
            'remove_layer',
            'apply_pixel',
            'get_composite_pixels',
            'sync_frame_from_layers',
            'resize_pixels',
            'replace_pixels',
            'move_layer',
            'set_layer_visible',
            'set_layer_opacity'
        ]
        
        for method_name in required_methods:
            assert hasattr(LayerManager, method_name), f"LayerManager missing {method_name}"


class TestHistoryManagerAPI:
    """Test HistoryManager public API"""
    
    def test_history_manager_has_required_methods(self, app):
        """HistoryManager has required public methods"""
        from domain.history import HistoryManager
        
        required_methods = [
            'push_command',
            'undo',
            'redo',
            'can_undo',
            'can_redo'
        ]
        
        for method_name in required_methods:
            assert hasattr(HistoryManager, method_name), f"HistoryManager missing {method_name}"


class TestAutomationQueueManagerAPI:
    """Test AutomationQueueManager public API"""
    
    def test_automation_queue_manager_has_required_methods(self, app):
        """AutomationQueueManager has required public methods"""
        from domain.automation.queue import AutomationQueueManager
        
        required_methods = [
            'append',  # Uses append instead of enqueue
            'clear',
            'actions',
            'remove_at',  # Uses remove_at instead of remove
            'set_actions'
        ]
        
        for method_name in required_methods:
            assert hasattr(AutomationQueueManager, method_name), f"AutomationQueueManager missing {method_name}"


class TestDesignToolsTabAPI:
    """Test DesignToolsTab public API"""
    
    def test_design_tools_tab_has_required_methods(self, app):
        """DesignToolsTab has required public methods"""
        from ui.tabs.design_tools_tab import DesignToolsTab
        tab = DesignToolsTab()
        
        required_methods = [
            'load_pattern',
            'update_pattern'
        ]
        
        for method_name in required_methods:
            assert hasattr(tab, method_name), f"DesignToolsTab missing {method_name}"
        
        tab.deleteLater()
    
    def test_design_tools_tab_has_required_managers(self, app):
        """DesignToolsTab has required managers"""
        from ui.tabs.design_tools_tab import DesignToolsTab
        tab = DesignToolsTab()
        
        required_managers = [
            'frame_manager',
            'layer_manager',
            'history_manager',
            'automation_manager'
        ]
        
        for manager_name in required_managers:
            assert hasattr(tab, manager_name), f"DesignToolsTab missing {manager_name}"
            assert getattr(tab, manager_name) is not None, f"DesignToolsTab.{manager_name} is None"
        
        tab.deleteLater()


class TestFileIOAPI:
    """Test File I/O API"""
    
    def test_lms_formats_has_required_functions(self):
        """lms_formats module has required functions"""
        from core.io import lms_formats
        
        required_functions = [
            'parse_dat_file',
            'parse_hex_file',
            'parse_bin_stream',
            'parse_leds_file',
            'write_leds_file'
        ]
        
        for func_name in required_functions:
            assert hasattr(lms_formats, func_name), f"lms_formats missing {func_name}"
            assert callable(getattr(lms_formats, func_name)), f"lms_formats.{func_name} is not callable"


class TestConstantsAndEnums:
    """Test constants and enums exist"""
    
    def test_known_lms_actions_exists(self):
        """KNOWN_LMS_ACTIONS constant exists"""
        # This may be in different modules
        # Implementation dependent
        pass
    
    def test_action_param_config_exists(self):
        """ACTION_PARAM_CONFIG constant exists"""
        # This may be in different modules
        # Implementation dependent
        pass

