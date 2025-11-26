"""
AI Pattern Generator - Integration with Cloudie CLI for prompt-based pattern generation

This module provides integration with AI CLI tools (like Cloudie) to generate
LED matrix patterns from natural language prompts.
"""

from __future__ import annotations

import json
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass

from core.pattern import Pattern, Frame, PatternMetadata

logger = logging.getLogger(__name__)


@dataclass
class AIGenerationConfig:
    """Configuration for AI pattern generation"""
    prompt: str
    width: int = 16
    height: int = 16
    frames: int = 10
    style: str = "animated"  # "static", "animated", "scrolling", "effect"
    colors: Optional[List[Tuple[int, int, int]]] = None
    duration_ms: int = 100
    cli_path: Optional[str] = None  # Path to cloudie CLI executable
    api_key: Optional[str] = None  # API key if required
    model: str = "default"  # AI model to use


class CloudieCLIInterface:
    """
    Interface to Cloudie CLI for pattern generation.
    
    Supports both direct CLI execution and API-based generation.
    """
    
    def __init__(self, cli_path: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Cloudie CLI interface.
        
        Args:
            cli_path: Path to cloudie CLI executable (or None to auto-detect)
            api_key: API key for authentication (if required)
        """
        self.cli_path = cli_path or self._detect_cli_path()
        self.api_key = api_key
        self._validate_cli()
    
    def _detect_cli_path(self) -> Optional[str]:
        """Auto-detect cloudie CLI installation"""
        # Check common installation paths
        common_paths = [
            "cloudie",
            "cloudie-cli",
            shutil.which("cloudie"),
            shutil.which("cloudie-cli"),
        ]
        
        for path in common_paths:
            if path and self._check_cli_available(path):
                return path
        
        # Check in common installation directories
        if Path.home().exists():
            for base_dir in [Path.home() / ".local" / "bin", Path.home() / "bin"]:
                for exe_name in ["cloudie", "cloudie-cli", "cloudie.exe"]:
                    exe_path = base_dir / exe_name
                    if exe_path.exists() and exe_path.is_file():
                        return str(exe_path)
        
        return None
    
    def _check_cli_available(self, path: str) -> bool:
        """Check if CLI is available and executable"""
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return False
    
    def _validate_cli(self) -> None:
        """Validate that CLI is available"""
        if not self.cli_path:
            raise RuntimeError(
                "Cloudie CLI not found. Please install it or specify the path.\n"
                "Installation: npm install -g @cloudie/cli or pip install cloudie-cli"
            )
        
        if not self._check_cli_available(self.cli_path):
            raise RuntimeError(f"Cloudie CLI not executable at: {self.cli_path}")
    
    def generate_pattern(
        self,
        config: AIGenerationConfig,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate pattern from prompt using Cloudie CLI.
        
        Args:
            config: Generation configuration
            output_format: Output format ("json", "leds", "bin")
        
        Returns:
            Dictionary with pattern data and metadata
        """
        if not self.cli_path:
            raise RuntimeError("Cloudie CLI not available")
        
        # Build command
        cmd = [
            self.cli_path,
            "generate",
            "pattern",
            "--prompt", config.prompt,
            "--width", str(config.width),
            "--height", str(config.height),
            "--frames", str(config.frames),
            "--style", config.style,
            "--format", output_format,
        ]
        
        # Add optional parameters
        if config.duration_ms:
            cmd.extend(["--duration", str(config.duration_ms)])
        
        if config.colors:
            colors_str = ",".join([f"{r},{g},{b}" for r, g, b in config.colors])
            cmd.extend(["--colors", colors_str])
        
        if config.model != "default":
            cmd.extend(["--model", config.model])
        
        if self.api_key:
            cmd.extend(["--api-key", self.api_key])
        
        # Execute CLI
        try:
            logger.info(f"Executing Cloudie CLI: {' '.join(cmd[:5])}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                check=True
            )
            
            # Parse output
            if output_format == "json":
                return json.loads(result.stdout)
            else:
                # For other formats, return raw output with metadata
                return {
                    "output": result.stdout,
                    "format": output_format,
                    "metadata": {
                        "width": config.width,
                        "height": config.height,
                        "frames": config.frames,
                    }
                }
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("AI generation timed out after 2 minutes")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e.stdout or "Unknown error"
            raise RuntimeError(f"Cloudie CLI error: {error_msg}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse AI output: {e}")
    
    def convert_to_pattern(self, ai_output: Dict[str, Any]) -> Pattern:
        """
        Convert AI CLI output to Pattern object.
        
        Args:
            ai_output: Output from generate_pattern()
        
        Returns:
            Pattern object
        """
        metadata = ai_output.get("metadata", {})
        width = metadata.get("width", 16)
        height = metadata.get("height", 16)
        
        # Create pattern metadata
        pattern_metadata = PatternMetadata(
            width=width,
            height=height,
            name=ai_output.get("name", "AI Generated Pattern"),
            description=ai_output.get("description", ""),
        )
        
        # Convert frames
        frames_data = ai_output.get("frames", [])
        frames: List[Frame] = []
        
        for frame_data in frames_data:
            pixels = frame_data.get("pixels", [])
            duration_ms = frame_data.get("duration_ms", 100)
            
            # Ensure pixels are in correct format
            if isinstance(pixels, list) and len(pixels) > 0:
                # Convert to RGB tuples if needed
                rgb_pixels: List[Tuple[int, int, int]] = []
                for pixel in pixels:
                    if isinstance(pixel, (list, tuple)) and len(pixel) >= 3:
                        rgb_pixels.append((int(pixel[0]), int(pixel[1]), int(pixel[2])))
                    elif isinstance(pixel, dict):
                        rgb_pixels.append((
                            int(pixel.get("r", 0)),
                            int(pixel.get("g", 0)),
                            int(pixel.get("b", 0))
                        ))
                    else:
                        rgb_pixels.append((0, 0, 0))
                
                # Pad or truncate to match matrix size
                expected_count = width * height
                if len(rgb_pixels) < expected_count:
                    rgb_pixels.extend([(0, 0, 0)] * (expected_count - len(rgb_pixels)))
                elif len(rgb_pixels) > expected_count:
                    rgb_pixels = rgb_pixels[:expected_count]
                
                frame = Frame(pixels=rgb_pixels, duration_ms=duration_ms)
                frames.append(frame)
            else:
                # Empty frame
                blank_pixels = [(0, 0, 0)] * (width * height)
                frame = Frame(pixels=blank_pixels, duration_ms=duration_ms)
                frames.append(frame)
        
        # Create pattern
        pattern = Pattern(
            name=pattern_metadata.name,
            metadata=pattern_metadata,
            frames=frames
        )
        
        return pattern


class FallbackAIGenerator:
    """
    Fallback AI generator that creates simple patterns when CLI is not available.
    
    This provides basic pattern generation using rule-based logic for common prompts.
    """
    
    @staticmethod
    def generate_from_prompt(
        config: AIGenerationConfig
    ) -> Pattern:
        """
        Generate a simple pattern from prompt using rule-based logic.
        
        This is a fallback when Cloudie CLI is not available.
        """
        prompt_lower = config.prompt.lower()
        width = config.width
        height = config.height
        frames = config.frames
        
        # Create metadata
        metadata = PatternMetadata(
            width=width,
            height=height,
            name=f"AI: {config.prompt[:30]}",
            description=f"Generated from prompt: {config.prompt}"
        )
        
        # Generate frames based on prompt keywords
        pattern_frames: List[Frame] = []
        
        if "scrolling" in prompt_lower or "text" in prompt_lower:
            # Scrolling text animation
            pattern_frames = FallbackAIGenerator._generate_scrolling_text(
                config, width, height, frames
            )
        elif "bounce" in prompt_lower or "ball" in prompt_lower:
            # Bouncing ball
            pattern_frames = FallbackAIGenerator._generate_bouncing_ball(
                config, width, height, frames
            )
        elif "rain" in prompt_lower:
            # Rain effect
            pattern_frames = FallbackAIGenerator._generate_rain(
                config, width, height, frames
            )
        elif "fire" in prompt_lower or "flame" in prompt_lower:
            # Fire effect
            pattern_frames = FallbackAIGenerator._generate_fire(
                config, width, height, frames
            )
        else:
            # Default: simple gradient animation
            pattern_frames = FallbackAIGenerator._generate_gradient(
                config, width, height, frames
            )
        
        return Pattern(
            name=metadata.name,
            metadata=metadata,
            frames=pattern_frames
        )
    
    @staticmethod
    def _generate_scrolling_text(
        config: AIGenerationConfig,
        width: int,
        height: int,
        frames: int
    ) -> List[Frame]:
        """Generate scrolling text animation"""
        frames_list: List[Frame] = []
        text = config.prompt.replace("scrolling", "").replace("text", "").strip()[:10]
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            offset = frame_idx % (width + len(text) * 3)
            
            # Simple text rendering
            for char_idx, char in enumerate(text):
                x = width - offset + char_idx * 3
                if 0 <= x < width:
                    # Simple 3x5 character pattern
                    for py in range(5):
                        for px in range(3):
                            if 0 <= x + px < width and 0 <= py < height:
                                idx = py * width + (x + px)
                                if idx < len(pixels):
                                    pixels[idx] = (255, 255, 255)
            
            frame = Frame(pixels=pixels, duration_ms=config.duration_ms)
            frames_list.append(frame)
        
        return frames_list
    
    @staticmethod
    def _generate_bouncing_ball(
        config: AIGenerationConfig,
        width: int,
        height: int,
        frames: int
    ) -> List[Frame]:
        """Generate bouncing ball animation"""
        frames_list: List[Frame] = []
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Calculate ball position (bouncing)
            t = (frame_idx / frames) * 2 * 3.14159  # 0 to 2π
            x = int((width - 2) * (0.5 + 0.4 * (t % (2 * 3.14159) / (2 * 3.14159))))
            y = int((height - 2) * abs(0.5 - 0.4 * abs((t % (2 * 3.14159)) - 3.14159) / 3.14159))
            
            # Draw ball (2x2 pixels)
            for dy in range(2):
                for dx in range(2):
                    px = x + dx
                    py = y + dy
                    if 0 <= px < width and 0 <= py < height:
                        idx = py * width + px
                        if idx < len(pixels):
                            pixels[idx] = (255, 100, 0)  # Orange ball
            
            frame = Frame(pixels=pixels, duration_ms=config.duration_ms)
            frames_list.append(frame)
        
        return frames_list
    
    @staticmethod
    def _generate_rain(
        config: AIGenerationConfig,
        width: int,
        height: int,
        frames: int
    ) -> List[Frame]:
        """Generate rain effect"""
        frames_list: List[Frame] = []
        import random
        random.seed(42)  # Deterministic
        
        # Create rain drops
        drops = [(random.randint(0, width - 1), random.randint(-height, 0)) 
                 for _ in range(width // 2)]
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Update and draw drops
            for i, (x, y) in enumerate(drops):
                y += 1
                if y >= height:
                    y = -1
                    x = random.randint(0, width - 1)
                drops[i] = (x, y)
                
                if 0 <= y < height:
                    idx = y * width + x
                    if idx < len(pixels):
                        pixels[idx] = (0, 100, 255)  # Blue rain
            
            frame = Frame(pixels=pixels, duration_ms=config.duration_ms)
            frames_list.append(frame)
        
        return frames_list
    
    @staticmethod
    def _generate_fire(
        config: AIGenerationConfig,
        width: int,
        height: int,
        frames: int
    ) -> List[Frame]:
        """Generate fire effect"""
        frames_list: List[Frame] = []
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Fire effect: hot at bottom, cool at top
            for y in range(height):
                intensity = 1.0 - (y / height)
                for x in range(width):
                    # Add some randomness
                    noise = (hash((x, y, frame_idx)) % 100) / 100.0
                    r = int(255 * intensity * (0.7 + 0.3 * noise))
                    g = int(100 * intensity * (0.5 + 0.5 * noise))
                    b = int(20 * intensity)
                    
                    idx = y * width + x
                    if idx < len(pixels):
                        pixels[idx] = (r, g, b)
            
            frame = Frame(pixels=pixels, duration_ms=config.duration_ms)
            frames_list.append(frame)
        
        return frames_list
    
    @staticmethod
    def _generate_gradient(
        config: AIGenerationConfig,
        width: int,
        height: int,
        frames: int
    ) -> List[Frame]:
        """Generate gradient animation"""
        frames_list: List[Frame] = []
        
        for frame_idx in range(frames):
            pixels = [(0, 0, 0)] * (width * height)
            
            # Animated gradient
            phase = (frame_idx / frames) * 2 * 3.14159
            
            for y in range(height):
                for x in range(width):
                    # Calculate color based on position and phase
                    r = int(128 + 127 * ((x / width) + 0.3 * (frame_idx / frames)))
                    g = int(128 + 127 * ((y / height) + 0.3 * (frame_idx / frames)))
                    b = int(128 + 127 * (0.5 + 0.5 * (frame_idx / frames)))
                    
                    r = max(0, min(255, r))
                    g = max(0, min(255, g))
                    b = max(0, min(255, b))
                    
                    idx = y * width + x
                    if idx < len(pixels):
                        pixels[idx] = (r, g, b)
            
            frame = Frame(pixels=pixels, duration_ms=config.duration_ms)
            frames_list.append(frame)
        
        return frames_list

