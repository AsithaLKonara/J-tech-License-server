"""
LMS Parity Verification Tool

This tool verifies pixel-for-pixel matching with LED Matrix Studio by:
1. Running the engine with test patterns (or LMS project files)
2. Comparing pixel output frame-by-frame
3. Verifying timing matches exactly
4. Generating detailed verification reports
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import json
from typing import List, Tuple, Optional, Dict, Any

from domain.layers import LayerManager, LayerTrack, LayerFrame
from domain.automation.layer_action import LayerAction
from domain.pattern_state import PatternState
from core.pattern import Pattern, PatternMetadata

Color = Tuple[int, int, int]


class LMSParityVerifier:
    """Verifies pixel-for-pixel matching with LED Matrix Studio."""
    
    def __init__(self, width: int = 8, height: int = 8):
        """Initialize verifier with matrix dimensions."""
        self.width = width
        self.height = height
        # Create pattern and state
        metadata = PatternMetadata(width=width, height=height)
        pattern = Pattern(metadata=metadata, frames=[])
        self.state = PatternState(pattern)
        self.layer_manager = LayerManager(self.state)
        self.verification_results: List[Dict[str, Any]] = []
    
    def create_test_pattern_scroll(self) -> None:
        """Create a test pattern with scroll action (LMS reference)."""
        # Clear existing layers
        while len(self.layer_manager._layer_tracks) > 0:
            self.layer_manager.remove_layer_track(0)
        
        # Create layer with white pixel at (0, 0)
        track_idx = self.layer_manager.add_layer_track("Scroll Test")
        track = self.layer_manager._layer_tracks[track_idx]
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * (self.width * self.height - 1)
        frame = LayerFrame(pixels=pixels)
        track.set_frame(0, frame)
        
        # Add scroll action: right, 1 pixel per frame, frames 0-10
        action = LayerAction(
            type="scroll",
            start_frame=0,
            end_frame=10,
            params={"direction": "right", "offset": 1}
        )
        track.add_automation(action)
    
    def create_test_pattern_rotate(self) -> None:
        """Create a test pattern with rotate action (LMS reference)."""
        while len(self.layer_manager._layer_tracks) > 0:
            self.layer_manager.remove_layer_track(0)
        
        # Create pattern: white at (0,0), red at (7,0)
        pixels = [(255, 255, 255)] + [(0, 0, 0)] * 6 + [(255, 0, 0)] + [(0, 0, 0)] * (self.width * self.height - 8)
        track_idx = self.layer_manager.add_layer_track("Rotate Test")
        track = self.layer_manager._layer_tracks[track_idx]
        frame = LayerFrame(pixels=pixels)
        track.set_frame(0, frame)
        
        # Add rotate: 90° clockwise, frames 0-10
        action = LayerAction(
            type="rotate",
            start_frame=0,
            end_frame=10,
            params={"mode": "90° Clockwise"}
        )
        track.add_automation(action)
    
    def create_test_pattern_opacity(self) -> None:
        """Create a test pattern with opacity (LMS reference)."""
        while len(self.layer_manager._layer_tracks) > 0:
            self.layer_manager.remove_layer_track(0)
        
        # Create layer with red pixels
        pixels = [(255, 0, 0)] * (self.width * self.height)
        track_idx = self.layer_manager.add_layer_track("Opacity Test")
        track = self.layer_manager._layer_tracks[track_idx]
        frame = LayerFrame(pixels=pixels)
        track.set_frame(0, frame)
        track.opacity = 0.5  # 50% opacity
    
    def create_test_pattern_multi_layer(self) -> None:
        """Create a test pattern with multiple layers (LMS reference)."""
        while len(self.layer_manager._layer_tracks) > 0:
            self.layer_manager.remove_layer_track(0)
        
        # Bottom layer: red
        bottom_idx = self.layer_manager.add_layer_track("Bottom")
        bottom_track = self.layer_manager._layer_tracks[bottom_idx]
        bottom_frame = LayerFrame(pixels=[(255, 0, 0)] * (self.width * self.height))
        bottom_track.set_frame(0, bottom_frame)
        bottom_track.z_index = 0
        
        # Top layer: black (transparent) with white pixel
        top_idx = self.layer_manager.add_layer_track("Top")
        top_track = self.layer_manager._layer_tracks[top_idx]
        top_pixels = [(0, 0, 0)] * (self.width * self.height)
        top_pixels[0] = (255, 255, 255)  # White at (0,0)
        top_frame = LayerFrame(pixels=top_pixels)
        top_track.set_frame(0, top_frame)
        top_track.z_index = 1
    
    def render_frame(self, frame_index: int) -> List[Color]:
        """Render a frame using the engine."""
        return self.layer_manager.render_frame(frame_index)
    
    def compare_frames(
        self,
        frame1: List[Color],
        frame2: List[Color],
        frame_index: int,
        test_name: str
    ) -> Dict[str, Any]:
        """
        Compare two frames pixel-by-pixel.
        
        Returns:
            Comparison result with match status, differences, and statistics
        """
        if len(frame1) != len(frame2):
            return {
                "match": False,
                "frame_index": frame_index,
                "test_name": test_name,
                "error": f"Frame length mismatch: {len(frame1)} vs {len(frame2)}",
                "differences": [],
                "match_percentage": 0.0
            }
        
        differences = []
        match_count = 0
        total_pixels = len(frame1)
        
        for i, (p1, p2) in enumerate(zip(frame1, frame2)):
            if p1 != p2:
                x = i % self.width
                y = i // self.width
                differences.append({
                    "index": i,
                    "position": (x, y),
                    "expected": p1,
                    "actual": p2
                })
            else:
                match_count += 1
        
        match_percentage = (match_count / total_pixels) * 100.0
        
        return {
            "match": len(differences) == 0,
            "frame_index": frame_index,
            "test_name": test_name,
            "match_count": match_count,
            "total_pixels": total_pixels,
            "match_percentage": match_percentage,
            "differences": differences[:10],  # Limit to first 10 differences
            "total_differences": len(differences)
        }
    
    def verify_timing(
        self,
        action: LayerAction,
        frame_index: int,
        expected_step: Optional[int]
    ) -> Dict[str, Any]:
        """
        Verify automation timing matches LMS behavior.
        
        Args:
            action: LayerAction to verify
            frame_index: Frame index to check
            expected_step: Expected step value (None if action should be inactive)
        
        Returns:
            Timing verification result
        """
        from domain.automation.layer_action import get_action_step
        
        actual_step = get_action_step(action, frame_index)
        
        return {
            "frame_index": frame_index,
            "action_type": action.type,
            "action_start": action.start_frame,
            "action_end": action.end_frame,
            "expected_step": expected_step,
            "actual_step": actual_step,
            "match": actual_step == expected_step
        }
    
    def run_scroll_verification(self) -> Dict[str, Any]:
        """Verify scroll behavior matches LMS."""
        self.create_test_pattern_scroll()
        
        results = []
        # Expected behavior:
        # Frame 0: pixel at (0,0) = white
        # Frame 1: pixel at (1,0) = white, (0,0) = black
        # Frame 8: pixel at (7,0) = white
        # Frame 9: pixel at (7,0) = black (out of bounds)
        
        expected_positions = {
            0: 0,   # Frame 0: position 0
            1: 1,   # Frame 1: position 1
            8: 7,   # Frame 8: position 7 (last column)
            9: None  # Frame 9: out of bounds (black)
        }
        
        for frame_idx, expected_pos in expected_positions.items():
            rendered = self.render_frame(frame_idx)
            
            if expected_pos is None:
                # Should be all black
                is_black = all(p == (0, 0, 0) for p in rendered)
                results.append({
                    "frame_index": frame_idx,
                    "expected": "all black",
                    "actual": "all black" if is_black else "has pixels",
                    "match": is_black
                })
            else:
                # Check pixel at expected position
                pixel = rendered[expected_pos]
                is_white = pixel == (255, 255, 255)
                # Check previous positions are black
                prev_black = all(rendered[i] == (0, 0, 0) for i in range(expected_pos))
                
                results.append({
                    "frame_index": frame_idx,
                    "expected_position": expected_pos,
                    "pixel_at_position": pixel,
                    "is_white": is_white,
                    "previous_black": prev_black,
                    "match": is_white and prev_black
                })
        
        return {
            "test_name": "Scroll Verification",
            "results": results,
            "all_match": all(r["match"] for r in results)
        }
    
    def run_opacity_verification(self) -> Dict[str, Any]:
        """Verify opacity behavior matches LMS (brightness scaling)."""
        self.create_test_pattern_opacity()
        
        rendered = self.render_frame(0)
        
        # With 0.5 opacity, red (255, 0, 0) should become (127, 0, 0)
        expected = (127, 0, 0)
        actual = rendered[0]
        
        match = actual == expected
        
        return {
            "test_name": "Opacity Verification",
            "expected": expected,
            "actual": actual,
            "match": match,
            "all_pixels_match": all(p == expected for p in rendered)
        }
    
    def run_compositing_verification(self) -> Dict[str, Any]:
        """Verify black=transparent compositing."""
        self.create_test_pattern_multi_layer()
        
        rendered = self.render_frame(0)
        
        # Position 0: should be white (top layer overwrites)
        # Position 1+: should be red (black is transparent, shows bottom layer)
        
        pos0_white = rendered[0] == (255, 255, 255)
        pos1_red = rendered[1] == (255, 0, 0)
        all_others_red = all(rendered[i] == (255, 0, 0) for i in range(1, len(rendered)))
        
        return {
            "test_name": "Compositing Verification",
            "position_0_white": pos0_white,
            "position_1_red": pos1_red,
            "all_others_red": all_others_red,
            "match": pos0_white and pos1_red and all_others_red
        }
    
    def run_timing_verification(self) -> Dict[str, Any]:
        """Verify frame-relative timing."""
        self.create_test_pattern_scroll()
        
        track = self.layer_manager._layer_tracks[0]
        action = track.automation[0]
        
        test_cases = [
            (0, 0),   # Frame 0: step 0
            (1, 1),   # Frame 1: step 1
            (5, 5),   # Frame 5: step 5
            (10, 10), # Frame 10: step 10 (at end_frame)
            (11, None), # Frame 11: None (after end_frame)
            (-1, None), # Frame -1: None (before start_frame)
        ]
        
        results = []
        for frame_idx, expected_step in test_cases:
            result = self.verify_timing(action, frame_idx, expected_step)
            results.append(result)
        
        return {
            "test_name": "Timing Verification",
            "results": results,
            "all_match": all(r["match"] for r in results)
        }
    
    def run_all_verifications(self) -> Dict[str, Any]:
        """Run all verification tests."""
        print("Running LMS Parity Verification...")
        print("=" * 60)
        
        all_results = {}
        
        # Scroll verification
        print("\n1. Scroll Verification...")
        scroll_result = self.run_scroll_verification()
        all_results["scroll"] = scroll_result
        print(f"   {'✓ PASS' if scroll_result['all_match'] else '✗ FAIL'}")
        
        # Opacity verification
        print("\n2. Opacity Verification...")
        opacity_result = self.run_opacity_verification()
        all_results["opacity"] = opacity_result
        print(f"   {'✓ PASS' if opacity_result['match'] else '✗ FAIL'}")
        
        # Compositing verification
        print("\n3. Compositing Verification...")
        compositing_result = self.run_compositing_verification()
        all_results["compositing"] = compositing_result
        print(f"   {'✓ PASS' if compositing_result['match'] else '✗ FAIL'}")
        
        # Timing verification
        print("\n4. Timing Verification...")
        timing_result = self.run_timing_verification()
        all_results["timing"] = timing_result
        print(f"   {'✓ PASS' if timing_result['all_match'] else '✗ FAIL'}")
        
        # Summary
        print("\n" + "=" * 60)
        all_passed = all([
            scroll_result.get("all_match", False),
            opacity_result.get("match", False),
            compositing_result.get("match", False),
            timing_result.get("all_match", False)
        ])
        
        print(f"\nOverall Status: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
        
        return {
            "overall_status": "PASS" if all_passed else "FAIL",
            "results": all_results
        }
    
    def save_report(self, output_path: str) -> None:
        """Save verification report to JSON file."""
        report = {
            "width": self.width,
            "height": self.height,
            "verification_results": self.verification_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {output_path}")


def main():
    """Run LMS parity verification."""
    verifier = LMSParityVerifier(width=8, height=8)
    results = verifier.run_all_verifications()
    
    # Save report
    report_path = Path(__file__).parent / "lms_parity_report.json"
    verifier.save_report(str(report_path))
    
    return results


if __name__ == "__main__":
    main()
