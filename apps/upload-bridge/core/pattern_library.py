"""
Pattern Library - Local pattern database with search, filter, and metadata
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from .pattern import Pattern, load_pattern_from_file

logger = logging.getLogger(__name__)


@dataclass
class PatternEntry:
    """Pattern library entry"""
    id: str
    name: str
    file_path: str
    led_count: int
    frame_count: int
    width: int
    height: int
    duration_ms: int
    tags: List[str]
    category: str
    created_at: str
    last_accessed: str
    access_count: int
    thumbnail_path: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None


class PatternLibrary:
    """
    Local pattern library with SQLite database
    
    Features:
    - Pattern metadata storage
    - Search and filtering
    - Categories and tags
    - Thumbnail generation
    - Access tracking
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize pattern library
        
        Args:
            db_path: Path to SQLite database (default: ~/.upload_bridge/pattern_library.db)
        """
        if db_path is None:
            db_dir = Path.home() / ".upload_bridge"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "pattern_library.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                file_path TEXT,
                led_count INTEGER,
                frame_count INTEGER,
                width INTEGER,
                height INTEGER,
                duration_ms INTEGER,
                category TEXT DEFAULT 'Uncategorized',
                description TEXT,
                author TEXT,
                thumbnail_path TEXT,
                created_at TEXT,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT,
                tag TEXT,
                FOREIGN KEY (pattern_id) REFERENCES patterns(id),
                UNIQUE(pattern_id, tag)
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON patterns(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON patterns(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON tags(pattern_id)")
        
        conn.commit()
        conn.close()
    
    def add_pattern(self, pattern: Pattern, file_path: str, 
                   category: str = "Uncategorized", tags: List[str] = None,
                   description: str = None, author: str = None) -> str:
        """
        Add pattern to library
        
        Args:
            pattern: Pattern object
            file_path: Path to pattern file
            category: Category name
            tags: List of tag strings
            description: Optional description
            author: Optional author name
            
        Returns:
            Pattern entry ID
        """
        import uuid
        from datetime import datetime
        
        pattern_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert pattern
            cursor.execute("""
                INSERT INTO patterns (
                    id, name, file_path, led_count, frame_count,
                    width, height, duration_ms, category, description,
                    author, created_at, last_accessed, access_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_id,
                pattern.name,
                file_path,
                pattern.led_count,
                pattern.frame_count,
                pattern.metadata.width,
                pattern.metadata.height,
                pattern.duration_ms,
                category,
                description,
                author,
                now,
                now,
                0
            ))
            
            # Insert tags
            if tags:
                for tag in tags:
                    cursor.execute("""
                        INSERT INTO tags (pattern_id, tag) VALUES (?, ?)
                    """, (pattern_id, tag))
            
            conn.commit()
            logger.info(f"Added pattern to library: {pattern.name} ({pattern_id})")
            
        except sqlite3.IntegrityError as e:
            # Pattern already exists (likely by ID or other constraint), update it if it has a path
            if file_path:
                logger.warning(f"Pattern already exists, updating: {file_path}")
                pattern_id = self._get_pattern_id_by_path(file_path)
                if pattern_id:
                    self.update_pattern(pattern_id, pattern, category, tags, description, author)
                else:
                    raise
            else:
                raise
        
        finally:
            conn.close()
        
        return pattern_id
    
    def _get_pattern_id_by_path(self, file_path: str) -> Optional[str]:
        """Get pattern ID by file path"""
        if not file_path:
            return None
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM patterns WHERE file_path = ?", (file_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def update_pattern(self, pattern_id: str, pattern: Pattern = None,
                      tags: List[str] = None, **kwargs):
        """
        Update pattern metadata
        
        Args:
            pattern_id: ID of the pattern to update
            pattern: Optional Pattern object to update stats from
            tags: Optional list of tags to replace current ones
            **kwargs: Column names and values to update (e.g., thumbnail_path, category)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        # Stats from pattern object
        if pattern:
            updates.append("name = ?")
            params.append(pattern.name)
            updates.append("led_count = ?")
            params.append(pattern.led_count)
            updates.append("frame_count = ?")
            params.append(pattern.frame_count)
            updates.append("width = ?")
            params.append(pattern.metadata.width)
            updates.append("height = ?")
            params.append(pattern.metadata.height)
            updates.append("duration_ms = ?")
            params.append(pattern.duration_ms)
        
        # Arbitrary column updates
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ?")
                params.append(value)
        
        if updates:
            params.append(pattern_id)
            cursor.execute(f"""
                UPDATE patterns SET {', '.join(updates)} WHERE id = ?
            """, params)
        
        # Update tags
        if tags is not None:
            cursor.execute("DELETE FROM tags WHERE pattern_id = ?", (pattern_id,))
            for tag in tags:
                cursor.execute("INSERT INTO tags (pattern_id, tag) VALUES (?, ?)", (pattern_id, tag))
        
        conn.commit()
        conn.close()
        logger.info(f"Updated pattern metadata for: {pattern_id}")
    
    def remove_pattern(self, pattern_id: str):
        """Remove pattern from library"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tags WHERE pattern_id = ?", (pattern_id,))
        cursor.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Removed pattern from library: {pattern_id}")
    
    def search_patterns(self, query: str = None, category: str = None,
                       tags: List[str] = None, min_leds: int = None,
                       max_leds: int = None, min_frames: int = None,
                       max_frames: int = None) -> List[PatternEntry]:
        """
        Search patterns with filters
        
        Args:
            query: Text search in name/description
            category: Filter by category
            tags: Filter by tags (all must match)
            min_leds: Minimum LED count
            max_leds: Maximum LED count
            min_frames: Minimum frame count
            max_frames: Maximum frame count
            
        Returns:
            List of PatternEntry objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if query:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            query_param = f"%{query}%"
            params.extend([query_param, query_param])
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        if min_leds is not None:
            conditions.append("led_count >= ?")
            params.append(min_leds)
        
        if max_leds is not None:
            conditions.append("led_count <= ?")
            params.append(max_leds)
        
        if min_frames is not None:
            conditions.append("frame_count >= ?")
            params.append(min_frames)
        
        if max_frames is not None:
            conditions.append("frame_count <= ?")
            params.append(max_frames)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor.execute(f"""
            SELECT * FROM patterns WHERE {where_clause}
            ORDER BY last_accessed DESC, access_count DESC
        """, params)
        
        rows = cursor.fetchall()
        
        # Filter by tags if specified
        if tags:
            pattern_ids = set()
            for tag in tags:
                cursor.execute("SELECT DISTINCT pattern_id FROM tags WHERE tag = ?", (tag,))
                tag_ids = {row[0] for row in cursor.fetchall()}
                if not pattern_ids:
                    pattern_ids = tag_ids
                else:
                    pattern_ids &= tag_ids  # Intersection (all tags must match)
            
            rows = [row for row in rows if row['id'] in pattern_ids]
        
        # Convert to PatternEntry objects
        entries = []
        for row in rows:
            # Get tags for this pattern
            cursor.execute("SELECT tag FROM tags WHERE pattern_id = ?", (row['id'],))
            pattern_tags = [tag_row[0] for tag_row in cursor.fetchall()]
            
            entry = PatternEntry(
                id=row['id'],
                name=row['name'],
                file_path=row['file_path'],
                led_count=row['led_count'],
                frame_count=row['frame_count'],
                width=row['width'],
                height=row['height'],
                duration_ms=row['duration_ms'],
                tags=pattern_tags,
                category=row['category'],
                created_at=row['created_at'],
                last_accessed=row['last_accessed'],
                access_count=row['access_count'],
                thumbnail_path=row['thumbnail_path'],
                description=row['description'],
                author=row['author']
            )
            entries.append(entry)
        
        conn.close()
        return entries
    
    def get_pattern(self, pattern_id: str) -> Optional[PatternEntry]:
        """Get pattern entry by ID"""
        entries = self.search_patterns()
        for entry in entries:
            if entry.id == pattern_id:
                return entry
        return None
    
    def get_categories(self) -> List[str]:
        """Get all categories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM patterns ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories
    
    def get_tags(self) -> List[str]:
        """Get all tags"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT tag FROM tags ORDER BY tag")
        tags = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tags
    
    def record_access(self, pattern_id: str):
        """Record pattern access (for statistics)"""
        from datetime import datetime
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patterns 
            SET last_accessed = ?, access_count = access_count + 1
            WHERE id = ?
        """, (now, pattern_id))
        conn.commit()
        conn.close()
    
    def generate_thumbnail(self, pattern: Pattern, output_path: str, size: Tuple[int, int] = (128, 128)):
        """
        Generate thumbnail image for pattern
        
        Args:
            pattern: Pattern object
            output_path: Path to save thumbnail
            size: Thumbnail size (width, height)
        """
        try:
            from PIL import Image, ImageDraw
            
            width, height = size
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)
            
            if pattern.frames:
                # Use first frame for thumbnail
                frame = pattern.frames[0]
                pattern_width = pattern.metadata.width
                pattern_height = pattern.metadata.height
                
                # Scale pixels to thumbnail size
                pixel_width = width / pattern_width
                pixel_height = height / pattern_height
                
                for y in range(pattern_height):
                    for x in range(pattern_width):
                        idx = y * pattern_width + x
                        if idx < len(frame.pixels):
                            r, g, b = frame.pixels[idx]
                            x1 = int(x * pixel_width)
                            y1 = int(y * pixel_height)
                            x2 = int((x + 1) * pixel_width)
                            y2 = int((y + 1) * pixel_height)
                            draw.rectangle([x1, y1, x2, y2], fill=(r, g, b))
            
            # Save thumbnail
            img.save(output_path, 'PNG')
            logger.info(f"Generated thumbnail: {output_path}")
            
        except ImportError:
            logger.warning("PIL not available, skipping thumbnail generation")
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}", exc_info=True)

