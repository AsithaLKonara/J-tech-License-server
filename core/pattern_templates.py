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

from core.pattern import Pattern, Frame, PatternMetadata

RGB = Tuple[int, int, int]


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
            description="Text that scrolls across the matrix",
            parameters={
                "text": "Hello",
                "speed": 1,
                "color": (255, 255, 255),
                "direction": "left"
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
                "color": (0, 255, 0)
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
                "condition": "sunny"
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
        
        # Merge parameters
        params = template.parameters.copy()
        params.update(kwargs)
        params["width"] = width
        params["height"] = height
        
        return template.generator(**params)
    
    def _generate_scrolling_text(self, text: str, speed: int, color: RGB, direction: str, width: int, height: int, **kwargs) -> Pattern:
        """Generate scrolling text pattern."""
        frames: List[Frame] = []
        char_width = 5
        text_width = len(text) * char_width
        total_frames = text_width + width
        
        for frame_idx in range(total_frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Calculate text position
            if direction == "left":
                offset = width - frame_idx
            else:  # right
                offset = frame_idx - text_width
            
            # Simple text rendering (simplified)
            for char_idx, char in enumerate(text):
                char_x = offset + char_idx * char_width
                if 0 <= char_x < width:
                    # Draw simple character pattern
                    for py in range(min(7, height)):
                        for px in range(min(char_width, width - char_x)):
                            if py < 7 and px < char_width:
                                pixel_idx = py * width + (char_x + px)
                                if 0 <= pixel_idx < len(pixels):
                                    pixels[pixel_idx] = color
            
            frame = Frame(pixels=pixels, duration_ms=100)
            frames.append(frame)
        
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
        """Generate clock pattern (simplified - shows static time)."""
        from datetime import datetime
        now = datetime.now()
        
        if format == "12h":
            time_str = now.strftime("%I:%M")
        else:
            time_str = now.strftime("%H:%M")
        
        pixels = [(0, 0, 0)] * (width * height)
        
        # Simple text rendering (simplified)
        char_width = 5
        text_width = len(time_str) * char_width
        start_x = max(0, (width - text_width) // 2)
        start_y = max(0, (height - 7) // 2)
        
        for char_idx, char in enumerate(time_str):
            char_x = start_x + char_idx * char_width
            if char_x + char_width <= width:
                # Draw simple digit pattern
                for py in range(min(7, height - start_y)):
                    for px in range(min(char_width, width - char_x)):
                        pixel_idx = (start_y + py) * width + (char_x + px)
                        if 0 <= pixel_idx < len(pixels):
                            pixels[pixel_idx] = color
        
        frame = Frame(pixels=pixels, duration_ms=1000)
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name=f"Clock: {time_str}", metadata=metadata, frames=[frame])
    
    def _generate_weather(self, temperature: int, condition: str, width: int, height: int, **kwargs) -> Pattern:
        """Generate weather display pattern."""
        pixels = [(0, 0, 0)] * (width * height)
        
        # Simple display (simplified)
        temp_str = f"{temperature}°F"
        condition_icon = "☀" if condition == "sunny" else "☁"
        
        # Render temperature (simplified)
        start_y = max(0, (height - 7) // 2)
        for i, char in enumerate(temp_str[:5]):  # Limit to 5 chars
            x = i * 5
            if x + 5 <= width:
                for py in range(min(7, height - start_y)):
                    for px in range(min(5, width - x)):
                        pixel_idx = (start_y + py) * width + (x + px)
                        if 0 <= pixel_idx < len(pixels):
                            pixels[pixel_idx] = (0, 255, 0)
        
        frame = Frame(pixels=pixels, duration_ms=1000)
        metadata = PatternMetadata(width=width, height=height)
        return Pattern(name=f"Weather: {temperature}°F", metadata=metadata, frames=[frame])
    
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

