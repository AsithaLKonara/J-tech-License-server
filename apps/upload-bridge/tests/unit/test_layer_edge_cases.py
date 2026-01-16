"""
Edge case tests for layer compositing.
"""

import unittest
from domain.layers import LayerManager, LayerTrack, LayerFrame
from domain.pattern_state import PatternState
from core.pattern import Pattern, PatternMetadata, Frame


class TestLayerEdgeCases(unittest.TestCase):
    """Test edge cases for layer compositing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)]
        )
        self.state = PatternState()
        self.state.set_pattern(self.pattern)
        self.layer_manager = LayerManager(self.state)
        self.layer_manager.set_pattern(self.pattern)
    
    def test_black_pixels_with_opacity_blend(self):
        """Black pixels with opacity < 1.0 should blend, not skip."""
        # Layer 0: Red background
        bg_track = self.layer_manager.get_layer_track(0)
        bg_frame = bg_track.get_frame(0)
        bg_frame.pixels = [(255, 0, 0)] * 64  # Red background
        
        # Layer 1: Black pixels with opacity 0.5
        fg_index = self.layer_manager.add_layer_track("Black Layer")
        fg_track = self.layer_manager.get_layer_track(fg_index)
        fg_track.opacity = 0.5  # 50% opacity
        fg_frame = fg_track.get_or_create_frame(0, 8, 8)
        fg_frame.pixels = [(0, 0, 0)] * 64  # Black pixels
        
        # Composite
        composite = self.layer_manager.get_composite_pixels(0)
        
        # Should be dark red (blended), not pure red (skipped)
        # With opacity 0.5: result = red * 0.5 + black * 0.5 = dark red
        r, g, b = composite[0]
        self.assertGreater(r, 0, "Should have some red")
        self.assertLess(r, 255, "Should be darker than pure red (blended)")
        self.assertEqual(g, 0)
        self.assertEqual(b, 0)
    
    def test_black_pixels_middle_layer(self):
        """Black pixels in middle layer should preserve bottom layer."""
        # Layer 0: Red
        bg_track = self.layer_manager.get_layer_track(0)
        bg_frame = bg_track.get_or_create_frame(0, 8, 8)
        bg_frame.pixels = [(255, 0, 0)] * 64
        
        # Layer 1: Black (should preserve red - skipped due to black + opacity 1.0)
        mid_index = self.layer_manager.add_layer_track("Middle")
        mid_track = self.layer_manager.get_layer_track(mid_index)
        mid_frame = mid_track.get_or_create_frame(0, 8, 8)
        mid_frame.pixels = [(0, 0, 0)] * 64  # Black pixels with default opacity 1.0
        
        # Verify middle layer is skipped (composite should still have red)
        composite_after_mid = self.layer_manager.get_composite_pixels(0)
        has_red_after_mid = any(r > 0 for r, g, b in composite_after_mid)
        self.assertTrue(has_red_after_mid, "Red should be preserved after black middle layer")
        
        # Layer 2: Green with partial opacity (should blend with red, not black)
        fg_index = self.layer_manager.add_layer_track("Top")
        fg_track = self.layer_manager.get_layer_track(fg_index)
        fg_track.opacity = 0.5  # 50% opacity so it blends, not replaces
        fg_frame = fg_track.get_or_create_frame(0, 8, 8)
        fg_frame.pixels = [(0, 255, 0)] * 64
        
        # Composite
        composite = self.layer_manager.get_composite_pixels(0)
        
        # Should have both red and green (black layer skipped, green blends with red)
        # With 50% opacity: result = red * 0.5 + green * 0.5 = (127, 127, 0) - yellow
        has_red = any(r > 0 for r, g, b in composite)
        has_green = any(g > 0 for r, g, b in composite)
        self.assertTrue(has_red, f"Red should be preserved (black middle layer skipped). First pixel: {composite[0]}")
        self.assertTrue(has_green, "Green should be present (blended with red)")


if __name__ == '__main__':
    unittest.main()
