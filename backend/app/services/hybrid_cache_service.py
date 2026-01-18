# backend/app/services/hybrid_cache_service.py


from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime 
from app.services.postgres_cache_service import PostgresCacheService
from app.core.scraper.image_fetcher import ImageFetcher
from app.models.wiki_article import WikiArticle 

logger = logging.getLogger(__name__)

class HybridCacheService:
    """
    Hybrid cache combining PostgreSQL + Filesystem.
    
    Orchestrates between PostgreSQL (metadata) and Filesystem (images).
    """
    
    def __init__(self, db: Session):
        """
        Initialize hybrid service.
        """
        self.db = db
        self.pg_cache = PostgresCacheService(db)
        self.image_fetcher = ImageFetcher()
    
    # ============================================
    # GŁÓWNA ZMODYFIKOWANA FUNKCJA
    # ============================================
    
    def get_category_with_metadata(
        self,
        universe: str,
        category: str,
        limit: Optional[int] = 50,
        offset: int = 0,
        search: Optional[str] = None,
        with_images: bool = False
    ) -> Dict:
        """
        Pobiera dane kategorii bezpośrednio z PostgreSQL z paginacją i wyszukiwaniem.
        To jest teraz główna funkcja do pobierania danych dla frontendu.
        """
        
        
        search_result = self.pg_cache.search_articles_paginated(
            universe=universe,
            category=category,
            query=search,
            limit=limit,
            offset=offset,
            with_images_only=with_images
        )
        
        articles = search_result['items']
        total_count = search_result['total_count']
        
        
        items = [
            {
                'id': article.id,
                'name': article.title,
                'description': article.content.get('description') if article.content else None,
                'image_url': article.image_url,
                'image_cached': article.image_cached,
                'source_url': article.source_url 
            }
            for article in articles
        ]
        
        return {
            'universe': universe,
            'category': category,
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'returned': len(items),
            'items': items
        }
    
    # ============================================
    # POZOSTAŁE FUNKCJE (Uproszczone lub bez zmian)
    # ============================================
    
    def get_planets_with_metadata(
        self,
        universe: str,
        limit: Optional[int] = None,
        offset: int = 0,
        ensure_images: bool = False 
    ) -> List[Dict]:
        """
        Pobiera planety z metadanymi z PostgreSQL.
        Używa teraz nowej, paginowanej funkcji.
        """
        result = self.get_category_with_metadata(
            universe=universe,
            category='planets',
            limit=limit,
            offset=offset
        )
        return result['items']
    
    def search_all_categories(
        self,
        universe: str,
        query: str,
        limit: int = 10 
    ) -> Dict[str, List[Dict]]:
        """
        Przeszukuje wszystkie kategorie (używa nowej funkcji).
        """
        results = {}
        categories = [
            'planets', 'species', 'characters', 'weapons',
            'armor', 'vehicles', 'droids', 'organizations', 'locations'
        ]
        
        for category in categories:
            
            search_result = self.pg_cache.search_articles_paginated(
                universe=universe,
                category=category,
                query=query,
                limit=limit
            )
            
            articles = search_result['items']
            if articles:
                results[category] = [
                    {
                        'name': article.title,
                        'description': article.content.get('description') if article.content else None,
                        'image_url': article.image_url
                    }
                    for article in articles
                ]
        
        return results
    
    # ============================================
    # FUNKCJE POMOCNICZE (bez zmian)
    # Wywoływane przez startup_prefetch_service lub inne
    # ============================================
    
    def prefetch_images_for_category(
        self,
        universe: str,
        category: str,
        max_workers: int = 15
    ) -> Dict[str, int]:
        """Prefetch images for all articles in category."""
        logger.info(f"🖼️ Prefetching images for {category}...")
        
        articles = self.pg_cache.get_articles_by_category(
            universe=universe,
            category=category
        )
        
        to_fetch = [
            article for article in articles
            if article.image_url and not article.image_cached
        ]
        
        logger.info(f"   Found {len(to_fetch)} images to download")
        if not to_fetch:
            return {'downloaded': 0, 'cached': 0, 'failed': 0}
        
        tasks = [
            (article.title, article.image_url, idx + 1, len(to_fetch))
            for idx, article in enumerate(to_fetch)
        ]
        
        stats = self.image_fetcher.fetch_batch_parallel(
            tasks,
            max_workers=max_workers,
            show_progress=True
        )
        
        logger.info(f"💾 Updating database...")
        for article in to_fetch:
            if article.image_url:
                cache_path = self.image_fetcher.get_cache_path(article.image_url)
                if cache_path.exists():
                    
                    self.pg_cache.mark_image_cached(
                        article.title,
                        article.universe,
                        str(cache_path)
                    )
                    url_hash = cache_path.stem
                    try:
                        self.pg_cache.register_image(
                            url=article.image_url,
                            url_hash=url_hash,
                            local_path=str(cache_path),
                            size_bytes=cache_path.stat().st_size
                        )
                    except Exception:
                        pass 
        
        logger.info(f"✅ Image prefetch complete: {stats}")
        return stats
    
    def _ensure_image_cached(self, article: WikiArticle):
        """Ensure article's image is cached (downloads if needed)."""
        if not article.image_url or article.image_cached:
            return
        
        success, was_cached, content = self.image_fetcher.fetch_single(article.image_url)
        
        if success:
            cache_path = self.image_fetcher.get_cache_path(article.image_url)
            self.pg_cache.mark_image_cached(article.title, article.universe, str(cache_path))
            url_hash = cache_path.stem
            try:
                self.pg_cache.register_image(
                    url=article.image_url,
                    url_hash=url_hash,
                    local_path=str(cache_path),
                    size_bytes=cache_path.stat().st_size if cache_path.exists() else None
                )
            except Exception:
                pass
    
    def get_comprehensive_stats(self, universe: str) -> Dict:
        """Get comprehensive statistics."""
        pg_stats = self.pg_cache.get_cache_stats(universe)
        category_cache = self.pg_cache.get_category_cache(universe)
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
                    'articles_processed': log.articles_cached, # Użyj cached zamiast fetched
                    'started_at': log.started_at.isoformat()
                }
                for log in recent_logs
            ]
        }
    
    def update_all_statistics(self, universe: str):
        """Update all cached statistics."""
        logger.info(f"📊 Updating statistics for {universe}...")
        self.pg_cache.update_category_cache(universe)
        logger.info(f"✅ Statistics updated")
    
    def cleanup_expired(self, universe: Optional[str] = None) -> Dict:
        """Cleanup expired data from both DB and filesystem."""
        logger.info("🗑️ Running cleanup...")
        deleted_articles = self.pg_cache.cleanup_expired(universe)
        deleted_images = self.image_fetcher.clear_cache(older_than_days=30)
        logger.info(f"✅ Cleanup complete: {deleted_articles} articles, {deleted_images} images")
        return {
            'deleted_articles': deleted_articles,
            'deleted_images': deleted_images
        }
    
    def force_refresh(self, universe: str):
        """Force refresh all data for universe."""
        logger.info(f"🔄 Force refresh for {universe}...")
        from app.models.wiki_article import WikiArticle
        deleted = self.db.query(WikiArticle).filter(
            WikiArticle.universe == universe
        ).delete()
        self.db.commit()
        logger.info(f"🗑️ Deleted {deleted} articles")