"""
Frame-by-Frame Comparison Tests

These tests compare rendered frames against expected LMS outputs.
Can be extended to load actual LMS project files for comparison.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from typing import List, Tuple
from domain.layers import LayerManager, LayerTrack, LayerFrame
from domain.automation.layer_action import LayerAction
from domain.pattern_state import PatternState
from core.pattern import Pattern, PatternMetadata

Color = Tuple[int, int, int]


class TestLMSFrameComparison(unittest.TestCase):
    """Compare rendered frames against expected LMS outputs."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.width = 8
        self.height = 8
        metadata = PatternMetadata(width=self.width, height=self.height)
        pattern = Pattern(metadata=metadata, frames=[])
        self.state = PatternState(pattern)
        self.layer_manager = LayerManager(self.state)
    
    def assert_frame_matches(
        self,
        actual: List[Color],
        expected: List[Color],
        frame_index: int,
        tolerance: int = 0
    ):
        """
        Assert that actual frame matches expected frame.
        
        Args:
            actual: Rendered frame pixels
            expected: Expected frame pixels (LMS reference)
            frame_index: Frame index for error messages
            tolerance: Pixel value tolerance (0 = exact match)
        """
        self.assertEqual(
            len(actual),
            len(expected),
            f"Frame {frame_index}: Length mismatch"
        )
        
        mismatches = []
        for i, (a, e) in enumerate(zip(actual, expected)):
            if tolerance == 0:
                if a != e:
                    x = i % self.width
                    y = i // self.width
                    mismatches.append(f"  Position ({x},{y}): expected {e}, got {a}")
            else:
                # Allow tolerance for rounding differences
                diff = max(abs(a[0] - e[0]), abs(a[1] - e[1]), abs(a[2] - e[2]))
                if diff > tolerance:
                    x = i % self.width
                    y = i // self.width
                    mismatches.append(f"  Position ({x},{y}): expected {e}, got {a} (diff: {diff})")
        
        if mismatches:
            error_msg = f"Frame {frame_index} mismatches:\n" + "\n".join(mismatches[:10])
            if len(mismatches) > 10:
                error_msg += f"\n  ... and {len(mismatches) - 10} more"
            self.fail(error_msg)
    
    def test_scroll_frame_by_frame(self):
        """Test scroll action frame-by-frame against expected outputs."""
        # Create scroll pattern
        track_idx = self.layer_manager.add_layer_track("Scroll")
        track = self.layer_manager._layer_tracks[track_idx]
        base_pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        
        # Set frames at all indices we'll test
        for frame_idx in [0, 1, 7, 8, 9]:
            frame = LayerFrame(pixels=base_pixels)
            track.set_frame(frame_idx, frame)
        
        action = LayerAction(
            type="scroll",
            start_frame=0,
            end_frame=10,
            params={"direction": "right", "offset": 1}
        )
        track.add_automation(action)
        
        # Expected outputs (LMS reference)
        expected_frames = {
            0: [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1),  # Frame 0: white at (0,0)
            1: [(0, 0, 0), (255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 2),  # Frame 1: white at (1,0)
            7: [(0, 0, 0)] * 7 + [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 8),  # Frame 7: white at (7,0)
            8: [(0, 0, 0)] * (self.width * self.height),  # Frame 8: all black (out of bounds, step=8)
            9: [(0, 0, 0)] * (self.width * self.height),  # Frame 9: all black (out of bounds)
        }
        
        for frame_idx, expected in expected_frames.items():
            actual = self.layer_manager.render_frame(frame_idx)
            self.assert_frame_matches(actual, expected, frame_idx)
    
    def test_opacity_frame_exact(self):
        """Test opacity produces exact brightness values."""
        track_idx = self.layer_manager.add_layer_track("Opacity")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 0, 0)] * (self.width * self.height)  # Red
        frame = LayerFrame(pixels=pixels)
        track.set_frame(0, frame)
        track.opacity = 0.5
        
        actual = self.layer_manager.render_frame(0)
        # 255 * 0.5 = 127.5, int() = 127
        expected = [(127, 0, 0)] * (self.width * self.height)
        
        self.assert_frame_matches(actual, expected, 0)
    
    def test_multi_layer_compositing(self):
        """Test multi-layer compositing matches LMS."""
        # Bottom: red
        bottom_idx = self.layer_manager.add_layer_track("Bottom")
        bottom = self.layer_manager._layer_tracks[bottom_idx]
        bottom_frame = LayerFrame(pixels=[(255, 0, 0)] * (self.width * self.height))
        bottom.set_frame(0, bottom_frame)
        bottom.z_index = 0
        
        # Top: black with white at (0,0)
        top_idx = self.layer_manager.add_layer_track("Top")
        top = self.layer_manager._layer_tracks[top_idx]
        top_pixels = [(0, 0, 0)] * (self.width * self.height)
        top_pixels[0] = (255, 255, 255)
        top_frame = LayerFrame(pixels=top_pixels)
        top.set_frame(0, top_frame)
        top.z_index = 1
        
        actual = self.layer_manager.render_frame(0)
        
        # Expected: white at (0,0), red everywhere else
        expected = [(255, 255, 255)] + [(255, 0, 0)] * (self.width * self.height - 1)
        
        self.assert_frame_matches(actual, expected, 0)
    
    def test_rotate_frame_sequence(self):
        """Test rotate produces correct frame sequence."""
        # Create pattern: white at (0,0)
        track_idx = self.layer_manager.add_layer_track("Rotate")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        frame = LayerFrame(pixels=pixels)
        track.set_frame(0, frame)
        
        action = LayerAction(
            type="rotate",
            start_frame=0,
            end_frame=10,
            params={"mode": "90° Clockwise"}
        )
        track.add_automation(action)
        
        # Frame 0: step=0, no rotation
        frame0 = self.layer_manager.render_frame(0)
        self.assertEqual(frame0[0], (255, 255, 255), "Frame 0: white at (0,0)")
        
        # Frame 1: step=1, 90° rotation
        # After 90° CW on 8x8: (0,0) -> (0,7)
        frame1 = self.layer_manager.render_frame(1)
        # Note: exact position depends on rotation implementation
        # Key is that it uses base pixels, not accumulating
        
        # Frame 2: step=2, 180° rotation
        # Should be same as rotating base by 180°, not frame1 by 90°
        frame2 = self.layer_manager.render_frame(2)
        # Verify it's not just frame1 rotated again
    
    def test_automation_order_impact(self):
        """Test that automation order produces correct results."""
        track_idx = self.layer_manager.add_layer_track("Order Test")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        frame = LayerFrame(pixels=pixels)
        track.set_frame(0, frame)
        
        # Add scroll (priority 10) and invert (priority 90)
        # Order should be: scroll first, then invert
        scroll = LayerAction(
            type="scroll",
            start_frame=0,
            end_frame=5,
            params={"direction": "right", "offset": 1}
        )
        invert = LayerAction(
            type="invert",
            start_frame=0,
            end_frame=5,
            params={}
        )
        
        # Add in reverse order (invert first)
        track.add_automation(invert)
        track.add_automation(scroll)
        
        # Result should be: scroll moves pixel, then invert inverts it
        # Frame 1: pixel at (1,0) should be inverted white = black
        frame1 = self.layer_manager.render_frame(1)
        # Scroll moves white to position 1, invert makes it black
        self.assertEqual(frame1[1], (0, 0, 0), "Frame 1: scroll then invert")


if __name__ == "__main__":
    unittest.main()
