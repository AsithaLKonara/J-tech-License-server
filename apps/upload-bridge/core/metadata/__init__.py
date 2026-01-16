"""
Metadata & Tag Taxonomy System

Provides tag taxonomy and extended metadata utilities for pattern management.
"""

from .tag_taxonomy import (
    TagTaxonomy,
    TagCategory,
    get_tags_by_category,
    validate_tag,
)
from .pattern_metadata import (
    ExtendedPatternMetadata,
    enrich_pattern_metadata,
)

__all__ = [
    'TagTaxonomy',
    'TagCategory',
    'get_tags_by_category',
    'validate_tag',
    'ExtendedPatternMetadata',
    'enrich_pattern_metadata',
]

