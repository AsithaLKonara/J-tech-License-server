# User Acceptance Testing (UAT) Scenarios

## Overview
This document outlines test scenarios for User Acceptance Testing (UAT) of the Upload Bridge application. UAT will be conducted with 3-5 internal team members over 3-5 days.

## Test Environment
- **Platform**: Windows 10/11
- **Python Version**: 3.10, 3.11, or 3.12
- **Test Duration**: 3-5 days
- **Participants**: 3-5 internal team members

## Critical Workflow Test Scenarios

### Scenario 1: Pattern Creation and Editing
**Objective**: Verify users can create and edit patterns successfully

**Steps**:
1. Launch application
2. Create new pattern (12x6, 24 FPS)
3. Use pixel brush to draw on frame 1
4. Add 3 more frames
5. Draw different content on each frame
6. Save pattern to file
7. Close and reopen the saved pattern

**Expected Results**:
- ✅ Pattern creates successfully
- ✅ Drawing works correctly
- ✅ Frames can be added
- ✅ Pattern saves and loads correctly
- ✅ All frames preserved after save/load

**UX Verification**:
- ✅ Error messages are clear if save fails
- ✅ Unsaved changes warning appears when closing with unsaved work

---

### Scenario 2: File Loading with Error Handling
**Objective**: Verify error handling for invalid/corrupted files

**Steps**:
1. Try to open a non-existent file
2. Try to open a corrupted .dat file
3. Try to open an empty file
4. Try to open a valid pattern file
5. Try to open a file with unsupported format

**Expected Results**:
- ✅ Clear error messages for each failure type
- ✅ User-friendly error dialogs
- ✅ Application remains stable after errors
- ✅ Valid files load successfully

**UX Verification**:
- ✅ Error messages explain what went wrong
- ✅ Suggestions provided for fixing issues

---

### Scenario 3: Frame Management
**Objective**: Verify frame operations work correctly

**Steps**:
1. Create pattern with 5 frames
2. Try to delete the last frame (should show error)
3. Delete frame 3 (should succeed)
4. Duplicate frame 2
5. Move frame 1 to position 3
6. Change frame duration

**Expected Results**:
- ✅ Cannot delete last frame (error shown)
- ✅ Frames can be deleted when more than 1 exists
- ✅ Frames can be duplicated
- ✅ Frames can be reordered
- ✅ Frame duration changes apply

**UX Verification**:
- ✅ Clear error when trying to delete last frame
- ✅ Visual feedback for all operations

---

### Scenario 4: Brush Broadcast Warning
**Objective**: Verify broadcast mode warning works

**Steps**:
1. Create pattern with 3 frames
2. Draw different content on each frame
3. Enable "Apply brush strokes to all frames" checkbox
4. Observe warning dialog
5. Click "No" - verify checkbox stays unchecked
6. Enable again, click "Yes"
7. Draw on frame 1
8. Check frames 2 and 3

**Expected Results**:
- ✅ Warning dialog appears on first enable
- ✅ Dialog has clear warning message
- ✅ User can cancel enabling broadcast
- ✅ When enabled, drawing affects all frames
- ✅ Visual indicator (red border/banner) shows when active

**UX Verification**:
- ✅ Warning is clear and prominent
- ✅ Visual indicators are obvious

---

### Scenario 5: Undo/Redo Operations
**Objective**: Verify undo/redo works correctly

**Steps**:
1. Create pattern and draw on frame 1
2. Check undo button state (should be enabled)
3. Press Ctrl+Z to undo
4. Check redo button state (should be enabled)
5. Press Ctrl+Y to redo
6. Make multiple changes
7. Undo several times
8. Check tooltips show action count

**Expected Results**:
- ✅ Undo/redo buttons enable/disable correctly
- ✅ Tooltips show available actions
- ✅ Undo/redo works as expected
- ✅ Buttons disabled when nothing to undo/redo

**UX Verification**:
- ✅ Visual indication of undo/redo availability
- ✅ Tooltips are helpful

---

### Scenario 6: Unsaved Changes Warning
**Objective**: Verify unsaved changes are protected

