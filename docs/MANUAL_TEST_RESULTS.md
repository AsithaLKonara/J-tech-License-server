# Manual Test Results - Layer Features

**Date**: [Date]  
**Tester**: [Name]  
**Application Version**: [Version]

---

## Test Execution Summary

| Scenario | Status | Notes | Time |
|----------|--------|-------|------|
| 1. Automation Layer Creation | ⏳ Pending | | |
| 2. Layer Sync Warning | ⏳ Pending | | |
| 3. Brush Broadcast Feedback | ⏳ Pending | | |
| 4. Hidden Layer Prevention | ⏳ Pending | | |
| 5. Copy Layer to Frames | ⏳ Pending | | |
| 6. Multiple Automation Layers | ⏳ Pending | | |
| 7. Edge Cases | ⏳ Pending | | |

---

## Scenario 1: Automation Layer Creation

**Status**: ⏳ Pending  
**Date**: [Date]  
**Tester**: [Name]

### Steps Executed:
- [ ] Launched application: `python main.py`
- [ ] Created new pattern (8x8 or larger)
- [ ] Painted something on canvas
- [ ] Went to Automation tab
- [ ] Added "Scroll Left" action to queue
- [ ] Clicked "Process Queue"
- [ ] Checked Layers tab for new "Auto: Scroll Left" layer
- [ ] Verified original layer still exists
- [ ] Toggled automation layer visibility
- [ ] Verified frame shows composite correctly

### Results:
- **New "Auto:" layer created**: [ ] Yes [ ] No
- **Original layer preserved**: [ ] Yes [ ] No
- **Composite works correctly**: [ ] Yes [ ] No

### Issues Found:
[Describe any issues encountered]

### Screenshots:
[Add screenshots if helpful]

---

## Scenario 2: Layer Sync Warning

**Status**: ⏳ Pending  
**Date**: [Date]  
**Tester**: [Name]

### Steps Executed:
- [ ] Created pattern and painted on layer
- [ ] Applied automation (creates new layer)
- [ ] Checked if sync warning banner appears
- [ ] Verified warning message: "⚠️ Layers are out of sync with frame X"
- [ ] Clicked "Sync Layers" button
- [ ] Verified confirmation dialog appears
- [ ] Confirmed sync action
- [ ] Verified warning disappears after sync
- [ ] Verified layers are now in sync

### Results:
- **Warning appears**: [ ] Yes [ ] No
- **Sync button works**: [ ] Yes [ ] No
- **Warning clears after sync**: [ ] Yes [ ] No

### Issues Found:
[Describe any issues encountered]

### Screenshots:
[Add screenshots if helpful]

---

## Scenario 3: Brush Broadcast Feedback

**Status**: ⏳ Pending  
**Date**: [Date]  
**Tester**: [Name]

### Steps Executed:
- [ ] Created pattern with 3+ frames
- [ ] Painted different content on each frame
- [ ] Enabled "Apply brush strokes to all frames" checkbox
- [ ] Verified warning dialog appears on first enable
- [ ] Tested cancel (checkbox stays unchecked)
- [ ] Enabled broadcast mode (clicked "Yes")
- [ ] Verified all frames highlighted in timeline (yellow/orange)
- [ ] Verified checkbox shows red border and warning icon
- [ ] Verified warning banner appears at top
- [ ] Painted on one frame, verified all frames update

### Results:
- **Warning dialog appears**: [ ] Yes [ ] No
- **Frame highlighting works**: [ ] Yes [ ] No
- **Visual indicators present**: [ ] Yes [ ] No
- **Broadcast works correctly**: [ ] Yes [ ] No

### Issues Found:
[Describe any issues encountered]

### Screenshots:
[Add screenshots if helpful]

---

## Scenario 4: Hidden Layer Prevention

**Status**: ⏳ Pending  
**Date**: [Date]  
**Tester**: [Name]

