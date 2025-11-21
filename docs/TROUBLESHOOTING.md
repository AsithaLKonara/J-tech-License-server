# Troubleshooting Guide

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Purpose**: Common issues, solutions, and diagnostic steps for the Design Tools Tab

---

## Overview

This guide documents common issues, their symptoms, causes, and solutions. It covers performance issues, memory problems, rendering issues, export/import failures, and more.

---

## Performance Issues

### Slow Rendering

**Symptoms**:
- Canvas updates are slow or laggy
- UI becomes unresponsive during painting
- Frame switching is slow

**Possible Causes**:
1. Large pattern (many pixels)
2. Many layers (10+ layers per frame)
3. Inefficient compositing
4. Cache not working properly

**Solutions**:
1. **Reduce pattern size**: Use smaller dimensions (e.g., 16x16 instead of 64x64)
2. **Reduce layer count**: Consolidate or remove unused layers
3. **Hide unused layers**: Hide layers that aren't being edited
4. **Clear caches**: Clear composite and thumbnail caches
5. **Check performance**: Use profiling tools to identify bottlenecks

**Diagnostic Steps**:
```python
# Check pattern size
pattern = pattern_state.pattern()
print(f"Pattern: {pattern.width()}x{pattern.height()}, {len(pattern.frames())} frames")

# Check layer count
for i in range(len(pattern.frames())):
    layers = layer_manager.get_layers(i)
    print(f"Frame {i}: {len(layers)} layers")
```

---

### High Memory Usage

**Symptoms**:
- Application uses excessive memory (>100 MB for typical patterns)
- System becomes slow
- Out of memory errors

**Possible Causes**:
1. Very large pattern (64x64+ with many frames)
2. Many layers per frame (10+ layers)
3. Memory leaks (caches not cleared)
4. History stack too large

**Solutions**:
1. **Reduce pattern size**: Use smaller dimensions
2. **Reduce layer count**: Consolidate layers
3. **Clear caches**: Clear composite, thumbnail, and preview caches
4. **Limit history**: Reduce undo/redo history depth
5. **Unload unused frames**: Unload frames that are far from current frame

**Diagnostic Steps**:
```python
import sys
print(f"Memory usage: {sys.getsizeof(pattern_state.pattern())} bytes")
# Check cache sizes
print(f"Composite cache: {len(layer_manager._composite_cache)} entries")
```

---

### Cache Problems

**Symptoms**:
- Canvas shows stale data
- Changes not reflected immediately
- Performance degrades over time

**Possible Causes**:
1. Cache not invalidated on changes
2. Cache size too large
3. Cache corruption

**Solutions**:
1. **Clear caches**: Manually clear all caches
2. **Check cache invalidation**: Verify caches are invalidated on changes
3. **Reduce cache size**: Limit cache size to prevent memory issues

**Diagnostic Steps**:
```python
# Check cache state
print(f"Composite cache keys: {list(layer_manager._composite_cache.keys())}")
# Clear cache
layer_manager._composite_cache.clear()
```

---

## Memory Issues

### Out of Memory Errors

**Symptoms**:
- Application crashes with "Out of memory" error
- System becomes unresponsive
- Cannot load large patterns

**Possible Causes**:
1. Pattern too large for available memory
2. Memory leak (memory not released)
3. Too many patterns loaded simultaneously

**Solutions**:
1. **Reduce pattern size**: Use smaller dimensions
2. **Close unused patterns**: Close patterns that aren't being edited
3. **Restart application**: Restart to clear memory leaks
4. **Increase system memory**: Add more RAM if possible

**Diagnostic Steps**:
```python
# Check memory usage
import tracemalloc
tracemalloc.start()
# ... perform operations ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")
```

---

### Memory Leaks

**Symptoms**:
- Memory usage increases over time
- Application becomes slower after extended use
- System becomes unresponsive

**Possible Causes**:
1. Caches not cleared
2. Signal connections not disconnected
3. Objects not garbage collected

**Solutions**:
1. **Clear caches periodically**: Clear caches when not needed
2. **Disconnect signals**: Disconnect signals when objects are destroyed
3. **Use weak references**: Use weak references for signal connections
4. **Restart application**: Restart periodically to clear leaks

