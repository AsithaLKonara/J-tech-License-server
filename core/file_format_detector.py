"""
File Format Detector - Auto-detect wiring mode and data-in corner from pattern data

This module analyzes pattern pixel data to determine the most likely wiring format.
It uses heuristics based on pixel patterns and corner/edge analysis.
"""

from typing import Tuple, Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

from .pattern import Pattern
from .matrix_mapper import (
    MatrixMappingOptions,
    get_linear_index,
    unwrap_pixels_to_design_order,
)
from .dimension_scorer import _pixel_alignment_bonus


def _average_neighbor_diff(pixels: List[Tuple[int, int, int]], step: int) -> float:
    """Average RGB difference between pixels separated by `step`."""
    if step <= 0 or step >= len(pixels):
        return 0.0
    total = 0
    count = 0
    for idx in range(len(pixels) - step):
        a = pixels[idx]
        b = pixels[idx + step]
        total += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        count += 1
    return (total / count) if count else 0.0


def _estimate_column_serpentine(
    raw_pixels: List[Tuple[int, int, int]],
    design_pixels: List[Tuple[int, int, int]],
    width: int,
    height: int,
) -> Optional[bool]:
    """Estimate whether column data alternates direction using design-order pixels."""
    if height <= 1 or len(raw_pixels) != len(design_pixels):
        return None

    serp_columns = 0
    straight_columns = 0

    for col in range(width):
        raw_start = col * height
        raw_column = raw_pixels[raw_start : raw_start + height]
        design_column = [design_pixels[row * width + col] for row in range(height)]

        straight_diff = 0
        serp_diff = 0
        for row in range(height):
            a = raw_column[row]
            straight_b = design_column[row]
            serp_b = design_column[height - 1 - row]
            straight_diff += abs(a[0] - straight_b[0]) + abs(a[1] - straight_b[1]) + abs(a[2] - straight_b[2])
            serp_diff += abs(a[0] - serp_b[0]) + abs(a[1] - serp_b[1]) + abs(a[2] - serp_b[2])

        if serp_diff + 5 < straight_diff:
            serp_columns += 1
        elif straight_diff + 5 < serp_diff:
            straight_columns += 1

    if serp_columns == straight_columns == 0:
        return None
    return serp_columns > straight_columns


def _avg_color_diff(pixels: List[Tuple[int, int, int]], step: int) -> float:
    total = 0
    count = 0
    limit = len(pixels) - step
    for i in range(limit):
        a = pixels[i]
        b = pixels[i + step]
        total += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        count += 1
    return (total / count) if count else 0.0


def _detect_row_serpentine(pixels: List[Tuple[int, int, int]], width: int, height: int) -> bool:
    if height < 2:
        return False
    row0 = pixels[0:width]
    row1 = pixels[width:width * 2]
    if len(row1) != width:
        return False

    row0_reversed = list(reversed(row0))
    reversed_matches = sum(1 for i in range(width) if row0_reversed[i] == row1[i])
    forward_matches = sum(1 for i in range(width) if row0[i] == row1[i])

    if width == 0:
        return False
    return reversed_matches >= forward_matches


