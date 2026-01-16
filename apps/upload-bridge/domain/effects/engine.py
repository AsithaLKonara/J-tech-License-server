"""
Effects Engine - High-level effects engine interface

This module provides the main effects engine interface that coordinates
between effect definitions, application logic, and the effects library.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from core.pattern import Pattern, Frame

from .library import EffectLibrary
from .models import EffectDefinition
from .apply import apply_effect_to_frames, generate_effect_preview


class EffectsEngine:
    """
    High-level effects engine that manages effect definitions and application.
    
    Features:
    - Effect library management
    - Effect application to patterns
    - Effect preview generation
    - Deterministic effect processing
    """
    
    def __init__(self):
        """Initialize effects engine with default library."""
        self.library = EffectLibrary()
    
    def get_effect(self, effect_id: str) -> Optional[EffectDefinition]:
        """
        Get effect definition by ID.
        
        Args:
            effect_id: Effect identifier
            
        Returns:
            EffectDefinition if found, None otherwise
        """
        return self.library.get_effect(effect_id)
    
    def list_effects(self) -> List[EffectDefinition]:
        """
        List all available effects.
        
        Returns:
            List of all effect definitions
        """
        return self.library.list_effects()
    
    def apply_effect(
        self,
        pattern: Pattern,
        effect_id: str,
        frame_indices: Optional[Iterable[int]] = None,
        intensity: float = 1.0,
        **kwargs
    ) -> Pattern:
        """
        Apply effect to pattern frames.
        
        Args:
            pattern: Pattern to apply effect to
            effect_id: Effect identifier
            frame_indices: Optional frame indices (applies to all frames if None)
            intensity: Effect intensity (0.0-1.0)
            **kwargs: Additional effect-specific parameters
            
        Returns:
            New Pattern with effect applied
        """
        from copy import deepcopy
        
        effect = self.library.get_effect(effect_id)
        if not effect:
            raise ValueError(f"Effect not found: {effect_id}")
        
        # Create copy of pattern
        new_pattern = deepcopy(pattern)
        
        # Determine frame indices
        if frame_indices is None:
            frame_indices = range(len(new_pattern.frames))
        
        # Apply effect
        apply_effect_to_frames(new_pattern, effect, frame_indices, intensity)
        
        return new_pattern
    
    def generate_preview(
        self,
        effect_id: str,
        width: int,
        height: int,
        frame_count: int = 10,
        intensity: float = 1.0
    ) -> Pattern:
        """
        Generate preview pattern for effect.
        
        Args:
            effect_id: Effect identifier
            width: Pattern width
            height: Pattern height
            frame_count: Number of preview frames
            intensity: Effect intensity (0.0-1.0)
            
        Returns:
            Preview Pattern
        """
        from core.pattern import PatternMetadata, Pattern as PatternClass
        
        effect = self.library.get_effect(effect_id)
        if not effect:
            raise ValueError(f"Effect not found: {effect_id}")
        
        # Create empty pattern
        metadata = PatternMetadata(
            width=width,
            height=height,
            color_order="RGB",
            wiring_mode="Row-major",
            data_in_corner="LT"
        )
        
        pattern = PatternClass(
            id="preview",
            name=f"{effect.name} Preview",
            metadata=metadata,
            frames=[]
        )
        
        # Generate preview frames
        preview_pattern = generate_effect_preview(
            pattern,
            effect,
            frame_count=frame_count,
            intensity=intensity
        )
        
        return preview_pattern
    
    def is_available(self, effect_id: str) -> bool:
        """
        Check if effect is available.
        
        Args:
            effect_id: Effect identifier
            
        Returns:
            True if effect is available
        """
        return self.library.has_effect(effect_id)
    
    def register_custom_effect(self, effect: EffectDefinition) -> None:
        """
        Register custom effect.
        
        Args:
            effect: Effect definition to register
        """
        self.library.add_effect(effect)
    
    def unregister_effect(self, effect_id: str) -> bool:
        """
        Unregister effect.
        
        Args:
            effect_id: Effect identifier
            
        Returns:
            True if effect was removed
        """
        return self.library.remove_effect(effect_id)


# Global effects engine instance
_global_engine: Optional[EffectsEngine] = None


def get_effects_engine() -> EffectsEngine:
    """
    Get global effects engine instance.
    
    Returns:
        Global EffectsEngine instance
    """
    global _global_engine
    if _global_engine is None:
        _global_engine = EffectsEngine()
    return _global_engine


__all__ = [
    'EffectsEngine',
    'get_effects_engine',
]

