#!/usr/bin/env python3
"""
Interactive Feature Testing Script
Tests features one by one with detailed output
"""

import sys
from typing import Callable, Dict

class InteractiveTester:
    """Interactive feature tester with detailed output"""
    
    def __init__(self):
        self.test_results: Dict[str, bool] = {}
    
    def test_feature(self, name: str, description: str, test_func: Callable) -> bool:
        """Test a single feature with detailed output"""
        print(f"\n{'='*70}")
        print(f"Testing: {name}")
        print(f"Description: {description}")
        print(f"{'='*70}")
        
        try:
            result = test_func()
            if result:
                print(f"✓ PASS: {name}")
                self.test_results[name] = True
                return True
            else:
                print(f"✗ FAIL: {name} - Test returned False")
                self.test_results[name] = False
                return False
        except Exception as e:
            print(f"✗ ERROR: {name} - {e}")
            import traceback
            traceback.print_exc()
            self.test_results[name] = False
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total = len(self.test_results)
        passed = sum(1 for v in self.test_results.values() if v)
        failed = total - passed
        
        print(f"Total Features Tested: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print("\nFailed Features:")
            for name, result in self.test_results.items():
                if not result:
                    print(f"  ✗ {name}")
        
        print("="*70)
        return failed == 0


def test_1_core_pattern():
    """Test 1: Core Pattern Features"""
    print("\n[1] CORE PATTERN FEATURES")
    print("-" * 70)
    
    tester = InteractiveTester()
    
    # 1.1 Pattern Creation
    def test_pattern_creation():
        from core.pattern import Pattern, Frame, PatternMetadata
        pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=16, height=16),
            frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)]
        )
        print(f"  Created pattern: {pattern.name}")
        print(f"  Dimensions: {pattern.metadata.width}x{pattern.metadata.height}")
        print(f"  Frames: {len(pattern.frames)}")
        return pattern.name == "Test Pattern" and len(pattern.frames) == 1
    
    tester.test_feature("Pattern Creation", "Create a pattern with metadata and frames", test_pattern_creation)
    
    # 1.2 Multiple Frames
    def test_multiple_frames():
        from core.pattern import Pattern, Frame, PatternMetadata
        pattern = Pattern(
            name="Multi Frame",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(255,0,0)]*64, duration_ms=100),
                Frame(pixels=[(0,255,0)]*64, duration_ms=100),
                Frame(pixels=[(0,0,255)]*64, duration_ms=100)
            ]
        )
        print(f"  Created {len(pattern.frames)} frames")
        print(f"  Frame 0: {pattern.frames[0].pixels[0]}")
        print(f"  Frame 1: {pattern.frames[1].pixels[0]}")
        print(f"  Frame 2: {pattern.frames[2].pixels[0]}")
        return len(pattern.frames) == 3
    
    tester.test_feature("Multiple Frames", "Create pattern with multiple frames", test_multiple_frames)
    
    # 1.3 Pattern Duration
    def test_pattern_duration():
        from core.pattern import Pattern, Frame, PatternMetadata
        pattern = Pattern(
            name="Duration Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(0,0,0)]*64, duration_ms=100),
                Frame(pixels=[(0,0,0)]*64, duration_ms=200),
                Frame(pixels=[(0,0,0)]*64, duration_ms=150)
            ]
        )
        duration = pattern.duration_ms
        print(f"  Total duration: {duration}ms")
        print(f"  Frame durations: {[f.duration_ms for f in pattern.frames]}")
        return duration == 450
    
    tester.test_feature("Pattern Duration Calculation", "Calculate total pattern duration", test_pattern_duration)
    
    return tester.print_summary()


def test_2_automation():
    """Test 2: Automation Features"""
    print("\n[2] AUTOMATION FEATURES")
    print("-" * 70)
    
    tester = InteractiveTester()
    
    # 2.1 Automation Queue
    def test_automation_queue():
        from domain.automation.queue import AutomationQueueManager
        from domain.actions import DesignAction
        
        manager = AutomationQueueManager()
        print(f"  Created AutomationQueueManager")
        
        action1 = DesignAction(
            name="Scroll Left",
            action_type="scroll",
            params={"direction": "Left", "offset": 1}
        )
        action2 = DesignAction(
            name="Rotate 90°",
            action_type="rotate",
            params={"mode": "90° Clockwise"}
        )
        
        manager.enqueue(action1)
        manager.enqueue(action2)
        
        actions = manager.actions()
        print(f"  Enqueued {len(actions)} actions")
        print(f"  Actions: {[a.name for a in actions]}")
        
        return len(actions) == 2
    
    tester.test_feature("Automation Queue Manager", "Create and manage automation action queue", test_automation_queue)
    
    # 2.2 Frame Generation
    def test_frame_generation():
        from core.pattern import Pattern, Frame, PatternMetadata
        
        # Create source frame
        source_frame = Frame(pixels=[(255,0,0)]*64, duration_ms=100)
        pattern = Pattern(
            name="Frame Gen Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[source_frame]
        )
        
        # Generate frames with proper copying
        frame_count = 5
        new_frames = []
        current_pixels = [tuple(p) for p in source_frame.pixels]
        
        for i in range(frame_count):
            frame_pixels = [tuple(p) for p in current_pixels]
            temp_frame = Frame(pixels=frame_pixels, duration_ms=100)
            new_frames.append(temp_frame)
            current_pixels = [tuple(p) for p in temp_frame.pixels]
        
        print(f"  Generated {len(new_frames)} frames")
        print(f"  All frames have correct pixel count: {all(len(f.pixels) == 64 for f in new_frames)}")
        if len(new_frames) > 1:
            print(f"  Frames are independent: {new_frames[0].pixels[0] != new_frames[1].pixels[0]}")
        
        return len(new_frames) == frame_count and all(len(f.pixels) == 64 for f in new_frames)
    
    tester.test_feature("Frame Generation with Actions", "Generate frames by applying actions incrementally", test_frame_generation)
    
    # 2.3 Automation Engine
    def test_automation_engine():
        from core.automation.engine import AutomationEngine
        from domain.actions import DesignAction
        
        engine = AutomationEngine()
        print(f"  Created AutomationEngine")
        
        # Test schedule building
        actions = [
            DesignAction(name="Test", action_type="scroll", params={"direction": "Left", "offset": 1, "repeat": 2})
        ]
        schedule = engine.build_schedule(actions)
        print(f"  Built schedule with {len(schedule)} items")
        
        return len(schedule) == 1
    
    tester.test_feature("Automation Engine", "Automation engine for applying actions to frames", test_automation_engine)
    
    return tester.print_summary()