def _detect_column_serpentine_from_raw(
    raw_pixels: List[Tuple[int, int, int]], 
    width: int, 
    height: int,
    frames_pixels: Optional[List[List[Tuple[int, int, int]]]] = None
) -> bool:
    """
    Detect column-serpentine from raw column-major pixel data.
    In column-serpentine, even columns go top-to-bottom, odd columns go bottom-to-top.
    
    Strategy: Analyze gradient patterns within each column to detect direction changes.
    In serpentine, alternating columns should have opposite gradients.
    """
    if height < 2 or width < 2 or len(raw_pixels) < width * height:
        return False
    
    # For column-serpentine detection, analyze gradients within columns
    # In serpentine, even columns have one gradient direction, odd columns have opposite
    
    def calculate_column_gradient(col_pixels: List[Tuple[int, int, int]]) -> float:
        """Calculate the gradient direction of a column (positive = top-to-bottom, negative = bottom-to-top)"""
        if len(col_pixels) < 2:
            return 0.0
        
        # Use brightness gradient
        gradients = []
        for i in range(len(col_pixels) - 1):
            brightness_a = sum(col_pixels[i])
            brightness_b = sum(col_pixels[i + 1])
            gradients.append(brightness_b - brightness_a)
        
        # Return average gradient
        return sum(gradients) / len(gradients) if gradients else 0.0
    
    # Check if columns have alternating gradient patterns
    column_gradients = []
    for col_idx in range(min(width, 4)):  # Check first few columns
        col_start = col_idx * height
        col_pixels = raw_pixels[col_start:col_start + height]
        if len(col_pixels) == height:
            gradient = calculate_column_gradient(col_pixels)
            column_gradients.append((col_idx, gradient))
    
    if len(column_gradients) < 2:
        return False
    
    # Check for alternating patterns
    # In serpentine, even columns should have opposite gradient to odd columns
    alternating_score = 0.0
    same_direction_score = 0.0
    
    for i in range(len(column_gradients) - 1):
        col_a_idx, grad_a = column_gradients[i]
        col_b_idx, grad_b = column_gradients[i + 1]
        
        # Check if gradients are opposite (serpentine) or same (straight)
        grad_diff = abs(grad_a - grad_b)
        grad_sum = abs(grad_a) + abs(grad_b)
        
        if grad_sum > 0:
            # If columns have opposite parity (even/odd), they should have opposite gradients in serpentine
            if (col_a_idx % 2) != (col_b_idx % 2):
                # Different parity - serpentine should have opposite gradients
                if grad_a * grad_b < 0:  # Opposite signs
                    alternating_score += grad_diff / grad_sum
                else:
                    same_direction_score += grad_diff / grad_sum
            else:
                # Same parity - both should have same gradient in serpentine
                if grad_a * grad_b > 0:  # Same signs
                    alternating_score += grad_diff / grad_sum
                else:
                    same_direction_score += grad_diff / grad_sum
    
    # Also compare adjacent columns directly (original method as fallback)
    serpentine_votes = 0
    straight_votes = 0
    serpentine_total_score = 0.0
    straight_total_score = 0.0
    
    for col_idx in range(min(width - 1, 4)):
        col_start = col_idx * height
        next_col_start = (col_idx + 1) * height
        
        if next_col_start + height > len(raw_pixels):
            break
            
        col_a = raw_pixels[col_start:col_start + height]
        col_b = raw_pixels[next_col_start:next_col_start + height]
        
        if len(col_a) != height or len(col_b) != height:
            continue
        
        # Compare in both orientations
        straight_diff = 0.0
        serp_diff = 0.0

        for i in range(height):
            a = col_a[i]
            b_straight = col_b[i]
            b_serp = col_b[height - 1 - i]
            
            straight_diff += abs(a[0] - b_straight[0]) + abs(a[1] - b_straight[1]) + abs(a[2] - b_straight[2])
            serp_diff += abs(a[0] - b_serp[0]) + abs(a[1] - b_serp[1]) + abs(a[2] - b_serp[2])

        # Use a more lenient threshold
        threshold = max(3, (straight_diff + serp_diff) * 0.08)
        
        if serp_diff + threshold < straight_diff:
            serpentine_votes += 1
        elif straight_diff + threshold < serp_diff:
            straight_votes += 1
        
        serpentine_total_score += serp_diff
        straight_total_score += straight_diff
    
    # Multi-frame consensus: analyze multiple frames if provided
    if frames_pixels and len(frames_pixels) > 1:
        frame_votes_serp = 0
        frame_votes_straight = 0
        for frame_pixels in frames_pixels[1:]:  # Skip first frame (already analyzed)
            if len(frame_pixels) != width * height:
                continue
            
            # Quick check: compare column gradients across frames
            frame_gradients = []
            for col_idx in range(min(width, 3)):  # Check first few columns
                col_start = col_idx * height
                col_pixels = frame_pixels[col_start:col_start + height]
                if len(col_pixels) == height:
                    # Calculate gradient (simple brightness difference)
                    grad = sum(sum(col_pixels[i + 1]) - sum(col_pixels[i]) 
                              for i in range(len(col_pixels) - 1)) / max(1, len(col_pixels) - 1)
                    frame_gradients.append((col_idx, grad))
            
            # Check if gradients alternate (serpentine pattern)
            if len(frame_gradients) >= 2:
                alternating = 0
                same_direction = 0
                for i in range(len(frame_gradients) - 1):
                    idx_a, grad_a = frame_gradients[i]
                    idx_b, grad_b = frame_gradients[i + 1]
                    # If columns have opposite parity, they should have opposite gradients in serpentine
                    if (idx_a % 2) != (idx_b % 2):
                        if grad_a * grad_b < 0:  # Opposite signs
                            alternating += 1
                        else:
                            same_direction += 1
                
                if alternating > same_direction:
                    frame_votes_serp += 1
                elif same_direction > alternating:
                    frame_votes_straight += 1
        
        # If multiple frames agree, use consensus
        if frame_votes_serp + frame_votes_straight >= 2:
            if frame_votes_serp > frame_votes_straight * 1.5:
                return True
            elif frame_votes_straight > frame_votes_serp * 1.5:
                return False

    # Combine gradient analysis with direct comparison
    # Gradient analysis is more reliable for patterns with clear structure
    if alternating_score > same_direction_score * 1.1:
        return True
    
    # Use votes/score as fallback
    if serpentine_votes > straight_votes:
        return True
    if straight_votes > serpentine_votes:
        return False
    
    # If tied, use score comparison
    if straight_total_score > 0 or serpentine_total_score > 0:
        if serpentine_total_score < straight_total_score * 0.95:  # 5% margin
            return True
    
    return False


