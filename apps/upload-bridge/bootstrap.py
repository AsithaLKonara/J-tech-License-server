# apps/upload-bridge/bootstrap.py

import sys
import subprocess
import importlib.util
from pathlib import Path
from tkinter import messagebox, Tk
import shutil
import logging
from logging.handlers import RotatingFileHandler

# -------------------------------------------------
# 1. FORCE PROJECT ROOT INTO sys.path (CRITICAL)
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "startup.log"

handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1_000_000,
    backupCount=3
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("bootstrap")
logger.info("Bootstrap starting")

# -------------------------------------------------
# 2. DEPENDENCY CHECK
# -------------------------------------------------
REQUIRED_PACKAGES = [
    "jsonschema>=4.0.0",
    "requests",
    "PySide6",
]

def is_installed(pkg):
    return importlib.util.find_spec(pkg) is not None

import shutil

OFFLINE_WHEELS_DIR = PROJECT_ROOT / "wheels"

def install_packages():
    if OFFLINE_WHEELS_DIR.exists():
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(OFFLINE_WHEELS_DIR),
            *REQUIRED_PACKAGES,
        ])
    else:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            *REQUIRED_PACKAGES,
        ])

def ensure_dependencies():
    missing = [p for p in REQUIRED_PACKAGES if not is_installed(p.split(">=")[0])]

    if missing:
        root = Tk()
        root.withdraw()

        if messagebox.askyesno(
            "Missing Dependencies",
            "Required dependencies are missing.\n\n"
            "They will now be installed automatically.\n\n"
            "Continue?"
        ):
            install_packages()
        else:
            sys.exit(1)

# -------------------------------------------------
# 3. SAFE APP LAUNCH
# -------------------------------------------------
def main():
    try:
        ensure_dependencies()
        logger.info("Dependencies OK")

        # ALL application imports happen AFTER this line
        from main import run_app
        logger.info("Launching app")
        run_app()

    except Exception:
        logger.exception("Fatal startup error")
        raise

if __name__ == "__main__":
    main()