# backend/app/services/hybrid_cache_service.py
"""
Hybrid Cache Service - Best of both worlds!

Architecture:
- PostgreSQL: Structured metadata (fast queries, relationships)
- Filesystem: Binary images (optimized for large files)

This service orchestrates between both layers.

Example:
    service = HybridCacheService(db)
    
    # Get planets with metadata from DB
    planets = service.get_planets_with_metadata('star_wars', limit=100)
    
    # Images are on filesystem, referenced in DB
    # Frontend uses /image-proxy?url=... to fetch them
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.services.postgres_cache_service import PostgresCacheService
from app.core.scraper.image_fetcher import ImageFetcher
from app.core.scraper.wiki_scraper import WikiScraper

logger = logging.getLogger(__name__)


class HybridCacheService:
    """
    Hybrid cache combining PostgreSQL + Filesystem.
    
    Responsibilities:
    - Orchestrate between PostgreSQL and filesystem
    - Provide high-level API for unified cache access
    - Handle sync between DB metadata and filesystem files
    
    Design:
    - PostgreSQL stores: article metadata, image URLs, cache status
    - Filesystem stores: actual image binary files
    - This service: coordinates both layers
    
    Example:
        service = HybridCacheService(db)
        
        # Metadata from DB (fast!)
        planets = service.get_planets_with_metadata('star_wars')
        
        # Images from filesystem (when requested via proxy)
    """
    
    def __init__(self, db: Session):
        """
        Initialize hybrid service.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.pg_cache = PostgresCacheService(db)
        self.image_fetcher = ImageFetcher()
        self.scraper = WikiScraper()
    
    # ============================================
    # HIGH-LEVEL DATA ACCESS
    # ============================================
    
    def get_planets_with_metadata(
        self,
        universe: str,
        limit: Optional[int] = None,
        offset: int = 0,
        ensure_images: bool = False
    ) -> List[Dict]:
        """
        Get planets with metadata from PostgreSQL.
        
        Fast query using indexes!
        
        Args:
            universe: Universe name
            limit: Max results
            offset: Pagination offset
            ensure_images: If True, prefetch missing images
            
        Returns:
            List of planet dicts with metadata
        """
        # Query PostgreSQL (< 5ms!)
        articles = self.pg_cache.get_articles_by_category(
            universe=universe,
            category='planets',
            limit=limit,
            offset=offset
        )
        
        planets = []
        
        for article in articles:
            planet_dict = {
                'id': article.id,
                'name': article.title,
                'description': article.content.get('description') if article.content else None,
                'image_url': article.image_url,
                'image_cached': article.image_cached,
                'image_cache_path': article.image_cache_path,
                'source_url': article.source_url,
                'access_count': article.access_count,
                'last_accessed': article.last_accessed.isoformat() if article.last_accessed else None
            }
            
            # Optional: Ensure image is cached
            if ensure_images and article.image_url and not article.image_cached:
                self._ensure_image_cached(article)
            
            planets.append(planet_dict)
        
        return planets
    
    def get_category_with_metadata(
        self,
        universe: str,
        category: str,
        limit: Optional[int] = None,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Dict:
        """
        Get category items with metadata and pagination.
        
        Args:
            universe: Universe name
            category: Category name
            limit: Max results
            offset: Pagination offset
            search: Optional search query
            
        Returns:
            Dict with items and metadata
        """
        # Search or list
        if search:
            articles = self.pg_cache.search_articles(
                universe=universe,
                query=search,
                category=category,
                limit=limit or 100
            )
            total = len(articles)
        else:
            articles = self.pg_cache.get_articles_by_category(
                universe=universe,
                category=category,
                limit=limit,
                offset=offset
            )
            
            # Get total count
            from sqlalchemy import func
            from app.models.wiki_article import WikiArticle
            total = self.db.query(func.count(WikiArticle.id)).filter(
                WikiArticle.universe == universe,
                WikiArticle.category == category,
                WikiArticle.expires_at > datetime.now()
            ).scalar()
        
        # Format results
        items = [
            {
                'id': article.id,
                'name': article.title,
                'description': article.content.get('description') if article.content else None,
                'image_url': article.image_url,
                'image_cached': article.image_cached
            }
            for article in articles
        ]
        
        return {
            'universe': universe,
            'category': category,
            'total': total,
            'offset': offset,
            'limit': limit,
            'returned': len(items),
            'items': items
        }
    
    def search_all_categories(
        self,
        universe: str,
        query: str,
        limit: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Search across all categories.
        
        Args:
            universe: Universe name
            query: Search query
            limit: Max results per category
            
        Returns:
            Dict with results per category
        """
        results = {}
        
        # Get all categories
        categories = [
            'planets', 'species', 'characters', 'weapons',
            'armor', 'vehicles', 'droids', 'organizations'
        ]
        
        for category in categories:
            articles = self.pg_cache.search_articles(
                universe=universe,
                query=query,
                category=category,
                limit=limit
            )
            
            if articles:
                results[category] = [
                    {
                        'name': article.title,
                        'description': article.content.get('description') if article.content else None
                    }
                    for article in articles
                ]
        
        return results
    
    # ============================================
    # PREFETCH & SYNC
    # ============================================
    
    def prefetch_category_to_db(
        self,
        universe: str,
        category: str,
        articles: List[str]
    ) -> Dict[str, int]:
        """
        Prefetch category articles to PostgreSQL.
        
        Scrapes article data and stores in DB.
        
        Args:
            universe: Universe name
            category: Category name
            articles: List of article titles
            
        Returns:
            Stats dict
        """
        logger.info(f"📦 Prefetching {len(articles)} {category} to PostgreSQL...")
        
        articles_data = []
        
        for idx, title in enumerate(articles):
            try:
                # Get article URL
                url = self.scraper.search_character(title, universe)
                
                if not url:
                    continue
                
                # Scrape data
                data = self.scraper.scrape_character_data(url)
                
                articles_data.append({
                    'title': title,
                    'universe': universe,
                    'category': category,
                    'content': {
                        'description': data.get('description'),
                        'biography': data.get('biography'),
                        'info_box': data.get('info_box')
                    },
                    'image_url': data.get('image_url'),
                    'source_url': url
                })
                
                # Progress
                if (idx + 1) % 50 == 0:
                    logger.info(f"   Scraped {idx + 1}/{len(articles)} articles...")
                
            except Exception as e:
                logger.error(f"Error scraping {title}: {e}")
        
        # Bulk insert to DB
        logger.info(f"💾 Inserting {len(articles_data)} articles to PostgreSQL...")
        stats = self.pg_cache.bulk_upsert_articles(articles_data)
        
        logger.info(f"✅ Prefetch complete: {stats}")
        return stats
    
    def prefetch_images_for_category(
        self,
        universe: str,
        category: str,
        max_workers: int = 15
    ) -> Dict[str, int]:
        """
        Prefetch images for all articles in category.
        
        Downloads images and updates DB status.
        
        Args:
            universe: Universe name
            category: Category name
            max_workers: Parallel workers
            
        Returns:
            Stats dict
        """
        logger.info(f"🖼️ Prefetching images for {category}...")
        
        # Get articles from DB
        articles = self.pg_cache.get_articles_by_category(
            universe=universe,
            category=category
        )
        
        # Filter: only articles with image_url and not yet cached
        to_fetch = [
            article for article in articles
            if article.image_url and not article.image_cached
        ]
        
        logger.info(f"   Found {len(to_fetch)} images to download")
        
        if not to_fetch:
            return {'downloaded': 0, 'cached': 0, 'failed': 0}
        
        # Prepare tasks
        tasks = [
            (article.title, article.image_url, idx + 1, len(to_fetch))
            for idx, article in enumerate(to_fetch)
        ]
        
        # Fetch in parallel
        stats = self.image_fetcher.fetch_batch_parallel(
            tasks,
            max_workers=max_workers,
            show_progress=True
        )
        
        # Update DB: mark images as cached
        logger.info(f"💾 Updating database...")
        for article in to_fetch:
            if article.image_url:
                cache_path = self.image_fetcher.get_cache_path(article.image_url)
                
                if cache_path.exists():
                    self.pg_cache.mark_image_cached(
                        article.id,
                        str(cache_path)
                    )
                    
                    # Register in image_cache table
                    url_hash = cache_path.stem  # Filename is hash
                    self.pg_cache.register_image(
                        url=article.image_url,
                        url_hash=url_hash,
                        local_path=str(cache_path),
                        size_bytes=cache_path.stat().st_size
                    )
        
        logger.info(f"✅ Image prefetch complete: {stats}")
        return stats
    
    def _ensure_image_cached(self, article):
        """
        Ensure article's image is cached (downloads if needed).
        
        Args:
            article: WikiArticle object
        """
        if not article.image_url or article.image_cached:
            return
        
        # Fetch image
        success, was_cached, content = self.image_fetcher.fetch_single(article.image_url)
        
        if success:
            cache_path = self.image_fetcher.get_cache_path(article.image_url)
            
            # Update DB
            self.pg_cache.mark_image_cached(article.id, str(cache_path))
            
            # Register in image_cache table
            url_hash = cache_path.stem
            self.pg_cache.register_image(
                url=article.image_url,
                url_hash=url_hash,
                local_path=str(cache_path),
                size_bytes=cache_path.stat().st_size if cache_path.exists() else None
            )
    
    # ============================================
    # STATISTICS & ANALYTICS
    # ============================================
    
    def get_comprehensive_stats(self, universe: str) -> Dict:
        """
        Get comprehensive statistics.
        
        Combines:
        - PostgreSQL stats (article counts)
        - Filesystem stats (image sizes)
        - Cache hit rates
        
        Args:
            universe: Universe name
            
        Returns:
            Complete stats dict
        """
        # PostgreSQL stats
        pg_stats = self.pg_cache.get_cache_stats(universe)
        
        # Category cache (instant!)
        category_cache = self.pg_cache.get_category_cache(universe)
        
        # Recent logs
        recent_logs = self.pg_cache.get_recent_logs(universe, limit=5)
        
        return {
            'universe': universe,
            'timestamp': datetime.now().isoformat(),
            'postgresql': pg_stats,
            'category_cache': category_cache,
            'recent_operations': [
                {
                    'operation': log.operation_type,
                    'status': log.status,
                    'duration': log.duration_seconds,
                    'articles_processed': log.articles_processed,
                    'started_at': log.started_at.isoformat()
                }
                for log in recent_logs
            ]
        }
    
    def update_all_statistics(self, universe: str):
        """
        Update all cached statistics.
        
        Args:
            universe: Universe name
        """
        logger.info(f"📊 Updating statistics for {universe}...")
        
        # Update category cache
        self.pg_cache.update_category_cache(universe)
        
        logger.info(f"✅ Statistics updated")
    
    # ============================================
    # MAINTENANCE
    # ============================================
    
    def cleanup_expired(self, universe: Optional[str] = None) -> Dict:
        """
        Cleanup expired data from both DB and filesystem.
        
        Args:
            universe: Optional universe filter
            
        Returns:
            Cleanup stats
        """
        logger.info("🗑️ Running cleanup...")
        
        # Cleanup expired articles from DB
        deleted_articles = self.pg_cache.cleanup_expired(universe)
        
        # Cleanup old images from filesystem (30+ days)
        deleted_images = self.image_fetcher.clear_cache(older_than_days=30)
        
        logger.info(f"✅ Cleanup complete: {deleted_articles} articles, {deleted_images} images")
        
        return {
            'deleted_articles': deleted_articles,
            'deleted_images': deleted_images
        }
    
    def force_refresh(self, universe: str):
        """
        Force refresh all data for universe.
        
        Args:
            universe: Universe name
        """
        logger.info(f"🔄 Force refresh for {universe}...")
        
        # Delete all articles for universe
        from app.models.wiki_article import WikiArticle
        
        deleted = self.db.query(WikiArticle).filter(
            WikiArticle.universe == universe
        ).delete()
        
        self.db.commit()
        
        logger.info(f"🗑️ Deleted {deleted} articles")
        logger.info("⚠️ Run startup_prefetch_all() to repopulate!")