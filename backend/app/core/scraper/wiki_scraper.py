# # backend/app/core/scraper/wiki_scraper.py
# from typing import Dict, List, Optional
# from .http_client import WikiHttpClient
# from .rate_limiter import RateLimiter
# from .cache_manager import CacheManager
# from .category_scraper import CategoryScraper
# from .character_scraper import CharacterScraper
# from .parsers.wookieepedia_parser import WookieepediaParser
# from .config import ScraperConfig
# from .wiki_content_cache import WikiContentCache
# from bs4 import BeautifulSoup, Comment

# class WikiScraper:
#     """
#     Główny interfejs do scrapowania wiki
#     Wspiera Canon filtering + NON-CANON detection dla WSZYSTKICH kategorii
#     """
    
#     def __init__(self):
#         self.config = ScraperConfig()
#         self.cache = CacheManager('cache', validity_hours=24)
#         self.content_cache = WikiContentCache('wiki_content_cache', validity_hours=168)
#         self.rate_limiter = RateLimiter(delay=self.config.request_delay)
#         self.http_client = WikiHttpClient(self.rate_limiter, timeout=self.config.request_timeout)
        
#         self.parser = WookieepediaParser()
#         self.category_scraper = CategoryScraper(
#             self.http_client,
#             self.parser,
#             self.cache,
#             self.config
#         )
#         self.character_scraper = CharacterScraper(self.http_client, self.parser)
        
#         self.base_urls = {
#             'star_wars': 'https://starwars.fandom.com',
#             'lotr': 'https://lotr.fandom.com',
#             'harry_potter': 'https://harrypotter.fandom.com'
#         }
    
#     # ========================================================================
#     # UNIWERSALNA METODA - dla wszystkich kategorii
#     # ========================================================================
    
#     def get_category_with_images(
#         self, 
#         category_name: str,
#         universe: str = 'star_wars', 
#         limit: int = 20
#     ) -> List[Dict]:
#         """
#         UNIWERSALNA metoda dla WSZYSTKICH kategorii
#         Pobiera listę z obrazkami (Canon już przefiltrowane przez API!)
        
#         Args:
#             category_name: 'Planets', 'Sentient_species', 'Organizations', etc.
#             universe: 'star_wars', 'lotr', etc.
#             limit: Max items to return
        
#         Returns:
#             [{"name": "...", "url": "...", "image_url": "...", "description": "..."}]
#         """
#         print(f"🔍 Loading {category_name} for {universe}...")
        
#         base_url = self.base_urls.get(universe)
#         if not base_url:
#             return []
        
#         # ✅ Get Canon-filtered names from API (already pre-filtered!)
#         item_names = self.category_scraper.scrape_canon_category(
#             category_name,
#             base_url,
#             universe,
#             max_items=limit * 2  # Get a bit more for safety
#         )
        
#         print(f"📋 Received {len(item_names)} Canon {category_name}")
        
#         # Teraz scrapuj obrazki (już wiemy że Canon!)
#         items = []
#         scraped_count = 0
#         cached_count = 0
        
#         for name in item_names[:limit]:
#             # Check WikiContentCache first
#             cached_data = self.content_cache.get_article(name, universe)
            
#             if cached_data:
#                 cached_count += 1
#                 items.append({
#                     'name': cached_data.get('name', name),
#                     'url': cached_data.get('url', ''),
#                     'image_url': cached_data.get('image_url', ''),
#                     'description': cached_data.get('description', '')
#                 })
#                 print(f"  ✓ {name} (from cache)")
#             else:
#                 # Scrapuj (już wiemy że Canon!)
#                 try:
#                     item_data = self._scrape_item_with_image_no_check(name, base_url)
#                     if item_data:
#                         scraped_count += 1
#                         items.append(item_data)
                        
#                         # Zapisz do WikiContentCache
#                         self.content_cache.save_article(name, universe, item_data)
#                         print(f"  ✓ {name} (scraped & cached)")
#                 except Exception as e:
#                     print(f"  ✗ {name}: {e}")
#                     continue
        
