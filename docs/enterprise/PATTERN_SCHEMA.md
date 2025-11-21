# Pattern JSON Schema v1.0 Documentation

## Overview

The Pattern JSON Schema v1.0 provides a canonical, standardized format for LED pattern data with full validation, versioning, and migration support.

## Schema Structure

```json
{
  "schema_version": "1.0",
  "id": "uuid-v4",
  "name": "Pattern Name",
  "description": "Optional description",
  "tags": ["tag1", "tag2"],
  "created_at": "ISO-8601-timestamp",
  "modified_at": "ISO-8601-timestamp",
  "matrix": {
    "width": 16,
    "height": 16,
    "layout": "row_major",
    "wiring": "linear",
    "default_color_order": "RGB"
  },
  "frames": [
    {
      "index": 0,
      "duration_ms": 100,
      "layers": [
        {
          "id": "uuid-v4",
          "name": "base",
          "opacity": 1.0,
          "blend_mode": "normal",
          "visible": true,
          "pixels": "base64-rle-encoded-data",
          "encoding": "rle+rgba8"
        }
      ]
    }
  ],
  "effects": [],
  "metadata": {
    "author": "Author Name",
    "source_file": "/path/to/source",
    "approx_memory_bytes": 768
  }
}
```

## Key Components

### Schema Version

- **Field**: `schema_version`
- **Type**: `string`
- **Pattern**: `^1\.0$`
- **Description**: Schema version identifier

### Matrix Configuration

- **width**: Matrix width (LEDs) - integer, 1-256
- **height**: Matrix height (LEDs) - integer, 1-256
- **layout**: Pixel layout - `"row_major"` or `"column_major"`
- **wiring**: Wiring pattern - `"linear"`, `"zigzag"`, or `"serpentine"`
- **default_color_order**: Color order - `"RGB"`, `"GRB"`, `"BRG"`, `"BGR"`, `"RBG"`, or `"GBR"`

### Frames

Each frame contains:
- **index**: Frame index (0-based)
- **duration_ms**: Frame duration (1-10000ms)
- **layers**: Array of layer objects

### Layers

Each layer contains:
- **id**: Layer UUID
- **name**: Layer name
- **opacity**: Opacity (0.0-1.0)
- **blend_mode**: Blend mode (`"normal"`, `"add"`, `"multiply"`, `"screen"`)
- **visible**: Visibility flag
- **pixels**: Pixel data (RLE-encoded string or raw array)
- **encoding**: Encoding format (`"rle+rgba8"`, `"raw+rgba8"`, `"raw+rgb8"`)

### Effects

Non-destructive effects applied to frames:
- **id**: Effect UUID
- **type**: Effect type (`"scroll"`, `"rotate"`, `"mirror"`, etc.)
- **parameters**: Effect-specific parameters
- **frame_range**: Optional frame range for effect

## Pixel Encoding

### RLE Encoding (Recommended)

Run-Length Encoding compresses pixel data:

```
Format: [run_length, r, g, b, run_length, r, g, b, ...]
Encoded: Base64 string
```

Example:
- Input: `[(255,0,0), (255,0,0), (255,0,0), (0,255,0)]`
- RLE: `[3, 255, 0, 0, 1, 0, 255, 0]`
- Base64: Encoded bytes

### Raw Encoding

Uncompressed pixel array:

```json
"pixels": [[255, 0, 0], [0, 255, 0], [0, 0, 255]]
```

## Usage

### Convert Pattern to JSON

```python
from core.pattern import Pattern
from core.schemas import PatternConverter

pattern = Pattern(...)
json_data = PatternConverter.pattern_to_json(pattern, use_rle=True)
```

Or use Pattern method:

```python
json_data = pattern.to_json(use_rle=True)
```

### Convert JSON to Pattern

```python
json_data = {...}  # Pattern JSON
pattern = PatternConverter.pattern_from_json(json_data)
```

Or use Pattern static method:

```python
pattern = Pattern.from_json(json_data)
```

### Validate JSON

```python
from core.schemas import validate_pattern_json, PatternSchemaError

try:
    validate_pattern_json(json_data)
    print("Valid pattern JSON")
except PatternSchemaError as e:
    print(f"Validation error: {e}")
```

### Migration

```python
from core.schemas import migrate_pattern_json, get_schema_version

# Get version
version = get_schema_version(json_data)

# Migrate to latest
migrated = migrate_pattern_json(json_data, target_version="1.0")
```

## Validation Rules

1. **Required Fields**: `schema_version`, `id`, `name`, `matrix`, `frames`
2. **Matrix Dimensions**: 1-256 for width/height
3. **Frame Duration**: 1-10000ms
4. **Layer Opacity**: 0.0-1.0
5. **Pixel Values**: 0-255 for R, G, B
6. **UUID Format**: Valid UUID v4 format

## Schema Migration

### From Legacy Format

Legacy patterns without `schema_version` are automatically migrated:

```python
legacy_data = {
    "name": "Legacy Pattern",
    "metadata": {"width": 16, "height": 16},
    "frames": [...]
}

migrated = migrate_pattern_json(legacy_data)
# Now has schema_version: "1.0"
```

### Version Updates

Future schema versions will be supported via migration functions in `core/schemas/migration.py`.

## Best Practices

1. **Use RLE Encoding**: Reduces file size for patterns with repeated colors
2. **Include Metadata**: Add author, tags, and descriptions for better organization
3. **Validate Before Save**: Always validate JSON before saving
4. **Version Control**: Include `schema_version` in all exports

## Examples

See `tests/unit/test_pattern_schema.py` for comprehensive examples of:
- Valid schema creation
- Round-trip conversion
- RLE encoding/decoding
- Migration from legacy formats

