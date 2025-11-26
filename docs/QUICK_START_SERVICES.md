# Quick Start Guide - Service Layer

**Last Updated**: 2024  
**Purpose**: Quick reference for using the service layer in your code

---

## PatternService

### Load a Pattern

```python
from core.services.pattern_service import PatternService

service = PatternService()
pattern, format_name = service.load_pattern("/path/to/pattern.bin")
```

### Save a Pattern

```python
service = PatternService()
service.save_pattern(pattern, "/path/to/output.bin")
```

### Create a Pattern

```python
service = PatternService()
pattern = service.create_blank_pattern(name="New Pattern", width=72, height=1)
```

### Duplicate a Pattern

```python
service = PatternService()
duplicated = service.duplicate_pattern(pattern, new_name="Copy")
```

### Validate a Pattern

```python
service = PatternService()
is_valid, error = service.validate_pattern(pattern)
if not is_valid:
    print(f"Validation failed: {error}")
```

---

## ExportService

### Export a Pattern

```python
from core.services.export_service import ExportService

service = ExportService()
output_path = service.export_pattern(pattern, "output.bin", "bin")
```

### Validate Export

```python
service = ExportService()
is_valid, error, preview = service.validate_export(pattern, "bin")
if is_valid:
    # Proceed with export
    pass
```

### Get Available Formats

```python
service = ExportService()
formats = service.get_available_formats()
# Returns: ['bin', 'hex', 'dat', 'leds', 'json', ...]
```

---

## FlashService

### Build Firmware

```python
from core.services.flash_service import FlashService

service = FlashService()
build_result = service.build_firmware(
    pattern,
    chip_id="esp8266",
    config={'gpio_pin': 3}
)
```

### Upload Firmware

```python
service = FlashService()
upload_result = service.upload_firmware(
    firmware_path,
    chip_id="esp8266",
    port="COM3"
)
```

### Verify Upload

```python
service = FlashService()
is_valid, error = service.verify_upload(
    chip_id="esp8266",
    port="COM3",
    config={'firmware_path': firmware_path}
)
```

### Check Chip Support

```python
service = FlashService()
if service.is_chip_supported("esp8266"):
    # Chip is supported
    pass
```

---

## PatternRepository

### Get Current Pattern

```python
from core.repositories.pattern_repository import PatternRepository

pattern = PatternRepository.get_current_pattern()
```

### Set Current Pattern

```python
PatternRepository.set_current_pattern(pattern, file_path="/path/to/file.bin")
```

### Check Dirty State

```python
if PatternRepository.is_dirty():
    # Pattern has unsaved changes
    pass
```

### Listen to Changes

```python
repo = PatternRepository.instance()
repo.pattern_changed.connect(lambda pattern: print(f"Pattern changed: {pattern.name}"))
```

---

## EventBus

### Subscribe to Events

```python
from core.events import get_event_bus, PatternCreatedEvent

bus = get_event_bus()

def on_pattern_created(event):
    print(f"Pattern created: {event.pattern.name}")

bus.subscribe(PatternCreatedEvent, on_pattern_created)
```

### Publish Events

```python
from core.events import get_event_bus, PatternCreatedEvent

bus = get_event_bus()
bus.publish(PatternCreatedEvent(pattern))
```

### Get Event History

```python
bus = get_event_bus()
history = bus.get_event_history(PatternCreatedEvent, limit=10)
```

---

## ErrorHandler

### Handle Errors

```python
from core.errors import get_error_handler, PatternLoadError

handler = get_error_handler()

try:
    service = PatternService()
    pattern = service.load_pattern(file_path)
except PatternLoadError as e:
    handler.handle_pattern_error(e, file_path)
```

### Set User Notification

```python
handler = get_error_handler()

def notify_user(message, severity):
    QMessageBox.critical(None, "Error", message)

handler.set_user_notification_callback(notify_user)
```

### Register Custom Handler

```python
handler = get_error_handler()

def custom_handler(error):
    # Custom error handling
    pass

handler.register_handler(PatternLoadError, custom_handler)
```

---

## Complete Example

```python
from core.services.pattern_service import PatternService
from core.services.export_service import ExportService
from core.repositories.pattern_repository import PatternRepository
from core.events import get_event_bus, PatternCreatedEvent
from core.errors import get_error_handler, PatternLoadError

# Initialize
pattern_service = PatternService()
export_service = ExportService()
repository = PatternRepository.instance()
event_bus = get_event_bus()
error_handler = get_error_handler()

# Subscribe to events
def on_pattern_created(event):
    print(f"Pattern created: {event.pattern.name}")

event_bus.subscribe(PatternCreatedEvent, on_pattern_created)

# Load pattern
try:
    pattern, format_name = pattern_service.load_pattern("/path/to/pattern.bin")
    print(f"Loaded {format_name} pattern: {pattern.name}")
except PatternLoadError as e:
    error_handler.handle_pattern_error(e, "/path/to/pattern.bin")

# Export pattern
is_valid, error, preview = export_service.validate_export(pattern, "bin")
if is_valid:
    output_path = export_service.export_pattern(pattern, "output.bin", "bin")
    print(f"Exported to: {output_path}")
```

---

*Quick Start Guide - Updated: 2024*

