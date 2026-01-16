"""
Integration tests for complete LED Matrix Studio workflows.

Tests end-to-end functionality from project creation through export.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from domain.project import Project
from domain.timeline import Timeline
from domain.layer_track import LayerTrack
from domain.effect import EffectType
from domain.keyframe import EasingType

from core.frame_utils import empty_frame
from core.automation.engine import automation_executor
from core.export_manager import export_manager
from core.project_serializer import serialize_project, deserialize_project
from core.version_manager import version_manager
from core.cloud_sync import cloud_sync_manager


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete workflows from creation to export."""

    def setUp(self):
        """Create test project with multiple layers and effects."""
        self.width, self.height = 16, 8
        self.timeline = Timeline(fps=30, duration_seconds=2.0)
        self.project = Project(timeline=self.timeline)

        # Create background layer
        bg_layer = LayerTrack(
            name="Background",
            frames=[empty_frame(self.width, self.height) for _ in range(self.timeline.total_frames)]
        )
        # Fill background with blue gradient
        for i, frame in enumerate(bg_layer.frames):
            frame[:, :, 2] = int(255 * (i / len(bg_layer.frames)))  # Blue gradient
        self.project.layers.append(bg_layer)

        # Create animated layer
        anim_layer = LayerTrack(
            name="Animation",
            frames=[empty_frame(self.width, self.height) for _ in range(self.timeline.total_frames)]
        )
        # Create simple pattern
        for frame in anim_layer.frames:
            frame[2:6, 6:10] = [255, 255, 255]  # White square
        self.project.layers.append(anim_layer)

        # Add keyframes to animation layer
        anim_layer.set_keyframe("opacity", 0, 0.0)
        anim_layer.set_keyframe("opacity", 15, 1.0)
        anim_layer.set_keyframe("opacity", 45, 0.5)
        anim_layer.set_keyframe("opacity", 59, 0.0)

        # Set easing
        if "opacity" in anim_layer.keyframes:
            anim_layer.keyframes["opacity"].easing_type = EasingType.EASE_IN_OUT_QUAD

    def test_complete_animation_workflow(self):
        """Test complete workflow: create → animate → export."""
        # Apply scroll effect to animation layer
        action = {
            'type': EffectType.SCROLL.value,
            'target_layer_id': self.project.layers[1].id,
            'params': {'speed': 0.5, 'direction': 'right'}
        }

        # Execute automation
        success = automation_executor(self.project, action)
        self.assertTrue(success)

        # Verify animation was applied
        # Check that frames are different (scroll effect applied)
        first_frame = self.project.layers[1].frames[0]
        last_frame = self.project.layers[1].frames[-1]
        self.assertFalse((first_frame == last_frame).all())

        # Test rendering
        from core.compositor import render_frame
        rendered_frame = render_frame(self.project, 30)
        self.assertIsNotNone(rendered_frame)
        self.assertEqual(rendered_frame.shape, (self.height, self.width, 3))

    def test_project_persistence_workflow(self):
        """Test complete save/load workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = os.path.join(temp_dir, "test_project.json")

            # Save project
            data = serialize_project(self.project)
            self.assertIn('layers', data)
            self.assertEqual(len(data['layers']), 2)

            # Load project
            restored_project = deserialize_project(data)
            self.assertEqual(restored_project.timeline.fps, self.project.timeline.fps)
            self.assertEqual(len(restored_project.layers), 2)

            # Verify keyframes were preserved
            anim_layer = restored_project.layers[1]
            self.assertIn('opacity', anim_layer.keyframes)
            opacity_track = anim_layer.keyframes['opacity']
            self.assertEqual(len(opacity_track.keyframes), 4)
            self.assertEqual(opacity_track.easing_type, EasingType.EASE_IN_OUT_QUAD)

    def test_export_workflow(self):
        """Test complete export workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test multiple export formats
            formats_to_test = ['json', 'csv', 'bin']

            for fmt in formats_to_test:
                output_path = os.path.join(temp_dir, f"test.{fmt}")

                success = export_manager.export_project(self.project, output_path, fmt)
                self.assertTrue(success, f"Export failed for format: {fmt}")
                self.assertTrue(os.path.exists(output_path), f"Output file not created for format: {fmt}")

                # Verify file has content
                file_size = os.path.getsize(output_path)
                self.assertGreater(file_size, 0, f"Output file is empty for format: {fmt}")

    def test_version_control_workflow(self):
        """Test version control workflow."""
        # Create initial version
        version_id = version_manager.save_version(self.project, "Initial version")
        self.assertIsNotNone(version_id)

        # Modify project
        new_layer = LayerTrack(
            name="New Layer",
            frames=[empty_frame(self.width, self.height) for _ in range(self.timeline.total_frames)]
        )
        self.project.layers.append(new_layer)

        # Save new version
        version_id2 = version_manager.save_version(self.project, "Added new layer")
        self.assertIsNotNone(version_id2)
        self.assertNotEqual(version_id, version_id2)

        # Load old version
        restored_project = version_manager.load_version(version_id)
        self.assertIsNotNone(restored_project)
        self.assertEqual(len(restored_project.layers), 2)  # Should have original layers

        # Load new version
        restored_project2 = version_manager.load_version(version_id2)
        self.assertIsNotNone(restored_project2)
        self.assertEqual(len(restored_project2.layers), 3)  # Should have new layer

    def test_cloud_sync_workflow(self):
        """Test cloud sync workflow."""
        project_name = "test_integration_project"

        # Initial upload
        success, message = cloud_sync_manager.sync_project(self.project, project_name)
        self.assertTrue(success, f"Initial sync failed: {message}")

        # Modify project
        self.project.layers[0].opacity = 0.8

        # Sync again (should detect changes)
        success, message = cloud_sync_manager.sync_project(self.project, project_name)
        self.assertTrue(success, f"Update sync failed: {message}")
        self.assertIn("newer", message.lower())

        # Download project
        downloaded = cloud_sync_manager.download_project(
            f"{project_name}_{hash(project_name) % 1000000}"
        )
        self.assertIsNotNone(downloaded)
        self.assertEqual(len(downloaded.layers), len(self.project.layers))

    def test_performance_workflow(self):
        """Test performance under load."""
        from core.performance_profiler import benchmark_rendering

        # Benchmark rendering performance
        results = benchmark_rendering(self.project, frames=10)
        self.assertIn('avg_fps', results)
        self.assertGreater(results['avg_fps'], 1.0)  # Should render at least 1 FPS

        # Test memory usage
        from core.performance_profiler import check_memory_usage
        memory = check_memory_usage()
        self.assertIn('rss', memory)
        self.assertGreater(memory['rss'], 0)

    def test_large_project_workflow(self):
        """Test workflow with larger project."""
        # Create larger project
        large_timeline = Timeline(fps=30, duration_seconds=5.0)
        large_project = Project(timeline=large_timeline)

        # Add multiple layers
        for i in range(5):
            layer = LayerTrack(
                name=f"Large Layer {i}",
                frames=[empty_frame(32, 16) for _ in range(large_timeline.total_frames)]
            )
            large_project.layers.append(layer)

        # Test rendering doesn't crash
        from core.compositor import render_frame
        frame = render_frame(large_project, 0)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (16, 32, 3))

        # Test serialization
        data = serialize_project(large_project)
        restored = deserialize_project(data)
        self.assertEqual(len(restored.layers), 5)

    def test_error_recovery_workflow(self):
        """Test error recovery and edge cases."""
        # Test with corrupted project data
        corrupted_data = {"invalid": "data"}

        with self.assertRaises(Exception):
            deserialize_project(corrupted_data)

        # Test with invalid export format
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = os.path.join(temp_dir, "test.invalid")

            success = export_manager.export_project(self.project, invalid_path, 'invalid_format')
            self.assertFalse(success)

        # Test version control with non-existent version
        restored = version_manager.load_version("non_existent_version")
        self.assertIsNone(restored)


