"""
Custom LED Position Importer - Import LED positions from CSV/JSON files.

This module supports importing custom LED positions for Budurasmala designs
with custom PCBs. Positions can be in mm, inches, or grid units.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Tuple, Optional


def import_positions_from_csv(
    file_path: Path,
    x_column: int = 0,
    y_column: int = 1,
    skip_header: bool = True,
    units: str = "mm"
) -> List[Tuple[float, float]]:
    """
    Import LED positions from CSV file.
    
    Args:
        file_path: Path to CSV file
        x_column: Column index for X coordinates (0-based)
        y_column: Column index for Y coordinates (0-based)
        skip_header: Whether to skip first row (header)
        units: Units of positions ("mm", "inches", "grid")
        
    Returns:
        List of (x, y) position tuples
        
    Raises:
        ValueError: If file cannot be read or columns are invalid
    """
    positions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            if skip_header:
                next(reader, None)  # Skip header row
            
            for row_idx, row in enumerate(reader):
                if len(row) <= max(x_column, y_column):
                    continue  # Skip rows with insufficient columns
                
                try:
                    x = float(row[x_column])
                    y = float(row[y_column])
                    positions.append((x, y))
                except (ValueError, IndexError) as e:
                    # Skip invalid rows
                    continue
    
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    if not positions:
        raise ValueError("No valid positions found in CSV file")
    
    return positions


def import_positions_from_json(
    file_path: Path,
    x_key: str = "x",
    y_key: str = "y",
    units: str = "mm"
) -> List[Tuple[float, float]]:
    """
    Import LED positions from JSON file.
    
    Expected JSON format:
    {
        "positions": [
            {"x": 10.5, "y": 20.3},
            {"x": 11.2, "y": 21.1},
            ...
        ]
    }
    
    Or array format:
    [
        {"x": 10.5, "y": 20.3},
        {"x": 11.2, "y": 21.1},
        ...
    ]
    
    Args:
        file_path: Path to JSON file
        x_key: Key name for X coordinate
        y_key: Key name for Y coordinate
        units: Units of positions ("mm", "inches", "grid")
        
    Returns:
        List of (x, y) position tuples
        
    Raises:
        ValueError: If file cannot be read or format is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        positions = []
        
        # Handle object with "positions" key
        if isinstance(data, dict) and "positions" in data:
            pos_list = data["positions"]
        # Handle direct array
        elif isinstance(data, list):
            pos_list = data
        else:
            raise ValueError("JSON must contain 'positions' array or be an array")
        
        for item in pos_list:
            if isinstance(item, dict):
                if x_key in item and y_key in item:
                    try:
                        x = float(item[x_key])
                        y = float(item[y_key])
                        positions.append((x, y))
                    except (ValueError, TypeError):
                        continue
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                # Handle [x, y] format
                try:
                    x = float(item[0])
                    y = float(item[1])
                    positions.append((x, y))
                except (ValueError, TypeError):
                    continue
        
        if not positions:
            raise ValueError("No valid positions found in JSON file")
        
        return positions
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Failed to read JSON file: {e}")


def detect_units_from_filename(file_path: Path) -> str:
    """
    Try to detect units from filename or extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        Detected units ("mm", "inches", "grid")
    """
    filename_lower = file_path.name.lower()
    
    if "inch" in filename_lower or "in" in filename_lower:
        return "inches"
    elif "mm" in filename_lower or "millimeter" in filename_lower:
        return "mm"
    else:
        return "mm"  # Default to mm for PCB designs

