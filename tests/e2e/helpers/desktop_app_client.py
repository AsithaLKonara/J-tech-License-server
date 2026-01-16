"""
Desktop App Client Helper for E2E Tests
Provides helpers for interacting with the desktop application
"""

import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import sys

from tests.e2e.test_config import DESKTOP_APP_PATH, DESKTOP_APP_TIMEOUT

logger = logging.getLogger(__name__)


class DesktopAppClient:
    """Client for interacting with desktop application"""
    
    def __init__(self, app_path: Optional[str] = None):
        self.app_path = app_path or DESKTOP_APP_PATH
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
    
    def start_app(self, args: Optional[list] = None) -> Tuple[bool, Optional[str]]:
        """Start desktop application"""
        if not self.app_path:
            return False, "Desktop app path not configured"
        
        if not Path(self.app_path).exists():
            return False, f"Desktop app not found at {self.app_path}"
        
        try:
            cmd = [self.app_path]
            if args:
                cmd.extend(args)
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for app to start
            time.sleep(2)
            
            if self.process.poll() is None:
                self.is_running = True
                return True, None
            else:
                return False, "App process terminated immediately"
        except Exception as e:
            return False, f"Error starting app: {str(e)}"
    
    def stop_app(self) -> bool:
        """Stop desktop application"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.is_running = False
                return True
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.is_running = False
                return True
            except Exception as e:
                logger.error(f"Error stopping app: {e}")
                return False
        return True
    
    def is_app_running(self) -> bool:
        """Check if app is running"""
        if self.process:
            return self.process.poll() is None
        return False
    
    def get_app_output(self) -> Tuple[str, str]:
        """Get app stdout and stderr"""
        if self.process:
            try:
                stdout, stderr = self.process.communicate(timeout=1)
                return stdout or "", stderr or ""
            except subprocess.TimeoutExpired:
                return "", ""
        return "", ""


# Alternative: Use Python imports if testing in-process
class InProcessDesktopClient:
    """Client for testing desktop app in-process (imports modules directly)"""
    
    def __init__(self):
        self.license_manager = None
        self.auth_manager = None
        self.pattern_service = None
    
    def initialize(self, server_url: Optional[str] = None):
        """Initialize desktop app components"""
        try:
            from core.license_manager import LicenseManager
            from core.auth_manager import AuthManager
            from core.services.pattern_service import PatternService
            
            self.license_manager = LicenseManager.instance(server_url=server_url)
            self.auth_manager = AuthManager(server_url=server_url)
            self.pattern_service = PatternService()
            
            return True
        except Exception as e:
            logger.error(f"Error initializing desktop app components: {e}")
            return False
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """Login using AuthManager"""
        if not self.auth_manager:
            return False, "AuthManager not initialized"
        
        try:
            success, message = self.auth_manager.login(email=email, password=password)
            return success, message
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def validate_license(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validate license using LicenseManager"""
        if not self.license_manager:
            return False, None, "LicenseManager not initialized"
        
        try:
            is_valid, license_data, error = self.license_manager.validate_license()
            return is_valid, license_data, error
        except Exception as e:
            return False, None, f"License validation error: {str(e)}"
    
    def get_license_info(self) -> Optional[Dict[str, Any]]:
        """Get license information"""
        if not self.license_manager:
            return None
        
        try:
            return self.license_manager.get_license_info()
        except Exception as e:
            logger.error(f"Error getting license info: {e}")
            return None
    
    def create_pattern(self, name: str = "Test Pattern", width: int = 72, height: int = 1) -> Optional[Any]:
        """Create a new pattern"""
        if not self.pattern_service:
            return None
        
        try:
            from core.pattern import PatternMetadata
            metadata = PatternMetadata(width=width, height=height)
            pattern = self.pattern_service.create_pattern(
                name=name,
                width=width,
                height=height,
                metadata=metadata
            )
            return pattern
        except Exception as e:
            logger.error(f"Error creating pattern: {e}")
            return None
