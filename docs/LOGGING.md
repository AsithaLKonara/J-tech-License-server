# Logging Guide

This project uses the Python `logging` library with a shared initializer.

- Entry point initializes logging early via `core/logging_config.setup_logging()`.
- Modules acquire a logger with:
  
  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```

- Use levels appropriately:
  - `logger.debug()` for verbose developer diagnostics
  - `logger.info()` for high-level progress
  - `logger.warning()` for recoverable issues
  - `logger.error()` for failures
  - `logger.exception()` inside `except` blocks

## Configuration

Environment variables:
- `UPLOADBRIDGE_LOG_LEVEL` (INFO, DEBUG, WARNING, ERROR)
- `UPLOADBRIDGE_LOG_FILE` (optional, file path to write logs)

Example:
```bash
UPLOADBRIDGE_LOG_LEVEL=DEBUG python main.py
```

## Rationale

- Console `print()` in app code is replaced with structured logging for consistency, routing, and CI visibility.
- Tests may still use `print()`; Ruff is configured to ignore print in tests.

## Tools

- Ruff enforces no `print()` in non-test code (rule T201).
- Pre-commit runs Ruff (fix) and Black formatting.
- CI runs Ruff, Black (check), tests, and the project checkup script.


