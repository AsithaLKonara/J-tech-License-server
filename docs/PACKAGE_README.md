# Upload Bridge - Universal Wiring Fix Edition
## Version 1.0 - Build 20251107

---

## 🎉 **What's Fixed in This Version**

This package contains the **COMPLETE UNIVERSAL FIX** for LED matrix wiring issues.

### **Major Features:**

✅ **File Format Auto-Detection**
- Automatically detects Serpentine, Row-major, Column-major, Column-serpentine
- Auto-detects data-in corner (Left Top, Left Bottom, Right Top, Right Bottom)
- Manual override available if needed

✅ **Universal Wiring Support**
- All 16 wiring/corner combinations fully supported
- Verified with comprehensive tests (all passing)
- Deterministic pixel mapping with checksums
- Flip X/Y corrections for orientation mismatches

✅ **Brightness Options**
- Global brightness slider (0-100%)
- Brightness curves (Linear, Gamma, Logarithmic, etc.)
- Per-channel RGB controls
- LED type selection (WS2812, SK6812, APA102, etc.)
- All settings exported to firmware

✅ **Preview Always Correct**
- Preview shows design order (all rows left-to-right)
- No more flipped rows in preview
- What you see is what you get

✅ **Comprehensive Logging**
- Traces every conversion step
- SHA-256 checksums for verification
- BEFORE/AFTER pixel samples at each stage
- Easy debugging

---

## 📦 **Package Contents**

### **Core Application:**
- `main.py` - Main application entry point
- `ui/` - User interface modules (Preview, Flash, etc.)
- `core/` - Core logic modules
  - `file_format_detector.py` ⭐ NEW - Auto-detection
  - `pattern_converter.py` ⭐ NEW - Hardware ↔ Design conversion
  - `wiring_mapper.py` ⭐ NEW - All 16 wiring modes
  - `pattern.py` - Pattern data structures
- `parsers/` - File format parsers
  - `enhanced_binary_parser.py` - LED Matrix Studio format
- `firmware/` - Firmware generators and templates
- `uploaders/` - Chip uploaders (ESP8266, ESP32, etc.)

### **Documentation:**
- `AUTO_DETECT_AND_BRIGHTNESS_SUMMARY.md` - New features guide
- `UNIVERSAL_FIX_SUMMARY.md` - Complete fix summary
- `COMPLETE_FLOW_DOCUMENTATION.md` - Full pipeline documentation
- `DIAGNOSTIC_TOOLS_README.md` - Testing tools guide
- `docs/PREVIEW_vs_FIRMWARE_WIRING.md` - Visual wiring diagrams

### **Test & Diagnostic Tools:**
- `create_diagnostic_pattern.py` - Generate test patterns
- `diagnostic_12x6.bin` - Pre-made diagnostic pattern
- `test_brightness_options.py` - Verify brightness works
- `verify_all_16_wiring_combinations.py` - Test all 16 modes
- `verify_hardware_to_design.py` - Round-trip conversion test
- `verify_speed_brightness_pixel_order.py` - Order preservation test

### **Installer:**
- `install_simple.bat` - Simple dependency installer

---

## 🚀 **Quick Start**

### **Installation:**
1. Extract the ZIP file to a folder
2. Run `install_simple.bat` (installs Python dependencies)
3. Run `python main.py` to start the app

### **First Use:**
1. Load a pattern file (e.g., your "12.6 rows up down.bin")
2. **Auto-detection runs automatically** - check the console
3. Preview should show correctly (no flipped rows)
4. Go to Flash tab
5. Select your target hardware wiring
6. Click "Flash to Device"
7. Verify hardware matches preview

---

## 🔍 **How to Use Auto-Detection**

### **File Format Dropdowns (Preview Tab):**

**"File Format"** - What format is your INPUT file stored in?
- Default: "Auto-detect"
- Options: Serpentine, Row-major, Column-major, Column-serpentine
- Auto-detection analyzes your file and selects the best match

**"File Data-In"** - Where does data start in your INPUT file?
- Default: "Auto-detect"  
- Options: Left Top, Left Bottom, Right Top, Right Bottom
- Auto-detection identifies the starting corner

### **Target Wiring Dropdowns (Preview Tab):**

**"Wiring"** - How is your HARDWARE wired?
- Options: Row-major, Serpentine, Column-major, Column-serpentine
- This is your physical LED panel's wiring

**"Data In"** - Where does your HARDWARE strip start?
- Options: Left Top, Left Bottom, Right Top, Right Bottom
- This is your physical LED strip's first pixel location

### **If Preview Looks Wrong:**
1. Try different **File Format** options manually
2. Try different **File Data-In** options manually
3. Find the combination where preview looks correct
4. That's your file's actual format!