def _detect_row_serpentine_from_raw(
    raw_pixels: List[Tuple[int, int, int]],
    width: int,
    height: int,
) -> bool:
    if width < 2 or height < 2 or len(raw_pixels) < width * height:
        return False

    serp_votes = 0
    straight_votes = 0
    serp_score = 0.0
    straight_score = 0.0
    tolerance = 5

    for row_idx in range(height - 1):
        start_a = row_idx * width
        start_b = (row_idx + 1) * width
        row_a = raw_pixels[start_a : start_a + width]
        row_b = raw_pixels[start_b : start_b + width]
        if len(row_a) != width or len(row_b) != width:
            continue

        straight = 0.0
        serp = 0.0
        for col in range(width):
            a = row_a[col]
            b_straight = row_b[col]
            b_serp = row_b[width - 1 - col]
            straight += abs(a[0] - b_straight[0]) + abs(a[1] - b_straight[1]) + abs(a[2] - b_straight[2])
            serp += abs(a[0] - b_serp[0]) + abs(a[1] - b_serp[1]) + abs(a[2] - b_serp[2])

        if serp + tolerance < straight:
            serp_votes += 1
        elif straight + tolerance < serp:
            straight_votes += 1
        serp_score += serp
        straight_score += straight

    if serp_votes == straight_votes == 0:
        return serp_score < straight_score
    if serp_votes == straight_votes:
        return serp_score < straight_score
    return serp_votes > straight_votes


def _detect_column_serpentine(pixels: List[Tuple[int, int, int]], height: int) -> bool:
    """Legacy function - kept for compatibility but should use _detect_column_serpentine_from_raw instead."""
    if height < 2 or len(pixels) < height * 2:
        return False

    col0 = pixels[0:height]
    col1 = pixels[height:height * 2]

    forward_diff = sum(
        abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        for a, b in zip(col0, col1)
    )

    reverse_diff = sum(
        abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        for a, b in zip(col0, reversed(col1))
    )

    return reverse_diff <= forward_diff


