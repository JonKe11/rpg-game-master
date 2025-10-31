# backend/app/services/startup_prefetch_service.py
"""
Startup Prefetch Service - Background data loading with PostgreSQL Hybrid Backend.
NEW ARCHITECTURE:
- Primary: PostgreSQL (HybridCacheService) - structured, queryable data
- Uses FANDOM API for all data fetching
- Images: Filesystem cache (ImageFetcher) - binary files
- Audit: ScrapingLog - tracks all operations
This service runs in the background when the backend starts, ensuring:
1. All canon articles are categorized and cached in PostgreSQL
2. All images are pre-downloaded to filesystem
3. Frontend gets instant responses (zero waiting!)
The API is available immediately - prefetch doesn't block startup.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from app.services.unified_cache_service import UnifiedCacheService
from app.core.scraper.image_fetcher import ImageFetcher
from app.core.wiki import create_wiki_client  # ✅ NOWY IMPORT
from app.models.database import SessionLocal
logger = logging.getLogger(__name__)
class StartupPrefetchService:
    """
    Manages background prefetching with PostgreSQL Hybrid Backend.
    
    Features:
    - PostgreSQL storage (structured, queryable)
    - Non-blocking (API ready immediately)
    - Progress tracking
    - Audit logging (ScrapingLog)
    - Error resilience
    - Parallel image downloading
    - FANDOM API integration (fast!)
    
    Architecture:
    1. FANDOM API fetches all data with details (image URLs!)
    2. HybridCacheService writes to PostgreSQL
    3. ImageFetcher downloads images (filesystem)
    4. ScrapingLog tracks everything
    """
    
    def __init__(self):
        self.cache_service = UnifiedCacheService(use_hybrid=True)
        self.image_fetcher = ImageFetcher()
        
        # Prefetch status
        self.is_running = False
        self.is_complete = False
        self.progress = {
            'stage': 'idle',
            'articles_total': 0,
            'articles_processed': 0,
            'articles_created': 0,
            'articles_updated': 0,
            'images_total': 0,
            'images_downloaded': 0,
            'images_cached': 0,
            'images_failed': 0,
            'started_at': None,
            'completed_at': None,
            'errors': [],
            'log_id': None  # ScrapingLog ID
        }
        
        # Hybrid service (lazy init)
        self._hybrid_service = None
        self._db = None
    
    def _init_hybrid_service(self):
        """Initialize hybrid service (lazy)."""
        if self._hybrid_service is None:
            try:
                from app.services.hybrid_cache_service import HybridCacheService
                self._db = SessionLocal()
                self._hybrid_service = HybridCacheService(self._db)
                logger.info("✅ Hybrid service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize hybrid service: {e}")
        
        return self._hybrid_service
    
    def _close_hybrid_service(self):
        """Close hybrid service resources."""
        if self._db:
            self._db.close()
            self._db = None
        self._hybrid_service = None
    
    # ============================================
    # MAIN PREFETCH METHOD
    # ============================================
    
    async def prefetch_all(
        self,
        universe: str = 'star_wars',
        force_refresh: bool = False,
        prefetch_images: bool = True,
        image_workers: int = 20,
        use_hybrid: bool = True
    ):
        """
        Main prefetch orchestrator - runs all prefetch stages.
        
        Args:
            universe: Universe to prefetch
            force_refresh: Force refresh even if cache exists
            prefetch_images: Whether to prefetch images
            image_workers: Number of parallel image workers
            use_hybrid: Use PostgreSQL hybrid backend
        """
        if self.is_running:
            logger.warning("⚠️ Prefetch already running!")
            return
        
        self.is_running = True
        self.is_complete = False
        self.progress['started_at'] = datetime.now().isoformat()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 STARTUP PREFETCH - FANDOM API MODE")
        logger.info(f"{'='*80}")
        logger.info(f"Universe: {universe}")
        logger.info(f"Force refresh: {force_refresh}")
        logger.info(f"Prefetch images: {prefetch_images}")
        logger.info(f"Image workers: {image_workers}")
        logger.info(f"Hybrid backend: {use_hybrid}")
        logger.info(f"{'='*80}\n")
        
        hybrid_service = None
        
        try:
            # Initialize hybrid service
            if use_hybrid:
                hybrid_service = self._init_hybrid_service()
                
                if hybrid_service:
                    # Create scraping log
                    log = hybrid_service.pg_cache.create_scraping_log(
                        universe=universe,
                        operation_type='startup_prefetch_all'
                    )
                    self.progress['log_id'] = log.id
                    logger.info(f"📋 Created scraping log #{log.id}\n")
            
            # STAGE 1: Fetch ALL data via FANDOM API (with details!)
            await self._stage_1_fetch_via_api(universe, force_refresh)
            
            # STAGE 1.5: Write to PostgreSQL
            if use_hybrid and hybrid_service:
                await self._stage_1_5_write_to_postgresql(universe, hybrid_service)
            
            # STAGE 2: Prefetch Images (parallel!)
            if prefetch_images:
                await self._stage_2_prefetch_images(
                    universe,
                    image_workers,
                    hybrid_service if use_hybrid else None
                )
            
            # STAGE 3: Finalize
            await self._stage_3_finalize(hybrid_service if use_hybrid else None)
            
        except Exception as e:
            logger.error(f"❌ Prefetch failed: {e}")
            import traceback
            traceback.print_exc()
            self.progress['errors'].append(str(e))
            self.progress['stage'] = 'failed'
            
            # Mark log as failed
            if hybrid_service and self.progress['log_id']:
                hybrid_service.pg_cache.complete_scraping_log(
                    log_id=self.progress['log_id'],
                    stats=self.progress,
                    status='failed',
                    error_message=str(e)
                )
        
        finally:
            self.is_running = False
            self.is_complete = True
            self.progress['completed_at'] = datetime.now().isoformat()
            
            # Close hybrid service
            self._close_hybrid_service()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ STARTUP PREFETCH COMPLETE")
            logger.info(f"{'='*80}\n")
    
    # ============================================
    # STAGE 1: Fetch via FANDOM API (WITH DETAILS!)
    # ============================================
    
    async def _stage_1_fetch_via_api(
        self,
        universe: str,
        force_refresh: bool
    ):
        """
        Stage 1: Fetch ALL canon data via SMART CATEGORIZATION.
        
        ✅ NEW APPROACH:
        - Fetches ALL ~58k articles from Canon_articles
        - Checks each article's categories
        - Sorts automatically using keyword matching
        
        Takes ~5-10 minutes for 58k articles.
        """
        self.progress['stage'] = 'fetching_via_api'
        
        logger.info("📊 STAGE 1: Smart Canon Categorization")
        logger.info("="*80)
        logger.info("⏱️  Estimated time: ~5-10 minutes")
        logger.info("🎯 Method: Fetch from Canon_articles + auto-categorize")
        logger.info("📦 Expected: ~58,000 articles\n")
        
        try:
            # ✅ Use NEW smart method!
            async with create_wiki_client(universe) as client:
                logger.info(f"🔗 Connected to {client.config.name}\n")
                
                # This does EVERYTHING:
                # 1. Fetches ALL from Canon_articles
                # 2. Gets categories for each article
                # 3. Categorizes automatically
                # 4. Fetches details (image URLs!)
                categorized_data = await client.get_all_canonical_data_smart(
                    with_details=True,  # Get image URLs!
                    max_workers=20       # Parallel processing
                )
            
            # Store for later stages
            self._categorized_data = categorized_data
            
            # Update progress
            total_articles = sum(len(items) for items in categorized_data.values())
            self.progress['articles_total'] = total_articles
            self.progress['articles_processed'] = total_articles
            
            logger.info(f"\n✅ STAGE 1 COMPLETE!")
            logger.info(f"   📦 Total articles: {total_articles:,}")
            
            for category, items in sorted(categorized_data.items(), key=lambda x: -len(x[1])):
                if items:
                    # Count how many have images
                    with_images = sum(1 for item in items if item.get('image_url'))
                    logger.info(f"      {category:15s}: {len(items):5,} items ({with_images:,} with images)")
            
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Stage 1 failed: {e}", exc_info=True)
            raise
    
    # ============================================
    # ✅ FIXED STAGE 1.5: Write to PostgreSQL
    # ============================================
    
    async def _stage_1_5_write_to_postgresql(
        self,
        universe: str,
        hybrid_service
    ):
        """
        Stage 1.5: Write categorized data to PostgreSQL.
        
        ✅ FIXED: 
        - Saves full content (all article fields, not just description)
        - Preserves species, homeworld, abilities, etc.
        """
        self.progress['stage'] = 'writing_to_postgresql'
        
        logger.info("💾 STAGE 1.5: Writing to PostgreSQL")
        logger.info("="*80)
        logger.info("⏱️  Estimated time: ~1 minute")
        logger.info("🔥 Using bulk upsert (500 per batch)\n")
        
        try:
            categorized_data = self._categorized_data
            
            created = 0
            updated = 0
            
            # Run in executor to not block event loop
            loop = asyncio.get_event_loop()
            
            for category, articles in categorized_data.items():
                logger.info(f"   📦 {category}: {len(articles):,} articles...")
                
                def write_category():
                    # Prepare article data
                    articles_data = []
                    
                    for article in articles:
                        if isinstance(article, dict):
                            # ✅ FIXED: Save ALL fields to content
                            # Extract title and image_url, put rest in content
                            title = article.get('title', article.get('name', 'Unknown'))
                            image_url = article.get('image_url') or article.get('thumbnail')
                            source_url = article.get('url')
                            
                            # Build content dict from ALL article fields
                            content = {}
                            for key, value in article.items():
                                # Skip fields we store separately
                                if key not in ['title', 'name', 'image_url', 'thumbnail', 'url']:
                                    content[key] = value
                            
                            # Add description if exists
                            if 'abstract' in article:
                                content['description'] = article['abstract']
                            elif 'description' in article:
                                content['description'] = article['description']
                            
                            articles_data.append({
                                'title': title,
                                'universe': universe,
                                'category': category,
                                'content': content,  # ✅ Full content!
                                'image_url': image_url,
                                'source_url': source_url
                            })
                        else:
                            # Just title (string)
                            articles_data.append({
                                'title': article,
                                'universe': universe,
                                'category': category,
                                'content': {},
                                'image_url': None,
                                'source_url': None
                            })
                    
                    # Bulk insert
                    return hybrid_service.pg_cache.bulk_upsert_articles(
                        articles_data,
                        batch_size=500
                    )
                
                stats = await loop.run_in_executor(None, write_category)
                
                created += stats['created']
                updated += stats['updated']
                
                logger.info(f"      ✅ Created: {stats['created']:,}, Updated: {stats['updated']:,}")
            
            self.progress['articles_created'] = created
            self.progress['articles_updated'] = updated
            
            logger.info(f"\n✅ STAGE 1.5 COMPLETE!")
            logger.info(f"   ✨ Created: {created:,}")
            logger.info(f"   🔄 Updated: {updated:,}")
            
            # Update category cache
            logger.info(f"\n📊 Updating category cache...")
            
            def update_cache():
                hybrid_service.pg_cache.update_category_cache(universe)
            
            await loop.run_in_executor(None, update_cache)
            
            logger.info(f"   ✅ Category cache updated\n")
            
        except Exception as e:
            logger.error(f"❌ Stage 1.5 failed: {e}")
            # Don't raise - PostgreSQL is optional
            self.progress['errors'].append(f"PostgreSQL write: {str(e)}")
    
    # ============================================
    # STAGE 2: Prefetch Images (FROM POSTGRESQL!)
    # ============================================
    
    async def _stage_2_prefetch_images(
        self,
        universe: str,
        max_workers: int,
        hybrid_service
    ):
        """
        Stage 2: Pre-download images using data from PostgreSQL.
        
        ✅ NEW: Reads image URLs from PostgreSQL (already fetched in Stage 1!)
        ✅ No more HTML scraping!
        
        Downloads images for:
        - Planets (for location selector)
        - Weapons, Armor, Vehicles, Droids, Items (for item browser)
        
        Uses parallel downloading for speed.
        Takes ~3-5 minutes depending on network.
        """
        self.progress['stage'] = 'prefetching_images'
        
        logger.info("🖼️ STAGE 2: Prefetching Images")
        logger.info("="*80)
        logger.info("⏱️  Estimated time: ~3-5 minutes")
        logger.info(f"💷 Workers: {max_workers} parallel downloads\n")
        
        # Categories that need images
        VISUAL_CATEGORIES = ['planets', 'weapons', 'armor', 'vehicles', 'droids', 'items']
        
        try:
            if not hybrid_service:
                logger.warning("⚠️ No hybrid service - skipping image prefetch")
                return
            
            logger.info(f"📦 Reading image URLs from PostgreSQL...\n")
            
            # Process each category
            for category in VISUAL_CATEGORIES:
                logger.info(f"   🎯 {category.upper()}")
                
                # Get articles from PostgreSQL
                articles = await self.postgres_service.get_articles_with_images(
                    universe=universe,
                    category=category,
                    limit=5000  # ✅ Zwiększone z 1000 do 5000!
    )
                
                # Filter: only articles with image_url and not yet cached
                to_fetch = [
                    article for article in articles
                    if article.image_url and not article.image_cached
                ]
                
                logger.info(f"      📋 Found {len(articles):,} articles, {len(to_fetch):,} need image download")
                
                if not to_fetch:
                    logger.info(f"      ✅ All images already cached!\n")
                    continue
                
                # Prepare tasks
                tasks = [
                    (article.title, article.image_url, idx + 1, len(to_fetch))
                    for idx, article in enumerate(to_fetch)
                ]
                
                # Run in executor
                loop = asyncio.get_event_loop()
                
                def fetch_images():
                    return self.image_fetcher.fetch_batch_parallel(
                        tasks,
                        max_workers=max_workers,
                        show_progress=False  # We log ourselves
                    )
                
                stats = await loop.run_in_executor(None, fetch_images)
                
                # Update progress
                self.progress['images_downloaded'] += stats['downloaded']
                self.progress['images_cached'] += stats['cached']
                self.progress['images_failed'] += stats['failed']
                
                logger.info(f"      ✅ ↓{stats['downloaded']:,} ✓{stats['cached']:,} ✗{stats['failed']:,}")
                
                # Update PostgreSQL image status
                def update_image_status():
                    for article in to_fetch:
                        if article.image_url:
                            cache_path = self.image_fetcher.get_cache_path(article.image_url)
                            
                            if cache_path.exists():
                                hybrid_service.pg_cache.mark_image_cached(
                                    article.title,
                                    article.universe,
                                    str(cache_path)
                                )
                                
                                # Register in image_cache table
                                url_hash = cache_path.stem
                                try:
                                    hybrid_service.pg_cache.register_image(
                                        url=article.image_url,
                                        url_hash=url_hash,
                                        local_path=str(cache_path),
                                        size_bytes=cache_path.stat().st_size
                                    )
                                except Exception as e:
                                    # Ignore duplicate key errors
                                    pass
                
                await loop.run_in_executor(None, update_image_status)
                logger.info(f"      💾 PostgreSQL updated\n")
            
            logger.info(f"✅ STAGE 2 COMPLETE!")
            logger.info(f"   💾 Downloaded: {self.progress['images_downloaded']:,}")
            logger.info(f"   ✅ Cached: {self.progress['images_cached']:,}")
            logger.info(f"   ❌ Failed: {self.progress['images_failed']:,}\n")
            
        except Exception as e:
            logger.error(f"❌ Stage 2 failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - images are optional
            self.progress['errors'].append(f"Image prefetch: {str(e)}")
    
    # ============================================
    # STAGE 3: Finalize
    # ============================================
    
    async def _stage_3_finalize(self, hybrid_service):
        """
        Stage 3: Finalize and log summary.
        """
        self.progress['stage'] = 'complete'
        
        # Calculate duration
        duration = None
        if self.progress['started_at'] and self.progress['completed_at']:
            start = datetime.fromisoformat(self.progress['started_at'])
            end = datetime.fromisoformat(self.progress['completed_at'])
            duration = (end - start).total_seconds()
            
            logger.info(f"⏱️  Total duration: {duration:.1f}s ({duration/60:.1f}min)")
        
        # Log summary
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Articles total: {self.progress['articles_total']:,}")
        logger.info(f"   Articles created: {self.progress['articles_created']:,}")
        logger.info(f"   Articles updated: {self.progress['articles_updated']:,}")
        logger.info(f"   Images downloaded: {self.progress['images_downloaded']:,}")
        logger.info(f"   Images cached: {self.progress['images_cached']:,}")
        logger.info(f"   Images failed: {self.progress['images_failed']:,}")
        
        if self.progress['errors']:
            logger.warning(f"   ⚠️  Errors: {len(self.progress['errors'])}")
        
        # Complete scraping log
        if hybrid_service and self.progress['log_id']:
            loop = asyncio.get_event_loop()
            
            def complete_log():
                hybrid_service.pg_cache.complete_scraping_log(
                    log_id=self.progress['log_id'],
                    stats=self.progress,
                    status='completed'
                )
            
            await loop.run_in_executor(None, complete_log)
            
            logger.info(f"\n📋 Scraping log #{self.progress['log_id']} completed")
    
    # ============================================
    # PUBLIC API
    # ============================================
    
    def get_progress(self) -> Dict:
        """
        Get current prefetch progress.
        
        Returns:
            Dict with progress information
        """
        return self.progress.copy()
    
    def is_prefetch_complete(self) -> bool:
        """Check if prefetch is complete."""
        return self.is_complete


# ============================================
# GLOBAL INSTANCE & ENTRY POINT
# ============================================

_prefetch_service: Optional[StartupPrefetchService] = None


def get_prefetch_service() -> StartupPrefetchService:
    """Get or create global prefetch service instance."""
    global _prefetch_service
    if _prefetch_service is None:
        _prefetch_service = StartupPrefetchService()
    return _prefetch_service


async def startup_prefetch_all(
    universe: str = 'star_wars',
    force_refresh: bool = False,
    prefetch_images: bool = True,
    image_workers: int = 20
):
    """
    Entry point for startup prefetch - called from main.py lifespan.
    
    This is the main function called during backend startup.
    It runs in background - API is available immediately!
    
    Args:
        universe: Universe to prefetch (default: star_wars)
        force_refresh: Force refresh cache (default: False)
        prefetch_images: Whether to prefetch images (default: True)
        image_workers: Number of parallel image workers (default: 20)
    """
    service = get_prefetch_service()
    
    # Check if cache is valid (skip if not force_refresh)
    if not force_refresh:
        cache_info = service.cache_service.get_cache_info(universe)
        
        # Check file cache or PostgreSQL
        file_exists = cache_info.get('file_cache', {}).get('exists')
        pg_info = cache_info.get('postgresql')
        pg_has_data = pg_info and pg_info.get('total_articles', 0) > 0
        
        if file_exists or pg_has_data:
            logger.info("✅ Cache exists (file or PostgreSQL)")
            logger.info("   ⏩ Skipping full prefetch")
            logger.info("   💡 Use force_refresh=True to refresh\n")
            
            # Still check for missing images
            if prefetch_images and pg_has_data:
                logger.info("🖼️  Checking for missing images...")
                hybrid_service = service._init_hybrid_service()
                if hybrid_service:
                    await service._stage_2_prefetch_images(
                        universe,
                        image_workers,
                        hybrid_service
                    )
                    service._close_hybrid_service()
            
            return
    
    # Run full prefetch
    await service.prefetch_all(
        universe=universe,
        force_refresh=force_refresh,
        prefetch_images=prefetch_images,
        image_workers=image_workers,
        use_hybrid=True
    )