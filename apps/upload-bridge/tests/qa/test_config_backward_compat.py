"""
QA Test: Config System Backward Compatibility
Tests that all import styles work after PR 3 changes
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_backward_compatible_import():
    """Test: from config import ..."""
    from config import load_app_config, load_chip_database, save_app_config
    
    assert callable(load_app_config)
    assert callable(load_chip_database)
    assert callable(save_app_config)
    
    # Test they work
    app_config = load_app_config()
    assert isinstance(app_config, dict)
    
    chip_db = load_chip_database()
    assert isinstance(chip_db, dict)
    assert 'chips' in chip_db or chip_db == {}  # Empty dict is OK if file doesn't exist
    
    print("✅ Backward compatible import works")


def test_direct_module_import():
    """Test: from config.app_config import ..."""
    from config.app_config import load_app_config, save_app_config
    from config.chip_database import load_chip_database
    
    assert callable(load_app_config)
    assert callable(load_chip_database)
    assert callable(save_app_config)
    
    # Test they work
    app_config = load_app_config()
    assert isinstance(app_config, dict)
    
    chip_db = load_chip_database()
    assert isinstance(chip_db, dict)
    
    print("✅ Direct module imports work")


def test_uploader_registry_import():
    """Test: uploader_registry.py import style"""
    from uploaders.uploader_registry import UploaderRegistry
    
    # This should work without errors
    registry = UploaderRegistry.instance()
    assert registry is not None
    
    print("✅ UploaderRegistry works with config imports")


if __name__ == "__main__":
    test_backward_compatible_import()
    test_direct_module_import()
    test_uploader_registry_import()
    print("\n✅ All backward compatibility tests passed")

