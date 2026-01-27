"""
Pattern Templates - Library of common LED matrix patterns

Provides pre-built templates for common animations and effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import math
import random
from PIL import Image, ImageDraw, ImageFont

from core.pattern import Pattern, Frame, PatternMetadata

RGB = Tuple[int, int, int]

# Simple 5x7 Font Bitmaps (Column-major)
BASIC_FONT = {
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
    '"': [0x00, 0x07, 0x00, 0x07, 0x00],
    '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
    '$': [0x24, 0x2A, 0x7F, 0x2A, 0x12],
    '%': [0x23, 0x13, 0x08, 0x64, 0x62],
    '&': [0x36, 0x49, 0x55, 0x22, 0x50],
    '\'': [0x00, 0x05, 0x03, 0x00, 0x00],
    '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
    ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
    '*': [0x14, 0x08, 0x3E, 0x08, 0x14],
    '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
    ',': [0x00, 0x50, 0x30, 0x00, 0x00],
    '-': [0x08, 0x08, 0x08, 0x08, 0x08],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00],
    '/': [0x20, 0x10, 0x08, 0x04, 0x02],
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
    '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],
    '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],
    '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],
    ';': [0x00, 0x56, 0x36, 0x00, 0x00],
    '<': [0x08, 0x14, 0x22, 0x41, 0x00],
    '=': [0x14, 0x14, 0x14, 0x14, 0x14],
    '>': [0x00, 0x41, 0x22, 0x14, 0x08],
    '?': [0x02, 0x01, 0x51, 0x09, 0x06],
    '@': [0x32, 0x49, 0x79, 0x41, 0x3E],
    'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],
    'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
    'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
    'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
    'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
    'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
    'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
    'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
    'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
    'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
    'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
}


class TemplateCategory(Enum):
    """Template categories."""
    ANIMATION = "Animation"
    EFFECT = "Effect"
    TEXT = "Text"
    GAME = "Game"
    BUDURASMALA = "Budurasmala"


@dataclass
class PatternTemplate:
    """Pattern template definition."""
    name: str
    category: TemplateCategory
    description: str
    parameters: Dict[str, Any]
    generator: callable


class TemplateLibrary:
    """Library of pattern templates."""
    
    def __init__(self):
        self.templates: List[PatternTemplate] = []
        self._register_templates()
    
    def _register_templates(self):
        """Register all built-in templates."""
        # Scrolling Text
        self.templates.append(PatternTemplate(
            name="Scrolling Text",
            category=TemplateCategory.TEXT,
            description="Text scrolling across the matrix",
            parameters={
                "text": "HELLO",
                "speed": 1,
                "color": (255, 0, 0),
                "direction": "left",
                "font_size": 10,
                "font_name": "arial.ttf"
            },
            generator=self._generate_scrolling_text
        ))
        
        # Bouncing Ball
        self.templates.append(PatternTemplate(
            name="Bouncing Ball",
            category=TemplateCategory.ANIMATION,
            description="A ball that bounces around the matrix",
            parameters={
                "color": (255, 100, 0),
                "frames": 30,
                "speed": 1.0
            },
            generator=self._generate_bouncing_ball
        ))
        
        # Fire Effect
        self.templates.append(PatternTemplate(
            name="Fire Effect",
            category=TemplateCategory.EFFECT,
            description="Animated fire/flame effect",
            parameters={
                "intensity": 0.8,
                "frames": 20
            },
            generator=self._generate_fire
        ))
        
        # Rain Effect
        self.templates.append(PatternTemplate(
            name="Rain Effect",
            category=TemplateCategory.EFFECT,
            description="Falling rain animation",
            parameters={
                "drops": 10,
                "color": (0, 100, 255),
                "frames": 30
            },
            generator=self._generate_rain
        ))
        
        # Matrix Rain
        self.templates.append(PatternTemplate(
            name="Matrix Rain",
            category=TemplateCategory.EFFECT,
            description="Matrix-style falling characters",
            parameters={
                "columns": 8,
                "speed": 2,
                "frames": 40
            },
            generator=self._generate_matrix_rain
        ))
        
        # Clock
        self.templates.append(PatternTemplate(
            name="Clock",
            category=TemplateCategory.TEXT,
            description="Digital clock display",
            parameters={
                "format": "12h",
                "color": (0, 255, 0),
                "frames": 60,
                "font_size": 10,
                "font_name": "arial.ttf"
            },
            generator=self._generate_clock
        ))
        
        # Weather Display
        self.templates.append(PatternTemplate(
            name="Weather Display",
            category=TemplateCategory.TEXT,
            description="Weather information display",
            parameters={
                "temperature": 72,
                "condition": "sunny",
                "frames": 60,
                "font_size": 10
            },
            generator=self._generate_weather
        ))
        
        # Color Cycle
        self.templates.append(PatternTemplate(
            name="Color Cycle",
            category=TemplateCategory.EFFECT,
            description="Smooth color cycling animation",
            parameters={
                "speed": 1.0,
                "frames": 60,
                "hue_start": 0.0,
                "saturation": 1.0,
                "brightness": 1.0
            },
            generator=self._generate_color_cycle
        ))
        
        # Wave
        self.templates.append(PatternTemplate(
            name="Wave",
            category=TemplateCategory.ANIMATION,
            description="Animated wave pattern",
            parameters={
                "color": (0, 150, 255),
                "frames": 40,
                "frequency": 2.0,
                "amplitude": 0.5
            },
            generator=self._generate_wave
        ))
        
        # Spiral
        self.templates.append(PatternTemplate(
            name="Spiral",
            category=TemplateCategory.ANIMATION,
            description="Rotating spiral animation",
            parameters={
                "color": (255, 255, 0),
                "frames": 30,
                "speed": 1.0,
                "thickness": 1
            },
            generator=self._generate_spiral
        ))
        
        # Pulse
        self.templates.append(PatternTemplate(
            name="Pulse",
            category=TemplateCategory.EFFECT,
            description="Pulsing center animation",
            parameters={
                "color": (255, 0, 0),
                "frames": 20,
                "speed": 1.0,
                "center_x": 0.5,
                "center_y": 0.5
            },
            generator=self._generate_pulse
        ))
        
        # Fade
        self.templates.append(PatternTemplate(
            name="Fade",
            category=TemplateCategory.EFFECT,
            description="Fade in/out effect",
            parameters={
                "color": (255, 255, 255),
                "frames": 30,
                "fade_type": "in_out"
            },
            generator=self._generate_fade
        ))
        
        # Random
        self.templates.append(PatternTemplate(
            name="Random Pixels",
            category=TemplateCategory.EFFECT,
            description="Random pixel twinkling",
            parameters={
                "density": 0.1,
                "frames": 30,
                "color": (255, 255, 255)
            },
            generator=self._generate_random
        ))
        
        # Budurasmala Templates
        # Ray Rotation
        self.templates.append(PatternTemplate(
            name="Ray Rotation",
            category=TemplateCategory.BUDURASMALA,
            description="Rotating rays around center (Budurasmala)",
            parameters={
                "speed": 2.0,
                "color": (255, 255, 0),
                "ray_count": 8,
                "frames": 30
            },
            generator=self._generate_ray_rotation
        ))
        
        # Pulsing Halo
        self.templates.append(PatternTemplate(
            name="Pulsing Halo",
            category=TemplateCategory.BUDURASMALA,
            description="Expanding and contracting rings (Budurasmala)",
            parameters={
                "ring_count": 3,
                "pulse_speed": 1.0,
                "color": (255, 200, 0),
                "frames": 40
            },
            generator=self._generate_pulsing_halo
        ))
        
        # Twinkling Stars
        self.templates.append(PatternTemplate(
            name="Twinkling Stars",
            category=TemplateCategory.BUDURASMALA,
            description="Random LEDs twinkling (Budurasmala)",
            parameters={
                "density": 0.15,
                "twinkle_speed": 3.0,
                "color": (255, 255, 255),
                "frames": 50
            },
            generator=self._generate_twinkling_stars
        ))
        
        # Wave Propagation
        self.templates.append(PatternTemplate(
            name="Wave Propagation",
            category=TemplateCategory.BUDURASMALA,
            description="Wave moving around circle (Budurasmala)",
            parameters={
                "wave_count": 2,
                "speed": 2.0,
                "color": (0, 150, 255),
                "frames": 60
            },
            generator=self._generate_wave_propagation
        ))
        
        # Color Gradient Rotation
        self.templates.append(PatternTemplate(
            name="Color Gradient Rotation",
            category=TemplateCategory.BUDURASMALA,
            description="Rotating color gradient pattern (Budurasmala)",
            parameters={
                "gradient_colors": [(255, 0, 0), (0, 255, 0), (0, 0, 255)],
                "rotation_speed": 1.5,
                "frames": 40
            },
            generator=self._generate_color_gradient_rotation
        ))
    
        # Cultural Patterns (Phase 3)
        # Lotus Pattern
        self.templates.append(PatternTemplate(
            name="Lotus Pattern",
            category=TemplateCategory.BUDURASMALA,
            description="Lotus flower pattern (Buddhist symbolism)",
            parameters={
                "color": (255, 215, 0),  # Gold
                "frames": 30
            },
            generator=self._generate_lotus_pattern
        ))
        
        # Dharma Wheel
        self.templates.append(PatternTemplate(
            name="Dharma Wheel",
            category=TemplateCategory.BUDURASMALA,
            description="Dharma wheel pattern (Buddhist symbolism)",
            parameters={
                "color": (255, 255, 255),  # White
                "frames": 40
            },
            generator=self._generate_dharma_wheel
        ))
        
        # Vesak Stars
        self.templates.append(PatternTemplate(
            name="Vesak Stars",
            category=TemplateCategory.BUDURASMALA,
            description="Traditional Vesak festival stars pattern",
            parameters={
                "color": (255, 215, 0),  # Gold
                "frames": 50
            },
            generator=self._generate_vesak_stars
        ))
    
    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[PatternTemplate]:
        """List all templates, optionally filtered by category."""
        if category:
            return [t for t in self.templates if t.category == category]
        return self.templates
    
    def get_template(self, name: str) -> Optional[PatternTemplate]:
        """Get template by name."""
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def generate_pattern(self, template_name: str, width: int, height: int, **kwargs) -> Pattern:
        """Generate a pattern from a template."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Merge parameters - remove width/height from kwargs if present to avoid conflicts
        params = template.parameters.copy()
        # Remove width/height from kwargs to prevent "multiple values" error
        kwargs_clean = {k: v for k, v in kwargs.items() if k not in ("width", "height")}
        params.update(kwargs_clean)
        
        # Explicitly set width/height (override any in template parameters)
        params["width"] = width
        params["height"] = height
        
        return template.generator(**params)
    
    def _get_font(self, font_name: Optional[str] = None, size: int = 10) -> ImageFont.FreeTypeFont:
        """Load a font or fallback to default."""
        try:
            if font_name:
                return ImageFont.truetype(font_name, size)
            # Try common system fonts if no name provided
            common_fonts = ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf", "Verdana.ttf"]
            for f in common_fonts:
                try:
                    return ImageFont.truetype(f, size)
                except OSError:
                    continue
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    def _generate_scrolling_text(self, text: str, speed: int, color: RGB, direction: str, width: int, height: int, **kwargs) -> Pattern:
        """Generate scrolling text pattern using system fonts."""
        frames: List[Frame] = []
        
        # Load Font
        font_size = kwargs.get('font_size', max(8, height - 2))
        font_name = kwargs.get('font_name', None)
        font = self._get_font(font_name, font_size)
        
        # Calculate dimensions using PIL
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Ensure we have enough space to scroll
        total_scroll_width = text_width + width
        
        # Create image with full text
        # Make height large enough to center text
        # width = exact text width
        full_text_img = Image.new('RGB', (text_width + 10, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(full_text_img)
        
        # Vertical centering
        text_y = (height - text_height) // 2 
        # Fine tune y-offset for some fonts that render high
        text_y = max(0, text_y - 1) 
        
        draw.text((0, text_y), text, font=font, fill=color)
        
        # Generate frames
        # We scroll the "viewport" across the text image
        
        # Create a blank buffer for off-screen areas
        buffer_pixels = [(0, 0, 0)] * (width * height)
        
        step = max(1, speed)
        
        for scroll_pos in range(0, total_scroll_width, step):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Current viewport X relative to text start:
            # When scroll_pos = 0, text is just off-screen to the right (if dir=left)
            # Standard marquee: text starts at width, moves to -text_width
            
            # Logic for "left" scroll:
            # Text starts at x=width, moves left.
            # text_x_on_screen = width - scroll_pos
            
            text_x_start = width - scroll_pos if direction == "left" else scroll_pos - text_width
            
            # We copy pixels from full_text_img to the frame buffer
            # Intersection of [0, width] and [text_x_start, text_x_start + text_width]
            
            # Optimization: iterate over screen pixels and sample image
            # Or iterate over image pixels and place on screen?
            # Iterating screen pixels is safer for bounds
            
            text_img_data = full_text_img.load()
            
            for y in range(height):
                for x in range(width):
                    # Map screen x to text image x
                    img_x = x - text_x_start
                    
                    if 0 <= img_x < text_width:
                         try:
                            # Sample directly
                            r, g, b = text_img_data[img_x, y]
                            if r > 0 or g > 0 or b > 0:
                                pixels[y * width + x] = (r, g, b)
                         except IndexError:
                             pass
            
            frames.append(Frame(pixels=pixels, duration_ms=100))
            
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name=f"Scrolling: {text}", metadata=metadata, frames=frames)
    
    def _generate_bouncing_ball(self, color: RGB, frames: int, speed: float, width: int, height: int, **kwargs) -> Pattern:
        """Generate bouncing ball pattern."""
        pattern_frames: List[Frame] = []
        ball_size = 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Calculate ball position (bouncing)
            t = (frame_idx / frames) * 2 * math.pi
            x = int((width - ball_size) * (0.5 + 0.4 * math.sin(t)))
            y = int((height - ball_size) * (0.5 + 0.4 * abs(math.cos(t))))
            
            # Draw ball
            for dy in range(ball_size):
                for dx in range(ball_size):
                    px = x + dx
                    py = y + dy
                    if 0 <= px < width and 0 <= py < height:
                        idx = py * width + px
                        if idx < len(pixels):
                            pixels[idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Bouncing Ball", metadata=metadata, frames=pattern_frames)
    
    def _generate_fire(self, intensity: float, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate fire effect pattern."""
        pattern_frames: List[Frame] = []
        random.seed(42)  # Deterministic
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Fire effect: hot at bottom, cool at top
            for y in range(height):
                fire_intensity = 1.0 - (y / height) * intensity
                for x in range(width):
                    noise = (hash((x, y, frame_idx)) % 100) / 100.0
                    r = int(255 * fire_intensity * (0.7 + 0.3 * noise))
                    g = int(100 * fire_intensity * (0.5 + 0.5 * noise))
                    b = int(20 * fire_intensity)
                    
                    idx = y * width + x
                    if idx < len(pixels):
                        pixels[idx] = (r, g, b)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Fire Effect", metadata=metadata, frames=pattern_frames)
    
    def _generate_rain(self, drops: int, color: RGB, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate rain effect pattern."""
        pattern_frames: List[Frame] = []
        random.seed(42)
        
        # Create rain drops
        drop_positions = [(random.randint(0, width - 1), random.randint(-height, 0)) 
                         for _ in range(drops)]
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Update and draw drops
            for i, (x, y) in enumerate(drop_positions):
                y += 1
                if y >= height:
                    y = -1
                    x = random.randint(0, width - 1)
                drop_positions[i] = (x, y)
                
                if 0 <= y < height:
                    idx = y * width + x
                    if idx < len(pixels):
                        pixels[idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Rain Effect", metadata=metadata, frames=pattern_frames)
    
    def _generate_matrix_rain(self, columns: int, speed: int, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate Matrix-style rain effect."""
        pattern_frames: List[Frame] = []
        random.seed(42)
        
        # Create columns
        column_data = []
        for col in range(columns):
            col_x = (col * width) // columns
            length = random.randint(5, height)
            column_data.append({
                "x": col_x,
                "y": random.randint(-height, 0),
                "length": length,
                "chars": [random.choice("0123456789ABCDEF") for _ in range(length)]
            })
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            for col_info in column_data:
                col_y = col_info["y"]
                for i, char in enumerate(col_info["chars"]):
                    y = col_y + i
                    if 0 <= y < height:
                        # Fade from bright to dark
                        intensity = 1.0 - (i / col_info["length"])
                        r = int(0 * intensity)
                        g = int(255 * intensity)
                        b = int(0 * intensity)
                        
                        idx = y * width + col_info["x"]
                        if idx < len(pixels):
                            pixels[idx] = (r, g, b)
                
                # Move column down
                col_info["y"] += speed
                if col_info["y"] > height:
                    col_info["y"] = -col_info["length"]
                    col_info["chars"] = [random.choice("0123456789ABCDEF") for _ in range(col_info["length"])]
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Matrix Rain", metadata=metadata, frames=pattern_frames)
    
    def _generate_clock(self, format: str, color: RGB, width: int, height: int, **kwargs) -> Pattern:
        """Generate clock pattern with animation using system fonts."""
        from datetime import datetime, timedelta
        pattern_frames: List[Frame] = []
        
        frames_count = kwargs.get('frames', 60)
        font_size = kwargs.get('font_size', max(8, height - 2))
        font_name = kwargs.get('font_name', None)
        font = self._get_font(font_name, font_size)
        
        start_time = datetime.now()
        
        for frame_idx in range(frames_count):
            current_time = start_time + timedelta(seconds=frame_idx)
            
            if format == "12h":
                time_str = current_time.strftime("%I:%M:%S")
            else:
                time_str = current_time.strftime("%H:%M:%S")
            
            # Create image for frame
            img = Image.new('RGB', (width, height), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Center text
            bbox = draw.textbbox((0, 0), time_str, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (width - text_w) // 2
            y = (height - text_h) // 2
            y = max(0, y - 1) # Fine tune
            
            draw.text((x, y), time_str, font=font, fill=color)
            
            # Convert to pixels
            pixels = [(0, 0, 0)] * (width * height)
            img_data = img.load()
            for py in range(height):
                for px in range(width):
                    r, g, b = img_data[px, py]
                    pixels[py * width + px] = (r, g, b)
            
            frame = Frame(pixels=pixels, duration_ms=500)
            pattern_frames.append(frame)
            
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name=f"Animated Clock", metadata=metadata, frames=pattern_frames)
    
    def _generate_weather(self, temperature: int, condition: str, width: int, height: int, **kwargs) -> Pattern:
        """Generate weather display pattern with animation using system fonts."""
        pattern_frames: List[Frame] = []
        frames_count = kwargs.get('frames', 60)
        
        font_size = kwargs.get('font_size', max(8, height - 2))
        font_name = kwargs.get('font_name', None)
        font = self._get_font(font_name, font_size)
        
        for frame_idx in range(frames_count):
            img = Image.new('RGB', (width, height), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Animate condition icon position
            icon_x = width - 8 + int(math.sin(frame_idx * 0.2) * 2)
            icon_y = (height - 6) // 2
            
            # Draw temperature text on left
            temp_str = f"{temperature}"
            draw.text((2, (height - font_size) // 2 - 1), temp_str, font=font, fill=(255, 255, 255))
            
            # Draw icon manually (no font for icons yet)
            pixels = [(0, 0, 0)] * (width * height)
            
            # First, copy text from image
            img_data = img.load()
            for py in range(height):
                for px in range(width):
                    r, g, b = img_data[px, py]
                    if r > 0 or g > 0 or b > 0:
                        pixels[py * width + px] = (r, g, b)

            # Then overlay icon
            if condition == "sunny":
                # Draw sun
                sun_color = (255, 200, 0)
                for dy in range(4):
                    for dx in range(4):
                        if (dx == 0 or dx == 3) and (dy == 0 or dy == 3): continue
                        px, py = icon_x + dx, icon_y + dy
                        if 0 <= px < width and 0 <= py < height:
                            pixels[py * width + px] = sun_color
            else:
                # Draw cloud
                cloud_color = (150, 150, 200)
                for dy in range(3):
                    for dx in range(5):
                        px, py = icon_x + dx, icon_y + dy + 1
                        if 0 <= px < width and 0 <= py < height:
                            pixels[py * width + px] = cloud_color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
            
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name=f"Weather: {temperature}°", metadata=metadata, frames=pattern_frames)
    
    def _generate_color_cycle(self, speed: float, frames: int, hue_start: float, saturation: float, brightness: float, width: int, height: int, **kwargs) -> Pattern:
        """Generate color cycle pattern."""
        pattern_frames: List[Frame] = []
        
        def hsv_to_rgb(h, s, v):
            """Convert HSV to RGB."""
            c = v * s
            x = c * (1 - abs((h * 6) % 2 - 1))
            m = v - c
            
            if h < 1/6:
                r, g, b = c, x, 0
            elif h < 2/6:
                r, g, b = x, c, 0
            elif h < 3/6:
                r, g, b = 0, c, x
            elif h < 4/6:
                r, g, b = 0, x, c
            elif h < 5/6:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            
            return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            hue = (hue_start + (frame_idx * speed / frames)) % 1.0
            
            for y in range(height):
                for x in range(width):
                    # Create gradient based on position
                    pos_hue = (hue + (x + y) / (width + height) * 0.3) % 1.0
                    color = hsv_to_rgb(pos_hue, saturation, brightness)
                    idx = y * width + x
                    if idx < len(pixels):
                        pixels[idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Color Cycle", metadata=metadata, frames=pattern_frames)
    
    def _generate_wave(self, color: RGB, frames: int, frequency: float, amplitude: float, width: int, height: int, **kwargs) -> Pattern:
        """Generate wave pattern."""
        pattern_frames: List[Frame] = []
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = (frame_idx / frames) * 2 * math.pi
            
            for x in range(width):
                # Calculate wave height
                wave_y = int(height / 2 + amplitude * (height / 2) * math.sin((x / width) * frequency * 2 * math.pi + t))
                
                # Draw wave line
                for offset in range(-1, 2):
                    y = wave_y + offset
                    if 0 <= y < height:
                        idx = y * width + x
                        if idx < len(pixels):
                            pixels[idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Wave", metadata=metadata, frames=pattern_frames)
    
    def _generate_spiral(self, color: RGB, frames: int, speed: float, thickness: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate spiral pattern."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            angle_offset = (frame_idx * speed / frames) * 2 * math.pi
            
            # Draw spiral
            for r in range(0, int(max_radius), 1):
                angle = (r / max_radius) * 4 * math.pi + angle_offset
                x = int(center_x + r * math.cos(angle))
                y = int(center_y + r * math.sin(angle))
                
                # Draw with thickness
                for dy in range(-thickness, thickness + 1):
                    for dx in range(-thickness, thickness + 1):
                        px, py = x + dx, y + dy
                        if 0 <= px < width and 0 <= py < height:
                            idx = py * width + px
                            if idx < len(pixels):
                                pixels[idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Spiral", metadata=metadata, frames=pattern_frames)
    
    def _generate_pulse(self, color: RGB, frames: int, speed: float, center_x: float, center_y: float, width: int, height: int, **kwargs) -> Pattern:
        """Generate pulse pattern."""
        pattern_frames: List[Frame] = []
        cx, cy = int(width * center_x), int(height * center_y)
        max_radius = min(width, height) / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = (frame_idx / frames) * 2 * math.pi
            radius = max_radius * (0.3 + 0.7 * abs(math.sin(t * speed)))
            
            # Draw pulsing circle
            for y in range(height):
                for x in range(width):
                    dx, dy = x - cx, y - cy
                    dist = math.sqrt(dx * dx + dy * dy)
                    if abs(dist - radius) < 2:
                        idx = y * width + x
                        if idx < len(pixels):
                            intensity = 1.0 - abs(dist - radius) / 2.0
                            r = int(color[0] * intensity)
                            g = int(color[1] * intensity)
                            b = int(color[2] * intensity)
                            pixels[idx] = (r, g, b)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Pulse", metadata=metadata, frames=pattern_frames)
    
    def _generate_fade(self, color: RGB, frames: int, fade_type: str, width: int, height: int, **kwargs) -> Pattern:
        """Generate fade in/out pattern."""
        pattern_frames: List[Frame] = []
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            if fade_type == "in":
                intensity = frame_idx / frames
            elif fade_type == "out":
                intensity = 1.0 - (frame_idx / frames)
            else:  # in_out
                if frame_idx < frames / 2:
                    intensity = (frame_idx * 2) / frames
                else:
                    intensity = 1.0 - ((frame_idx - frames / 2) * 2) / frames
            
            r = int(color[0] * intensity)
            g = int(color[1] * intensity)
            b = int(color[2] * intensity)
            fade_color = (r, g, b)
            
            # Fill entire matrix
            for idx in range(len(pixels)):
                pixels[idx] = fade_color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Fade", metadata=metadata, frames=pattern_frames)
    
    def _generate_random(self, density: float, frames: int, color: RGB, width: int, height: int, **kwargs) -> Pattern:
        """Generate random pixel pattern."""
        pattern_frames: List[Frame] = []
        random.seed(42)
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            num_pixels = int(width * height * density)
            
            for _ in range(num_pixels):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                idx = y * width + x
                if idx < len(pixels):
                    pixels[idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Random Pixels", metadata=metadata, frames=pattern_frames)
    
    def _generate_ray_rotation(self, speed: float, color: RGB, ray_count: int, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate rotating rays pattern (Budurasmala)."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            angle_offset = (frame_idx * speed / frames) * 2 * math.pi
            
            # Draw rays
            for ray_idx in range(ray_count):
                ray_angle = (2 * math.pi * ray_idx / ray_count) + angle_offset
                
                # Draw ray from center outward
                for r in range(0, int(max_radius), 2):
                    x = int(center_x + r * math.cos(ray_angle))
                    y = int(center_y + r * math.sin(ray_angle))
                    
                    if 0 <= x < width and 0 <= y < height:
                        idx = y * width + x
                        if idx < len(pixels):
                            # Fade intensity based on distance
                            fade = 1.0 - (r / max_radius) * 0.5
                            r_val = int(color[0] * fade)
                            g_val = int(color[1] * fade)
                            b_val = int(color[2] * fade)
                            pixels[idx] = (r_val, g_val, b_val)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Ray Rotation", metadata=metadata, frames=pattern_frames)
    
    def _generate_pulsing_halo(self, ring_count: int, pulse_speed: float, color: RGB, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate pulsing halo pattern (Budurasmala)."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = (frame_idx / frames) * 2 * math.pi
            
            # Calculate pulse factor (0.3 to 1.0)
            pulse_factor = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * pulse_speed))
            
            # Draw concentric rings
            for ring_idx in range(ring_count):
                base_radius = (max_radius * (ring_idx + 1) / (ring_count + 1))
                radius = base_radius * pulse_factor
                
                # Draw ring
                for angle in range(0, 360, 2):
                    rad = math.radians(angle)
                    x = int(center_x + radius * math.cos(rad))
                    y = int(center_y + radius * math.sin(rad))
                    
                    if 0 <= x < width and 0 <= y < height:
                        idx = y * width + x
                        if idx < len(pixels):
                            # Fade outer rings
                            fade = 1.0 - (ring_idx / ring_count) * 0.3
                            r_val = int(color[0] * fade)
                            g_val = int(color[1] * fade)
                            b_val = int(color[2] * fade)
                            pixels[idx] = (r_val, g_val, b_val)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Pulsing Halo", metadata=metadata, frames=pattern_frames)
    
    def _generate_twinkling_stars(self, density: float, twinkle_speed: float, color: RGB, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate twinkling stars pattern (Budurasmala)."""
        pattern_frames: List[Frame] = []
        num_stars = int(width * height * density)
        random.seed(42)
        
        # Pre-generate star positions
        star_positions = []
        for _ in range(num_stars):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            star_positions.append((x, y))
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = frame_idx / frames
            
            # Draw twinkling stars
            for star_x, star_y in star_positions:
                # Each star has its own phase
                star_phase = (star_x + star_y) % 10
                phase_offset = (star_phase / 10.0) * 2 * math.pi
                intensity = 0.3 + 0.7 * abs(math.sin(t * twinkle_speed * 2 * math.pi + phase_offset))
                
                idx = star_y * width + star_x
                if idx < len(pixels):
                    r_val = int(color[0] * intensity)
                    g_val = int(color[1] * intensity)
                    b_val = int(color[2] * intensity)
                    pixels[idx] = (r_val, g_val, b_val)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Twinkling Stars", metadata=metadata, frames=pattern_frames)
    
    def _generate_wave_propagation(self, wave_count: int, speed: float, color: RGB, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate wave propagation pattern (Budurasmala)."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = frame_idx / frames
            
            # Draw waves propagating around circle
            for wave_idx in range(wave_count):
                wave_phase = (t * speed + wave_idx / wave_count) * 2 * math.pi
                
                # Draw wave along circle
                for angle_deg in range(0, 360, 1):
                    angle = math.radians(angle_deg)
                    wave_angle = angle + wave_phase
                    
                    # Wave intensity based on angle
                    wave_intensity = 0.5 + 0.5 * math.sin(wave_angle * 8)
                    
                    # Draw at multiple radii for wave effect
                    for r_offset in range(-3, 4):
                        radius = max_radius * 0.7 + r_offset
                        x = int(center_x + radius * math.cos(angle))
                        y = int(center_y + radius * math.sin(angle))
                        
                        if 0 <= x < width and 0 <= y < height:
                            idx = y * width + x
                            if idx < len(pixels):
                                # Fade based on distance from wave center
                                distance_fade = 1.0 - abs(r_offset) / 3.0
                                intensity = wave_intensity * distance_fade
                                
                                if intensity > 0.1:
                                    r_val = int(color[0] * intensity)
                                    g_val = int(color[1] * intensity)
                                    b_val = int(color[2] * intensity)
                                    pixels[idx] = (r_val, g_val, b_val)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Wave Propagation", metadata=metadata, frames=pattern_frames)
    
    def _generate_color_gradient_rotation(self, gradient_colors: List[RGB], rotation_speed: float, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate rotating color gradient pattern (Budurasmala)."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2
        
        if not gradient_colors:
            gradient_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            angle_offset = (frame_idx * rotation_speed / frames) * 2 * math.pi
            
            # Draw gradient pattern
            for y in range(height):
                for x in range(width):
                    dx, dy = x - center_x, y - center_y
                    angle = math.atan2(dy, dx) + angle_offset
                    radius = math.sqrt(dx * dx + dy * dy)
                    
                    if radius <= max_radius:
                        # Normalize angle to 0-2π
                        angle = (angle % (2 * math.pi) + 2 * math.pi) % (2 * math.pi)
                        
                        # Map angle to gradient
                        gradient_pos = angle / (2 * math.pi)
                        color_idx = int(gradient_pos * len(gradient_colors)) % len(gradient_colors)
                        next_color_idx = (color_idx + 1) % len(gradient_colors)
                        
                        # Interpolate between colors
                        local_pos = (gradient_pos * len(gradient_colors)) % 1.0
                        color1 = gradient_colors[color_idx]
                        color2 = gradient_colors[next_color_idx]
                        
                        r = int(color1[0] * (1 - local_pos) + color2[0] * local_pos)
                        g = int(color1[1] * (1 - local_pos) + color2[1] * local_pos)
                        b = int(color1[2] * (1 - local_pos) + color2[2] * local_pos)
                        
                        # Fade based on radius
                        radius_fade = 1.0 - (radius / max_radius) * 0.3
                        r = int(r * radius_fade)
                        g = int(g * radius_fade)
                        b = int(b * radius_fade)
                        
                        idx = y * width + x
                        if idx < len(pixels):
                            pixels[idx] = (r, g, b)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Color Gradient Rotation", metadata=metadata, frames=pattern_frames)
    
    # Cultural Pattern Templates (Budurasmala - Phase 3)
    def _generate_lotus_pattern(self, color: RGB, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate lotus flower pattern (Buddhist symbolism)."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = (frame_idx / frames) * 2 * math.pi
            
            # Draw lotus petals (8 petals)
            for petal_idx in range(8):
                petal_angle = (2 * math.pi * petal_idx / 8) + t * 0.1
                
                # Draw petal as elongated ellipse
                for r in range(0, int(max_radius * 0.8), 1):
                    for angle_offset in range(-15, 16, 2):
                        angle = petal_angle + math.radians(angle_offset)
                        x = int(center_x + r * math.cos(angle))
                        y = int(center_y + r * math.sin(angle))
                        
                        if 0 <= x < width and 0 <= y < height:
                            idx = y * width + x
                            if idx < len(pixels):
                                # Fade from center
                                fade = 1.0 - (r / (max_radius * 0.8))
                                r_val = int(color[0] * fade)
                                g_val = int(color[1] * fade)
                                b_val = int(color[2] * fade)
                                pixels[idx] = (r_val, g_val, b_val)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Lotus Pattern", metadata=metadata, frames=pattern_frames)
    
    def _generate_dharma_wheel(self, color: RGB, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate dharma wheel pattern (Buddhist symbolism)."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = (frame_idx / frames) * 2 * math.pi
            
            # Draw outer circle
            for angle_deg in range(0, 360, 1):
                angle = math.radians(angle_deg)
                x = int(center_x + max_radius * 0.9 * math.cos(angle))
                y = int(center_y + max_radius * 0.9 * math.sin(angle))
                
                if 0 <= x < width and 0 <= y < height:
                    idx = y * width + x
                    if idx < len(pixels):
                        pixels[idx] = color
            
            # Draw spokes (8 spokes)
            for spoke_idx in range(8):
                spoke_angle = (2 * math.pi * spoke_idx / 8) + t * 0.2
                
                for r in range(int(max_radius * 0.3), int(max_radius * 0.9), 1):
                    x = int(center_x + r * math.cos(spoke_angle))
                    y = int(center_y + r * math.sin(spoke_angle))
                    
                    if 0 <= x < width and 0 <= y < height:
                        idx = y * width + x
                        if idx < len(pixels):
                            pixels[idx] = color
            
            # Draw center hub
            for r in range(0, int(max_radius * 0.3), 1):
                for angle_deg in range(0, 360, 2):
                    angle = math.radians(angle_deg)
                    x = int(center_x + r * math.cos(angle))
                    y = int(center_y + r * math.sin(angle))
                    
                    if 0 <= x < width and 0 <= y < height:
                        idx = y * width + x
                        if idx < len(pixels):
                            pixels[idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Dharma Wheel", metadata=metadata, frames=pattern_frames)
    
    def _generate_vesak_stars(self, color: RGB, frames: int, width: int, height: int, **kwargs) -> Pattern:
        """Generate Vesak stars pattern (traditional festival pattern)."""
        pattern_frames: List[Frame] = []
        center_x, center_y = width / 2, height / 2
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            t = frame_idx / frames
            
            # Draw 5-pointed stars at various positions
            star_positions = [
                (center_x, center_y),
                (center_x * 0.5, center_y * 0.5),
                (center_x * 1.5, center_y * 0.5),
                (center_x * 0.5, center_y * 1.5),
                (center_x * 1.5, center_y * 1.5),
            ]
            
            for star_x, star_y in star_positions:
                if star_x >= width or star_y >= height:
                    continue
                
                # Draw 5-pointed star
                star_size = min(width, height) * 0.15
                rotation = t * 2 * math.pi
                
                for i in range(5):
                    # Outer point
                    outer_angle = (2 * math.pi * i / 5) - math.pi / 2 + rotation
                    outer_x = int(star_x + star_size * math.cos(outer_angle))
                    outer_y = int(star_y + star_size * math.sin(outer_angle))
                    
                    # Inner point
                    inner_angle = (2 * math.pi * (i + 0.5) / 5) - math.pi / 2 + rotation
                    inner_x = int(star_x + star_size * 0.4 * math.cos(inner_angle))
                    inner_y = int(star_y + star_size * 0.4 * math.sin(inner_angle))
                    
                    # Draw lines
                    self._draw_line(pixels, width, height, 
                                   int(star_x), int(star_y), outer_x, outer_y, color)
                    self._draw_line(pixels, width, height,
                                   outer_x, outer_y, inner_x, inner_y, color)
            
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern_frames.append(frame)
        
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name="Vesak Stars", metadata=metadata, frames=pattern_frames)
    
    def _draw_line(self, pixels: List[RGB], width: int, height: int, 
                   x1: int, y1: int, x2: int, y2: int, color: RGB):
        """Draw a line between two points."""
        steps = max(abs(x2 - x1), abs(y2 - y1))
        if steps == 0:
            return
        
        for i in range(steps + 1):
            t = i / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            
            if 0 <= x < width and 0 <= y < height:
                idx = y * width + x
                if idx < len(pixels):
                    pixels[idx] = color

