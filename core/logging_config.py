"""
Reusable logging configuration for Upload Bridge.

Usage:
    from core.logging_config import setup_logging
    setup_logging()
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional


def _get_level_from_env(default: str = "INFO") -> int:
    level_name = os.getenv("UPLOADBRIDGE_LOG_LEVEL") or os.getenv("LOG_LEVEL") or default
    level_name = level_name.upper()
    return getattr(logging, level_name, logging.INFO)


def setup_logging(app_name: str = "UploadBridge", level: Optional[int] = None, log_to_file: bool = False) -> None:
    """Initialize root logging handlers once.

    - Level can be provided or derived from env (UPLOADBRIDGE_LOG_LEVEL / LOG_LEVEL).
    - If log_to_file is True, writes to UPLOADBRIDGE_LOG_FILE or app_name.log.
    """
    if getattr(setup_logging, "_configured", False):
        return

    log_level = level if level is not None else _get_level_from_env()

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Basic stream handler to stdout
    try:
        logging.basicConfig(level=log_level, format=fmt, datefmt=datefmt)
    except Exception:
        # As a safety net, reinitialize with a simple handler
        root = logging.getLogger()
        root.handlers.clear()
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(log_level)
        sh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        root.addHandler(sh)
        root.setLevel(log_level)

    if log_to_file:
        try:
            file_path = os.getenv("UPLOADBRIDGE_LOG_FILE", f"{app_name}.log")
            fh = logging.FileHandler(file_path, encoding="utf-8")
            fh.setLevel(log_level)
            fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
            logging.getLogger().addHandler(fh)
        except Exception:
            # Fallback silently if file handler fails
            pass

    setup_logging._configured = True  # type: ignore[attr-defined]


