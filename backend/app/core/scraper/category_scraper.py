# backend/app/core/scraper/category_scraper.py
from typing import List, Optional
from bs4 import BeautifulSoup
from .http_client import WikiHttpClient
from .parsers.base_parser import BaseParser
from .cache_manager import CacheManager
from .config import ScraperConfig

class CategoryScraper:
    """Single responsibility: scraping kategorii Wiki"""
    
    def __init__(
        self, 
        http_client: WikiHttpClient,
        parser: BaseParser,
        cache_manager: CacheManager,
        config: ScraperConfig
    ):
        self.http_client = http_client
        self.parser = parser
        self.cache = cache_manager
        self.config = config
    
    def scrape_category(
        self, 
        category: str, 
        base_url: str,
        universe: str,
        max_items: Optional[int] = None
    ) -> List[str]:
        """Scrapuje kategorię z cache'owaniem"""
        cache_key = f"{universe}_{category}"
        
        # Sprawdź cache
        cached = self.cache.get(cache_key)
        if cached:
            print(f"✓ Loaded {len(cached)} items for {category} from cache")
            return cached
        
        # Scrapuj
        print(f"⟳ Scraping {category} from {universe}...")
        items = self._scrape_all_pages(category, base_url, max_items)
        
        # Zapisz do cache
        if items:
            self.cache.set(cache_key, items)
            print(f"✓ Scraped and cached {len(items)} items for {category}")
        
        return items
    
    def _scrape_all_pages(
        self, 
        category: str, 
        base_url: str,
        max_items: Optional[int]
    ) -> List[str]:
        """Scrapuje wszystkie strony kategorii z paginacją"""
        max_items = max_items or self.config.max_category_items
        all_items = []
        url = f"{base_url}/wiki/Category:{category}"
        pages_scraped = 0
        
        while url and len(all_items) < max_items and pages_scraped < self.config.max_pages_per_category:
            response = self.http_client.get(url)
            if not response:
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            items = self.parser.parse_category_items(soup)
            
            if not items:
                break
            
            all_items.extend(items)
            pages_scraped += 1
            print(f"  Page {pages_scraped}: +{len(items)} items (total: {len(all_items)})")
            
            # Następna strona
            url = self.parser.find_next_page_url(soup, base_url)
            if not url:
                break
        
        # Deduplikacja i sortowanie
        unique_items = sorted(list(set(all_items)))
        return unique_items[:max_items]