# backend/app/core/scraper/category_scraper.py
"""
Category Scraper z MediaWiki API
Bardziej niezawodny niż HTML scraping
"""
from typing import List, Optional, Set
from .cache_manager import CacheManager
from .config import ScraperConfig
from .api_client import WikiAPIClient

class CategoryScraper:
    """
    Scraping kategorii Wiki przez MediaWiki API
    Automatyczne filtrowanie Canon vs Legends
    """
    
    def __init__(
        self, 
        http_client,  # Kept for backwards compatibility, not used with API
        parser,  # Kept for backwards compatibility, not used with API
        cache_manager: CacheManager,
        config: ScraperConfig
    ):
        self.cache = cache_manager
        self.config = config
        self._api_clients: dict = {}  # Cache API clients per base_url
    
    def _get_api_client(self, base_url: str) -> WikiAPIClient:
        """Get or create API client for base URL"""
        if base_url not in self._api_clients:
            self._api_clients[base_url] = WikiAPIClient(base_url)
        return self._api_clients[base_url]
    
    # ========================================================================
    # Canon filtering methods (using API)
    # ========================================================================
    
    def get_all_canon_articles(self, base_url: str, universe: str) -> Set[str]:
        """
        Pobiera WSZYSTKIE artykuły oznaczone jako Canon
        Używa MediaWiki API - bardziej niezawodne niż HTML
        """
        # Check cache first
        cache_key = f"{universe}_canon_articles"
        cached = self.cache.get(cache_key)
        if cached:
            print(f"✓ Loaded {len(cached)} Canon articles from cache")
            return set(cached)
        
        # Fetch via API
        print(f"📡 Fetching Canon articles via API...")
        api_client = self._get_api_client(base_url)
        canon_articles = api_client.get_canon_articles()
        
        if canon_articles:
            # Save to cache
            canon_list = list(canon_articles)
            self.cache.set(cache_key, canon_list)
            print(f"✅ Cached {len(canon_articles)} Canon articles")
        else:
            print(f"⚠️ No Canon articles found")
        
        return canon_articles
    
    def scrape_canon_category(
        self,
        category: str,
        base_url: str,
        universe: str,
        max_items: Optional[int] = None
    ) -> List[str]:
        """
        Scrapuje kategorię i FILTRUJE tylko Canon
        Używa MediaWiki API
        
        Args:
            max_items: None = bez limitu, pobierz wszystkie
        """
        cache_key = f"{universe}_{category}_canon"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            print(f"✓ Loaded {len(cached)} Canon {category} from cache")
            return cached
        
        # Fetch via API with Canon filtering
        print(f"📡 Fetching Canon {category} via API...")
        api_client = self._get_api_client(base_url)
        
        # ✅ ZMIENIONE: Użyj max_items albo BARDZO WYSOKI domyślny limit
        if max_items is None:
            # None = pobierz wszystkie (użyj bardzo wysoki limit jako safety)
            limit = 100000
        else:
            limit = max_items
        
        canon_items = api_client.get_canon_filtered_category(
            category,
            limit=limit,
            max_depth=self.config.max_subcategory_depth
        )
        
        if canon_items:
            # Save to cache
            self.cache.set(cache_key, canon_items)
            print(f"✅ Cached {len(canon_items)} Canon {category}")
        else:
            print(f"⚠️ No Canon items found for {category}")
        
        return canon_items
    
    # ========================================================================
    # Non-filtered methods (all items, not just Canon)
    # ========================================================================
    
    def scrape_category(
        self, 
        category: str, 
        base_url: str,
        universe: str,
        max_items: Optional[int] = None
    ) -> List[str]:
        """
        Scrapuje kategorię (wszystkie items, bez filtrowania Canon)
        Używa MediaWiki API
        """
        cache_key = f"{universe}_{category}_all"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            print(f"✓ Loaded {len(cached)} items for {category} from cache")
            return cached
        
        # Fetch via API
        print(f"📡 Fetching {category} via API (all items)...")
        api_client = self._get_api_client(base_url)
        
        # ✅ ZMIENIONE: Użyj max_items albo BARDZO WYSOKI domyślny limit
        limit = max_items if max_items is not None else 100000
        
        items = api_client.get_category_members(
            category,
            limit=limit,
            recursive=True,
            max_depth=self.config.max_subcategory_depth
        )
        
        if items:
            # Save to cache
            self.cache.set(cache_key, items)
            print(f"✅ Cached {len(items)} items for {category}")
        else:
            print(f"⚠️ No items found for {category}")
        
        return items
    
    def clear_cache(self):
        """Czyści cache (files + API clients)"""
        self.cache.clear()
        # Clear API client caches
        for client in self._api_clients.values():
            client.clear_cache()