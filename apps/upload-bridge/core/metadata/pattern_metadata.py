"""
Extended Pattern Metadata - Enhanced metadata utilities

Provides utilities for enriching pattern metadata with tags, categories,
and additional information for better organization and searchability.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from core.pattern import Pattern, PatternMetadata
from core.metadata.tag_taxonomy import TagTaxonomy, TagCategory


class ExtendedPatternMetadata:
    """Extended metadata with tags and categorization"""
    
    def __init__(
        self,
        pattern: Pattern,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize extended metadata.
        
        Args:
            pattern: Pattern object
            tags: List of tags
            category: Category string
            author: Author name
            description: Description text
            custom_fields: Custom metadata fields
        """
        self.pattern = pattern
        self.tags = tags or []
        self.category = category
        self.author = author or ""
        self.description = description or ""
        self.custom_fields = custom_fields or {}
        self.created_at = datetime.utcnow().isoformat() + 'Z'
        self.modified_at = datetime.utcnow().isoformat() + 'Z'
    
    def add_tag(self, tag: str) -> bool:
        """
        Add a tag if valid.
        
        Args:
            tag: Tag to add
            
        Returns:
            True if added, False if invalid
        """
        normalized = TagTaxonomy.normalize_tag(tag)
        if TagTaxonomy.validate_tag(normalized):
            if normalized not in [TagTaxonomy.normalize_tag(t) for t in self.tags]:
                self.tags.append(normalized)
                return True
        return False
    
    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag.
        
        Args:
            tag: Tag to remove
            
        Returns:
            True if removed, False if not present
        """
        normalized = TagTaxonomy.normalize_tag(tag)
        original_tags = self.tags.copy()
        self.tags = [
            t for t in self.tags
            if TagTaxonomy.normalize_tag(t) != normalized
        ]
        return len(self.tags) < len(original_tags)
    
    def get_tags_by_category(self) -> Dict[TagCategory, List[str]]:
        """Get tags organized by category"""
        return TagTaxonomy.categorize_tags(self.tags)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tags": self.tags,
            "category": self.category,
            "author": self.author,
            "description": self.description,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "custom_fields": self.custom_fields,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], pattern: Pattern) -> 'ExtendedPatternMetadata':
        """Create from dictionary"""
        return cls(
            pattern=pattern,
            tags=data.get("tags", []),
            category=data.get("category"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            custom_fields=data.get("custom_fields", {}),
        )


def enrich_pattern_metadata(
    pattern: Pattern,
    tags: Optional[List[str]] = None,
    category: Optional[str] = None,
    author: Optional[str] = None,
    description: Optional[str] = None
) -> ExtendedPatternMetadata:
    """
    Create extended metadata for a pattern.
    
    Args:
        pattern: Pattern object
        tags: Optional tags list
        category: Optional category
        author: Optional author
        description: Optional description
        
    Returns:
        ExtendedPatternMetadata object
    """
    extended = ExtendedPatternMetadata(
        pattern=pattern,
        tags=tags,
        category=category,
        author=author,
        description=description
    )
    
    # Auto-detect tags from pattern if not provided
    if not tags:
        # Could analyze pattern to suggest tags
        # For now, just return with empty tags
        pass
    
    return extended

