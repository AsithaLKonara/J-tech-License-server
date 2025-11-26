# Developer Migration Guide

**Last Updated**: 2024  
**Purpose**: Guide for developers migrating code to use the new service layer architecture

---

## Overview

This guide helps developers migrate existing code to use the new service layer architecture, which provides better separation of concerns, testability, and maintainability.

---

## Migration Principles

1. **Use Services for Business Logic**: Move business logic from UI to services
2. **Use Repository for State**: Access pattern state through PatternRepository
3. **Use Events for Communication**: Communicate changes through events
4. **Use Error Handler for Errors**: Handle errors through ErrorHandler

---

## Migration Patterns

### Pattern 1: Loading Patterns

**Before (Direct Pattern Access)**:
```python
# In UI component
pattern = load_pattern_from_file(file_path)
self.pattern = pattern
self.current_file = file_path
```

**After (Using PatternService)**:
```python
# In UI component
from core.services.pattern_service import PatternService

service = PatternService()
pattern, format_name = service.load_pattern(file_path)
# Pattern is automatically stored in repository
# Access via: PatternRepository.get_current_pattern()
```

---

### Pattern 2: Saving Patterns

**Before (Direct Save)**:
```python
# In UI component
pattern.save_to_file(file_path)
self.current_file = file_path
self.is_dirty = False
```

**After (Using PatternService)**:
```python
# In UI component
from core.services.pattern_service import PatternService

service = PatternService()
service.save_pattern(pattern, file_path)
# Repository automatically updated
# Dirty state automatically cleared
```

---

### Pattern 3: Creating Patterns

**Before (Direct Creation)**:
```python
# In UI component
metadata = PatternMetadata(width=72, height=1)
frame = Frame(pixels=[(0,0,0)]*72, duration_ms=50)
pattern = Pattern(name="New", metadata=metadata, frames=[frame])
self.pattern = pattern
```

**After (Using PatternService)**:
```python
# In UI component
from core.services.pattern_service import PatternService

service = PatternService()
pattern = service.create_blank_pattern(name="New", width=72, height=1)
# Pattern automatically stored in repository
```

---

### Pattern 4: Exporting Patterns

**Before (Direct Export)**:
```python
# In UI component
from core.export.exporters import PatternExporter

exporter = PatternExporter()
exporter.export_binary(pattern, output_path)
```

**After (Using ExportService)**:
```python
# In UI component
from core.services.export_service import ExportService

service = ExportService()
# Validate first
is_valid, error, preview = service.validate_export(pattern, "bin")
if is_valid:
    output_path = service.export_pattern(pattern, "output.bin", "bin")
```

---

### Pattern 5: Accessing Current Pattern

**Before (Direct Reference)**:
```python
# In UI component
pattern = self.pattern  # Direct reference
if pattern is None:
    return
```

**After (Using Repository)**:
```python
# In UI component
from core.repositories.pattern_repository import PatternRepository

pattern = PatternRepository.get_current_pattern()
if pattern is None:
    return
```

---

### Pattern 6: Checking Dirty State

**Before (Direct Flag)**:
```python
# In UI component
if self.is_dirty:
    # Show unsaved changes warning
    pass
```

**After (Using Repository)**:
```python
# In UI component
from core.repositories.pattern_repository import PatternRepository

if PatternRepository.is_dirty():
    # Show unsaved changes warning
    pass
```

---

### Pattern 7: Listening to Pattern Changes

**Before (Manual Updates)**:
```python
# In UI component
def on_pattern_changed(self, pattern):
    self.pattern = pattern
    self.update_ui()
```

**After (Using Repository Signals)**:
```python
# In UI component
from core.repositories.pattern_repository import PatternRepository

def __init__(self):
    repo = PatternRepository.instance()
    repo.pattern_changed.connect(self.on_pattern_changed)

def on_pattern_changed(self, pattern):
    # Pattern automatically updated in repository
    self.update_ui()
```

---

### Pattern 8: Error Handling

**Before (Try/Except with MessageBox)**:
```python
# In UI component
try:
    pattern = load_pattern_from_file(file_path)
except Exception as e:
    QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")
```

**After (Using ErrorHandler)**:
```python
# In UI component
from core.errors import get_error_handler, PatternLoadError

handler = get_error_handler()
try:
    service = PatternService()
    pattern = service.load_pattern(file_path)
except PatternLoadError as e:
    handler.handle_pattern_error(e, file_path)
```

---

### Pattern 9: Event Publishing

**Before (No Events)**:
```python
# In UI component
pattern = create_pattern()
# No event notification
```

