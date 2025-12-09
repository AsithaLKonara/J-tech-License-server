# Budurasmala Design Gap Analysis

## Executive Summary

This document analyzes the gap between the current circular view implementation and the actual requirements for designing **Budurasmala** (බුදු රැස් මාලා) - traditional Sri Lankan Buddhist LED halo displays used in Vesak festivals.

**Key Finding**: The current implementation provides a solid foundation for circular LED layouts, but lacks several critical features needed for authentic Budurasmala design workflows.

---

## What is Budurasmala?

Budurasmala is a **circular/ring LED display** that:
- Forms a **halo/aura** around Buddha statues or images
- Uses **addressable RGB LEDs** (typically WS2812B)
- Creates **dynamic, animated light patterns** (rays, gradients, twinkles, moving effects)
- Can be **full circles, partial arcs, or matrix-style** arrangements
- Often uses **custom PCBs** with curved/circular LED placement
- Requires **complex animation sequences** for festival displays

---

## Current Implementation Capabilities

### ✅ What We Have

1. **Circular Layout Support**
   - Circle, Ring, Arc, Radial layouts
   - Mapping table system (grid → circular LED order)
   - Split-view preview (rectangular grid + circular preview)

2. **Basic Parameters**
   - LED count configuration
   - Radius (outer/inner) settings
   - Start/end angles for arcs
   - Grid-based editing with circular interpretation

3. **Visual Feedback**
   - Real-time circular preview
   - Active cell highlighting
   - Geometry overlay (circle/ring bounds)

4. **Export System**
   - Reorders pixels by LED index for circular layouts
   - Supports various export formats

---

## Critical Gaps for Budurasmala Design

### 🔴 HIGH PRIORITY GAPS

#### 1. **Multi-Ring/Concentric Circle Support**

**Current State**: 
- Single ring/circle only
- Inner radius is visual only (LEDs always on outer radius)

**Budurasmala Need**:
- **Multiple concentric rings** (2-5 rings common)
- LEDs on **both inner and outer rings**
- **Radial "rays"** extending from center to outer edge
- **Layered halo effect** (inner glow + outer ring)

**Impact**: **CRITICAL** - Most Budurasmala use multi-ring designs

**Example**:
```
    O  ← Outer ring (60 LEDs)
   O O ← Middle ring (40 LEDs)  
  O   O ← Inner ring (20 LEDs)
   O O
    O
```

**Required Changes**:
- Extend `CircularMapper` to support multi-ring layouts
- Add ring count parameter
- Generate mapping for each ring separately
- Support radial ray patterns (LEDs along radius lines)

---

#### 2. **Radial Ray Pattern Support**

**Current State**:
- Radial layout exists but uses row/column interpretation
- No true radial ray patterns

**Budurasmala Need**:
- **Radial rays** extending from center outward
- LEDs arranged along **straight lines from center**
- **Rotating ray effects** (common animation)
- **Pulsing center** with expanding rays

**Impact**: **CRITICAL** - Core Budurasmala visual pattern

**Required Changes**:
- New layout type: "radial_rays"
- Parameters: ray count, LEDs per ray, ray spacing angle
- Mapping table for ray-based arrangement
- Preview visualization for rays

---

#### 3. **Curved PCB/Non-Uniform LED Spacing**

**Current State**:
- Assumes uniform LED spacing around circle
- Grid-based approximation

**Budurasmala Need**:
- **Custom PCB layouts** with non-uniform spacing
- **Curved board designs** (LEDs follow custom curve)
- **Variable LED density** (more LEDs in certain arcs)
- **Physical LED position import** (from PCB design files)

**Impact**: **HIGH** - Many Budurasmala use custom PCBs

**Required Changes**:
- Support for custom LED position arrays
- Import from PCB design tools (EasyEDA, KiCad)
- Manual LED position editor
- Non-uniform spacing calculations

---

#### 4. **Budurasmala-Specific Animation Patterns**

**Current State**:
- Generic animation templates (scroll, fade, pulse)
- No Budurasmala-specific patterns

**Budurasmala Need**:
- **"Ray rotation"** - Rays rotating around center
- **"Pulsing halo"** - Expanding/contracting rings
- **"Twinkling stars"** - Random LEDs twinkling
- **"Wave propagation"** - Wave moving around circle
- **"Color gradient rotation"** - Gradient pattern rotating
- **"Buddha light effect"** - Soft glow expanding from center

