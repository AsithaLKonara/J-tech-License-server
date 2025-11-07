"""
Media Upload Demo - Demonstrate image, GIF, and video conversion to LED patterns
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from core.media_converter import MediaConverter
from core.pattern import Pattern


def demo_media_conversion():
    """Demonstrate media conversion capabilities"""
    
    print("🎬 Upload Bridge - Media Conversion Demo")
    print("=" * 50)
    
    converter = MediaConverter()
    
    # Show supported formats
    print("\n📁 Supported Formats:")
    formats = converter.get_supported_formats()
    print(f"   Images: {', '.join(formats['images'])}")
    print(f"   Videos: {', '.join(formats['videos'])}")
    
    # Demo conversion settings
    print("\n⚙️ Conversion Settings:")
    print("   Target Dimensions: 64x32 (2048 LEDs)")
    print("   FPS: 30")
    print("   Brightness: 80%")
    print("   Color Order: RGB")
    
    # Example conversion (would work with actual files)
    print("\n🔄 Example Conversion Process:")
    print("   1. Load media file (image/GIF/video)")
    print("   2. Analyze dimensions and frame count")
    print("   3. Resize to target LED matrix size")
    print("   4. Apply brightness and color order")
    print("   5. Generate LED pattern frames")
    print("   6. Create Pattern object")
    print("   7. Ready for preview and flashing!")
    
    # Conversion tips
    print("\n💡 Conversion Tips:")
    print("   • High contrast images work best")
    print("   • Shorter videos (under 10s) recommended")
    print("   • GIFs with fewer colors convert faster")
    print("   • Test with small dimensions first")
    print("   • Adjust brightness for your LED strip")
    
    # Usage instructions
    print("\n🚀 How to Use:")
    print("   1. Launch Upload Bridge")
    print("   2. Go to '🎬 Media Upload' tab")
    print("   3. Click 'Select Media File'")
    print("   4. Choose your image/GIF/video")
    print("   5. Adjust conversion settings")
    print("   6. Preview the result")
    print("   7. Click 'Convert to LED Pattern'")
    print("   8. Load pattern and flash to device!")
    
    print("\n✅ Media conversion system ready!")
    print("   Upload Bridge now supports:")
    print("   • Static images → LED patterns")
    print("   • Animated GIFs → LED animations")
    print("   • Videos → LED video sequences")
    print("   • Real-time preview and controls")
    print("   • Custom dimensions and settings")


if __name__ == "__main__":
    demo_media_conversion()

