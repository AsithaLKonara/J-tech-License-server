"""
PCB Exporter - Export LED positions to PCB design tools.

Supports export to EasyEDA, KiCad, and Gerber format.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional
import csv
import json


class PCBExporter:
    """Export LED positions to PCB design tools."""
    
    @staticmethod
    def export_to_easyeda(
        positions: List[Tuple[float, float]],
        output_path: Path,
        units: str = "mm"
    ) -> Path:
        """
        Export LED positions to EasyEDA format (CSV).
        
        EasyEDA expects CSV with columns: Designator, Footprint, X, Y, Rotation
        
        Args:
            positions: List of (x, y) LED positions
            output_path: Output file path
            units: Units ("mm" or "inches")
            
        Returns:
            Path to exported file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(["Designator", "Footprint", "X", "Y", "Rotation"])
            
            # Write LED positions
            for i, (x, y) in enumerate(positions):
                designator = f"D{i+1}"  # D1, D2, D3, ...
                footprint = "LED_WS2812B"  # Default footprint
                rotation = 0
                
                writer.writerow([designator, footprint, x, y, rotation])
        
        return output_path
    
    @staticmethod
    def export_to_kicad(
        positions: List[Tuple[float, float]],
        output_path: Path,
        units: str = "mm"
    ) -> Path:
        """
        Export LED positions to KiCad format (JSON).
        
        KiCad uses JSON format for component placement.
        
        Args:
            positions: List of (x, y) LED positions
            output_path: Output file path
            units: Units ("mm" or "inches")
            
        Returns:
            Path to exported file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # KiCad JSON format
        kicad_data = {
            "version": 1,
            "components": []
        }
        
        for i, (x, y) in enumerate(positions):
            component = {
                "ref": f"D{i+1}",
                "footprint": "LED_WS2812B",
                "x": x,
                "y": y,
                "rotation": 0,
                "side": "top"
            }
            kicad_data["components"].append(component)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(kicad_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    @staticmethod
    def export_to_gerber(
        positions: List[Tuple[float, float]],
        output_path: Path,
        units: str = "mm",
        pad_size: float = 2.0  # Pad size in mm
    ) -> Path:
        """
        Export LED positions to basic Gerber format.
        
        Creates a simple Gerber file with pads at LED positions.
        This is a basic implementation - full Gerber support would require
        more complex format handling.
        
        Args:
            positions: List of (x, y) LED positions
            output_path: Output file path
            units: Units ("mm" or "inches")
            pad_size: Pad size in mm
            
        Returns:
            Path to exported file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Basic Gerber format (simplified)
        with open(output_path, 'w', encoding='ascii') as f:
            # Gerber header
            f.write("G04 LED Positions Gerber Export*\n")
            f.write("G04 Format: Gerber X2*\n")
            f.write("%FSLAX36Y36*%\n")  # 3.6 format (mm with 6 decimals)
            f.write("%MOMM*%\n")  # Units: millimeters
            f.write("G04 D01*\n")  # Set to linear interpolation
            
            # Draw pads for each LED position
            for i, (x, y) in enumerate(positions):
                # Move to position
                f.write(f"G04 LED {i+1} at ({x:.6f}, {y:.6f})*\n")
                f.write(f"G04*\n")
                f.write(f"D03*\n")  # Flash aperture
                # Draw circular pad
                f.write(f"G36*\n")  # Start region
                f.write(f"G01 X{x:.6f}Y{y:.6f}D02*\n")  # Move to position
                # Simple pad (circle approximation)
                f.write(f"G75*\n")  # Multi-quadrant mode
                f.write(f"G37*\n")  # End region
            
            # Footer
            f.write("M02*\n")  # End of file
        
        return output_path
    
    @staticmethod
    def export_to_csv(
        positions: List[Tuple[float, float]],
        output_path: Path,
        units: str = "mm"
    ) -> Path:
        """
        Export LED positions to generic CSV format.
        
        Args:
            positions: List of (x, y) LED positions
            output_path: Output file path
            units: Units ("mm" or "inches")
            
        Returns:
            Path to exported file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(["LED_Index", f"X ({units})", f"Y ({units})"])
            
            # Write positions
            for i, (x, y) in enumerate(positions):
                writer.writerow([i, x, y])
        
        return output_path

