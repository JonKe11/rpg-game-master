# backend/app/services/scraper_service.py
"""
Scraper Service - Unified API for wiki data access.

✅ UPDATED: Uses UnifiedCacheService + WikiFetcherService
✅ Fast: Reads from PostgreSQL cache
✅ Reliable: FANDOM API backend
"""

from typing import Dict, Optional, List
from app.services.unified_cache_service import UnifiedCacheService
from app.services.wiki_fetcher_service import WikiFetcherService
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Service for wiki data access.
    
    ✅ NEW: Uses UnifiedCacheService for fast cached access
    ✅ NEW: Uses WikiFetcherService for detailed article data
    
    This service provides a simple API for getting wiki data:
    - Category lists (species, planets, etc.)
    - Entity details (characters, locations, etc.)
    - Search functionality
    """
    
    def __init__(self):
        self.cache_service = UnifiedCacheService(use_hybrid=True)
        self.wiki_fetcher = WikiFetcherService()
    
    def get_category_list(
        self, 
        universe: str, 
        category: str, 
        limit: int = 200
    ) -> List[str]:
        """
        Get full list of items from category.
        
        ✅ UPDATED: Uses UnifiedCacheService (PostgreSQL + file cache)
        
        Args:
            universe: Universe name (e.g., 'star_wars')
            category: Category name
            limit: Max results
            
        Returns:
            List of item names
        """
        try:
            # Map category to cache service method
            category_methods = {
                'species': self.cache_service.get_species,
                'planets': self.cache_service.get_planets,
                'characters': self.cache_service.get_characters,
                'weapons': self.cache_service.get_weapons,
                'armor': self.cache_service.get_armor,
                'vehicles': self.cache_service.get_vehicles,
                'droids': self.cache_service.get_droids,
                'items': self.cache_service.get_items,
                'organizations': self.cache_service.get_organizations,
                'locations': self.cache_service.get_locations,
                'battles': self.cache_service.get_battles,
                'creatures': self.cache_service.get_creatures,
                'technology': self.cache_service.get_technology
            }
            
            # Special cases
            if category == 'genders':
                return ['Male', 'Female', 'Other', 'None']
            
            if category == 'colors':
                return self._get_colors()
            
            # Get from cache
            method = category_methods.get(category)
            if not method:
                logger.warning(f"Unknown category: {category}")
                return []
            
            items = method(universe, limit=limit)
            
            # Convert to list of strings if needed
            if items and isinstance(items[0], dict):
                items = [item['name'] for item in items]
            
            return items[:limit]
        
        except Exception as e:
            logger.error(f"Error fetching {category}: {e}")
            return []
    
    def search_category(
        self, 
        universe: str, 
        category: str, 
        query: str
    ) -> List[str]:
        """
        Search within category for items matching query.
        
        ✅ UPDATED: Uses UnifiedCacheService.search()
        
        Args:
            universe: Universe name
            category: Category to search in
            query: Search query
            
        Returns:
            List of matching item names
        """
        try:
            # Use cache service search
            results = self.cache_service.search(
                universe=universe,
                query=query,
                category=category,
                limit=20
            )
            
            return [result['name'] for result in results]
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_planet_info(
        self, 
        planet_name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """
        Get detailed planet information.
        
        ✅ UPDATED: Uses WikiFetcherService with FANDOM API
        
        Args:
            planet_name: Planet name
            universe: Universe name
            
        Returns:
            Dict with planet data
        """
        try:
            # Fetch from wiki
            data = self.wiki_fetcher.fetch_article(planet_name, universe)
            
            if not data:
                raise NotFoundError("Planet", planet_name)
            
            return {
                'name': planet_name,
                'description': data.get('description', ''),
                'image_url': data.get('image_url'),
                'url': data.get('url', ''),
                'system': 'Unknown',  # Would need additional parsing
                'sector': 'Unknown',
                'region': 'Unknown',
                'climate': 'Unknown'
            }
        
        except Exception as e:
            logger.error(f"Failed to get planet info: {e}")
            raise NotFoundError("Planet", planet_name)
    
    def get_affiliation_info(
        self, 
        affiliation_name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """
        Get organization/affiliation information.
        
        ✅ UPDATED: Uses WikiFetcherService with FANDOM API
        
        Args:
            affiliation_name: Organization name
            universe: Universe name
            
        Returns:
            Dict with organization data
        """
        try:
            data = self.wiki_fetcher.fetch_article(affiliation_name, universe)
            
            if not data:
                raise NotFoundError("Affiliation", affiliation_name)
            
            return {
                'name': affiliation_name,
                'description': data.get('description', ''),
                'image_url': data.get('image_url'),
                'url': data.get('url', '')
            }
        
        except Exception as e:
            logger.error(f"Failed to get affiliation info: {e}")
            raise NotFoundError("Affiliation", affiliation_name)
    
    def search_entity(
        self, 
        name: str, 
        universe: str = 'star_wars'
    ) -> Optional[str]:
        """
        Search for entity (character, location, item) in wiki.
        
        ✅ UPDATED: Uses cache service search
        
        Args:
            name: Entity name
            universe: Universe name
            
        Returns:
            Entity URL or None
        """
        try:
            # Search in cache
            results = self.cache_service.search(
                universe=universe,
                query=name,
                limit=1
            )
            
            if results:
                # Fetch full data to get URL
                data = self.wiki_fetcher.fetch_article(results[0]['name'], universe)
                return data.get('url') if data else None
            
            return None
        
        except Exception as e:
            logger.error(f"Entity search failed: {e}")
            return None
    
    def get_entity_data(
        self, 
        name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """
        Get full entity data from wiki.
        
        ✅ UPDATED: Uses WikiFetcherService
        
        Args:
            name: Entity name
            universe: Universe name
            
        Returns:
            Dict with entity data
        """
        try:
            data = self.wiki_fetcher.fetch_article(name, universe)
            
            if not data:
                raise NotFoundError("Entity", name)
            
            return self._format_wiki_data(data)
        
        except Exception as e:
            logger.error(f"Failed to get entity data: {e}")
            raise NotFoundError("Entity", name)
    
    def get_canon_elements(self, universe: str) -> Dict[str, List]:
        """
        Get basic canonical elements for universe.
        
        ✅ UPDATED: Uses UnifiedCacheService
        
        Args:
            universe: Universe name
            
        Returns:
            Dict with popular elements from each category
        """
        try:
            return {
                'popular_species': self.cache_service.get_species(universe, limit=20),
                'popular_planets': self.cache_service.get_planets(universe, limit=20),
                'popular_affiliations': self.cache_service.get_organizations(universe, limit=20),
                'genders': ['Male', 'Female', 'Other', 'None'],
                'colors': self._get_colors()
            }
        
        except Exception as e:
            logger.error(f"Error getting canon elements: {e}")
            # Fallback
            return {
                'popular_species': ['Human'],
                'popular_planets': ['Tatooine'],
                'popular_affiliations': ['Jedi Order'],
                'genders': ['Male', 'Female', 'Other', 'None'],
                'colors': self._get_colors()
            }
    
    def clear_cache(self):
        """
        Clear cache.
        
        ✅ UPDATED: Clears UnifiedCacheService caches
        """
        try:
            # Force refresh will clear caches
            self.cache_service.force_refresh_all()
            logger.info("✅ Cache cleared")
        
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
    
    def _format_wiki_data(self, data: Dict) -> Dict:
        """
        Format and clean wiki data.
        
        Args:
            data: Raw wiki data
            
        Returns:
            Formatted data dict
        """
        return {
            'name': data.get('title', 'Unknown'),
            'description': data.get('description', ''),
            'biography': data.get('description', '')[:2000],  # Use description as biography
            'abilities': [],  # Would need additional parsing
            'affiliations': [],  # Would need additional parsing
            'image_url': data.get('image_url'),
            'info': {}  # Would need additional parsing
        }
    
    def _get_colors(self) -> List[str]:
        """Get standard color list"""
        return [
            'Blue', 'Green', 'Brown', 'Red', 'Black', 'White',
            'Yellow', 'Purple', 'Orange', 'Pink', 'Gray', 'Silver',
            'Gold', 'Cyan', 'Magenta', 'Violet', 'Turquoise'
        ]