#         print(f"✅ Final result: {len(items)} {category_name}")
#         print(f"   (cached: {cached_count}, scraped: {scraped_count})")
        
#         return items
    
#     def _scrape_item_with_image_no_check(self, item_name: str, base_url: str) -> Optional[Dict]:
#         """
#         Scrapuje artykuł z obrazkiem BEZ sprawdzania NON-CANON
#         (już sprawdzone przez API)
#         """
#         # Search for item URL
#         url = self.character_scraper.search_character(item_name, base_url)
#         if not url:
#             return None
        
#         # Fetch page
#         response = self.http_client.get(url)
#         if not response:
#             return None
        
#         soup = BeautifulSoup(response.content, 'html.parser')
        
#         # Extract image from infobox
#         image_url = self._extract_infobox_image(soup)
        
#         # Extract short description
#         description = self._extract_first_paragraph(soup)
        
#         return {
#             'name': item_name.replace('_', ' '),
#             'url': url,
#             'image_url': image_url or self._get_placeholder_image(item_name),
#             'description': description[:200] if description else '',
#             'is_canon': True
#         }
    
#     def _extract_infobox_image(self, soup: BeautifulSoup) -> Optional[str]:
#         """Wyciąga obrazek z infoboxa"""
#         # Try portable infobox (Fandom style)
#         infobox = soup.find('aside', class_='portable-infobox')
#         if infobox:
#             img = infobox.find('img')
#             if img and 'src' in img.attrs:
#                 src = img['src']
#                 # Remove thumbnail parameters for full size
#                 if '/revision/' in src:
#                     src = src.split('/revision/')[0]
#                 return src
        
#         # Try old-style infobox
#         infobox = soup.find('table', class_='infobox')
#         if infobox:
#             img = infobox.find('img')
#             if img and 'src' in img.attrs:
#                 return img['src']
        
#         # Try first image in content
#         content = soup.find('div', class_='mw-parser-output')
#         if content:
#             img = content.find('img')
#             if img and 'src' in img.attrs:
#                 return img['src']
        
#         return None
    
#     def _extract_first_paragraph(self, soup: BeautifulSoup) -> Optional[str]:
#         """Wyciąga pierwszy paragraf jako opis"""
#         content = soup.find('div', class_='mw-parser-output')
#         if content:
#             paragraphs = content.find_all('p', recursive=False)
#             for p in paragraphs:
#                 text = p.text.strip()
#                 if text and len(text) > 20:
#                     # Remove citations [1], [2]
#                     import re
#                     text = re.sub(r'\[\d+\]', '', text)
#                     return text
#         return None
    
#     def _get_placeholder_image(self, item_name: str) -> str:
#         """Generuje placeholder jeśli nie ma obrazka"""
#         clean_name = item_name.replace('_', '+').replace(' ', '+')
#         return f"https://via.placeholder.com/400x300/1a1a2e/16a085?text={clean_name}"
    
#     # ========================================================================
#     # PUBLICZNE METODY - używają uniwersalnej get_category_with_images()
#     # ========================================================================
    
#     def get_planets_list(self, universe: str = 'star_wars', limit: int = 20) -> List[Dict]:
#         """Pobiera planety z obrazkami (Canon + NON-CANON filtered)"""
#         return self.get_category_with_images('Planets', universe, limit)
    
#     def get_species_list(self, universe: str = 'star_wars', limit: int = 20) -> List[Dict]:
#         """Pobiera gatunki z obrazkami (Canon + NON-CANON filtered)"""
#         return self.get_category_with_images('Sentient_species', universe, limit)
    
#     def get_organizations_list(self, universe: str = 'star_wars', limit: int = 20) -> List[Dict]:
#         """Pobiera organizacje z obrazkami (Canon + NON-CANON filtered)"""
#         return self.get_category_with_images('Organizations', universe, limit)
    
