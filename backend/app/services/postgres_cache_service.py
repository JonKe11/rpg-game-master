# backend/app/services/postgres_cache_service.py
"""
PostgreSQL Cache Service - Database operations for wiki cache.

Features:
- Fast queries with indexes
- Bulk operations (upsert batch)
- JSONB queries
- Statistics and analytics
- Automatic TTL management
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
import logging

from app.models.wiki_article import WikiArticle, ImageCache, ScrapingLog, CategoryCache

logger = logging.getLogger(__name__)


class PostgresCacheService:
    """
    PostgreSQL-backed cache for wiki articles.
    
    Replaces file-based JSON cache with queryable database.
    
    Features:
    - Indexed queries (< 5ms for most operations)
    - Full-text search (ILIKE with indexes)
    - JSONB queries (query inside JSON content)
    - Bulk operations (batch upsert)
    - TTL management (automatic expiry)
    
    Example:
        db = SessionLocal()
        service = PostgresCacheService(db)
        
        # Get all planets
        planets = service.get_articles_by_category('star_wars', 'planets')
        
        # Search
        results = service.search_articles('star_wars', 'Tato')
    """
    
    def __init__(self, db: Session, ttl_days: int = 7):
        """
        Initialize service.
        
        Args:
            db: SQLAlchemy session
            ttl_days: Time-to-live in days (default: 7)
        """
        self.db = db
        self.ttl_days = ttl_days
    
    # ============================================
    # ARTICLE OPERATIONS
    # ============================================
    
    def get_articles_by_category(
        self,
        universe: str,
        category: str,
        limit: Optional[int] = None,
        offset: int = 0,
        include_expired: bool = False
    ) -> List[WikiArticle]:
        """
        Get articles from category.
        
        Uses composite index (universe, category) for fast query!
        
        Args:
            universe: Universe name
            category: Category name
            limit: Max results (None = all)
            offset: Pagination offset
            include_expired: Include expired articles
            
        Returns:
            List of WikiArticle objects
        """
        query = self.db.query(WikiArticle).filter(
            WikiArticle.universe == universe,
            WikiArticle.category == category
        )
        
        if not include_expired:
            query = query.filter(WikiArticle.expires_at > datetime.now())
        
        query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_article_by_title(
        self,
        title: str,
        universe: str
    ) -> Optional[WikiArticle]:
        """
        Get single article by title.
        
        Uses unique index (title, universe).
        
        Args:
            title: Article title
            universe: Universe name
            
        Returns:
            WikiArticle or None
        """
        return self.db.query(WikiArticle).filter(
            WikiArticle.title == title,
            WikiArticle.universe == universe
        ).first()
    
    def search_articles(
        self,
        universe: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[WikiArticle]:
        """
        Full-text search in articles.
        
        Uses ILIKE with index for fast search.
        
        Args:
            universe: Universe name
            query: Search query
            category: Optional category filter
            limit: Max results
            
        Returns:
            List of matching articles
        """
        db_query = self.db.query(WikiArticle).filter(
            WikiArticle.universe == universe,
            WikiArticle.title.ilike(f'%{query}%'),
            WikiArticle.expires_at > datetime.now()
        )
        
        if category:
            db_query = db_query.filter(WikiArticle.category == category)
        
        return db_query.limit(limit).all()
    
    def upsert_article(
        self,
        title: str,
        universe: str,
        category: str,
        content: Dict,
        image_url: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> WikiArticle:
        """
        Insert or update article.
        
        Uses unique constraint (title, universe) for upsert logic.
        
        Args:
            title: Article title
            universe: Universe name
            category: Category name
            content: JSONB content
            image_url: Optional image URL
            source_url: Optional source URL
            
        Returns:
            WikiArticle (created or updated)
        """
        # Check if exists
        existing = self.get_article_by_title(title, universe)
        
        expires_at = datetime.now() + timedelta(days=self.ttl_days)
        
        if existing:
            # Update
            existing.category = category
            existing.content = content
            existing.image_url = image_url
            existing.source_url = source_url
            existing.scraped_at = datetime.now()
            existing.expires_at = expires_at
            existing.last_accessed = datetime.now()
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Insert
            article = WikiArticle(
                title=title,
                universe=universe,
                category=category,
                content=content,
                image_url=image_url,
                source_url=source_url,
                expires_at=expires_at
            )
            
            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)
            return article
    
    def bulk_upsert_articles(
        self,
        articles: List[Dict],
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Bulk insert/update articles.
        
        Much faster than individual upserts!
        Processes in batches to avoid memory issues.
        
        Args:
            articles: List of article dicts
            batch_size: Batch size for commits
            
        Returns:
            Dict with stats: {'created': X, 'updated': Y, 'failed': Z}
        """
        stats = {'created': 0, 'updated': 0, 'failed': 0}
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            for article_data in batch:
                try:
                    # Check if exists
                    existing = self.get_article_by_title(
                        article_data['title'],
                        article_data['universe']
                    )
                    
                    if existing:
                        # Update
                        existing.category = article_data['category']
                        existing.content = article_data.get('content', {})
                        existing.image_url = article_data.get('image_url')
                        existing.source_url = article_data.get('source_url')
                        existing.scraped_at = datetime.now()
                        existing.expires_at = datetime.now() + timedelta(days=self.ttl_days)
                        stats['updated'] += 1
                    else:
                        # Insert
                        article = WikiArticle(
                            title=article_data['title'],
                            universe=article_data['universe'],
                            category=article_data['category'],
                            content=article_data.get('content', {}),
                            image_url=article_data.get('image_url'),
                            source_url=article_data.get('source_url'),
                            expires_at=datetime.now() + timedelta(days=self.ttl_days)
                        )
                        self.db.add(article)
                        stats['created'] += 1
                        
                except Exception as e:
                    logger.error(f"Error upserting {article_data.get('title')}: {e}")
                    stats['failed'] += 1
            
            # Commit batch
            try:
                self.db.commit()
            except Exception as e:
                logger.error(f"Batch commit error: {e}")
                self.db.rollback()
        
        logger.info(f"Bulk upsert complete: {stats}")
        return stats
    
    def mark_image_cached(
        self,
        article_id: int,
        cache_path: str
    ):
        """
        Mark article's image as cached.
        
        Args:
            article_id: Article ID
            cache_path: Path to cached image file
        """
        article = self.db.query(WikiArticle).filter(
            WikiArticle.id == article_id
        ).first()
        
        if article:
            article.image_cached = True
            article.image_cache_path = cache_path
            self.db.commit()
    
    # ============================================
    # CATEGORY STATISTICS
    # ============================================
    
    def get_category_counts(self, universe: str) -> Dict[str, int]:
        """
        Get article counts per category.
        
        Uses SQL GROUP BY - very fast!
        
        Args:
            universe: Universe name
            
        Returns:
            Dict: {category: count}
        """
        results = self.db.query(
            WikiArticle.category,
            func.count(WikiArticle.id)
        ).filter(
            WikiArticle.universe == universe,
            WikiArticle.expires_at > datetime.now()
        ).group_by(
            WikiArticle.category
        ).all()
        
        return {category: count for category, count in results}
    
    def update_category_cache(self, universe: str):
        """
        Update pre-computed category cache.
        
        Stores counts in category_cache table for instant access.
        
        Args:
            universe: Universe name
        """
        counts = self.get_category_counts(universe)
        
        for category, count in counts.items():
            # Count articles with images
            images_count = self.db.query(func.count(WikiArticle.id)).filter(
                WikiArticle.universe == universe,
                WikiArticle.category == category,
                WikiArticle.image_cached == True,
                WikiArticle.expires_at > datetime.now()
            ).scalar()
            
            # Upsert cache entry
            existing = self.db.query(CategoryCache).filter(
                CategoryCache.universe == universe,
                CategoryCache.category == category
            ).first()
            
            if existing:
                existing.article_count = count
                existing.articles_with_images = images_count
                existing.last_updated = datetime.now()
            else:
                cache_entry = CategoryCache(
                    universe=universe,
                    category=category,
                    article_count=count,
                    articles_with_images=images_count
                )
                self.db.add(cache_entry)
        
        self.db.commit()
        logger.info(f"Category cache updated for {universe}")
    
    def get_category_cache(self, universe: str) -> Dict[str, Dict]:
        """
        Get cached category statistics (instant!).
        
        Args:
            universe: Universe name
            
        Returns:
            Dict with category stats
        """
        results = self.db.query(CategoryCache).filter(
            CategoryCache.universe == universe
        ).all()
        
        return {
            cache.category: {
                'count': cache.article_count,
                'with_images': cache.articles_with_images,
                'last_updated': cache.last_updated.isoformat()
            }
            for cache in results
        }
    
    # ============================================
    # IMAGE CACHE
    # ============================================
    
    def register_image(
        self,
        url: str,
        url_hash: str,
        local_path: str,
        size_bytes: Optional[int] = None,
        format: Optional[str] = None
    ) -> ImageCache:
        """
        Register downloaded image in database.
        
        Args:
            url: Image URL
            url_hash: MD5 hash of URL
            local_path: Local filesystem path
            size_bytes: File size
            format: Image format (png, jpg, etc)
            
        Returns:
            ImageCache object
        """
        # Check if exists
        existing = self.db.query(ImageCache).filter(
            ImageCache.url_hash == url_hash
        ).first()
        
        if existing:
            # Update access time
            existing.last_accessed = datetime.now()
            existing.access_count += 1
            self.db.commit()
            return existing
        
        # Create new
        image = ImageCache(
            url=url,
            url_hash=url_hash,
            local_path=local_path,
            size_bytes=size_bytes,
            format=format
        )
        
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        
        return image
    
    def is_image_cached(self, url_hash: str) -> bool:
        """
        Check if image is in cache.
        
        Args:
            url_hash: MD5 hash of URL
            
        Returns:
            True if cached and valid
        """
        return self.db.query(ImageCache).filter(
            ImageCache.url_hash == url_hash,
            ImageCache.is_valid == True
        ).first() is not None
    
    def get_image_cache_stats(self) -> Dict:
        """
        Get image cache statistics.
        
        Returns:
            Dict with stats
        """
        total = self.db.query(func.count(ImageCache.id)).scalar()
        valid = self.db.query(func.count(ImageCache.id)).filter(
            ImageCache.is_valid == True
        ).scalar()
        total_size = self.db.query(func.sum(ImageCache.size_bytes)).scalar() or 0
        
        return {
            'total_images': total,
            'valid_images': valid,
            'invalid_images': total - valid,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2)
        }
    
    # ============================================
    # SCRAPING LOGS
    # ============================================
    
    def create_scraping_log(
        self,
        universe: str,
        operation_type: str
    ) -> ScrapingLog:
        """
        Start new scraping operation log.
        
        Args:
            universe: Universe name
            operation_type: Operation type (e.g., 'categorize_articles')
            
        Returns:
            ScrapingLog object
        """
        log = ScrapingLog(
            universe=universe,
            operation_type=operation_type,
            status='running'
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        logger.info(f"Started scraping log #{log.id}: {operation_type}")
        return log
    
    def complete_scraping_log(
        self,
        log_id: int,
        stats: Dict,
        status: str = 'completed',
        error_message: Optional[str] = None
    ):
        """
        Complete scraping operation log.
        
        Args:
            log_id: Log ID
            stats: Statistics dict
            status: Status ('completed' or 'failed')
            error_message: Optional error message
        """
        log = self.db.query(ScrapingLog).filter(
            ScrapingLog.id == log_id
        ).first()
        
        if not log:
            logger.error(f"Log #{log_id} not found")
            return
        
        log.status = status
        log.completed_at = datetime.now()
        log.articles_processed = stats.get('articles_processed', 0)
        log.articles_created = stats.get('articles_created', 0)
        log.articles_updated = stats.get('articles_updated', 0)
        log.images_downloaded = stats.get('images_downloaded', 0)
        log.images_cached = stats.get('images_cached', 0)
        log.images_failed = stats.get('images_failed', 0)
        log.errors_count = stats.get('errors_count', 0)
        log.error_message = error_message
        
        # Calculate duration
        if log.started_at:
            duration = (log.completed_at - log.started_at).total_seconds()
            log.duration_seconds = int(duration)
        
        self.db.commit()
        
        logger.info(f"Completed scraping log #{log_id}: {status}")
    
    def get_recent_logs(
        self,
        universe: Optional[str] = None,
        limit: int = 10
    ) -> List[ScrapingLog]:
        """
        Get recent scraping logs.
        
        Args:
            universe: Optional universe filter
            limit: Max results
            
        Returns:
            List of ScrapingLog objects
        """
        query = self.db.query(ScrapingLog).order_by(
            ScrapingLog.started_at.desc()
        )
        
        if universe:
            query = query.filter(ScrapingLog.universe == universe)
        
        return query.limit(limit).all()
    
    # ============================================
    # MAINTENANCE
    # ============================================
    
    def cleanup_expired(self, universe: Optional[str] = None) -> int:
        """
        Delete expired articles.
        
        Args:
            universe: Optional universe filter
            
        Returns:
            Number of deleted articles
        """
        query = self.db.query(WikiArticle).filter(
            WikiArticle.expires_at < datetime.now()
        )
        
        if universe:
            query = query.filter(WikiArticle.universe == universe)
        
        count = query.count()
        query.delete()
        self.db.commit()
        
        logger.info(f"🗑️ Cleaned up {count} expired articles")
        return count
    
    def get_cache_stats(self, universe: str) -> Dict:
        """
        Get comprehensive cache statistics.
        
        Args:
            universe: Universe name
            
        Returns:
            Dict with all stats
        """
        # Article stats
        total_articles = self.db.query(func.count(WikiArticle.id)).filter(
            WikiArticle.universe == universe,
            WikiArticle.expires_at > datetime.now()
        ).scalar()
        
        articles_with_images = self.db.query(func.count(WikiArticle.id)).filter(
            WikiArticle.universe == universe,
            WikiArticle.image_cached == True,
            WikiArticle.expires_at > datetime.now()
        ).scalar()
        
        # Category counts
        category_counts = self.get_category_counts(universe)
        
        # Image stats
        image_stats = self.get_image_cache_stats()
        
        return {
            'universe': universe,
            'total_articles': total_articles,
            'articles_with_images': articles_with_images,
            'categories': category_counts,
            'images': image_stats
        }