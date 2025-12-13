"""
QA Test: Config System Edge Cases
Tests error handling for missing/corrupted config files
"""

import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.app_config import load_app_config, save_app_config
from config.chip_database import load_chip_database


def test_missing_app_config():
    """Test: Missing app_config.yaml"""
    with patch('config.app_config.Path') as mock_path:
        mock_file = mock_path.return_value.__truediv__.return_value
        mock_file.exists.return_value = False
        
        result = load_app_config()
        assert result == {}, "Should return empty dict for missing file"
        print("✅ Missing app_config.yaml handled correctly")


def test_missing_chip_database():
    """Test: Missing chip_database.yaml"""
    with patch('config.chip_database.Path') as mock_path:
        mock_file = mock_path.return_value.__truediv__.return_value
        mock_file.exists.return_value = False
        
        result = load_chip_database()
        assert result == {}, "Should return empty dict for missing file"
        print("✅ Missing chip_database.yaml handled correctly")


def test_corrupted_yaml():
    """Test: Corrupted YAML file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [unclosed")
        temp_path = Path(f.name)
    
    try:
        with patch('config.app_config.Path') as mock_path:
            mock_file = mock_path.return_value.__truediv__.return_value
            mock_file.exists.return_value = True
            mock_file.__str__ = lambda: str(temp_path)
            
            result = load_app_config()
            # Should return empty dict on error
            assert isinstance(result, dict), "Should return dict even on error"
            print("✅ Corrupted YAML handled correctly")
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_empty_file():
    """Test: Empty config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = Path(f.name)
    
    try:
        with patch('config.app_config.Path') as mock_path:
            mock_file = mock_path.return_value.__truediv__.return_value
            mock_file.exists.return_value = True
            mock_file.__str__ = lambda: str(temp_path)
            
            result = load_app_config()
            assert result == {}, "Should return empty dict for empty file"
            print("✅ Empty file handled correctly")
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_save_app_config_success():
    """Test: Successful save"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_config = {"test": "value", "number": 42}
        
        with patch('config.app_config.Path') as mock_path:
            mock_file = mock_path.return_value.__truediv__.return_value
            mock_file.__str__ = lambda: str(Path(tmpdir) / "app_config.yaml")
            
            result = save_app_config(test_config)
            assert result is True, "Should return True on success"
            print("✅ Save app_config works")


def test_save_app_config_permission_error():
    """Test: Permission error on save"""
    with patch('config.app_config.open', side_effect=PermissionError("No write permission")):
        result = save_app_config({"test": "value"})
        assert result is False, "Should return False on permission error"
        print("✅ Permission error handled correctly")


if __name__ == "__main__":
    test_missing_app_config()
    test_missing_chip_database()
    test_corrupted_yaml()
    test_empty_file()
    test_save_app_config_success()
    test_save_app_config_permission_error()
    print("\n✅ All edge case tests passed")

