# Upload Bridge API Reference

## Overview

Complete API reference for Upload Bridge v3.0 - Enterprise Edition.

## Core APIs

### Pattern Schema API

#### `Pattern.to_json(use_rle: bool = True) -> Dict`

Convert Pattern object to canonical JSON schema format.

**Parameters:**
- `use_rle`: Whether to use RLE compression for pixel data (default: True)

**Returns:**
- Dictionary conforming to pattern JSON schema v1.0

**Example:**
```python
pattern = Pattern(...)
json_data = pattern.to_json(use_rle=True)
```

#### `Pattern.from_json(data: Dict) -> Pattern`

Create Pattern object from canonical JSON schema format.

**Parameters:**
- `data`: Pattern JSON dictionary conforming to schema v1.0

**Returns:**
- Pattern object

**Example:**
```python
json_data = {...}  # Pattern JSON
pattern = Pattern.from_json(json_data)
```

#### `validate_pattern_json(data: Dict, schema: Optional[Dict] = None) -> bool`

Validate pattern JSON against schema.

**Parameters:**
- `data`: Pattern JSON data
- `schema`: Optional schema (defaults to PATTERN_SCHEMA_V1)

**Returns:**
- True if valid

**Raises:**
- `PatternSchemaError`: If validation fails

### Project File API

#### `save_project(pattern: Pattern, file_path: Path, metadata: Optional[ProjectMetadata] = None, use_rle: bool = True) -> None`

Save pattern as project file (.ledproj).

**Parameters:**
- `pattern`: Pattern to save
- `file_path`: Path to save project file
- `metadata`: Optional project metadata
- `use_rle`: Whether to use RLE compression

**Example:**
```python
from core.project import save_project

pattern = Pattern(...)
metadata = ProjectMetadata(name="My Project")
save_project(pattern, Path("project.ledproj"), metadata=metadata)
```

#### `load_project(file_path: Path) -> Tuple[Pattern, ProjectMetadata]`

Load pattern and metadata from project file.

**Parameters:**
- `file_path`: Path to project file

**Returns:**
- Tuple of (Pattern, ProjectMetadata)

**Example:**
```python
from core.project import load_project

pattern, metadata = load_project(Path("project.ledproj"))
```

### Uploader Adapter API

#### `get_adapter(chip_id: str, chip_variant: Optional[str] = None) -> Optional[UploaderAdapter]`

Get uploader adapter for chip.

**Parameters:**
- `chip_id`: Chip identifier (e.g., "ESP32", "STM32F407")
- `chip_variant`: Optional chip variant (e.g., "ESP32-C3")

**Returns:**
- UploaderAdapter instance or None if not found

**Example:**
```python
from uploaders.adapter_registry import get_adapter

adapter = get_adapter("ESP32", "ESP32-C3")
if adapter:
    device = adapter.detect_device(port="/dev/ttyUSB0")
    if device:
        result = adapter.build_firmware(pattern, Path("firmware.bin"))
```

#### `detect_adapter(port: Optional[str] = None) -> Optional[Tuple[UploaderAdapter, DeviceInfo]]`

Auto-detect adapter for connected device.

**Parameters:**
- `port`: Optional serial port (auto-detect if None)

**Returns:**
- Tuple of (UploaderAdapter, DeviceInfo) if detected, None otherwise

**Example:**
```python
from uploaders.adapter_registry import detect_adapter

result = detect_adapter(port="/dev/ttyUSB0")
if result:
    adapter, device_info = result
    print(f"Detected: {device_info.chip_id} on {device_info.port}")
```

#### `UploaderAdapter.detect_device(port: Optional[str] = None) -> Optional[DeviceInfo]`

Detect connected device.

**Parameters:**
- `port`: Optional serial port

**Returns:**
- DeviceInfo if detected, None otherwise

#### `UploaderAdapter.build_firmware(pattern: Pattern, output_path: Path, options: Optional[Dict[str, Any]] = None) -> BuildResult`

Build firmware from pattern.

**Parameters:**
- `pattern`: Pattern object
- `output_path`: Path to save firmware binary
- `options`: Optional build options

**Returns:**
- BuildResult with success status and firmware path

#### `UploaderAdapter.flash_firmware(firmware_path: Path, device_info: DeviceInfo, options: Optional[FlashOptions] = None) -> FlashResult`

Flash firmware to device.

**Parameters:**
- `firmware_path`: Path to firmware binary
- `device_info`: Device information
- `options`: Optional flash options

**Returns:**
- FlashResult enum

#### `UploaderAdapter.verify_firmware(firmware_path: Path, device_info: DeviceInfo, expected_hash: Optional[str] = None) -> VerifyResult`

Verify flashed firmware.

**Parameters:**
- `firmware_path`: Path to firmware binary
- `device_info`: Device information
- `expected_hash`: Optional expected hash

**Returns:**
- VerifyResult enum

### Verification API

#### `verify_firmware_hash(firmware_path: Path, device_info: DeviceInfo, adapter: UploaderAdapter, expected_hash: Optional[str] = None) -> Tuple[VerifyResult, Optional[str]]`

Verify firmware hash.

**Parameters:**
- `firmware_path`: Path to firmware binary
- `device_info`: Device information
- `adapter`: UploaderAdapter instance
- `expected_hash`: Optional expected hash

**Returns:**
- Tuple of (VerifyResult, actual_hash)

