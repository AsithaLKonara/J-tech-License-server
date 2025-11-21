"""
Feature Linkage Testing & Verification
Tests all implemented feature linkages and cross-tab synchronization
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import unittest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

try:
    from core.pattern import Pattern, PatternMetadata
    from core.pattern_clipboard import PatternClipboard
    from core.undo_redo_manager import SharedUndoRedoManager, UndoCommand
    from core.tab_state_manager import TabStateManager
    from core.workspace_manager import WorkspaceManager
    from PySide6.QtCore import QSettings
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[:3]}")
    raise


class TestPatternClipboard(unittest.TestCase):
    """Test pattern clipboard functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset singleton
        PatternClipboard._instance = None
        self.clipboard = PatternClipboard()
    
    def test_clipboard_singleton(self):
        """Test that clipboard is a singleton"""
        clipboard1 = PatternClipboard()
        clipboard2 = PatternClipboard()
        self.assertIs(clipboard1, clipboard2)
    
    def test_copy_pattern(self):
        """Test copying pattern to clipboard"""
        pattern = Pattern(name="Test Pattern", metadata=PatternMetadata(width=10, height=1), frames=[])
        self.clipboard.copy_pattern(pattern)
        self.assertTrue(self.clipboard.has_pattern())
    
    def test_paste_pattern(self):
        """Test pasting pattern from clipboard"""
        pattern = Pattern(name="Test Pattern", metadata=PatternMetadata(width=10, height=1), frames=[])
        self.clipboard.copy_pattern(pattern)
        pasted = self.clipboard.paste_pattern()
        self.assertIsNotNone(pasted)
        self.assertEqual(pasted.name, pattern.name)
    
    def test_clear_clipboard(self):
        """Test clearing clipboard"""
        pattern = Pattern(name="Test Pattern", metadata=PatternMetadata(width=10, height=1), frames=[])
        self.clipboard.copy_pattern(pattern)
        self.clipboard.clear()
        self.assertFalse(self.clipboard.has_pattern())


class TestUndoRedoManager(unittest.TestCase):
    """Test undo/redo manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = SharedUndoRedoManager(max_history=10)
    
    def test_push_command(self):
        """Test pushing command to history"""
        command = Mock(spec=UndoCommand)
        command.description = "Test Command"
        self.manager.push_command("test_tab", command)
        self.assertTrue(self.manager.can_undo("test_tab"))
    
    def test_undo_redo(self):
        """Test undo and redo operations"""
        command = Mock(spec=UndoCommand)
        command.description = "Test Command"
        command.execute = Mock()
        command.undo = Mock()
        
        self.manager.push_command("test_tab", command)
        self.assertTrue(self.manager.can_undo("test_tab"))
        self.assertFalse(self.manager.can_redo("test_tab"))
        
        # Undo
        result = self.manager.undo("test_tab")
        self.assertTrue(result)
        command.undo.assert_called_once()
        self.assertFalse(self.manager.can_undo("test_tab"))
        self.assertTrue(self.manager.can_redo("test_tab"))
        
        # Redo
        result = self.manager.redo("test_tab")
        self.assertTrue(result)
        command.execute.assert_called_once()
        self.assertTrue(self.manager.can_undo("test_tab"))
        self.assertFalse(self.manager.can_redo("test_tab"))


class TestTabStateManager(unittest.TestCase):
    """Test tab state manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use in-memory settings for testing
        self.settings = QSettings("TestOrg", "TestApp")
        self.manager = TabStateManager(self.settings)
    
    def test_save_load_state(self):
        """Test saving and loading tab state"""
        state = {'chip_id': 'esp8266', 'port': 'COM3', 'gpio': 2}
        self.manager.save_tab_state('test_tab', state)
        loaded = self.manager.load_tab_state('test_tab')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['chip_id'], 'esp8266')
    
    def test_clear_state(self):
        """Test clearing tab state"""
        state = {'chip_id': 'esp8266'}
        self.manager.save_tab_state('test_tab', state)
        self.manager.clear_tab_state('test_tab')
        loaded = self.manager.load_tab_state('test_tab')
        self.assertIsNone(loaded)


