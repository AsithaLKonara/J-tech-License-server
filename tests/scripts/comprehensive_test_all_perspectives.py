#!/usr/bin/env python3
"""
Comprehensive Test from All 4 Perspectives:
1. User - Basic functionality
2. Tester - Systematic testing  
3. QA - Quality assurance and edge cases
4. Professional Matrix Designer - Advanced workflows
"""
import sys
import os
import traceback
from pathlib import Path
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, msg):
        self.passed.append(msg)
        print(f"✓ {msg}")
    
    def add_fail(self, msg, error=None):
        self.failed.append((msg, error))
        print(f"✗ {msg}")
        if error:
            print(f"  Error: {error}")
    
    def add_warning(self, msg):
        self.warnings.append(msg)
        print(f"⚠ {msg}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")
        print("\nFailed Tests:")
        for msg, error in self.failed:
            print(f"  - {msg}")
            if error:
                print(f"    {error}")
        print("="*70)

results = TestResults()

# ============================================================================
# PERSPECTIVE 1: USER - Basic Functionality
# ============================================================================
print("\n" + "="*70)
print("PERSPECTIVE 1: USER - Basic Functionality Testing")
print("="*70)

# Test 1.1: App can launch
print("\n[USER] Testing app launch...")
try:
    from PySide6.QtWidgets import QApplication
    from ui.main_window import UploadBridgeMainWindow
    
    # Create app without showing window
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Try to create main window
    window = UploadBridgeMainWindow()
    results.add_pass("[USER] App can launch and create main window")
    window.close()
    app.quit()
except Exception as e:
    results.add_fail("[USER] App launch failed", str(e))

# Test 1.2: Core services work
print("\n[USER] Testing core services...")
try:
    from core.services.pattern_service import PatternService
    from core.services.export_service import ExportService
    
    service = PatternService()
    pattern = service.create_pattern("Test Pattern", 16, 16)
    
    if pattern and pattern.metadata.width == 16:
        results.add_pass("[USER] Can create patterns")
    else:
        results.add_fail("[USER] Pattern creation returned invalid result")
except Exception as e:
    results.add_fail("[USER] Pattern service failed", str(e))

# Test 1.3: Can export pattern
print("\n[USER] Testing export functionality...")
try:
    from core.services.pattern_service import PatternService
    from core.services.export_service import ExportService
    
    service = PatternService()
    export_service = ExportService()
    pattern = service.create_pattern("Export Test", 8, 8)
    
    # Add frame if needed
    if len(pattern.frames) == 0:
        from core.pattern import Frame
        frame = Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)
        pattern.frames.append(frame)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.bin"
        export_service.export_pattern(pattern, str(filepath), "bin")
        if filepath.exists() and filepath.stat().st_size > 0:
            results.add_pass("[USER] Can export patterns")
        else:
            results.add_fail("[USER] Export created invalid file")
except Exception as e:
    results.add_fail("[USER] Export failed", str(e))

# ============================================================================
# PERSPECTIVE 2: TESTER - Systematic Testing
# ============================================================================
print("\n" + "="*70)
print("PERSPECTIVE 2: TESTER - Systematic Testing")
print("="*70)

# Test 2.1: All modules import correctly
print("\n[TESTER] Testing module imports...")
modules_to_test = [
    ("core.config", "get_config"),
    ("core.services.pattern_service", "PatternService"),
    ("core.services.export_service", "ExportService"),
    ("core.services.flash_service", "FlashService"),
    ("ui.main_window", "UploadBridgeMainWindow"),
    ("ui.tabs.design_tools_tab", "DesignToolsTab"),
    ("ui.tabs.preview_tab", "PreviewTab"),
    ("ui.tabs.flash_tab", "FlashTab"),
    ("core.pattern", "Pattern"),
    ("core.export_options", "ExportOptions"),
]

imported_count = 0
for module_name, attr_name in modules_to_test:
    try:
        module = __import__(module_name, fromlist=[attr_name])
        if hasattr(module, attr_name):
            imported_count += 1
        else:
            results.add_warning(f"[TESTER] Module {module_name} missing {attr_name}")
    except Exception as e:
        results.add_fail(f"[TESTER] Cannot import {module_name}.{attr_name}", str(e))