class TestStressTesting(unittest.TestCase):
    """Stress tests for system limits and edge cases."""

    def test_maximum_layers(self):
        """Test system with maximum number of layers."""
        timeline = Timeline(fps=30, duration_seconds=1.0)
        project = Project(timeline=timeline)

        # Add many layers
        max_layers = 20
        for i in range(max_layers):
            layer = LayerTrack(
                name=f"Stress Layer {i}",
                frames=[empty_frame(8, 8) for _ in range(timeline.total_frames)]
            )
            project.layers.append(layer)

        # Should still render
        from core.compositor import render_frame
        frame = render_frame(project, 0)
        self.assertIsNotNone(frame)

    def test_high_frame_rate(self):
        """Test with high frame rates."""
        high_fps_timeline = Timeline(fps=120, duration_seconds=1.0)
        project = Project(timeline=high_fps_timeline)

        layer = LayerTrack(
            name="High FPS Layer",
            frames=[empty_frame(12, 6) for _ in range(high_fps_timeline.total_frames)]
        )
        project.layers.append(layer)

        # Should handle high frame counts
        self.assertEqual(high_fps_timeline.total_frames, 120)

        # Rendering should work
        from core.compositor import render_frame
        frame = render_frame(project, 60)
        self.assertIsNotNone(frame)

    def test_memory_efficiency(self):
        """Test memory efficiency with large animations."""
        # Create memory-intensive project
        timeline = Timeline(fps=30, duration_seconds=10.0)  # 300 frames
        project = Project(timeline=timeline)

        # Large matrix
        width, height = 64, 32

        for i in range(3):
            layer = LayerTrack(
                name=f"Memory Layer {i}",
                frames=[empty_frame(width, height) for _ in range(timeline.total_frames)]
            )
            project.layers.append(layer)

        # Calculate expected memory usage
        bytes_per_frame = width * height * 3  # RGB
        total_bytes = bytes_per_frame * timeline.total_frames * len(project.layers)
        total_mb = total_bytes / (1024 * 1024)

        # Should be manageable (under 200MB for this test)
        self.assertLess(total_mb, 200.0, f"Memory usage too high: {total_mb:.1f} MB")


if __name__ == '__main__':
    print("Running LED Matrix Studio Integration Tests...")
    print("=" * 60)
    unittest.main(verbosity=2)
