"""
History Management - Enhanced undo/redo with delta compression

Provides unlimited depth undo/redo with snapshot diffing for memory efficiency.
"""

# Import from parent module to avoid circular import
import sys
from pathlib import Path

# Get the parent directory and import history.py directly
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import using importlib to avoid module name conflicts
import importlib.util
history_module_path = parent_dir / "history.py"
spec = importlib.util.spec_from_file_location("domain_history", history_module_path)
domain_history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(domain_history)

HistoryManager = domain_history.HistoryManager
FrameStateCommand = domain_history.FrameStateCommand
HistoryCommand = domain_history.HistoryCommand

from .delta import (
    StateDelta,
    compute_delta,
    apply_delta,
)

__all__ = [
    'HistoryManager',
    'HistoryCommand',
    'FrameStateCommand',
    'StateDelta',
    'compute_delta',
    'apply_delta',
]

