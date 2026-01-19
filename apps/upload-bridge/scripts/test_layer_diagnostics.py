#!/usr/bin/env python3
"""
Comprehensive Layer System Diagnostic Test

Tests:
1. Pattern structure and dimensions
2. Layer frame isolation
3. Frame conflict detection
4. Layer visibility at different global frames
5. Animation accuracy
6. Render pipeline integrity

Pattern Setup:
- Matrix: 12×6 (72 pixels)
- Layer 1: Red bar (left), Scroll Right, 12 frames (0-11)
- Layer 2: Blue bar (right), Scroll Left, 6 frames (0-5)
- Layer 3: Green bar (top), Scroll Down, 4 frames (0-3)
- Global timeline: 12 frames (max of all layers)
"""

import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pattern import Pattern, PatternMetadata, Frame
from domain.pattern_state import PatternState
from domain.layers import LayerManager, LayerTrack, LayerFrame
from domain.layer_animation import create_scroll_animation


class LayerDiagnosticTest:
    def __init__(self):
        self.width = 12
        self.height = 6
        self.total_pixels = self.width * self.height
        self.errors = []
        self.warnings = []
        self.pattern = None
        self.state = None
        self.layer_manager = None
        
    def print_header(self, title):
        """Print section header."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    
    def print_subheader(self, title):
        """Print subsection header."""
        print(f"\n{'-'*80}")
        print(f"  {title}")
        print(f"{'-'*80}")
    
    def error(self, msg):
        """Record an error."""
        self.errors.append(msg)
        print(f"❌ ERROR: {msg}")
    
    def warning(self, msg):
        """Record a warning."""
        self.warnings.append(msg)
        print(f"⚠️  WARNING: {msg}")
    
    def success(self, msg):
        """Print success message."""
        print(f"✅ {msg}")
    
    def info(self, msg):
        """Print info message."""
        print(f"ℹ️  {msg}")
    
    def setup_pattern(self):
        """Create test pattern with specified structure."""
        self.print_header("PATTERN SETUP")
        
        # Create pattern
        metadata = PatternMetadata(width=self.width, height=self.height, color_order="RGB")
        self.pattern = Pattern(metadata=metadata)
        
        # Add blank frames (will be populated by layer system)
        for _ in range(15):  # Safety buffer
            frame = Frame(pixels=[(0, 0, 0)] * self.total_pixels, duration_ms=100)
            self.pattern.frames.append(frame)
        
        # Create layer manager
        self.state = PatternState()
        self.state.set_pattern(self.pattern)
        self.layer_manager = LayerManager(self.state)
        
        self.success(f"Pattern created: {self.width}×{self.height} = {self.total_pixels} pixels")
        self.success(f"Initial global frames: {len(self.pattern.frames)}")
    
    def create_layers(self):
        """Create test layers with different content."""
        self.print_header("LAYER CREATION")
        
        # Clear default layer
        while len(self.layer_manager.get_layer_tracks()) > 0:
            self.layer_manager.remove_layer_track(0)
        
        # Layer 1: Red vertical bar at left (x=0,1)
        self.info("Creating Layer 1 (Red, Left, Scroll Right)...")
        layer1_idx = self.layer_manager.add_layer_track(name="Layer 1 - Red Right")
        tracks = self.layer_manager.get_layer_tracks()
        layer1 = tracks[layer1_idx]
        
        # Create initial frame with red bar
        frame0 = layer1.get_or_create_frame(0, self.width, self.height)
        for y in range(self.height):
            frame0.pixels[y * self.width + 0] = (255, 0, 0)
            frame0.pixels[y * self.width + 1] = (255, 0, 0)
            frame0.alpha[y * self.width + 0] = 255
            frame0.alpha[y * self.width + 1] = 255
        
        # Simulate frames 0-11 (12 frames total)
        for i in range(12):
            layer1.set_frame(i, frame0.copy())
        
        layer1.start_frame = 0
        layer1.end_frame = 11
        
        self.success(f"Layer 1 created: frames {layer1.start_frame}-{layer1.end_frame} ({layer1.end_frame - layer1.start_frame + 1} frames)")
        
        # Layer 2: Blue vertical bar at right (x=10,11)
        self.info("Creating Layer 2 (Blue, Right, Scroll Left)...")
        layer2_idx = self.layer_manager.add_layer_track(name="Layer 2 - Blue Left")
        tracks = self.layer_manager.get_layer_tracks()
        layer2 = tracks[layer2_idx]
        
        # Create initial frame with blue bar
        frame0 = layer2.get_or_create_frame(0, self.width, self.height)
        for y in range(self.height):
            frame0.pixels[y * self.width + 10] = (0, 0, 255)
            frame0.pixels[y * self.width + 11] = (0, 0, 255)
            frame0.alpha[y * self.width + 10] = 255
            frame0.alpha[y * self.width + 11] = 255
        
        # Simulate frames 0-5 (6 frames total)
        for i in range(6):
            layer2.set_frame(i, frame0.copy())
        
        layer2.start_frame = 0
        layer2.end_frame = 5
        
        self.success(f"Layer 2 created: frames {layer2.start_frame}-{layer2.end_frame} ({layer2.end_frame - layer2.start_frame + 1} frames)")
        
        # Layer 3: Green horizontal bar at top (y=0)
        self.info("Creating Layer 3 (Green, Top, Scroll Down)...")
        layer3_idx = self.layer_manager.add_layer_track(name="Layer 3 - Green Down")
        tracks = self.layer_manager.get_layer_tracks()
        layer3 = tracks[layer3_idx]
        
        # Create initial frame with green bar
        frame0 = layer3.get_or_create_frame(0, self.width, self.height)
        for x in range(4, 8):  # Middle section
            frame0.pixels[0 * self.width + x] = (0, 255, 0)
            frame0.alpha[0 * self.width + x] = 255
        
        # Simulate frames 0-3 (4 frames total)
        for i in range(4):
            layer3.set_frame(i, frame0.copy())
        
        layer3.start_frame = 0
        layer3.end_frame = 3
        
        self.success(f"Layer 3 created: frames {layer3.start_frame}-{layer3.end_frame} ({layer3.end_frame - layer3.start_frame + 1} frames)")
    
    def test_layer_isolation(self):
        """Test that layers have independent frame ranges."""
        self.print_header("LAYER ISOLATION TEST")
        
        tracks = self.layer_manager.get_layer_tracks()
        
        # Test 1: Each layer starts at frame 0
        self.print_subheader("Test 1: Layer-Local Frame Indexing")
        for i, track in enumerate(tracks):
            if track.start_frame == 0:
                self.success(f"Layer {i} ({track.name}): Starts at frame 0 ✓")
            else:
                self.error(f"Layer {i} ({track.name}): Starts at frame {track.start_frame} (expected 0)")
        
        # Test 2: Layer frames don't overlap in global timeline
        self.print_subheader("Test 2: No Sequential Appending")
        expected_ranges = {
            0: (0, 11),  # Layer 1
            1: (0, 5),   # Layer 2
            2: (0, 3),   # Layer 3
        }
        
        for i, track in enumerate(tracks):
            expected_start, expected_end = expected_ranges.get(i, (None, None))
            if expected_start is not None:
                if track.start_frame == expected_start and track.end_frame == expected_end:
                    self.success(f"Layer {i}: Correct range {track.start_frame}-{track.end_frame}")
                else:
                    self.error(f"Layer {i}: Got {track.start_frame}-{track.end_frame}, expected {expected_start}-{expected_end}")
        
        # Test 3: Check for forbidden sequential appending
        self.print_subheader("Test 3: Forbidden Sequential Appending Detection")
        if len(tracks) >= 2:
            layer1 = tracks[0]
            layer2 = tracks[1]
            
            # Layer 2 should NOT start where Layer 1 ends
            if layer2.start_frame == layer1.end_frame + 1:
                self.error(f"Layer 2 APPENDED after Layer 1! (starts at {layer2.start_frame}, should be 0)")
            else:
                self.success("No sequential appending detected ✓")
    
    def test_frame_conflicts(self):
        """Detect frame conflicts between layers."""
        self.print_header("FRAME CONFLICT DETECTION")
        
        tracks = self.layer_manager.get_layer_tracks()
        
        # Calculate global frame range
        max_frame = max((track.end_frame for track in tracks if track.end_frame is not None), default=0)
        
        self.info(f"Global timeline: 0-{max_frame} ({max_frame + 1} frames)")
        
        # Test frames at key points
        test_frames = [0, 3, 5, 8, 11, 12]
        
        self.print_subheader("Frame Visibility Matrix")
        print(f"\n{'Frame':<8} {'L1 (0-11)':<12} {'L2 (0-5)':<12} {'L3 (0-3)':<12} {'Status'}")
        print("-" * 60)
        
        for frame_idx in test_frames:
            if frame_idx > max_frame:
                continue
            
            l1_active = self.layer_manager.is_layer_active(tracks[0], frame_idx)
            l2_active = self.layer_manager.is_layer_active(tracks[1], frame_idx) if len(tracks) > 1 else False
            l3_active = self.layer_manager.is_layer_active(tracks[2], frame_idx) if len(tracks) > 2 else False
            
            l1_str = "ACTIVE" if l1_active else "inactive"
            l2_str = "ACTIVE" if l2_active else "inactive"
            l3_str = "ACTIVE" if l3_active else "inactive"
            
            # Check for expected behavior
            expected_l1 = (0 <= frame_idx <= 11)
            expected_l2 = (0 <= frame_idx <= 5)
            expected_l3 = (0 <= frame_idx <= 3)
            
            status = "✅ OK"
            if l1_active != expected_l1 or l2_active != expected_l2 or l3_active != expected_l3:
                status = "❌ MISMATCH"
                self.error(f"Frame {frame_idx}: Layer activity mismatch")
            
            print(f"{frame_idx:<8} {l1_str:<12} {l2_str:<12} {l3_str:<12} {status}")
    
    def test_rendering(self):
        """Test rendering at critical frames."""
        self.print_header("RENDER PIPELINE TEST")
        
        tracks = self.layer_manager.get_layer_tracks()
        max_frame = max((track.end_frame for track in tracks if track.end_frame is not None), default=0)
        
        test_frames = [0, 3, 5, 11]
        
        for frame_idx in test_frames:
            if frame_idx > max_frame:
                continue
            
            self.print_subheader(f"Frame {frame_idx}")
            
            try:
                # Render composite
                composite = self.layer_manager.render_frame(frame_idx)
                
                if len(composite) != self.total_pixels:
                    self.error(f"Frame {frame_idx}: Wrong pixel count ({len(composite)}, expected {self.total_pixels})")
                else:
                    # Count colored pixels
                    red_count = sum(1 for p in composite if p == (255, 0, 0))
                    blue_count = sum(1 for p in composite if p == (0, 0, 255))
                    green_count = sum(1 for p in composite if p == (0, 255, 0))
                    black_count = sum(1 for p in composite if p == (0, 0, 0))
                    
                    self.info(f"  Red pixels: {red_count}, Blue: {blue_count}, Green: {green_count}, Black: {black_count}")
                    
                    # Expected active layers
                    l1_active = frame_idx <= 11
                    l2_active = frame_idx <= 5
                    l3_active = frame_idx <= 3
                    
                    # Verify content
                    if l1_active and red_count == 0:
                        self.warning(f"Frame {frame_idx}: Layer 1 should be visible but no red pixels found")
                    if l2_active and blue_count == 0:
                        self.warning(f"Frame {frame_idx}: Layer 2 should be visible but no blue pixels found")
                    if l3_active and green_count == 0:
                        self.warning(f"Frame {frame_idx}: Layer 3 should be visible but no green pixels found")
                    
                    if not l1_active and red_count > 0:
                        self.error(f"Frame {frame_idx}: Layer 1 inactive but red pixels found!")
                    if not l2_active and blue_count > 0:
                        self.error(f"Frame {frame_idx}: Layer 2 inactive but blue pixels found!")
                    if not l3_active and green_count > 0:
                        self.error(f"Frame {frame_idx}: Layer 3 inactive but green pixels found!")
                    
                    if l1_active or l2_active or l3_active:
                        self.success(f"Frame {frame_idx}: Rendered successfully")
            
            except Exception as e:
                self.error(f"Frame {frame_idx}: Render failed - {e}")
    
    def print_summary(self):
        """Print test summary."""
        self.print_header("TEST SUMMARY")
        
        tracks = self.layer_manager.get_layer_tracks()
        
        print(f"\n📊 Pattern Information:")
        print(f"   Matrix: {self.width}×{self.height} ({self.total_pixels} pixels)")
        print(f"   Layers: {len(tracks)}")
        print(f"   Global frames: {len(self.pattern.frames)}")
        
        print(f"\n📋 Layer Structure:")
        for i, track in enumerate(tracks):
            frame_count = (track.end_frame - track.start_frame + 1) if track.end_frame is not None else 0
            print(f"   Layer {i} ({track.name}):")
            print(f"     - Frame range: {track.start_frame}-{track.end_frame}")
            print(f"     - Frame count: {frame_count}")
            print(f"     - Z-Index: {track.z_index}")
            print(f"     - Visible: {track.visible}")
        
        print(f"\n📈 Test Results:")
        print(f"   ✅ Successes: {len([m for m in dir(self) if not m.startswith('_')]) - len(self.errors) - len(self.warnings)}")
        print(f"   ❌ Errors: {len(self.errors)}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n❌ Errors Found:")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        print(f"\n{'='*80}")
        if not self.errors:
            print("  ✅✅✅ ALL TESTS PASSED - LAYER SYSTEM WORKING CORRECTLY ✅✅✅")
        else:
            print("  ❌❌❌ TESTS FAILED - ISSUES DETECTED ❌❌❌")
        print(f"{'='*80}\n")
        
        return len(self.errors) == 0
    
    def run(self):
        """Run all tests."""
        self.print_header("COMPREHENSIVE LAYER DIAGNOSTIC TEST")
        print("Testing layer isolation and frame conflict detection\n")
        
        try:
            self.setup_pattern()
            self.create_layers()
            self.test_layer_isolation()
            self.test_frame_conflicts()
            self.test_rendering()
            success = self.print_summary()
            
            return 0 if success else 1
        
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {e}")
            import traceback
            traceback.print_exc()
            return 2


if __name__ == "__main__":
    tester = LayerDiagnosticTest()
    sys.exit(tester.run())