class TestWorkspaceManager(unittest.TestCase):
    """Test workspace manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.workspace = WorkspaceManager()
    
    def test_add_pattern(self):
        """Test adding pattern to workspace"""
        pattern = Pattern(name="Test Pattern", metadata=PatternMetadata(width=10, height=1), frames=[])
        name = self.workspace.add_pattern(pattern)
        self.assertIsNotNone(name)
        self.assertIn(name, self.workspace.list_patterns())
    
    def test_set_active_pattern(self):
        """Test setting active pattern"""
        pattern = Pattern(name="Test Pattern", metadata=PatternMetadata(width=10, height=1), frames=[])
        name = self.workspace.add_pattern(pattern)
        result = self.workspace.set_active_pattern(name)
        self.assertTrue(result)
        self.assertEqual(self.workspace.get_active_pattern_name(), name)
    
    def test_duplicate_pattern(self):
        """Test duplicating pattern"""
        pattern = Pattern(name="Test Pattern", metadata=PatternMetadata(width=10, height=1), frames=[])
        name = self.workspace.add_pattern(pattern)
        dup_name = self.workspace.duplicate_pattern(name)
        self.assertIsNotNone(dup_name)
        self.assertNotEqual(name, dup_name)
        self.assertIn(dup_name, self.workspace.list_patterns())
    
    def test_remove_pattern(self):
        """Test removing pattern from workspace"""
        pattern = Pattern(name="Test Pattern", metadata=PatternMetadata(width=10, height=1), frames=[])
        name = self.workspace.add_pattern(pattern)
        result = self.workspace.remove_pattern(name)
        self.assertTrue(result)
        self.assertNotIn(name, self.workspace.list_patterns())


class TestSignalConnections(unittest.TestCase):
    """Test signal connections between tabs"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for Qt tests"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_pattern_changed_signal_exists(self):
        """Test that pattern_changed signal exists in MainWindow"""
        from ui.main_window import UploadBridgeMainWindow
        window = UploadBridgeMainWindow()
        self.assertTrue(hasattr(window, 'pattern_changed'))
        self.assertTrue(hasattr(window, 'save_state_changed'))
    
    def test_playback_signals_exist(self):
        """Test that playback signals exist in tabs"""
        from ui.tabs.preview_tab import PreviewTab
        from ui.tabs.design_tools_tab import DesignToolsTab
        
        preview = PreviewTab()
        design = DesignToolsTab()
        
        self.assertTrue(hasattr(preview, 'playback_state_changed'))
        self.assertTrue(hasattr(preview, 'frame_changed'))
        self.assertTrue(hasattr(design, 'playback_state_changed'))
        self.assertTrue(hasattr(design, 'frame_changed'))
    
    def test_sync_methods_exist(self):
        """Test that sync methods exist in tabs"""
        from ui.tabs.preview_tab import PreviewTab
        from ui.tabs.design_tools_tab import DesignToolsTab
        
        preview = PreviewTab()
        design = DesignToolsTab()
        
        self.assertTrue(hasattr(preview, 'sync_playback_state'))
        self.assertTrue(hasattr(preview, 'sync_frame_selection'))
        self.assertTrue(hasattr(design, 'sync_playback_state'))
        self.assertTrue(hasattr(design, 'sync_frame_selection'))


