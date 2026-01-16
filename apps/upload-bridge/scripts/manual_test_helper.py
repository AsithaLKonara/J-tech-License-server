#!/usr/bin/env python3
"""
Manual Testing Helper Script

This script provides utilities to help with manual testing of layer features.
It can create test patterns, verify states, and provide testing guidance.

Usage:
    python scripts/manual_test_helper.py --scenario 1
    python scripts/manual_test_helper.py --create-test-pattern
    python scripts/manual_test_helper.py --verify-layer-state
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pattern import Pattern, Frame, PatternMetadata


def print_scenario_guide(scenario_num: int):
    """Print step-by-step guide for a test scenario."""
    scenarios = {
        1: {
            "name": "Automation Layer Creation",
            "steps": [
                "Launch application: python main.py",
                "Create new pattern (8x8 or larger)",
                "Paint something on canvas",
                "Go to Automation tab",
                "Add 'Scroll Left' action to queue",
                "Click 'Process Queue'",
                "Check Layers tab for new 'Auto: Scroll Left' layer",
                "Verify original layer still exists",
                "Toggle automation layer visibility",
                "Verify frame shows composite correctly"
            ],
            "success_criteria": [
                "New 'Auto:' layer created",
                "Original layer preserved",
                "Composite works correctly"
            ]
        },
        2: {
            "name": "Layer Sync Warning",
            "steps": [
                "Create pattern and paint on layer",
                "Apply automation (creates new layer)",
                "Check if sync warning banner appears",
                "Verify warning message: '⚠️ Layers are out of sync with frame X'",
                "Click 'Sync Layers' button",
                "Verify confirmation dialog appears",
                "Confirm sync action",
                "Verify warning disappears after sync",
                "Verify layers are now in sync"
            ],
            "success_criteria": [
                "Warning appears",
                "Sync button works",
                "Warning clears after sync"
            ]
        },
        3: {
            "name": "Brush Broadcast Feedback",
            "steps": [
                "Create pattern with 3+ frames",
                "Paint different content on each frame",
                "Enable 'Apply brush strokes to all frames' checkbox",
                "Verify warning dialog appears on first enable",
                "Test cancel (checkbox stays unchecked)",
                "Enable broadcast mode (click 'Yes')",
                "Verify all frames highlighted in timeline (yellow/orange)",
                "Verify checkbox shows red border and warning icon",
                "Verify warning banner appears at top",
                "Paint on one frame, verify all frames update"
            ],
            "success_criteria": [
                "Warning dialog appears",
                "Frame highlighting works",
                "Visual indicators present",
                "Broadcast works correctly"
            ]
        },
        4: {
            "name": "Hidden Layer Prevention",
            "steps": [
                "Create pattern with multiple layers",
                "Hide a layer (click eye icon)",
                "Select the hidden layer",
                "Try to paint on canvas",
                "Verify dialog: 'Cannot paint on hidden layer'",
                "Make layer visible",
                "Verify painting works on visible layer"
            ],
            "success_criteria": [
                "Hidden layer painting blocked",
                "Clear error message",
                "Works when visible"
            ]
        },
        5: {
            "name": "Copy Layer to Frames",
            "steps": [
                "Create pattern with 3+ frames",
                "Add custom layer to frame 0",
                "Paint something on this layer",
                "Right-click layer in layer panel",
                "Verify 'Copy Layer to Frame' option exists in context menu",
                "Select option, choose target frames (1, 2)",
                "Click 'Copy'",
                "Verify layer copied to selected frames",
                "Verify original layer unchanged",
                "Verify copied layers have same pixels"
            ],
            "success_criteria": [
                "Context menu option exists",
                "Copy works correctly",
                "Pixels match",
                "Original preserved"
            ]
        },
        6: {
            "name": "Multiple Automation Layers",
            "steps": [
                "Create pattern",
                "Apply first automation (scroll)",
                "Apply second automation (rotate)",
                "Apply third automation (mirror)",
                "Verify all automation layers exist in Layers tab",
                "Verify can toggle each independently",
                "Verify composite shows all layers correctly"
            ],
            "success_criteria": [
                "Multiple automation layers coexist",
                "Independent toggling works",
                "Correct composite"
            ]
        },
        7: {
            "name": "Edge Cases",
            "steps": [
                "Test with single frame pattern",
                "Test with single layer",
                "Test with many layers (10+)",
                "Test with large pattern (64x64)",
                "Test undo/redo after automation",
                "Test save/load with automation layers",
                "Test copy layer to same frame (should skip)"
            ],
            "success_criteria": [
                "All edge cases handled gracefully",
                "No crashes"
            ]
        }
    }
    
    if scenario_num not in scenarios:
        print(f"Unknown scenario number: {scenario_num}")
        print(f"Available scenarios: {list(scenarios.keys())}")
        return
    
    scenario = scenarios[scenario_num]
    print("=" * 70)
    print(f"Scenario {scenario_num}: {scenario['name']}")
    print("=" * 70)
    print()
    print("Steps:")
    for i, step in enumerate(scenario['steps'], 1):
        print(f"  {i}. {step}")
    print()
    print("Success Criteria:")
    for i, criterion in enumerate(scenario['success_criteria'], 1):
        print(f"  {i}. {criterion}")
    print()
    print("=" * 70)


def create_test_pattern(width: int = 8, height: int = 8, num_frames: int = 3, filename: str = None):
    """Create a test pattern file for manual testing."""
    if filename is None:
        filename = f"test_pattern_{width}x{height}_{num_frames}frames.leds"
    
    metadata = PatternMetadata(width=width, height=height)
    frames = []
    for i in range(num_frames):
        pixels = [(i * 10, i * 20, i * 30)] * (width * height)
        frame = Frame(pixels=pixels, duration_ms=100)
        frames.append(frame)
    
    pattern = Pattern(name=f"Test Pattern {width}x{height}", metadata=metadata, frames=frames)
    
    # Save pattern (you would need to implement pattern saving here)
    print(f"Test pattern created: {width}x{height}, {num_frames} frames")
    print(f"Pattern name: {pattern.name}")
    print(f"Total pixels per frame: {width * height}")
    print()
    print("Note: This is a helper script. Actual pattern saving would need to be implemented.")
    print("You can create patterns manually in the application for testing.")


def main():
    parser = argparse.ArgumentParser(description="Manual Testing Helper")
    parser.add_argument("--scenario", type=int, help="Print guide for scenario number (1-7)")
    parser.add_argument("--create-test-pattern", action="store_true", help="Create a test pattern")
    parser.add_argument("--width", type=int, default=8, help="Pattern width (default: 8)")
    parser.add_argument("--height", type=int, default=8, help="Pattern height (default: 8)")
    parser.add_argument("--frames", type=int, default=3, help="Number of frames (default: 3)")
    parser.add_argument("--list-scenarios", action="store_true", help="List all available scenarios")
    
    args = parser.parse_args()
    
    if args.list_scenarios:
        print("Available Test Scenarios:")
        print("  1. Automation Layer Creation")
        print("  2. Layer Sync Warning")
        print("  3. Brush Broadcast Feedback")
        print("  4. Hidden Layer Prevention")
        print("  5. Copy Layer to Frames")
        print("  6. Multiple Automation Layers")
        print("  7. Edge Cases")
        return
    
    if args.scenario:
        print_scenario_guide(args.scenario)
    elif args.create_test_pattern:
        create_test_pattern(args.width, args.height, args.frames)
    else:
        parser.print_help()
        print()
        print("Quick start:")
        print("  python scripts/manual_test_helper.py --scenario 1")
        print("  python scripts/manual_test_helper.py --list-scenarios")


if __name__ == "__main__":
    main()

