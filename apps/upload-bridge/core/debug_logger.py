"""
Debug Logger - Runtime debugging instrumentation for DEBUG MODE.

Writes NDJSON logs to the debug log file for runtime analysis.
"""
import json
import os
import traceback
from typing import Any, Dict, Optional
from pathlib import Path

# Debug log path from system configuration
DEBUG_LOG_PATH = Path(__file__).parent.parent / ".cursor" / "debug.log"


def _write_log_entry(entry: Dict[str, Any]) -> None:
    """Write a single NDJSON log entry to the debug log file."""
    try:
        # Ensure directory exists
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Append NDJSON line
        with open(DEBUG_LOG_PATH, 'a', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    except Exception:
        # Silently fail to avoid breaking application
        pass


def debug_log(
    location: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    hypothesis_id: Optional[str] = None,
    session_id: str = "debug-session",
    run_id: str = "run1"
) -> None:
    """
    Write a debug log entry.
    
    Args:
        location: File and line location (e.g., "main.py:42")
        message: Log message description
        data: Optional data dictionary
        hypothesis_id: Optional hypothesis ID (A, B, C, etc.)
        session_id: Session identifier
        run_id: Run identifier (run1, run2, post-fix, etc.)
    """
    import time
    
    entry = {
        "id": f"log_{int(time.time() * 1000)}",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data or {},
        "sessionId": session_id,
        "runId": run_id,
        "hypothesisId": hypothesis_id
    }
    
    _write_log_entry(entry)


def debug_log_function_entry(
    func_name: str,
    location: str,
    params: Optional[Dict[str, Any]] = None,
    hypothesis_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log function entry with parameters."""
    debug_log(
        location=location,
        message=f"Function entry: {func_name}",
        data={"function": func_name, "parameters": params or {}},
        hypothesis_id=hypothesis_id,
        **kwargs
    )


def debug_log_function_exit(
    func_name: str,
    location: str,
    return_value: Any = None,
    hypothesis_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log function exit with return value."""
    # Serialize return value safely
    ret_data = None
    if return_value is not None:
        try:
            if isinstance(return_value, (str, int, float, bool, type(None))):
                ret_data = return_value
            elif isinstance(return_value, (list, dict)):
                ret_data = str(return_value)[:200]  # Truncate long values
            else:
                ret_data = str(type(return_value).__name__)
        except Exception:
            ret_data = "<unserializable>"
    
    debug_log(
        location=location,
        message=f"Function exit: {func_name}",
        data={"function": func_name, "return_value": ret_data},
        hypothesis_id=hypothesis_id,
        **kwargs
    )


def debug_log_error(
    location: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    hypothesis_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log an error with traceback."""
    debug_log(
        location=location,
        message=f"Error: {type(error).__name__}: {str(error)}",
        data={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()[:500],  # Truncate long tracebacks
            "context": context or {}
        },
        hypothesis_id=hypothesis_id,
        **kwargs
    )


def debug_log_state_change(
    location: str,
    state_name: str,
    old_value: Any = None,
    new_value: Any = None,
    hypothesis_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log a state change."""
    debug_log(
        location=location,
        message=f"State change: {state_name}",
        data={
            "state": state_name,
            "old_value": str(old_value)[:200] if old_value is not None else None,
            "new_value": str(new_value)[:200] if new_value is not None else None
        },
        hypothesis_id=hypothesis_id,
        **kwargs
    )

