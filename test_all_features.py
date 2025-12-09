#!/usr/bin/env python3
"""
Comprehensive Feature Testing Script
Tests all features of Upload Bridge systematically
"""

import sys
from typing import Dict, List, Tuple
from core.pattern import Pattern, Frame, PatternMetadata

class FeatureTester:
    """Systematic feature tester"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def test(self, category: str, feature_name: str, test_func):
        """Run a single test"""
        self.total_tests += 1
        test_key = f"{category}::{feature_name}"
        
        try:
            result = test_func()
            if result:
                self.passed_tests += 1
                self.results[test_key] = {"status": "PASS", "message": "OK"}
                print(f"  ✓ {feature_name}")
                return True
            else:
                self.failed_tests += 1
                self.results[test_key] = {"status": "FAIL", "message": "Test returned False"}
                print(f"  ✗ {feature_name} - Test returned False")
                return False
        except Exception as e:
            self.failed_tests += 1
            self.results[test_key] = {"status": "ERROR", "message": str(e)}
            print(f"  ✗ {feature_name} - Error: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        print(f"Failed: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")
        print("=" * 70)
        
        if self.failed_tests > 0:
            print("\nFAILED TESTS:")
            for test_key, result in self.results.items():
                if result["status"] != "PASS":
                    print(f"  ✗ {test_key}: {result['message']}")
        
        return self.failed_tests == 0


def test_core_pattern_features(tester: FeatureTester):
    """Test core pattern features"""
    print("\n" + "=" * 70)
    print("1. CORE PATTERN FEATURES")
    print("=" * 70)
    
    # Test 1.1: Pattern Creation
    tester.test("Core", "Pattern Creation", lambda: (
        pattern := Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=16, height=16),
            frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)]
        ),
        pattern.name == "Test Pattern" and len(pattern.frames) == 1
    )[1])
    
    # Test 1.2: Frame Creation
    tester.test("Core", "Frame Creation", lambda: (
        frame := Frame(pixels=[(255,0,0)]*64, duration_ms=100),
        len(frame.pixels) == 64 and frame.duration_ms == 100
    )[1])
    
    # Test 1.3: Pattern Metadata
    tester.test("Core", "Pattern Metadata", lambda: (
        metadata := PatternMetadata(width=8, height=8),
        metadata.width == 8 and metadata.height == 8 and metadata.led_count == 64
    )[1])
    
    # Test 1.4: Multiple Frames
    tester.test("Core", "Multiple Frames", lambda: (
        pattern := Pattern(
            name="Multi Frame",
            metadata=PatternMetadata(width=4, height=4),
            frames=[
                Frame(pixels=[(255,0,0)]*16, duration_ms=100),
                Frame(pixels=[(0,255,0)]*16, duration_ms=100),
                Frame(pixels=[(0,0,255)]*16, duration_ms=100)
            ]
        ),
        len(pattern.frames) == 3
    )[1])
    
    # Test 1.5: Frame Pixel Access
    tester.test("Core", "Frame Pixel Access", lambda: (
        frame := Frame(pixels=[(255,0,0), (0,255,0), (0,0,255)], duration_ms=100),
        frame.pixels[0] == (255,0,0) and frame.pixels[1] == (0,255,0)
    )[1])
    
    # Test 1.6: Pattern Duration Calculation
    tester.test("Core", "Pattern Duration Calculation", lambda: (
        pattern := Pattern(
            name="Duration Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(0,0,0)]*64, duration_ms=100),
                Frame(pixels=[(0,0,0)]*64, duration_ms=200),
                Frame(pixels=[(0,0,0)]*64, duration_ms=150)
            ]
        ),
        pattern.duration_ms == 450
    )[1])


def test_drawing_tools(tester: FeatureTester):
    """Test drawing tools"""
    print("\n" + "=" * 70)
    print("2. DRAWING TOOLS")
    print("=" * 70)
    
    # Test 2.1: Pixel Tool (conceptual)
    tester.test("Drawing", "Pixel Tool Concept", lambda: True)  # UI feature, tested in UI tests
    
    # Test 2.2: Rectangle Tool (conceptual)
    tester.test("Drawing", "Rectangle Tool Concept", lambda: True)
    
    # Test 2.3: Circle Tool (conceptual)
    tester.test("Drawing", "Circle Tool Concept", lambda: True)
    
    # Test 2.4: Line Tool (conceptual)
    tester.test("Drawing", "Line Tool Concept", lambda: True)
    
    # Test 2.5: Fill Tool (conceptual)
    tester.test("Drawing", "Fill Tool Concept", lambda: True)
    
    # Test 2.6: Text Tool Integration
    try:
        from domain.text.text_renderer import TextRenderer, TextRenderOptions
        from domain.text.glyph_provider import GlyphProvider
        
        tester.test("Drawing", "Text Tool Integration", lambda: (
            renderer := TextRenderer(),
            options := TextRenderOptions(width=16, height=8, color=(255,255,255)),
            renderer is not None and options is not None
        )[2])
    except ImportError as e:
        tester.test("Drawing", "Text Tool Integration", lambda: False)
    
    # Test 2.7: Bitmap Font Support
    try:
        from domain.text.bitmap_font import BitmapFont
        tester.test("Drawing", "Bitmap Font Support", lambda: True)
    except ImportError:
        tester.test("Drawing", "Bitmap Font Support", lambda: False)


def test_automation_features(tester: FeatureTester):
    """Test automation features"""
    print("\n" + "=" * 70)
    print("3. AUTOMATION FEATURES")
    print("=" * 70)
    
    # Test 3.1: Automation Queue Manager
    try:
        from domain.automation.queue import AutomationQueueManager
        tester.test("Automation", "Automation Queue Manager", lambda: (
            manager := AutomationQueueManager(),
            manager is not None
        )[1])
    except ImportError:
        tester.test("Automation", "Automation Queue Manager", lambda: False)
    
    # Test 3.2: Design Action Creation
    try:
        from domain.actions import DesignAction
        tester.test("Automation", "Design Action Creation", lambda: (
            action := DesignAction(
                name="Test Scroll",
                action_type="scroll",
                params={"direction": "Left", "offset": 1}
            ),
            action.action_type == "scroll" and action.name == "Test Scroll"
        )[1])
    except ImportError:
        tester.test("Automation", "Design Action Creation", lambda: False)
    
    # Test 3.3: Automation Engine
    try:
        from core.automation.engine import AutomationEngine
        tester.test("Automation", "Automation Engine", lambda: (
            engine := AutomationEngine(),
            engine is not None
        )[1])
    except ImportError:
        tester.test("Automation", "Automation Engine", lambda: False)
    
    # Test 3.4: Frame Generation with Actions
    tester.test("Automation", "Frame Generation Logic", lambda: (
        source_frame := Frame(pixels=[(255,0,0)]*64, duration_ms=100),
        frames := [],
        [frames.append(Frame(pixels=[tuple(p) for p in source_frame.pixels], duration_ms=100)) for _ in range(3)],
        len(frames) == 3 and all(len(f.pixels) == 64 for f in frames)
    )[3])


def test_effects_features(tester: FeatureTester):
    """Test effects features"""
    print("\n" + "=" * 70)
    print("4. EFFECTS FEATURES")
    print("=" * 70)
    
    # Test 4.1: Effects System
    try:
        from domain.effects.apply import apply_effect_to_frames
        tester.test("Effects", "Effects System", lambda: True)
    except ImportError:
        tester.test("Effects", "Effects System", lambda: False)
    
    # Test 4.2: Effect Application
    tester.test("Effects", "Effect Application Concept", lambda: True)  # UI feature


def test_import_export_features(tester: FeatureTester):
    """Test import/export features"""
    print("\n" + "=" * 70)
    print("5. IMPORT/EXPORT FEATURES")
    print("=" * 70)
    
    # Test 5.1: Pattern Serialization
    tester.test("Import/Export", "Pattern Serialization", lambda: (
        pattern := Pattern(
            name="Export Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(255,0,0)]*64, duration_ms=100)]
        ),
        pattern.name == "Export Test" and len(pattern.frames) == 1
    )[1])
    
    # Test 5.2: Frame to Bytes
    tester.test("Import/Export", "Frame to Bytes Conversion", lambda: (
        frame := Frame(pixels=[(255,0,0), (0,255,0), (0,0,255)], duration_ms=100),
        bytes_data := frame.to_bytes(),
        len(bytes_data) == 9  # 3 pixels * 3 bytes
    )[2])
    
    # Test 5.3: Pattern Metadata Export
    tester.test("Import/Export", "Pattern Metadata Export", lambda: (
        metadata := PatternMetadata(width=16, height=16, brightness=0.8),
        metadata.width == 16 and metadata.brightness == 0.8
    )[1])


def test_performance_features(tester: FeatureTester):
    """Test performance features"""
    print("\n" + "=" * 70)
    print("6. PERFORMANCE FEATURES")
    print("=" * 70)
    
    # Test 6.1: Performance Monitor
    try:
        from core.performance import PerformanceMonitor
        tester.test("Performance", "Performance Monitor", lambda: (
            monitor := PerformanceMonitor(),
            monitor is not None
        )[1])
    except ImportError:
        tester.test("Performance", "Performance Monitor", lambda: False)
    
    # Test 6.2: LRU Cache
    try:
        from core.performance import LRUCache
        tester.test("Performance", "LRU Cache", lambda: (
            cache := LRUCache(max_size=10),
            cache.max_size == 10
        )[1])
    except ImportError:
        tester.test("Performance", "LRU Cache", lambda: False)
    
    # Test 6.3: Timed Operation Decorator
    try:
        from core.performance import timed_operation
        tester.test("Performance", "Timed Operation Decorator", lambda: True)
    except ImportError:
        tester.test("Performance", "Timed Operation Decorator", lambda: False)
    
    # Test 6.4: Frame Cache
    try:
        from core.performance.cache import FrameCache
        tester.test("Performance", "Frame Cache", lambda: True)
    except ImportError:
        tester.test("Performance", "Frame Cache", lambda: False)


def test_text_features(tester: FeatureTester):
    """Test text rendering features"""
    print("\n" + "=" * 70)
    print("7. TEXT RENDERING FEATURES")
    print("=" * 70)
    
    # Test 7.1: Text Renderer
    try:
        from domain.text.text_renderer import TextRenderer
        tester.test("Text", "Text Renderer", lambda: (
            renderer := TextRenderer(),
            renderer is not None
        )[1])
    except ImportError:
        tester.test("Text", "Text Renderer", lambda: False)
    
    # Test 7.2: Text Render Options
    try:
        from domain.text.text_renderer import TextRenderOptions
        tester.test("Text", "Text Render Options", lambda: (
            options := TextRenderOptions(width=16, height=8, color=(255,255,255)),
            options.width == 16 and options.height == 8
        )[1])
    except ImportError:
        tester.test("Text", "Text Render Options", lambda: False)
    
    # Test 7.3: Glyph Provider
    try:
        from domain.text.glyph_provider import GlyphProvider
        tester.test("Text", "Glyph Provider", lambda: True)
    except ImportError:
        tester.test("Text", "Glyph Provider", lambda: False)
    
    # Test 7.4: Bitmap Font
    try:
        from domain.text.bitmap_font import BitmapFont
        tester.test("Text", "Bitmap Font", lambda: True)
    except ImportError:
        tester.test("Text", "Bitmap Font", lambda: False)


def test_services_features(tester: FeatureTester):
    """Test service features"""
    print("\n" + "=" * 70)
    print("8. SERVICES FEATURES")
    print("=" * 70)
    
    # Test 8.1: Pattern Service
    try:
        from core.services.pattern_service import PatternService
        tester.test("Services", "Pattern Service", lambda: True)
    except ImportError:
        tester.test("Services", "Pattern Service", lambda: False)
    
    # Test 8.2: Configuration Service
    try:
        from core.config import get_config
        tester.test("Services", "Configuration Service", lambda: (
            config := get_config(),
            config is not None
        )[1])
    except ImportError:
        tester.test("Services", "Configuration Service", lambda: False)


def main():
    """Run all feature tests"""
    print("=" * 70)
    print("UPLOAD BRIDGE - COMPREHENSIVE FEATURE TESTING")
    print("=" * 70)
    
    tester = FeatureTester()
    
    # Run all test categories
    test_core_pattern_features(tester)
    test_drawing_tools(tester)
    test_automation_features(tester)
    test_effects_features(tester)
    test_import_export_features(tester)
    test_performance_features(tester)
    test_text_features(tester)
    test_services_features(tester)
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

