# backend/app/models/wiki_article.py
"""
PostgreSQL models for wiki scraping cache.

Architecture:
- WikiArticle: Structured article metadata (queryable!)
- ImageCache: Image metadata (binary files stay on filesystem!)
- ScrapingLog: Audit log for operations
- CategoryCache: Pre-computed statistics
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from app.models.database import Base


class WikiArticle(Base):
    """
    Cached wiki article with JSONB content.
    
    Replaces file-based JSON cache with queryable database.
    
    Features:
    - Fast queries with indexes (universe + category)
    - JSONB content (flexible + queryable!)
    - Automatic expiry (TTL)
    - Access tracking (statistics)
    
    Example:
        article = WikiArticle(
            title="Tatooine",
            universe="star_wars",
            category="planets",
            content={
                'description': 'Desert planet...',
                'climate': 'Arid',
                'population': 200000
            }
        )
    """
    __tablename__ = "wiki_articles"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Article identification
    title = Column(String(500), nullable=False)
    universe = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    
    # Content (JSONB = PostgreSQL superpower!)
    # Can query inside JSON: content->>'climate' = 'Arid'
    content = Column(JSONB, nullable=True, default={})
    
    # Images (metadata only, files on filesystem!)
    image_url = Column(String(1000), nullable=True)
    image_cached = Column(Boolean, default=False, index=True)
    image_cache_path = Column(String(500), nullable=True)
    
    # Source
    source_url = Column(String(1000), nullable=True)
    
    # Timestamps
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Statistics
    access_count = Column(Integer, default=0)
    
    # Composite indexes for fast queries
    __table_args__ = (
        # Most common query: universe + category
        Index('idx_universe_category', 'universe', 'category'),
        
        # Search by title
        Index('idx_title_universe', 'title', 'universe'),
        
        # Expire cleanup
        Index('idx_expires_at', 'expires_at'),
        
        # Image status
        Index('idx_image_cached', 'image_cached'),
        
        # Unique constraint
        Index('idx_unique_article', 'title', 'universe', unique=True),
    )
    
    def __repr__(self):
        return f"<WikiArticle(title='{self.title}', universe='{self.universe}', category='{self.category}')>"
    
    def is_expired(self) -> bool:
        """Check if article is expired."""
        return datetime.now() > self.expires_at
    
    def extend_ttl(self, days: int = 7):
        """Extend TTL by X days."""
        self.expires_at = datetime.now() + timedelta(days=days)


class ImageCache(Base):
    """
    Image cache metadata.
    
    Tracks downloaded images (binary files stored on filesystem).
    
    Features:
    - URL → local path mapping
    - Size tracking
    - Access statistics
    - Validation status
    
    Example:
        image = ImageCache(
            url="https://fandom.com/image.png",
            url_hash="abc123...",
            local_path="./image_cache/abc123.img",
            size_bytes=51200
        )
    """
    __tablename__ = "image_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # URL identification
    url = Column(String(1000), nullable=False)
    url_hash = Column(String(32), unique=True, nullable=False, index=True)  # MD5 hash
    
    # Local storage
    local_path = Column(String(500), nullable=False)
    size_bytes = Column(BigInteger, nullable=True)
    format = Column(String(10), nullable=True)  # png, jpg, webp, gif
    
    # Validation
    is_valid = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    cached_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    access_count = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index('idx_url_hash', 'url_hash'),
        Index('idx_is_valid', 'is_valid'),
        Index('idx_cached_at', 'cached_at'),
    )
    
    def __repr__(self):
        return f"<ImageCache(url_hash='{self.url_hash}', size={self.size_bytes})>"
    
    def mark_invalid(self, reason: str):
        """Mark image as invalid."""
        self.is_valid = False
        self.error_message = reason


class ScrapingLog(Base):
    """
    Audit log for scraping operations.
    
    Tracks:
    - When scraping happened
    - How long it took
    - How many articles processed
    - Errors
    
    Example:
        log = ScrapingLog(
            universe="star_wars",
            operation_type="categorize_articles",
            status="running"
        )
        # ... do work ...
        log.status = "completed"
        log.articles_processed = 52986
    """
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Operation info
    universe = Column(String(50), nullable=False, index=True)
    operation_type = Column(String(100), nullable=False, index=True)
    
    # Statistics
    articles_processed = Column(Integer, default=0)
    articles_created = Column(Integer, default=0)
    articles_updated = Column(Integer, default=0)
    images_downloaded = Column(Integer, default=0)
    images_cached = Column(Integer, default=0)
    images_failed = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Performance
    duration_seconds = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, index=True)  # running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default={})
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_operation_type', 'operation_type'),
        Index('idx_started_at', 'started_at'),
    )
    
    def __repr__(self):
        return f"<ScrapingLog(operation='{self.operation_type}', status='{self.status}')>"
    
    def complete(self, status: str = 'completed'):
        """Mark log as completed."""
        self.status = status
        self.completed_at = datetime.now()
        
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = int(duration)


class CategoryCache(Base):
    """
    Pre-computed category statistics.
    
    Materialized view for fast counts.
    
    Features:
    - Article counts per category
    - Last update timestamp
    - Universe-specific
    
    Example:
        cache = CategoryCache(
            universe="star_wars",
            category="planets",
            article_count=2195
        )
    """
    __tablename__ = "category_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    universe = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    
    # Statistics
    article_count = Column(Integer, default=0)
    articles_with_images = Column(Integer, default=0)
    
    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Additional stats
    extra_metadata = Column(JSONB, nullable=True, default={})
    
    # Indexes
    __table_args__ = (
        Index('idx_universe_category_unique', 'universe', 'category', unique=True),
    )
    
    def __repr__(self):
        return f"<CategoryCache(universe='{self.universe}', category='{self.category}', count={self.article_count})>"