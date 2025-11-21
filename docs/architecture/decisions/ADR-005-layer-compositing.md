# ADR-005: Layer Compositing Strategy

**Status**: Accepted  
**Date**: 2025-01-XX  
**Deciders**: Architecture Team

## Context

The Design Tools Tab supports multiple layers per frame with visibility and opacity controls. We needed to decide how to composite (blend) multiple layers into a single frame display.

**Options considered**:
1. **Alpha blending (bottom-to-top)**: Standard alpha compositing from bottom layer to top
2. **Alpha blending (top-to-bottom)**: Composite from top layer to bottom (unusual)
3. **Additive blending**: Add pixel values together
4. **Multiply blending**: Multiply pixel values together

## Decision

We chose **bottom-to-top alpha compositing**:
- Layers are composited from bottom (index 0) to top (highest index)
- Each layer's opacity is applied during blending
- Hidden layers are skipped
- Final composite is stored in frame pixels via `sync_frame_from_layers()`

**Rationale**:
- **Standard approach**: Bottom-to-top alpha compositing is the industry standard (Photoshop, GIMP, etc.)
- **Intuitive**: Users expect bottom layers to be "behind" top layers
- **Opacity support**: Alpha blending naturally supports opacity values
- **Visibility support**: Hidden layers are simply skipped
- **Performance**: Single-pass compositing is efficient

## Consequences

### Positive
- **Intuitive behavior**: Matches user expectations from other graphics software
- **Opacity support**: Natural support for layer opacity (0.0-1.0)
- **Visibility support**: Easy to skip hidden layers
- **Standard algorithm**: Well-understood compositing algorithm
- **Performance**: Single-pass compositing is O(n*pixels) where n is layer count

### Negative
- **Performance with many layers**: Compositing 10+ layers can be slow for large patterns
- **Memory usage**: Must store all layer pixel arrays
- **Complexity**: Compositing logic adds complexity to LayerManager
- **Cache invalidation**: Composite cache must be invalidated when layers change

### Mitigations
- Composite caching: Cache composite result until layers change
- Lazy compositing: Only composite when needed (on display)
- Layer limit: Consider limiting maximum layers per frame (future enhancement)
- Performance monitoring: Track compositing performance for large patterns

## Implementation Details

```python
# LayerManager.get_composite_pixels()
def get_composite_pixels(self, frame_index: int) -> List[RGB]:
    layers = self.get_layers(frame_index)
    composite = [(0, 0, 0)] * (width * height)  # Start with black
    
    # Composite from bottom to top
    for layer in layers:
        if not layer.visible:
            continue  # Skip hidden layers
        
        opacity = layer.opacity
        for i, pixel in enumerate(layer.pixels):
            # Alpha blend: composite = composite * (1 - opacity) + pixel * opacity
            composite[i] = blend(composite[i], pixel, opacity)
    
    return composite
```

## References

- `domain/layers.py` - LayerManager.get_composite_pixels() implementation
- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - Layer Compositing section
- Alpha Compositing: https://en.wikipedia.org/wiki/Alpha_compositing

