# backend/app/core/scraper/wiki_scraper.py
from typing import List, Dict, Optional
from .config import ScraperConfig
from .rate_limiter import RateLimiter
from .http_client import WikiHttpClient
from .cache_manager import CacheManager
from .parsers.wookieepedia_parser import WookieepediaParser
from .category_scraper import CategoryScraper
from .character_scraper import CharacterScraper

class WikiScraper:
    """
    Facade Pattern - prosty interfejs do złożonego systemu scrapingu
    Koordynuje wszystkie komponenty
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        
        # Inicjalizacja komponentów (Dependency Injection)
        self.rate_limiter = RateLimiter(self.config.request_delay)
        self.http_client = WikiHttpClient(
            self.rate_limiter, 
            self.config.request_timeout
        )
        self.cache = CacheManager(
            'cache/wiki', 
            int(self.config.cache_validity.total_seconds() / 3600)
        )
        self.parser = WookieepediaParser()
        
        self.category_scraper = CategoryScraper(
            self.http_client,
            self.parser,
            self.cache,
            self.config
        )
        
        self.character_scraper = CharacterScraper(
            self.http_client,
            self.parser
        )
        
        self.base_urls = {
            'star_wars': 'https://starwars.fandom.com',
            'lotr': 'https://lotr.fandom.com',
        }
    
    def get_all_species(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz wszystkie gatunki/rasy"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        category = 'Sentient_species' if universe == 'star_wars' else 'Races'
        return self.category_scraper.scrape_category(
            category,
            base_url,
            universe,
            max_items=1000
        )
    
    def get_all_planets(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz wszystkie planety"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        return self.category_scraper.scrape_category(
            'Planets',
            base_url,
            universe,
            max_items=800
        )
    
    def get_all_organizations(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz wszystkie organizacje"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        return self.category_scraper.scrape_category(
            'Organizations',
            base_url,
            universe,
            max_items=500
        )
    
    def get_popular_affiliations(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz popularne afiliacje (kombinacja kategorii)"""
        affiliations = set()
        
        # Organizacje
        orgs = self.get_all_organizations(universe)
        affiliations.update(orgs)
        
        # Rządy
        base_url = self.base_urls.get(universe)
        if base_url:
            govs = self.category_scraper.scrape_category(
                'Governments',
                base_url,
                universe,
                max_items=200
            )
            affiliations.update(govs)
            
            # Military units
            military = self.category_scraper.scrape_category(
                'Military_units',
                base_url,
                universe,
                max_items=200
            )
            affiliations.update(military)
        
        return sorted(list(affiliations))
    
    def get_colors(self) -> List[str]:
        """Lista kolorów (hardcoded - brak kategorii na wiki)"""
        return [
            'Blue', 'Green', 'Brown', 'Black', 'White', 'Red', 
            'Yellow', 'Gray', 'Grey', 'Orange', 'Purple', 'Pink',
            'Fair', 'Pale', 'Light', 'Tan', 'Dark', 'Olive', 
            'Bronze', 'Golden', 'Silver',
            'Blue-gray', 'Gray-blue', 'Green-blue', 'Brown-green',
            'Light brown', 'Dark brown', 'Reddish-brown',
            'Amber', 'Hazel', 'Gold', 'Crimson', 'Violet'
        ]
    
    def search_character(self, character_name: str, universe: str = 'star_wars') -> Optional[str]:
        """Wyszukaj postać"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return None
        
        return self.character_scraper.search_character(character_name, base_url)
    
    def scrape_character_data(self, url: str) -> Dict:
        """Scrapuje dane postaci"""
        return self.character_scraper.scrape_character(url)
    
    def clear_cache(self, universe: Optional[str] = None):
        """Wyczyść cache"""
        pattern = f"{universe}_" if universe else None
        self.cache.clear(pattern)