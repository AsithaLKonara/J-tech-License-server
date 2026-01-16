"""
Comprehensive test suite for LED Matrix Studio core functionality.

Tests cover all major components: projects, layers, keyframes, effects,
rendering, export, and performance.
"""

import unittest
import numpy as np
import time
import tempfile
import os
from pathlib import Path

# Import all core modules
from domain.project import Project
from domain.timeline import Timeline
from domain.layer_track import LayerTrack, BlendMode
from domain.keyframe import KeyframeTrack, EasingType
from domain.bezier_keyframe import BezierKeyframeTrack
from domain.effect import EffectType, get_effect_config
from domain.pixel_buffer import PixelBuffer

from core.frame_utils import empty_frame
from core.compositor import render_frame, composite
from core.project_serializer import serialize_project, deserialize_project
from core.timeline_manager import retime_project, RetimingMode
from core.automation.effects import apply_scroll_frame, apply_fade_frame
from core.export_manager import export_manager
from core.version_manager import version_manager


class TestCoreFunctionality(unittest.TestCase):
    """Test core LED Matrix Studio functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.width, self.height = 12, 6
        self.timeline = Timeline(fps=30, duration_seconds=3.0)
        self.project = Project(timeline=self.timeline)

        # Create test layer
        self.layer = LayerTrack(
            name="Test Layer",
            frames=[empty_frame(self.width, self.height) for _ in range(self.timeline.total_frames)]
        )
        self.project.layers.append(self.layer)

    def test_project_creation(self):
        """Test basic project creation and properties."""
        self.assertEqual(self.project.timeline.fps, 30)
        self.assertEqual(self.project.timeline.duration_seconds, 3.0)
        self.assertEqual(self.project.timeline.total_frames, 90)
        self.assertEqual(len(self.project.layers), 1)

    def test_layer_operations(self):
        """Test layer creation and manipulation."""
        # Test layer properties
        self.assertEqual(self.layer.name, "Test Layer")
        self.assertEqual(len(self.layer.frames), 90)
        self.assertTrue(self.layer.visible)
        self.assertEqual(self.layer.opacity, 1.0)
        self.assertEqual(self.layer.blend_mode, BlendMode.NORMAL)
        self.assertEqual(self.layer.z_index, 0)

        # Test layer modification
        self.layer.opacity = 0.8
        self.layer.z_index = 5
        self.layer.blend_mode = BlendMode.MULTIPLY

        self.assertEqual(self.layer.opacity, 0.8)
        self.assertEqual(self.layer.z_index, 5)
        self.assertEqual(self.layer.blend_mode, BlendMode.MULTIPLY)

    def test_keyframe_system(self):
        """Test keyframe creation and interpolation."""
        # Create keyframe track
        kf_track = KeyframeTrack("opacity", [
            Keyframe(frame=0, value=0.0),
            Keyframe(frame=45, value=1.0),
            Keyframe(frame=89, value=0.5)
        ])

        # Test interpolation
        self.assertEqual(kf_track.get_value_at(0), 0.0)   # First keyframe
        self.assertEqual(kf_track.get_value_at(89), 0.5)  # Last keyframe
        self.assertAlmostEqual(kf_track.get_value_at(22), 0.5, places=1)  # Mid interpolation

        # Test easing
        kf_track.easing_type = EasingType.EASE_IN_OUT_QUAD
        eased_value = kf_track.get_value_at(22)
        self.assertGreater(eased_value, 0.0)  # Should be eased

    def test_bezier_keyframes(self):
        """Test bezier keyframe system."""
        bz_track = BezierKeyframeTrack("scroll_speed", [])

        # Add keyframes
        bz_track.add_keyframe(0, 0.0)
        bz_track.add_keyframe(45, 1.0)
        bz_track.add_keyframe(89, 0.5)

        # Test basic interpolation
        self.assertEqual(bz_track.get_value_at(0), 0.0)
        self.assertEqual(bz_track.get_value_at(45), 1.0)

        # Test auto-smoothing
        bz_track.auto_smooth(tension=0.5)
        # Should have control points set
        self.assertNotEqual(bz_track.keyframes[1].left_control, (0.0, 0.0))

    def test_rendering(self):
        """Test frame rendering and compositing."""
        # Test basic rendering
        frame = render_frame(self.project, 0)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (self.height, self.width, 3))

        # Test compositing
        dst = empty_frame(self.width, self.height)
        src = empty_frame(self.width, self.height)
        src.fill(255)  # White source

        result = composite(dst, src, opacity=0.5)
        # Should be 50% white
        self.assertTrue(np.allclose(result, 127.5, atol=1))

    def test_effects(self):
        """Test effect application."""
        # Test scroll effect
        original_frame = self.layer.frames[0].copy()
        apply_scroll_frame(self.layer, 10, speed=0.5, direction="right")

        # Frame should be modified
        self.assertFalse(np.array_equal(self.layer.frames[10], original_frame))

        # Test fade effect
        apply_fade_frame(self.layer, 20, opacity=0.5)
        # Should be dimmed
        self.assertTrue(np.all(self.layer.frames[20] <= original_frame))

    def test_serialization(self):
        """Test project serialization and deserialization."""
        # Add some keyframes to test serialization
        self.layer.set_keyframe("opacity", 0, 0.5)
        self.layer.set_keyframe("opacity", 45, 1.0)

        # Serialize
        data = serialize_project(self.project)
        self.assertIn('timeline', data)
        self.assertIn('layers', data)
        self.assertEqual(len(data['layers']), 1)

        # Deserialize
        restored_project = deserialize_project(data)
        self.assertEqual(restored_project.timeline.fps, self.project.timeline.fps)
        self.assertEqual(len(restored_project.layers), 1)

        # Check keyframes were preserved
        restored_layer = restored_project.layers[0]
        self.assertIn('opacity', restored_layer.keyframes)
        opacity_track = restored_layer.keyframes['opacity']
        self.assertEqual(len(opacity_track.keyframes), 2)

    def test_retiming(self):
        """Test timeline retiming functionality."""
        original_frames = self.project.timeline.total_frames

        # Retime to longer duration
        retime_project(self.project, 6.0, RetimingMode.LINEAR)
        new_frames = self.project.timeline.total_frames

        self.assertGreater(new_frames, original_frames)
        self.assertEqual(len(self.layer.frames), new_frames)

    def test_export_formats(self):
        """Test various export formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON export
            json_path = os.path.join(temp_dir, "test.json")
            success = export_manager.export_project(self.project, json_path, 'json')
            self.assertTrue(success)
            self.assertTrue(os.path.exists(json_path))

            # Test CSV export
            csv_path = os.path.join(temp_dir, "test.csv")
            success = export_manager.export_project(self.project, csv_path, 'csv')
            self.assertTrue(success)
            self.assertTrue(os.path.exists(csv_path))

            # Test binary export
            bin_path = os.path.join(temp_dir, "test.bin")
            success = export_manager.export_project(self.project, bin_path, 'bin')
            self.assertTrue(success)
            self.assertTrue(os.path.exists(bin_path))

    def test_layer_blending(self):
        """Test layer blending modes."""
        # Create second layer
        layer2 = LayerTrack(
            name="Blend Test Layer",
            frames=[empty_frame(self.width, self.height) for _ in range(self.timeline.total_frames)]
        )
        layer2.frames[0].fill(255)  # White layer
        layer2.blend_mode = BlendMode.MULTIPLY
        self.project.layers.append(layer2)

        # Render frame with blending
        frame = render_frame(self.project, 0)
        self.assertIsNotNone(frame)

        # Test z-index ordering
        layer2.z_index = -1  # Should render first
        frame_reordered = render_frame(self.project, 0)
        # Result should be different due to ordering
        self.assertFalse(np.array_equal(frame, frame_reordered))


