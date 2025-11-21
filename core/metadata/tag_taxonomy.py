"""
Tag Taxonomy System - Categorization and tagging for LED patterns

Defines tag categories and validation rules for pattern tags.
"""

from enum import Enum
from typing import List, Dict, Set, Optional


class TagCategory(Enum):
    """Tag categories for pattern organization"""
    ANIMATION = "animation"
    TEXT = "text"
    EFFECTS = "effects"
    GEOMETRIC = "geometric"
    NATURE = "nature"
    ABSTRACT = "abstract"
    HOLIDAY = "holiday"
    SEASONAL = "seasonal"
    SPORTS = "sports"
    TECHNOLOGY = "technology"
    GAMING = "gaming"
    MUSIC = "music"
    CUSTOM = "custom"


class TagTaxonomy:
    """Tag taxonomy and validation system"""
    
    # Predefined tags by category
    TAG_CATEGORIES: Dict[TagCategory, List[str]] = {
        TagCategory.ANIMATION: [
            "scroll", "rotate", "pulse", "fade", "wave", "spiral",
            "chase", "wipe", "reveal", "bounce", "flash", "strobe"
        ],
        TagCategory.TEXT: [
            "alphabet", "numbers", "symbols", "words", "sentences",
            "scrolling-text", "static-text"
        ],
        TagCategory.EFFECTS: [
            "gradient", "rainbow", "fire", "water", "smoke",
            "particles", "sparkles", "matrix-rain"
        ],
        TagCategory.GEOMETRIC: [
            "circle", "square", "rectangle", "triangle", "line",
            "grid", "checkerboard", "diamond"
        ],
        TagCategory.NATURE: [
            "flower", "tree", "leaf", "sun", "moon", "star",
            "cloud", "rain", "snow"
        ],
        TagCategory.ABSTRACT: [
            "noise", "random", "chaos", "fractal", "mandala"
        ],
        TagCategory.HOLIDAY: [
            "christmas", "halloween", "easter", "valentines",
            "new-year", "thanksgiving", "independence-day"
        ],
        TagCategory.SEASONAL: [
            "spring", "summer", "autumn", "winter"
        ],
        TagCategory.SPORTS: [
            "football", "basketball", "soccer", "baseball", "tennis"
        ],
        TagCategory.TECHNOLOGY: [
            "loading", "progress", "signal", "data", "network"
        ],
        TagCategory.GAMING: [
            "pacman", "tetris", "pong", "snake", "space-invaders"
        ],
        TagCategory.MUSIC: [
            "audio-reactive", "spectrum", "beat", "frequency", "vu-meter"
        ],
        TagCategory.CUSTOM: []  # User-defined tags
    }
    
    # Reserved tags that cannot be used
    RESERVED_TAGS: Set[str] = {
        "internal", "system", "template", "default"
    }
    
    # Maximum tag length
    MAX_TAG_LENGTH = 64
    
    @classmethod
    def get_all_tags(cls) -> List[str]:
        """Get all predefined tags"""
        all_tags = []
        for category_tags in cls.TAG_CATEGORIES.values():
            all_tags.extend(category_tags)
        return sorted(set(all_tags))
    
    @classmethod
    def get_tags_by_category(cls, category: TagCategory) -> List[str]:
        """Get tags for a specific category"""
        return cls.TAG_CATEGORIES.get(category, [])
    
    @classmethod
    def get_category_for_tag(cls, tag: str) -> Optional[TagCategory]:
        """Get category for a tag"""
        tag_lower = tag.lower()
        for category, tags in cls.TAG_CATEGORIES.items():
            if tag_lower in [t.lower() for t in tags]:
                return category
        return TagCategory.CUSTOM
    
    @classmethod
    def validate_tag(cls, tag: str) -> bool:
        """
        Validate a tag.
        
        Args:
            tag: Tag string to validate
            
        Returns:
            True if valid
        """
        if not tag or not isinstance(tag, str):
            return False
        
        # Check length
        if len(tag) > cls.MAX_TAG_LENGTH:
            return False
        
        # Check reserved tags
        if tag.lower() in cls.RESERVED_TAGS:
            return False
        
        # Check characters (alphanumeric, dash, underscore)
        if not all(c.isalnum() or c in ['-', '_'] for c in tag):
            return False
        
        return True
    
    @classmethod
    def normalize_tag(cls, tag: str) -> str:
        """
        Normalize a tag (lowercase, strip whitespace).
        
        Args:
            tag: Tag to normalize
            
        Returns:
            Normalized tag
        """
        return tag.lower().strip().replace(' ', '-')
    
    @classmethod
    def categorize_tags(cls, tags: List[str]) -> Dict[TagCategory, List[str]]:
        """
        Categorize a list of tags.
        
        Args:
            tags: List of tags to categorize
            
        Returns:
            Dictionary mapping categories to tags
        """
        categorized: Dict[TagCategory, List[str]] = {}
        uncategorized = []
        
        for tag in tags:
            category = cls.get_category_for_tag(tag)
            if category:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(tag)
            else:
                uncategorized.append(tag)
        
        if uncategorized:
            categorized[TagCategory.CUSTOM] = uncategorized
        
        return categorized


def get_tags_by_category(category: TagCategory) -> List[str]:
    """Get tags for a category (convenience function)"""
    return TagTaxonomy.get_tags_by_category(category)


def validate_tag(tag: str) -> bool:
    """Validate a tag (convenience function)"""
    return TagTaxonomy.validate_tag(tag)

