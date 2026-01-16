"""
External dependency checker and installer.

Checks for required external tools like esptool, avrdude, etc.
and provides installation guidance when missing.
"""

import subprocess
import sys
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import shutil

logger = logging.getLogger(__name__)


class DependencyStatus(Enum):
    """Status of a dependency"""
    INSTALLED = "installed"
    MISSING = "missing"
    OUTDATED = "outdated"
    OPTIONAL = "optional"


class ExternalDependency:
    """Represents an external dependency"""
    
    def __init__(
        self,
        name: str,
        command: str,
        version_check: str = "--version",
        min_version: Optional[str] = None,
        required: bool = False,
        install_url: str = "",
        install_command: Optional[str] = None,
        description: str = "",
    ):
        """
        Initialize dependency.
        
        Args:
            name: Human-readable name
            command: Command to run
            version_check: Argument to get version
            min_version: Minimum required version
            required: Whether dependency is required
            install_url: URL for installation guide
            install_command: Command to install (if available)
            description: Description of what it does
        """
        self.name = name
        self.command = command
        self.version_check = version_check
        self.min_version = min_version
        self.required = required
        self.install_url = install_url
        self.install_command = install_command
        self.description = description
    
    def check_installed(self) -> Tuple[bool, Optional[str]]:
        """
        Check if dependency is installed.
        
        Returns:
            Tuple of (is_installed, version)
        """
        try:
            # Check if command exists
            result = subprocess.run(
                [self.command, self.version_check],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False, None
            
            # Extract version from output
            version = self._extract_version(result.stdout + result.stderr)
            return True, version
        
        except FileNotFoundError:
            return False, None
        except Exception as e:
            logger.debug(f"Error checking {self.name}: {e}")
            return False, None
    
    def _extract_version(self, output: str) -> Optional[str]:
        """Extract version number from output"""
        import re
        match = re.search(r'(\d+\.\d+(?:\.\d+)?)', output)
        return match.group(1) if match else "unknown"
    
    def compare_versions(self, current: str, required: str) -> bool:
        """
        Compare versions.
        
        Args:
            current: Current version string
            required: Required version string
        
        Returns:
            True if current >= required
        """
        try:
            current_parts = [int(x) for x in current.split('.')]
            required_parts = [int(x) for x in required.split('.')]
            
            # Pad with zeros
            max_len = max(len(current_parts), len(required_parts))
            current_parts += [0] * (max_len - len(current_parts))
            required_parts += [0] * (max_len - len(required_parts))
            
            return current_parts >= required_parts
        except Exception:
            return False


class DependencyChecker:
    """Checks system dependencies"""
    
    # Define all dependencies
    DEPENDENCIES = {
        'esptool': ExternalDependency(
            name='esptool',
            command='esptool.py',
            version_check='version',
            min_version='3.0',
            required=True,
            install_url='https://github.com/espressif/esptool',
            install_command='pip install esptool',
            description='ESP chip programming tool'
        ),
        'avrdude': ExternalDependency(
            name='avrdude',
            command='avrdude',
            version_check='-v',
            min_version='6.0',
            required=False,  # Only needed for AVR chips
            install_url='https://github.com/avrdudes/avrdude',
            description='AVR microcontroller programmer'
        ),
        'python': ExternalDependency(
            name='python',
            command=sys.executable,
            version_check='--version',
            min_version='3.8',
            required=True,
            description='Python interpreter'
        ),
    }
    
    def __init__(self, check_required_only: bool = False):
        """
        Initialize dependency checker.
        
        Args:
            check_required_only: Only check required dependencies
        """
        self.check_required_only = check_required_only
        self.results: Dict[str, Tuple[DependencyStatus, Optional[str]]] = {}
    
    def check_all(self) -> Dict[str, Tuple[DependencyStatus, Optional[str]]]:
        """
        Check all dependencies.
        
        Returns:
            Dictionary of {name: (status, version)}
        """
        self.results.clear()
        
        for dep_name, dependency in self.DEPENDENCIES.items():
            if self.check_required_only and not dependency.required:
                continue
            
            is_installed, version = dependency.check_installed()
            
            if not is_installed:
                status = DependencyStatus.MISSING
            elif dependency.min_version and version:
                if dependency.compare_versions(version, dependency.min_version):
                    status = DependencyStatus.INSTALLED
                else:
                    status = DependencyStatus.OUTDATED
            else:
                status = DependencyStatus.INSTALLED
            
            self.results[dep_name] = (status, version)
        
        return self.results
    
    def get_missing_required(self) -> List[str]:
        """Get list of missing required dependencies"""
        missing = []
        
        for dep_name, (status, _) in self.results.items():
            dependency = self.DEPENDENCIES[dep_name]
            if dependency.required and status == DependencyStatus.MISSING:
                missing.append(dep_name)
        
        return missing
    
    def get_installation_guide(self) -> str:
        """
        Get installation guide for missing dependencies.
        
        Returns:
            Installation guide string
        """
        guide = "Missing Dependencies - Installation Guide\n"
        guide += "=" * 50 + "\n\n"
        
        for dep_name, (status, _) in self.results.items():
            if status != DependencyStatus.MISSING:
                continue
            
            dependency = self.DEPENDENCIES[dep_name]
            
            guide += f"• {dependency.name}\n"
            guide += f"  Description: {dependency.description}\n"
            guide += f"  Required: {'Yes' if dependency.required else 'Optional'}\n"
            
            if dependency.install_command:
                guide += f"  Install: {dependency.install_command}\n"
            
            guide += f"  More info: {dependency.install_url}\n\n"
        
        return guide
    
    def get_status_report(self) -> str:
        """
        Get formatted status report.
        
        Returns:
            Status report string
        """
        report = "Dependency Status Report\n"
        report += "=" * 50 + "\n\n"
        
        for dep_name, (status, version) in self.results.items():
            dependency = self.DEPENDENCIES[dep_name]
            status_icon = {
                DependencyStatus.INSTALLED: "✓",
                DependencyStatus.MISSING: "✗",
                DependencyStatus.OUTDATED: "⚠",
                DependencyStatus.OPTIONAL: "○",
            }.get(status, "?")
            
            version_str = f" (v{version})" if version else ""
            required_str = "[REQUIRED]" if dependency.required else "[OPTIONAL]"
            
            report += f"{status_icon} {dep_name}{version_str} {required_str}\n"
        
        # Summary
        missing = self.get_missing_required()
        if missing:
            report += f"\n⚠ Missing required: {', '.join(missing)}\n"
            report += "Please install missing dependencies before continuing.\n"
        else:
            report += "\n✓ All required dependencies are installed!\n"
        
        return report


class DependencyValidator:
    """Validates that dependencies can be used"""
    
    @staticmethod
    def validate_esptool() -> Tuple[bool, str]:
        """
        Validate esptool is working.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            result = subprocess.run(
                ['esptool.py', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, f"esptool OK: {result.stdout.strip()}"
            else:
                return False, f"esptool error: {result.stderr}"
        
        except Exception as e:
            return False, f"esptool validation failed: {e}"
    
    @staticmethod
    def validate_avrdude() -> Tuple[bool, str]:
        """
        Validate avrdude is working.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            result = subprocess.run(
                ['avrdude', '-v'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 or 'avrdude' in (result.stdout + result.stderr):
                return True, "avrdude OK"
            else:
                return False, "avrdude validation failed"
        
        except Exception as e:
            return False, f"avrdude validation failed: {e}"


def check_dependencies(required_only: bool = True) -> Tuple[bool, str]:
    """
    Check all dependencies.
    
    Args:
        required_only: Only check required dependencies
    
    Returns:
        Tuple of (all_ok, status_report)
    """
    checker = DependencyChecker(check_required_only=required_only)
    checker.check_all()
    
    report = checker.get_status_report()
    
    missing = checker.get_missing_required()
    all_ok = len(missing) == 0
    
    if not all_ok:
        guide = checker.get_installation_guide()
        report += "\n" + guide
    
    return all_ok, report
