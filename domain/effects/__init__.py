"""
Effects Package - Effect definitions, library, and engine

Provides complete effects system for LED pattern effects.
"""

from .models import EffectDefinition
from .library import EffectLibrary
from .apply import apply_effect_to_frames, generate_effect_preview
from .engine import EffectsEngine, get_effects_engine

__all__ = [
    'EffectDefinition',
    'EffectLibrary',
    'apply_effect_to_frames',
    'generate_effect_preview',
    'EffectsEngine',
    'get_effects_engine',
]