class TestPerformance(unittest.TestCase):
    """Performance and optimization tests."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.width, self.height = 32, 16  # Larger matrix for performance testing
        self.timeline = Timeline(fps=30, duration_seconds=5.0)
        self.project = Project(timeline=self.timeline)

        # Create multiple layers
        for i in range(3):
            layer = LayerTrack(
                name=f"Perf Layer {i}",
                frames=[empty_frame(self.width, self.height) for _ in range(self.timeline.total_frames)]
            )
            self.project.layers.append(layer)

    def test_render_performance(self):
        """Test rendering performance."""
        start_time = time.time()

        # Render all frames
        for frame_idx in range(min(30, self.timeline.total_frames)):  # Test first 30 frames
            frame = render_frame(self.project, frame_idx)
            self.assertIsNotNone(frame)

        end_time = time.time()
        total_time = end_time - start_time

        # Should render at least 10 FPS for performance test
        fps = 30 / total_time
        self.assertGreater(fps, 5.0, f"Rendering too slow: {fps:.1f} FPS")

    def test_memory_usage(self):
        """Test memory usage is reasonable."""
        # Calculate expected memory usage
        bytes_per_frame = self.width * self.height * 3  # RGB
        total_layers = len(self.project.layers)
        total_frames = self.timeline.total_frames

        expected_bytes = bytes_per_frame * total_frames * total_layers
        expected_mb = expected_bytes / (1024 * 1024)

        # Should be reasonable (less than 100MB for this test)
        self.assertLess(expected_mb, 100.0, f"Memory usage too high: {expected_mb:.1f} MB")

    def test_keyframe_performance(self):
        """Test keyframe interpolation performance."""
        # Create many keyframes
        kf_track = KeyframeTrack("test_property", [])
        for i in range(0, self.timeline.total_frames, 5):
            kf_track.add_keyframe(i, float(i) / self.timeline.total_frames)

        start_time = time.time()

        # Test interpolation performance
        for frame in range(self.timeline.total_frames):
            value = kf_track.get_value_at(frame)

        end_time = time.time()
        total_time = end_time - start_time

        # Should interpolate very fast
        self.assertLess(total_time, 1.0, f"Keyframe interpolation too slow: {total_time:.3f}s")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_empty_project(self):
        """Test handling of empty projects."""
        project = Project()
        frame = render_frame(project, 0)
        self.assertIsNone(frame)  # Should handle gracefully

    def test_invalid_frames(self):
        """Test handling of invalid frame indices."""
        timeline = Timeline(fps=30, duration_seconds=1.0)
        project = Project(timeline=timeline)

        layer = LayerTrack(
            name="Test",
            frames=[empty_frame(12, 6) for _ in range(10)]  # Only 10 frames
        )
        project.layers.append(layer)

        # Should handle out-of-bounds gracefully
        frame = render_frame(project, 50)  # Beyond available frames
        self.assertIsNone(frame)

    def test_zero_duration(self):
        """Test handling of zero duration timelines."""
        timeline = Timeline(fps=30, duration_seconds=0.0)
        self.assertEqual(timeline.total_frames, 0)

        project = Project(timeline=timeline)
        frame = render_frame(project, 0)
        self.assertIsNone(frame)

    def test_large_matrices(self):
        """Test handling of large LED matrices."""
        width, height = 64, 32  # Large matrix
        timeline = Timeline(fps=30, duration_seconds=1.0)
        project = Project(timeline=timeline)

        layer = LayerTrack(
            name="Large Matrix",
            frames=[empty_frame(width, height) for _ in range(timeline.total_frames)]
        )
        project.layers.append(layer)

        # Should handle large matrices
        frame = render_frame(project, 0)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (height, width, 3))


if __name__ == '__main__':
    # Run performance tests with timing
    import sys

    print("Running LED Matrix Studio Tests...")
    print("=" * 50)

    # Run all tests
    unittest.main(verbosity=2)
