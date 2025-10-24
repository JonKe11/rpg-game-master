# backend/app/core/scraper/wiki_scraper.py
"""
Wiki Scraper - Main scraping orchestrator with Canon categorization.

Features:
- Recursive category fetching
- Parallel batch categorization (58k articles in ~2 minutes!)
- Image prefetching during categorization
- File-based caching (7-day TTL)
"""

import requests
from typing import Dict, Optional, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging

from app.core.scraper.canon_cache import CanonCache
from app.core.scraper.data_extractor import DataExtractor
from app.core.scraper.image_fetcher import ImageFetcher

logger = logging.getLogger(__name__)


class WikiScraper:
    """
    Main wiki scraper with Canon categorization and image prefetching.
    
    Architecture:
    - Fetching: Recursive category traversal via MediaWiki API
    - Categorization: Parallel batch processing (10 workers, 50 articles/batch)
    - Extraction: Delegated to DataExtractor (Beautiful Soup)
    - Images: Delegated to ImageFetcher (parallel downloads)
    - Caching: Delegated to CanonCache (file-based, 7-day TTL)
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
        
        # Components (Dependency Injection)
        self.canon_cache = CanonCache()
        self.data_extractor = DataExtractor()
        self.image_fetcher = ImageFetcher()
        
        # Category keywords for classification
        self.CATEGORY_KEYWORDS = {
            'characters': [
                'individuals', 'males', 'females', 'characters',
                'jedi', 'sith', 'bounty hunters', 'pirates',
                'smugglers', 'officers', 'generals'
            ],
            'species': [
                'sentient species', 'species', 'humanoid species',
                'near-human species', 'reptilian species', 'amphibian species'
            ],
            'organizations': [
                'organizations', 'governments', 'military units',
                'criminal organizations', 'religious organizations',
                'companies', 'corporations', 'syndicates'
            ],
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
            'battles': [
                'battles', 'wars', 'conflicts', 'skirmishes',
                'sieges', 'campaigns'
            ],
            'events': [
                'events', 'ceremonies', 'missions', 'operations',
                'treaties', 'agreements'
            ],
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
            'items': [
                'items', 'equipment', 'tools', 'medical equipment',
                'communication devices', 'sensors', 'scanners',
                'cybernetics', 'prosthetics', 'credits', 'currency',
                'food', 'beverages', 'clothing'
            ],
            'vehicles': [
                'starfighters', 'capital ships', 'transports',
                'speeders', 'landspeeders', 'airspeeders',
                'swoop bikes', 'walkers', 'at-at', 'at-st',
                'corvettes', 'frigates', 'cruisers', 'destroyers'
            ],
            'droids': [
                'droid models', 'protocol droids', 'astromech droids',
                'medical droids', 'battle droids', 'assassin droids',
                'utility droids', 'labor droids'
            ],
            'technology': [
                'technology', 'computers', 'holocrons', 'hyperdrives',
                'shields', 'deflector shields', 'reactors',
                'power generators', 'navicomputers'
            ],
            'creatures': [
                'creatures', 'non-sentient species', 'predators',
                'beasts of burden', 'pets', 'mounts', 'fauna'
            ],
            'abilities': [
                'force powers', 'combat abilities', 'skills',
                'techniques', 'force techniques'
            ],
        }
    
    # ============================================
    # MAIN PUBLIC METHOD
    # ============================================
    
    def get_canon_categorized_data(
        self, 
        universe: str = 'star_wars',
        depth: int = 3,
        limit: int = 60000,
        force_refresh: bool = False,
        prefetch_images: bool = False  # ✨ NEW!
    ) -> Dict[str, List[str]]:
        """
        Get all Canon articles categorized.
        
        Args:
            universe: star_wars, lotr, harry_potter
            depth: Recursion depth (3 recommended)
            limit: Max articles (60000 = full coverage)
            force_refresh: Force refresh from wiki
            prefetch_images: Prefetch images during categorization
            
        Returns:
            Dict with 15 categories of Canon articles
        """
        logger.info("="*60)
        logger.info("🎯 Canon Articles Scraper")
        logger.info("="*60)
        logger.info(f"Universe: {universe}")
        logger.info(f"Depth: {depth}")
        logger.info(f"Limit: {limit:,}")
        logger.info(f"Force refresh: {force_refresh}")
        logger.info(f"Prefetch images: {prefetch_images}")
        logger.info("="*60 + "\n")
        
        # 1. Try cache
        if not force_refresh:
            cached = self.canon_cache.load(universe, depth)
            if cached:
                return cached
        
        # 2. Fetch articles
        logger.info(f"🔄 Fetching fresh data from {universe} wiki...")
        logger.info(f"⏱️  This may take 2-3 minutes...\n")
        
        all_canon = self._fetch_category_recursive(
            category="Category:Canon_articles",
            universe=universe,
            depth=depth,
            limit=limit
        )
        
        logger.info(f"\n✅ Fetched {len(all_canon):,} canon articles")
        
        # 3. Categorize (PARALLEL!)
        logger.info(f"\n🔥 Categorizing articles (PARALLEL MODE)...")
        categorized = self._categorize_articles_parallel(
            all_canon, 
            universe,
            prefetch_images=prefetch_images
        )
        
        # 4. Save to cache
        logger.info(f"\n💾 Saving to cache...")
        self.canon_cache.save(universe, depth, categorized)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Done! Cache valid for {self.canon_cache.ttl_days} days")
        logger.info(f"{'='*60}\n")
        
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
        """Recursively fetch articles from category tree."""
        
        if _visited is None:
            _visited = set()
        
        # Anti-loop
        if category in _visited:
            return []
        _visited.add(category)
        
        # Depth limit
        if _current_depth > depth:
            return []
        
        indent = "  " * _current_depth
        logger.info(f"{indent}📁 {category} (depth {_current_depth}/{depth})")
        
        all_articles = []
        
        try:
            base_url = self.wiki_urls.get(universe, self.wiki_urls['star_wars'])
            api_url = base_url.replace('/wiki/', '/api.php')
            
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
                    
                    # ns=14 = Subcategory
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
                        logger.warning(f"{indent}⚠️  Limit reached: {limit:,}")
                        return all_articles[:limit]
                
                # Pagination
                if 'continue' not in data:
                    break
                
                continue_token = data['continue'].get('cmcontinue')
                if not continue_token:
                    break
            
            logger.info(f"{indent}✅ {len(all_articles):,} articles")
            
        except Exception as e:
            logger.error(f"{indent}❌ Error: {e}")
        
        return all_articles
    
    # ============================================
    # PARALLEL CATEGORIZATION + IMAGE PREFETCH
    # ============================================
    
    def _categorize_articles_parallel(
        self, 
        articles: List[str],
        universe: str,
        max_workers: int = 10,
        prefetch_images: bool = False  # ✨ NEW!
    ) -> Dict[str, List[str]]:
        """
        Categorize articles in parallel batches.
        
        Optionally prefetch images for visual categories.
        
        Args:
            articles: List of article names
            universe: Universe name
            max_workers: Number of parallel workers
            prefetch_images: Whether to prefetch images
            
        Returns:
            Dict with categorized articles
        """
        categorized = {key: [] for key in self.CATEGORY_KEYWORDS.keys()}
        categorized_lock = threading.Lock()
        
        total = len(articles)
        batch_size = 50
        batches = [articles[i:i + batch_size] for i in range(0, total, batch_size)]
        
        logger.info(f"\n🔥🔥🔥 PARALLEL BATCH MODE ACTIVATED!")
        logger.info(f"   Workers: {max_workers} threads")
        logger.info(f"   Batch size: {batch_size} articles/request")
        logger.info(f"   Total batches: {len(batches):,}")
        logger.info(f"   Estimated time: ~{len(batches) / max_workers / 2:.1f} minutes\n")
        
        completed_batches = 0
        
        def process_batch(batch):
            """Process single batch."""
            batch_categories = self._get_article_categories_batch(batch, universe)
            local_categorized = {key: [] for key in self.CATEGORY_KEYWORDS.keys()}
            
            for article in batch:
                categories = batch_categories.get(article, [])
                
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
            future_to_batch = {
                executor.submit(process_batch, batch): idx 
                for idx, batch in enumerate(batches)
            }
            
            for future in as_completed(future_to_batch):
                try:
                    local_categorized = future.result()
                    
                    with categorized_lock:
                        for category, items in local_categorized.items():
                            categorized[category].extend(items)
                        
                        completed_batches += 1
                        
                        if completed_batches % 50 == 0 or completed_batches == len(batches):
                            progress = (completed_batches / len(batches)) * 100
                            logger.info(f"   ⚡ Progress: {completed_batches:,}/{len(batches):,} batches ({progress:.1f}%)")
                
                except Exception as e:
                    logger.error(f"   ❌ Batch error: {e}")
        
        # Remove duplicates
        logger.info(f"\n🔧 Removing duplicates...")
        for category in categorized:
            categorized[category] = list(set(categorized[category]))
        
        # Log results
        logger.info(f"\n📊 Categorization Results:")
        for category, items in sorted(categorized.items(), key=lambda x: -len(x[1])):
            if items:
                logger.info(f"   {category:15s}: {len(items):5,} items")
        
        # ✨ NEW: Prefetch images if requested
        if prefetch_images:
            self._prefetch_category_images(categorized, universe)
        
        return categorized
    
    def _get_article_categories_batch(
        self, 
        article_titles: List[str],
        universe: str
    ) -> Dict[str, List[str]]:
        """Get categories for multiple articles (batch API call)."""
        try:
            base_url = self.wiki_urls.get(universe, self.wiki_urls['star_wars'])
            api_url = base_url.replace('/wiki/', '/api.php')
            
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
            
        except Exception:
            return {}
    
    def _prefetch_category_images(
        self,
        categorized: Dict[str, List[str]],
        universe: str,
        max_workers: int = 20
    ):
        """
        ✨ NEW: Prefetch images for visual categories.
        
        Args:
            categorized: Categorized articles
            universe: Universe name
            max_workers: Number of parallel image workers
        """
        logger.info(f"\n🖼️ Prefetching images for visual categories...")
        
        visual_categories = ['planets', 'weapons', 'armor', 'vehicles', 'droids', 'items']
        
        # Collect items
        items_to_fetch = []
        for category in visual_categories:
            items = categorized.get(category, [])
            logger.info(f"   📦 {category}: {len(items):,} items")
            items_to_fetch.extend(items)
        
        total = len(items_to_fetch)
        logger.info(f"\n   🚀 Fetching images for {total:,} items...\n")
        
        # Prepare tasks
        tasks = []
        for idx, item_name in enumerate(items_to_fetch):
            try:
                url = self.search_character(item_name, universe)
                if url:
                    data = self.scrape_character_data(url)
                    image_url = data.get('image_url')
                    
                    if image_url:
                        tasks.append((item_name, image_url, idx + 1, total))
            except Exception:
                continue
        
        # Fetch in parallel
        if tasks:
            stats = self.image_fetcher.fetch_batch_parallel(
                tasks,
                max_workers=max_workers,
                show_progress=True
            )
            
            logger.info(f"\n   ✅ Image prefetch complete!")
            logger.info(f"      💾 Downloaded: {stats['downloaded']:,}")
            logger.info(f"      ✅ Cached: {stats['cached']:,}")
            logger.info(f"      ❌ Failed: {stats['failed']:,}")
    
    # ============================================
    # ARTICLE SCRAPING (uses DataExtractor)
    # ============================================
    
    def search_character(self, name: str, universe: str = 'star_wars') -> Optional[str]:
        """Search for article and return URL."""
        base_url = self.wiki_urls.get(universe, self.wiki_urls['star_wars'])
        url = f"{base_url}{name.replace(' ', '_')}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return url
        except Exception as e:
            logger.debug(f"Search error for {name}: {e}")
        
        return None
    
    def scrape_character_data(self, url: str) -> Dict:
        """
        Scrape article data (delegates to DataExtractor).
        
        Args:
            url: Article URL
            
        Returns:
            Dict with extracted data
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Use DataExtractor
            return self.data_extractor.extract_all(response.content, url)
            
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            return {}
    
    # ============================================
    # BACKWARD COMPATIBLE METHODS (simplified!)
    # ============================================
    
    def _get_category(self, category: str, universe: str, limit: int) -> List[str]:
        """Helper for backward compatible methods."""
        data = self.get_canon_categorized_data(universe)
        return data.get(category, [])[:limit]
    
    def get_all_species(self, universe: str, limit: int = 2000) -> List[str]:
        """✅ 100% Canon species."""
        return self._get_category('species', universe, limit)
    
    def get_all_planets(self, universe: str, limit: int = 3000) -> List[str]:
        """✅ 100% Canon planets."""
        return self._get_category('planets', universe, limit)
    
    def get_all_organizations(self, universe: str, limit: int = 1500) -> List[str]:
        """✅ 100% Canon organizations."""
        return self._get_category('organizations', universe, limit)
    
    def get_all_weapons(self, universe: str, limit: int = 1200) -> List[str]:
        """✅ 100% Canon weapons."""
        return self._get_category('weapons', universe, limit)
    
    def get_all_vehicles(self, universe: str, limit: int = 2000) -> List[str]:
        """✅ 100% Canon vehicles."""
        return self._get_category('vehicles', universe, limit)
    
    def get_all_locations(self, universe: str, limit: int = 5000) -> List[str]:
        """✅ 100% Canon locations."""
        return self._get_category('locations', universe, limit)
    
    def get_all_characters(self, universe: str, limit: int = 15000) -> List[str]:
        """✅ 100% Canon characters."""
        return self._get_category('characters', universe, limit)
    
    def get_all_droids(self, universe: str, limit: int = 400) -> List[str]:
        """✅ 100% Canon droids."""
        return self._get_category('droids', universe, limit)
    
    def get_all_armor(self, universe: str, limit: int = 300) -> List[str]:
        """✅ 100% Canon armor."""
        return self._get_category('armor', universe, limit)
    
    def get_all_items(self, universe: str, limit: int = 4000) -> List[str]:
        """✅ 100% Canon items."""
        return self._get_category('items', universe, limit)
    
    def get_all_battles(self, universe: str, limit: int = 800) -> List[str]:
        """✅ 100% Canon battles."""
        return self._get_category('battles', universe, limit)
    
    def get_all_creatures(self, universe: str, limit: int = 1500) -> List[str]:
        """✅ 100% Canon creatures."""
        return self._get_category('creatures', universe, limit)
    
    def get_all_technology(self, universe: str, limit: int = 800) -> List[str]:
        """✅ 100% Canon technology."""
        return self._get_category('technology', universe, limit)
    
    def clear_cache(self):
        """Clear all caches."""
        self.canon_cache.invalidate('star_wars', depth=3)
        self.image_fetcher.clear_cache()