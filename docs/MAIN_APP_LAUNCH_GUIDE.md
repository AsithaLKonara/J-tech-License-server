# Main Application Launch Guide

**Application**: Upload Bridge  
**Launch Command**: `python main.py`

---

## Application Status

**Status**: ⏳ **Running**

The main Upload Bridge application has been launched. You should see the main window open.

---

## What to Expect

### Main Window
- **Title**: "Upload Bridge" (or similar)
- **Tabs**: Multiple tabs including Design Tools Tab
- **Interface**: Full application interface

### Design Tools Tab
- **Location**: One of the tabs in the main window
- **Features**: All layer features available for testing

---

## Testing New Layer Features

Now that the main app is running, you can test the new layer features:

### 1. Automation Layer Creation
1. Go to **Design Tools Tab**
2. Create a new pattern (8x8 or larger)
3. Paint something on canvas
4. Go to **Automation Tab**
5. Add "Scroll Left" action to queue
6. Click "Process Queue"
7. Check **Layers Tab** for new "Auto: Scroll Left" layer

### 2. Layer Sync Warning
1. Create pattern and paint on layer
2. Apply automation
3. Check if sync warning banner appears
4. Click "Sync Layers" button if warning appears
5. Verify warning disappears after sync

### 3. Brush Broadcast Feedback
1. Create pattern with 3+ frames
2. Paint different content on each frame
3. Enable "Apply brush strokes to all frames" checkbox
4. Verify warning dialog appears
5. Enable broadcast mode
6. Check timeline for frame highlighting
7. Paint on one frame, verify all frames update

### 4. Hidden Layer Prevention
1. Create pattern with multiple layers
2. Hide a layer (click eye icon)
3. Select the hidden layer
4. Try to paint on canvas
5. Verify dialog appears: "Cannot paint on hidden layer"

### 5. Copy Layer to Frames
1. Create pattern with 3+ frames
2. Add custom layer to frame 0
3. Paint something on this layer
4. Right-click layer in layer panel
5. Select "Copy Layer to Frame"
6. Choose target frames
7. Verify layer copied

### 6. Multiple Automation Layers
1. Create pattern
2. Apply first automation (scroll)
3. Apply second automation (rotate)
4. Apply third automation (mirror)
5. Check Layers tab for all automation layers

---

## Manual Testing Checklist

Use `docs/MANUAL_TEST_RESULTS.md` to record your test results:

- [ ] Scenario 1: Automation Layer Creation
- [ ] Scenario 2: Layer Sync Warning
- [ ] Scenario 3: Brush Broadcast Feedback
- [ ] Scenario 4: Hidden Layer Prevention
- [ ] Scenario 5: Copy Layer to Frames
- [ ] Scenario 6: Multiple Automation Layers
- [ ] Scenario 7: Edge Cases

---

## Helper Scripts

### Get Test Scenario Guide
```bash
python scripts/manual_test_helper.py --scenario 1
python scripts/manual_test_helper.py --scenario 2
# ... etc
```

### List All Scenarios
```bash
python scripts/manual_test_helper.py --list-scenarios
```

---

## Quick Reference

- **Main App**: Running (launched with `python main.py`)
- **Design Tools Tab**: Available for testing
- **Test Guide**: `docs/MANUAL_TEST_RESULTS.md`
- **Helper Script**: `scripts/manual_test_helper.py`

---

## Next Steps

1. **Navigate to Design Tools Tab**
2. **Follow test scenarios** from `docs/MANUAL_TEST_RESULTS.md`
3. **Record results** as you test
4. **Document any issues** in `docs/BUG_REPORT.md`

---

**Application Status**: ✅ Running  
**Ready for Testing**: ✅ Yes








