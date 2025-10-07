# backend/app/core/scraper/wiki_scraper.py
from typing import List, Dict, Optional, Set
import requests
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
        
        # Inicjalizacja komponentów
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
    
    def _get_all_category_members_recursive(
        self,
        category: str,
        base_url: str,
        universe: str,
        max_depth: int = 2
    ) -> List[str]:
        """
        Rekurencyjnie pobiera wszystkie elementy z kategorii i podkategorii
        Używa MediaWiki API zamiast HTML scrapingu
        """
        api_url = f"{base_url}/api.php"
        all_items: Set[str] = set()
        processed_categories: Set[str] = set()
        
        def scrape_category_api(cat_name: str, depth: int = 0):
            if depth > max_depth or cat_name in processed_categories:
                return
            
            processed_categories.add(cat_name)
            print(f"  {'  ' * depth}Scraping {cat_name} (depth: {depth})")
            
            params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': f'Category:{cat_name}',
                'cmlimit': 500,
                'format': 'json'
            }
            
            continue_token = None
            pages_count = 0
            
            while True:
                if continue_token:
                    params['cmcontinue'] = continue_token
                
                try:
                    self.rate_limiter.wait_if_needed()
                    response = requests.get(
                        api_url, 
                        params=params, 
                        timeout=self.config.request_timeout,
                        headers=self.http_client.headers
                    )
                    data = response.json()
                    
                    if 'query' not in data or 'categorymembers' not in data['query']:
                        break
                    
                    members = data['query']['categorymembers']
                    
                    for member in members:
                        title = member['title']
                        ns = member['ns']
                        
                        if ns == 14:  # Subcategory
                            subcat_name = title.replace('Category:', '')
                            scrape_category_api(subcat_name, depth + 1)
                        elif ns == 0:  # Article
                            if not self._is_meta_page(title):
                                all_items.add(title)
                    
                    pages_count += len(members)
                    print(f"  {'  ' * depth}  +{len(members)} items (batch total: {pages_count})")
                    
                    # Paginacja
                    if 'continue' in data and 'cmcontinue' in data['continue']:
                        continue_token = data['continue']['cmcontinue']
                    else:
                        break
                        
                except Exception as e:
                    print(f"  {'  ' * depth}  Error: {e}")
                    break
        
        scrape_category_api(category)
        
        result = sorted(list(all_items))
        print(f"  Total unique items: {len(result)}")
        return result
    
    def _is_meta_page(self, title: str) -> bool:
        """Filtruje meta-strony i listy"""
        meta_keywords = [
            'List of', 'Lists of', 'Category:', 'Template:',
            'File:', 'Help:', 'User:', 'Talk:', 'Special:',
            'Unidentified', 'Unknown'
        ]
        return any(title.startswith(keyword) for keyword in meta_keywords)
    
    def get_all_species(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz wszystkie gatunki/rasy rekurencyjnie"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        category = 'Sentient_species' if universe == 'star_wars' else 'Races'
        cache_key = f"{universe}_{category}_recursive"
        
        # Sprawdź cache
        cached = self.cache.get(cache_key)
        if cached:
            print(f"Loaded {len(cached)} species from cache")
            return cached
        
        print(f"Scraping {category} recursively from {universe}...")
        
        try:
            species = self._get_all_category_members_recursive(
                category,
                base_url,
                universe,
                max_depth=3
            )
            
            if species:
                self.cache.set(cache_key, species)
            
            return species
            
        except Exception as e:
            print(f"API scraping failed, falling back to HTML: {e}")
            return self.category_scraper.scrape_category(
                category, base_url, universe, max_items=1000
            )
    
    def get_all_planets(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz wszystkie planety rekurencyjnie"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        cache_key = f"{universe}_Planets_recursive"
        
        # Sprawdź cache
        cached = self.cache.get(cache_key)
        if cached:
            print(f"Loaded {len(cached)} planets from cache")
            return cached
        
        print(f"Scraping Planets recursively from {universe}...")
        
        try:
            planets = self._get_all_category_members_recursive(
                'Planets',
                base_url,
                universe,
                max_depth=3  # Planets -> Desert_planets -> items
            )
            
            if planets:
                self.cache.set(cache_key, planets)
            
            return planets
            
        except Exception as e:
            print(f"API scraping failed, falling back to HTML: {e}")
            return self.category_scraper.scrape_category(
                'Planets', base_url, universe, max_items=800
            )
    
    def get_all_organizations(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz wszystkie organizacje rekurencyjnie"""
        base_url = self.base_urls.get(universe)
        if not base_url:
            return []
        
        cache_key = f"{universe}_Organizations_recursive"
        
        # Sprawdź cache
        cached = self.cache.get(cache_key)
        if cached:
            print(f"Loaded {len(cached)} organizations from cache")
            return cached
        
        print(f"Scraping Organizations recursively from {universe}...")
        
        try:
            orgs = self._get_all_category_members_recursive(
                'Organizations',
                base_url,
                universe,
                max_depth=3
            )
            
            if orgs:
                self.cache.set(cache_key, orgs)
            
            return orgs
            
        except Exception as e:
            print(f"API scraping failed, falling back to HTML: {e}")
            return self.category_scraper.scrape_category(
                'Organizations', base_url, universe, max_items=500
            )
    
    def get_popular_affiliations(self, universe: str = 'star_wars') -> List[str]:
        """Pobierz popularne afiliacje (kombinacja kategorii)"""
        affiliations = set()
        
        orgs = self.get_all_organizations(universe)
        affiliations.update(orgs)
        
        return sorted(list(affiliations))
    
    def get_colors(self) -> List[str]:
        """Lista kolorów"""
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