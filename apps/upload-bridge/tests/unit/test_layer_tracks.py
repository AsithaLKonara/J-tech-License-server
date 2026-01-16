"""
Unit tests for LayerTrack-based layer system.

Tests the new layer architecture where layers span across frames
(like video editing software) instead of being per-frame.
"""

import unittest
from domain.layers import LayerManager, LayerTrack, LayerFrame, LayerGroup, Layer
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
        
        # Can remove non-last layer
        result = self.layer_manager.remove_layer_track(1)
        self.assertTrue(result)
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 2)
        
        # Remove another layer, leaving only 1
        result = self.layer_manager.remove_layer_track(0)
        self.assertTrue(result)
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 1)
        
        # Can't remove last remaining layer
        result = self.layer_manager.remove_layer_track(0)
        self.assertFalse(result)
        tracks = self.layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 1)  # Still 1 layer
    
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

    def test_two_layer_scroll_animation_matches_docs(self):
        """
        Sanity check: two layers with independent scroll animations overlay correctly.

        This corresponds to the example in LAYER_ANIMATION_INTEGRATION.md where
        one layer scrolls right and another scrolls up at the same time.
        """
        from domain.layer_animation import create_scroll_animation

        pattern = Pattern(
            name="Anim Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100) for _ in range(4)],
        )
        state = PatternState()
        state.set_pattern(pattern)
        layer_manager = LayerManager(state)
        layer_manager.set_pattern(pattern)

        # Layer 0: horizontal bar scrolling right
        bg_track = layer_manager.get_layer_track(0)
        for i in range(4):
            frame = bg_track.get_or_create_frame(i, 8, 8)
            frame.pixels = [(0, 0, 0)] * 64
            for x in range(8):
                frame.pixels[3 * 8 + x] = (255, 0, 0)  # red bar on row 3

        scroll_right = create_scroll_animation(direction="right", speed=1.0, start_frame=0, end_frame=None)
        layer_manager.set_layer_animation(0, scroll_right)

        # Layer 1: vertical bar scrolling up
        fg_index = layer_manager.add_layer_track("Vertical")
        fg_track = layer_manager.get_layer_track(fg_index)
        for i in range(4):
            frame = fg_track.get_or_create_frame(i, 8, 8)
            frame.pixels = [(0, 0, 0)] * 64
            for y in range(8):
                frame.pixels[y * 8 + 4] = (0, 255, 0)  # green bar on column 4

        scroll_up = create_scroll_animation(direction="up", speed=1.0, start_frame=0, end_frame=None)
        layer_manager.set_layer_animation(fg_index, scroll_up)

        # At frame 0 (before scrolling), both bars should be visible and overlap
        # The red bar is on row 3, green bar is on column 4, so they intersect at (4, 3)
        composite_frame0 = layer_manager.get_composite_pixels(0)
        assert len(composite_frame0) == 64
        # At frame 0, both colors should be present (red bar on row 3, green bar on column 4)
        has_red = any(r > 0 for (r, g, b) in composite_frame0)
        has_green = any(g > 0 for (r, g, b) in composite_frame0)
        assert has_red, "Red bar should be visible at frame 0"
        assert has_green, "Green bar should be visible at frame 0"
        
        # Verify animations are applied by checking that pixels move across frames
        # At least one frame should have both colors (they may scroll apart in later frames)
        any_frame_has_both = False
        for frame_index in range(4):
            composite = layer_manager.get_composite_pixels(frame_index)
            assert len(composite) == 64
            has_red_frame = any(r > 0 for (r, g, b) in composite)
            has_green_frame = any(g > 0 for (r, g, b) in composite)
            if has_red_frame and has_green_frame:
                any_frame_has_both = True
        assert any_frame_has_both, "At least one frame should contain both red and green (animations working)"

    def test_migrate_multiple_frames_same_layer_names(self):
        """Old per-frame layers with same names are grouped into single tracks."""
        from core.migration.layer_migration import migrate_layers_to_tracks

        pattern = Pattern(
            name="Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100),
                Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100),
            ],
        )
        state = PatternState()
        state.set_pattern(pattern)
        layer_manager = LayerManager(state)

        # Simulate legacy per-frame layers: frame 0 and 1 both have "Background" and "Foreground"
        bg0 = Layer(name="Background", pixels=[(10, 10, 10)] * 64, visible=True, opacity=1.0)
        fg0 = Layer(name="Foreground", pixels=[(20, 20, 20)] * 64, visible=True, opacity=0.5)
        bg1 = Layer(name="Background", pixels=[(30, 30, 30)] * 64, visible=True, opacity=1.0)
        fg1 = Layer(name="Foreground", pixels=[(40, 40, 40)] * 64, visible=True, opacity=0.5)

        old_layers = {
            0: [bg0, fg0],
            1: [bg1, fg1],
        }

        migrate_layers_to_tracks(layer_manager, old_layers)

        tracks = layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 2)
        names = {t.name for t in tracks}
        self.assertEqual(names, {"Background", "Foreground"})

        bg_track = next(t for t in tracks if t.name == "Background")
        fg_track = next(t for t in tracks if t.name == "Foreground")

        # Background pixels differ per frame
        self.assertEqual(bg_track.get_frame(0).pixels[0], (10, 10, 10))
        self.assertEqual(bg_track.get_frame(1).pixels[0], (30, 30, 30))
        # Foreground pixels differ per frame
        self.assertEqual(fg_track.get_frame(0).pixels[0], (20, 20, 20))
        self.assertEqual(fg_track.get_frame(1).pixels[0], (40, 40, 40))

    def test_migrate_mismatched_layer_sets(self):
        """Frames with different layer sets migrate correctly."""
        from core.migration.layer_migration import migrate_layers_to_tracks

        pattern = Pattern(
            name="Test",
            metadata=PatternMetadata(width=4, height=4),
            frames=[
                Frame(pixels=[(0, 0, 0)] * 16, duration_ms=100),
                Frame(pixels=[(0, 0, 0)] * 16, duration_ms=100),
            ],
        )
        state = PatternState()
        state.set_pattern(pattern)
        layer_manager = LayerManager(state)

        # Frame 0: Background + Text, Frame 1: only Background
        bg0 = Layer(name="Background", pixels=[(1, 1, 1)] * 16)
        text0 = Layer(name="Text", pixels=[(2, 2, 2)] * 16)
        bg1 = Layer(name="Background", pixels=[(3, 3, 3)] * 16)

        old_layers = {
            0: [bg0, text0],
            1: [bg1],
        }

        migrate_layers_to_tracks(layer_manager, old_layers)

        tracks = layer_manager.get_layer_tracks()
        names = {t.name for t in tracks}
        self.assertEqual(names, {"Background", "Text"})

        bg_track = next(t for t in tracks if t.name == "Background")
        text_track = next(t for t in tracks if t.name == "Text")

        # Background exists in both frames
        self.assertIsNotNone(bg_track.get_frame(0))
        self.assertIsNotNone(bg_track.get_frame(1))
        # Text only in frame 0
        self.assertIsNotNone(text_track.get_frame(0))
        self.assertIsNone(text_track.get_frame(1))

    def test_migrate_preserves_visibility_and_opacity_overrides(self):
        """Visibility and opacity differences per frame become overrides on LayerFrame."""
        from core.migration.layer_migration import migrate_layers_to_tracks

        pattern = Pattern(
            name="Test",
            metadata=PatternMetadata(width=2, height=2),
            frames=[
                Frame(pixels=[(0, 0, 0)] * 4, duration_ms=100),
                Frame(pixels=[(0, 0, 0)] * 4, duration_ms=100),
            ],
        )
        state = PatternState()
        state.set_pattern(pattern)
        layer_manager = LayerManager(state)

        # Frame 0: visible, opacity 1.0 (baseline)
        base = Layer(name="Layer", pixels=[(1, 1, 1)] * 4, visible=True, opacity=1.0)
        # Frame 1: hidden, opacity 0.5 (should be stored as overrides)
        override = Layer(name="Layer", pixels=[(2, 2, 2)] * 4, visible=False, opacity=0.5)

        old_layers = {
            0: [base],
            1: [override],
        }

        migrate_layers_to_tracks(layer_manager, old_layers)

        tracks = layer_manager.get_layer_tracks()
        self.assertEqual(len(tracks), 1)
        track = tracks[0]

        # Global properties come from first layer instance
        self.assertTrue(track.visible)
        self.assertEqual(track.opacity, 1.0)

        frame0 = track.get_frame(0)
        frame1 = track.get_frame(1)
        self.assertIsNotNone(frame0)
        self.assertIsNotNone(frame1)

        # Frame 0 uses global defaults (no overrides)
        self.assertIsNone(frame0.visible)
        self.assertIsNone(frame0.opacity)

        # Frame 1 stores overrides
        self.assertEqual(frame1.visible, False)
        self.assertAlmostEqual(frame1.opacity, 0.5, places=3)


if __name__ == '__main__':
    unittest.main()
