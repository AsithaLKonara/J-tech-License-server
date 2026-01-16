# LED Matrix Studio - User Guide

## Introduction

LED Matrix Studio is a powerful, production-grade LED matrix animation editor that allows you to create, edit, and export animations for LED matrices. This guide will help you get started with creating stunning LED animations.

## Getting Started

### Installation

1. **Download the Application**
   - Download the latest release from the distribution package
   - Extract the archive to your desired location
   - Run `UploadBridge.exe` (Windows) or the appropriate executable for your platform

2. **System Requirements**
   - Windows 10/11, macOS 10.14+, or Linux
   - 4GB RAM minimum (8GB recommended)
   - 500MB free disk space

### First Launch

When you first launch LED Matrix Studio, you'll see:
- **Timeline**: Control animation playback and frame navigation
- **Layer Panel**: Manage multiple animation layers
- **Preview**: Real-time preview of your animation
- **Effect & Keyframe Editor**: Apply effects and create keyframe animations
- **Export & Playback**: Export your animations in various formats

## Core Concepts

### Projects

A **Project** is the container for your entire animation. It includes:
- **Timeline**: Defines FPS and duration
- **Layers**: Multiple layers that can be composited together
- **Keyframes**: Animated properties over time
- **Effects**: LED-specific effects (scroll, fade, blink, etc.)

### Layers

Layers are the building blocks of your animation:
- Each layer can contain different content
- Layers can be stacked and blended using different blend modes
- Each layer has its own opacity, visibility, and z-index
- Layers can have keyframes for animated properties

### Keyframes

Keyframes allow you to animate properties over time:
- Set keyframes at specific frames
- Properties interpolate between keyframes
- Support for easing curves (linear, ease-in, ease-out, etc.)
- Bezier curves for smooth, natural animations

## Creating Your First Animation

### Step 1: Create a New Project

1. Click **File > New Project** (or use the default project)
2. Set your matrix dimensions (width × height)
3. Set FPS (frames per second) - typically 30 FPS
4. Set duration in seconds

### Step 2: Add Content to Layers

1. Select a layer from the **Layer Panel**
2. Use drawing tools or import images
3. Each frame in the timeline represents a point in time

### Step 3: Apply Effects

1. Select a layer
2. Choose an effect from the **Effect** dropdown:
   - **Scroll**: Move content horizontally or vertically
   - **Fade**: Fade in/out over time
   - **Blink**: Create blinking patterns
   - **Color Shift**: Shift colors through the spectrum
   - **Wave**: Create wave-like animations
   - **Pulse**: Pulsing brightness effects
   - **Rainbow**: Rainbow color cycling
   - **Sparkle**: Random sparkle effects
   - **Wipe**: Wipe transitions

3. Click **Apply Effect** to apply to the selected layer

### Step 4: Add Keyframes

1. Select a layer and property (e.g., "opacity")
2. Navigate to the frame where you want the keyframe
3. Click **Add Keyframe**
4. Set the value for that keyframe
5. Add more keyframes at different frames to create animation

### Step 5: Preview Your Animation

1. Use the **Play** button to preview your animation
2. Use the timeline scrubber to navigate to specific frames
3. The preview updates in real-time

### Step 6: Export Your Animation

1. Choose an export format:
   - **JSON**: Human-readable format for editing
   - **CSV**: Spreadsheet-compatible format
   - **Binary**: Compact binary format
   - **LED Pattern**: Native LED pattern format
   - **MP4/GIF**: Video formats for previews
   - **LED Hardware**: Export for specific LED protocols (WS2812B, APA102, etc.)

2. Click **Export** and choose a location

## Advanced Features

### Layer Compositing

- **Blend Modes**: Normal, Multiply, Screen, Overlay, Add, Subtract
- **Opacity**: Control layer transparency (0-100%)
- **Z-Index**: Control layer stacking order
- **Visibility**: Toggle layers on/off

### Timeline Management

- **Retiming**: Change animation duration while preserving keyframes
- **FPS Changes**: Adjust frame rate with different interpolation modes
- **Frame Navigation**: Use arrow keys or timeline scrubber

### Keyframe Animation

- **Regular Keyframes**: Linear or eased interpolation
- **Bezier Keyframes**: Smooth, curved animations
- **Auto-Smooth**: Automatically smooth bezier curves
- **Property Animation**: Animate opacity, position, color, and more

### Version Control

- **Save Versions**: Create snapshots of your project
- **Undo/Redo**: Step through your editing history
- **Version List**: View and load previous versions

### Cloud Sync

- **Sync to Cloud**: Upload projects to cloud storage
- **Download from Cloud**: Retrieve synced projects
- **Conflict Resolution**: Automatic handling of sync conflicts

## Tips & Best Practices

1. **Start Simple**: Begin with basic effects and gradually add complexity
2. **Use Layers**: Organize content into separate layers for easier editing
3. **Keyframe Timing**: Space keyframes appropriately for smooth animations
4. **Performance**: Large matrices (64×32+) may require optimization
5. **Export Testing**: Test exports on actual hardware when possible
6. **Version Control**: Save versions frequently to avoid losing work

## Troubleshooting

### Animation Not Playing
- Check that frames exist in the timeline
- Verify layer visibility is enabled
- Ensure FPS is set correctly

### Export Fails
- Check file path permissions
- Ensure sufficient disk space
- Verify export format is supported

### Performance Issues
- Reduce matrix size for testing
- Use fewer layers
- Disable preview during editing

## Keyboard Shortcuts

- **Left Arrow**: Previous frame
- **Right Arrow**: Next frame
- **Space**: Play/Pause
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Ctrl+S**: Save project
- **Ctrl+O**: Open project
- **Ctrl+N**: New project

## Getting Help

For additional support:
- Check the Developer Documentation
- Review example projects
- Contact support through the application

---

**Version**: 1.0.0  
**Last Updated**: 2024

