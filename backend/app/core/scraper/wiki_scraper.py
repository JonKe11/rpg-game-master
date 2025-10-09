# backend/app/core/scraper/wiki_scraper.py
from typing import Dict, List, Optional
from .http_client import WikiHttpClient
from .rate_limiter import RateLimiter
from .cache_manager import CacheManager
from .category_scraper import CategoryScraper
from .character_scraper import CharacterScraper
from .parsers.wookieepedia_parser import WookieepediaParser
from .config import ScraperConfig

class WikiScraper:
    """
    Główny interfejs do scrapowania wiki
    Wspiera Canon filtering dla Star Wars
    """
    
    def __init__(self):
        self.config = ScraperConfig()
        self.cache = CacheManager('cache', validity_hours=24)
        self.rate_limiter = RateLimiter(delay=self.config.request_delay)
        self.http_client = WikiHttpClient(self.rate_limiter, timeout=self.config.request_timeout)
        
        self.parser = WookieepediaParser()
        self.category_scraper = CategoryScraper(
            self.http_client,
            self.parser,
            self.cache,
            self.config
        )
        self.character_scraper = CharacterScraper(self.http_client, self.parser)
        
        self.base_urls = {
            'star_wars': 'https://starwars.fandom.com',
            'lotr': 'https://lotr.fandom.com',
            'harry_potter': 'https://harrypotter.fandom.com'
        }
    
    # ========================================================================
    # Canon Category Methods - BEZ LIMITÓW!
    # ========================================================================
    
    def get_all_planets(self, universe: str = 'star_wars') -> List[str]:
        """
        Pobiera WSZYSTKIE KANONICZNE planety (bez limitu)
        Filtruje przez Category:Canon_articles
        """
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        return self.category_scraper.scrape_canon_category(
            'Planets',
            base_url,
            universe,
            max_items=None  # ✅ ZMIENIONE: None = BEZ LIMITU!
        )
    
    def get_all_species(self, universe: str = 'star_wars') -> List[str]:
        """
        Pobiera WSZYSTKIE KANONICZNE rasy (bez limitu)
        Filtruje przez Category:Canon_articles
        """
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        return self.category_scraper.scrape_canon_category(
            'Sentient_species',
            base_url,
            universe,
            max_items=None  # ✅ ZMIENIONE: None = BEZ LIMITU!
        )
    
    def get_all_organizations(self, universe: str = 'star_wars') -> List[str]:
        """
        Pobiera WSZYSTKIE KANONICZNE organizacje (bez limitu)
        Filtruje przez Category:Canon_articles
        """
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        return self.category_scraper.scrape_canon_category(
            'Organizations',
            base_url,
            universe,
            max_items=None  # ✅ ZMIENIONE: None = BEZ LIMITU!
        )
    
    def get_colors(self) -> List[str]:
        """Podstawowe kolory (nie wymaga scrapowania)"""
        return [
            'Blue', 'Green', 'Brown', 'Gray', 'Black', 'White',
            'Red', 'Yellow', 'Orange', 'Purple', 'Pink', 'Blonde',
            'Auburn', 'Silver', 'Gold', 'Tan', 'Pale', 'Dark'
        ]
    
    # ========================================================================
    # Character Methods
    # ========================================================================
    
    def search_character(self, character_name: str, universe: str = 'star_wars') -> Optional[str]:
        """Wyszukaj postać i zwróć URL"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return None
        return self.character_scraper.search_character(character_name, base_url)
    
    def scrape_character_data(self, url: str) -> Dict:
        """Scrapuje pełne dane postaci z URL"""
        return self.character_scraper.scrape_character(url)
    
    def clear_cache(self):
        """Czyści cache"""
        self.cache.clear()
        self.category_scraper.clear_cache()