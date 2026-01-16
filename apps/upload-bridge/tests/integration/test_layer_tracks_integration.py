"""
Integration tests for LayerTrack system.

Tests the integration of LayerTracks with the full system including
compositing, frame management, and UI components.
"""

import unittest
from domain.layers import LayerManager, LayerTrack, LayerFrame
from domain.pattern_state import PatternState
from domain.frames import FrameManager
from core.pattern import Pattern, PatternMetadata, Frame


class TestLayerTrackIntegration(unittest.TestCase):
    """Integration tests for LayerTrack system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=16, height=16),
            frames=[
                Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100),
                Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100),
                Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100),
            ]
        )
        self.state = PatternState()
        self.state.set_pattern(self.pattern)
        self.layer_manager = LayerManager(self.state)
        self.layer_manager.set_pattern(self.pattern)
        self.frame_manager = FrameManager(self.state)
    
    def test_multi_layer_compositing(self):
        """Test compositing multiple layers across frames."""
        # Create background layer (blue, all frames)
        bg_track = self.layer_manager.get_layer_track(0)
        for i in range(3):
            frame = bg_track.get_or_create_frame(i, 16, 16)
            frame.pixels = [(0, 0, 255)] * 256
        
        # Create foreground layer (red, 50% opacity, all frames)
        fg_index = self.layer_manager.add_layer_track("Foreground")
        fg_track = self.layer_manager.get_layer_track(fg_index)
        fg_track.opacity = 0.5
        for i in range(3):
            frame = fg_track.get_or_create_frame(i, 16, 16)
            frame.pixels = [(255, 0, 0)] * 256
        
        # Composite each frame
        for i in range(3):
            composite = self.layer_manager.get_composite_pixels(i)
            self.assertEqual(len(composite), 256)
            # Should be blend of blue and red
            r, g, b = composite[0]
            self.assertGreater(r, 0)
            self.assertGreater(b, 0)
    
    def test_layer_independent_animation(self):
        """Test that layers can have different content per frame."""
        # Background: static blue
        bg_track = self.layer_manager.get_layer_track(0)
        for i in range(3):
            frame = bg_track.get_or_create_frame(i, 16, 16)
            frame.pixels = [(0, 0, 255)] * 256
        
        # Foreground: animated (red in frame 0, green in frame 1, blue in frame 2)
        fg_index = self.layer_manager.add_layer_track("Animation")
        fg_track = self.layer_manager.get_layer_track(fg_index)
        
        frame0 = fg_track.get_or_create_frame(0, 16, 16)
        frame0.pixels = [(255, 0, 0)] * 256
        
        frame1 = fg_track.get_or_create_frame(1, 16, 16)
        frame1.pixels = [(0, 255, 0)] * 256
        
        frame2 = fg_track.get_or_create_frame(2, 16, 16)
        frame2.pixels = [(0, 0, 255)] * 256
        
        # Verify each frame has correct content
        composite0 = self.layer_manager.get_composite_pixels(0)
        composite1 = self.layer_manager.get_composite_pixels(1)
        composite2 = self.layer_manager.get_composite_pixels(2)
        
        # Frame 0: blue background + red foreground
        r, g, b = composite0[0]
        self.assertGreater(r, b)  # More red than blue
        
        # Frame 1: blue background + green foreground
        r, g, b = composite1[0]
        self.assertGreater(g, b)  # More green than blue
        
        # Frame 2: blue background + blue foreground (both blue)
        r, g, b = composite2[0]
        self.assertGreater(b, r)  # More blue
    
    def test_layer_visibility_per_frame(self):
        """Test per-frame visibility overrides."""
        # Create layer
        layer_index = self.layer_manager.add_layer_track("Test")
        track = self.layer_manager.get_layer_track(layer_index)
        
        # Set content for all frames
        for i in range(3):
            frame = track.get_or_create_frame(i, 16, 16)
            frame.pixels = [(255, 0, 0)] * 256
        
        # Hide in frame 1 only
        frame1 = track.get_frame(1)
        frame1.visible = False
        
        # Composite frames
        composite0 = self.layer_manager.get_composite_pixels(0)
        composite1 = self.layer_manager.get_composite_pixels(1)
        composite2 = self.layer_manager.get_composite_pixels(2)
        
        # Frame 0 and 2 should have red
        r0, _, _ = composite0[0]
        r1, _, _ = composite1[0]
        r2, _, _ = composite2[0]
        
        self.assertGreater(r0, 0)  # Visible in frame 0
        self.assertEqual(r1, 0)  # Hidden in frame 1
        self.assertGreater(r2, 0)  # Visible in frame 2
    
    def test_z_order_compositing(self):
        """Test that z-order affects compositing."""
        # Bottom layer: blue
        bg_track = self.layer_manager.get_layer_track(0)
        bg_track.z_index = 0
        frame = bg_track.get_frame(0)
        frame.pixels = [(0, 0, 255)] * 256
        
        # Top layer: red
        fg_index = self.layer_manager.add_layer_track("Foreground")
        fg_track = self.layer_manager.get_layer_track(fg_index)
        fg_track.z_index = 1
        frame = fg_track.get_or_create_frame(0, 16, 16)
        frame.pixels = [(255, 0, 0)] * 256
        
        # Composite should have red on top
        composite = self.layer_manager.get_composite_pixels(0)
        r, g, b = composite[0]
        self.assertGreater(r, b)  # Red should dominate
    
    def test_frame_sync_from_layers(self):
        """Test syncing frame pixels from layer composite."""
        # Create layers
        bg_track = self.layer_manager.get_layer_track(0)
        frame = bg_track.get_frame(0)
        frame.pixels = [(0, 0, 255)] * 256
        
        fg_index = self.layer_manager.add_layer_track("Foreground")
        fg_track = self.layer_manager.get_layer_track(fg_index)
        fg_frame = fg_track.get_or_create_frame(0, 16, 16)
        fg_frame.pixels = [(255, 0, 0)] * 256
        fg_frame.opacity = 0.5
        
        # Sync frame
        self.layer_manager.sync_frame_from_layers(0)
        
        # Frame should have composite
        frame_pixels = self.pattern.frames[0].pixels
        self.assertEqual(len(frame_pixels), 256)
        r, g, b = frame_pixels[0]
        self.assertGreater(r, 0)
        self.assertGreater(b, 0)


if __name__ == '__main__':
    unittest.main()
