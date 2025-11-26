# Service Layer Architecture

**Last Updated**: 2024  
**Status**: Complete

---

## Overview

The service layer provides a clean separation between the UI and business logic, improving testability, maintainability, and code organization.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer                             │
│  (MainWindow, Tabs, Dialogs, Widgets)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Uses
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Service Layer                           │
│  PatternService │ ExportService │ FlashService          │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Uses
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Repository Layer                           │
│              PatternRepository                          │
│         (Single Source of Truth)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Manages
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Domain Layer                            │
│  Pattern │ Frame │ PatternMetadata                      │
└─────────────────────────────────────────────────────────┘
```

---

## Services

### PatternService

**Purpose**: Business logic for pattern operations.

**Methods**:
- `load_pattern(file_path)` - Load pattern from file
- `save_pattern(pattern, file_path)` - Save pattern to file
- `create_blank_pattern(name, width, height)` - Create new pattern
- `duplicate_pattern(pattern, new_name)` - Duplicate pattern
- `validate_pattern(pattern)` - Validate pattern

**Events Published**:
- `PatternCreatedEvent`
- `PatternLoadedEvent`
- `PatternSavedEvent`
- `PatternDuplicatedEvent`

**Usage**:
```python
service = PatternService()
pattern, format_name = service.load_pattern("/path/to/pattern.bin")
service.save_pattern(pattern, "/path/to/output.bin")
```

---

### ExportService

**Purpose**: Business logic for pattern export operations.

**Methods**:
- `export_pattern(pattern, output_path, format)` - Export pattern
- `validate_export(pattern, format)` - Validate export
- `get_available_formats()` - Get supported formats
- `get_export_preview(pattern, format)` - Get export preview

**Supported Formats**: bin, hex, dat, leds, json, csv, txt, ledproj, h

**Usage**:
```python
service = ExportService()
output_path = service.export_pattern(pattern, "output.bin", "bin")
```

---

### FlashService

**Purpose**: Business logic for firmware building and uploading.

**Methods**:
- `build_firmware(pattern, chip_id, config)` - Build firmware
- `upload_firmware(firmware_path, chip_id, port, config)` - Upload firmware
- `verify_upload(chip_id, port, config)` - Verify upload
- `list_supported_chips()` - List supported chips
- `is_chip_supported(chip_id)` - Check chip support

**Usage**:
```python
service = FlashService()
build_result = service.build_firmware(pattern, "esp8266", config={'gpio_pin': 3})
upload_result = service.upload_firmware(build_result.firmware_path, "esp8266", port="COM3")
```

---

## PatternRepository

**Purpose**: Single source of truth for pattern state.

**Methods**:
- `get_current_pattern()` - Get current pattern
- `set_current_pattern(pattern, file_path)` - Set current pattern
- `clear_pattern()` - Clear current pattern
- `get_current_file()` - Get current file path
- `is_dirty()` - Check if pattern has unsaved changes
- `set_dirty(dirty)` - Mark pattern as dirty

**Signals**:
- `pattern_changed(Pattern)` - Emitted when pattern changes
- `pattern_cleared()` - Emitted when pattern is cleared

**Usage**:
```python
repo = PatternRepository.instance()
pattern = repo.get_current_pattern()
repo.pattern_changed.connect(callback)
```

---

## Event System

### EventBus

**Purpose**: Centralized event dispatching for domain events.

**Methods**:
- `subscribe(event_type, handler)` - Subscribe to events
- `publish(event)` - Publish event
- `unsubscribe(event_type, handler)` - Unsubscribe from events
- `get_event_history(event_type, limit)` - Get event history

**Usage**:
```python
from core.events import get_event_bus, PatternCreatedEvent

bus = get_event_bus()
bus.subscribe(PatternCreatedEvent, handler_function)
bus.publish(PatternCreatedEvent(pattern))
```

---

## Error Handling

### ErrorHandler

**Purpose**: Centralized error handling.

**Methods**:
- `handle_error(error, severity, show_to_user, context)` - Handle error
- `handle_pattern_error(error, file_path)` - Handle pattern error
- `handle_export_error(error, format)` - Handle export error
- `handle_flash_error(error, chip_id, port)` - Handle flash error
- `register_handler(exception_type, handler)` - Register custom handler
- `set_user_notification_callback(callback)` - Set user notification callback

**Custom Exceptions**:
- `PatternError`, `PatternLoadError`, `PatternSaveError`
- `ExportError`, `ExportValidationError`
- `FlashError`, `FlashBuildError`, `FlashUploadError`

**Usage**:
```python
from core.errors import get_error_handler, PatternLoadError

handler = get_error_handler()
try:
    # ... operation ...
except PatternLoadError as e:
    handler.handle_pattern_error(e, file_path="/path/to/file.bin")
```

---

## Component Architecture (Proof of Concept)

### PatternOperationsComponent

Handles pattern-level operations (create, load, save, duplicate).

### FrameManagementComponent

Handles frame-level operations (add, delete, duplicate, move).

### CanvasControllerComponent

Handles canvas operations and pixel manipulation.

---

## Benefits

1. **Separation of Concerns**: UI separated from business logic
2. **Testability**: Services can be tested independently
3. **Maintainability**: Changes to business logic don't affect UI
4. **Reusability**: Services can be used by multiple UI components
5. **Consistency**: Single source of truth through PatternRepository
6. **Event-Driven**: Decoupled communication through events
7. **Error Handling**: Centralized error management

---

## Migration Path

1. ✅ Created PatternRepository
2. ✅ Created Service Layer
3. ✅ Integrated into MainWindow
4. ✅ Integrated into FlashTab
5. ✅ Integrated into PreviewTab
6. ✅ Integrated into DesignToolsTab
7. ✅ Added unit tests
8. ✅ Added integration tests
9. ✅ Added domain events
10. ✅ Added error handling

---

## Testing

### Unit Tests
- `tests/unit/test_pattern_repository.py`
- `tests/unit/test_pattern_service.py`
- `tests/unit/test_export_service.py`
- `tests/unit/test_flash_service.py`
- `tests/unit/test_event_bus.py`
- `tests/unit/test_error_handler.py`

### Integration Tests
- `tests/integration/test_service_integration.py`
- `tests/integration/test_ui_service_integration.py`

### Performance Tests
- `tests/performance/test_service_performance.py`

---

## Future Improvements

1. **Large Class Refactoring**: Complete refactoring of DesignToolsTab
2. **More Events**: Add more domain events as needed
3. **Error Recovery**: Add error recovery mechanisms
4. **Caching**: Add caching layer for performance
5. **Async Operations**: Add async support for long-running operations

---

*Architecture Documentation - Updated: 2024*