def _contiguity_bonus(
    design_pixels: List[Tuple[int, int, int]],
    width: int,
    height: int,
    order: str,
) -> float:
    """
    Heuristic that rewards candidates where rows/columns remain contiguous.
    Diagnostic patterns typically light whole rows or columns. When the correct
    wiring is used, transitions along the driving axis are sparse compared to
    the perpendicular axis.
    """
    if width <= 0 or height <= 0 or len(design_pixels) != width * height:
        return 0.0

    def brightness(pixel: Tuple[int, int, int]) -> int:
        return pixel[0] + pixel[1] + pixel[2]

    def count_row_transitions() -> int:
        transitions = 0
        for row in range(height):
            base = row * width
            for col in range(width - 1):
                a = design_pixels[base + col]
                b = design_pixels[base + col + 1]
                if abs(brightness(a) - brightness(b)) > 10:
                    transitions += 1
        return transitions

    def count_col_transitions() -> int:
        transitions = 0
        for col in range(width):
            for row in range(height - 1):
                idx = row * width + col
                a = design_pixels[idx]
                b = design_pixels[idx + width]
                if abs(brightness(a) - brightness(b)) > 10:
                    transitions += 1
        return transitions

    row_transitions = count_row_transitions()
    col_transitions = count_col_transitions()
    if order == "row":
        target = row_transitions
        other = col_transitions
    else:
        target = col_transitions
        other = row_transitions

    if target >= other or other == 0:
        return 0.0

    diff = other - target
    total = target + other
    ratio = diff / (total + 1e-6)
    return min(0.18, max(0.0, ratio * 0.18))


def _corner_marker_bonus(
    design_pixels: List[Tuple[int, int, int]],
    width: int,
    height: int,
) -> float:
    """
    Detect diagnostic patterns that encode wiring via corner colours.
    Recognises the default LED Matrix Studio diagnostic palette:
        TL = Red, TR = Green, BL = Blue, BR = Yellow.
    """
    if width <= 1 or height <= 1 or len(design_pixels) != width * height:
        return 0.0

    expected = [
        ((255, 0, 0), 0),  # TL
        ((0, 255, 0), width - 1),  # TR
        ((0, 0, 255), width * (height - 1)),  # BL
        ((255, 255, 0), width * height - 1),  # BR
    ]
    matches = 0
    for color, idx in expected:
        actual = design_pixels[idx]
        diff = abs(actual[0] - color[0]) + abs(actual[1] - color[1]) + abs(actual[2] - color[2])
        if diff <= 50:
            matches += 1
    if matches == 0:
        return 0.0
    return min(0.2, matches * 0.05)


def _analyze_order_unwrap(
    raw_pixels: List[Tuple[int, int, int]],
    width: int,
    height: int,
    order: str,
) -> Tuple[List[Tuple[int, int, int]], Optional[bool], float]:
    best_score = float("-inf")
    best_pixels = raw_pixels
    best_serp: Optional[bool] = None
    for serp in (False, True):
        for origin in ("top_left", "top_right", "bottom_left", "bottom_right"):
            options = MatrixMappingOptions(
                width=width,
                height=height,
                order=order,
                serpentine=serp,
                origin=origin,
            )
            unwrapped = unwrap_pixels_to_design_order(raw_pixels, options)
            alignment = _pixel_alignment_bonus(unwrapped, width)
            contiguity = _contiguity_bonus(unwrapped, width, height, order)
            marker = _corner_marker_bonus(unwrapped, width, height)
            score = alignment + contiguity + marker
            if score > best_score:
                best_score = score
                best_pixels = unwrapped
                best_serp = serp
    return best_pixels, best_serp, best_score


def _score_orientation(
    frames_pixels: List[List[Tuple[int, int, int]]],
    width: int,
    height: int,
    order: str,
    serpentine: bool,
) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    if not frames_pixels:
        return {"LT": 0.0, "RT": 0.0, "LB": 0.0, "RB": 0.0}

    for origin, label in [
        ("top_left", "LT"),
        ("top_right", "RT"),
        ("bottom_left", "LB"),
        ("bottom_right", "RB"),
    ]:
        total_score = 0.0
        valid_frames = 0
        for pixels in frames_pixels:
            if len(pixels) != width * height:
                continue
            options = MatrixMappingOptions(
                width=width,
                height=height,
                order=order,
                serpentine=serpentine,
                origin=origin,
            )
            design = unwrap_pixels_to_design_order(pixels, options)
            alignment = _pixel_alignment_bonus(design, width)
            contiguity = _contiguity_bonus(design, width, height, order)
            marker = _corner_marker_bonus(design, width, height)
            total_score += alignment + contiguity + marker
            valid_frames += 1
        if valid_frames:
            scores[label] = total_score / valid_frames
        else:
            scores[label] = 0.0
    return scores


