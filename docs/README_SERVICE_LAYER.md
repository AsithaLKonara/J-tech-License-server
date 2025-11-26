# Service Layer - Quick Reference

**Last Updated**: 2024

---

## 🚀 Quick Start

### Pattern Operations

```python
from core.services.pattern_service import PatternService

service = PatternService()

# Create
pattern = service.create_blank_pattern(name="New", width=72, height=1)

# Load
pattern, format = service.load_pattern("/path/to/file.bin")

# Save
service.save_pattern(pattern, "/path/to/output.bin")

# Duplicate
duplicated = service.duplicate_pattern(pattern)
```

### Export Operations

```python
from core.services.export_service import ExportService

service = ExportService()

# Validate
is_valid, error, preview = service.validate_export(pattern, "bin")

# Export
if is_valid:
    output_path = service.export_pattern(pattern, "output.bin", "bin")
```

### Flash Operations

```python
from core.services.flash_service import FlashService

service = FlashService()

# Build
build_result = service.build_firmware(pattern, "esp8266", config={'gpio_pin': 3})

# Upload
upload_result = service.upload_firmware(build_result.firmware_path, "esp8266", port="COM3")
```

### Repository Access

```python
from core.repositories.pattern_repository import PatternRepository

# Get current pattern
pattern = PatternRepository.get_current_pattern()

# Check dirty state
if PatternRepository.is_dirty():
    # Has unsaved changes
    pass

# Listen to changes
repo = PatternRepository.instance()
repo.pattern_changed.connect(lambda p: print(f"Pattern changed: {p.name}"))
```

### Events

```python
from core.events import get_event_bus, PatternCreatedEvent

bus = get_event_bus()

# Subscribe
bus.subscribe(PatternCreatedEvent, lambda e: print(f"Created: {e.pattern.name}"))

# Publish (usually done by services automatically)
bus.publish(PatternCreatedEvent(pattern))
```

### Error Handling

```python
from core.errors import get_error_handler, PatternLoadError

handler = get_error_handler()

try:
    service = PatternService()
    pattern = service.load_pattern(file_path)
except PatternLoadError as e:
    handler.handle_pattern_error(e, file_path)
```

---

## 📚 Full Documentation

- **Architecture**: `docs/architecture/SERVICE_LAYER_ARCHITECTURE.md`
- **Diagrams**: `docs/architecture/SERVICE_LAYER_DIAGRAM.md`
- **Migration Guide**: `docs/DEVELOPER_MIGRATION_GUIDE.md`
- **Quick Start**: `docs/QUICK_START_SERVICES.md`

---

*Service Layer Quick Reference - Updated: 2024*

