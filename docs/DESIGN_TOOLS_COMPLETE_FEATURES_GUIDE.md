# Design Tools Tab - Complete Features & Options Guide

**Version**: 1.0  
**Last Updated**: 2025-11-27  
**Last Verified**: 2025-11-27  
**Verification Status**: ✅ All 157 features verified (100% pass rate)  
**Verification Report**: See `DESIGN_TOOLS_VERIFICATION_REPORT.md`  
**Purpose**: Comprehensive documentation of all features, options, and workflows in the Design Tools Tab

---

## Table of Contents

1. [Overview](#overview)
2. [Main Interface Layout](#main-interface-layout)
3. [Header Toolbar](#header-toolbar)
4. [Canvas Panel](#canvas-panel)
5. [Toolbox Column (8 Tabs)](#toolbox-column-8-tabs)
   - [Brushes Tab](#1-brushes-tab)
   - [LED Colors Tab](#2-led-colors-tab)
   - [Pixel Mapping Tab](#3-pixel-mapping-tab)
   - [Scratchpads Tab](#4-scratchpads-tab)
   - [Layers Tab](#5-layers-tab)
   - [Effects Tab](#6-effects-tab)
   - [Automation Tab](#7-automation-tab)
   - [Export Tab](#8-export-tab)
6. [Timeline Dock](#timeline-dock)
7. [Complete Feature Flows](#complete-feature-flows)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Advanced Workflows](#advanced-workflows)

---

## Overview

The Design Tools Tab is a comprehensive LED matrix pattern authoring environment that provides:

- **Interactive Canvas**: Paint, draw, and edit LED matrix frames pixel-by-pixel
- **Frame Management**: Create, duplicate, delete, and reorder animation frames
- **Layer System**: Multi-layer support with blend modes and visibility controls
- **Drawing Tools**: 8 drawing tools (Pixel, Rectangle, Circle, Line, Fill, Gradient, Random, Eyedropper)
- **Color Management**: Advanced LED color controls, brightness, gamma, temperature
- **Automation**: Queue transformations (scroll, rotate, mirror, flip, etc.)
- **Effects Library**: Apply visual effects to frames
- **LMS Integration**: Build MCU-ready LED Matrix Studio instructions
- **Export/Import**: Save patterns, export code templates, import images/GIFs

---

## Main Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Header Toolbar (New, Templates, AI Generate, Save, Settings)  │
├──────────────┬──────────────────────────────┬───────────────────┤
│              │                              │                   │
│  Toolbox     │      Canvas Panel            │   Live Preview   │
│  Column      │   (Matrix Design Canvas)     │   (Simulator)    │
│  (8 Tabs)    │                              │                   │
│              │                              │                   │
├──────────────┴──────────────────────────────┴───────────────────┤
│                    Timeline Dock                                │
│  (Frame thumbnails, playhead, playback controls, duration)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Header Toolbar

Located at the top of the Design Tools Tab, provides quick access to common operations.

### Features:

#### 1. **New Pattern Button**
- **Function**: Creates a new blank pattern
- **Flow**:
  1. Click "New" button
  2. Dialog appears asking for dimensions (width × height)
  3. Optional: Select LED type (RGB, RGBW, single-color)
  4. Click "Create"
  5. New blank pattern loads with one empty frame
- **Options**:
  - Width: 1-256 pixels
  - Height: 1-256 pixels
  - LED Type: RGB, RGBW, Single-color
  - Single-color mode toggle

#### 1a. **Open Pattern Button**
- **Function**: Opens an existing pattern file
- **Flow**:
  1. Click "Open" button
  2. File dialog opens
  3. Select pattern file (.leds, .dat, .hex, .bin, .json, etc.)
  4. File loads into editor
  5. Pattern available in all tabs
- **Supported Formats**:
  - LEDS (LED Matrix Studio)
  - DAT (Data format)
  - HEX (Intel HEX)
  - BIN (Binary)
  - JSON (Pattern format)
  - Project files

#### 2. **Templates Button**
- **Function**: Opens template library to create patterns from pre-made templates
- **Flow**:
  1. Click "Templates" button
  2. Template dialog opens showing available templates
  3. Select a template category (animations, text, effects, etc.)
  4. Choose specific template
  5. Adjust parameters if available
  6. Click "Generate"
  7. Pattern loads into editor
- **Template Categories**:
  - Text Animations
  - Geometric Patterns
  - Effects
  - Custom Templates

#### 3. **AI Generate Button**
- **Function**: Generate patterns using AI
- **Flow**:
  1. Click "AI Generate" button
  2. AI dialog opens
  3. Enter prompt or select generation mode
  4. Configure parameters (style, complexity, etc.)
  5. Click "Generate"
  6. AI generates pattern
  7. Pattern loads into editor
- **Options**:
  - Text prompt
  - Style selection
  - Complexity level
  - Generation seed

#### 4. **Create Animation Button**
- **Function**: Create animation from scratch with wizard
- **Flow**:
  1. Click "Create Animation"
  2. Animation wizard opens
  3. Select animation type (scroll, fade, etc.)
  4. Configure parameters
  5. Click "Generate"
  6. Animation loads as multiple frames

#### 5. **Version History Button**
- **Function**: View and restore previous versions of pattern
- **Flow**:
  1. Click "Version History"
  2. Dialog shows version timeline
  3. Select a version
  4. Preview changes
  5. Click "Restore" to load that version
- **Features**:
  - Auto-versioning (saves versions automatically)
  - Manual version creation
  - Version comparison
  - Metadata preservation

#### 6. **Save Button**
- **Function**: Opens export dialog to save pattern
- **Flow**:
  1. Click "Save" button
  2. Export dialog opens
  3. Select export format (.leds, .dat, .hex, .bin, etc.)
  4. Choose destination
  5. Configure export options
  6. Click "Export"
- **Formats**:
  - LEDS (LED Matrix Studio format)
  - DAT (Data format)
  - HEX (Intel HEX)
  - BIN (Binary)
  - JSON (Pattern format)

#### 7. **Settings Button**
- **Function**: Opens design settings (future feature)
- **Status**: Placeholder for future preferences

#### 8. **Quick Size Buttons**
- **Function**: Quickly set matrix dimensions
- **Flow**:
  1. Click one of the preset size buttons (8×8, 16×16, 32×32, 64×32)
  2. Matrix dimensions update immediately
  3. Canvas resizes
  4. Or click "Custom..." to open matrix configuration dialog
- **Options**:
  - 8×8 pixels
  - 16×16 pixels
  - 32×32 pixels
  - 64×32 pixels
  - Custom... (opens dialog)

#### 9. **Quick Actions Toolbar**
- **Function**: Quick access to common frame operations
- **Buttons**:
  - **Clear**: Clear current frame (Delete key)
  - **Invert**: Invert colors (Ctrl+N)
  - **Flip H**: Flip horizontal (Ctrl+H)
  - **Flip V**: Flip vertical (Ctrl+V)
  - **Rotate 90°**: Rotate 90 degrees clockwise
- **Flow**:
  1. Select frame
  2. Click quick action button
  3. Operation applies immediately
  4. History entry created (undoable)

---

## Canvas Panel

The central workspace where you paint and edit LED matrix frames.

### Components:

#### 1. **Matrix Design Canvas**
- **Purpose**: Interactive pixel grid for drawing
- **Features**:
  - Pixel-by-pixel painting
  - Drag painting (hold mouse button)
  - Hover feedback (shows pixel coordinates)
  - Zoom and pan support
  - Onion skinning (show previous/next frames)
  - Grid overlay
  - Pixel shape options (square, round, rounded)

#### 2. **Canvas Controls Group**
Located above the canvas.

**View Controls**:
- **Canvas Zoom Slider**: Adjust canvas zoom (25% - 300%)
  - Range: 25% to 300%
  - Default: 100%
  - Updates in real-time
- **Zoom Label**: Shows current zoom percentage (e.g., "100%")
- **Reset Zoom Button**: Return to 100% (target icon)
- **Flow**:
  1. Drag zoom slider
  2. Canvas scales immediately
  3. Zoom percentage updates
  4. Click reset button to return to 100%

**Onion Skinning Controls**:
- **Enable Onion Skin**: Toggle onion skinning on/off
- **Previous Frames**: Number of previous frames to show (0-5, default: 1)
- **Previous Opacity**: Opacity of previous frames (0-100%, default: 50%)
- **Next Frames**: Number of next frames to show (0-5, default: 1)
- **Next Opacity**: Opacity of next frames (0-100%, default: 30%)
- **Flow**:
  1. Enable onion skinning checkbox
  2. Set previous/next frame counts
  3. Adjust opacity sliders
  4. Previous/next frames appear on canvas with transparency

**Geometry Overlay**:
- **Function**: Show matrix geometry visualization
- **Options**:
  - Matrix: Standard grid
  - Circle: Circular arrangement
  - Ring: Ring arrangement
  - Radial: Radial arrangement
- **Flow**:
  1. Select geometry type from dropdown
  2. Canvas shows overlay
  3. Helps visualize non-rectangular layouts

**Pixel Shape**:
- **Function**: Change visual style of pixels
- **Options**:
  - Square: Square pixels
  - Round: Circular pixels
  - Rounded: Rounded square pixels
- **Flow**:
  1. Select pixel shape from dropdown
  2. Canvas updates pixel appearance
  3. Does not affect actual pixel data

**Detached Preview Button**:
- **Function**: Open pattern in separate preview window
- **Flow**:
  1. Click "Detached Preview" button
  2. New window opens showing pattern
  3. Preview plays animation
  4. Window can be moved/resized independently
  5. Close window to return to main view

#### 3. **Canvas HUD (Heads-Up Display)**
Located above the canvas:
- **Undo Button**: Undo last action (Ctrl+Z)
- **Redo Button**: Redo last undone action (Ctrl+Y)
- **Tooltips**: Show keyboard shortcuts

#### 4. **Warning Banners**
- **Brush Broadcast Banner**: Appears when "Apply brush strokes to all frames" is enabled
  - Shows warning about destructive operation
  - Can dismiss or disable broadcast mode
- **Hidden Layer Banner**: Appears when active layer is hidden
  - Warns that drawing may not be visible
  - Can show layer or make it visible

#### 5. **Canvas Status Bar**
Shows:
- Current pixel coordinates (X, Y)
- Current color (RGB values)
- Frame number and total frames
- Layer information
- Drawing tool in use
- Helpful hints ("Click to paint. Right-click to erase.")

---

## Toolbox Column (8 Tabs)

The left sidebar contains 8 tabs with different tool categories.

---

### 1. Brushes Tab

Contains drawing tools, appearance settings, palette, and text animation.

#### **Appearance Group**

**Autosave Settings**:
- **Enable Autosave**: Toggle automatic saving
- **Autosave Interval**: Minutes between saves (1-60 minutes)
- **Flow**:
  1. Enable autosave checkbox
  2. Set interval (default: 5 minutes)
  3. Pattern auto-saves at interval
  4. Notification appears when saved

#### **Drawing Tools Group**

**8 Drawing Tools**:

1. **Pixel Tool** (Default)
   - **Function**: Paint individual pixels
   - **Flow**:
     1. Select Pixel tool
     2. Click on canvas to paint pixel
     3. Drag to paint multiple pixels
     4. Right-click to erase (set to black)
   - **Options**:
     - Brush size: 1-8 pixels (default: 1)
     - Shape: Square, Round, Rounded

2. **Rectangle Tool**
   - **Function**: Draw rectangles
   - **Flow**:
     1. Select Rectangle tool
     2. Click and drag to define rectangle
     3. Release to draw
   - **Options**:
     - Filled: Draw filled rectangle
     - Outlined: Draw rectangle outline only
     - Border width: 1-5 pixels

3. **Circle Tool**
   - **Function**: Draw circles/ellipses
   - **Flow**:
     1. Select Circle tool
     2. Click and drag to define circle
     3. Release to draw
   - **Options**:
     - Filled: Draw filled circle
     - Outlined: Draw circle outline only
     - Perfect circle: Hold Shift for perfect circle

4. **Line Tool**
   - **Function**: Draw straight lines
   - **Flow**:
     1. Select Line tool
     2. Click start point
     3. Drag to end point
     4. Release to draw line
   - **Options**:
     - Line width: 1-5 pixels
     - Anti-aliasing: Smooth line edges

5. **Fill Tool (Bucket Fill)**
   - **Function**: Fill connected area with color
   - **Flow**:
     1. Select Fill tool
     2. Click on area to fill
     3. Connected pixels of same color fill
   - **Options**:
     - Tolerance: 0-255 (color matching tolerance)
     - Fill mode: Same color, Similar colors

6. **Gradient Tool**
   - **Function**: Apply gradient between two colors
   - **Flow**:
     1. Select Gradient tool
     2. Set start and end colors
     3. Click start point
     4. Drag to end point
     5. Release to apply gradient
   - **Options**:
     - Gradient type: Linear, Radial, Horizontal, Vertical
     - Steps: Number of gradient steps (2-256)
     - Start color: RGB picker
     - End color: RGB picker

7. **Random Spray Tool**
   - **Function**: Spray random pixels
   - **Flow**:
     1. Select Random tool
     2. Click or drag on canvas
     3. Random pixels appear based on settings
   - **Options**:
     - Density: 1-100% (how many pixels)
     - Color palette: Select colors to use
     - Brush size: Area of spray

8. **Eyedropper Tool**
   - **Function**: Pick color from canvas
   - **Flow**:
     1. Select Eyedropper tool
     2. Click on pixel
     3. Color is selected and set as current color
   - **Options**: None (automatic)

#### **Palette Group**

**Color Palette**:
- **Function**: Quick color selection
- **Default Colors**: 16 predefined colors
- **Flow**:
  1. Click color in palette
  2. Color becomes current drawing color
  3. Canvas updates to show selected color
- **Options**:
  - Add custom color: Click "+" button
  - Remove color: Right-click color
  - Edit color: Double-click color
  - Save palette: Export palette to file
  - Load palette: Import palette from file

**RGB Sliders**:
- **Function**: Fine-tune color values
- **Flow**:
  1. Adjust R, G, B sliders (0-255)
  2. Color updates in real-time
  3. Current color updates
- **Options**:
  - Red: 0-255
  - Green: 0-255
  - Blue: 0-255
  - Hex input: Enter hex code directly

**Gradient Generator**:
- **Function**: Generate gradients between colors
- **Flow**:
  1. Set start color
  2. Set end color
  3. Set number of steps
  4. Click "Generate"
  5. Gradient colors appear in palette
- **Options**:
  - Start color: RGB picker
  - End color: RGB picker
  - Steps: 2-256
  - Direction: Horizontal, Vertical, Radial

#### **Text Animation Group**

**Text Animation Tools**:
- **Function**: Create animated text effects and add text to frames
- **Flow**:
  1. Enter text in text input field
  2. Select font (built-in or custom bitmap font)
  3. Select animation type
  4. Configure parameters (color, speed, etc.)
  5. Click "Generate Text Frames"
  6. Text animation frames are created
- **Text Input**:
  - Enhanced text tool widget (primary)
  - Legacy text input (hidden, for compatibility)
  - Real-time preview as you type
- **Font Selection**:
  - Built-in 5×7 font (default)
  - Custom bitmap fonts from repository
  - Font Designer button to create/edit fonts
  - Font size: 4-16 pixels (for built-in font)
- **Animation Types**:
  - Typed (Character by Character)
  - Scrolling Left
  - Scrolling Right
  - Scrolling Up
  - Scrolling Down
- **Options**:
  - Text Color: Select color for text
  - Frames per Character: 1-10 (default: 2)
  - Font Size: 4-16 pixels (for built-in font)
  - Font Designer: Open font creation tool
- **Features**:
  - Enhanced text tool with advanced features
  - Real-time text preview
  - Font designer integration
  - Multiple animation styles

---

### 2. LED Colors Tab

Advanced LED color management and preview.

#### **LED Color Panel**

**Brightness Control**:
- **Function**: Adjust overall brightness
- **Flow**:
  1. Adjust brightness slider (0-100%)
  2. Canvas preview updates in real-time
  3. Pattern brightness changes
- **Options**:
  - Brightness: 0-100%
  - Per-frame brightness: Different brightness per frame
  - Brightness curve: Custom brightness curve

**Gamma Correction**:
- **Function**: Adjust gamma for LED color accuracy
- **Flow**:
  1. Adjust gamma slider (0.1-3.0)
  2. Colors adjust for LED display
  3. Preview updates
- **Options**:
  - Gamma: 0.1-3.0 (default: 2.2)
  - Per-channel gamma: Separate R, G, B gamma
  - Gamma curve: Custom gamma curve

**Color Temperature**:
- **Function**: Adjust color temperature (warm/cool)
- **Flow**:
  1. Adjust temperature slider (2000K-10000K)
  2. Colors shift warm or cool
  3. Preview updates
- **Options**:
  - Temperature: 2000K-10000K (default: 6500K)
  - Intensity: 0-100% (how much to apply)

**Preview Mode**:
- **Function**: Preview how colors will look on LED
- **Modes**:
  - **Normal**: Standard RGB preview
  - **LED Simulation**: Simulate LED color rendering
  - **Brightness Preview**: Show brightness levels
  - **Gamma Preview**: Show gamma correction
- **Flow**:
  1. Select preview mode
  2. Canvas updates to show preview
  3. Adjust settings to fine-tune

**LED Palette**:
- **Function**: LED-optimized color palette
- **Flow**:
  1. Select color from LED palette
  2. Color is optimized for LED display
  3. Color becomes current drawing color
- **Features**:
  - LED-optimized colors
  - Brightness-aware colors
  - Gamma-corrected colors

---

### 3. Pixel Mapping Tab

Configure pixel mapping and wiring for LED matrices.

#### **Pixel Mapping Widget**

**Wiring Configuration**:
- **Function**: Configure how pixels are mapped
- **Flow**:
  1. Select wiring mode
  2. Select start corner
  3. Configure row/column direction
  4. Apply to pattern
- **Wiring Modes**:
  - **Row-Major**: Left-to-right, top-to-bottom
  - **Serpentine**: Zigzag pattern
  - **Column-Major**: Top-to-bottom, left-to-right
  - **Column-Serpentine**: Vertical zigzag
- **Start Corners**:
  - Top-Left
  - Top-Right
  - Bottom-Left
  - Bottom-Right

**Pixel Order**:
- **Function**: Configure RGB order
- **Options**:
  - RGB
  - RBG
  - GRB
  - GBR
  - BRG
  - BGR
- **Flow**:
  1. Select pixel order
  2. Preview updates
  3. Apply to export

**Matrix Geometry**:
- **Function**: Define matrix shape
- **Options**:
  - **Matrix**: Standard grid
  - **Circle**: Circular arrangement
  - **Ring**: Ring arrangement
  - **Radial**: Radial arrangement
- **Flow**:
  1. Select geometry
  2. Configure parameters (radius, segments, etc.)
  3. Preview updates
  4. Apply to pattern

**Mapping Preview**:
- **Function**: Visual preview of pixel mapping
- **Shows**:
  - Pixel order
  - Wiring path
  - Start/end points
  - Direction arrows

---

### 4. Scratchpads Tab

Temporary storage for frames (similar to LED Matrix Studio buffers).

#### **Scratchpad System**

**Function**: Copy frames to temporary slots for later pasting

**Flow - Copy to Scratchpad**:
1. Paint or edit frame
2. Click "Copy" button on scratchpad slot (01-16)
3. Frame is copied to slot
4. Status changes to "Stored"
5. Slot persists with project

**Flow - Paste from Scratchpad**:
1. Select target frame
2. Click "Paste" button on filled scratchpad slot
3. Scratchpad contents paste into current frame
4. Frame updates
5. History entry created (undoable)

**Flow - Clear Scratchpad**:
1. Click "Clear" button on slot
2. Slot is cleared
3. Status changes to "Empty"

**Features**:
- **16 Slots**: Numbered 01-16
- **Persistent**: Saved with project file
- **Status Indicators**: Shows "Stored" or "Empty"
- **Visual Feedback**: Green text for stored, gray for empty
- **Tooltips**: Hover for slot information

**Use Cases**:
- Store background frames
- Save intermediate designs
- Copy frames between projects
- Create frame variations

---

### 5. Layers Tab

Multi-layer support with blend modes and visibility.

#### **Layer Panel Widget**

**Layer Management**:
- **Function**: Manage multiple layers per frame
- **Flow - Add Layer**:
  1. Click "Add Layer" button
  2. New layer appears in list
  3. Layer is active (selected)
  4. Can paint on new layer
- **Flow - Delete Layer**:
  1. Select layer
  2. Click "Delete" button
  3. Confirm deletion
  4. Layer removed
- **Flow - Duplicate Layer**:
  1. Select layer
  2. Click "Duplicate" button
  3. Copy of layer created
  4. New layer is active

**Layer Properties**:
- **Name**: Custom layer name
- **Visibility**: Eye icon to show/hide
- **Opacity**: 0-100% transparency
- **Blend Mode**: How layer blends with below layers
- **Lock**: Prevent editing

**Blend Modes**:
- **Normal**: Standard blending
- **Add**: Additive blending
- **Multiply**: Multiplicative blending
- **Screen**: Screen blending
- **Overlay**: Overlay blending
- **Difference**: Difference blending

**Layer Operations**:
- **Move Up/Down**: Reorder layers
- **Merge Down**: Combine with layer below
- **Flatten**: Merge all layers
- **Solo Mode**: Show only active layer
- **Lock/Unlock**: Prevent editing

**Active Layer**:
- **Function**: Layer currently being edited
- **Indication**: Highlighted in layer list
- **Behavior**: All drawing operations affect active layer
- **Switching**: Click layer to make active

**Composite View**:
- **Function**: Shows all visible layers combined
- **Toggle**: Switch between composite and active layer view
- **Update**: Updates in real-time as layers change

**Timeline Integration**:
- **Function**: Layers shown in timeline
- **Features**:
  - Layer tracks in timeline
  - Visibility toggles
  - Layer selection
  - Drag-and-drop reordering

**Automation Layer Integration**:
- **Function**: Automation operations create new layers instead of modifying frames directly
- **Flow**:
  1. Apply automation (scroll, rotate, mirror, etc.)
  2. New layer is automatically created with "Auto:" prefix
  3. Layer name indicates the automation type (e.g., "Auto: Scroll Left")
  4. Frame pixels are updated from layer composite
  5. Original layers remain intact
- **Benefits**:
  - Preserves original layer data
  - Allows toggling automation effects on/off
  - Enables multiple automation layers
  - Non-destructive workflow
- **Layer Naming**: Automation layers are prefixed with "Auto:" for easy identification

**Layer Sync Detection**:
- **Function**: Detects when layers are out of sync with frame pixels
- **Flow**:
  1. System checks if layer composite matches frame pixels
  2. If out of sync, warning banner appears
  3. Warning shows: "⚠️ Layers are out of sync with frame X - sync recommended"
  4. "Sync Layers" button available to restore sync
- **Sync Warning Banner**:
  - Appears automatically when layers are out of sync
  - Yellow/orange warning color
  - Contains sync button and dismiss option
  - Updates in real-time as layers change
- **Sync Layers Button**:
  - Replaces active layer with current frame pixels
  - Hides all other layers
  - Confirmation dialog before syncing
  - Restores layer-to-frame synchronization
- **When Sync Issues Occur**:
  - After automation operations
  - After manual frame pixel modifications
  - After loading patterns with mismatched data

**Copy Layer to Frames**:
- **Function**: Copy a layer from one frame to multiple target frames
- **Flow**:
  1. Right-click on layer in layer panel
  2. Select "Copy Layer to Frame" from context menu
  3. Dialog appears with frame selection
  4. Select target frames (checkboxes)
  5. Click "Copy"
  6. Layer is copied to selected frames
- **Features**:
  - Preserves layer name, pixels, and properties
  - Can copy to multiple frames at once
  - Creates new layer in target frames
  - Original layer remains unchanged
- **Use Cases**:
  - Duplicate base layers across frames
  - Share automation layers between frames
  - Copy background layers to animation frames

**Hidden Layer Prevention**:
- **Function**: Prevents painting on hidden layers
- **Flow**:
  1. User hides a layer (eye icon)
  2. User attempts to paint
  3. System detects hidden layer is active
  4. Dialog appears: "Cannot paint on hidden layer"
  5. User must make layer visible or switch to visible layer
- **Benefits**:
  - Prevents accidental edits on hidden layers
  - Maintains layer visibility state
  - Clear user feedback
- **Error Message**: "This layer is hidden. Please make it visible or select a different layer to paint."

**Brush Broadcast Feedback**:
- **Function**: Visual feedback when brush broadcast mode is active
- **Flow**:
  1. Enable "Apply brush strokes to all frames" checkbox
  2. Warning dialog appears on first enable
  3. If confirmed, broadcast mode activates
  4. All frames in timeline are highlighted (yellow/orange)
  5. Visual indicator on checkbox (red border, warning icon)
  6. Warning banner appears at top of canvas
- **Visual Indicators**:
  - Timeline frame highlighting: All frames show yellow/orange highlight
  - Checkbox styling: Red border and warning icon when active
  - Warning banner: "⚠️ Broadcast Mode Active - All frames will be affected"
- **Warning Dialog**:
  - Appears on first enable
  - Message: "⚠️ WARNING: Broadcast Mode will apply ALL brush strokes to EVERY frame..."
  - Options: "Yes" (enable) or "No" (cancel)
  - Can be dismissed permanently per session

---

### 6. Effects Tab

Visual effects library for frames.

#### **Effects Library Widget**

**Effect Categories**:
- **Blur**: Blur effects
- **Color**: Color adjustments
- **Distortion**: Distortion effects
- **Glow**: Glow effects
- **Motion**: Motion effects
- **Pattern**: Pattern effects
- **Custom**: User-created effects

**Effect Application Flow**:
1. Select frame(s) to apply effect
2. Browse effects library
3. Select effect
4. Preview effect (optional)
5. Configure parameters
6. Click "Apply"
7. Effect applied to frame(s)
8. History entry created

**Effect Parameters**:
- **Intensity**: 0-100% effect strength
- **Duration**: Frames affected
- **Blend Mode**: How effect blends
- **Custom Parameters**: Effect-specific options

**Effect Preview**:
- **Function**: Preview effect before applying
- **Flow**:
  1. Select effect
  2. Click "Preview" button
  3. Preview dialog opens
  4. Adjust parameters
  5. See real-time preview
  6. Click "Apply" or "Cancel"

**Effect Library Management**:
- **Refresh**: Reload effects from disk
- **Open Folder**: Open effects directory
- **Add Custom**: Add custom effect files
- **Categories**: Filter by category

**Available Effects** (Sample):
- **Blur**: Gaussian blur, motion blur
- **Color**: Hue shift, saturation, brightness
- **Glow**: Outer glow, inner glow
- **Distortion**: Wave, ripple, twirl
- **Pattern**: Checkerboard, stripes, dots

---

### 7. Automation Tab

Two automation systems: Canvas Automation and LMS Automation.

#### **Canvas Automation Panel**

**Automation Actions**:
Queue transformations that apply across frame ranges.

**Available Actions**:
1. **Scroll**
   - **Function**: Scroll pattern horizontally or vertically
   - **Flow**:
     1. Select frame range
     2. Choose scroll direction (Up, Down, Left, Right)
     3. Set offset per frame (1-10 pixels, default: 1)
     4. Click "Add to Queue"
     5. Action queued
   - **Options**:
     - Direction: Up, Down, Left, Right (default: Right)
     - Offset per Frame: 1-10 pixels (default: 1)
     - Description: Number of pixels to shift per frame

2. **Rotate**
   - **Function**: Rotate pattern 90 degrees
   - **Flow**:
     1. Select frame range
     2. Choose rotation mode (90° Clockwise or 90° Counter-clockwise)
     3. Click "Add to Queue"
   - **Options**:
     - Rotation: 90° Clockwise (default), 90° Counter-clockwise
     - Note: Only 90-degree rotations supported

3. **Mirror**
   - **Function**: Mirror pattern along axis
   - **Flow**:
     1. Select frame range
     2. Choose axis (horizontal or vertical)
     3. Click "Add to Queue"
   - **Options**:
     - Axis: Horizontal (default), Vertical

4. **Flip**
   - **Function**: Flip pattern
   - **Flow**:
     1. Select frame range
     2. Choose axis (vertical or horizontal)
     3. Click "Add to Queue"
   - **Options**:
     - Axis: Vertical (default), Horizontal

5. **Invert**
   - **Function**: Invert colors
   - **Flow**:
     1. Select frame range
     2. Click "Add to Queue"
   - **Options**:
     - Inverts all RGB values: (255 - r, 255 - g, 255 - b)
     - Applies to all pixels in selected frames

6. **Wipe**
   - **Function**: Wipe transition effect
   - **Flow**:
     1. Select frame range
     2. Choose mode (Left to Right, Right to Left, Top to Bottom, Bottom to Top)
     3. Set offset per frame (1-10 pixels, default: 1)
     4. Set intensity (0.1-5.0, default: 1.0)
     5. Click "Add to Queue"
   - **Options**:
     - Mode: Left to Right (default), Right to Left, Top to Bottom, Bottom to Top
     - Offset per Frame: 1-10 pixels (default: 1)
     - Intensity: 0.1-5.0 multiplier (default: 1.0, step: 0.1)
     - Description: Multiplier for the wipe fade intensity

7. **Reveal**
   - **Function**: Reveal pattern gradually
   - **Flow**:
     1. Select frame range
     2. Choose reveal direction (Left, Right, Top, Bottom)
     3. Set offset per frame (1-10 pixels, default: 1)
     4. Set feather pixels (0-10, default: 0) - softens edge
     5. Click "Add to Queue"
   - **Options**:
     - Reveal From: Left (default), Right, Top, Bottom
     - Offset per Frame: 1-10 pixels (default: 1)
     - Feather Pixels: 0-10 (default: 0) - Softens the reveal edge

**Action Queue**:
- **Function**: List of queued actions
- **Features**:
  - View all queued actions
  - Reorder actions (drag-and-drop)
  - Remove actions
  - Duplicate actions
  - Edit action parameters

**Processing**:
- **Function**: Execute queued actions
- **Flow**:
  1. Review action queue
  2. Click "Process Queue"
  3. Progress dialog appears
  4. Actions execute in order
  5. **New "Auto:" layer created for each automation** (e.g., "Auto: Scroll Left")
  6. Frames update from layer composite
  7. History entries created
- **Layer Integration**:
  - Each automation creates a new layer (non-destructive)
  - Layer name indicates automation type
  - Original layers remain intact
  - Can toggle automation layers on/off
  - Multiple automation layers can be stacked
- **Options**:
  - Process all: Execute all actions
  - Process selected: Execute selected actions only
  - Preview: Preview before processing

**Presets**:
- **Function**: Save and load action presets
- **Flow - Save Preset**:
  1. Configure actions
  2. Click "Save Preset"
  3. Enter name
  4. Preset saved
- **Flow - Load Preset**:
  1. Click "Load Preset"
  2. Select preset
  3. Actions load into queue
- **Features**:
  - Preset library
  - Share presets
  - Import/export presets

#### **LMS Automation Panel**

LED Matrix Studio instruction builder for MCU-ready patterns.

**Instruction Builder Tab**:

**Layer Bindings**:
- **Source (Layer 1)**: Primary frame source
- **Layer 2 (optional)**: Secondary layer for blending
- **Mask (optional)**: Mask frame for selective application
- **Flow**:
  1. Select source frame from dropdown
  2. Optionally select Layer 2 frame
  3. Optionally select mask frame
  4. Configure instruction parameters

**Instruction Parameters**:
- **Action**: LMS action code (scroll, rotate, etc.)
- **Repeat Count**: How many times MCU executes (1-999)
- **Gap Spacing**: Frame spacing between repeats (0-120 frames)
- **Brightness Delta**: Brightness adjustment (-255 to +255)
- **Extra Params**: JSON parameters for custom actions
- **Flow**:
  1. Select action from dropdown
  2. Set repeat count
  3. Set gap spacing (optional)
  4. Set brightness delta (optional)
  5. Add custom params (optional)
  6. Click "Add Instruction"

**Custom Actions**:
- **Function**: Define custom MCU instructions
- **Flow**:
  1. Select "Custom…" from action dropdown
  2. Enter custom instruction code
  3. Configure parameters
  4. Add to queue

**Queue & Preview Tab**:

**Instruction Queue**:
- **Function**: List of LMS instructions
- **Features**:
  - View all instructions
  - Remove instructions
  - Duplicate instructions
  - Move up/down
  - Clear all
- **Display Format**:
  - `Frame1 → SCROLL • repeat ×5 • gap 2 • L2 Frame2 • Mask Frame3`

**Preview Sequence**:
- **Function**: Preview LMS sequence without baking frames
- **Flow**:
  1. Build instruction sequence
  2. Click "Preview Sequence"
  3. Preview dialog opens
  4. Animation plays based on instructions
  5. Can adjust and re-preview
- **Options**:
  - Max frames: Limit preview length (1-240)
  - Loop: Repeat preview
  - Speed: Playback speed

**Apply Preview**:
- **Function**: Apply preview changes to pattern
- **Flow**:
  1. Preview sequence
  2. Make adjustments
  3. Click "Apply Preview Changes"
  4. Changes applied to pattern
  5. Frames updated

**Restore Original**:
- **Function**: Restore pattern before preview
- **Flow**:
  1. Click "Restore Original" (Ctrl+R)
  2. Pattern reverts to state before preview
  3. Preview changes discarded

**Import / Export Tab**:

**Import LEDS**:
- **Function**: Import LED Matrix Studio .leds files
- **Flow**:
  1. Click "Import LEDS…"
  2. Select .leds file
  3. File parsed
  4. Instructions load into queue
  5. Frames imported if present

**Export LEDS**:
- **Function**: Export instruction sequence as .leds file
- **Flow**:
  1. Build instruction sequence
  2. Click "Export LEDS…"
  3. Choose destination
  4. File exported
  5. Ready for MCU

**Analyze DAT/HEX/BIN**:
- **Function**: Inspect exported files
- **Flow**:
  1. Click "Analyze DAT/HEX/BIN…"
  2. Select file
  3. Analysis dialog opens
  4. Shows metadata, dimensions, etc.
  5. Verify before flashing

---

### 8. Export Tab

Pattern export, import, and code generation.

#### **Import Group**

**Import Image/GIF**:
- **Function**: Import images or GIFs as frames
- **Flow**:
  1. Click "Import Image/GIF"
  2. Select file
  3. Choose resize mode
  4. Click "Import"
  5. Image converted to frame(s)
- **Resize Modes**:
  - **Fit (Maintain Aspect)**: Scale to fit, keep aspect ratio
  - **Stretch (Fill Matrix)**: Stretch to fill, may distort
  - **Crop (Center)**: Crop to fit, center crop
- **Options**:
  - Dithering: Apply dithering for color reduction
  - Color quantization: Reduce color count
  - Frame extraction: Extract frames from GIF

#### **Matrix Configuration Group**

**Matrix Settings**:
- **Width**: Matrix width (1-256 pixels)
- **Height**: Matrix height (1-256 pixels)
- **Colour Mode**: Mono, Bi-colour, RGB
- **Background**: Select background color
- **Preset**: Matrix dimension presets (Custom, 8×8, 16×16, etc.)
- **Dimension Source**: Shows where dimensions came from (design session, imported file, etc.)
- **Flow**:
  1. Adjust width/height spinners
  2. Select colour mode
  3. Optionally set background color
  4. Select preset or use custom
  5. Dimensions update automatically
  6. Canvas resizes
  7. Pattern metadata updated

#### **Pattern Export Group**

**Save Design to Pattern**:
- **Function**: Save current design as pattern
- **Flow**:
  1. Enter pattern name (optional)
  2. Click "Save Design to Pattern"
  3. Pattern saved
  4. Available in other tabs (Preview, Flash, WiFi Upload)
- **Options**:
  - Pattern name
  - Include metadata
  - Include layers
  - Include automation

**Optimize Pattern**:
- **Function**: Remove duplicates and compress
- **Flow**:
  1. Click "Optimize Pattern"
  2. Analysis runs
  3. Duplicate frames removed
  4. Colors compressed
  5. Pattern optimized
- **Optimizations**:
  - Remove duplicate frames
  - Compress color palette
  - Merge similar frames
  - Remove empty frames

**Export Frame as Image**:
- **Function**: Export current frame as image
- **Flow**:
  1. Select frame
  2. Click "Export Frame as Image"
  3. Choose format (PNG, BMP, etc.)
  4. Choose destination
  5. Frame exported
- **Formats**: PNG, BMP, JPEG, GIF

**Export Animation as GIF**:
- **Function**: Export all frames as animated GIF
- **Flow**:
  1. Click "Export Animation as GIF"
  2. Configure GIF options
  3. Choose destination
  4. Click "Export"
  5. GIF created
- **Options**:
  - Frame duration: ms per frame
  - Loop: Repeat animation
  - Dithering: Color dithering
  - Color palette: Number of colors

#### **Code Template Group**

**MCU Code Templates**:
- **Function**: Generate ready-to-paste code for microcontrollers
- **Flow**:
  1. Select template (Arduino, PIC, etc.)
  2. Click "Export Code Template"
  3. Code generated
  4. Copy to clipboard or save
- **Templates**:
  - Arduino (FastLED, NeoPixel)
  - PIC (PIC18F4550, etc.)
  - ESP32 (ESP-IDF, Arduino)
  - STM32
  - Custom templates
- **Options**:
  - Include pattern data
  - Include initialization
  - Include playback code
  - Optimize for size

**Backup Custom Fonts**:
- **Function**: Backup custom bitmap fonts
- **Flow**:
  1. Click "Backup Custom Fonts…"
  2. Choose destination
  3. Fonts exported
  4. Can restore later

#### **Export Summary Group**

**Export Summary**:
- **Function**: Shows export information
- **Displays**:
  - Pattern dimensions
  - Frame count
  - Total duration
  - File size estimate
  - Export format info

---

## Timeline Dock

Located at the bottom, manages frames and playback.

### Components:

#### **Timeline Widget**

**Frame Display**:
- **Function**: Visual timeline of frames
- **Features**:
  - Frame thumbnails
  - Frame numbers
  - Frame duration bars
  - Playhead indicator
  - Selection highlighting
  - Multi-select support

**Frame Operations**:
- **Add Frame**: Create new frame (Ctrl+Shift+A)
- **Duplicate Frame**: Copy selected frame
- **Delete Frame**: Remove frame (Del)
- **Reorder Frames**: Drag-and-drop to reorder

**Playhead**:
- **Function**: Current frame indicator
- **Features**:
  - Draggable playhead
  - Shows current frame
  - Updates during playback
  - Can drag to jump to frame

**Playback Controls**:
- **Previous Frame**: Step back (←)
- **Play**: Start playback (Space key)
- **Pause**: Pause playback (Space key)
- **Stop**: Stop and reset to first frame
- **Next Frame**: Step forward (→)
- **Loop**: Toggle loop mode (∞ symbol)
- **FPS Control**: Playback frames per second (1-240, default: 24)
  - Located in header toolbar
  - Adjusts playback speed
  - Updates in real-time
- **Playback Info**: Shows "Loop: ∞ • X ms/frame" status

**Frame Duration**:
- **Function**: Set duration per frame
- **Flow**:
  1. Select frame(s)
  2. Adjust duration spinner (1-2000 ms)
  3. Duration updates immediately
  4. Timeline refreshes
  5. Playback speed adjusts
- **Options**:
  - Duration: 1-2000 milliseconds (default: varies)
  - Per-frame: Different duration per frame (supported)
  - Global: Can set same duration for all frames
- **Location**: Timeline controls bar, labeled "Frame duration (ms):"

**Timeline Zoom**:
- **Function**: Zoom timeline view
- **Flow**:
  1. Adjust zoom slider (25%-400%)
  2. Timeline scales horizontally
  3. More/less frames visible
  4. Zoom percentage shown in label
- **Options**:
  - Zoom: 25%-400% (default: 100%)
  - Slider: Horizontal slider with label showing percentage
  - Location: Timeline controls bar
  - Updates: Real-time as slider moves

**Layer Tracks**:
- **Function**: Show layers in timeline
- **Features**:
  - Layer rows below main timeline
  - Layer visibility toggles (eye icon)
  - Layer selection
  - Layer drag-and-drop
  - Layer duration visualization

**Simple Mode**:
- **Function**: Hide layer tracks for simple animations
- **Toggle**: "Hide layers (simple animations)" checkbox
- **Effect**: Hides layer tracks, shows only main timeline

**Markers**:
- **Function**: Mark important frames
- **Flow**:
  1. Right-click frame
  2. Select "Add Marker"
  3. Enter label
  4. Marker appears on timeline
- **Features**:
  - Custom labels
  - Color coding
  - Jump to marker

**Automation Overlays**:
- **Function**: Show automation actions on timeline
- **Features**:
  - Visual bars showing action range
  - Color-coded by action type
  - Click to select action
  - Tooltips show action details

**Context Menu**:
- **Function**: Right-click menu for frames
- **Options**:
  - Add Frame
  - Duplicate Frame
  - Delete Frame
  - Add Marker
  - Set Duration
  - Copy Frame
  - Paste Frame

---

## Complete Feature Flows

### Flow 1: Create New Pattern

1. Click "New" button in header
2. Dialog opens
3. Set width and height
4. Select LED type
5. Click "Create"
6. Blank pattern loads
7. Canvas shows empty frame
8. Ready to draw

### Flow 2: Draw and Animate

1. Select drawing tool (e.g., Pixel)
2. Select color from palette
3. Paint on canvas
4. Add new frame (Ctrl+Shift+A)
5. Paint next frame
6. Repeat for animation
7. Adjust frame durations
8. Play preview
9. Save pattern

### Flow 3: Apply Automation

1. Create base frames
2. Go to Automation tab
3. Select frame range
4. Choose action (e.g., Scroll)
5. Configure parameters
6. Add to queue
7. Repeat for more actions
8. Click "Process Queue"
9. Frames update with automation
10. Preview result

### Flow 4: Multi-Layer Workflow

1. Create base layer
2. Add new layer
3. Paint on new layer
4. Set blend mode
5. Adjust opacity
6. Toggle visibility
7. Add more layers
8. View composite
9. Export pattern

### Flow 5: Import and Edit

1. Click "Import Image/GIF"
2. Select file
3. Choose resize mode
4. Import
5. Frames created from image/GIF
6. Edit frames as needed
7. Apply effects
8. Add automation
9. Export pattern

### Flow 6: LMS Instruction Workflow

1. Create base frames
2. Go to Automation → LMS Automation
3. Select source frame
4. Choose LMS action
5. Set repeat and gap
6. Add instruction
7. Repeat for more instructions
8. Preview sequence
9. Export LEDS file
10. Flash to MCU

### Flow 7: Effect Application

1. Select frame(s)
2. Go to Effects tab
3. Browse effects
4. Select effect
5. Preview effect
6. Adjust parameters
7. Apply effect
8. Effect applied to frames
9. Can undo if needed

### Flow 8: Scratchpad Workflow

1. Paint frame
2. Go to Scratchpads tab
3. Click "Copy" on slot 01
4. Frame stored
5. Edit frame or create new
6. Click "Paste" on slot 01
7. Original frame restored
8. Can use multiple slots

---

## Keyboard Shortcuts

### General
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Ctrl+D**: Duplicate frame
- **Ctrl+R**: Restore original (LMS preview)
- **Delete**: Clear current frame

### Canvas Operations
- **Space**: Play/Pause playback
- **Ctrl+N**: Invert colors
- **Ctrl+H**: Flip horizontal
- **Ctrl+V**: Flip vertical
- **Ctrl+I**: Eyedropper tool (or E key)
- **E**: Eyedropper tool (when not in text input)
- **Ctrl+0**: Reset zoom (handled by canvas)
- **Ctrl+1**: Fit to window (handled by canvas)

### Frames
- **Ctrl+Shift+A**: Add new frame
- **Ctrl+D**: Duplicate selected frame
- **Delete**: Clear/delete frame

### Timeline
- **Space**: Play/Pause
- **←**: Previous frame (step back)
- **→**: Next frame (step forward)
- **Home**: First frame
- **End**: Last frame
- **Page Up**: Previous page
- **Page Down**: Next page

**Note**: Some shortcuts like Ctrl+N (New), Ctrl+O (Open), Ctrl+S (Save) are handled by the main window, not the Design Tools Tab itself.

---

## Advanced Workflows

### Workflow 1: Complex Animation

1. Create base frames with drawing tools
2. Add layers for different elements
3. Apply effects to specific layers
4. Use scratchpads to store variations
5. Queue automation actions
6. Preview with timeline
7. Adjust frame durations
8. Export as pattern and GIF

### Workflow 2: Text Animation

1. Go to Brushes tab → Text Animation group
2. Enter text in text input field
3. Choose font
4. Select animation type (scroll)
5. Configure animation parameters
6. Add to frame
7. Text animates across frames
8. Adjust speed and duration
9. Export

### Workflow 3: LED-Optimized Design

1. Set matrix dimensions
2. Configure pixel mapping
3. Adjust LED colors (brightness, gamma)
4. Preview with LED simulation
5. Fine-tune colors
6. Export with correct pixel order
7. Generate MCU code
8. Flash to hardware

### Workflow 4: Template-Based Design

1. Click Templates button
2. Select template category
3. Choose template
4. Adjust parameters
5. Generate pattern
6. Customize frames
7. Add automation
8. Export

### Workflow 5: Version Control Workflow

1. Create pattern
2. Make changes
3. Auto-versioning saves versions
4. Continue editing
5. Click Version History
6. Browse versions
7. Compare versions
8. Restore if needed
9. Continue from restored version

---

## Technical Details

### Data Flow

```
User Action (UI Event)
    ↓
Manager Method (Domain Logic)
    ↓
PatternState Update (Model Change)
    ↓
Signal Emitted (State Change Notification)
    ↓
UI Update (View Refresh)
```

### Managers

- **PatternState**: Single source of truth for pattern data
- **FrameManager**: Frame operations (add, delete, duplicate, reorder)
- **LayerManager**: Multi-layer support and blending
- **CanvasController**: Canvas rendering and interaction
- **AutomationQueueManager**: Automation action queue
- **HistoryManager**: Undo/redo system
- **ScratchpadManager**: Temporary frame storage
- **EffectLibrary**: Visual effects management
- **BitmapFontRepository**: Font asset management

### File Formats

- **.leds**: LED Matrix Studio format
- **.dat**: Data format
- **.hex**: Intel HEX format
- **.bin**: Binary format
- **.json**: Pattern JSON format
- **.ledproj**: Project file format

---

## Conclusion

The Design Tools Tab provides a comprehensive environment for creating LED matrix patterns. With 8 toolbox tabs, multiple drawing tools, layer support, automation, effects, and export options, it offers everything needed to create professional LED animations.

This guide covers all features, options, and workflows. For specific questions or advanced usage, refer to the code documentation or contact support.

---

**Last Updated**: 2025-11-27  
**Document Version**: 1.0

