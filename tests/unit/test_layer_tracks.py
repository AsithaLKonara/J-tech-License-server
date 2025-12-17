"""
Unit tests for LayerTrack-based layer system.

Tests the new layer architecture where layers span across frames
(like video editing software) instead of being per-frame.
"""

import unittest
from domain.layers import LayerManager, LayerTrack, LayerFrame, LayerGroup
from domain.pattern_state import PatternState
from core.pattern import Pattern, PatternMetadata, Frame


class TestLayerTrack(unittest.TestCase):
    """Test LayerTrack class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100),
                Frame(pixels=[(255, 255, 255)] * 64, duration_ms=100),
            ]
        )
        self.state = PatternState()
        self.state.set_pattern(self.pattern)
        self.layer_manager = LayerManager(self.state)
        self.layer_manager.set_pattern(self.pattern)
    
    def test_layer_track_creation(self):
        """Test creating a LayerTrack."""
        track = LayerTrack(name="Test Layer", z_index=0)
        self.assertEqual(track.name, "Test Layer")
        self.assertEqual(track.z_index, 0)
        self.assertEqual(track.visible, True)
        self.assertEqual(track.opacity, 1.0)
        self.assertEqual(len(track.frames), 0)
    
    def test_layer_frame_creation(self):
        """Test creating a LayerFrame."""
        pixels = [(255, 0, 0)] * 64
        layer_frame = LayerFrame(pixels=pixels)
        self.assertEqual(len(layer_frame.pixels), 64)
        self.assertIsNone(layer_frame.visible)  # None = use layer default
        self.assertIsNone(layer_frame.opacity)  # None = use layer default
    
    def test_layer_track_get_or_create_frame(self):
        """Test getting or creating frame in LayerTrack."""
        track = LayerTrack(name="Test")
        frame = track.get_or_create_frame(0, 8, 8)
        self.assertIsNotNone(frame)
        self.assertEqual(len(frame.pixels), 64)
        
        # Getting again should return same frame
        frame2 = track.get_or_create_frame(0, 8, 8)
        self.assertIs(frame, frame2)
    
    def test_layer_track_effective_properties(self):
        """Test effective visibility and opacity with overrides."""
        track = LayerTrack(name="Test", visible=True, opacity=0.8)
        
        # Frame without override uses layer default
        frame1 = LayerFrame(pixels=[(0, 0, 0)] * 64)
        track.set_frame(0, frame1)
        self.assertTrue(track.get_effective_visibility(0))
        self.assertEqual(track.get_effective_opacity(0), 0.8)
        
        # Frame with override uses frame value
        frame2 = LayerFrame(pixels=[(0, 0, 0)] * 64, visible=False, opacity=0.5)
        track.set_frame(1, frame2)
        self.assertFalse(track.get_effective_visibility(1))
        self.assertEqual(track.get_effective_opacity(1), 0.5)


class TestLayerManagerTracks(unittest.TestCase):
    """Test LayerManager with LayerTracks."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100),
                Frame(pixels=[(255, 255, 255)] * 64, duration_ms=100),
            ]
        )
        self.state = PatternState()
        self.state.set_pattern(self.pattern)
        self.layer_manager = LayerManager(self.state)
        self.layer_manager.set_pattern(self.pattern)
    
    def test_get_layer_tracks(self):
        """Test getting all layer tracks."""
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 1)  # Default layer
        self.assertEqual(tracks[0].name, "Layer 1")
    
    def test_add_layer_track(self):
        """Test adding a new layer track."""
        track_index = self.layer_manager.add_layer_track("Background")
        self.assertEqual(track_index, 1)
        
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[1].name, "Background")
    
    def test_remove_layer_track(self):
        """Test removing a layer track."""
        self.layer_manager.add_layer_track("Layer 2")
        self.layer_manager.add_layer_track("Layer 3")
        
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 3)
        
        # Can't remove last layer
        result = self.layer_manager.remove_layer_track(0)
        self.assertFalse(result)
        
        # Can remove non-last layer
        result = self.layer_manager.remove_layer_track(1)
        self.assertTrue(result)
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 2)
    
    def test_move_layer_track(self):
        """Test moving layer tracks (reordering)."""
        self.layer_manager.add_layer_track("Layer 2")
        self.layer_manager.add_layer_track("Layer 3")
        
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(tracks[0].name, "Layer 1")
        self.assertEqual(tracks[1].name, "Layer 2")
        self.assertEqual(tracks[2].name, "Layer 3")
        
        # Move layer 2 to position 0
        self.layer_manager.move_layer_track(1, 0)
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(tracks[0].name, "Layer 2")
        self.assertEqual(tracks[1].name, "Layer 1")
        self.assertEqual(tracks[2].name, "Layer 3")
    
    def test_apply_pixel_to_track(self):
        """Test applying pixel to layer track."""
        track_index = self.layer_manager.add_layer_track("Foreground")
        
        # Apply pixel to frame 0
        self.layer_manager.apply_pixel(0, 2, 3, (255, 0, 0), 8, 8, track_index)
        
        # Verify pixel was set
        track = self.layer_manager.get_layer_track(track_index)
        frame = track.get_frame(0)
        self.assertIsNotNone(frame)
        idx = 3 * 8 + 2
        self.assertEqual(frame.pixels[idx], (255, 0, 0))
    
    def test_composite_pixels(self):
        """Test compositing multiple layer tracks."""
        # Create background layer
        bg_track = self.layer_manager.get_layer_track(0)
        bg_frame = bg_track.get_frame(0)
        bg_frame.pixels = [(0, 0, 255)] * 64  # Blue background
        
        # Create foreground layer
        fg_index = self.layer_manager.add_layer_track("Foreground")
        fg_track = self.layer_manager.get_layer_track(fg_index)
        fg_frame = fg_track.get_or_create_frame(0, 8, 8)
        fg_frame.pixels = [(255, 0, 0)] * 64  # Red foreground
        fg_frame.opacity = 0.5  # 50% opacity
        
        # Composite
        composite = self.layer_manager.get_composite_pixels(0)
        
        # Should be blend of blue and red
        self.assertEqual(len(composite), 64)
        # First pixel should be blended
        r, g, b = composite[0]
        self.assertGreater(r, 0)  # Some red
        self.assertGreater(b, 0)  # Some blue
    
    def test_layer_track_spans_frames(self):
        """Test that layer tracks span across all frames."""
        track_index = self.layer_manager.add_layer_track("Animation")
        track = self.layer_manager.get_layer_track(track_index)
        
        # Set different content for each frame
        frame0 = track.get_or_create_frame(0, 8, 8)
        frame0.pixels = [(255, 0, 0)] * 64  # Red
        
        frame1 = track.get_or_create_frame(1, 8, 8)
        frame1.pixels = [(0, 255, 0)] * 64  # Green
        
        # Verify both frames exist
        self.assertIsNotNone(track.get_frame(0))
        self.assertIsNotNone(track.get_frame(1))
        self.assertEqual(track.get_frame(0).pixels[0], (255, 0, 0))
        self.assertEqual(track.get_frame(1).pixels[0], (0, 255, 0))


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with old per-frame layer API."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100),
                Frame(pixels=[(255, 255, 255)] * 64, duration_ms=100),
            ]
        )
        self.state = PatternState()
        self.state.set_pattern(self.pattern)
        self.layer_manager = LayerManager(self.state)
        self.layer_manager.set_pattern(self.pattern)
    
    def test_get_layers_backward_compat(self):
        """Test get_layers() returns compatible Layer objects."""
        layers = self.layer_manager.get_layers(0)
        self.assertIsInstance(layers, list)
        self.assertEqual(len(layers), 1)
        # Should work with old API
        from domain.layers import Layer
        self.assertIsInstance(layers[0], Layer)
    
    def test_add_layer_backward_compat(self):
        """Test add_layer() works with old API."""
        layer_index = self.layer_manager.add_layer(0, "Background")
        self.assertEqual(layer_index, 1)
        
        # Should create a layer track
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[1].name, "Background")
    
    def test_set_layer_visible_backward_compat(self):
        """Test set_layer_visible() works with old API."""
        self.layer_manager.add_layer(0, "Test")
        
        # Set visibility for frame 0
        self.layer_manager.set_layer_visible(0, 1, False)
        
        # Check it worked
        track = self.layer_manager.get_layer_track(1)
        self.assertFalse(track.get_effective_visibility(0))
    
    def test_set_layer_opacity_backward_compat(self):
        """Test set_layer_opacity() works with old API."""
        self.layer_manager.add_layer(0, "Test")
        
        # Set opacity for frame 0
        self.layer_manager.set_layer_opacity(0, 1, 0.5)
        
        # Check it worked
        track = self.layer_manager.get_layer_track(1)
        self.assertEqual(track.get_effective_opacity(0), 0.5)


class TestMigration(unittest.TestCase):
    """Test migration from old per-frame structure."""
    
    def test_migration_detection(self):
        """Test detecting old layer structure."""
        from core.migration.layer_migration import detect_old_layer_structure
        
        pattern = Pattern(
            name="Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)]
        )
        state = PatternState()
        state.set_pattern(pattern)
        layer_manager = LayerManager(state)
        layer_manager.set_pattern(pattern)
        
        # New structure should not be detected as old
        is_old = detect_old_layer_structure(layer_manager)
        self.assertFalse(is_old)


if __name__ == '__main__':
    unittest.main()