**Example:**
```python
from uploaders.verification import verify_firmware_hash

result, actual_hash = verify_firmware_hash(
    firmware_path=Path("firmware.bin"),
    device_info=device_info,
    adapter=adapter,
    expected_hash="abc123..."
)
```

### Build Manifest API

#### `generate_build_manifest(pattern: Pattern, export_format: str = "bin", device_profiles: Optional[List[str]] = None, firmware_bytes: Optional[bytes] = None) -> BuildManifest`

Generate build manifest for exported pattern.

**Parameters:**
- `pattern`: Pattern object
- `export_format`: Export format (bin, hex, leds, etc.)
- `device_profiles`: Optional list of device profile IDs
- `firmware_bytes`: Optional firmware binary

**Returns:**
- BuildManifest object

**Example:**
```python
from core.export.build_manifest import generate_build_manifest

manifest = generate_build_manifest(
    pattern=pattern,
    export_format="bin",
    device_profiles=["esp32"],
    firmware_bytes=firmware_bytes
)
manifest.save(Path("manifest.json"))
```

### Layer Blending API

#### `blend_pixels(bottom: RGB, top: RGB, opacity: float, blend_mode: BlendMode = BlendMode.NORMAL) -> RGB`

Blend two pixels using specified blend mode.

**Parameters:**
- `bottom`: Bottom pixel (R, G, B)
- `top`: Top pixel (R, G, B)
- `opacity`: Top pixel opacity (0.0-1.0)
- `blend_mode`: Blend mode to use

**Returns:**
- Blended pixel (R, G, B)

**Blend Modes:**
- `BlendMode.NORMAL`: Alpha compositing
- `BlendMode.ADD`: Additive blending
- `BlendMode.MULTIPLY`: Multiply blending
- `BlendMode.SCREEN`: Screen blending

**Example:**
```python
from domain.layer_blending.blending import blend_pixels, BlendMode

bottom = (255, 0, 0)
top = (0, 255, 0)
result = blend_pixels(bottom, top, opacity=0.5, blend_mode=BlendMode.ADD)
```

#### `composite_layers(layers: List[Tuple[List[RGB], float, BlendMode, bool]], pixel_count: int) -> List[RGB]`

Composite multiple layers into single pixel array.

**Parameters:**
- `layers`: List of (pixels, opacity, blend_mode, visible) tuples
- `pixel_count`: Expected number of pixels

**Returns:**
- Composited pixel array

### Drawing Tools API

#### `create_tool(tool_type: str, brush: Brush = None) -> DrawingTool`

Create drawing tool by type.

**Parameters:**
- `tool_type`: Tool type ("pixel", "rectangle", "circle", "line", "fill", "gradient", "random", "text")
- `brush`: Optional brush settings

**Returns:**
- DrawingTool instance

**Example:**
```python
from domain.drawing.tools import create_tool
from domain.drawing.brush import Brush, BrushSettings

brush = Brush(BrushSettings(size=3, shape=BrushShape.CIRCLE))
tool = create_tool("pixel", brush=brush)
new_frame = tool.apply(frame, (5, 5), (5, 5), (255, 0, 0), 16, 16)
```

### Automation Actions API

#### `create_action(action_type: str, parameters: Optional[Dict[str, Any]] = None, frame_range: Optional[Tuple[int, int]] = None) -> ParametricAction`

Create parametric action.

**Parameters:**
- `action_type`: Action type ("scroll", "rotate", "mirror", "flip", "invert", "wipe", "reveal", "bounce")
- `parameters`: Optional parameters dict
- `frame_range`: Optional frame range

**Returns:**
- ParametricAction instance

**Example:**
```python
from domain.automation.parametric_actions import create_action

action = create_action(
    action_type="scroll",
    parameters={"direction": "right", "speed": 1.0, "distance": 1},
    frame_range=(0, 9)
)
new_pattern = action.apply(pattern)
```

### Security API

#### `ProjectEncryption.encrypt_project(project_data: dict, password: str, output_path: Path) -> bool`

Encrypt project file.

**Parameters:**
- `project_data`: Project data dictionary
- `password`: Encryption password
- `output_path`: Path to save encrypted file

**Returns:**
- True if encryption successful

#### `ProjectEncryption.decrypt_project(encrypted_path: Path, password: str) -> Optional[dict]`

Decrypt project file.

**Parameters:**
- `encrypted_path`: Path to encrypted file
- `password`: Decryption password

**Returns:**
- Project data dictionary or None if decryption fails

#### `ProjectSigning.sign_project(project_data: dict, private_key_pem: bytes) -> dict`

Sign project file.

**Parameters:**
- `project_data`: Project data dictionary
- `private_key_pem`: Private key in PEM format

**Returns:**
- Project data dictionary with signature

#### `ProjectSigning.verify_project(project_data: dict, public_key_pem: bytes) -> bool`

Verify project file signature.

**Parameters:**
- `project_data`: Project data dictionary with signature
- `public_key_pem`: Public key in PEM format

**Returns:**
- True if signature is valid

## Error Handling

All APIs use standard Python exceptions:

- `PatternSchemaError`: Schema validation errors
- `ProjectFileError`: Project file operation errors
- `TypeError`: Type validation errors
- `ValueError`: Invalid parameter values
- `RuntimeError`: Runtime errors

## Best Practices

1. **Always validate input**: Use schema validation for JSON data
2. **Handle None values**: Check for None returns from detection methods
3. **Use type hints**: All APIs are type-annotated
4. **Check availability**: Use `is_available()` methods before using optional features
5. **Handle errors gracefully**: Wrap operations in try/except blocks

