"""
Tests for config system fixes
Verifies YAML config loading and no orphaned config files
"""

import pytest
from pathlib import Path
from core.config.config_manager import ConfigManager


class TestConfigSystem:
    """Test configuration system"""
    
    def test_app_config_yaml_exists(self):
        """Test app_config.yaml exists"""
        yaml_config = Path("config/app_config.yaml")
        assert yaml_config.exists(), "app_config.yaml should exist"
    
    def test_config_manager_loads_yaml(self):
        """Test ConfigManager loads YAML config if it exists"""
        yaml_config = Path("config/app_config.yaml")
        if not yaml_config.exists():
            pytest.skip("app_config.yaml not found")
        
        # Reset singleton for testing
        ConfigManager._instance = None
        config = ConfigManager.instance()
        
        # ConfigManager should try to load YAML first
        assert config._config_file is not None, "ConfigManager should load config file"
    
    def test_config_module_functions_exist(self):
        """Test config module provides loading functions"""
        from config import load_chip_database, load_app_config
        
        assert callable(load_chip_database), "load_chip_database should be callable"
        assert callable(load_app_config), "load_app_config should be callable"
    
    def test_chip_database_loads(self):
        """Test chip database loads via config module"""
        from config import load_chip_database
        
        db = load_chip_database()
        assert isinstance(db, dict), "load_chip_database should return dict"
        assert 'chips' in db, "Database should have 'chips' key"
    
    def test_empty_config_modules(self):
        """Test if config modules are empty (documentation)"""
        app_config_py = Path("config/app_config.py")
        chip_db_py = Path("config/chip_database.py")
        
        if app_config_py.exists():
            content = app_config_py.read_text(encoding='utf-8')
            # Check if it's mostly empty (just imports)
            non_comment_lines = [l for l in content.split('\n') 
                               if l.strip() and not l.strip().startswith('#')]
            # Should have at most a few lines (imports)
            assert len(non_comment_lines) <= 5, \
                "app_config.py should be empty or have minimal code"
        
        if chip_db_py.exists():
            content = chip_db_py.read_text(encoding='utf-8')
            non_comment_lines = [l for l in content.split('\n') 
                               if l.strip() and not l.strip().startswith('#')]
            assert len(non_comment_lines) <= 5, \
                "chip_database.py should be empty or have minimal code"