#     def get_vehicles_list(self, universe: str = 'star_wars', limit: int = 20) -> List[Dict]:
#         """Pobiera pojazdy z obrazkami (Canon + NON-CANON filtered)"""
#         return self.get_category_with_images('Vehicles', universe, limit)
    
#     def get_weapons_list(self, universe: str = 'star_wars', limit: int = 20) -> List[Dict]:
#         """Pobiera broń z obrazkami (Canon + NON-CANON filtered)"""
#         return self.get_category_with_images('Weapons', universe, limit)
    
#     # ========================================================================
#     # STARE METODY - tylko nazwy (bez obrazków)
#     # ========================================================================
    
#     def get_all_planets(self, universe: str = 'star_wars') -> List[str]:
#         """Pobiera WSZYSTKIE planety (tylko nazwy, bez obrazków)"""
#         base_url = self.base_urls.get(universe)
#         if not base_url:
#             return []
        
#         return self.category_scraper.scrape_canon_category(
#             'Planets',
#             base_url,
#             universe,
#             max_items=None
#         )
    
#     def get_all_species(self, universe: str = 'star_wars') -> List[str]:
#         """Pobiera WSZYSTKIE gatunki (tylko nazwy)"""
#         base_url = self.base_urls.get(universe)
#         if not base_url:
#             return []
        
#         return self.category_scraper.scrape_canon_category(
#             'Sentient_species',
#             base_url,
#             universe,
#             max_items=None
#         )
    
#     def get_all_organizations(self, universe: str = 'star_wars') -> List[str]:
#         """Pobiera WSZYSTKIE organizacje (tylko nazwy)"""
#         base_url = self.base_urls.get(universe)
#         if not base_url:
#             return []
        
#         return self.category_scraper.scrape_canon_category(
#             'Organizations',
#             base_url,
#             universe,
#             max_items=None
#         )
    
#     def get_colors(self) -> List[str]:
#         """Podstawowe kolory"""
#         return [
#             'Blue', 'Green', 'Brown', 'Gray', 'Black', 'White',
#             'Red', 'Yellow', 'Orange', 'Purple', 'Pink', 'Blonde',
#             'Auburn', 'Silver', 'Gold', 'Tan', 'Pale', 'Dark'
#         ]
    
#     # ========================================================================
#     # Character Methods
#     # ========================================================================
    
#     def search_character(self, character_name: str, universe: str = 'star_wars') -> Optional[str]:
#         """Wyszukaj postać i zwróć URL"""
#         base_url = self.base_urls.get(universe)
#         if not base_url:
#             return None
#         return self.character_scraper.search_character(character_name, base_url)
    
#     def scrape_character_data(self, url: str) -> Dict:
#         """Scrapuje pełne dane postaci z URL"""
#         return self.character_scraper.scrape_character(url)
    
#     def clear_cache(self):
#         """Czyści cache"""
#         self.cache.clear()
#         self.content_cache.clear()
#         self.category_scraper.clear_cache()

# backend/app/core/scraper/wiki_scraper.py

# backend/app/core/scraper/wiki_scraper.py

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from app.core.scraper.canon_cache import CanonCache