def run_integration_tests():
    """Run integration tests with actual UI components"""
    print("\n" + "="*70)
    print("FEATURE LINKAGE INTEGRATION TESTS")
    print("="*70)
    
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # Test 1: Clipboard functionality
    print("\n[TEST 1] Pattern Clipboard")
    try:
        PatternClipboard._instance = None
        clipboard = PatternClipboard()
        pattern = Pattern(name="Test", metadata=PatternMetadata(width=10, height=1), frames=[])
        clipboard.copy_pattern(pattern)
        assert clipboard.has_pattern(), "Clipboard should have pattern"
        pasted = clipboard.paste_pattern()
        assert pasted is not None, "Should be able to paste pattern"
        assert pasted.name == pattern.name, "Pasted pattern should match"
        print("  ✓ Clipboard copy/paste works")
        results['passed'] += 1
    except Exception as e:
        print(f"  ✗ Clipboard test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Clipboard: {e}")
    
    # Test 2: Undo/Redo Manager
    print("\n[TEST 2] Undo/Redo Manager")
    try:
        manager = SharedUndoRedoManager()
        command = Mock(spec=UndoCommand)
        command.description = "Test"
        command.execute = Mock()
        command.undo = Mock()
        
        manager.push_command("test", command)
        assert manager.can_undo("test"), "Should be able to undo"
        assert not manager.can_redo("test"), "Should not be able to redo initially"
        
        manager.undo("test")
        assert not manager.can_undo("test"), "Should not be able to undo after undo"
        assert manager.can_redo("test"), "Should be able to redo"
        
        manager.redo("test")
        assert manager.can_undo("test"), "Should be able to undo after redo"
        print("  ✓ Undo/Redo manager works")
        results['passed'] += 1
    except Exception as e:
        print(f"  ✗ Undo/Redo test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Undo/Redo: {e}")
    
    # Test 3: Tab State Manager
    print("\n[TEST 3] Tab State Manager")
    try:
        settings = QSettings("TestOrg", "TestApp")
        manager = TabStateManager(settings)
        state = {'chip_id': 'esp8266', 'gpio': 2}
        manager.save_tab_state('test', state)
        loaded = manager.load_tab_state('test')
        assert loaded is not None, "Should load saved state"
        assert loaded['chip_id'] == 'esp8266', "State should match"
        print("  ✓ Tab state save/load works")
        results['passed'] += 1
    except Exception as e:
        print(f"  ✗ Tab state test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Tab State: {e}")
    
    # Test 4: Workspace Manager
    print("\n[TEST 4] Workspace Manager")
    try:
        workspace = WorkspaceManager()
        pattern = Pattern(name="Test", metadata=PatternMetadata(width=10, height=1), frames=[])
        name = workspace.add_pattern(pattern)
        assert name in workspace.list_patterns(), "Pattern should be in list"
        workspace.set_active_pattern(name)
        assert workspace.get_active_pattern_name() == name, "Active pattern should match"
        
        dup_name = workspace.duplicate_pattern(name)
        assert dup_name in workspace.list_patterns(), "Duplicate should be in list"
        assert workspace.count() == 2, "Should have 2 patterns"
        print("  ✓ Workspace manager works")
        results['passed'] += 1
    except Exception as e:
        print(f"  ✗ Workspace test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Workspace: {e}")
    
    # Test 5: Signal Existence
    print("\n[TEST 5] Signal Existence")
    try:
        from ui.tabs.preview_tab import PreviewTab
        from ui.tabs.design_tools_tab import DesignToolsTab
        from ui.main_window import UploadBridgeMainWindow
        
        preview = PreviewTab()
        design = DesignToolsTab()
        window = UploadBridgeMainWindow()
        
        assert hasattr(preview, 'playback_state_changed'), "PreviewTab should have playback_state_changed"
        assert hasattr(preview, 'frame_changed'), "PreviewTab should have frame_changed"
        assert hasattr(design, 'playback_state_changed'), "DesignToolsTab should have playback_state_changed"
        assert hasattr(design, 'frame_changed'), "DesignToolsTab should have frame_changed"
        assert hasattr(window, 'pattern_changed'), "MainWindow should have pattern_changed"
        assert hasattr(preview, 'sync_playback_state'), "PreviewTab should have sync_playback_state"
        assert hasattr(design, 'sync_playback_state'), "DesignToolsTab should have sync_playback_state"
        print("  ✓ All required signals and methods exist")
        results['passed'] += 1
    except Exception as e:
        print(f"  ✗ Signal existence test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Signals: {e}")
    
    # Test 6: FlashTab State Methods
    print("\n[TEST 6] FlashTab State Methods")
    try:
        from ui.tabs.flash_tab import FlashTab
        flash_tab = FlashTab()
        assert hasattr(flash_tab, 'get_state'), "FlashTab should have get_state"
        assert hasattr(flash_tab, 'restore_state'), "FlashTab should have restore_state"
        
        state = flash_tab.get_state()
        assert isinstance(state, dict), "State should be a dict"
        print("  ✓ FlashTab state methods work")
        results['passed'] += 1
    except Exception as e:
        print(f"  ✗ FlashTab state test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"FlashTab State: {e}")
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    print("="*70 + "\n")
    
    return results['failed'] == 0


if __name__ == '__main__':
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration tests
    success = run_integration_tests()
    sys.exit(0 if success else 1)

