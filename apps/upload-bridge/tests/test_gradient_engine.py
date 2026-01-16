
import sys
import os
from pathlib import Path

# Add project root to sys.path
# File is in apps/upload-bridge/tests/test_gradient_engine.py
# We want apps/upload-bridge in sys.path
app_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, app_root)
print(f"App root: {app_root}")

from core.gradient import Gradient, GradientStop, GradientType, GradientRenderer, create_simple_gradient

def test_gradient_engine():
    print("Testing Gradient Engine...")
    
    # Test simple gradient
    grad = create_simple_gradient((255, 0, 0), (0, 0, 255))
    assert grad.get_color_at(0.0) == (255, 0, 0)
    assert grad.get_color_at(1.0) == (0, 0, 255)
    
    mid = grad.get_color_at(0.5)
    print(f"Mid color (Red -> Blue): {mid}")
    assert mid[0] == 127
    assert mid[1] == 0
    assert mid[2] == 127
    
    # Test multi-stop
    grad.add_stop(0.5, (0, 255, 0))
    assert grad.get_color_at(0.0) == (255, 0, 0)
    assert grad.get_color_at(0.5) == (0, 255, 0)
    assert grad.get_color_at(1.0) == (0, 0, 255)
    
    print("Multi-stop interpolation test passed.")
    
    # Test rendering
    grid = GradientRenderer.render_linear(grad, 16, 1, 0, 0, 15, 0)
    assert len(grid) == 1
    assert len(grid[0]) == 16
    assert grid[0][0] == (255, 0, 0)
    assert grid[0][15] == (0, 0, 255)
    
    print("Linear rendering test passed.")
    
    # Test radial rendering
    grid_radial = GradientRenderer.render_radial(grad, 16, 16, 8, 8, 8)
    assert grid_radial[8][8] == (255, 0, 0) # Center
    
    print("Radial rendering test passed.")
    print("All Gradient Engine tests PASSED!")

if __name__ == "__main__":
    try:
        test_gradient_engine()
    except Exception as e:
        print(f"Test FAILED: {e}")
        sys.exit(1)
