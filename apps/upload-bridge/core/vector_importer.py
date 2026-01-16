"""
Vector Importer - Import SVG and PDF files.

This module provides functionality to import SVG and PDF vector graphics,
converting them to LED matrix patterns.
"""

from __future__ import annotations

import os
from typing import List, Tuple, Optional
from PIL import Image
from core.pattern import Pattern, Frame, PatternMetadata

RGB = Tuple[int, int, int]


class VectorImporter:
    """Handles importing SVG and PDF vector graphics into LED matrix patterns."""
    
    @staticmethod
    def import_svg(
        filepath: str,
        target_width: int,
        target_height: int,
        resize_mode: str = "fit"
    ) -> List[RGB]:
        """
        Import an SVG file and convert to RGB pixel array.
        
        Args:
            filepath: Path to SVG file
            target_width: Target matrix width
            target_height: Target matrix height
            resize_mode: "fit" (maintain aspect, pad), "stretch" (fill entire matrix), "crop" (center crop)
        
        Returns:
            List of RGB tuples in row-major order
        """
        try:
            # Try using cairosvg
            try:
                import cairosvg
                from io import BytesIO
                
                # Render SVG to PNG
                png_data = cairosvg.svg2png(url=filepath, output_width=target_width, output_height=target_height)
                img = Image.open(BytesIO(png_data))
                img = img.convert("RGB")
                
            except ImportError:
                # Fallback: try using svglib
                try:
                    from svglib.svglib import svg2rlg
                    from reportlab.graphics import renderPM
                    from io import BytesIO
                    
                    drawing = svg2rlg(filepath)
                    if drawing is None:
                        raise ValueError("Failed to parse SVG file")
                    
                    # Render to PIL Image
                    img_data = renderPM.drawToString(drawing, fmt='PNG', dpi=72)
                    img = Image.open(BytesIO(img_data))
                    img = img.convert("RGB")
                    
                except ImportError:
                    raise ImportError(
                        "SVG import requires either 'cairosvg' or 'svglib' package. "
                        "Install with: pip install cairosvg or pip install svglib reportlab"
                    )
            
            # Resize image
            img = VectorImporter._resize_image(img, target_width, target_height, resize_mode)
            
            # Convert to RGB pixel array
            pixels = []
            for y in range(target_height):
                for x in range(target_width):
                    if x < img.width and y < img.height:
                        r, g, b = img.getpixel((x, y))
                        pixels.append((r, g, b))
                    else:
                        pixels.append((0, 0, 0))
            
            return pixels
            
        except Exception as e:
            raise Exception(f"Failed to import SVG: {e}")
    
    @staticmethod
    def import_pdf(
        filepath: str,
        target_width: int,
        target_height: int,
        page_number: int = 0,
        resize_mode: str = "fit"
    ) -> List[RGB]:
        """
        Import a PDF file page and convert to RGB pixel array.
        
        Args:
            filepath: Path to PDF file
            target_width: Target matrix width
            target_height: Target matrix height
            page_number: Page number to import (0-based)
            resize_mode: "fit" (maintain aspect, pad), "stretch" (fill entire matrix), "crop" (center crop)
        
        Returns:
            List of RGB tuples in row-major order
        """
        try:
            # Try using pdf2image
            try:
                from pdf2image import convert_from_path
                
                # Convert PDF page to PIL Image
                images = convert_from_path(filepath, first_page=page_number + 1, last_page=page_number + 1)
                if not images:
                    raise ValueError(f"PDF has no page {page_number}")
                img = images[0].convert("RGB")
                
            except ImportError:
                # Fallback: try using PyMuPDF (fitz)
                try:
                    import fitz  # PyMuPDF
                    
                    doc = fitz.open(filepath)
                    if page_number >= len(doc):
                        raise ValueError(f"PDF has only {len(doc)} pages, requested page {page_number}")
                    
                    page = doc[page_number]
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    doc.close()
                    
                except ImportError:
                    raise ImportError(
                        "PDF import requires either 'pdf2image' or 'PyMuPDF' package. "
                        "Install with: pip install pdf2image or pip install PyMuPDF"
                    )
            
            # Resize image
            img = VectorImporter._resize_image(img, target_width, target_height, resize_mode)
            
            # Convert to RGB pixel array
            pixels = []
            for y in range(target_height):
                for x in range(target_width):
                    if x < img.width and y < img.height:
                        r, g, b = img.getpixel((x, y))
                        pixels.append((r, g, b))
                    else:
                        pixels.append((0, 0, 0))
            
            return pixels
            
        except Exception as e:
            raise Exception(f"Failed to import PDF: {e}")
    
    @staticmethod
    def import_pdf_all_pages(
        filepath: str,
        target_width: int,
        target_height: int,
        resize_mode: str = "fit"
    ) -> Pattern:
        """
        Import all pages from a PDF file as a multi-frame pattern.
        
        Args:
            filepath: Path to PDF file
            target_width: Target matrix width
            target_height: Target matrix height
            resize_mode: "fit" (maintain aspect, pad), "stretch" (fill entire matrix), "crop" (center crop)
        
        Returns:
            Pattern with one frame per PDF page
        """
        try:
            # Try using pdf2image
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(filepath)
                
            except ImportError:
                # Fallback: try using PyMuPDF
                try:
                    import fitz  # PyMuPDF
                    images = []
                    doc = fitz.open(filepath)
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        images.append(img)
                    doc.close()
                    
                except ImportError:
                    raise ImportError(
                        "PDF import requires either 'pdf2image' or 'PyMuPDF' package. "
                        "Install with: pip install pdf2image or pip install PyMuPDF"
                    )
            
            frames = []
            for img in images:
                img = img.convert("RGB")
                img = VectorImporter._resize_image(img, target_width, target_height, resize_mode)
                
                # Convert to RGB pixel array
                pixels = []
                for y in range(target_height):
                    for x in range(target_width):
                        if x < img.width and y < img.height:
                            r, g, b = img.getpixel((x, y))
                            pixels.append((r, g, b))
                        else:
                            pixels.append((0, 0, 0))
                
                frames.append(Frame(pixels=pixels, duration_ms=100))
            
            metadata = PatternMetadata(width=target_width, height=target_height)
            return Pattern(name="Imported PDF", metadata=metadata, frames=frames)
            
        except Exception as e:
            raise Exception(f"Failed to import PDF: {e}")
    
    @staticmethod
    def _resize_image(img: Image.Image, target_width: int, target_height: int, resize_mode: str) -> Image.Image:
        """Resize image according to resize mode."""
        if resize_mode == "stretch":
            return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        elif resize_mode == "crop":
            # Center crop
            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            # Center crop to exact size
            left = (img.width - target_width) // 2
            top = (img.height - target_height) // 2
            return img.crop((left, top, left + target_width, top + target_height))
        else:  # fit
            # Maintain aspect ratio, pad with black
            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            new_img = Image.new("RGB", (target_width, target_height), (0, 0, 0))
            x_offset = (target_width - img.width) // 2
            y_offset = (target_height - img.height) // 2
            new_img.paste(img, (x_offset, y_offset))
            return new_img
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported vector formats."""
        return ["SVG", "PDF"]

