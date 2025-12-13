# Configuration Guide - Upload Bridge

This guide explains the configuration systems in Upload Bridge and when to use each.

---

## Configuration Systems Overview

Upload Bridge uses two configuration systems:

1. **Enterprise Config Manager** (`core.config`) - For application settings
2. **YAML Config Loaders** (`config`) - For chip database and app config files

---

## 1. Enterprise Config Manager (`core.config`)

**Purpose**: Centralized application configuration with environment-based settings.

**Usage**:
```python
from core.config import get_config

config = get_config()
app_version = config.get('app_version')
log_level = config.get('log_level', 'INFO')
```

**Features**:
- Environment-based configuration (dev/staging/prod)
- Loads from environment variables
- Loads from YAML config files (`config/app_config.yaml`)
- Falls back to JSON config files if YAML doesn't exist
- Provides defaults
- Validates configuration values
- Secrets management

**Configuration Sources** (in order of precedence):
1. Environment variables (highest priority)
2. YAML config file (`config/app_config.yaml`)
3. JSON config file (`config/{environment}.json`)
4. Default values (lowest priority)

**When to Use**:
- Accessing application settings in code
- Getting version, logging, performance settings
- Feature flags
- Environment-specific configuration

---

## 2. YAML Config Loaders (`config`)

**Purpose**: Load chip database and application configuration from YAML files.

**Usage**:
```python
from config import load_chip_database, load_app_config

# Load chip database
chip_db = load_chip_database()
chips = chip_db.get('chips', {})

# Load app config (legacy - prefer core.config)
app_config = load_app_config()
```

**Files**:
- `config/chip_database.yaml` - Chip specifications
- `config/app_config.yaml` - Application settings (used by ConfigManager)

**When to Use**:
- Loading chip database in uploader registry
- Direct YAML file access
- Legacy code that hasn't migrated to ConfigManager

---

## Import Patterns

### For Application Configuration
```python
# ✅ CORRECT - Use enterprise config manager
from core.config import get_config
config = get_config()
version = config.get('app_version')
```

### For Chip Database
```python
# ✅ CORRECT - Use centralized loader
from config import load_chip_database
chip_db = load_chip_database()
```

### ❌ AVOID - Direct YAML Loading
```python
# ❌ DON'T DO THIS - Use centralized loaders
import yaml
with open('config/chip_database.yaml') as f:
    data = yaml.safe_load(f)
```

---

## Configuration File Structure

### app_config.yaml
```yaml
# Upload Bridge - Application Configuration
# Version: 3.0.0

# UI Settings
ui:
  theme: "dark"
  window_width: 1200
  window_height: 800
  auto_save: true
  preview_fps: 30

# Build Settings
build:
  default_output_dir: "build"
  clean_before_build: true
  verbose_output: false

# Upload Settings
upload:
  verify_after_upload: true
  auto_reset: true
  timeout: 30

# Pattern Settings
pattern:
  default_brightness: 1.0
  default_speed: 1.0
  max_leds: 2000
  max_frames: 10000

# Logging
logging:
  level: "INFO"
  file: "upload_bridge.log"
  max_size: "10MB"
  backup_count: 5
```

### chip_database.yaml
```yaml
chips:
  esp32:
    name: "ESP32"
    family: "ESP"
    uploader: "esp_uploader"
    # ... chip specifications

uploaders:
  esp_uploader:
    class: "EspUploader"
    module: "uploaders.esp_uploader"

defaults:
  brightness: 1.0
  frame_duration: 100
  color_order: "RGB"
```

---

## Environment Variables

You can override any config setting using environment variables:

```bash
# Set app version
export APP_VERSION=3.0.0

# Set log level
export LOG_LEVEL=DEBUG

# Enable debug mode
export DEBUG=true
```

Environment variables take precedence over file-based configuration.

---

## Migration Notes

### From Direct YAML Loading
**Old**:
```python
import yaml
with open('config/chip_database.yaml') as f:
    data = yaml.safe_load(f)
```

**New**:
```python
from config import load_chip_database
data = load_chip_database()
```

### From Empty Config Modules
The `config/app_config.py` and `config/chip_database.py` modules are import aliases that re-export functions from `config/__init__.py`. This allows both import styles:
- `from config import load_chip_database` (preferred)
- `from config.chip_database import load_chip_database` (also works)

Both are valid - the empty modules serve as convenience aliases.

---

## Best Practices

1. **Use ConfigManager for app settings**: Always use `core.config.get_config()` for application configuration
2. **Use centralized loaders**: Use `config.load_chip_database()` instead of direct YAML loading
3. **Don't duplicate loading logic**: If you need to load config, use existing functions
4. **Environment variables for overrides**: Use env vars for deployment-specific settings
5. **Validate before use**: ConfigManager validates values, but check for None when using loaders

---

## Troubleshooting

### Config not loading
- Check file exists: `config/app_config.yaml` or `config/{environment}.json`
- Check file permissions
- Check YAML syntax (use a YAML validator)
- Check logs for loading errors

### Wrong values
- Check environment variables (they override files)
- Check file format (YAML vs JSON)
- Check ConfigManager defaults

### Import errors
- Ensure `pyyaml` is installed for YAML support
- Check Python path includes project root
- Verify module structure matches imports

---

**Last Updated**: 2025-01-XX  
**Version**: 3.0.0

