# Upload Bridge - Quick Start Guide

Welcome to Upload Bridge! This guide will help you get started creating LED matrix patterns in just a few minutes.

## Installation (5 Steps)

### Step 1: Download Upload Bridge
- Download the installer for your platform (Windows, macOS, or Linux)
- Or clone the repository: `git clone https://github.com/your-repo/upload_bridge.git`

### Step 2: Install Python (if needed)
- Upload Bridge requires Python 3.10 or higher
- Download from [python.org](https://www.python.org/downloads/)
- Verify installation: `python --version`

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python main.py
```

### Step 5: Launch Application
- Run `python main.py` from the project directory
- Or use the installer to create a desktop shortcut

---

## Create Your First Pattern (10 Steps)

### Step 1: Open Upload Bridge
Launch the application and you'll see the main window with multiple tabs.

### Step 2: Go to Design Tools Tab
Click on the **"Design Tools"** tab to access the pattern editor.

### Step 3: Set Matrix Dimensions
- In the canvas area, set your LED matrix dimensions (e.g., 32x32, 64x32)
- Use the dimension controls in the toolbar

### Step 4: Select a Drawing Tool
Choose from the drawing tools:
- **Pixel Tool**: Draw individual pixels
- **Rectangle Tool**: Draw rectangles
- **Circle Tool**: Draw circles
- **Line Tool**: Draw lines
- **Fill Tool**: Fill areas with color
- **Gradient Tool**: Create gradients
- **Text Tool**: Add text

### Step 5: Choose a Color
- Click the color picker in the toolbar
- Select your desired color
- Or use the palette for quick color selection

### Step 6: Draw Your First Frame
- Click and drag on the canvas to draw
- Create a simple pattern (e.g., a smiley face, text, or geometric shape)

### Step 7: Add More Frames
- Click the **"+"** button in the timeline to add a new frame
- Draw different content in each frame to create animation

### Step 8: Set Frame Duration
- Select a frame in the timeline
- Set the duration (in milliseconds) for how long the frame displays
- Typical values: 100-500ms for smooth animation

### Step 9: Preview Your Animation
- Click the **Play** button to preview your animation
- Use **Stop** to pause
- Adjust frame durations as needed

### Step 10: Save Your Project
- Click **File → Save Project** (or Ctrl+S)
- Choose a location and name your `.ledproj` file
- Your pattern is now saved!

---

## Export and Flash (5 Steps)

### Step 1: Prepare Your Hardware
- Connect your microcontroller (ESP32, ATmega, etc.) to your computer
- Ensure the correct drivers are installed

### Step 2: Select Your Chip
- Go to the **Flash** tab
- Select your microcontroller type from the dropdown (e.g., ESP32, ATmega2560)

### Step 3: Configure Settings
- Set the serial port (COM port on Windows, /dev/tty* on Linux/Mac)
- Configure LED settings:
  - LED type (WS2812B, SK6812, etc.)
  - Color order (RGB, GRB, etc.)
  - Number of LEDs
  - Pin number

### Step 4: Build Firmware
- Click **"Build Firmware"** to compile the firmware with your pattern
- Wait for the build to complete (this may take a minute)

### Step 5: Flash to Device
- Click **"Flash Firmware"** to upload to your microcontroller
- Wait for the upload to complete
- Your pattern should now be playing on your LED matrix!

---

## Common Workflows

### Simple Animation
1. Create 3-5 frames with slight variations
2. Set frame durations to 200-300ms
3. Preview and adjust
4. Export and flash

### Text Scrolling
1. Use the Text Tool to create text in a frame
2. Duplicate the frame multiple times
3. Use the Scroll automation action to create scrolling effect
4. Set appropriate frame duration for scroll speed

### Image Import
1. Go to **Media Upload** tab
2. Select an image file (PNG, JPG, GIF)
3. Set target dimensions
4. Adjust brightness and color settings
5. Convert to LED pattern
6. Load into Design Tools for editing

---

## Next Steps

Now that you've created your first pattern:

1. **Explore Drawing Tools**: Try all 8 drawing tools to see their capabilities
2. **Learn About Layers**: Use multiple layers for complex compositions
3. **Try Automation**: Use automation actions (scroll, rotate, mirror) for dynamic effects
4. **Read the User Manual**: See `docs/USER_MANUAL.md` for detailed documentation
5. **Check Examples**: Look at example patterns in the `examples/` directory

---

## Tips

- **Start Small**: Begin with small matrices (8x8 or 16x16) to learn quickly
- **Use Presets**: Save common frame patterns as presets for reuse
- **Keyboard Shortcuts**: Learn keyboard shortcuts for faster workflow (see User Manual)
- **Save Often**: Use Ctrl+S frequently to save your work
- **Preview First**: Always preview before flashing to hardware

---

## Troubleshooting

### Application Won't Start
- Check Python version: `python --version` (needs 3.10+)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Can't Connect to Device
- Check USB cable connection
- Verify correct COM port selected
- Install device drivers if needed
- Try different USB port

### Pattern Doesn't Display Correctly
- Check LED wiring configuration
- Verify color order settings
- Check matrix dimensions match hardware
- Review brightness settings

### Need More Help?
- See `docs/TROUBLESHOOTING.md` for detailed troubleshooting
- Check `docs/USER_MANUAL.md` for comprehensive documentation
- Review `docs/INSTALLATION.md` for installation issues

---

**Happy Pattern Creating!** 🎨✨