**Diagnostic Steps**:
```python
# Use memory profiler
from memory_profiler import profile

@profile
def test_function():
    # ... code to test ...
    pass
```

---

## Rendering Problems

### Canvas Not Updating

**Symptoms**:
- Canvas shows old frame data
- Changes not visible on canvas
- Canvas is blank

**Possible Causes**:
1. Canvas not refreshed after changes
2. Frame not loaded into canvas
3. Composite cache stale
4. Signal not connected

**Solutions**:
1. **Manually refresh canvas**: Call `canvas.update()` or `canvas.repaint()`
2. **Check frame loading**: Verify frame is loaded into canvas
3. **Clear composite cache**: Clear cache to force recomputation
4. **Check signal connections**: Verify signals are connected

**Diagnostic Steps**:
```python
# Check canvas state
print(f"Canvas frame: {canvas_controller.current_frame_index}")
# Force refresh
canvas_controller.render_frame(frame_index)
canvas.update()
```

---

### Incorrect Colors

**Symptoms**:
- Colors appear wrong on canvas
- Colors don't match selected color
- Colors change unexpectedly

**Possible Causes**:
1. Color order mismatch (RGB vs BGR)
2. Color format incorrect
3. Layer opacity affecting colors
4. Composite blending issues

**Solutions**:
1. **Check color order**: Verify color order matches pattern metadata
2. **Check color format**: Ensure colors are RGB tuples (r, g, b)
3. **Check layer opacity**: Verify layer opacity settings
4. **Check composite**: Verify composite blending is correct

**Diagnostic Steps**:
```python
# Check pixel color
pixel = layer.pixels[pixel_index]
print(f"Pixel color: {pixel}")
# Check composite
composite = layer_manager.get_composite_pixels(frame_index)
print(f"Composite color: {composite[pixel_index]}")
```

---

### Layer Compositing Issues

**Symptoms**:
- Layers not blending correctly
- Hidden layers still visible
- Opacity not working

**Possible Causes**:
1. Compositing algorithm incorrect
2. Layer visibility not checked
3. Opacity not applied
4. Layer order incorrect

**Solutions**:
1. **Check layer visibility**: Verify `layer.visible` is set correctly
2. **Check layer opacity**: Verify `layer.opacity` is in range 0.0-1.0
3. **Check layer order**: Verify layers are composited bottom-to-top
4. **Clear composite cache**: Clear cache to force recomputation

**Diagnostic Steps**:
```python
# Check layer properties
for layer in layers:
    print(f"Layer: {layer.name}, visible: {layer.visible}, opacity: {layer.opacity}")
# Check composite
composite = layer_manager.get_composite_pixels(frame_index)
```

---

## Export Failures

### File Format Errors

**Symptoms**:
- Export fails with format error
- Exported file cannot be opened
- Exported file is corrupted

**Possible Causes**:
1. Invalid pattern data
2. Format-specific validation failure
3. File write error
4. Template rendering error

**Solutions**:
1. **Validate pattern**: Ensure pattern is valid before export
2. **Check format requirements**: Verify pattern meets format requirements
3. **Check file permissions**: Ensure write permissions for output file
4. **Check template**: Verify template is valid for code export

**Diagnostic Steps**:
```python
# Validate pattern
pattern = pattern_state.pattern()
assert pattern is not None
assert len(pattern.frames()) > 0
# Check export options
print(f"Export format: {export_format}")
print(f"Pattern dimensions: {pattern.width()}x{pattern.height()}")
```

---

### Permission Errors

**Symptoms**:
- Export fails with "Permission denied" error
- Cannot write to output directory
- File is locked

**Possible Causes**:
1. Insufficient file permissions
2. File is open in another application
3. Directory doesn't exist
4. Disk is full

**Solutions**:
1. **Check permissions**: Ensure write permissions for output directory
2. **Close other applications**: Close applications that may have file open
3. **Create directory**: Create output directory if it doesn't exist
4. **Check disk space**: Ensure sufficient disk space

**Diagnostic Steps**:
```python
# Check file permissions
from pathlib import Path
output_path = Path("output.leds")
print(f"Path exists: {output_path.parent.exists()}")
print(f"Path writable: {output_path.parent.is_dir() and os.access(output_path.parent, os.W_OK)}")
```

---

### Data Corruption

