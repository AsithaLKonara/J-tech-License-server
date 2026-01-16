"""
Timing Verification Tool

Verifies that automation timing matches LMS exactly:
- Frame-relative step calculation
- Action active window enforcement
- No timing drift or accumulation
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from domain.automation.layer_action import LayerAction, get_action_step
from domain.layers import LayerManager, LayerTrack, LayerFrame
from domain.pattern_state import PatternState
from core.pattern import Pattern, PatternMetadata


class TestTimingExact(unittest.TestCase):
    """Verify timing matches LMS exactly."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.width = 8
        self.height = 8
        metadata = PatternMetadata(width=self.width, height=self.height)
        pattern = Pattern(metadata=metadata, frames=[])
        self.state = PatternState(pattern)
        self.layer_manager = LayerManager(self.state)
    
    def test_step_calculation_exact(self):
        """Verify step calculation is frame-relative."""
        action = LayerAction(
            type="scroll",
            start_frame=10,
            end_frame=20,
            params={}
        )
        
        # Test cases: (frame_index, expected_step)
        test_cases = [
            (9, None),   # Before start
            (10, 0),     # At start
            (15, 5),     # Middle
            (20, 10),    # At end
            (21, None),  # After end
        ]
        
        for frame_idx, expected_step in test_cases:
            actual_step = get_action_step(action, frame_idx)
            self.assertEqual(
                actual_step,
                expected_step,
                f"Frame {frame_idx}: expected step {expected_step}, got {actual_step}"
            )
    
    def test_no_end_frame(self):
        """Verify action with no end_frame works correctly."""
        action = LayerAction(
            type="scroll",
            start_frame=5,
            end_frame=None,
            params={}
        )
        
        # Should work for any frame >= start_frame
        self.assertEqual(get_action_step(action, 5), 0)
        self.assertEqual(get_action_step(action, 100), 95)
        self.assertIsNone(get_action_step(action, 4))
    
    def test_scroll_timing_progression(self):
        """Verify scroll timing progresses correctly."""
        track_idx = self.layer_manager.add_layer_track("Timing Test")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        # Set frames at all indices we'll test
        for frame_idx in [4, 5, 6, 15]:
            frame = LayerFrame(pixels=pixels)
            track.set_frame(frame_idx, frame)
        
        # Scroll: 1 pixel per frame, starts at frame 5
        action = LayerAction(
            type="scroll",
            start_frame=5,
            end_frame=15,
            params={"direction": "right", "offset": 1}
        )
        track.add_automation(action)
        
        # Frame 4: action inactive, pixel at (0,0)
        frame4 = self.layer_manager.render_frame(4)
        self.assertEqual(frame4[0], (255, 255, 255), "Frame 4: action inactive")
        
        # Frame 5: step=0, pixel at (0,0)
        frame5 = self.layer_manager.render_frame(5)
        self.assertEqual(frame5[0], (255, 255, 255), "Frame 5: step=0")
        
        # Frame 6: step=1, pixel at (1,0)
        frame6 = self.layer_manager.render_frame(6)
        self.assertEqual(frame6[1], (255, 255, 255), "Frame 6: step=1")
        self.assertEqual(frame6[0], (0, 0, 0), "Frame 6: original position black")
        
        # Frame 15: step=10, pixel at (10,0) -> out of bounds, should be black
        frame15 = self.layer_manager.render_frame(15)
        self.assertEqual(frame15[0], (0, 0, 0), "Frame 15: out of bounds")
    
    def test_multiple_actions_timing(self):
        """Verify multiple actions with different timing work correctly."""
        track_idx = self.layer_manager.add_layer_track("Multi Action")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        # Set frames at all indices we'll test
        for frame_idx in [0, 3, 7, 12]:
            frame = LayerFrame(pixels=pixels)
            track.set_frame(frame_idx, frame)
        
        # Action 1: frames 0-5
        action1 = LayerAction(
            type="scroll",
            start_frame=0,
            end_frame=5,
            params={"direction": "right", "offset": 1}
        )
        
        # Action 2: frames 10-15
        action2 = LayerAction(
            type="scroll",
            start_frame=10,
            end_frame=15,
            params={"direction": "right", "offset": 1}
        )
        
        track.add_automation(action1)
        track.add_automation(action2)
        
        # Frame 3: only action1 active (step=3)
        frame3 = self.layer_manager.render_frame(3)
        self.assertEqual(frame3[3], (255, 255, 255), "Frame 3: action1 active")
        
        # Frame 7: no actions active
        frame7 = self.layer_manager.render_frame(7)
        self.assertEqual(frame7[0], (255, 255, 255), "Frame 7: no actions, original position")
        
        # Frame 12: only action2 active (step=2)
        frame12 = self.layer_manager.render_frame(12)
        self.assertEqual(frame12[2], (255, 255, 255), "Frame 12: action2 active")
    
    def test_timing_no_drift(self):
        """Verify timing doesn't drift or accumulate."""
        track_idx = self.layer_manager.add_layer_track("No Drift")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        # Set frames at all indices we'll test
        for frame_idx in [0, 3, 5, 7]:
            frame = LayerFrame(pixels=pixels)
            track.set_frame(frame_idx, frame)
        
        action = LayerAction(
            type="scroll",
            start_frame=0,
            end_frame=10,
            params={"direction": "right", "offset": 1}
        )
        track.add_automation(action)
        
        # Render frame 5 multiple times - should be identical
        frame5a = self.layer_manager.render_frame(5)
        frame5b = self.layer_manager.render_frame(5)
        frame5c = self.layer_manager.render_frame(5)
        
        self.assertEqual(frame5a, frame5b, "Frame 5: first and second render match")
        self.assertEqual(frame5b, frame5c, "Frame 5: second and third render match")
        
        # Render out of order - should still work
        frame3 = self.layer_manager.render_frame(3)
        frame7 = self.layer_manager.render_frame(7)
        frame3_again = self.layer_manager.render_frame(3)
        
        self.assertEqual(frame3, frame3_again, "Frame 3: out-of-order rendering works")
    
    def test_layer_window_timing(self):
        """Verify layer window blocks automation correctly."""
        track_idx = self.layer_manager.add_layer_track("Window Test")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        frame = LayerFrame(pixels=pixels)
        track.set_frame(5, frame)  # Frame only exists at frame 5
        track.start_frame = 5
        track.end_frame = 5
        
        # Add scroll action that matches layer window (starts at frame 5)
        # This ensures scroll step=0 at frame 5, so pixel stays at position 0
        action = LayerAction(
            type="scroll",
            start_frame=5,
            end_frame=5,
            params={"direction": "right", "offset": 1}
        )
        track.add_automation(action)
        
        # Frame 4: layer inactive
        frame4 = self.layer_manager.render_frame(4)
        self.assertEqual(frame4[0], (0, 0, 0), "Frame 4: layer inactive")
        
        # Frame 5: layer active, scroll step=0, pixel should be at position 0
        frame5 = self.layer_manager.render_frame(5)
        self.assertEqual(frame5[0], (255, 255, 255), "Frame 5: layer active, scroll step=0")


if __name__ == "__main__":
    unittest.main()