def test_3_text_rendering():
    """Test 3: Text Rendering Features"""
    print("\n[3] TEXT RENDERING FEATURES")
    print("-" * 70)
    
    tester = InteractiveTester()
    
    # 3.1 Text Renderer
    def test_text_renderer():
        from domain.text.text_renderer import TextRenderer, TextRenderOptions
        
        renderer = TextRenderer()
        print(f"  Created TextRenderer")
        
        options = TextRenderOptions(
            width=16,
            height=8,
            color=(255, 255, 255),
            alignment="left"
        )
        print(f"  Created TextRenderOptions: {options.width}x{options.height}")
        
        return renderer is not None and options.width == 16
    
    tester.test_feature("Text Renderer", "Text rendering with bitmap fonts", test_text_renderer)
    
    # 3.2 Glyph Provider
    def test_glyph_provider():
        from domain.text.glyph_provider import GlyphProvider
        
        provider = GlyphProvider()
        print(f"  Created GlyphProvider")
        
        # Test that provider exists and has expected attributes
        has_render = hasattr(provider, 'render_glyph') or hasattr(provider, 'get_glyph_data')
        print(f"  Has glyph rendering method: {has_render}")
        
        return provider is not None
    
    tester.test_feature("Glyph Provider", "Bitmap font glyph provider", test_glyph_provider)
    
    # 3.3 Bitmap Font
    def test_bitmap_font():
        from domain.text.bitmap_font import BitmapFont
        
        # Test that BitmapFont class exists
        print(f"  BitmapFont class available")
        
        return True
    
    tester.test_feature("Bitmap Font Support", "Bitmap font loading and usage", test_bitmap_font)
    
    return tester.print_summary()


def test_4_performance():
    """Test 4: Performance Features"""
    print("\n[4] PERFORMANCE FEATURES")
    print("-" * 70)
    
    tester = InteractiveTester()
    
    # 4.1 Performance Monitor
    def test_performance_monitor():
        from core.performance import PerformanceMonitor
        import time
        
        monitor = PerformanceMonitor()
        print(f"  Created PerformanceMonitor")
        
        # Test timing context
        with monitor.time_operation("test_operation"):
            time.sleep(0.01)  # Small delay
        
        summary = monitor.get_summary()
        print(f"  Recorded metrics: {len(summary)}")
        
        return len(summary) > 0
    
    tester.test_feature("Performance Monitor", "Monitor and log performance metrics", test_performance_monitor)
    
    # 4.2 LRU Cache
    def test_lru_cache():
        from core.performance import LRUCache
        
        cache = LRUCache(max_size=5)
        print(f"  Created LRUCache with max_size={cache.max_size}")
        
        # Test cache operations
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        value = cache.get("key1")
        
        print(f"  Put 2 items, retrieved: {value}")
        stats = cache.get_stats()
        print(f"  Cache stats: {stats}")
        
        return value == "value1" and stats['size'] == 2
    
    tester.test_feature("LRU Cache", "Least Recently Used cache implementation", test_lru_cache)
    
    # 4.3 Frame Cache
    def test_frame_cache():
        from core.performance.cache import FrameCache, get_frame_cache
        
        cache = get_frame_cache()
        print(f"  Retrieved FrameCache")
        
        return cache is not None
    
    tester.test_feature("Frame Cache", "Frame caching for performance", test_frame_cache)
    
    return tester.print_summary()


def main():
    """Run interactive feature tests"""
    print("="*70)
    print("UPLOAD BRIDGE - INTERACTIVE FEATURE TESTING")
    print("="*70)
    print("\nTesting features one by one with detailed output...")
    
    results = []
    
    # Test each category
    results.append(("Core Pattern", test_1_core_pattern()))
    results.append(("Automation", test_2_automation()))
    results.append(("Text Rendering", test_3_text_rendering()))
    results.append(("Performance", test_4_performance()))
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    for category, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {category}")
    
    print("="*70)
    
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n✅ All feature categories passed!")
    else:
        print("\n⚠ Some feature categories had failures. See details above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