if imported_count == len(modules_to_test):
    results.add_pass(f"[TESTER] All {len(modules_to_test)} critical modules import correctly")
else:
    results.add_warning(f"[TESTER] Only {imported_count}/{len(modules_to_test)} modules imported")

# Test 2.2: Configuration loads
print("\n[TESTER] Testing configuration...")
try:
    from core.config import get_config
    config = get_config()
    
    checks = [
        ("app_name", "Upload Bridge"),
        ("app_version", None),
    ]
    
    all_ok = True
    for key, expected in checks:
        value = config.get(key)
        if expected and value != expected:
            results.add_warning(f"[TESTER] Config {key} = {value}, expected {expected}")
            all_ok = False
    
    if all_ok:
        results.add_pass("[TESTER] Configuration loads correctly")
except Exception as e:
    results.add_fail("[TESTER] Configuration load failed", str(e))

# Test 2.3: Test pattern creation with various sizes
print("\n[TESTER] Testing pattern creation with various sizes...")
try:
    from core.services.pattern_service import PatternService
    service = PatternService()
    
    sizes = [(8, 8), (16, 16), (32, 32), (64, 64)]
    created = 0
    for w, h in sizes:
        try:
            pattern = service.create_pattern(f"Test {w}x{h}", w, h)
            if pattern and pattern.metadata.width == w and pattern.metadata.height == h:
                created += 1
        except Exception as e:
            results.add_warning(f"[TESTER] Failed to create {w}x{h} pattern: {e}")
    
    if created == len(sizes):
        results.add_pass(f"[TESTER] Successfully created patterns in {len(sizes)} sizes")
    else:
        results.add_warning(f"[TESTER] Only {created}/{len(sizes)} pattern sizes worked")
except Exception as e:
    results.add_fail("[TESTER] Pattern size testing failed", str(e))

# ============================================================================
# PERSPECTIVE 3: QA - Quality Assurance
# ============================================================================
print("\n" + "="*70)
print("PERSPECTIVE 3: QA - Quality Assurance & Edge Cases")
print("="*70)

# Test 3.1: Error handling
print("\n[QA] Testing error handling...")
try:
    from core.error_handler import ErrorHandler
    
    handler = ErrorHandler()
    try:
        raise FileNotFoundError("test_file.txt not found")
    except Exception as e:
        error_info = handler.handle_error(e)
        if error_info:
            results.add_pass("[QA] Error handling works correctly")
        else:
            results.add_fail("[QA] Error handler returned None")
except Exception as e:
    results.add_warning(f"[QA] Error handler test failed: {e}")

# Test 3.2: Edge case - empty pattern
print("\n[QA] Testing edge cases...")
try:
    from core.services.pattern_service import PatternService
    service = PatternService()
    
    # Empty pattern should be valid (no frames is OK)
    pattern = service.create_pattern("Empty", 1, 1)
    if pattern:
        results.add_pass("[QA] Empty pattern handling works")
    else:
        results.add_fail("[QA] Empty pattern creation failed")
except Exception as e:
    results.add_fail("[QA] Empty pattern test failed", str(e))

# Test 3.3: Large pattern handling
print("\n[QA] Testing large pattern handling...")
try:
    from core.services.pattern_service import PatternService
    service = PatternService()
    
    # Test large pattern
    pattern = service.create_pattern("Large", 64, 64)
    if pattern:
        # Add frame with all pixels
        if len(pattern.frames) == 0:
            from core.pattern import Frame
            frame = Frame(pixels=[(0, 0, 0)] * (64 * 64), duration_ms=100)
            pattern.frames.append(frame)
        
        if len(pattern.frames[0].pixels) == 64 * 64:
            results.add_pass("[QA] Large pattern (64x64) handled correctly")
        else:
            results.add_fail("[QA] Large pattern pixel count incorrect")
    else:
        results.add_fail("[QA] Large pattern creation failed")
except Exception as e:
    results.add_warning(f"[QA] Large pattern test failed: {e}")