def detect_file_format(pattern: Pattern) -> Tuple[str, str]:
    """
    Auto-detect the most likely file format (wiring mode + data-in corner).
    
    Returns:
        Tuple of (wiring_mode, data_in_corner)
        e.g., ("Serpentine", "LT")
    
    Strategy:
    1. Check metadata hints from parser/filename (strong hints override)
    2. Analyze corner pixels to identify data-in corner
    3. Analyze row/column patterns to identify wiring mode
    4. Return best match with confidence score
    """
    if not pattern or not pattern.frames:
        return ("Row-major", "LT")

    width = pattern.metadata.width
    height = pattern.metadata.height

    if height <= 1:
        return ("Row-major", "LT")
    
    # Get metadata hints (from filename/parser)
    hint_confidence = getattr(pattern.metadata, 'hint_confidence', 0.0)
    wiring_hint = getattr(pattern.metadata, 'wiring_mode_hint', None)
    corner_hint = getattr(pattern.metadata, 'data_in_corner_hint', None)

    frames_to_analyze: List[List[Tuple[int, int, int]]] = []
    for frame in pattern.frames[: min(3, len(pattern.frames))]:
        frames_to_analyze.append(list(frame.pixels))

    if not frames_to_analyze:
        return ("Row-major", "LT")

    first_frame_pixels = frames_to_analyze[0]
    if width * height != len(first_frame_pixels):
        logger.warning(
            "Pixel count mismatch: expected %s, got %s",
            width * height,
            len(first_frame_pixels),
        )
        return ("Row-major", "LT")

    raw_pixels = first_frame_pixels
    analysis_pixels = raw_pixels[:]

    order_hint: Optional[str] = None
    serp_hint: Optional[bool] = None

    adjacent_diff = _average_neighbor_diff(raw_pixels, 1)
    row_step_diff = _average_neighbor_diff(raw_pixels, width) if width > 1 else None
    col_step_diff = _average_neighbor_diff(raw_pixels, height) if height > 1 else None

    storage_order: Optional[str] = None
    dominance_ratio = 1.2

    if row_step_diff is not None and col_step_diff is not None:
        if row_step_diff > col_step_diff * dominance_ratio:
            storage_order = "row"
        elif col_step_diff > row_step_diff * dominance_ratio:
            storage_order = "column"

    if storage_order is None:
        ratio_threshold = 0.8
        if row_step_diff is not None and adjacent_diff < row_step_diff * ratio_threshold:
            storage_order = "row"
        elif col_step_diff is not None and adjacent_diff < col_step_diff * ratio_threshold:
            storage_order = "column"

    row_pixels, row_serp, row_score = _analyze_order_unwrap(raw_pixels, width, height, "row")
    col_pixels, col_serp, col_score = _analyze_order_unwrap(raw_pixels, width, height, "column")

    if col_score > row_score:
        analysis_pixels = col_pixels
        order_hint = "column"
        serp_hint = col_serp
    else:
        analysis_pixels = row_pixels
        order_hint = "row"
        serp_hint = row_serp if serp_hint is None else serp_hint

    # Pass multiple frames for better column-serpentine detection
    serp_estimate_column = _detect_column_serpentine_from_raw(raw_pixels, width, height, frames_to_analyze)
    if serp_estimate_column is not None and order_hint == "column":
        serp_hint = serp_estimate_column
    serp_estimate_row = _detect_row_serpentine_from_raw(raw_pixels, width, height)
    if serp_estimate_row is not None and order_hint == "row":
        serp_hint = serp_estimate_row

    # Corner detection uses analysis_pixels (row-major design order)
    pixels = analysis_pixels

    if serp_hint is None:
        if order_hint == "row":
            serp_hint = _detect_row_serpentine(pixels, width, height)
        elif order_hint == "column":
            serp_hint = _detect_column_serpentine(pixels, height)

    candidates = []
    for order in ("row", "column"):
        for serpentine in (False, True):
            orientation_scores = _score_orientation(frames_to_analyze, width, height, order, serpentine)
            best_corner, best_score = max(orientation_scores.items(), key=lambda item: item[1])
            candidates.append(
                {
                    "order": order,
                    "serpentine": serpentine,
                    "corner": best_corner,
                    "score": best_score,
                    "scores": orientation_scores,
                }
            )

    best_candidate = None
    best_score = float("-inf")
    order_hint_bonus = 0.05  # Increased to give stronger weight to order hints
    base_serp_hint_bonus = 0.03
    # Give even stronger bonus for column-serpentine (less common, more specific)
    column_serp_bonus = 0.05 if (order_hint == "column" and serp_hint is True) else base_serp_hint_bonus

    # Helper to convert wiring mode hint to (order, serpentine) tuple
    def _parse_wiring_hint(hint: Optional[str]) -> Optional[Tuple[str, bool]]:
        """Convert wiring mode hint string to (order, serpentine) tuple"""
        if not hint:
            return None
        hint_lower = hint.lower()
        if "column-serpentine" in hint_lower or "column_serpentine" in hint_lower:
            return ("column", True)
        elif "column-major" in hint_lower or "column_major" in hint_lower:
            return ("column", False)
        elif "serpentine" in hint_lower and "row" not in hint_lower:
            # Assume row-serpentine if not column
            return ("row", True)
        elif "row-major" in hint_lower or "row_major" in hint_lower:
            return ("row", False)
        return None

    # Parse metadata hints
    metadata_wiring = _parse_wiring_hint(wiring_hint)
    metadata_order_hint = metadata_wiring[0] if metadata_wiring else None
    metadata_serp_hint = metadata_wiring[1] if metadata_wiring else None

    for candidate in candidates:
        score = candidate["score"]
        
        # Heuristic-based bonuses (existing logic)
        if order_hint and candidate["order"] == order_hint:
            score += order_hint_bonus
        if serp_hint is not None:
            # Stronger bonus for matching serpentine hint, especially for column-serpentine
            bonus = column_serp_bonus if (candidate["order"] == "column" and candidate["serpentine"]) else base_serp_hint_bonus
            if candidate["serpentine"] == serp_hint:
                score += bonus
            else:
                score -= bonus * 0.5  # Less penalty to avoid over-correction
        
        # Metadata hint bonuses (from filename/parser)
        if hint_confidence > 0 and wiring_hint:
            if metadata_order_hint and candidate["order"] == metadata_order_hint:
                # Scale bonus by hint confidence
                if hint_confidence >= 0.9:
                    # Strong hint: large bonus
                    score += 0.15
                elif hint_confidence >= 0.7:
                    # Medium hint: medium bonus
                    score += 0.10
                else:
                    # Weak hint: small bonus
                    score += 0.05
            elif metadata_order_hint and candidate["order"] != metadata_order_hint:
                # Penalize mismatch, but less aggressively for weak hints
                if hint_confidence >= 0.9:
                    score -= 0.10
                elif hint_confidence >= 0.7:
                    score -= 0.05
            
            if metadata_serp_hint is not None:
                if candidate["serpentine"] == metadata_serp_hint:
                    # Match serpentine hint
                    if hint_confidence >= 0.9:
                        score += 0.12
                    elif hint_confidence >= 0.7:
                        score += 0.08
                    else:
                        score += 0.04
                else:
                    # Mismatch serpentine hint
                    if hint_confidence >= 0.9:
                        score -= 0.08
                    elif hint_confidence >= 0.7:
                        score -= 0.04
        
        # Corner hint bonus
        if corner_hint and hint_confidence > 0:
            if candidate["corner"] == corner_hint:
                # Match corner hint
                if hint_confidence >= 0.9:
                    score += 0.10
                elif hint_confidence >= 0.7:
                    score += 0.06
                else:
                    score += 0.03
            elif hint_confidence >= 0.9:
                # Strong hint mismatch: small penalty
                score -= 0.04

        if score > best_score:
            best_score = score
            best_candidate = candidate

    assert best_candidate is not None

    order = best_candidate["order"]
    serpentine = best_candidate["serpentine"]
    best_corner = best_candidate["corner"]
    best_score = best_score  # type: ignore

    # If we have a strong serpentine hint, use it (but only if order matches)
    if serp_hint is not None:
        if order_hint == "column" and order == "column":
            serpentine = bool(serp_hint)
        elif order_hint == "row" and order == "row":
            serpentine = bool(serp_hint)
    
    # Strong metadata hints can override heuristic decisions (but check consistency)
    # Medium hints (>= 0.85) can also override, especially for column-serpentine which is less common
    if hint_confidence >= 0.85 and metadata_wiring:
        metadata_order, metadata_serp = metadata_wiring
        # For strong hints (>= 0.9), always override
        # For medium hints (>= 0.85) with column order, also override (less ambiguous than row)
        if hint_confidence >= 0.9 or (hint_confidence >= 0.85 and metadata_order == "column"):
            # Can override order: strong hints always, or medium column hints
            # Allow override when hint confidence is high enough
            order = metadata_order
            serpentine = metadata_serp
        else:
            # Medium hint with row order: only override if order matches (heuristic already agrees)
            if metadata_order == order:
                serpentine = metadata_serp
        # Corner hint overrides for medium+ hints
        if corner_hint:
            best_corner = corner_hint

    # Fallback orientation if all scores are near zero
    if best_score < 1e-6:
        best_corner = corner_hint or "LT"

    wiring_mode = (
        "Serpentine" if order == "row" and serpentine else
        "Row-major" if order == "row" else
        "Column-serpentine" if serpentine else
        "Column-major"
    )

    # Log detection method (hint vs heuristic)
    detection_method = "hint" if hint_confidence >= 0.9 and wiring_hint else "heuristic"
    logger.info(
        "🔍 Auto-detected file format: %s %s (score=%.4f, method=%s, hint_conf=%.2f)",
        wiring_mode,
        best_corner,
        best_score,
        detection_method,
        hint_confidence,
    )

    return wiring_mode, best_corner