class WikiScraper:
    """
    Klasa do scrapowania danych z wiki z pełnym wsparciem Canon
    + PARALLEL PROCESSING dla ultra szybkości!
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.wiki_urls = {
            'star_wars': 'https://starwars.fandom.com/wiki/',
            'lotr': 'https://lotr.fandom.com/wiki/',
            'harry_potter': 'https://harrypotter.fandom.com/wiki/'
        }
        
        # ✨ Cache system
        self.canon_cache = CanonCache()
        
        # Keywords dla kategoryzacji
        self.CATEGORY_KEYWORDS = {
            # Characters & Species
            'characters': [
                'individuals', 'males', 'females', 'characters',
                'jedi', 'sith', 'bounty hunters', 'pirates',
                'smugglers', 'officers', 'generals'
            ],
            'species': [
                'sentient species', 'species', 'humanoid species',
                'near-human species', 'reptilian species', 'amphibian species'
            ],
            
            # Organizations
            'organizations': [
                'organizations', 'governments', 'military units',
                'criminal organizations', 'religious organizations',
                'companies', 'corporations', 'syndicates'
            ],
            
            # Planets & Locations
            'planets': [
                'planets', 'outer rim planets', 'core worlds',
                'mid rim planets', 'inner rim planets',
                'unknown regions planets', 'wild space planets',
                'expansion region planets'
            ],
            'locations': [
                'locations', 'cities', 'bases', 'temples',
                'cantinas', 'spaceports', 'palaces', 'prisons',
                'fortresses', 'settlements', 'stations'
            ],
            
            # Battles & Events
            'battles': [
                'battles', 'wars', 'conflicts', 'skirmishes',
                'sieges', 'campaigns'
            ],
            'events': [
                'events', 'ceremonies', 'missions', 'operations',
                'treaties', 'agreements'
            ],
            
            # Weapons & Armor
            'weapons': [
                'weapons', 'blasters', 'blaster pistols', 'blaster rifles',
                'heavy blasters', 'lightsabers', 'vibroblades',
                'explosives', 'grenades', 'slugthrower weapons',
                'projectile weapons', 'melee weapons'
            ],
            'armor': [
                'armor', 'stormtrooper armor', 'mandalorian armor',
                'battle armor', 'body armor', 'helmets', 'suits'
            ],
            
            # Items & Equipment
            'items': [
                'items', 'equipment', 'tools', 'medical equipment',
                'communication devices', 'sensors', 'scanners',
                'cybernetics', 'prosthetics', 'credits', 'currency',
                'food', 'beverages', 'clothing'
            ],
            
            # Vehicles
            'vehicles': [
                'starfighters', 'capital ships', 'transports',
                'speeders', 'landspeeders', 'airspeeders',
                'swoop bikes', 'walkers', 'at-at', 'at-st',
                'corvettes', 'frigates', 'cruisers', 'destroyers'
            ],
            
            # Droids
            'droids': [
                'droid models', 'protocol droids', 'astromech droids',
                'medical droids', 'battle droids', 'assassin droids',
                'utility droids', 'labor droids'
            ],
            
            # Technology
            'technology': [
                'technology', 'computers', 'holocrons', 'hyperdrives',
                'shields', 'deflector shields', 'reactors',
                'power generators', 'navicomputers'
            ],
            
            # Creatures
            'creatures': [
                'creatures', 'non-sentient species', 'predators',
                'beasts of burden', 'pets', 'mounts', 'fauna'
            ],
            
            # Abilities & Powers
            'abilities': [
                'force powers', 'combat abilities', 'skills',
                'techniques', 'force techniques'
            ],
        }
    
    # ============================================
    # GŁÓWNA METODA - Get All Canon Data
    # ============================================
    
    def get_canon_categorized_data(
        self, 
        universe: str = 'star_wars',
        depth: int = 3,
        limit: int = 60000,
        force_refresh: bool = False
    ) -> Dict[str, List[str]]:
        """
        Pobiera WSZYSTKIE Canon_articles i kategoryzuje
        
        Args:
            universe: star_wars, lotr, harry_potter
            depth: Głębokość rekurencji (3 = recommended)
            limit: Max artykułów (60000 = full coverage)
            force_refresh: Pomiń cache i pobierz na nowo
        
        Returns:
            Dict z 15 kategoriami artykułów (100% Canon!)
        """
        
        print(f"\n{'='*60}")
        print(f"🎯 Canon Articles Scraper")
        print(f"{'='*60}")
        print(f"Universe: {universe}")
        print(f"Depth: {depth}")
        print(f"Limit: {limit:,}")
        print(f"Force refresh: {force_refresh}")
        print(f"{'='*60}\n")
        
        # 1. Try cache first
        if not force_refresh:
            cached = self.canon_cache.load(universe, depth)
            if cached:
                return cached
        
        # 2. Fetch from API
        print(f"🔄 Fetching fresh data from {universe} wiki...")
        print(f"⏱️  This may take 2-3 minutes...\n")
        
        all_canon = self._fetch_category_recursive(
            category="Category:Canon_articles",
            universe=universe,
            depth=depth,
            limit=limit
        )
        
        print(f"\n✅ Fetched {len(all_canon):,} canon articles")
        
        # 3. Categorize (PARALLEL!)
        print(f"\n🔥 Categorizing articles (PARALLEL MODE)...")
        categorized = self._categorize_articles_parallel(all_canon, universe)
        
        # 4. Save to cache
        print(f"\n💾 Saving to cache...")
        self.canon_cache.save(universe, depth, categorized)
        
        print(f"\n{'='*60}")
        print(f"✅ Done! Cache will be valid for {self.canon_cache.ttl_days} days")
        print(f"{'='*60}\n")
        
        return categorized
    
    # ============================================
    # RECURSIVE CATEGORY FETCHING
    # ============================================
    
    def _fetch_category_recursive(
        self,
        category: str,
        universe: str,
        depth: int = 3,
        limit: int = 60000,
        _current_depth: int = 0,
        _visited: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Rekurencyjnie pobiera artykuły z kategorii
        """
        
        if _visited is None:
            _visited = set()
        
        # Anti-loop protection
        if category in _visited:
            return []
        _visited.add(category)
        
        # Depth limit
        if _current_depth > depth:
            return []
        
        indent = "  " * _current_depth
        print(f"{indent}📁 {category} (depth {_current_depth}/{depth})")
        
        all_articles = []
        
        try:
            # Get API URL
            base_url = self.wiki_urls.get(universe, self.wiki_urls['star_wars'])
            api_url = base_url.replace('/wiki/', '/api.php')
            
            # Paginated fetch
            continue_token = None
            
            while True:
                params = {
                    'action': 'query',
                    'list': 'categorymembers',
                    'cmtitle': category,
                    'cmlimit': 500,
                    'format': 'json'
                }
                
                if continue_token:
                    params['cmcontinue'] = continue_token
                
                response = requests.get(
                    api_url, 
                    params=params, 
                    headers=self.headers,
                    timeout=30
                )
                data = response.json()
                
                if 'query' not in data:
                    break
                
                members = data['query']['categorymembers']
                
                for member in members:
                    title = member['title']
                    ns = member.get('ns', 0)
                    
                    # ns=14 = Category
                    if ns == 14:
                        if _current_depth < depth:
                            sub_articles = self._fetch_category_recursive(
                                category=title,
                                universe=universe,
                                depth=depth,
                                limit=limit,
                                _current_depth=_current_depth + 1,
                                _visited=_visited
                            )
                            all_articles.extend(sub_articles)
                    
                    # ns=0 = Article
                    elif ns == 0:
                        # Skip meta pages
                        if not any(skip in title for skip in [
                            'List of', 'Timeline of', 'Category:',
                            'Wookieepedia:', 'Template:', 'User:'
                        ]):
                            all_articles.append(title)
                    
                    # Limit check
                    if len(all_articles) >= limit:
                        print(f"{indent}⚠️  Limit reached: {limit:,}")
                        return all_articles[:limit]
                
                # Pagination
                if 'continue' not in data:
                    break
                
                continue_token = data['continue'].get('cmcontinue')
                if not continue_token:
                    break
            
            print(f"{indent}✅ {len(all_articles):,} articles")
            
        except Exception as e:
            print(f"{indent}❌ Error: {e}")
        
        return all_articles
    
    # ============================================
    # 🔥 PARALLEL CATEGORIZATION (ULTRA FAST!)
    # ============================================
    
    def _get_article_categories_batch(
        self, 
        article_titles: List[str],
        universe: str
    ) -> Dict[str, List[str]]:
        """
        Pobiera kategorie dla wielu artykułów naraz (BATCH!)
        
        API MediaWiki pozwala na max 50 tytułów na request
        """
        
        try:
            base_url = self.wiki_urls.get(universe, self.wiki_urls['star_wars'])
            api_url = base_url.replace('/wiki/', '/api.php')
            
            # Join titles with pipe separator (max 50)
            titles_param = '|'.join(article_titles[:50])
            
            params = {
                'action': 'query',
                'prop': 'categories',
                'titles': titles_param,
                'cllimit': 500,
                'format': 'json'
            }
            
            response = requests.get(
                api_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            data = response.json()
            
            if 'query' not in data or 'pages' not in data['query']:
                return {}
            
            # Parse results
            results = {}
            pages = data['query']['pages']
            
            for page_id, page_data in pages.items():
                if 'title' not in page_data:
                    continue
                    
                title = page_data['title']
                
                if 'categories' in page_data:
                    categories = [
                        cat['title'].replace('Category:', '')
                        for cat in page_data['categories']
                    ]
                    results[title] = categories
                else:
                    results[title] = []
            
            return results
            
        except Exception as e:
            # Silent fail - return empty dict
            return {}
    
    def _categorize_articles_parallel(
        self, 
        articles: List[str],
        universe: str,
        max_workers: int = 10  # 10 równoległych requestów!
    ) -> Dict[str, List[str]]:
        """
        Kategoryzuje artykuły - PARALLEL + BATCH = ULTRA FAST!
        
        20x szybciej niż wersja sekwencyjna!
        """
        
        categorized = {key: [] for key in self.CATEGORY_KEYWORDS.keys()}
        categorized_lock = threading.Lock()  # Thread safety
        
        total = len(articles)
        batch_size = 50  # API limit
        batches = [articles[i:i + batch_size] for i in range(0, total, batch_size)]
        
        print(f"\n🔥🔥🔥 PARALLEL BATCH MODE ACTIVATED!")
        print(f"   Workers: {max_workers} threads")
        print(f"   Batch size: {batch_size} articles/request")
        print(f"   Total batches: {len(batches):,}")
        print(f"   Estimated time: ~{len(batches) / max_workers / 2:.1f} minutes\n")
        
        completed_batches = 0
        
        def process_batch(batch):
            """Process single batch of 50 articles"""
            
            # Get categories for entire batch (1 request!)
            batch_categories = self._get_article_categories_batch(batch, universe)
            
            # Categorize all articles from batch
            local_categorized = {key: [] for key in self.CATEGORY_KEYWORDS.keys()}
            
            for article in batch:
                categories = batch_categories.get(article, [])
                
                # Match against our keywords
                for our_category, keywords in self.CATEGORY_KEYWORDS.items():
                    for cat in categories:
                        cat_lower = cat.lower()
                        
                        if any(kw in cat_lower for kw in keywords):
                            if article not in local_categorized[our_category]:
                                local_categorized[our_category].append(article)
                            break
            
            return local_categorized
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(process_batch, batch): idx 
                for idx, batch in enumerate(batches)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                
                try:
                    local_categorized = future.result()
                    
                    # Merge results (thread-safe)
                    with categorized_lock:
                        for category, items in local_categorized.items():
                            categorized[category].extend(items)
                        
                        completed_batches += 1
                        
                        # Progress update every 50 batches
                        if completed_batches % 50 == 0 or completed_batches == len(batches):
                            progress = (completed_batches / len(batches)) * 100
                            print(f"   ⚡ Progress: {completed_batches:,}/{len(batches):,} batches ({progress:.1f}%)")
                
                except Exception as e:
                    print(f"   ❌ Error in batch {batch_idx}: {e}")
        
        # Remove duplicates
        print(f"\n🔧 Removing duplicates...")
        for category in categorized:
            categorized[category] = list(set(categorized[category]))
        
        # Final stats
        print(f"\n📊 Categorization Results:")
        for category, items in sorted(categorized.items(), key=lambda x: -len(x[1])):
            if items:
                print(f"   {category:15s}: {len(items):5,} items")
        
        return categorized
    
    # ============================================
    # OLD METHODS (still here for character scraping)
    # ============================================
    
    def search_character(self, character_name: str, universe: str = 'star_wars') -> Optional[str]:
        """Wyszukuje postać w wiki i zwraca URL do jej strony"""
        base_url = self.wiki_urls.get(universe, self.wiki_urls['star_wars'])
        
        character_url = character_name.replace(' ', '_')
        full_url = f"{base_url}{character_url}"
        
        try:
            response = requests.get(full_url, headers=self.headers)
            if response.status_code == 200:
                return full_url
            else:
                return self._search_via_api(character_name, universe)
        except Exception as e:
            print(f"Błąd podczas wyszukiwania: {e}")
            return None
    
    def scrape_character_data(self, url: str) -> Dict:
        """Pobiera dane o postaci z podanego URL"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            character_data = {
                'name': self._extract_name(soup),
                'description': self._extract_description(soup),
                'biography': self._extract_biography(soup),
                'abilities': self._extract_abilities(soup),
                'affiliations': self._extract_affiliations(soup),
                'appearances': self._extract_appearances(soup),
                'image_url': self._extract_image(soup),
                'info_box': self._extract_infobox(soup)
            }
            
            return character_data
            
        except Exception as e:
            print(f"Błąd podczas scrapowania: {e}")
            return {}
    
    def _extract_name(self, soup: BeautifulSoup) -> str:
        title_element = soup.find('h1', class_='page-header__title')
        if title_element:
            return title_element.text.strip()
        
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.text.split('|')[0].strip()
        
        return "Unknown"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        content = soup.find('div', class_='mw-parser-output')
        if content:
            paragraphs = content.find_all('p', recursive=False)
            for p in paragraphs:
                text = p.text.strip()
                if text and len(text) > 20:
                    text = re.sub(r'\[\d+\]', '', text)
                    return text
        return ""
    
    def _extract_biography(self, soup: BeautifulSoup) -> str:
        biography_sections = []
        
        headers = soup.find_all(['h2', 'h3'])
        
        for header in headers:
            header_text = header.text.lower()
            if 'biography' in header_text or 'history' in header_text:
                current = header.find_next_sibling()
                section_text = []
                
                while current and current.name not in ['h2', 'h3']:
                    if current.name == 'p':
                        text = current.text.strip()
                        text = re.sub(r'\[\d+\]', '', text)
                        if text:
                            section_text.append(text)
                    current = current.find_next_sibling()
                
                if section_text:
                    biography_sections.append('\n'.join(section_text))
        
        return '\n\n'.join(biography_sections)[:2000]
    
    def _extract_abilities(self, soup: BeautifulSoup) -> List[str]:
        abilities = []
        
        headers = soup.find_all(['h2', 'h3'])
        
        for header in headers:
            header_text = header.text.lower()
            if any(word in header_text for word in ['power', 'abilit', 'skill']):
                next_element = header.find_next_sibling()
                if next_element and next_element.name == 'ul':
                    for li in next_element.find_all('li'):
                        ability = li.text.strip()
                        ability = re.sub(r'\[\d+\]', '', ability)
                        if ability:
                            abilities.append(ability)
        
        return abilities[:10]
    
    def _extract_affiliations(self, soup: BeautifulSoup) -> List[str]:
        affiliations = []
        
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            sections = infobox.find_all('section')
            for section in sections:
                label = section.find('h3')
                if label and 'affiliation' in label.text.lower():
                    values = section.find_all('a')
                    for value in values:
                        affiliations.append(value.text.strip())
        
        return list(set(affiliations))[:5]
    
    def _extract_appearances(self, soup: BeautifulSoup) -> List[str]:
        appearances = []
        
        headers = soup.find_all('h2')
        for header in headers:
            if 'appearances' in header.text.lower():
                next_element = header.find_next_sibling()
                if next_element and next_element.name == 'ul':
                    for li in next_element.find_all('li')[:10]:
                        appearances.append(li.text.strip())
        
        return appearances
    
    def _extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            img = infobox.find('img')
            if img and 'src' in img.attrs:
                return img['src']
        
        content = soup.find('div', class_='mw-parser-output')
        if content:
            img = content.find('img')
            if img and 'src' in img.attrs:
                return img['src']
        
        return None
    
    def _extract_infobox(self, soup: BeautifulSoup) -> Dict:
        info = {}
        
        infobox = soup.find('aside', class_='portable-infobox')
        if not infobox:
            return info
        
        sections = infobox.find_all('div', class_='pi-item')
        for section in sections:
            label = section.find('h3', class_='pi-data-label')
            value = section.find('div', class_='pi-data-value')
            
            if label and value:
                key = label.text.strip().lower().replace(' ', '_')
                val = value.text.strip()
                info[key] = val
        
        return info
    
    def _search_via_api(self, query: str, universe: str) -> Optional[str]:
        return None
    
    # ============================================
    # BACKWARD COMPATIBLE METHODS
    # ============================================
    
    def get_all_species(self, universe: str, limit: int = 2000) -> List[str]:
        """✅ 100% Canon species"""
        data = self.get_canon_categorized_data(universe)
        return data['species'][:limit]
    
    def get_all_planets(self, universe: str, limit: int = 3000) -> List[str]:
        """✅ 100% Canon planets"""
        data = self.get_canon_categorized_data(universe)
        return data['planets'][:limit]
    
    def get_all_organizations(self, universe: str, limit: int = 1500) -> List[str]:
        """✅ 100% Canon organizations"""
        data = self.get_canon_categorized_data(universe)
        return data['organizations'][:limit]
    
    def get_all_weapons(self, universe: str, limit: int = 1200) -> List[str]:
        """✅ 100% Canon weapons"""
        data = self.get_canon_categorized_data(universe)
        return data['weapons'][:limit]
    
    def get_all_vehicles(self, universe: str, limit: int = 2000) -> List[str]:
        """✅ 100% Canon vehicles"""
        data = self.get_canon_categorized_data(universe)
        return data['vehicles'][:limit]
    
    def get_all_locations(self, universe: str, limit: int = 5000) -> List[str]:
        """✅ 100% Canon locations"""
        data = self.get_canon_categorized_data(universe)
        return data['locations'][:limit]
    
    def get_all_characters(self, universe: str, limit: int = 15000) -> List[str]:
        """✅ 100% Canon characters"""
        data = self.get_canon_categorized_data(universe)
        return data['characters'][:limit]
    
    def get_all_droids(self, universe: str, limit: int = 400) -> List[str]:
        """✅ 100% Canon droids"""
        data = self.get_canon_categorized_data(universe)
        return data['droids'][:limit]
    
    def get_all_armor(self, universe: str, limit: int = 300) -> List[str]:
        """✅ 100% Canon armor"""
        data = self.get_canon_categorized_data(universe)
        return data['armor'][:limit]
    
    def get_all_items(self, universe: str, limit: int = 4000) -> List[str]:
        """✅ 100% Canon items"""
        data = self.get_canon_categorized_data(universe)
        return data['items'][:limit]
    
    def get_all_battles(self, universe: str, limit: int = 800) -> List[str]:
        """✅ 100% Canon battles"""
        data = self.get_canon_categorized_data(universe)
        return data['battles'][:limit]
    
    def get_all_creatures(self, universe: str, limit: int = 1500) -> List[str]:
        """✅ 100% Canon creatures"""
        data = self.get_canon_categorized_data(universe)
        return data['creatures'][:limit]
    
    def get_all_technology(self, universe: str, limit: int = 800) -> List[str]:
        """✅ 100% Canon technology"""
        data = self.get_canon_categorized_data(universe)
        return data['technology'][:limit]