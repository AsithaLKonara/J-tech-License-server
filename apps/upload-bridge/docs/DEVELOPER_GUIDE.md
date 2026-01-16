# LED Matrix Studio - Developer Guide

## Architecture Overview

LED Matrix Studio is built on a clean, modular architecture designed for scalability and maintainability.

### Core Architecture

```
domain/          # Data models (Project, Timeline, LayerTrack, PixelBuffer)
core/            # Business logic (compositor, automation, export, etc.)
ui/              # User interface (PyQt6 widgets and controllers)
tests/           # Unit and integration tests
```

### Key Components

#### Domain Layer (`domain/`)

**Data Models:**
- `Project`: Root container for animation data
- `Timeline`: FPS and duration management
- `LayerTrack`: Individual animation layer with frames and keyframes
- `PixelBuffer`: NumPy array for pixel data (H×W×3 RGB)

**Animation:**
- `Keyframe`: Single keyframe with value and easing
- `KeyframeTrack`: Collection of keyframes for a property
- `BezierKeyframe`: Bezier curve keyframes with control points
- `BezierKeyframeTrack`: Bezier keyframe collection

**Effects:**
- `EffectType`: Enumeration of available effects
- `EffectConfig`: Effect configuration and keyframe properties

#### Core Layer (`core/`)

**Project Management:**
- `project_manager.py`: Create projects and layers
- `project_serializer.py`: Serialize/deserialize projects
- `frame_utils.py`: Frame creation utilities

**Rendering:**
- `compositor.py`: Layer compositing and blend modes
- `render_frame()`: Render a single frame from project

**Automation:**
- `automation/engine.py`: Automation execution engine
- `automation/effects.py`: LED-specific effect implementations

**Timeline:**
- `timeline_manager.py`: Retiming and FPS changes
- `RetimingMode`: Interpolation modes (nearest, linear, hold)

**Export:**
- `export_manager.py`: General export formats (JSON, CSV, Binary)
- `video_exporter.py`: Video exports (MP4, GIF)
- `led_hardware_exporter.py`: LED protocol exports

**Playback:**
- `playback_engine.py`: Real-time animation playback

**Versioning:**
- `version_manager.py`: Project versioning and undo/redo

**Cloud Sync:**
- `cloud_sync.py`: Local file-based cloud synchronization

**Performance:**
- `performance_profiler.py`: Performance monitoring and benchmarking

#### UI Layer (`ui/`)

**Controllers:**
- `editor_controller.py`: Main editor controller (MVC pattern)
- Signals: `project_changed`, `frame_changed`, `layer_changed`

**Views:**
- `project_view.py`: Main project view with timeline, layers, preview
- Timeline scrubber, layer panel, keyframe editor

## Development Setup

### Prerequisites

```bash
# Python 3.10+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Key Dependencies

- **PyQt6**: GUI framework
- **NumPy**: Efficient pixel manipulation
- **OpenCV** (optional): Video export
- **PIL/Pillow** (optional): Image processing

### Project Structure

```
apps/upload-bridge/
├── domain/              # Data models
│   ├── project.py
│   ├── timeline.py
│   ├── layer_track.py
│   ├── keyframe.py
│   └── ...
├── core/                # Business logic
│   ├── project_manager.py
│   ├── compositor.py
│   ├── automation/
│   └── ...
├── ui/                  # User interface
│   ├── editor_controller.py
│   ├── project_view.py
│   └── ...
├── tests/               # Test suite
└── main.py             # Application entry point
```

## Adding New Features

### Adding a New Effect

1. **Define Effect Type** (`domain/effect.py`):
```python
class EffectType(Enum):
    NEW_EFFECT = "new_effect"
```

2. **Add Effect Config** (`domain/effect.py`):
```python
EffectConfig(
    effect_type=EffectType.NEW_EFFECT,
    name="New Effect",
    category="Animation",
    keyframe_properties=["speed", "intensity"]
)
```

3. **Implement Effect** (`core/automation/effects.py`):
```python
def apply_new_effect_frame(layer: LayerTrack, frame_idx: int, speed: float = 1.0, intensity: float = 1.0):
    """Apply new effect to a single frame."""
    # Implementation here
    pass