def detect_file_format_with_confidence(pattern: Pattern) -> Tuple[str, str, float, str]:
    """
    Auto-detect file format with confidence score (0.0-1.0) and detection reason.
    
    Returns:
        Tuple of (wiring_mode, data_in_corner, confidence, reason)
        reason: "strong_hint", "medium_hint", "weak_hint", "heuristic", "low_confidence"
    """
    if not pattern or not pattern.frames:
        return ("Row-major", "LT", 0.5, "fallback")
    
    # Check metadata hints first
    hint_confidence = getattr(pattern.metadata, 'hint_confidence', 0.0)
    wiring_hint = getattr(pattern.metadata, 'wiring_mode_hint', None)
    corner_hint = getattr(pattern.metadata, 'data_in_corner_hint', None)
    
    # Run detection
    wiring, corner = detect_file_format(pattern)
    
    # Calculate confidence based on hints and heuristics
    confidence = 0.6  # Base confidence
    reason = "heuristic"
    
    if hint_confidence >= 0.9 and wiring_hint:
        # Strong hint from filename/metadata
        confidence = min(0.95, hint_confidence)
        reason = "strong_hint"
    elif hint_confidence >= 0.7:
        # Medium hint: good confidence but verify
        confidence = min(0.85, 0.6 + hint_confidence * 0.3)
        reason = "medium_hint"
    elif hint_confidence > 0:
        # Weak hint: slight boost
        confidence = min(0.75, 0.6 + hint_confidence * 0.2)
        reason = "weak_hint"
    else:
        # Pure heuristic: confidence depends on score
        # We need to check the actual detection score (would need to refactor to return it)
        # For now, use base confidence
        confidence = 0.65
        reason = "heuristic"
    
    # Low confidence threshold
    if confidence < 0.6:
        reason = "low_confidence"
    
    return (wiring, corner, confidence, reason)