**Impact**: **HIGH** - Essential for authentic Budurasmala

**Required Changes**:
- New template category: "Budurasmala"
- Pre-built animation patterns
- Cultural pattern library
- Animation parameter presets

---

#### 5. **Matrix-Style Budurasmala Support**

**Current State**:
- Circular layouts only
- No matrix grid arrangements

**Budurasmala Need**:
- **Matrix-style Budurasmala** (grid of LEDs, not just ring)
- **Curved matrix** arrangements
- **Text/graphics** on matrix displays
- **Hybrid layouts** (ring + matrix center)

**Impact**: **MEDIUM** - Common in larger displays

**Required Changes**:
- Support matrix layouts with circular interpretation
- Curved matrix mapping
- Text rendering on circular matrix

---

### 🟡 MEDIUM PRIORITY GAPS

#### 6. **WLED/Falcon Player Integration**

**Current State**:
- Generic export formats
- No WLED-specific export

**Budurasmala Need**:
- **Direct WLED export** (JSON sequences)
- **Falcon Player compatibility**
- **xLights integration** workflow
- **Wireless control** pattern export

**Impact**: **MEDIUM** - Many builders use WLED

**Required Changes**:
- WLED JSON export format
- Falcon Player sequence export
- xLights import/export bridge

---

#### 7. **Physical LED Wiring Order**

**Current State**:
- LED index order only
- No physical wiring consideration

**Budurasmala Need**:
- **Serpentine wiring** support (LEDs wired back-and-forth)
- **Custom wiring paths** (LEDs not in logical order)
- **Wiring visualization** in preview
- **Wiring order editor**

**Impact**: **MEDIUM** - Affects export correctness

**Required Changes**:
- Wiring path configuration
- Serpentine pattern generator
- Wiring order mapping
- Export respects wiring order

---

#### 8. **Power Supply & LED Density Planning**

**Current State**:
- No power calculations
- No LED density warnings

**Budurasmala Need**:
- **Power consumption calculator** (LED count × current)
- **Voltage drop warnings** (for long strips)
- **Power supply recommendations**
- **LED density optimization** (spacing recommendations)

**Impact**: **MEDIUM** - Important for large displays

**Required Changes**:
- Power calculation tool
- Voltage drop estimation
- Power supply sizing recommendations

---

#### 9. **Cultural Pattern Library**

**Current State**:
- Generic patterns only
- No cultural context

**Budurasmala Need**:
- **Traditional Vesak patterns**
- **Buddhist symbolism** patterns (lotus, dharma wheel)
- **Festival color schemes** (gold, white, blue)
- **Cultural animation presets**

**Impact**: **MEDIUM** - Enhances authenticity

**Required Changes**:
- Cultural pattern library
- Symbol templates
- Festival color palettes
- Cultural animation presets

---

### 🟢 LOW PRIORITY GAPS

#### 10. **3D Preview/Visualization**

**Current State**:
- 2D circular preview only
- Flat representation

**Budurasmala Need**:
- **3D preview** showing halo around statue
- **Perspective view** of circular display
- **Statue placement** visualization
- **Lighting simulation**

**Impact**: **LOW** - Nice to have, not essential

---

#### 11. **PCB Design Integration**

**Current State**:
- No PCB design tools

**Budurasmala Need**:
- **PCB layout editor** (basic)
- **LED placement tool**
- **Export to PCB design tools**
- **Gerber file generation**

**Impact**: **LOW** - Advanced feature

---

## Gap Priority Matrix

| Gap | Priority | Impact | Effort | Recommendation |
|-----|----------|--------|--------|----------------|
| Multi-ring support | 🔴 HIGH | CRITICAL | High | **Implement first** |
| Radial ray patterns | 🔴 HIGH | CRITICAL | Medium | **Implement second** |
| Budurasmala animations | 🔴 HIGH | HIGH | Medium | **Implement third** |
| Curved PCB support | 🟡 MEDIUM | HIGH | High | Phase 2 |
| Matrix-style layouts | 🟡 MEDIUM | MEDIUM | Medium | Phase 2 |
| WLED integration | 🟡 MEDIUM | MEDIUM | Low | Phase 2 |
| Wiring order | 🟡 MEDIUM | MEDIUM | Medium | Phase 3 |
| Power calculations | 🟡 MEDIUM | MEDIUM | Low | Phase 3 |
| Cultural patterns | 🟡 MEDIUM | MEDIUM | Low | Phase 3 |
| 3D preview | 🟢 LOW | LOW | High | Future |
| PCB design | 🟢 LOW | LOW | Very High | Future |

