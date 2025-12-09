"""
Pattern Sharing Service - Share and discover Budurasmala patterns.

Provides functionality for uploading, downloading, and sharing patterns
with the community.
"""

from __future__ import annotations

import json
import logging
import hashlib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SharedPattern:
    """Represents a shared pattern."""
    pattern_id: str
    name: str
    author: str
    description: str
    category: str  # "Vesak", "Buddhist", "Festival", "Custom", etc.
    tags: List[str]
    pattern_data: bytes
    thumbnail: Optional[bytes] = None
    created_at: datetime = None
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class PatternSharingService:
    """
    Service for sharing and discovering Budurasmala patterns.
    
    Features:
    - Upload patterns to marketplace
    - Download patterns from marketplace
    - Pattern ratings and reviews
    - Pattern collections
    - Search and filtering
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize pattern sharing service.
        
        Args:
            storage_path: Path to store shared patterns (local storage)
        """
        if storage_path is None:
            storage_path = Path.home() / ".upload_bridge" / "shared_patterns"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._patterns: Dict[str, SharedPattern] = {}
        self._load_local_patterns()
    
    def upload_pattern(
        self,
        pattern_data: bytes,
        name: str,
        author: str,
        description: str = "",
        category: str = "Custom",
        tags: List[str] = None,
        thumbnail: Optional[bytes] = None
    ) -> str:
        """
        Upload a pattern to the sharing service.
        
        Args:
            pattern_data: Pattern data bytes
            name: Pattern name
            author: Author name
            description: Pattern description
            category: Pattern category
            tags: List of tags
            thumbnail: Optional thumbnail image
            
        Returns:
            Pattern ID
        """
        # Generate pattern ID from hash
        pattern_hash = hashlib.sha256(pattern_data).hexdigest()[:16]
        pattern_id = f"pattern_{pattern_hash}"
        
        shared_pattern = SharedPattern(
            pattern_id=pattern_id,
            name=name,
            author=author,
            description=description,
            category=category,
            tags=tags or [],
            pattern_data=pattern_data,
            thumbnail=thumbnail
        )
        
        self._patterns[pattern_id] = shared_pattern
        self._save_pattern(shared_pattern)
        
        logger.info(f"Pattern uploaded: {name} by {author} (ID: {pattern_id})")
        return pattern_id
    
    def download_pattern(self, pattern_id: str) -> Optional[SharedPattern]:
        """
        Download a pattern by ID.
        
        Args:
            pattern_id: Pattern ID
            
        Returns:
            SharedPattern or None if not found
        """
        pattern = self._patterns.get(pattern_id)
        if pattern:
            pattern.downloads += 1
            self._save_pattern(pattern)
            return pattern
        return None
    
    def search_patterns(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_rating: float = 0.0
    ) -> List[SharedPattern]:
        """
        Search for patterns.
        
        Args:
            query: Search query (searches name, description)
            category: Filter by category
            tags: Filter by tags
            min_rating: Minimum rating
            
        Returns:
            List of matching patterns
        """
        results = []
        
        for pattern in self._patterns.values():
            # Filter by category
            if category and pattern.category != category:
                continue
            
            # Filter by rating
            if pattern.rating < min_rating:
                continue
            
            # Filter by tags
            if tags:
                if not any(tag in pattern.tags for tag in tags):
                    continue
            
            # Filter by query
            if query:
                query_lower = query.lower()
                if (query_lower not in pattern.name.lower() and
                    query_lower not in pattern.description.lower() and
                    not any(query_lower in tag.lower() for tag in pattern.tags)):
                    continue
            
            results.append(pattern)
        
        # Sort by rating and downloads
        results.sort(key=lambda p: (p.rating, p.downloads), reverse=True)
        
        return results
    
    def rate_pattern(self, pattern_id: str, rating: float) -> bool:
        """
        Rate a pattern (1.0 to 5.0).
        
        Args:
            pattern_id: Pattern ID
            rating: Rating value (1.0-5.0)
            
        Returns:
            True if successful
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return False
        
        rating = max(1.0, min(5.0, rating))
        
        # Update average rating
        total_rating = pattern.rating * pattern.rating_count + rating
        pattern.rating_count += 1
        pattern.rating = total_rating / pattern.rating_count
        
        self._save_pattern(pattern)
        return True
    
    def get_popular_patterns(self, limit: int = 10) -> List[SharedPattern]:
        """Get most popular patterns."""
        patterns = list(self._patterns.values())
        patterns.sort(key=lambda p: (p.downloads, p.rating), reverse=True)
        return patterns[:limit]
    
    def get_recent_patterns(self, limit: int = 10) -> List[SharedPattern]:
        """Get most recent patterns."""
        patterns = list(self._patterns.values())
        patterns.sort(key=lambda p: p.created_at, reverse=True)
        return patterns[:limit]
    
    def _save_pattern(self, pattern: SharedPattern):
        """Save pattern to local storage."""
        pattern_dir = self.storage_path / pattern.pattern_id
        pattern_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = {
            'pattern_id': pattern.pattern_id,
            'name': pattern.name,
            'author': pattern.author,
            'description': pattern.description,
            'category': pattern.category,
            'tags': pattern.tags,
            'created_at': pattern.created_at.isoformat(),
            'downloads': pattern.downloads,
            'rating': pattern.rating,
            'rating_count': pattern.rating_count,
            'metadata': pattern.metadata
        }
        
        with open(pattern_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Save pattern data
        with open(pattern_dir / 'pattern.bin', 'wb') as f:
            f.write(pattern.pattern_data)
        
        # Save thumbnail if available
        if pattern.thumbnail:
            with open(pattern_dir / 'thumbnail.png', 'wb') as f:
                f.write(pattern.thumbnail)
    
    def _load_local_patterns(self):
        """Load patterns from local storage."""
        if not self.storage_path.exists():
            return
        
        for pattern_dir in self.storage_path.iterdir():
            if not pattern_dir.is_dir():
                continue
            
            try:
                # Load metadata
                metadata_path = pattern_dir / 'metadata.json'
                if not metadata_path.exists():
                    continue
                
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Load pattern data
                pattern_path = pattern_dir / 'pattern.bin'
                if not pattern_path.exists():
                    continue
                
                with open(pattern_path, 'rb') as f:
                    pattern_data = f.read()
                
                # Load thumbnail if available
                thumbnail = None
                thumbnail_path = pattern_dir / 'thumbnail.png'
                if thumbnail_path.exists():
                    with open(thumbnail_path, 'rb') as f:
                        thumbnail = f.read()
                
                pattern = SharedPattern(
                    pattern_id=metadata['pattern_id'],
                    name=metadata['name'],
                    author=metadata['author'],
                    description=metadata['description'],
                    category=metadata['category'],
                    tags=metadata['tags'],
                    pattern_data=pattern_data,
                    thumbnail=thumbnail,
                    created_at=datetime.fromisoformat(metadata['created_at']),
                    downloads=metadata['downloads'],
                    rating=metadata['rating'],
                    rating_count=metadata['rating_count'],
                    metadata=metadata.get('metadata', {})
                )
                
                self._patterns[pattern.pattern_id] = pattern
                
            except Exception as e:
                logger.error(f"Failed to load pattern from {pattern_dir}: {e}")

