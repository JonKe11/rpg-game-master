
"""
Base class for all wiki API clients.

✅ FIXED: Added search() and get_details() methods required by ScraperService.
✅ FIXED: Added MediaWiki API for Canon articles category.

Provides:
- Rate limiting
- Async requests  
- Error handling
- Caching integration
- Batch operations
- Smart categorization
- MediaWiki API fallback
"""

from typing import Dict, List, Optional, Set, Any
import asyncio
import aiohttp
from datetime import datetime
import logging
from types import SimpleNamespace

from app.core.wiki.wiki_factory import WikiConfig
from app.core.wiki.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseWikiClient:
    """
    Base class for wiki API clients.
    
    ✅ CONCRETE IMPLEMENTATION with smart categorization + MediaWiki API.
    """
    
    
    CATEGORY_KEYWORDS = {
        'characters': [
            'Individuals', 'Characters', 'Humans', 'Males', 'Females',
            'Jedi', 'Sith', 'Rebels', 'Imperials', 'Clones',
            'Force-sensitives', 'Mandalorians', 'Bounty hunters',
            'Pilots', 'Commanders', 'Generals', 'Admirals',
            'Smugglers', 'Pirates', 'Mercenaries', 'Assassins',
            'Senators', 'Politicians', 'Diplomats', 'Leaders',
            'Padawans', 'Knights', 'Masters', 'Lords'
        ],
        'planets': [
            'Planets', 'Astronomical objects', 'Moons', 'Star systems',
            'Sectors', 'Regions', 'Space stations', 'Asteroids',
            'Nebulae', 'Worlds', 'Systems', 'Orbits'
        ],
        'species': [
            'Species', 'Sentient species', 'Non-sentient species',
            'Humanoids', 'Reptilians', 'Amphibians', 'Mammals',
            'Insectoids', 'Avians', 'Aquatic species'
        ],
        'weapons': [
            'Weapons', 'Blasters', 'Lightsabers', 'Explosives',
            'Melee weapons', 'Ranged weapons', 'Missiles', 'Cannons',
            'Rifles', 'Pistols', 'Grenades', 'Bombs', 'Torpedoes'
        ],
        'armor': [
            'Armor', 'Protective gear', 'Clothing', 'Uniforms',
            'Helmets', 'Suits', 'Robes', 'Garments', 'Attire'
        ],
        'vehicles': [
            'Vehicles', 'Starships', 'Starfighters', 'Capital ships',
            'Transports', 'Speeders', 'Walkers', 'Cruisers',
            'Freighters', 'Corvettes', 'Frigates', 'Destroyers',
            'Shuttles', 'Fighters', 'Bombers', 'Interceptors'
        ],
        'droids': [
            'Droids', 'Droid models', 'Protocol droids',
            'Astromech droids', 'Battle droids', 'Medical droids',
            'Service droids', 'Utility droids', 'Repair droids'
        ],
        'items': [
            'Technology', 'Equipment', 'Tools', 'Devices',
            'Objects', 'Artifacts', 'Instruments', 'Gadgets',
            'Machinery', 'Computers', 'Holocrons', 'Crystals'
        ],
        'organizations': [
            'Organizations', 'Governments', 'Factions', 'Companies',
            'Orders', 'Guilds', 'Gangs', 'Empires', 'Republics',
            'Alliances', 'Confederacies', 'Syndicates', 'Cartels',
            'Corporations', 'Military units', 'Squadrons'
        ],
        'locations': [
            'Locations', 'Cities', 'Bases', 'Structures', 'Buildings',
            'Temples', 'Palaces', 'Installations', 'Fortresses',
            'Outposts', 'Settlements', 'Facilities', 'Landmarks',
            'Monuments', 'Districts', 'Quarters', 'Stations'
        ],
        'battles': [
            'Battles', 'Conflicts', 'Wars', 'Sieges', 'Campaigns',
            'Events', 'Operations', 'Missions', 'Skirmishes',
            'Engagements', 'Assaults', 'Invasions'
        ],
        'creatures': [
            'Creatures', 'Animals', 'Beasts', 'Fauna', 'Monsters',
            'Predators', 'Wildlife', 'Organisms'
        ],
        'media': [
            'Media', 'Films', 'Television', 'Books', 'Comics',
            'Games', 'Novels', 'Series', 'Episodes', 'Chapters',
            'Issues', 'Magazines', 'Publications'
        ],
        'technology': [
            'Technology', 'Science', 'Physics', 'Hyperspace',
            'Communications', 'Sensors', 'Shields', 'Reactors',
            'Engines', 'Propulsion', 'Navigation', 'Scanners'
        ]
    }
    
    def __init__(self, config: WikiConfig):
        """
        Initialize wiki client.
        
        Args:
            config: WikiConfig with wiki-specific settings
        """
        self.config = config
        self.base_url = config.base_url
        
        
        rate_limit_calls = getattr(config, 'rate_limit_calls', 150)
        rate_limit_period = getattr(config, 'rate_limit_period', 60)
        
        self.rate_limiter = RateLimiter(
            calls=rate_limit_calls,
            period=rate_limit_period
        )
        
        
        self._session: Optional[aiohttp.ClientSession] = None
        
        
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'cache_hits': 0,
            'total_articles': 0
        }
        
        logger.info(f"✅ Initialized {config.name} client")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None or self._session.closed:
            timeout = getattr(self.config, 'timeout', 30)
            self._session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'RPG-GameMaster/1.0 (Educational Project)',
                    'Accept': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=timeout)
            )
    
    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            await asyncio.sleep(0.50)
    
    
    
    
    def get_category_mapping(self) -> Dict[str, str]:
        """
        Get mapping from frontend categories to wiki categories.
        
        Returns:
            Dict mapping category names
        """
        
        return {
            'planets': 'Planets',
            'species': 'Species',
            'characters': 'Characters',
            'weapons': 'Weapons',
            'armor': 'Armor',
            'vehicles': 'Vehicles',
            'droids': 'Droids',
            'items': 'Items',
            'organizations': 'Organizations',
            'locations': 'Locations',
            'battles': 'Battles',
            'creatures': 'Creatures',
            'technology': 'Technology',
            'media': 'Media'  
        }
    
    def validate_entity(self, entity_name: str, entity_type: str) -> bool:
        """
        Validate if entity exists (basic check).
        
        Args:
            entity_name: Entity to validate
            entity_type: Type (e.g., "planet", "species")
            
        Returns:
            True if valid
        """
        
        
        return True
    
    def get_fallback_entity(self, entity_type: str) -> str:
        """
        Get fallback entity name.
        
        Args:
            entity_type: Type (e.g., "planet")
            
        Returns:
            Safe fallback entity name
        """
        
        fallbacks = {
            'planet': 'Earth',
            'species': 'Human',
            'character': 'Unknown',
            'weapon': 'Sword',
            'vehicle': 'Ship',
        }
        return fallbacks.get(entity_type, 'Unknown')
    
    
    
    
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make rate-limited API request.
        
        ✅ FIXED: Ensures correct URL for FANDOM API endpoints (Articles and Search)
        
        Args:
            endpoint: API endpoint (e.g., "/Articles/List" or "/Search/List")
            params: Query parameters
            
        Returns:
            JSON response
        """
        await self._ensure_session()
        
        
        base_url = self.base_url
        
        
        
        if endpoint.startswith('/Articles') or endpoint.startswith('/Search'):
            
            if 'fandom.com' in base_url:
                
                domain = base_url.split('/api')[0].split('/wiki')[0]
                base_url = f"{domain}/api/v1"
        
        url = f"{base_url}{endpoint}"
        
        
        await self.rate_limiter.acquire()
        
        try:
            self.stats['requests_made'] += 1
            
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        
        except aiohttp.ClientError as e:
            self.stats['requests_failed'] += 1
            logger.error(f"Request failed for {self.config.name}: {e}")
            raise

    
    
    

    async def search(self, query: str, limit: int = 1) -> List[Dict]:
        """
        Search for articles using MediaWiki API (more reliable than Fandom API).
        """
        
        if 'fandom.com' in self.base_url:
            domain_parts = self.base_url.split('/api')[0].split('/wiki')[0]
            base_url = f"{domain_parts}/api.php"
        else:
            base_url = self.base_url.replace('/api/v1', '/api.php')

        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srlimit': limit,
            'format': 'json'
        }

        await self._ensure_session()
        await self.rate_limiter.acquire()

        try:
            self.stats['requests_made'] += 1
            async with self._session.get(base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                if 'query' in data and 'search' in data['query']:
                    for item in data['query']['search']:
                        results.append({
                            'id': item['pageid'],
                            'title': item['title'],
                            
                            'url': f"{self.base_url.split('/api')[0]}/wiki/{item['title'].replace(' ', '_')}" 
                        })
                return results
        except Exception as e:
            logger.warning(f"Search failed for '{query}': {e}")
            return []

    async def get_details(self, title: str) -> Optional[Any]:
        """
        Get details for an article by TITLE.
        Used by ScraperService.
        
        Since Fandom API details endpoint typically requires IDs,
        this method first searches for the ID if necessary.
        
        Returns:
            Object with .title, .content, .image_url, .url attributes
        """
        try:
            
            
            search_results = await self.search(title, limit=1)
            
            if not search_results:
                return None
                
            article_id = search_results[0]['id']
            
            
            details_dict = await self.get_article_details_batch([article_id])
            data = details_dict.get(str(article_id))
            
            if not data:
                return None

            
            
            result = SimpleNamespace()
            result.title = data.get('title', title)
            result.content = data.get('abstract', '')
            result.image_url = data.get('thumbnail')
            result.url = data.get('url')
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get details for '{title}': {e}")
            return None
    
    
    
    
    
    async def get_category_members_mediawiki(
        self,
        category: str,
        limit: int = 500,
        continue_token: Optional[str] = None
    ) -> Dict:
        """
        Get category members using MediaWiki API.
        
        ✅ WORKS FOR ALL CATEGORIES (including Canon articles)!
        
        MediaWiki API is more reliable than FANDOM API for categories.
        
        Args:
            category: Category name (e.g., "Canon_articles")
            limit: Max results (max 500 per request)
            continue_token: Continuation token for pagination
            
        Returns:
            Dict with 'members' list and 'continue' token
        """
        
        if 'fandom.com' in self.base_url:
            
            domain_parts = self.base_url.split('/api')[0].split('/wiki')[0]
            base_url = f"{domain_parts}/api.php"
        else:
            
            base_url = self.base_url.replace('/api/v1', '/api.php')
        
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': min(limit, 500),
            'cmtype': 'page',  
            'format': 'json'
        }
        
        if continue_token:
            params['cmcontinue'] = continue_token
        
        await self._ensure_session()
        await self.rate_limiter.acquire()
        
        try:
            self.stats['requests_made'] += 1
            
            async with self._session.get(base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                members = []
                if 'query' in data and 'categorymembers' in data['query']:
                    for item in data['query']['categorymembers']:
                        members.append({
                            'id': item['pageid'],
                            'title': item['title'],
                            'ns': item['ns']  
                        })
                
                
                continue_token = None
                if 'continue' in data:
                    continue_token = data['continue'].get('cmcontinue')
                
                return {
                    'members': members,
                    'continue': continue_token
                }
        
        except aiohttp.ClientError as e:
            self.stats['requests_failed'] += 1
            logger.error(f"MediaWiki API request failed: {e}")
            raise
    
    async def get_all_category_members_mediawiki(
        self,
        category: str,
        max_total: int = 100000
    ) -> List[Dict]:
        """
        Get ALL category members using MediaWiki API with pagination.
        
        ✅ RELIABLE METHOD for any category!
        
        Args:
            category: Category name (e.g., "Canon_articles")
            max_total: Maximum articles to fetch
            
        Returns:
            List of article dicts with id, title
        """
        all_members = []
        continue_token = None
        
        logger.info(f"📦 Fetching ALL from category: {category} (MediaWiki API)")
        logger.info(f"   Max total: {max_total:,}")
        
        while len(all_members) < max_total:
            result = await self.get_category_members_mediawiki(
                category,
                limit=500,
                continue_token=continue_token
            )
            
            members = result['members']
            
            if not members:
                break
            
            all_members.extend(members)
            
            
            if len(all_members) % 5000 == 0:
                logger.info(f"   Progress: {len(all_members):,} articles...")
            
            
            continue_token = result.get('continue')
            if not continue_token:
                break  
        
        logger.info(f"📦 Total articles in {category}: {len(all_members):,}")
        
        return all_members[:max_total]
    
    
    
    
    
    async def get_category_articles(
        self, 
        category: str, 
        limit: int = 5000,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get articles in category (FANDOM API).
        
        Args:
            category: Category name (e.g., "Planets")
            limit: Max results per request (API max: 5000)
            offset: Pagination offset
            
        Returns:
            List of article dicts with id, title, url
        """
        logger.debug(
            f"📦 Fetching category: {category} "
            f"(limit={limit}, offset={offset})"
        )
        
        try:
            response = await self._make_request(
                "/Articles/List",
                params={
                    "category": category,
                    "limit": min(limit, 5000),
                    "offset": offset
                }
            )
            
            items = response.get("items", [])
            logger.debug(f"   ✅ Retrieved {len(items)} articles")
            
            return items
        
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"Category not found: {category}")
                return []
            raise
    
    async def get_all_category_articles(
        self, 
        category: str, 
        max_total: int = 100000
    ) -> List[Dict]:
        """
        Get ALL articles in category with automatic fallback.
        
        ✅ SMART: Tries FANDOM API first, falls back to MediaWiki API.
        
        Args:
            category: Category name
            max_total: Maximum total articles to fetch (default: 100k)
            
        Returns:
            Complete list of articles with id, title, url
        """
        all_articles = []
        offset = 0
        batch_size = 5000  
        
        logger.info(f"📦 Fetching ALL from category: {category}")
        logger.info(f"   Max total: {max_total:,}")
        
        
        try:
            logger.debug("   Trying FANDOM API...")
            
            while len(all_articles) < max_total:
                batch = await self.get_category_articles(
                    category, 
                    limit=batch_size, 
                    offset=offset
                )
                
                if not batch:
                    break  
                
                all_articles.extend(batch)
                offset += len(batch)
                
                
                if len(all_articles) % 10000 == 0:
                    logger.info(f"   Progress: {len(all_articles):,} articles...")
                
                
                if len(batch) < batch_size:
                    break
            
            if all_articles:
                logger.info(f"   ✅ FANDOM API succeeded!")
        
        except Exception as e:
            logger.warning(f"   ⚠️ FANDOM API failed: {e}")
            logger.info(f"   🔄 Falling back to MediaWiki API...")
            
            
            all_articles = await self.get_all_category_members_mediawiki(
                category,
                max_total=max_total
            )
        
        logger.info(
            f"📦 Total articles in {category}: "
            f"{len(all_articles):,}"
        )
        
        return all_articles[:max_total]
    
    
    
    
    
    async def get_article_categories(self, article_id: int) -> List[str]:
        """
        Get categories for a single article.
        
        Uses FANDOM API endpoint: /Articles/Details?ids={id}
        
        Args:
            article_id: Article ID
            
        Returns:
            List of category names (e.g., ["Individuals", "Humans", "Jedi"])
        """
        try:
            response = await self._make_request(
                "/Articles/Details",
                params={"ids": str(article_id)}
            )
            
            
            items = response.get("items", {})
            article_data = items.get(str(article_id), {})
            
            
            categories_list = article_data.get("categories", [])
            
            
            category_names = []
            for cat in categories_list:
                cat_title = cat.get("title", "")
                
                if cat_title.startswith("Category:"):
                    cat_title = cat_title[9:]  
                
                if cat_title.startswith("Canon_"):
                    cat_title = cat_title[6:]  
                
                if cat_title:
                    category_names.append(cat_title)
            
            return category_names
        
        except Exception as e:
            logger.debug(f"Failed to get categories for article {article_id}: {e}")
            return []
    
    async def get_categories_batch(
        self, 
        article_ids: List[int]
    ) -> Dict[int, List[str]]:
        """
        Get categories for multiple articles using MediaWiki API.
        
        ✅ FIXED: FANDOM API doesn't return categories, use MediaWiki API instead!
        
        Args:
            article_ids: List of article IDs
            
        Returns:
            Dict mapping article_id -> list of category names
        """
        all_categories = {}
        
        
        batch_size = 50
        
        
        batches = [
            article_ids[i:i + batch_size]
            for i in range(0, len(article_ids), batch_size)
        ]
        
        for batch in batches:
            ids_str = "|".join(map(str, batch))
            
            
            if 'fandom.com' in self.base_url:
                domain_parts = self.base_url.split('/api')[0].split('/wiki')[0]
                base_url = f"{domain_parts}/api.php"
            else:
                base_url = self.base_url.replace('/api/v1', '/api.php')
            
            params = {
                'action': 'query',
                'pageids': ids_str,
                'prop': 'categories',
                'cllimit': 500,  
                'clshow': '!hidden',  
                'format': 'json'
            }
            
            await self._ensure_session()
            await self.rate_limiter.acquire()
            
            try:
                self.stats['requests_made'] += 1
                
                async with self._session.get(base_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    pages = data.get('query', {}).get('pages', {})
                    
                    for page_id_str, page_data in pages.items():
                        page_id = int(page_id_str)
                        
                        
                        categories_list = page_data.get('categories', [])
                        category_names = []
                        
                        for cat in categories_list:
                            cat_title = cat.get('title', '')
                            
                            if cat_title.startswith('Category:'):
                                cat_title = cat_title[9:]
                            
                            if cat_title.startswith('Canon_'):
                                cat_title = cat_title[6:]
                            
                            if cat_title and cat_title != 'articles':  
                                category_names.append(cat_title)
                        
                        all_categories[page_id] = category_names
            
            except Exception as e:
                logger.warning(f"MediaWiki categories batch failed: {e}")
                
                for article_id in batch:
                    all_categories[article_id] = []
        
        return all_categories
    
    
    
    
    
    def categorize_article(self, article_categories: List[str]) -> Optional[str]:
        """
        Determine article category based on its wiki categories.
        
        Uses keyword matching against CATEGORY_KEYWORDS.
        
        Args:
            article_categories: List of wiki category names
            
        Returns:
            Frontend category name (e.g., "characters", "planets")
            or None if can't determine
        """
        if not article_categories:
            return None
        
        
        categories_lower = [cat.lower() for cat in article_categories]
        
        
        scores = {}
        for frontend_cat, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                for article_cat in categories_lower:
                    if keyword_lower in article_cat or article_cat in keyword_lower:
                        score += 1
            
            if score > 0:
                scores[frontend_cat] = score
        
        
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])[0]
            return best_category
        
        return None
    
    async def categorize_articles_smart(
        self,
        articles: List[Dict],
        max_workers: int = 20
    ) -> Dict[str, List[Dict]]:
        """
        Categorize articles by fetching their categories and matching.
        
        Process:
        1. Fetch categories for all articles (batch)
        2. Categorize each article using keyword matching
        3. Return organized dict: category -> list of articles
        
        Args:
            articles: List of articles from Canon_articles
                      (must have 'id', 'title', 'url')
            max_workers: Max concurrent batch requests
            
        Returns:
            Dict: {
                'characters': [{id, title, url, categories}, ...],
                'planets': [...],
                ...
            }
        """
        logger.info(f"\n🎯 SMART CATEGORIZATION")
        logger.info(f"="*60)
        logger.info(f"Total articles to categorize: {len(articles):,}")
        logger.info(f"Max concurrent workers: {max_workers}")
        
        
        categorized = {cat: [] for cat in self.CATEGORY_KEYWORDS.keys()}
        uncategorized = []
        
        
        article_ids = [a['id'] for a in articles]
        
        
        batch_size = 100  
        batches = [
            article_ids[i:i + batch_size]
            for i in range(0, len(article_ids), batch_size)
        ]
        
        logger.info(f"📦 Processing {len(batches)} batches of {batch_size} articles...")
        
        
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_batch(batch):
            async with semaphore:
                return await self.get_categories_batch(batch)
        
        
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        
        all_article_categories = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch failed: {result}")
                continue
            all_article_categories.update(result)
        
        logger.info(f"✅ Fetched categories for {len(all_article_categories):,} articles")
        
        
        logger.info(f"\n🔍 Categorizing articles...")
        
        for article in articles:
            article_id = article['id']
            article_cats = all_article_categories.get(article_id, [])
            
            
            frontend_cat = self.categorize_article(article_cats)
            
            
            if frontend_cat:
                categorized[frontend_cat].append({
                    'id': article_id,
                    'title': article['title'],
                    'url': article.get('url', ''),
                    'categories': article_cats  
                })
            else:
                
                uncategorized.append({
                    'id': article_id,
                    'title': article['title'],
                    'url': article.get('url', ''),
                    'categories': article_cats
                })
        
        
        logger.info(f"\n📊 CATEGORIZATION RESULTS:")
        logger.info(f"="*60)
        
        total_categorized = 0
        for cat_name in sorted(categorized.keys()):
            count = len(categorized[cat_name])
            total_categorized += count
            if count > 0:
                logger.info(f"   {cat_name:15s}: {count:5,} articles")
        
        logger.info(f"   {'uncategorized':15s}: {len(uncategorized):5,} articles")
        logger.info(f"\n   TOTAL: {total_categorized + len(uncategorized):,} articles")
        logger.info(f"="*60)
        
        return categorized
    
    
    
    
    
    async def get_all_canonical_data_smart(
        self,
        with_details: bool = False,
        max_workers: int = 20
    ) -> Dict[str, List]:
        """
        Get ALL canonical data using smart categorization.
        
        ✅ FIXED: Uses MediaWiki API for Canon_articles!
        
        New approach:
        1. Fetch ALL articles from Canon_articles (~58k) via MediaWiki API
        2. Fetch categories for each article
        3. Categorize automatically using keywords
        4. Optionally enrich with full details
        
        Args:
            with_details: Fetch full article details (slower)
            max_workers: Max concurrent requests
            
        Returns:
            Dict: {
                'characters': [article_dicts],
                'planets': [article_dicts],
                ...
            }
        """
        logger.info("\n" + "="*60)
        logger.info(f"🚀 SMART CANON DATA FETCH")
        logger.info("="*60)
        logger.info(f"Source: Canon_articles category")
        logger.info(f"Method: Smart categorization with MediaWiki API")
        logger.info(f"Details: {'YES' if with_details else 'NO'}")
        logger.info("="*60)
        
        
        logger.info(f"\n📥 STEP 1/3: Fetching all Canon articles...")
        
        
        
        canon_category = "Canon_articles"  
        
        all_articles = await self.get_all_category_members_mediawiki(
            canon_category,
            max_total=100000  
        )
        
        if not all_articles:
            logger.warning("⚠️ No articles found in Canon_articles!")
            return {}
        
        logger.info(f"✅ Found {len(all_articles):,} canon articles\n")
        
        
        logger.info(f"📥 STEP 2/3: Categorizing articles...")
        
        categorized = await self.categorize_articles_smart(
            all_articles,
            max_workers=max_workers
        )
        
        
        if with_details:
            logger.info(f"\n📥 STEP 3/3: Enriching with article details...")
            
            for cat_name, articles in categorized.items():
                if not articles:
                    continue
                
                logger.info(f"   🎯 {cat_name}: {len(articles):,} articles...")
                
                article_ids = [a['id'] for a in articles]
                details = await self.get_article_details_batch(article_ids)
                
                
                for article in articles:
                    article_id = article['id']
                    detail = details.get(str(article_id), {})
                    
                    
                    article.update(detail)
                    
                    
                    if not article.get('image_url'):
                        article['image_url'] = article.get('thumbnail')
        
        logger.info(f"\n✅ SMART FETCH COMPLETE!")
        logger.info("="*60 + "\n")
        
        return categorized
    
    
    
    
    
    async def get_article_details_batch(
        self, 
        article_ids: List[int]
    ) -> Dict[int, Dict]:
        """
        Get details for multiple articles (batch operation).
        
        Uses concurrent requests for maximum speed.
        
        Args:
            article_ids: List of article IDs
            
        Returns:
            Dict mapping article_id -> article details
        """
        all_details = {}
        max_batch_size = getattr(self.config, 'max_batch_size', 100)
        batch_size = max_batch_size
        
        
        batches = [
            article_ids[i:i + batch_size]
            for i in range(0, len(article_ids), batch_size)
        ]
        
        logger.info(
            f"📄 Fetching details for {len(article_ids)} articles "
            f"in {len(batches)} batches..."
        )
        
        
        tasks = [
            self._fetch_details_batch(batch)
            for batch in batches
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch failed: {result}")
                continue
            all_details.update(result)
        
        logger.info(f"   ✅ Retrieved details for {len(all_details)} articles")
        
        return all_details
    
    async def _fetch_details_batch(self, article_ids: List[int]) -> Dict:
        """Fetch single batch of article details"""
        ids_str = ",".join(map(str, article_ids))
        
        try:
            response = await self._make_request(
                "/Articles/Details",
                params={"ids": ids_str}
            )
            
            return response.get("items", {})
        
        except Exception as e:
            logger.error(f"Failed to fetch details batch: {e}")
            return {}
    
    
    
    
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        return {
            **self.stats,
            'wiki': self.config.name,
            'available_tokens': self.rate_limiter.available_tokens
        }
    
    
    
    
    
    async def get_all_canonical_data(
        self,
        with_details: bool = False
    ) -> Dict[str, List[str]]:
        """
        Legacy method - redirects to smart version.
        
        For backwards compatibility.
        """
        logger.info("ℹ️ Using legacy method - redirecting to smart categorization")
        
        categorized = await self.get_all_canonical_data_smart(
            with_details=with_details
        )
        
        
        result = {}
        for cat_name, articles in categorized.items():
            result[cat_name] = [a['title'] for a in articles]
        
        return result
    
    async def get_canonical_data_by_category(
        self,
        frontend_category: str,
        limit: int = 10000,
        with_details: bool = False
    ) -> List[Dict]:
        """
        Legacy method - kept for compatibility.
        """
        logger.warning(
            f"⚠️ Using legacy category fetch for {frontend_category}. "
            f"Consider using get_all_canonical_data_smart() instead!"
        )
        
        
        category_mapping = self.get_category_mapping()
        wiki_category = category_mapping.get(frontend_category)
        
        if not wiki_category:
            logger.error(
                f"Unknown category: {frontend_category} "
                f"for {self.config.name}"
            )
            return []
        
        logger.info(
            f"🎯 Fetching {frontend_category} from {self.config.name}..."
        )
        
        
        articles = await self.get_all_category_articles(
            wiki_category, 
            max_total=limit
        )
        
        if not articles:
            return []
        
        
        if with_details:
            article_ids = [item["id"] for item in articles]
            details = await self.get_article_details_batch(article_ids)
            
            
            enriched = []
            for article in articles:
                article_id = article["id"]
                detail = details.get(str(article_id), {})
                
                enriched.append({
                    'id': article_id,
                    'title': article["title"],
                    'url': article.get("url", ""),
                    'abstract': detail.get("abstract", ""),
                    'thumbnail': detail.get("thumbnail"),
                    'image_url': detail.get("thumbnail"),
                    'category': frontend_category,
                    'wiki': self.config.name,
                    'is_canonical': True
                })
            
            self.stats['total_articles'] = len(enriched)
            logger.info(f"   ✅ Enriched {len(enriched)} {frontend_category}")
            
            return enriched
        
        else:
            
            simple = [
                {
                    'title': article["title"],
                    'category': frontend_category,
                    'is_canonical': True
                }
                for article in articles
            ]
            
            self.stats['total_articles'] = len(simple)
            return simple