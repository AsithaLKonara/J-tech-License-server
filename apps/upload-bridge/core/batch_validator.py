"""
Batch Pattern Validator - Validate multiple patterns at once
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .pattern import Pattern, load_pattern_from_file
from .matrix_detector import MatrixDetector, get_shared_detector

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of pattern validation"""
    file_path: str
    valid: bool
    errors: List[str]
    warnings: List[str]
    pattern: Optional[Pattern] = None
    metadata: Optional[Dict] = None


class BatchValidator:
    """
    Batch validator for multiple patterns.
    
    Features:
    - Validate multiple patterns at once
    - Generate validation reports
    - Progress tracking
    - Error collection
    """
    
    def __init__(self):
        self.detector = get_shared_detector()
        self.results: List[ValidationResult] = []
    
    def validate_pattern_file(self, file_path: str) -> ValidationResult:
        """
        Validate a single pattern file.
        
        Args:
            file_path: Path to pattern file
            
        Returns:
            ValidationResult object
        """
        errors = []
        warnings = []
        pattern = None
        metadata = None
        
        try:
            # Load pattern
            pattern = load_pattern_from_file(file_path)
            
            # Validate metadata
            validation = self._validate_pattern_metadata(pattern)
            if not validation['valid']:
                errors.append(validation['reason'])
            
            # Check dimensions
            if pattern.metadata.width * pattern.metadata.height != pattern.led_count:
                errors.append(
                    f"Dimension mismatch: {pattern.metadata.width}×{pattern.metadata.height} "
                    f"≠ {pattern.led_count} LEDs"
                )
            
            # Check frame consistency
            if pattern.frames:
                expected_leds = len(pattern.frames[0].pixels)
                for i, frame in enumerate(pattern.frames):
                    if len(frame.pixels) != expected_leds:
                        errors.append(
                            f"Frame {i} has {len(frame.pixels)} LEDs, expected {expected_leds}"
                        )
            
            # Check dimension confidence
            dimension_source = getattr(pattern.metadata, 'dimension_source', 'unknown')
            dimension_confidence = getattr(pattern.metadata, 'dimension_confidence', 0.0)
            
            if dimension_source != 'header' and dimension_confidence < 0.5:
                warnings.append(
                    f"Low confidence detection ({dimension_confidence:.0%}) from {dimension_source}"
                )
            
            # Collect metadata
            metadata = {
                'name': pattern.name,
                'led_count': pattern.led_count,
                'frame_count': pattern.frame_count,
                'width': pattern.metadata.width,
                'height': pattern.metadata.height,
                'dimension_source': dimension_source,
                'dimension_confidence': dimension_confidence,
                'duration_ms': pattern.duration_ms,
            }
            
        except Exception as e:
            errors.append(f"Failed to load pattern: {str(e)}")
            logger.error(f"Error validating {file_path}: {e}", exc_info=True)
        
        return ValidationResult(
            file_path=str(file_path),
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            pattern=pattern,
            metadata=metadata,
        )
    
    def validate_patterns(self, file_paths: List[str], progress_callback: Optional[Callable[[int, int], None]] = None) -> List[ValidationResult]:
        """
        Validate multiple pattern files.
        
        Args:
            file_paths: List of file paths to validate
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            List of ValidationResult objects
        """
        self.results = []
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            if progress_callback:
                progress_callback(i + 1, total)
            
            result = self.validate_pattern_file(file_path)
            self.results.append(result)
            
            status = "✓" if result.valid else "✗"
            logger.info(f"{status} {file_path}: {len(result.errors)} errors, {len(result.warnings)} warnings")
        
        return self.results
    
    def _validate_pattern_metadata(self, pattern: Pattern) -> dict:
        """Validate pattern metadata (same logic as preview_tab)."""
        if not pattern or not pattern.frames:
            return {'valid': False, 'reason': 'Pattern has no frames', 'should_redetect': False}
        
        expected_leds = pattern.metadata.width * pattern.metadata.height
        actual_leds = pattern.led_count
        
        if expected_leds != actual_leds:
            return {
                'valid': False,
                'reason': f'Dimension mismatch: {pattern.metadata.width}×{pattern.metadata.height}={expected_leds} but LED count={actual_leds}',
                'should_redetect': True
            }
        
        first_frame_leds = len(pattern.frames[0].pixels) if pattern.frames else 0
        if first_frame_leds != actual_leds:
            return {
                'valid': False,
                'reason': f'Frame LED count mismatch: first frame has {first_frame_leds} LEDs, expected {actual_leds}',
                'should_redetect': True
            }
        
        dimension_source = getattr(pattern.metadata, 'dimension_source', 'unknown')
        dimension_confidence = getattr(pattern.metadata, 'dimension_confidence', 0.0)
        
        if dimension_source != 'header' and dimension_confidence < 0.5:
            return {
                'valid': False,
                'reason': f'Low confidence detection ({dimension_confidence:.0%}) from {dimension_source}',
                'should_redetect': True
            }
        
        return {'valid': True, 'reason': 'Metadata is consistent', 'should_redetect': False}
    
    def generate_report_csv(self, output_path: str) -> None:
        """
        Generate CSV validation report.
        
        Args:
            output_path: Path to save CSV file
        """
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'File Path', 'Valid', 'Errors', 'Warnings', 'LED Count', 'Frame Count',
                'Width', 'Height', 'Dimension Source', 'Dimension Confidence'
            ])
            
            for result in self.results:
                writer.writerow([
                    result.file_path,
                    result.valid,
                    '; '.join(result.errors),
                    '; '.join(result.warnings),
                    result.metadata.get('led_count', '') if result.metadata else '',
                    result.metadata.get('frame_count', '') if result.metadata else '',
                    result.metadata.get('width', '') if result.metadata else '',
                    result.metadata.get('height', '') if result.metadata else '',
                    result.metadata.get('dimension_source', '') if result.metadata else '',
                    result.metadata.get('dimension_confidence', '') if result.metadata else '',
                ])
        
        logger.info(f"Validation report saved to {output_path}")
    
    def generate_report_json(self, output_path: str) -> None:
        """
        Generate JSON validation report.
        
        Args:
            output_path: Path to save JSON file
        """
        import json
        
        report_data = []
        for result in self.results:
            report_data.append({
                'file_path': result.file_path,
                'valid': result.valid,
                'errors': result.errors,
                'warnings': result.warnings,
                'metadata': result.metadata,
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Validation report saved to {output_path}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get validation summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        total = len(self.results)
        valid = sum(1 for r in self.results if r.valid)
        invalid = total - valid
        total_errors = sum(len(r.errors) for r in self.results)
        total_warnings = sum(len(r.warnings) for r in self.results)
        
        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'success_rate': (valid / total * 100) if total > 0 else 0.0,
        }