**Steps**:
1. Create pattern and make changes
2. Try to load a new file
3. Observe unsaved changes dialog
4. Click "Save and Continue" - verify save dialog appears
5. Cancel save, try loading again
6. Click "Discard and Continue" - verify changes lost
7. Make changes again, try loading
8. Click "Cancel" - verify nothing happens

**Expected Results**:
- ✅ Warning appears when loading with unsaved changes
- ✅ Three options: Save, Discard, Cancel
- ✅ Save option opens save dialog
- ✅ Discard option discards changes
- ✅ Cancel option cancels load operation

**UX Verification**:
- ✅ Dialog is clear and easy to understand
- ✅ Options are well-labeled

---

### Scenario 7: Image Import
**Objective**: Verify image import with error handling

**Steps**:
1. Create pattern (12x6)
2. Import a PNG image
3. Try to import a corrupted image file
4. Try to import an unsupported format
5. Try to import a very large image
6. Import a GIF with multiple frames

**Expected Results**:
- ✅ Valid images import successfully
- ✅ Clear error messages for invalid files
- ✅ Specific errors for different failure types
- ✅ GIF imports create multiple frames
- ✅ Large file warning appears

**UX Verification**:
- ✅ Error messages are specific and helpful
- ✅ User knows what went wrong

---

### Scenario 8: Export Functionality
**Objective**: Verify export works and validates correctly

**Steps**:
1. Try to export with no pattern loaded
2. Create pattern with empty frames
3. Try to export (should show validation error)
4. Add content to frames
5. Export to .bin format
6. Export to .dat format
7. Export frame as image

**Expected Results**:
- ✅ Export disabled/validated when no pattern
- ✅ Validation errors are clear
- ✅ Export works for all formats
- ✅ Image export works correctly

**UX Verification**:
- ✅ Validation prevents invalid exports
- ✅ Error messages guide user

---

### Scenario 9: LMS Preview and Restore
**Objective**: Verify LMS preview restore functionality

**Steps**:
1. Create pattern with 5 frames
2. Build LMS sequence
3. Preview sequence
4. Observe preview changes pattern
5. Click "Restore Original" button
6. Verify original pattern restored
7. Preview again
8. Click "Apply Preview Changes"
9. Verify changes are permanent

**Expected Results**:
- ✅ Preview shows changes
- ✅ "Restore Original" button visible
- ✅ "Apply Changes" button visible
- ✅ Restore works correctly
- ✅ Apply makes changes permanent

**UX Verification**:
- ✅ Buttons are clearly visible
- ✅ Workflow is intuitive

---

### Scenario 10: Layer Operations
**Objective**: Verify layer management works

**Steps**:
1. Create pattern with multiple layers
2. Hide layer 2
3. Paint on hidden layer
4. Observe warning banner
5. Show layer 2
6. Verify painting is visible
7. Change active layer
8. Paint on different layers

**Expected Results**:
- ✅ Layers can be shown/hidden
- ✅ Warning appears when painting on hidden layer
- ✅ Warning banner is persistent
- ✅ Painting on visible layers works normally

**UX Verification**:
- ✅ Warning is clear and persistent
- ✅ User knows they're painting on hidden layer

---

## UAT Feedback Form

For each scenario, testers should provide:
1. **Pass/Fail**: Did the scenario work as expected?
2. **Issues Found**: Any bugs or problems encountered
3. **Usability Notes**: Was the workflow intuitive?
4. **Suggestions**: Any improvements recommended

## UAT Sign-off Criteria

- ✅ All critical scenarios pass
- ✅ No critical bugs found
- ✅ Usability feedback is positive
- ✅ Team members can complete tasks successfully

## UAT Schedule

**Day 1**: Preparation
- Distribute test scenarios
- Set up test environment
- Brief team on testing process

**Day 2-3**: Execution
- Testers execute scenarios
- Document findings
- Collect feedback

**Day 4**: Analysis
- Compile feedback
- Prioritize issues
- Create bug reports

**Day 5**: Follow-up (if needed)
- Retest fixes
- Final sign-off