**After (Using EventBus)**:
```python
# In UI component
from core.events import get_event_bus, PatternCreatedEvent

# Service automatically publishes events
service = PatternService()
pattern = service.create_pattern()
# PatternCreatedEvent automatically published
```

---

### Pattern 10: Listening to Events

**Before (No Event System)**:
```python
# Manual synchronization required
```

**After (Using EventBus)**:
```python
# In UI component
from core.events import get_event_bus, PatternCreatedEvent

def __init__(self):
    bus = get_event_bus()
    bus.subscribe(PatternCreatedEvent, self.on_pattern_created)

def on_pattern_created(self, event):
    pattern = event.pattern
    self.update_ui(pattern)
```

---

## Step-by-Step Migration

### Step 1: Update Imports

Add service layer imports:
```python
from core.services.pattern_service import PatternService
from core.services.export_service import ExportService
from core.services.flash_service import FlashService
from core.repositories.pattern_repository import PatternRepository
from core.events import get_event_bus
from core.errors import get_error_handler
```

### Step 2: Initialize Services

In `__init__`:
```python
def __init__(self):
    # Initialize services
    self.pattern_service = PatternService()
    self.export_service = ExportService()
    self.flash_service = FlashService()
    self.repository = PatternRepository.instance()
    self.event_bus = get_event_bus()
    self.error_handler = get_error_handler()
```

### Step 3: Replace Direct Pattern Access

Replace `self.pattern` with repository access:
```python
# Before
pattern = self.pattern

# After
pattern = self.repository.get_current_pattern()
```

### Step 4: Replace Pattern Operations

Replace direct operations with service calls:
```python
# Before
pattern = Pattern(...)
self.pattern = pattern

# After
pattern = self.pattern_service.create_pattern(...)
```

### Step 5: Connect to Repository Signals

Connect to repository signals for automatic updates:
```python
def __init__(self):
    self.repository.pattern_changed.connect(self.on_pattern_changed)
    self.repository.pattern_cleared.connect(self.on_pattern_cleared)
```

### Step 6: Update Error Handling

Replace try/except with error handler:
```python
# Before
try:
    # operation
except Exception as e:
    QMessageBox.critical(self, "Error", str(e))

# After
try:
    # operation
except PatternLoadError as e:
    self.error_handler.handle_pattern_error(e, file_path)
```

---

## Common Pitfalls

### Pitfall 1: Forgetting to Use Repository

**Wrong**:
```python
pattern = self.pattern  # Direct access
```

**Correct**:
```python
pattern = PatternRepository.get_current_pattern()
```

### Pitfall 2: Not Using Services

**Wrong**:
```python
pattern.save_to_file(file_path)  # Direct save
```

**Correct**:
```python
service = PatternService()
service.save_pattern(pattern, file_path)
```

### Pitfall 3: Not Handling Errors

**Wrong**:
```python
try:
    pattern = load_pattern(file_path)
except:
    pass  # Silent failure
```

**Correct**:
```python
try:
    pattern = service.load_pattern(file_path)
except PatternLoadError as e:
    error_handler.handle_pattern_error(e, file_path)
```

### Pitfall 4: Not Using Events

**Wrong**:
```python
pattern = create_pattern()
# No notification to other components
```

**Correct**:
```python
pattern = service.create_pattern()
# Event automatically published
```

---

## Testing Migration

### Unit Tests

Test services independently:
```python
def test_pattern_service_load():
    service = PatternService()
    pattern, format = service.load_pattern("test.bin")
    assert pattern is not None
```

### Integration Tests

Test service integration:
```python
def test_service_repository_integration():
    service = PatternService()
    pattern = service.create_pattern()
    assert PatternRepository.get_current_pattern() == pattern
```

---

## Backward Compatibility

The new architecture maintains backward compatibility:

1. **Legacy Attributes**: Old `self.pattern` references still work (synced from repository)
2. **Gradual Migration**: Can migrate component by component
3. **No Breaking Changes**: Existing code continues to work

---

## Migration Checklist

- [ ] Update imports to include services
- [ ] Initialize services in `__init__`
- [ ] Replace direct pattern access with repository
- [ ] Replace pattern operations with service calls
- [ ] Connect to repository signals
- [ ] Update error handling to use ErrorHandler
- [ ] Subscribe to events if needed
- [ ] Update unit tests
- [ ] Update integration tests
- [ ] Remove legacy code after migration

---

## Examples

See the following files for complete examples:
- `ui/main_window.py` - MainWindow integration
- `ui/tabs/flash_tab.py` - FlashTab integration
- `ui/tabs/preview_tab.py` - PreviewTab integration
- `ui/tabs/design_tools_tab.py` - DesignToolsTab integration

---

*Developer Migration Guide - Updated: 2024*

