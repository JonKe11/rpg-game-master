# backend/app/services/scraper_service.py
from typing import Dict, Optional, List
import logging
import asyncio


from app.core.wiki.wiki_factory import create_wiki_client
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

class ScraperService:
    """
    Serwis do pobierania danych z Wiki (Online).
    Integruje się bezpośrednio z istniejącymi klientami (create_wiki_client).
    Wersja w pełni asynchroniczna (naprawa błędu Event Loop).
    """
    
    def __init__(self):
        pass
    
    async def _fetch_from_client(self, title: str, universe: str) -> Optional[Dict]:
        """Wewnętrzna logika pobierania z użyciem create_wiki_client."""
        try:
           
            client = create_wiki_client(universe)
        except ValueError:
            logger.warning(f"No wiki client found for universe: {universe}")
            return None
            
        if not client:
            return None
            
    
        search_results = await client.search(title)
        if not search_results:
            return None
            
        best_match = search_results[0]
       
        details = await client.get_details(best_match['title'])
        
        if details:
            return {
                'title': details.title,
                'description': details.content, 
                'image_url': details.image_url,
                'url': details.url
            }
        return None

    async def get_planet_info(self, planet_name: str, universe: str = 'star_wars') -> Dict:
        """Pobiera dane o planecie (Async)."""
        try:
            
            data = await self._fetch_from_client(planet_name, universe)
            if not data:
                return {'description': ''}
            return self._format_wiki_data(data)
        except Exception as e:
            logger.error(f"Failed to get planet info for {planet_name}: {e}")
            return {'description': ''}

    async def get_affiliation_info(self, affiliation_name: str, universe: str = 'star_wars') -> Dict:
        """Pobiera dane o organizacji (Async)."""
        try:
            
            data = await self._fetch_from_client(affiliation_name, universe)
            if not data:
                return {'description': ''}
            return self._format_wiki_data(data)
        except Exception as e:
            logger.error(f"Failed to get affiliation info: {e}")
            return {'description': ''}

    async def get_entity_data(self, name: str, universe: str = 'star_wars') -> Dict:
        """Pobiera ogólne dane o bycie (Async)."""
        try:
          
            data = await self._fetch_from_client(name, universe)
            if not data:
                return {'description': ''}
            return self._format_wiki_data(data)
        except Exception as e:
            logger.error(f"Failed to get entity data: {e}")
            return {'description': ''}

    def _format_wiki_data(self, data: Dict) -> Dict:
        return {
            'name': data.get('title', 'Unknown'),
            'description': data.get('description', ''), 
            'image_url': data.get('image_url'),
            'url': data.get('url', '')
        }


    def get_category_list(self, universe: str, category: str, limit: int = 200) -> List[str]:
        return []

    def search_category(self, universe: str, category: str, query: str) -> List[str]:
        return []