---

## Implementation Roadmap

### Phase 1: Core Budurasmala Support (HIGH PRIORITY)

**Goal**: Enable basic multi-ring Budurasmala design

1. **Multi-Ring Layout System**
   - Extend `CircularMapper` for multiple rings
   - Ring count parameter (1-5 rings)
   - LEDs per ring configuration
   - Ring spacing/radius calculation
   - Multi-ring preview rendering

2. **Radial Ray Pattern**
   - New layout type: "radial_rays"
   - Ray count parameter
   - LEDs per ray
   - Ray angle spacing
   - Ray-based mapping table

3. **Budurasmala Animation Templates**
   - Ray rotation animation
   - Pulsing halo effect
   - Twinkling stars
   - Wave propagation
   - Color gradient rotation

**Timeline**: 2-3 weeks
**Dependencies**: None (builds on existing circular system)

---

### Phase 2: Advanced Features (MEDIUM PRIORITY)

**Goal**: Support custom PCBs and matrix layouts

1. **Custom LED Position Support**
   - Manual LED position editor
   - Import from CSV/JSON
   - Non-uniform spacing
   - Curved board support

2. **Matrix-Style Budurasmala**
   - Curved matrix layouts
   - Text rendering on circular matrix
   - Hybrid ring+matrix layouts

3. **WLED/Falcon Integration**
   - WLED JSON export
   - Falcon Player sequences
   - xLights workflow bridge

**Timeline**: 3-4 weeks
**Dependencies**: Phase 1 complete

---

### Phase 3: Polish & Optimization (LOW PRIORITY)

**Goal**: Enhance workflow and add cultural context

1. **Wiring Order Management**
   - Serpentine pattern generator
   - Custom wiring paths
   - Wiring visualization

2. **Power & Density Tools**
   - Power consumption calculator
   - Voltage drop warnings
   - Power supply recommendations

3. **Cultural Pattern Library**
   - Traditional Vesak patterns
   - Buddhist symbolism
   - Festival color palettes

**Timeline**: 2-3 weeks
**Dependencies**: Phase 2 complete

---

## Technical Architecture Changes Needed

### 1. Extend PatternMetadata

```python
# New fields for multi-ring support
multi_ring_count: Optional[int] = None  # Number of rings
ring_led_counts: List[int] = []  # LEDs per ring
ring_radii: List[float] = []  # Radius for each ring
ring_spacing: Optional[float] = None  # Spacing between rings

# New fields for radial rays
ray_count: Optional[int] = None  # Number of rays
leds_per_ray: Optional[int] = None  # LEDs along each ray
ray_spacing_angle: Optional[float] = None  # Angle between rays

# Custom LED positions
custom_led_positions: Optional[List[Tuple[float, float]]] = None  # (x, y) in mm or units
led_position_units: str = "grid"  # "grid", "mm", "inches"
```

### 2. Extend CircularMapper

```python
@staticmethod
def generate_multi_ring_mapping(metadata: PatternMetadata) -> List[Tuple[int, int]]:
    """Generate mapping for multiple concentric rings."""
    # Implementation for multi-ring layouts

@staticmethod
def generate_radial_ray_mapping(metadata: PatternMetadata) -> List[Tuple[int, int]]:
    """Generate mapping for radial ray pattern."""
    # Implementation for ray-based layouts

@staticmethod
def generate_custom_position_mapping(metadata: PatternMetadata) -> List[Tuple[int, int]]:
    """Generate mapping from custom LED positions."""
    # Implementation for custom PCB layouts
```

### 3. New Animation Templates

```python
# In core/pattern_templates.py
class BudurasmalaTemplates:
    """Budurasmala-specific animation patterns."""
    
    @staticmethod
    def ray_rotation(width, height, led_count, frames, speed, color):
        """Rotating rays around center."""
        pass
    
    @staticmethod
    def pulsing_halo(width, height, led_count, frames, rings, color):
        """Expanding/contracting rings."""
        pass
    
    @staticmethod
    def twinkling_stars(width, height, led_count, frames, density, color):
        """Random twinkling LEDs."""
        pass
```

