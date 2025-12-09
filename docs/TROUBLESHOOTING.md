# Troubleshooting Guide - Layer Features

**Last Updated**: [Date]  
**Version**: [Version]

---

## Common Issues and Solutions

### Layer Sync Issues

#### Issue: Sync warning doesn't appear after automation

**Symptoms**:
- Applied automation but no sync warning banner appears
- Layers may be out of sync but no indication

**Possible Causes**:
1. Sync check not triggered after automation
2. Warning banner not visible
3. Layers actually in sync

**Solutions**:
1. Switch to a different frame and back to trigger sync check
2. Check if warning banner is visible (may be hidden)
3. Manually verify layers are out of sync by checking layer composite
4. Try applying another automation to trigger sync check

**Prevention**:
- Sync check should run automatically after automation
- Ensure `_update_layer_sync_warning()` is called after automation operations

---

#### Issue: Sync button doesn't work

**Symptoms**:
- Clicking "Sync Layers" button has no effect
- Warning banner doesn't disappear after sync

**Possible Causes**:
1. Confirmation dialog cancelled
2. Sync operation failed silently
3. UI not updating after sync

**Solutions**:
1. Check if confirmation dialog appears and click "Yes"
2. Verify active layer exists before syncing
3. Check console for error messages
4. Try switching frames to refresh UI

**Prevention**:
- Ensure sync operation completes successfully
- Update UI after sync operation

---

### Automation Layer Issues

#### Issue: Automation doesn't create new layer

**Symptoms**:
- Applied automation but no "Auto:" layer appears
- Frame pixels changed but no new layer

**Possible Causes**:
1. Automation not using new layer creation code path
2. Layer creation failed silently
3. Layer exists but not visible in layer panel

**Solutions**:
1. Check Layers tab for new layers
2. Verify automation completed successfully
3. Check console for error messages
4. Try a different automation type

**Prevention**:
- Ensure `_perform_action()` creates new layer
- Verify layer manager state after automation

---

#### Issue: Multiple automation layers not working correctly

**Symptoms**:
- Multiple automation layers don't composite correctly
- Toggling automation layers has unexpected results

**Possible Causes**:
1. Layer order incorrect
2. Composite calculation issue
3. Visibility state not preserved

**Solutions**:
1. Check layer order in Layers tab
2. Verify all layers are visible
3. Reorder layers if needed
4. Recalculate composite manually

**Prevention**:
- Ensure proper layer ordering
- Verify composite calculation handles all layers

---

### Broadcast Mode Issues

#### Issue: Frame highlighting doesn't appear

**Symptoms**:
- Enabled broadcast mode but frames not highlighted
- No visual feedback

**Possible Causes**:
1. Timeline widget doesn't support highlighting
2. Highlight signal not connected
3. Highlight color not visible

**Solutions**:
1. Check if timeline has `highlight_frames()` method
2. Verify signal connections in `_on_brush_broadcast_changed()`
3. Try different highlight color
4. Check if timeline is visible

**Prevention**:
- Ensure timeline widget supports highlighting
- Test highlight functionality during development

---

#### Issue: Broadcast mode affects wrong frames

**Symptoms**:
- Painting on one frame affects unexpected frames
- All frames not updating correctly

**Possible Causes**:
1. Frame selection incorrect
2. Broadcast logic error
3. Frame index mismatch

**Solutions**:
1. Verify current frame selection
2. Check broadcast logic in paint handlers
3. Verify frame indices are correct
4. Disable and re-enable broadcast mode

**Prevention**:
- Test broadcast with different frame counts
- Verify frame indices in broadcast operations

---

### Copy Layer Issues

#### Issue: Copy layer option not in context menu

**Symptoms**:
- Right-click layer but no "Copy Layer to Frame" option
- Context menu doesn't appear

**Possible Causes**:
1. Context menu not implemented
2. Menu option hidden
3. Layer panel not supporting context menu

**Solutions**:
1. Check if layer panel has context menu
2. Verify context menu implementation
3. Try different layer panel widget
4. Check if layer is selected

**Prevention**:
- Ensure context menu is properly implemented
- Test context menu during development

---

#### Issue: Copied layers don't match original

**Symptoms**:
- Copied layer has different pixels
- Layer properties not preserved

**Possible Causes**:
1. Copy operation incomplete
2. Pixels not copied correctly
3. Properties not preserved

**Solutions**:
1. Verify copy operation completes
2. Check pixel data matches
3. Verify layer properties (name, opacity, etc.)
4. Try copying again

**Prevention**:
- Ensure deep copy of pixel data
- Verify all properties are copied

---

### Hidden Layer Issues

#### Issue: Can still paint on hidden layer

**Symptoms**:
- Hidden layer but painting still works
- No error dialog appears

**Possible Causes**:
1. Hidden layer check not implemented
2. Check happens after paint
3. Layer visibility state incorrect

**Solutions**:
1. Verify layer is actually hidden
2. Check if hidden layer check is in paint handler
3. Ensure check happens before paint operation
4. Try hiding layer again

**Prevention**:
- Implement hidden layer check in paint handlers
- Verify layer visibility state before painting

---

#### Issue: Error dialog appears but painting still works

**Symptoms**:
- Error dialog appears but paint operation completes
- Dialog doesn't prevent painting

**Possible Causes**:
1. Dialog is informational only
2. Paint operation not cancelled
3. Dialog response not checked

**Solutions**:
1. Verify dialog prevents paint operation
2. Check if paint operation is cancelled on dialog
3. Ensure paint handler checks dialog result

**Prevention**:
- Implement proper paint cancellation
- Verify dialog prevents operation

---

## Performance Issues

### Issue: Slow performance with many layers

**Symptoms**:
- Application slows down with 10+ layers
- UI becomes unresponsive

**Solutions**:
1. Reduce number of layers
2. Use layer groups
3. Hide unused layers
4. Check for memory leaks
5. Optimize composite calculation

---

### Issue: Slow performance with large patterns

**Symptoms**:
- 64x64+ patterns are slow
- Operations take long time

**Solutions**:
1. Use batch updates
2. Enable dirty regions
3. Reduce frame count if possible
4. Check memory usage
5. Optimize rendering

---

## Getting Help

If you encounter issues not covered here:

1. **Check Console Logs**: Look for error messages in console
2. **Check Documentation**: See `docs/DESIGN_TOOLS_COMPLETE_FEATURES_GUIDE.md`
3. **Report Bug**: Use `docs/BUG_REPORT.md` template
4. **Check Known Issues**: See release notes for known issues

---

## Debugging Tips

### Enable Debug Logging
- Set environment variable: `DEBUG=1`
- Check console for detailed logs

### Verify State
- Check layer manager state
- Verify frame pixels vs layer composite
- Check signal connections

### Test Isolation
- Test features individually
- Use simple test patterns
- Verify with minimal setup

---

**Last Updated**: [Date]  
**Version**: [Version]
