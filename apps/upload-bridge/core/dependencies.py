"""
Dependency Manager - Handles checking and installing required system dependencies.
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Callable, Optional
from PySide6.QtCore import QObject, Signal, QProcess

logger = logging.getLogger(__name__)

class DependencyInfo:
    def __init__(self, name: str, check_cmd: List[str], install_cmd: List[str], description: str, critical: bool = False):
        self.name = name
        self.check_cmd = check_cmd
        self.install_cmd = install_cmd
        self.description = description
        self.critical = critical
        self.installed = False

class DependencyManager(QObject):
    """Manages system dependencies like Node.js, Cloudie CLI, etc."""
    
    progress_updated = Signal(int, str)  # percentage, message
    log_received = Signal(str)  # process output
    finished = Signal(bool, str)  # success, message
    
    def __init__(self):
        super().__init__()
        self.dependencies: List[DependencyInfo] = [
            DependencyInfo(
                "Node.js",
                ["node", "--version"],
                [], # Cannot easily install Node.js automatically via CLI without winget/brew
                "Required for Cloudie CLI and other tools.",
                critical=True
            ),
            DependencyInfo(
                "NPM",
                ["npm", "--version"],
                [],
                "Node Package Manager.",
                critical=True
            ),
            DependencyInfo(
                "Cloudie CLI",
                ["cloudie", "--version"],
                ["npm", "install", "-g", "@cloudie/cli"],
                "AI Pattern Generation CLI.",
                critical=False
            )
        ]
        self._current_process: Optional[QProcess] = None

    def check_all(self) -> List[DependencyInfo]:
        """Check status of all dependencies."""
        for dep in self.dependencies:
            dep.installed = self._is_installed(dep.check_cmd)
        return self.dependencies

    def _is_installed(self, cmd: List[str]) -> bool:
        try:
            # First check if the executable exists in PATH
            if not shutil.which(cmd[0]):
                return False
            # Then run the check command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def install_missing(self):
        """Install missing dependencies that have an install command."""
        missing = [d for d in self.dependencies if not d.installed and d.install_cmd]
        if not missing:
            self.finished.emit(True, "All dependencies are present.")
            return

        self._install_next(missing)

    def _install_next(self, remaining: List[DependencyInfo]):
        if not remaining:
            self.finished.emit(True, "Installation complete.")
            return

        dep = remaining[0]
        self.progress_updated.emit(0, f"Installing {dep.name}...")
        
        self._current_process = QProcess()
        self._current_process.setProcessChannelMode(QProcess.MergedChannels)
        self._current_process.readyReadStandardOutput.connect(self._handle_output)
        self._current_process.finished.connect(lambda exit_code, status: self._on_process_finished(exit_code, status, remaining))
        
        # On Windows, npm global install often needs .cmd extension or shell execution
        if sys.platform == "win32" and dep.install_cmd[0] == "npm":
            self._current_process.start("cmd.exe", ["/c"] + dep.install_cmd)
        else:
            self._current_process.start(dep.install_cmd[0], dep.install_cmd[1:])

    def _handle_output(self):
        if self._current_process:
            data = self._current_process.readAllStandardOutput().data().decode()
            self.log_received.emit(data)

    def _on_process_finished(self, exit_code, status, remaining):
        dep = remaining.pop(0)
        if exit_code == 0:
            dep.installed = True
            self.progress_updated.emit(100, f"Successfully installed {dep.name}")
            self._install_next(remaining)
        else:
            self.finished.emit(False, f"Failed to install {dep.name}. Exit code: {exit_code}")

def create_desktop_shortcut():
    """Create a desktop shortcut for the application."""
    if sys.platform != "win32":
        return False
        
    try:
        import winshell
        from win32com.client import Dispatch
        
        app_path = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve().parent.parent / "main.py")
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Upload Bridge.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = app_path
        shortcut.WorkingDirectory = os.path.dirname(app_path)
        shortcut.IconLocation = app_path
        shortcut.save()
        return True
    except Exception as e:
        logger.error(f"Failed to create desktop shortcut: {e}")
        return False

def create_start_menu_shortcut():
    """Create a start menu shortcut for the application."""
    if sys.platform != "win32":
        return False
        
    try:
        import winshell
        from win32com.client import Dispatch
        
        app_path = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve().parent.parent / "main.py")
        start_menu = winshell.start_menu()
        programs = os.path.join(start_menu, "Programs")
        if not os.path.exists(programs):
            os.makedirs(programs)
            
        path = os.path.join(programs, "Upload Bridge.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = app_path
        shortcut.WorkingDirectory = os.path.dirname(app_path)
        shortcut.IconLocation = app_path
        shortcut.save()
        return True
    except Exception as e:
        logger.error(f"Failed to create start menu shortcut: {e}")
        return False