```

4. **Register in Engine** (`core/automation/engine.py`):
```python
elif effect_type == EffectType.NEW_EFFECT:
    apply_new_effect_frame(layer, frame_idx, **params)
```

### Adding a New Export Format

1. **Add Format Handler** (`core/export_manager.py`):
```python
def _export_custom_format(self, project: Project, output_path: str, **kwargs) -> bool:
    """Export to custom format."""
    # Implementation
    return True
```

2. **Register Format**:
```python
self._exporters['custom'] = self._export_custom_format
```

### Adding a New Blend Mode

1. **Add to Enum** (`domain/layer_track.py`):
```python
class BlendMode(Enum):
    NEW_BLEND = "new_blend"
```

2. **Implement Blending** (`core/compositor.py`):
```python
elif blend_mode == BlendMode.NEW_BLEND:
    # Blending logic
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
python test_all_phases.py

# Run specific phase
python -m pytest tests/test_phase_1.py
```

### Test Structure

- **Phase 1**: Core architecture (Project, Timeline, LayerTrack)
- **Phase 2**: Keyframes and interpolation
- **Phase 3**: Effects and automation
- **Phase 4**: Timeline retiming
- **Phase 5**: Layer compositing
- **Phase 6**: UI integration
- **Phase 7**: Export formats
- **Phase 8**: Versioning and cloud sync
- **Phase 9**: Bezier keyframes
- **Phase 10**: Performance optimization

## Code Style

- **PEP 8**: Follow Python style guide
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Document all public functions and classes
- **Logging**: Use `logging` module for debug/info/error messages

## Performance Considerations

### Optimization Tips

1. **NumPy Operations**: Use vectorized NumPy operations
2. **Frame Caching**: Cache rendered frames when possible
3. **Lazy Loading**: Load frames on-demand for large projects
4. **Memory Management**: Clear unused frame buffers

### Profiling

```python
from core.performance_profiler import benchmark_rendering

results = benchmark_rendering(project, frames=100)
print(f"Average FPS: {results['avg_fps']}")
```

## Building Executables

### Windows

```bash
python scripts/build_executable.py
```

Uses PyInstaller with `installer/windows/UploadBridge.spec`

### Linux/macOS

Similar process with platform-specific spec files.

## Debugging

### Logging

```python
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message", exc_info=True)
```

### Common Issues

1. **Import Errors**: Check `sys.path` and module structure
2. **NumPy Shape Errors**: Verify array dimensions (H×W×3)
3. **Keyframe Interpolation**: Check frame bounds and keyframe order
4. **Memory Issues**: Monitor memory usage with profiler

## Contributing

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/new-feature`
3. **Write Tests**: Add tests for new features
4. **Follow Style Guide**: Ensure code follows PEP 8
5. **Submit Pull Request**: Include description and test results

## API Reference

### EditorController

Main controller for editor operations:

```python
controller = EditorController()
controller.new_project(width=12, height=6, fps=30, duration=3.0)
controller.add_layer("Layer 1", 12, 6)
controller.set_current_frame(10)
controller.apply_effect(layer_id, EffectType.SCROLL)
```

### Project Management

```python
from core.project_manager import create_new_project, create_layer

project = create_new_project(width=16, height=8, fps=30, duration_seconds=2.0)
layer = create_layer(project, "My Layer", 16, 8)
```

### Rendering

```python
from core.compositor import render_frame

frame = render_frame(project, frame_index=0)
# Returns: NumPy array (H×W×3) uint8 RGB
```

### Keyframes

```python
layer.set_keyframe("opacity", frame=0, value=0.0)
layer.set_keyframe("opacity", frame=30, value=1.0)
opacity = layer.get_keyframe_value("opacity", frame=15)  # Interpolated
```

## License

See LICENSE file for details.

---

**Version**: 1.0.0  
**Last Updated**: 2024

