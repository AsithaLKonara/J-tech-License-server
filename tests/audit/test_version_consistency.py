"""
Tests for version consistency fixes
Verifies version is 3.0.0 everywhere and Python version is >=3.10
"""

import pytest
import re
from pathlib import Path


class TestVersionConsistency:
    """Test version consistency across all files"""
    
    def test_setup_py_version(self):
        """Test setup.py has version 3.0.0"""
        setup_py = Path("setup.py")
        assert setup_py.exists(), "setup.py not found"
        
        content = setup_py.read_text(encoding='utf-8')
        # Check for version="3.0.0"
        assert 'version="3.0.0"' in content or "version='3.0.0'" in content, \
            "setup.py should have version 3.0.0"
    
    def test_setup_py_python_version(self):
        """Test setup.py requires Python >=3.10"""
        setup_py = Path("setup.py")
        content = setup_py.read_text(encoding='utf-8')
        
        # Check for python_requires=">=3.10"
        assert 'python_requires=">=3.10"' in content or "python_requires='>=3.10'" in content, \
            "setup.py should require Python >=3.10"
    
    def test_config_manager_version(self):
        """Test ConfigManager defaults to version 3.0.0"""
        from core.config.config_manager import ConfigManager
        
        # Reset singleton for testing
        ConfigManager._instance = None
        config = ConfigManager.instance()
        
        assert config.get('app_version') == '3.0.0', \
            "ConfigManager should default to version 3.0.0"
    
    def test_test_installation_python_version(self):
        """Test test_installation.py checks for Python 3.10+"""
        test_file = Path("tests/test_installation.py")
        if not test_file.exists():
            pytest.skip("test_installation.py not found")
        
        content = test_file.read_text(encoding='utf-8')
        
        # Check for Python 3.10 check
        assert 'version.minor < 10' in content or '3.10' in content, \
            "test_installation.py should check for Python 3.10+"
    
    def test_readme_version(self):
        """Test README.md references version 3.0.0"""
        readme = Path("README.md")
        content = readme.read_text(encoding='utf-8')
        
        # Check for version 3.0.0 references
        assert '3.0.0' in content or 'v3.0' in content, \
            "README.md should reference version 3.0.0"
    
    def test_no_version_1_0_0_in_code(self):
        """Test no code files reference version 1.0.0"""
        exclude_dirs = {'__pycache__', '.git', 'node_modules', 'venv', 'env', 
                       'tests', 'docs', 'scripts', '.pytest_cache'}
        
        version_1_0_0_files = []
        for py_file in Path('.').rglob('*.py'):
            if any(excluded in str(py_file) for excluded in exclude_dirs):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                # Check for version 1.0.0 in code (not in comments about old versions)
                if re.search(r'version\s*[=:]\s*["\']1\.0\.0["\']', content):
                    version_1_0_0_files.append(str(py_file))
            except Exception:
                pass
        
        assert len(version_1_0_0_files) == 0, \
            f"Found version 1.0.0 references in: {version_1_0_0_files}"

