# backend/app/services/unified_cache_service.py
"""
Unified Cache Service - Single API for all cache operations.

Now with HYBRID backend:
- Primary: PostgreSQL + Filesystem (HybridCacheService)
- Fallback: File-based cache (backward compatibility)

Migration strategy:
1. Try PostgreSQL first
2. Fallback to file cache if empty
3. Dual-write mode (during transition)
"""

from typing import Dict, List, Optional
from functools import lru_cache
import logging

from app.core.scraper.wiki_scraper import WikiScraper
from app.models.database import SessionLocal

logger = logging.getLogger(__name__)


class UnifiedCacheService:
    """
    Unified API for wiki cache operations.
    
    Architecture:
    - Primary: HybridCacheService (PostgreSQL + Filesystem)
    - Fallback: WikiScraper (file-based cache)
    - Transition: Dual-write mode
    
    Features:
    - Single API for all cache operations
    - Automatic fallback
    - Backward compatibility
    - Gradual migration support
    
    Example:
        service = UnifiedCacheService()
        
        # Get planets (tries PostgreSQL first, then file cache)
        planets = service.get_planets('star_wars')
    """
    
    def __init__(self, use_hybrid: bool = True):
        """
        Initialize unified cache service.
        
        Args:
            use_hybrid: Use hybrid (PostgreSQL + filesystem) backend
        """
        self.scraper = WikiScraper()
        self.use_hybrid = use_hybrid
        
        # Initialize hybrid service (lazy)
        self._hybrid = None
    
    @property
    def hybrid(self):
        """Lazy-load HybridCacheService."""
        if self._hybrid is None and self.use_hybrid:
            try:
                from app.services.hybrid_cache_service import HybridCacheService
                db = SessionLocal()
                self._hybrid = HybridCacheService(db)
                logger.info("✅ Hybrid cache service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize hybrid service: {e}")
                self.use_hybrid = False
        
        return self._hybrid
    
    # ============================================
    # HIGH-LEVEL CACHE ACCESS
    # ============================================
    
    def get_all_data(
        self,
        universe: str = 'star_wars',
        force_refresh: bool = False
    ) -> Dict[str, List[str]]:
        """
        Get all categorized data.
        
        Primary: PostgreSQL
        Fallback: File cache
        
        Args:
            universe: Universe name
            force_refresh: Force refresh from wiki
            
        Returns:
            Dict with all categories
        """
        # Try PostgreSQL first
        if self.use_hybrid and self.hybrid:
            try:
                return self._get_all_data_from_hybrid(universe)
            except Exception as e:
                logger.warning(f"Hybrid cache failed: {e}, falling back to file cache")
        
        # Fallback to file cache
        return self.scraper.get_canon_categorized_data(
            universe=universe,
            force_refresh=force_refresh
        )
    
    def _get_all_data_from_hybrid(self, universe: str) -> Dict[str, List[str]]:
        """
        Get all data from PostgreSQL.
        
        Args:
            universe: Universe name
            
        Returns:
            Dict with all categories
        """
        from sqlalchemy import func
        from app.models.wiki_article import WikiArticle
        from datetime import datetime
        
        db = self.hybrid.db
        
        # Get all categories
        results = db.query(
            WikiArticle.category,
            WikiArticle.title
        ).filter(
            WikiArticle.universe == universe,
            WikiArticle.expires_at > datetime.now()
        ).all()
        
        # Group by category
        data = {}
        for category, title in results:
            if category not in data:
                data[category] = []
            data[category].append(title)
        
        # If empty, fallback to file cache
        if not data:
            logger.warning(f"PostgreSQL empty for {universe}, using file cache")
            return self.scraper.get_canon_categorized_data(universe)
        
        return data
    
    def get_summary(self, universe: str = 'star_wars') -> Dict[str, int]:
        """
        Get summary counts.
        
        Primary: CategoryCache (instant!)
        Fallback: Count from data
        
        Args:
            universe: Universe name
            
        Returns:
            Dict with category counts
        """
        # Try PostgreSQL cache
        if self.use_hybrid and self.hybrid:
            try:
                cache = self.hybrid.pg_cache.get_category_cache(universe)
                if cache:
                    return {cat: stats['count'] for cat, stats in cache.items()}
            except Exception as e:
                logger.warning(f"Category cache failed: {e}")
        
        # Fallback: count from all data
        data = self.get_all_data(universe)
        return {cat: len(items) for cat, items in data.items()}
    
    # ============================================
    # CATEGORY METHODS (with images support!)
    # ============================================
    
    def get_planets(
        self,
        universe: str = 'star_wars',
        limit: int = 2000,
        with_images: bool = False
    ) -> List:
        """
        Get planets.
        
        Args:
            universe: Universe name
            limit: Max results
            with_images: Return with image metadata
            
        Returns:
            List of planets (str or dict)
        """
        if with_images and self.use_hybrid and self.hybrid:
            # Get from PostgreSQL with metadata
            try:
                return self.hybrid.get_planets_with_metadata(
                    universe=universe,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"Hybrid get_planets failed: {e}")
        
        # Fallback: simple list
        data = self.get_all_data(universe)
        planets = data.get('planets', [])
        
        if with_images:
            # Format as dicts (without images)
            return [{'name': p, 'image_url': None} for p in planets[:limit]]
        
        return planets[:limit]
    
    def get_species(self, universe: str = 'star_wars', limit: int = 2000) -> List[str]:
        """Get species."""
        data = self.get_all_data(universe)
        return data.get('species', [])[:limit]
    
    def get_characters(self, universe: str = 'star_wars', limit: int = 15000) -> List[str]:
        """Get characters."""
        data = self.get_all_data(universe)
        return data.get('characters', [])[:limit]
    
    def get_weapons(
        self,
        universe: str = 'star_wars',
        limit: int = 1200,
        with_images: bool = False
    ) -> List:
        """Get weapons."""
        if with_images and self.use_hybrid and self.hybrid:
            try:
                result = self.hybrid.get_category_with_metadata(
                    universe=universe,
                    category='weapons',
                    limit=limit
                )
                return result['items']
            except Exception as e:
                logger.error(f"Hybrid get_weapons failed: {e}")
        
        data = self.get_all_data(universe)
        weapons = data.get('weapons', [])[:limit]
        
        if with_images:
            return [{'name': w, 'image_url': None} for w in weapons]
        
        return weapons
    
    def get_armor(
        self,
        universe: str = 'star_wars',
        limit: int = 300,
        with_images: bool = False
    ) -> List:
        """Get armor."""
        if with_images and self.use_hybrid and self.hybrid:
            try:
                result = self.hybrid.get_category_with_metadata(
                    universe=universe,
                    category='armor',
                    limit=limit
                )
                return result['items']
            except Exception as e:
                logger.error(f"Hybrid get_armor failed: {e}")
        
        data = self.get_all_data(universe)
        armor = data.get('armor', [])[:limit]
        
        if with_images:
            return [{'name': a, 'image_url': None} for a in armor]
        
        return armor
    
    def get_vehicles(
        self,
        universe: str = 'star_wars',
        limit: int = 2000,
        with_images: bool = False
    ) -> List:
        """Get vehicles."""
        if with_images and self.use_hybrid and self.hybrid:
            try:
                result = self.hybrid.get_category_with_metadata(
                    universe=universe,
                    category='vehicles',
                    limit=limit
                )
                return result['items']
            except Exception as e:
                logger.error(f"Hybrid get_vehicles failed: {e}")
        
        data = self.get_all_data(universe)
        vehicles = data.get('vehicles', [])[:limit]
        
        if with_images:
            return [{'name': v, 'image_url': None} for v in vehicles]
        
        return vehicles
    
    def get_droids(
        self,
        universe: str = 'star_wars',
        limit: int = 400,
        with_images: bool = False
    ) -> List:
        """Get droids."""
        if with_images and self.use_hybrid and self.hybrid:
            try:
                result = self.hybrid.get_category_with_metadata(
                    universe=universe,
                    category='droids',
                    limit=limit
                )
                return result['items']
            except Exception as e:
                logger.error(f"Hybrid get_droids failed: {e}")
        
        data = self.get_all_data(universe)
        droids = data.get('droids', [])[:limit]
        
        if with_images:
            return [{'name': d, 'image_url': None} for d in droids]
        
        return droids
    
    def get_items(
        self,
        universe: str = 'star_wars',
        limit: int = 4000,
        with_images: bool = False
    ) -> List:
        """Get items."""
        if with_images and self.use_hybrid and self.hybrid:
            try:
                result = self.hybrid.get_category_with_metadata(
                    universe=universe,
                    category='items',
                    limit=limit
                )
                return result['items']
            except Exception as e:
                logger.error(f"Hybrid get_items failed: {e}")
        
        data = self.get_all_data(universe)
        items = data.get('items', [])[:limit]
        
        if with_images:
            return [{'name': i, 'image_url': None} for i in items]
        
        return items
    
    def get_organizations(self, universe: str = 'star_wars', limit: int = 1500) -> List[str]:
        """Get organizations."""
        data = self.get_all_data(universe)
        return data.get('organizations', [])[:limit]
    
    def get_locations(self, universe: str = 'star_wars', limit: int = 5000) -> List[str]:
        """Get locations."""
        data = self.get_all_data(universe)
        return data.get('locations', [])[:limit]
    
    def get_battles(self, universe: str = 'star_wars', limit: int = 800) -> List[str]:
        """Get battles."""
        data = self.get_all_data(universe)
        return data.get('battles', [])[:limit]
    
    def get_creatures(self, universe: str = 'star_wars', limit: int = 1500) -> List[str]:
        """Get creatures."""
        data = self.get_all_data(universe)
        return data.get('creatures', [])[:limit]
    
    def get_technology(self, universe: str = 'star_wars', limit: int = 800) -> List[str]:
        """Get technology."""
        data = self.get_all_data(universe)
        return data.get('technology', [])[:limit]
    
    # ============================================
    # SEARCH
    # ============================================
    
    def search(
        self,
        universe: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search articles.
        
        Primary: PostgreSQL (fast ILIKE!)
        Fallback: In-memory filter
        
        Args:
            universe: Universe name
            query: Search query
            category: Optional category filter
            limit: Max results
            
        Returns:
            List of matching articles
        """
        # Try PostgreSQL search
        if self.use_hybrid and self.hybrid:
            try:
                articles = self.hybrid.pg_cache.search_articles(
                    universe=universe,
                    query=query,
                    category=category,
                    limit=limit
                )
                
                return [
                    {
                        'name': article.title,
                        'category': article.category,
                        'description': article.content.get('description') if article.content else None
                    }
                    for article in articles
                ]
            except Exception as e:
                logger.warning(f"PostgreSQL search failed: {e}")
        
        # Fallback: in-memory search
        data = self.get_all_data(universe)
        query_lower = query.lower()
        
        results = []
        
        categories_to_search = [category] if category else data.keys()
        
        for cat in categories_to_search:
            items = data.get(cat, [])
            
            for item in items:
                if query_lower in item.lower():
                    results.append({
                        'name': item,
                        'category': cat,
                        'description': None
                    })
                    
                    if len(results) >= limit:
                        return results
        
        return results
    
    # ============================================
    # CACHE MANAGEMENT
    # ============================================
    
    def force_refresh_all(self, universe: str = 'star_wars'):
        """
        Force refresh all data.
        
        Clears both PostgreSQL and file cache.
        
        Args:
            universe: Universe name
        """
        logger.info(f"🔄 Force refresh: {universe}")
        
        # Clear PostgreSQL
        if self.use_hybrid and self.hybrid:
            try:
                self.hybrid.force_refresh(universe)
            except Exception as e:
                logger.error(f"Hybrid force_refresh failed: {e}")
        
        # Clear file cache
        self.scraper.canon_cache.invalidate(universe, depth=3)
        
        logger.info("✅ All caches cleared")
    
    def get_cache_info(self, universe: str = 'star_wars') -> Dict:
        """
        Get cache information.
        
        Args:
            universe: Universe name
            
        Returns:
            Dict with cache info
        """
        info = {
            'universe': universe,
            'backend': 'hybrid' if self.use_hybrid else 'file',
            'file_cache': {
                'exists': self.scraper.canon_cache.exists(universe, depth=3)
            }
        }
        
        # Add PostgreSQL info
        if self.use_hybrid and self.hybrid:
            try:
                pg_stats = self.hybrid.get_comprehensive_stats(universe)
                info['postgresql'] = pg_stats
            except Exception as e:
                logger.error(f"Failed to get PostgreSQL stats: {e}")
        
        return info


# ============================================
# SINGLETON INSTANCE
# ============================================

@lru_cache(maxsize=1)
def get_unified_cache_service() -> UnifiedCacheService:
    """Get singleton instance of UnifiedCacheService."""
    return UnifiedCacheService(use_hybrid=True)