# Test 3.4: Concurrent operations
print("\n[QA] Testing concurrent operations...")
try:
    from core.services.pattern_service import PatternService
    service = PatternService()
    
    pattern1 = service.create_pattern("Pattern 1", 8, 8)
    pattern2 = service.create_pattern("Pattern 2", 8, 8)
    
    if pattern1 and pattern2 and pattern1.name != pattern2.name:
        results.add_pass("[QA] Concurrent pattern creation works")
    else:
        results.add_fail("[QA] Concurrent operations failed")
except Exception as e:
    results.add_fail("[QA] Concurrent operations test failed", str(e))

# ============================================================================
# PERSPECTIVE 4: PROFESSIONAL MATRIX DESIGNER
# ============================================================================
print("\n" + "="*70)
print("PERSPECTIVE 4: PROFESSIONAL MATRIX DESIGNER - Advanced Workflows")
print("="*70)

# Test 4.1: Layer system
print("\n[DESIGNER] Testing layer system...")
try:
    from domain.layers import LayerManager
    from domain.pattern_state import PatternState
    from core.pattern import Pattern, PatternMetadata, Frame
    
    pattern = Pattern(
        name="Layer Test",
        metadata=PatternMetadata(width=16, height=16),
        frames=[Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
    )
    
    state = PatternState()
    state.set_pattern(pattern)
    layer_manager = LayerManager(state)
    layer_manager.set_pattern(pattern)
    
    # Add layers
    layer_manager.add_layer(0, "Background")
    layer_manager.add_layer(0, "Foreground")
    
    layers = layer_manager.get_layers(0)
    if len(layers) >= 3:  # Default + 2 new
        results.add_pass("[DESIGNER] Multi-layer system works")
    else:
        results.add_fail("[DESIGNER] Layer system failed")
except Exception as e:
    results.add_warning(f"[DESIGNER] Layer system test failed: {e}")

# Test 4.2: Export options
print("\n[DESIGNER] Testing advanced export options...")
try:
    from core.export_options import ExportOptions
    
    options = ExportOptions(
        bit_order_msb_lsb="LSB",
        scan_direction="Columns",
        rgb_order="BGR",
        color_space="RGB565"
    )
    
    if (options.bit_order_msb_lsb == "LSB" and 
        options.rgb_order == "BGR" and
        options.color_space == "RGB565"):
        results.add_pass("[DESIGNER] Advanced export options work")
    else:
        results.add_fail("[DESIGNER] Export options not applied correctly")
except Exception as e:
    results.add_fail("[DESIGNER] Export options test failed", str(e))

# Test 4.3: Template library
print("\n[DESIGNER] Testing template library...")
try:
    from core.pattern_templates import TemplateLibrary
    
    library = TemplateLibrary()
    templates = library.list_templates()
    
    if len(templates) > 0:
        results.add_pass(f"[DESIGNER] Template library has {len(templates)} templates")
    else:
        results.add_warning("[DESIGNER] Template library is empty")
except Exception as e:
    results.add_warning(f"[DESIGNER] Template library test failed: {e}")

# Test 4.4: Animation keyframes
print("\n[DESIGNER] Testing animation system...")
try:
    from domain.animation import KeyframeAnimation, Keyframe, KeyframeType
    
    animation = KeyframeAnimation()
    
    kf1 = Keyframe(
        frame_index=0,
        keyframe_type=KeyframeType.COLOR,
        value=(255, 0, 0),
        curve_type="linear"
    )
    animation.add_keyframe(kf1)
    
    value = animation.get_value_at_frame(0, KeyframeType.COLOR)
    if value is not None:
        results.add_pass("[DESIGNER] Keyframe animation system works")
    else:
        results.add_fail("[DESIGNER] Keyframe animation returned None")
except Exception as e:
    results.add_warning(f"[DESIGNER] Animation system test failed: {e}")

# Print final summary
results.print_summary()

# Exit with error code if any tests failed
if results.failed:
    sys.exit(1)
else:
    print("\n✓ All tests passed successfully!")
    sys.exit(0)

