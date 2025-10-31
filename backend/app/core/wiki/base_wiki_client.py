# backend/app/core/wiki/base_wiki_client.py
"""
Base class for all wiki API clients.

✅ FIXED: Added MediaWiki API for Canon articles category
- FANDOM API doesn't support "Canon articles" category
- MediaWiki API works for all categories
- Automatic fallback between APIs

Provides:
- Rate limiting
- Async requests  
- Error handling
- Caching integration
- Batch operations
- Smart categorization
- MediaWiki API fallback
"""

from typing import Dict, List, Optional, Set
import asyncio
import aiohttp
from datetime import datetime
import logging

from app.core.wiki.wiki_factory import WikiConfig
from app.core.wiki.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseWikiClient:
    """
    Base class for wiki API clients.
    
    ✅ CONCRETE IMPLEMENTATION with smart categorization + MediaWiki API.
    """
    
    # ✅ Category keywords for automatic classification (EXPANDED!)
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
        
        # Rate limiter (default values if not in config)
        rate_limit_calls = getattr(config, 'rate_limit_calls', 150)
        rate_limit_period = getattr(config, 'rate_limit_period', 60)
        
        self.rate_limiter = RateLimiter(
            calls=rate_limit_calls,
            period=rate_limit_period
        )
        
        # Session (reuse for connection pooling)
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Stats
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
    
    # ============================================
    # CONCRETE METHODS
    # ============================================
    
    def get_category_mapping(self) -> Dict[str, str]:
        """
        Get mapping from frontend categories to wiki categories.
        
        Returns:
            Dict mapping category names
        """
        # Default mapping (can be overridden in subclasses)
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
            'media': 'Media'  # ✅ NEW
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
        # Default: assume valid
        # Subclasses can override for stricter validation
        return True
    
    def get_fallback_entity(self, entity_type: str) -> str:
        """
        Get fallback entity name.
        
        Args:
            entity_type: Type (e.g., "planet")
            
        Returns:
            Safe fallback entity name
        """
        # Default fallbacks
        fallbacks = {
            'planet': 'Earth',
            'species': 'Human',
            'character': 'Unknown',
            'weapon': 'Sword',
            'vehicle': 'Ship',
        }
        return fallbacks.get(entity_type, 'Unknown')
    
    # ============================================
    # CORE API METHODS
    # ============================================
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make rate-limited API request.
        
        ✅ FIXED: Ensures correct URL for FANDOM API endpoints
        
        Args:
            endpoint: API endpoint (e.g., "/Articles/List")
            params: Query parameters
            
        Returns:
            JSON response
        """
        await self._ensure_session()
        
        # ✅ FIX: Determine correct base URL based on endpoint
        base_url = self.base_url
        
        # FANDOM API endpoints need /api/v1, not /wiki
        if endpoint.startswith('/Articles'):
            # This is a FANDOM API endpoint
            if 'fandom.com' in base_url:
                # Extract domain and add /api/v1
                domain = base_url.split('/api')[0].split('/wiki')[0]
                base_url = f"{domain}/api/v1"
        
        url = f"{base_url}{endpoint}"
        
        # Rate limiting
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
    
    # ============================================
    # ✅ NEW: MEDIAWIKI API METHODS
    # ============================================
    
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
        # ✅ FIX: Construct MediaWiki API URL properly
        if 'fandom.com' in self.base_url:
            # For FANDOM wikis: https://WIKI.fandom.com/api.php
            domain_parts = self.base_url.split('/api')[0].split('/wiki')[0]
            base_url = f"{domain_parts}/api.php"
        else:
            # Generic fallback
            base_url = self.base_url.replace('/api/v1', '/api.php')
        
        logger.debug(f"MediaWiki API URL: {base_url}")
        
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': min(limit, 500),
            'cmtype': 'page',  # Only pages, not subcategories
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
                            'ns': item['ns']  # namespace
                        })
                
                # Get continuation token
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
            
            # Progress log
            if len(all_members) % 5000 == 0:
                logger.info(f"   Progress: {len(all_members):,} articles...")
            
            # Check for continuation
            continue_token = result.get('continue')
            if not continue_token:
                break  # No more pages
        
        logger.info(f"📦 Total articles in {category}: {len(all_members):,}")
        
        return all_members[:max_total]
    
    # ============================================
    # CATEGORY OPERATIONS (FANDOM API with fallback)
    # ============================================
    
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
        batch_size = 5000  # API max per request
        
        logger.info(f"📦 Fetching ALL from category: {category}")
        logger.info(f"   Max total: {max_total:,}")
        
        # Try FANDOM API first
        try:
            logger.debug("   Trying FANDOM API...")
            
            while len(all_articles) < max_total:
                batch = await self.get_category_articles(
                    category, 
                    limit=batch_size, 
                    offset=offset
                )
                
                if not batch:
                    break  # No more articles
                
                all_articles.extend(batch)
                offset += len(batch)
                
                # Progress log every 10k
                if len(all_articles) % 10000 == 0:
                    logger.info(f"   Progress: {len(all_articles):,} articles...")
                
                # Check if we got less than requested (last page)
                if len(batch) < batch_size:
                    break
            
            if all_articles:
                logger.info(f"   ✅ FANDOM API succeeded!")
        
        except Exception as e:
            logger.warning(f"   ⚠️ FANDOM API failed: {e}")
            logger.info(f"   🔄 Falling back to MediaWiki API...")
            
            # ✅ FALLBACK: Use MediaWiki API
            all_articles = await self.get_all_category_members_mediawiki(
                category,
                max_total=max_total
            )
        
        logger.info(
            f"📦 Total articles in {category}: "
            f"{len(all_articles):,}"
        )
        
        return all_articles[:max_total]
    
    # ============================================
    # ARTICLE CATEGORIES FETCHING
    # ============================================
    
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
            
            # Response structure: {"items": {article_id: {... categories: [...]}}}
            items = response.get("items", {})
            article_data = items.get(str(article_id), {})
            
            # Extract category names
            categories_list = article_data.get("categories", [])
            
            # Categories come as list of dicts: [{"title": "Category:Individuals"}, ...]
            category_names = []
            for cat in categories_list:
                cat_title = cat.get("title", "")
                # Remove "Category:" prefix
                if cat_title.startswith("Category:"):
                    cat_title = cat_title[9:]  # Remove "Category:"
                # Remove "Canon_" prefix if present
                if cat_title.startswith("Canon_"):
                    cat_title = cat_title[6:]  # Remove "Canon_"
                
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
        
        # MediaWiki API supports max 50 pages per request
        batch_size = 50
        
        # Split into smaller batches
        batches = [
            article_ids[i:i + batch_size]
            for i in range(0, len(article_ids), batch_size)
        ]
        
        for batch in batches:
            ids_str = "|".join(map(str, batch))
            
            # MediaWiki API URL
            if 'fandom.com' in self.base_url:
                domain_parts = self.base_url.split('/api')[0].split('/wiki')[0]
                base_url = f"{domain_parts}/api.php"
            else:
                base_url = self.base_url.replace('/api/v1', '/api.php')
            
            params = {
                'action': 'query',
                'pageids': ids_str,
                'prop': 'categories',
                'cllimit': 500,  # Max categories per page
                'clshow': '!hidden',  # Exclude hidden categories
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
                        
                        # Extract categories
                        categories_list = page_data.get('categories', [])
                        category_names = []
                        
                        for cat in categories_list:
                            cat_title = cat.get('title', '')
                            # Remove "Category:" prefix
                            if cat_title.startswith('Category:'):
                                cat_title = cat_title[9:]
                            # Remove "Canon_" prefix if present
                            if cat_title.startswith('Canon_'):
                                cat_title = cat_title[6:]
                            
                            if cat_title and cat_title != 'articles':  # Skip "Canon articles"
                                category_names.append(cat_title)
                        
                        all_categories[page_id] = category_names
            
            except Exception as e:
                logger.warning(f"MediaWiki categories batch failed: {e}")
                # Fill with empty lists
                for article_id in batch:
                    all_categories[article_id] = []
        
        return all_categories
    
    # ============================================
    # SMART CATEGORIZATION
    # ============================================
    
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
        
        # Convert to lowercase for matching
        categories_lower = [cat.lower() for cat in article_categories]
        
        # Score each frontend category
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
        
        # Return category with highest score
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
        
        ✅ MAIN NEW METHOD: This replaces the old category-specific fetching!
        
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
        
        # Initialize result buckets
        categorized = {cat: [] for cat in self.CATEGORY_KEYWORDS.keys()}
        uncategorized = []
        
        # Extract article IDs
        article_ids = [a['id'] for a in articles]
        
        # Split into batches for concurrent processing
        batch_size = 100  # API limit
        batches = [
            article_ids[i:i + batch_size]
            for i in range(0, len(article_ids), batch_size)
        ]
        
        logger.info(f"📦 Processing {len(batches)} batches of {batch_size} articles...")
        
        # Process batches with concurrency limit
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_batch(batch):
            async with semaphore:
                return await self.get_categories_batch(batch)
        
        # Execute all batches
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge all categories
        all_article_categories = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch failed: {result}")
                continue
            all_article_categories.update(result)
        
        logger.info(f"✅ Fetched categories for {len(all_article_categories):,} articles")
        
        # Now categorize each article
        logger.info(f"\n🔍 Categorizing articles...")
        
        for article in articles:
            article_id = article['id']
            article_cats = all_article_categories.get(article_id, [])
            
            # Determine category
            frontend_cat = self.categorize_article(article_cats)
            
            # Add to appropriate bucket
            if frontend_cat:
                categorized[frontend_cat].append({
                    'id': article_id,
                    'title': article['title'],
                    'url': article.get('url', ''),
                    'categories': article_cats  # Keep original categories
                })
            else:
                # Couldn't categorize
                uncategorized.append({
                    'id': article_id,
                    'title': article['title'],
                    'url': article.get('url', ''),
                    'categories': article_cats
                })
        
        # Log results
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
    
    # ============================================
    # ✅ MAIN ENTRY POINT (FIXED)
    # ============================================
    
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
        
        # Step 1: Get ALL articles from Canon_articles
        logger.info(f"\n📥 STEP 1/3: Fetching all Canon articles...")
        
        # ✅ FIX: Use MediaWiki API directly for Canon_articles!
        # This category doesn't work with FANDOM /Articles/List endpoint
        canon_category = "Canon_articles"  # Use underscore for MediaWiki API
        
        all_articles = await self.get_all_category_members_mediawiki(
            canon_category,
            max_total=100000  # Up to 100k
        )
        
        if not all_articles:
            logger.warning("⚠️ No articles found in Canon_articles!")
            return {}
        
        logger.info(f"✅ Found {len(all_articles):,} canon articles\n")
        
        # Step 2: Categorize articles
        logger.info(f"📥 STEP 2/3: Categorizing articles...")
        
        categorized = await self.categorize_articles_smart(
            all_articles,
            max_workers=max_workers
        )
        
        # Step 3: Optionally enrich with details
        if with_details:
            logger.info(f"\n📥 STEP 3/3: Enriching with article details...")
            
            for cat_name, articles in categorized.items():
                if not articles:
                    continue
                
                logger.info(f"   🎯 {cat_name}: {len(articles):,} articles...")
                
                article_ids = [a['id'] for a in articles]
                details = await self.get_article_details_batch(article_ids)
                
                # Enrich
                for article in articles:
                    article_id = article['id']
                    detail = details.get(str(article_id), {})
                    
                    article['abstract'] = detail.get('abstract', '')
                    article['thumbnail'] = detail.get('thumbnail')
                    article['image_url'] = detail.get('thumbnail')
        
        logger.info(f"\n✅ SMART FETCH COMPLETE!")
        logger.info("="*60 + "\n")
        
        return categorized
    
    # ============================================
    # BATCH OPERATIONS (Kept from original)
    # ============================================
    
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
        
        # Split into batches
        batches = [
            article_ids[i:i + batch_size]
            for i in range(0, len(article_ids), batch_size)
        ]
        
        logger.info(
            f"📄 Fetching details for {len(article_ids)} articles "
            f"in {len(batches)} batches..."
        )
        
        # Process batches concurrently
        tasks = [
            self._fetch_details_batch(batch)
            for batch in batches
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
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
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        return {
            **self.stats,
            'wiki': self.config.name,
            'available_tokens': self.rate_limiter.available_tokens
        }
    
    # ============================================
    # LEGACY COMPATIBILITY (old methods still work)
    # ============================================
    
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
        
        # Convert to old format (just titles)
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
        
        Note: Smart categorization is now preferred!
        """
        logger.warning(
            f"⚠️ Using legacy category fetch for {frontend_category}. "
            f"Consider using get_all_canonical_data_smart() instead!"
        )
        
        # Use old method (fetches from specific category)
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
        
        # Get article list
        articles = await self.get_all_category_articles(
            wiki_category, 
            max_total=limit
        )
        
        if not articles:
            return []
        
        # Optionally enrich with details
        if with_details:
            article_ids = [item["id"] for item in articles]
            details = await self.get_article_details_batch(article_ids)
            
            # Enrich
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
            # Just titles (fast)
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