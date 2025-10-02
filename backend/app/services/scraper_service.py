# backend/app/services/scraper_service.py
from typing import Dict, Optional, List
from app.core.scraper.wiki_scraper import WikiScraper
from app.core.exceptions import NotFoundError

class ScraperService:
    """Service dla operacji scrapowania wiki - zaktualizowany dla refactored scrapera"""
    
    def __init__(self):
        self.scraper = WikiScraper()
        self.cache = {}
    
    def get_category_list(
        self, 
        universe: str, 
        category: str, 
        limit: int = 200
    ) -> List[str]:
        """
        Pobiera pełną listę elementów z kategorii
        Mapuje na nowe API scrapera
        """
        category_map = {
            'species': self.scraper.get_all_species,
            'planets': self.scraper.get_all_planets,
            'organizations': self.scraper.get_all_organizations,
            'colors': self.scraper.get_colors,
            'genders': lambda u: ['Male', 'Female', 'Other', 'None']
        }
        
        method = category_map.get(category)
        if not method:
            return []
        
        try:
            items = method(universe)
            return items[:limit]
        except Exception as e:
            print(f"Error fetching {category}: {e}")
            return []
    
    def search_category(
        self, 
        universe: str, 
        category: str, 
        query: str
    ) -> List[str]:
        """
        Wyszukuje w kategorii elementy pasujące do zapytania
        """
        all_items = self.get_category_list(universe, category)
        query_lower = query.lower()
        
        matches = [
            item for item in all_items 
            if query_lower in item.lower()
        ]
        
        return matches[:20]
    
    def get_planet_info(
        self, 
        planet_name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """Pobiera szczegółowe informacje o planecie"""
        url = self.scraper.search_character(planet_name, universe)
        if not url:
            raise NotFoundError("Planet", planet_name)
        
        data = self.scraper.scrape_character_data(url)
        
        # Format jako planet data
        return {
            'name': planet_name,
            'description': data.get('description', ''),
            'system': data.get('info', {}).get('system', 'Unknown'),
            'sector': data.get('info', {}).get('sector', 'Unknown'),
            'region': data.get('info', {}).get('region', 'Unknown'),
            'climate': data.get('info', {}).get('climate', 'Unknown'),
            'url': url
        }
    
    def get_affiliation_info(
        self, 
        affiliation_name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """Pobiera informacje o organizacji/afilacji"""
        url = self.scraper.search_character(affiliation_name, universe)
        if not url:
            raise NotFoundError("Affiliation", affiliation_name)
        
        data = self.scraper.scrape_character_data(url)
        
        return {
            'name': affiliation_name,
            'description': data.get('description', ''),
            'url': url
        }
    
    def search_entity(
        self, 
        name: str, 
        universe: str = 'star_wars'
    ) -> Optional[str]:
        """Wyszukuje encję (postać, lokację, przedmiot) w wiki"""
        cache_key = f"{universe}:{name.lower()}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = self.scraper.search_character(name, universe)
        if url:
            self.cache[cache_key] = url
        
        return url
    
    def get_entity_data(
        self, 
        name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """Pobiera pełne dane o encji z wiki"""
        url = self.search_entity(name, universe)
        
        if not url:
            raise NotFoundError("Entity", name)
        
        data = self.scraper.scrape_character_data(url)
        return self._format_wiki_data(data)
    
    def get_canon_elements(self, universe: str) -> Dict[str, List]:
        """Pobiera podstawowe kanoniczne elementy dla uniwersum"""
        try:
            species = self.scraper.get_all_species(universe)[:20]
            planets = self.scraper.get_all_planets(universe)[:20]
            orgs = self.scraper.get_all_organizations(universe)[:20]
            
            return {
                'popular_species': species,
                'popular_planets': planets,
                'popular_affiliations': orgs,
                'genders': ['Male', 'Female', 'Other', 'None'],
                'colors': self.scraper.get_colors()
            }
        except Exception as e:
            print(f"Error getting canon elements: {e}")
            # Fallback
            return {
                'popular_species': ['Human'],
                'popular_planets': ['Tatooine'],
                'popular_affiliations': ['Jedi Order'],
                'genders': ['Male', 'Female', 'Other', 'None'],
                'colors': ['Blue', 'Green', 'Brown']
            }
    
    def clear_cache(self):
        """Czyści cache"""
        self.cache = {}
        self.scraper.clear_cache()
    
    def _format_wiki_data(self, data: Dict) -> Dict:
        """Formatuje i czyści dane z wiki"""
        return {
            'name': data.get('name', 'Unknown'),
            'description': data.get('description', ''),
            'biography': data.get('biography', '')[:2000],
            'abilities': data.get('abilities', [])[:10],
            'affiliations': data.get('affiliations', []),
            'image_url': data.get('image_url'),
            'info': data.get('info_box', {})
        }