### 4. Enhanced Preview Widget

```python
# In ui/widgets/circular_preview_canvas.py
def _paint_multi_ring_preview(painter, rect):
    """Render multiple concentric rings."""
    pass

def _paint_radial_ray_preview(painter, rect):
    """Render radial ray pattern."""
    pass
```

---

## User Workflow Comparison

### Current Workflow (Generic Circular)

1. Create pattern → Select "Circle" shape
2. Set LED count, radius
3. Draw on rectangular grid
4. Preview shows circular arrangement
5. Export reorders by LED index

**Limitation**: Single ring only, no multi-ring or ray patterns

---

### Ideal Budurasmala Workflow

1. **Create Budurasmala Pattern**
   - Select "Multi-Ring" or "Radial Rays" layout
   - Configure rings: 3 rings, 60/40/20 LEDs
   - Set ring radii and spacing

2. **Design Pattern**
   - Draw on grid (interpreted as multi-ring)
   - Use Budurasmala animation templates
   - Apply ray rotation or pulsing halo

3. **Preview & Test**
   - See multi-ring preview
   - Test animations
   - Verify LED order

4. **Export for Hardware**
   - Export to WLED format
   - Or Falcon Player sequence
   - Or custom firmware format

**Advantage**: Authentic Budurasmala design workflow

---

## Recommendations

### Immediate Actions (Week 1-2)

1. **Research existing Budurasmala projects**
   - Analyze 5-10 documented builds
   - Extract common patterns and requirements
   - Document typical LED counts and arrangements

2. **Design multi-ring system**
   - Architecture design
   - API specification
   - Preview rendering approach

3. **Prototype radial ray pattern**
   - Basic ray mapping
   - Simple preview
   - Test with sample data

### Short-term (Month 1)

1. **Implement multi-ring support**
   - Core mapping system
   - Preview rendering
   - Dialog UI updates

2. **Add Budurasmala animation templates**
   - Ray rotation
   - Pulsing halo
   - Twinkling stars

3. **Test with real Budurasmala designs**
   - Create sample patterns
   - Validate export formats
   - Get user feedback

### Long-term (Months 2-3)

1. **Advanced features** (Phase 2)
2. **Polish & optimization** (Phase 3)
3. **Documentation & tutorials**

---

## Success Metrics

### Technical Metrics

- ✅ Support 2-5 ring Budurasmala designs
- ✅ Radial ray patterns working
- ✅ 5+ Budurasmala animation templates
- ✅ WLED export functional
- ✅ Multi-ring preview accurate

### User Experience Metrics

- ✅ Can design authentic Budurasmala in < 30 minutes
- ✅ Preview matches physical display
- ✅ Export works with common hardware (ESP32, WLED)
- ✅ Cultural patterns available

### Cultural Authenticity

- ✅ Patterns match traditional Vesak displays
- ✅ Animations feel authentic
- ✅ Color schemes appropriate
- ✅ Community feedback positive

---

## Conclusion

The current circular view implementation provides a **solid foundation** but needs **significant enhancements** to fully support Budurasmala design:

**Critical Gaps**:
1. Multi-ring support (CRITICAL)
2. Radial ray patterns (CRITICAL)
3. Budurasmala-specific animations (HIGH)

**Estimated Effort**: 
- Phase 1 (Core): 2-3 weeks
- Phase 2 (Advanced): 3-4 weeks
- Phase 3 (Polish): 2-3 weeks
- **Total**: ~2-3 months for complete Budurasmala support

**Recommendation**: Start with Phase 1 to enable basic Budurasmala design, then iterate based on user feedback and real-world usage.

---

## References

- [Hackster Budurasmala Project](https://www.hackster.io/yasith-lokuge/budurasmala-63c89f)
- [LED Buduras Mala Pattern Generator](https://stark9000.blogspot.com/2019/05/led-buduras-mala-led-pattern-generator.html)
- [Atapirikara Budhu Rasmala](https://atapirikara.lk/home/electrical-electronics/lighting/buy-budhu-rasmala-online-sri-lanka/)
- Current implementation: `core/mapping/circular_mapper.py`
- Current preview: `ui/widgets/circular_preview_canvas.py`