### Steps Executed:
- [ ] Created pattern with multiple layers
- [ ] Hid a layer (clicked eye icon)
- [ ] Selected the hidden layer
- [ ] Tried to paint on canvas
- [ ] Verified dialog: "Cannot paint on hidden layer"
- [ ] Made layer visible
- [ ] Verified painting works on visible layer

### Results:
- **Hidden layer painting blocked**: [ ] Yes [ ] No
- **Clear error message**: [ ] Yes [ ] No
- **Works when visible**: [ ] Yes [ ] No

### Issues Found:
[Describe any issues encountered]

### Screenshots:
[Add screenshots if helpful]

---

## Scenario 5: Copy Layer to Frames

**Status**: ⏳ Pending  
**Date**: [Date]  
**Tester**: [Name]

### Steps Executed:
- [ ] Created pattern with 3+ frames
- [ ] Added custom layer to frame 0
- [ ] Painted something on this layer
- [ ] Right-clicked layer in layer panel
- [ ] Verified "Copy Layer to Frame" option exists in context menu
- [ ] Selected option, chose target frames (1, 2)
- [ ] Clicked "Copy"
- [ ] Verified layer copied to selected frames
- [ ] Verified original layer unchanged
- [ ] Verified copied layers have same pixels

### Results:
- **Context menu option exists**: [ ] Yes [ ] No
- **Copy works correctly**: [ ] Yes [ ] No
- **Pixels match**: [ ] Yes [ ] No
- **Original preserved**: [ ] Yes [ ] No

### Issues Found:
[Describe any issues encountered]

### Screenshots:
[Add screenshots if helpful]

---

## Scenario 6: Multiple Automation Layers

**Status**: ⏳ Pending  
**Date**: [Date]  
**Tester**: [Name]

### Steps Executed:
- [ ] Created pattern
- [ ] Applied first automation (scroll)
- [ ] Applied second automation (rotate)
- [ ] Applied third automation (mirror)
- [ ] Verified all automation layers exist in Layers tab
- [ ] Verified can toggle each independently
- [ ] Verified composite shows all layers correctly

### Results:
- **Multiple automation layers coexist**: [ ] Yes [ ] No
- **Independent toggling works**: [ ] Yes [ ] No
- **Correct composite**: [ ] Yes [ ] No

### Issues Found:
[Describe any issues encountered]

### Screenshots:
[Add screenshots if helpful]

---

## Scenario 7: Edge Cases

**Status**: ⏳ Pending  
**Date**: [Date]  
**Tester**: [Name]

### Steps Executed:
- [ ] Tested with single frame pattern
- [ ] Tested with single layer
- [ ] Tested with many layers (10+)
- [ ] Tested with large pattern (64x64)
- [ ] Tested undo/redo after automation
- [ ] Tested save/load with automation layers
- [ ] Tested copy layer to same frame (should skip)

### Results:
- **Single frame pattern**: [ ] Pass [ ] Fail
- **Single layer**: [ ] Pass [ ] Fail
- **Many layers (10+)**: [ ] Pass [ ] Fail
- **Large pattern (64x64)**: [ ] Pass [ ] Fail
- **Undo/redo after automation**: [ ] Pass [ ] Fail
- **Save/load with automation layers**: [ ] Pass [ ] Fail
- **Copy layer to same frame**: [ ] Pass [ ] Fail

### Issues Found:
[Describe any issues encountered]

### Screenshots:
[Add screenshots if helpful]

---

## Overall Test Summary

**Total Scenarios**: 7  
**Passed**: 0  
**Failed**: 0  
**Pending**: 7

### Critical Issues:
[List any critical issues found]

### High Priority Issues:
[List any high priority issues found]

### Medium Priority Issues:
[List any medium priority issues found]

### Low Priority Issues:
[List any low priority issues found]

### Recommendations:
[Any recommendations for improvements]

---

## Sign-off

**Tester**: _________________  
**Date**: _________________  
**Status**: [ ] Ready for Integration Testing [ ] Needs Bug Fixes