**Symptoms**:
- Exported file loads but data is incorrect
- Pixels are wrong
- Frames are missing

**Possible Causes**:
1. Serialization error
2. Data format mismatch
3. Endianness issues
4. Encoding issues

**Solutions**:
1. **Verify serialization**: Check serialization/deserialization logic
2. **Check data format**: Verify data format matches specification
3. **Test round-trip**: Export and import to verify data integrity
4. **Check encoding**: Ensure correct encoding for text data

**Diagnostic Steps**:
```python
# Test round-trip
pattern1 = pattern_state.pattern()
export_pattern(pattern1, "test.leds")
pattern2 = import_pattern("test.leds")
assert pattern1.width() == pattern2.width()
assert pattern1.height() == pattern2.height()
```

---

## Import Failures

### Parser Errors

**Symptoms**:
- Import fails with parser error
- "Invalid file format" error
- File cannot be parsed

**Possible Causes**:
1. File format not supported
2. File is corrupted
3. File version incompatible
4. Parser bug

**Solutions**:
1. **Check file format**: Verify file format is supported
2. **Validate file**: Check if file is corrupted
3. **Check file version**: Verify file version is compatible
4. **Report bug**: Report parser bug if file is valid

**Diagnostic Steps**:
```python
# Check file format
from core.io.file_format_detector import detect_format
format = detect_format(file_path)
print(f"Detected format: {format}")
# Try parsing
try:
    pattern = parse_file(file_path)
except Exception as e:
    print(f"Parse error: {e}")
```

---

### Format Detection Failures

**Symptoms**:
- Format not detected correctly
- Wrong parser used
- Import fails with wrong error

**Possible Causes**:
1. File extension incorrect
2. File signature missing
3. Format detector bug

**Solutions**:
1. **Check file extension**: Verify file extension matches format
2. **Check file signature**: Verify file has correct signature
3. **Manual format selection**: Allow manual format selection

**Diagnostic Steps**:
```python
# Check file signature
with open(file_path, "rb") as f:
    signature = f.read(4)
    print(f"File signature: {signature.hex()}")
```

---

### Dimension Mismatches

**Symptoms**:
- Imported pattern has wrong dimensions
- Pixels don't align correctly
- Pattern appears distorted

**Possible Causes**:
1. Dimension detection incorrect
2. File doesn't specify dimensions
3. Dimension inference wrong

**Solutions**:
1. **Specify dimensions**: Allow user to specify dimensions
2. **Check file metadata**: Verify file contains dimension information
3. **Validate dimensions**: Validate detected dimensions

**Diagnostic Steps**:
```python
# Check dimensions
pattern = import_pattern(file_path)
print(f"Imported dimensions: {pattern.width()}x{pattern.height()}")
# Compare with expected
expected_width = 16
expected_height = 16
if pattern.width() != expected_width or pattern.height() != expected_height:
    print("Dimension mismatch!")
```

---

## General Diagnostic Steps

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Now all debug messages will be printed
```

### Check Manager State

```python
# Check PatternState
print(f"Pattern: {pattern_state.pattern() is not None}")
print(f"Dimensions: {pattern_state.width()}x{pattern_state.height()}")

# Check FrameManager
print(f"Current frame: {frame_manager.current_index()}")
print(f"Frame count: {len(frame_manager.frames())}")

# Check LayerManager
for i in range(len(pattern.frames())):
    layers = layer_manager.get_layers(i)
    print(f"Frame {i}: {len(layers)} layers")
```

### Check Signal Connections

```python
# Check if signals are connected
print(f"Frame index signal connected: {frame_manager.receivers(frame_manager.frame_index_changed)}")
print(f"Layers changed signal connected: {layer_manager.receivers(layer_manager.layers_changed)}")
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... perform operations ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Print top 10 functions
```

---

## Getting Help

If you cannot resolve an issue:

1. **Check this guide**: Review relevant troubleshooting section
2. **Check logs**: Review application logs for error messages
3. **Reproduce issue**: Create minimal test case that reproduces issue
4. **Report bug**: Report bug with:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Error messages
   - System information

---

## References

- PERFORMANCE_CONSIDERATIONS.md - Performance documentation
- API_REFERENCE.md - API documentation
- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - Architecture overview
- TESTING_GUIDE.md - Testing documentation

