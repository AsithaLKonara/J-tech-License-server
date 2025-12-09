# New Pattern Dialog - Complete Feature Documentation

## Overview

The New Pattern Dialog has been completely redesigned to match LED Matrix Studio's interface and includes comprehensive features for creating new LED matrix patterns.

## Dialog Structure

### Tabs

1. **Custom Tab** - Create patterns with full customization options
2. **From Preset Tab** - Quick creation from templates or size presets

## Custom Tab Features

### Matrix Options Section

#### RGB Dropdown
- **Options**: RGB, GRB, SINGLE
- **Default**: RGB
- **Purpose**: Selects LED color order/type

#### Dimensions
- **Width**: 1-256 pixels (spinbox)
- **Height**: 1-256 pixels (spinbox)
- **Format**: Width × Height (e.g., 12 × 6)
- **Validation**: Total LEDs cannot exceed 10,000

#### Shape Dropdown
- **Options**: Rectangular, Circle, Ring, Arc, Radial
- **Default**: Circle
- **Behavior**: 
  - Selecting circular shapes shows additional parameter fields
  - Rectangular hides circular parameters

#### Circular Layout Parameters (Conditional)
Visible when Circle/Ring/Arc/Radial is selected:

- **LED Count**: 1-512 LEDs
- **Outer Radius**: 1.0-1000.0 units (decimal)
- **Inner Radius**: 0.0-999.0 units (for Ring layouts only)
- **Start Angle**: 0.0-359.0 degrees (for Arc layouts only)
- **End Angle**: 1.0-360.0 degrees (for Arc layouts only)

**Field Visibility**:
- Inner Radius: Enabled only for Ring
- Start/End Angles: Enabled only for Arc
- All fields hidden when Rectangular is selected

#### Background
- **Color Swatch**: Click to open color picker (default: black)
- **Mode Radio Buttons**:
  - **Common**: Background color applied to first frame only
  - **All**: Background color applied to all frames
- **Visual Feedback**: Label shows which frames will receive background color

#### Border Dropdown
- **Options**: n/a, 1px, 2px, 3px
- **Default**: n/a
- **Purpose**: Sets visual pixel border width in canvas rendering

### Pixel Shape Section

Visual selector with three options:
1. **Square** - Square pixels with sharp corners
2. **Circle** (default) - Round pixels
3. **Rounded Square** - Square pixels with rounded corners

### Animation Section

#### Start with X animation frames
- **Range**: 1-1000 frames
- **Default**: 1
- **Purpose**: Creates multiple blank frames for animation

#### Clear all animation/matrix data
- **Checkbox**: When checked, uses background color for initial frames
- **Unchecked**: Uses black (0,0,0) as default

## From Preset Tab Features

### Matrix Size Presets

Quick selection of common matrix sizes:
- 8×8
- 16×16
- 32×8
- 32×32
- 64×32
- 128×64

**Behavior**: Selecting a preset updates dimensions (applied when creating pattern)

### Pattern Templates

Templates organized by category:
- **Animation**: Bouncing Ball, Fade, Pulse, Rotate
- **Effect**: Fire Effect, Rain Effect, Random Pixels
- **Text**: Scrolling Text
- **Game**: (Future templates)

**Template Selection**:
1. Select template from dropdown
2. Template description is displayed
3. Template-specific parameters appear in dynamic form
4. Adjust parameters as needed
5. Click Create to generate pattern

**Template Parameters**:
- Automatically generated based on template definition
- Supports: strings, integers, floats, RGB colors
- RGB colors entered as "R,G,B" (e.g., "255,0,0")

## Input Validation

### Real-time Validation

The dialog validates inputs in real-time and shows error messages:

- **Dimension Validation**:
  - Width/Height must be 1-256
  - Total LEDs (width × height) cannot exceed 10,000

- **Frame Validation**:
  - Frame count must be 1-1000

- **Circular Parameter Validation**:
  - LED count must be 1-512
  - Inner radius must be less than outer radius

### Error Display

- Validation errors shown in red below Animation section
- Create button disabled when errors are present
- Clear error messages guide users to fix issues

## Integration

### Pattern Creation Flow

1. **Custom Pattern**:
   - User configures all options
   - Pattern created with specified dimensions, frames, background
   - Circular layout mapping table generated if needed
   - Pixel shape and border applied to canvas

2. **Preset Template**:
   - User selects template
   - Adjusts template parameters
   - Pattern generated from template
   - Dialog options (pixel shape, etc.) still applied

### Background Mode Behavior

- **Common Mode**: 
  - First frame gets background color
  - Remaining frames are black (0,0,0)
  
- **All Mode**:
  - All frames get background color

### Border Rendering

- Border width applied to canvas pixel rendering
- 0 = no border (n/a)
- 1-3 = border width in pixels
- Border color uses canvas border color setting

## Error Handling

### Template Generation Errors

- Try/catch blocks around template generation
- User-friendly error dialogs with clear messages
- Graceful fallback to custom pattern creation

### Circular Layout Errors

- Mapping table generation errors caught
- Warning dialog explains the issue
- Falls back to rectangular layout
- No data loss

## Usage Examples

### Creating a Custom Circular Pattern

1. Open New Pattern dialog
2. Select "Circle" from Shape dropdown
3. Circular parameters appear
4. Set LED count: 60
5. Set Outer Radius: 10.0
6. Configure other options
7. Click Create

### Creating from Template

1. Open New Pattern dialog
2. Switch to "From Preset" tab
3. Select "Scrolling Text" template
4. Adjust parameters (text, speed, color)
5. Set dimensions if needed
6. Click Create

### Using Background Modes

1. Select background color (e.g., blue)
2. Choose "Common" mode
3. Set initial frames to 5
4. Result: Frame 1 = blue, Frames 2-5 = black
5. Choose "All" mode
6. Result: All 5 frames = blue

## Technical Details

### Dialog Methods

- `get_width()`, `get_height()` - Get dimensions
- `get_led_type()` - Get RGB/GRB/SINGLE
- `get_shape()` - Get selected shape
- `get_circular_led_count()` - Get LED count for circular layouts
- `get_circular_radius()` - Get outer radius
- `get_circular_inner_radius()` - Get inner radius (Ring only)
- `get_circular_start_angle()`, `get_circular_end_angle()` - Get arc angles
- `get_background_color()` - Get RGB tuple
- `get_background_mode()` - Get 'common' or 'all'
- `get_border()` - Get border setting
- `get_pixel_shape()` - Get 'square', 'circle', or 'rounded'
- `get_initial_frames()` - Get frame count
- `should_clear_data()` - Get checkbox state
- `get_selected_template()` - Get template if preset tab active
- `get_template_parameters()` - Get template parameter values
- `is_preset_tab_active()` - Check if preset tab is active

### Canvas Integration

- `set_pixel_shape()` - Applies pixel shape to canvas
- `set_border_width()` - Applies border width to canvas rendering

## Future Enhancements

- Additional template categories
- Custom template import
- Template preview
- Pattern preview before creation
- Save custom presets