### **If Hardware Looks Wrong (but preview is correct):**
1. Try different **Wiring** options for target
2. Try different **Data In** options for target
3. Use **Flip X** or **Flip Y** in Flash tab if needed
4. Use the diagnostic pattern to identify your panel's wiring

---

## 🧪 **Testing with Diagnostic Pattern**

### **Step 1: Generate Diagnostic Pattern**
```bash
python create_diagnostic_pattern.py
```
This creates `diagnostic_12x6.bin` with corner markers:
- **Red** = Top-Left
- **Green** = Top-Right
- **Blue** = Bottom-Left
- **Yellow** = Bottom-Right

### **Step 2: Load in App**
1. Load `diagnostic_12x6.bin`
2. Set File Format: Row-major
3. Set File Data-In: Left Top
4. Preview should show: Red (TL), Green (TR), Blue (BL), Yellow (BR)

### **Step 3: Flash to Hardware**
1. Try different Target Wiring modes
2. Flash each one
3. Check where colors appear on your physical panel
4. The corner colors tell you your panel's exact wiring

### **Example:**
- If hardware shows: **Blue** at top-left → Your panel starts at Bottom-Left
- If hardware shows: **Red** at top-left → Your panel starts at Top-Left ✓
- If odd rows are backwards → Your panel is Serpentine wiring

---

## ✅ **Verification Tests**

Run these to verify everything works:

```bash
# Test all 16 wiring combinations
python verify_all_16_wiring_combinations.py

# Test round-trip conversion
python verify_hardware_to_design.py

# Test speed/brightness don't affect pixel order
python verify_speed_brightness_pixel_order.py

# Test brightness options
python test_brightness_options.py
```

**All should PASS** ✓

---

## 📊 **What's Been Fixed**

### **Root Causes Identified:**
1. ❌ Broken auto-detection (always returned True)
2. ❌ Missing Frame import (preview failed)
3. ❌ Incomplete reverse mapping (8 of 16 modes broken)
4. ❌ Disabled conversion logic (no mapping applied)
5. ❌ Silent error handling (user never saw errors)

### **Solutions Implemented:**
1. ✅ File format auto-detection with user override
2. ✅ Added Frame import to preview_tab.py
3. ✅ Complete Row-major and Column-major support
4. ✅ Re-enabled conversion pipeline with comprehensive logging
5. ✅ Error dialogs shown to user

### **Architecture:**
```
File (any format) 
    ↓ Auto-detect or user-specified
Preview (unwrapped to design order)
    ↓ Convert: File → Design → Target
Flash (target hardware order)
    ↓ Optional: Flip X/Y corrections
Hardware (matches preview perfectly)
```

---

## 🎯 **Known Limitations**

1. **Auto-detection is heuristic** - not 100% accurate for all patterns
   - Works best with clear serpentine patterns
   - User should verify results
   - Manual override available

2. **Preview shows design order only** - can't preview in hardware wiring format
   - Preview is always unwrapped (all rows L→R)
   - Hardware output respects target wiring

3. **File format must be consistent** - all frames must have same format
   - Cannot mix different wiring modes in one file

---

## 📞 **Troubleshooting**

### **Preview shows flipped rows:**
→ Change "File Format" or "File Data-In" until preview looks correct

### **Hardware shows flipped rows (but preview is correct):**
→ Change "Wiring" or "Data In" (target hardware settings)  
→ OR enable Flip X/Flip Y in Flash tab

### **All settings tried, still flipping:**
→ Use `diagnostic_12x6.bin` to identify exact wiring  
→ Check corner colors on hardware vs preview  
→ Your panel may have non-standard wiring

### **Preview is blank:**
→ Check console for error messages  
→ File format may be unsupported  
→ Try different file format settings

### **Settings reset when changing one:**
→ This should be fixed in this version  
→ If still happening, report the issue

---

## 🔧 **System Requirements**

- Python 3.8 or higher
- Windows, Linux, or macOS
- PyQt5 (installed by install_simple.bat)
- Serial port access for flashing

---

## 📈 **Version History**

**v1.0 (2025-11-07) - Universal Wiring Fix Edition:**
- Added file format auto-detection
- Added universal wiring support (all 16 combinations)
- Fixed preview flipping issues
- Added comprehensive logging
- Added Flip X/Y corrections
- Verified brightness options working
- All tests passing

---

## ✨ **Status: PRODUCTION READY**

This version has been:
- ✅ Fully tested with all 16 wiring combinations
- ✅ Verified with round-trip conversions
- ✅ Tested with speed and brightness controls
- ✅ Documented comprehensively
- ✅ Ready for distribution

---

## 📧 **Support**

For issues or questions, check:
1. `TROUBLESHOOTING_GUIDE.md`
2. `COMPLETE_FLOW_DOCUMENTATION.md`
3. `DIAGNOSTIC_TOOLS_README.md`

---

**Enjoy your Upload Bridge with universal wiring support!** 🎉


















