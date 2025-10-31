# backend/app/services/postgres_cache_service.py
"""
PostgreSQL Cache Service - Database operations for wiki cache.

✅ FIXED VERSION:
- Timezone-aware datetimes
- Deduplication in bulk upsert
- Complete scraping log method

Features:
- Fast queries with indexes
- Bulk operations (upsert batch)
- JSONB queries
- Statistics and analytics
- Automatic TTL management
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.dialects.postgresql import insert
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
            query = query.filter(WikiArticle.expires_at > datetime.now(timezone.utc))
        
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
            WikiArticle.expires_at > datetime.now(timezone.utc)
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
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.ttl_days)
        
        if existing:
            # Update
            existing.category = category
            existing.content = content
            existing.image_url = image_url
            existing.source_url = source_url
            existing.scraped_at = datetime.now(timezone.utc)
            existing.expires_at = expires_at
            existing.last_accessed = datetime.now(timezone.utc)
            
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
        batch_size: int = 500
    ) -> Dict[str, int]:
        """
        Bulk insert/update articles with PostgreSQL native upsert.
        
        ✅ FIXED: Deduplicates articles before inserting.
        
        Much faster than individual upserts!
        Uses PostgreSQL's ON CONFLICT for atomic upsert.
        
        Args:
            articles: List of article dicts
            batch_size: Batch size for commits
            
        Returns:
            Dict with stats: {'created': X, 'updated': Y, 'failed': Z}
        """
        if not articles:
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        # ✅ DEDUPLICATE: Remove duplicates by (title, universe)
        seen = {}
        unique_articles = []
        for article in articles:
            key = (article['title'], article['universe'])
            if key not in seen:
                seen[key] = True
                unique_articles.append(article)
        
        if len(unique_articles) < len(articles):
            logger.warning(
                f"⚠️  Removed {len(articles) - len(unique_articles)} duplicate articles"
            )
        
        articles = unique_articles
        
        stats = {'created': 0, 'updated': 0, 'failed': 0}
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.ttl_days)
        
        # Process in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            try:
                # Prepare batch data
                batch_data = []
                for article_data in batch:
                    batch_data.append({
                        'title': article_data['title'],
                        'universe': article_data['universe'],
                        'category': article_data['category'],
                        'content': article_data.get('content', {}),
                        'image_url': article_data.get('image_url'),
                        'image_cached': article_data.get('image_cached', False),
                        'image_cache_path': article_data.get('image_cache_path'),
                        'source_url': article_data.get('source_url'),
                        'expires_at': expires_at,
                        'access_count': 0
                    })
                
                # PostgreSQL native upsert
                stmt = insert(WikiArticle).values(batch_data)
                
                # On conflict, update all fields except id and scraped_at
                stmt = stmt.on_conflict_do_update(
                    index_elements=['title', 'universe'],
                    set_={
                        'category': stmt.excluded.category,
                        'content': stmt.excluded.content,
                        'image_url': stmt.excluded.image_url,
                        'image_cached': stmt.excluded.image_cached,
                        'image_cache_path': stmt.excluded.image_cache_path,
                        'source_url': stmt.excluded.source_url,
                        'expires_at': stmt.excluded.expires_at,
                        'last_accessed': datetime.now(timezone.utc)
                    }
                )
                
                # Execute
                result = self.db.execute(stmt)
                self.db.commit()
                
                # Count created vs updated (approximate)
                # PostgreSQL doesn't return which were created/updated easily,
                # so we estimate based on existing records
                for article_data in batch:
                    existing = self.db.query(WikiArticle).filter(
                        WikiArticle.title == article_data['title'],
                        WikiArticle.universe == article_data['universe']
                    ).first()
                    
                    if existing and existing.scraped_at < (datetime.now(timezone.utc) - timedelta(seconds=5)):
                        stats['updated'] += 1
                    else:
                        stats['created'] += 1
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Batch commit error: {e}")
                
                # Try individual inserts for this batch
                for article_data in batch:
                    try:
                        existing = self.get_article_by_title(
                            article_data['title'],
                            article_data['universe']
                        )
                        
                        if existing:
                            existing.category = article_data['category']
                            existing.content = article_data.get('content', {})
                            existing.image_url = article_data.get('image_url')
                            existing.source_url = article_data.get('source_url')
                            existing.scraped_at = datetime.now(timezone.utc)
                            existing.expires_at = expires_at
                            stats['updated'] += 1
                        else:
                            article = WikiArticle(
                                title=article_data['title'],
                                universe=article_data['universe'],
                                category=article_data['category'],
                                content=article_data.get('content', {}),
                                image_url=article_data.get('image_url'),
                                source_url=article_data.get('source_url'),
                                expires_at=expires_at
                            )
                            self.db.add(article)
                            stats['created'] += 1
                        
                        self.db.commit()
                        
                    except Exception as e2:
                        self.db.rollback()
                        logger.error(f"Failed to insert article {article_data.get('title')}: {e2}")
                        stats['failed'] += 1
        
        logger.info(f"Bulk upsert complete: {stats}")
        return stats
    
    def mark_image_cached(
        self,
        title: str,
        universe: str,
        cache_path: str
    ) -> bool:
        """
        Mark article's image as cached.
        
        Args:
            title: Article title
            universe: Universe name
            cache_path: Local cache path
            
        Returns:
            True if updated
        """
        article = self.get_article_by_title(title, universe)
        
        if not article:
            return False
        
        article.image_cached = True
        article.image_cache_path = cache_path
        article.last_accessed = datetime.now(timezone.utc)
        
        self.db.commit()
        return True
    
    # ============================================
    # CATEGORY OPERATIONS
    # ============================================
    
    def get_category_counts(self, universe: str) -> Dict[str, int]:
        """
        Get article counts per category.
        
        Args:
            universe: Universe name
            
        Returns:
            Dict: category -> count
        """
        results = self.db.query(
            WikiArticle.category,
            func.count(WikiArticle.id)
        ).filter(
            WikiArticle.universe == universe,
            WikiArticle.expires_at > datetime.now(timezone.utc)
        ).group_by(
            WikiArticle.category
        ).all()
        
        return {category: count for category, count in results}
    
    def update_category_cache(self, universe: str):
        """
        Update category cache with current stats.
        
        Args:
            universe: Universe name
        """
        counts = self.get_category_counts(universe)
        
        for category, count in counts.items():
            # Count articles with images
            with_images = self.db.query(func.count(WikiArticle.id)).filter(
                WikiArticle.universe == universe,
                WikiArticle.category == category,
                WikiArticle.image_cached == True,
                WikiArticle.expires_at > datetime.now(timezone.utc)
            ).scalar()
            
            # Upsert cache
            cache = self.db.query(CategoryCache).filter(
                CategoryCache.universe == universe,
                CategoryCache.category == category
            ).first()
            
            if cache:
                cache.article_count = count
                cache.articles_with_images = with_images
                cache.last_updated = datetime.now(timezone.utc)
            else:
                cache = CategoryCache(
                    universe=universe,
                    category=category,
                    article_count=count,
                    articles_with_images=with_images
                )
                self.db.add(cache)
            
            self.db.commit()
        
        logger.info(f"Category cache updated for {universe}")
    
    def get_category_cache(self, universe: str) -> Dict:
        """
        Get cached category stats.
        
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
            existing.last_accessed = datetime.now(timezone.utc)
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
            operation_type: Operation type (e.g., 'startup_prefetch_all')
            
        Returns:
            ScrapingLog object
        """
        log = ScrapingLog(
            universe=universe,
            operation_type=operation_type,
            status='running',
            started_at=datetime.now(timezone.utc)
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
        status: str = 'completed'
    ):
        """
        Complete scraping operation log.
        
        ✅ FIXED: Handles timezone-aware datetimes properly.
        
        Args:
            log_id: Log ID
            stats: Statistics dict
            status: Status ('completed', 'failed', 'cancelled')
        """
        log = self.db.query(ScrapingLog).filter(
            ScrapingLog.id == log_id
        ).first()
        
        if not log:
            logger.warning(f"Scraping log #{log_id} not found")
            return
        
        # ✅ Always use timezone-aware datetime
        log.status = status
        log.completed_at = datetime.now(timezone.utc)
        
        # Calculate duration safely
        if log.completed_at and log.started_at:
            completed = log.completed_at
            started = log.started_at
            
            # Ensure both are timezone-aware
            if completed.tzinfo is None:
                completed = completed.replace(tzinfo=timezone.utc)
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            
            log.duration_seconds = int((completed - started).total_seconds())
        else:
            log.duration_seconds = 0
        
        # Update statistics
        log.articles_fetched = stats.get('articles_total', 0)
        log.articles_cached = (
            stats.get('articles_created', 0) + 
            stats.get('articles_updated', 0)
        )
        log.images_downloaded = stats.get('images_downloaded', 0)
        log.images_cached = stats.get('images_cached', 0)
        log.errors = stats.get('errors', [])
        
        try:
            self.db.commit()
            logger.info(f"✅ Scraping log #{log_id} completed: {status}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete scraping log: {e}")
    
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
            WikiArticle.expires_at < datetime.now(timezone.utc)
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
            WikiArticle.expires_at > datetime.now(timezone.utc)
        ).scalar()
        
        articles_with_images = self.db.query(func.count(WikiArticle.id)).filter(
            WikiArticle.universe == universe,
            WikiArticle.image_cached == True,
            WikiArticle.expires_at > datetime.now(timezone.utc)
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