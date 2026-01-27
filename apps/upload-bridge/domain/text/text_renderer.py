"""
Text Renderer
-------------

Pure-domain text rendering pipeline that converts text (with optional
effects) into LED-ready pixel buffers. The renderer supports character
spacing, alignment, multi-line layout, outline/shadow/gradient effects,
and provides helpers for scrolling and typing animations.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Optional, Sequence, Tuple

from domain.text.bitmap_font import BitmapFont
from domain.text.glyph_provider import GlyphProvider

RGB = Tuple[int, int, int]


@dataclass
class TextRenderOptions:
    width: int
    height: int
    color: RGB = (255, 255, 255)
    background: RGB = (0, 0, 0)
    alignment: str = "center"
    spacing: int = 0
    line_spacing: int = 1
    multiline: bool = True
    uppercase: bool = False
    font_size: int = 8
    font_name: Optional[str] = None  # Added for system fonts
    bitmap_font: Optional[BitmapFont] = None
    outline: bool = False
    outline_color: Optional[RGB] = (255, 255, 255)
    outline_thickness: int = 1
    shadow: bool = False
    shadow_color: Optional[RGB] = (0, 0, 0)
    shadow_offset: Tuple[int, int] = (1, 1)
    gradient: bool = False
    gradient_start: Optional[RGB] = None
    gradient_end: Optional[RGB] = None
    gradient_orientation: str = "vertical"  # or "horizontal"


@dataclass
class TextScrollOptions:
    direction: str = "left"  # left/right/up/down
    step: int = 1
    padding: int = 0


class TextRenderer:
    """Render text into RGB pixel buffers suitable for LED frames."""

    def __init__(self, default_provider: Optional[GlyphProvider] = None):
        self._provider = default_provider or GlyphProvider()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render_pixels(
        self,
        text: str,
        options: TextRenderOptions,
        offset: Tuple[int, int] = (0, 0),
    ) -> List[RGB]:
        """Render text into a flattened RGB buffer."""
        # Validate and sanitize text input
        if not isinstance(text, str):
            text = str(text)
        if not text:
            return [options.background] * (options.width * options.height)
        
        # Ensure text is properly encoded (handle any encoding issues)
        try:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            # Fallback: just use string representation
            text = str(text)
        
        width, height = options.width, options.height
        pixels = [options.background] * (width * height)
        if not text:
            return pixels

        glyph_provider = self._glyph_provider_for_options(options)
        char_width, char_height = self._char_dimensions(options, glyph_provider)
        lines = self._prepare_lines(text, options)
        
        # Branch for System Font (PIL) rendering
        if options.font_name:
            drawn_points = self._render_via_pil(text, lines, options)
        else:
            # Traditional Bitmap rendering
            drawn_points = []
            content_height = self._compute_content_height(len(lines), char_height, options.line_spacing)
            start_y = self._align_vertical(height, content_height)
            offset_x, offset_y = offset
            
            for line_idx, line in enumerate(lines):
                line_width = self._compute_line_width(line, char_width, options.spacing)
                cursor_x = self._align_horizontal(width, line_width, options.alignment) - offset_x
                cursor_y = start_y + line_idx * (char_height + options.line_spacing) - offset_y

                for char in line:
                    glyph = glyph_provider.glyph(char)
                    drawn_points.extend(
                        self._stamp_glyph(
                            glyph,
                            cursor_x,
                            cursor_y,
                            char_width,
                            char_height,
                            width,
                            height,
                            pixels,
                            record_only=True,
                        )
                    )
                    cursor_x += char_width + options.spacing

        if not drawn_points:
            return pixels

        # Apply effects in order: shadow -> outline -> fill
        if options.shadow:
            self._apply_shadow(drawn_points, options, pixels, width, height)

        if options.outline:
            self._apply_outline(drawn_points, options, pixels, width, height)

        self._apply_fill(drawn_points, options, pixels, width, height)
        return pixels

    def render_typing_frames(
        self,
        text: str,
        options: TextRenderOptions,
        frames_per_char: int,
        frame_duration_ms: int,
    ) -> List[List[Tuple[int, int, int]]]:
        """Generate frame pixel buffers for a typing animation."""
        frames: List[List[Tuple[int, int, int]]] = []
        for i in range(len(text) + 1):
            partial_text = text[:i]
            pixels = self.render_pixels(partial_text, options)
            for _ in range(max(1, frames_per_char)):
                frames.append(list(pixels))
        return frames

    def render_scroll_frames(
        self,
        text: str,
        options: TextRenderOptions,
        scroll: TextScrollOptions,
    ) -> List[List[Tuple[int, int, int]]]:
        """Generate scrolling frames using a sliding window approach."""
        if not text:
            return [self.render_pixels("", options)]

        glyph_provider = self._glyph_provider_for_options(options)
        char_width, char_height = self._char_dimensions(options, glyph_provider)
        work_opts, total_steps = self._build_scroll_workspace(text, options, scroll, char_width, char_height)
        base_pixels = self.render_pixels(text, work_opts)
        frames: List[List[Tuple[int, int, int]]] = []

        for step in range(0, total_steps, max(1, scroll.step)):
            offset = self._scroll_offset(step, scroll, work_opts, options)
            cropped = self._crop_pixels(base_pixels, work_opts.width, options.width, options.height, offset)
            frames.append(cropped)
        return frames

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _glyph_provider_for_options(self, options: TextRenderOptions) -> GlyphProvider:
        char_width, char_height = self._char_dimensions(options, self._provider)
        provider = GlyphProvider(bitmap_font=options.bitmap_font, width=char_width, height=char_height)
        return provider

    @staticmethod
    def _char_dimensions(options: TextRenderOptions, provider: GlyphProvider) -> Tuple[int, int]:
        if options.bitmap_font:
            return options.bitmap_font.width, options.bitmap_font.height
        char_height = max(5, options.font_size)
        char_width = max(3, int(char_height * 0.6))
        return char_width, char_height

    @staticmethod
    def _prepare_lines(text: str, options: TextRenderOptions) -> List[str]:
        if options.uppercase:
            text = text.upper()
        if options.multiline:
            lines = text.splitlines() or [""]
        else:
            lines = [" ".join(text.split())]
        return lines

    @staticmethod
    def _compute_line_width(line: str, char_width: int, spacing: int) -> int:
        if not line:
            return 0
        return len(line) * char_width + max(0, len(line) - 1) * spacing

    @staticmethod
    def _compute_content_height(line_count: int, char_height: int, line_spacing: int) -> int:
        if line_count == 0:
            return 0
        return line_count * char_height + max(0, line_count - 1) * line_spacing

    @staticmethod
    def _align_horizontal(width: int, content_width: int, alignment: str) -> int:
        if alignment == "left":
            return 0
        if alignment == "right":
            return max(0, width - content_width)
        return max(0, (width - content_width) // 2)

    @staticmethod
    def _align_vertical(height: int, content_height: int) -> int:
        if content_height >= height:
            return 0
        return max(0, (height - content_height) // 2)

    @staticmethod
    def _stamp_glyph(
        glyph: Sequence[Sequence[bool]],
        origin_x: int,
        origin_y: int,
        glyph_width: int,
        glyph_height: int,
        canvas_width: int,
        canvas_height: int,
        pixels: List[RGB],
        record_only: bool = False,
    ) -> List[Tuple[int, int]]:
        drawn: List[Tuple[int, int]] = []
        for gy in range(min(glyph_height, len(glyph))):
            row = glyph[gy]
            for gx in range(min(glyph_width, len(row))):
                if not row[gx]:
                    continue
                x = origin_x + gx
                y = origin_y + gy
                if 0 <= x < canvas_width and 0 <= y < canvas_height:
                    if record_only:
                        drawn.append((x, y))
                    else:
                        idx = y * canvas_width + x
                        pixels[idx] = (255, 255, 255)
        return drawn

    def _apply_shadow(
        self,
        points: List[Tuple[int, int]],
        options: TextRenderOptions,
        pixels: List[RGB],
        width: int,
        height: int,
    ) -> None:
        shadow_color = options.shadow_color or (20, 20, 20)
        dx, dy = options.shadow_offset
        for x, y in points:
            sx = x + dx
            sy = y + dy
            if 0 <= sx < width and 0 <= sy < height:
                idx = sy * width + sx
                pixels[idx] = shadow_color

    def _apply_outline(
        self,
        points: List[Tuple[int, int]],
        options: TextRenderOptions,
        pixels: List[RGB],
        width: int,
        height: int,
    ) -> None:
        outline_color = options.outline_color or options.color
        thickness = max(1, options.outline_thickness)
        point_set = set(points)
        for x, y in list(points):
            for dx in range(-thickness, thickness + 1):
                for dy in range(-thickness, thickness + 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx = x + dx
                    ny = y + dy
                    if (nx, ny) in point_set:
                        continue
                    if 0 <= nx < width and 0 <= ny < height:
                        idx = ny * width + nx
                        if pixels[idx] == options.background:
                            pixels[idx] = outline_color

    def _apply_fill(
        self,
        points: List[Tuple[int, int]],
        options: TextRenderOptions,
        pixels: List[RGB],
        width: int,
        height: int,
    ) -> None:
        if not points:
            return
        min_y = min(y for _, y in points)
        max_y = max(y for _, y in points)
        min_x = min(x for x, _ in points)
        max_x = max(x for x, _ in points)
        for x, y in points:
            idx = y * width + x
            pixels[idx] = self._pixel_color(x, y, min_x, max_x, min_y, max_y, options)

    @staticmethod
    def _pixel_color(
        x: int,
        y: int,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int,
        options: TextRenderOptions,
    ) -> RGB:
        if not options.gradient:
            return options.color
        start = options.gradient_start or options.color
        end = options.gradient_end or options.color
        if options.gradient_orientation == "horizontal":
            span = max(1, max_x - min_x)
            t = (x - min_x) / span
        else:
            span = max(1, max_y - min_y)
            t = (y - min_y) / span
        return (
            int(start[0] * (1 - t) + end[0] * t),
            int(start[1] * (1 - t) + end[1] * t),
            int(start[2] * (1 - t) + end[2] * t),
        )

    def _build_scroll_workspace(
        self,
        text: str,
        options: TextRenderOptions,
        scroll: TextScrollOptions,
        char_width: int,
        char_height: int,
    ) -> Tuple[TextRenderOptions, int]:
        if scroll.direction in ("left", "right"):
            extra = self._compute_line_width(text, char_width, options.spacing) + options.width + scroll.padding
            work_width = max(extra, options.width)
            work_height = options.height
            total_steps = max(1, work_width - options.width)
            work_options = replace(options, width=work_width, alignment="left")
        else:
            lines = text.splitlines() if options.multiline else [text]
            extra = self._compute_content_height(len(lines), char_height, options.line_spacing) + options.height + scroll.padding
            work_height = max(extra, options.height)
            work_width = options.width
            total_steps = max(1, work_height - options.height)
            work_options = replace(options, height=work_height, alignment="center")
        return work_options, total_steps

    @staticmethod
    def _scroll_offset(step: int, scroll: TextScrollOptions, work_opts: TextRenderOptions, view_opts: TextRenderOptions) -> Tuple[int, int]:
        if scroll.direction == "right":
            max_offset = max(0, work_opts.width - view_opts.width)
            return (max(0, max_offset - step), 0)
        if scroll.direction == "left":
            max_offset = max(0, work_opts.width - view_opts.width)
            return (min(step, max_offset), 0)
        if scroll.direction == "down":
            max_offset = max(0, work_opts.height - view_opts.height)
            return (0, max(0, max_offset - step))
        max_offset = max(0, work_opts.height - view_opts.height)
        return (0, min(step, max_offset))

    @staticmethod
    def _crop_pixels(
        pixels: List[RGB],
        source_width: int,
        target_width: int,
        target_height: int,
        offset: Tuple[int, int],
    ) -> List[RGB]:
        ox, oy = offset
        cropped: List[RGB] = []
        source_height = len(pixels) // source_width
        for row in range(target_height):
            src_y = row + oy
            # Corrected cropping bounds check
            if 0 <= src_y < source_height:
                for col in range(target_width):
                    src_x = col + ox
                    if 0 <= src_x < source_width:
                        idx = src_y * source_width + src_x
                        cropped.append(pixels[idx])
                    else:
                        cropped.append((0, 0, 0)) # Default background
            else:
                for _ in range(target_width):
                    cropped.append((0, 0, 0))
        return cropped

    def _render_via_pil(self, text: str, lines: List[str], options: TextRenderOptions) -> List[Tuple[int, int]]:
        """Render text using PIL and return a list of lit pixel coordinates."""
        from PIL import Image, ImageDraw, ImageFont
        
        # Try to load the font
        try:
            # Handle possible family name or path
            font_name = options.font_name
            if not font_name.lower().endswith(('.ttf', '.otf')):
                # Try common locations or just let PIL find it by name
                font = ImageFont.truetype(font_name, options.font_size)
            else:
                font = ImageFont.truetype(font_name, options.font_size)
        except Exception:
            try:
                # Fallback to load by family name if path failed
                font = ImageFont.truetype("arial.ttf", options.font_size)
            except Exception:
                font = ImageFont.load_default()

        # Measure text to center it
        # We render to a temporary high-res image and then extract points
        # For simplicity, we create an image larger than the target and center it
        temp_img = Image.new('L', (options.width * 2, options.height * 2), 0)
        draw = ImageDraw.Draw(temp_img)
        
        # Calculate total height
        total_height = 0
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            h = bbox[3] - bbox[1]
            line_heights.append(h)
            total_height += h + options.line_spacing
        
        start_y = (temp_img.height - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if options.alignment == "left":
                x = (temp_img.width - options.width) // 2
            elif options.alignment == "right":
                x = (temp_img.width + options.width) // 2 - line_width
            else: # center
                x = (temp_img.width - line_width) // 2
                
            draw.text((x, start_y), line, font=font, fill=255)
            start_y += line_heights[i] + options.line_spacing
            
        # Extract points that fall within the central window
        points = []
        win_x = (temp_img.width - options.width) // 2
        win_y = (temp_img.height - options.height) // 2
        
        for y in range(options.height):
            for x in range(options.width):
                if temp_img.getpixel((win_x + x, win_y + y)) > 128:
                    points.append((x, y))
                    
        return points


