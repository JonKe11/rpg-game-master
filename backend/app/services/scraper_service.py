# backend/app/services/scraper_service.py
from typing import Dict, Optional, List
from app.core.scraper.wiki_scraper import WikiScraper
from app.core.exceptions import NotFoundError

class ScraperService:
    """Service dla operacji scrapowania wiki"""
    
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
        
        Args:
            universe: np. 'star_wars'
            category: np. 'species', 'planets'
            limit: max liczba elementów
        
        Returns:
            Lista nazw elementów
        """
        return self.scraper.get_category_items(universe, category, limit)
    
    def search_category(
        self, 
        universe: str, 
        category: str, 
        query: str
    ) -> List[str]:
        """
        Wyszukuje w kategorii elementy pasujące do zapytania
        
        Args:
            universe: np. 'star_wars'
            category: np. 'species', 'planets'
            query: szukana fraza
        
        Returns:
            Lista pasujących elementów
        """
        return self.scraper.search_in_category(universe, category, query)
    
    def get_planet_info(
        self, 
        planet_name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """Pobiera szczegółowe informacje o planecie"""
        data = self.scraper.get_planet_data(planet_name, universe)
        if not data:
            raise NotFoundError("Planet", planet_name)
        return data
    
    def get_affiliation_info(
        self, 
        affiliation_name: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """Pobiera informacje o organizacji/afilacji"""
        data = self.scraper.get_affiliation_data(affiliation_name, universe)
        if not data:
            raise NotFoundError("Affiliation", affiliation_name)
        return data
    
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
        """
        Pobiera podstawowe kanoniczne elementy dla uniwersum
        (cached version z najpopularniejszymi)
        """
        canon = {
            'star_wars': {
                'popular_species': [
                    'Human', 'Twi\'lek', 'Wookiee', 'Rodian', 'Zabrak',
                    'Mon Calamari', 'Bothan', 'Duros', 'Sullustan', 'Trandoshan'
                ],
                'popular_planets': [
                    'Tatooine', 'Coruscant', 'Naboo', 'Alderaan', 'Hoth',
                    'Endor', 'Dagobah', 'Bespin', 'Kamino', 'Mustafar'
                ],
                'popular_affiliations': [
                    'Jedi Order', 'Sith', 'Galactic Republic', 'Galactic Empire',
                    'Rebel Alliance', 'New Republic', 'First Order', 'Resistance'
                ],
                'genders': ['Male', 'Female', 'Other', 'None'],
                'colors': ['Blue', 'Green', 'Brown', 'Red', 'Yellow', 'Orange', 
                          'Purple', 'Pink', 'White', 'Black', 'Gray', 'Hazel']
            },
            'lotr': {
                'popular_species': ['Human', 'Elf', 'Dwarf', 'Hobbit', 'Orc', 'Ent'],
                'popular_locations': [
                    'Shire', 'Rivendell', 'Gondor', 'Rohan', 'Mordor', 
                    'Moria', 'Isengard', 'Lothlórien'
                ],
                'popular_affiliations': [
                    'Fellowship of the Ring', 'Kingdom of Gondor', 'Rohan',
                    'Elves of Rivendell', 'Dwarves of Erebor'
                ]
            }
        }
        
        return canon.get(universe, {})
    
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