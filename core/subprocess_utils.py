"""
Subprocess utilities for Windows to prevent console windows from showing.
"""

import os
import subprocess
from typing import Dict


def get_hidden_subprocess_kwargs() -> Dict:
    """Return kwargs to hide console windows on Windows; no-op on other OSes."""
    if os.name == 'nt':
        # CREATE_NO_WINDOW prevents a console window. STARTF_USESHOWWINDOW hides if created.
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        return {"startupinfo": startupinfo, "creationflags": creationflags}
    return {}


def run_hidden(cmd, **kwargs) -> subprocess.CompletedProcess:
    """Convenience wrapper for subprocess.run with hidden window on Windows."""
    merged = {**kwargs, **get_hidden_subprocess_kwargs()}
    return subprocess.run(cmd, **merged)


def popen_hidden(cmd, **kwargs) -> subprocess.Popen:
    """Convenience wrapper for subprocess.Popen with hidden window on Windows."""
    merged = {**kwargs, **get_hidden_subprocess_kwargs()}
    return subprocess.Popen(cmd, **merged)


