#!/usr/bin/env python3
"""
Quick launcher for Design Tools Tab test GUI.

Usage:
    python tests/gui/run_tests.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

if __name__ == "__main__":
    from tests.gui.test_design_tools_gui import main
    main()

