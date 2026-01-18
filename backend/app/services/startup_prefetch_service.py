# backend/app/services/startup_prefetch_service.py



import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime


from app.core.scraper.image_fetcher import ImageFetcher
from app.core.wiki import create_wiki_client
from app.models.database import SessionLocal

from app.services.postgres_cache_service import PostgresCacheService

logger = logging.getLogger(__name__)

class StartupPrefetchService:
    """
    Manages background prefetching with PostgreSQL Hybrid Backend.
    """
    
    def __init__(self):
       
        self.image_fetcher = ImageFetcher()
        self.wiki_domain = None 
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
            'log_id': None
        }
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
            if use_hybrid:
                hybrid_service = self._init_hybrid_service()
                
                if hybrid_service:
                    log = hybrid_service.pg_cache.create_scraping_log(
                        universe=universe,
                        operation_type='startup_prefetch_all'
                    )
                    self.progress['log_id'] = log.id
                    logger.info(f"📋 Created scraping log #{log.id}\n")
            
            await self._stage_1_fetch_via_api(universe, force_refresh)
            
            if use_hybrid and hybrid_service:
                await self._stage_1_5_write_to_postgresql(universe, hybrid_service)
            
            if prefetch_images:
                await self._stage_2_prefetch_images(
                    universe,
                    image_workers,
                    hybrid_service if use_hybrid else None
                )
            
            await self._stage_3_finalize(hybrid_service if use_hybrid else None)
            
        except Exception as e:
            logger.error(f"❌ Prefetch failed: {e}", exc_info=True)
            self.progress['errors'].append(str(e))
            self.progress['stage'] = 'failed'
            
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
            self._close_hybrid_service()
            logger.info(f"\n{'='*80}\n✅ STARTUP PREFETCH COMPLETE\n{'='*80}\n")
    
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
        """
        self.progress['stage'] = 'fetching_via_api'
        logger.info("📊 STAGE 1: Smart Canon Categorization")
        logger.info("="*80)
        
        try:
            async with create_wiki_client(universe) as client:
                logger.info(f"🔗 Connected to {client.config.name}\n")
                
                try:
                    domain = client.base_url.split('/api')[0].split('/wiki')[0]
                    self.wiki_domain = domain
                    logger.info(f"Using wiki domain for URLs: {self.wiki_domain}")
                except Exception:
                    logger.error("Could not parse wiki domain")
                
                categorized_data = await client.get_all_canonical_data_smart(
                    with_details=True,
                    max_workers=20
                )
            
            self._categorized_data = categorized_data
            
            total_articles = sum(len(items) for items in categorized_data.values())
            self.progress['articles_total'] = total_articles
            self.progress['articles_processed'] = total_articles
            
            logger.info(f"\n✅ STAGE 1 COMPLETE! Total articles: {total_articles:,}")
            for category, items in sorted(categorized_data.items(), key=lambda x: -len(x[1])):
                if items:
                    with_images = sum(1 for item in items if item.get('image_url'))
                    logger.info(f"      {category:15s}: {len(items):5,} items ({with_images:,} with images)")
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Stage 1 failed: {e}", exc_info=True)
            raise
    
    # ============================================
    # STAGE 1.5: Write to PostgreSQL
    # ============================================
    
    async def _stage_1_5_write_to_postgresql(
        self,
        universe: str,
        hybrid_service
    ):
        """
        Stage 1.5: Write categorized data to PostgreSQL.
        """
        self.progress['stage'] = 'writing_to_postgresql'
        logger.info("💾 STAGE 1.5: Writing to PostgreSQL")
        logger.info("="*80)
        
        try:
            categorized_data = self._categorized_data
            created = 0
            updated = 0
            loop = asyncio.get_event_loop()
            
            def _parse_categories_for_infobox(categories: List[str]) -> Dict:
                infobox = {}
                if not categories: return infobox
                for cat in categories:
                    if cat.startswith("Planets in the "): infobox["Region"] = cat.replace("Planets in the ", "").strip()
                    elif cat.endswith(" sector"): infobox["Sector"] = cat
                    elif cat.startswith("Planets in ") and cat.endswith(" sector"): infobox["Sector"] = cat.replace("Planets in ", "").strip()
                    elif cat.endswith(" system") or cat.endswith(" system locations"): infobox["System"] = cat.replace(" locations", "").strip()
                    elif cat.endswith(" locations"): infobox["Planet"] = cat.replace(" locations", "").strip()
                return infobox
            
            for category, articles in categorized_data.items():
                logger.info(f"   📦 {category}: {len(articles):,} articles...")
                
                def write_category():
                    articles_data = []
                    for article in articles:
                        if isinstance(article, dict):
                            title = article.get('title', article.get('name', 'Unknown'))
                            image_url = article.get('image_url') or article.get('thumbnail')
                            
                            relative_url = article.get('url')
                            source_url = None
                            if relative_url and self.wiki_domain:
                                source_url = f"{self.wiki_domain}{relative_url}" if relative_url.startswith('/') else f"{self.wiki_domain}/{relative_url}"

                            content = {}
                            for key, value in article.items():
                                if key not in ['title', 'name', 'image_url', 'thumbnail', 'url']:
                                    content[key] = value
                            
                            raw_categories = content.get('categories', [])
                            parsed_infobox = _parse_categories_for_infobox(raw_categories)
                            content.update(parsed_infobox)
                            
                            if 'abstract' in article: content['description'] = article['abstract']
                            elif 'description' in article: content['description'] = article['description']
                            
                            articles_data.append({
                                'title': title, 'universe': universe, 'category': category,
                                'content': content, 'image_url': image_url, 'source_url': source_url
                            })
                        else:
                            articles_data.append({
                                'title': article, 'universe': universe, 'category': category,
                                'content': {}, 'image_url': None, 'source_url': None
                            })
                    
                    return hybrid_service.pg_cache.bulk_upsert_articles(articles_data, batch_size=500)
                
                stats = await loop.run_in_executor(None, write_category)
                created += stats['created']
                updated += stats['updated']
                logger.info(f"      ✅ Created: {stats['created']:,}, Updated: {stats['updated']:,}")
            
            self.progress['articles_created'] = created
            self.progress['articles_updated'] = updated
            
            logger.info(f"\n✅ STAGE 1.5 COMPLETE! Created: {created:,}, Updated: {updated:,}")
            
   
            self._categorized_data = None 
            logger.info(f"   ✅ Zwolniono pamięć RAM (self._categorized_data)\n")

            logger.info(f"📊 Updating category cache...")
            def update_cache():
                hybrid_service.pg_cache.update_category_cache(universe)
            await loop.run_in_executor(None, update_cache)
            logger.info(f"   ✅ Category cache updated\n")
            
        except Exception as e:
            logger.error(f"❌ Stage 1.5 failed: {e}")
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
        """
        self.progress['stage'] = 'prefetching_images'
        logger.info("🖼️ STAGE 2: Prefetching Images")
        logger.info("="*80)
        logger.info(f"💷 Workers: {max_workers} parallel downloads\n")
        
     
        VISUAL_CATEGORIES = [
            'planets', 'weapons', 'armor', 'vehicles', 'droids', 'items',
            'characters', 'species', 'creatures'
        ]
        
        try:
            if not hybrid_service:
                logger.warning("⚠️ No hybrid service - skipping image prefetch")
                return
            
            logger.info(f"📦 Reading image URLs from PostgreSQL...\n")
            
            for category in VISUAL_CATEGORIES:
                logger.info(f"   🎯 {category.upper()}")
                
           
           
                articles = hybrid_service.pg_cache.get_articles_by_category(
                    universe=universe,
                    category=category
              
                )
                
                to_fetch = [
                    article for article in articles
                    if article.image_url and not article.image_cached
                ]
                
                logger.info(f"      📋 Found {len(articles):,} articles, {len(to_fetch):,} need image download")
                
                if not to_fetch:
                    logger.info(f"       All images already cached!\n")
                    continue
                
                tasks = [(a.title, a.image_url, i + 1, len(to_fetch)) for i, a in enumerate(to_fetch)]
                loop = asyncio.get_event_loop()
                
                def fetch_images():
                    return self.image_fetcher.fetch_batch_parallel(
                        tasks, max_workers=max_workers, show_progress=False
                    )
                
                stats = await loop.run_in_executor(None, fetch_images)
                
                self.progress['images_downloaded'] += stats['downloaded']
                self.progress['images_cached'] += stats['cached']
                self.progress['images_failed'] += stats['failed']
                
                logger.info(f"      ✅ ↓{stats['downloaded']:,} ✓{stats['cached']:,} ✗{stats['failed']:,}")
                
                def update_image_status():
                    for article in to_fetch:
                        if article.image_url:
                            cache_path = self.image_fetcher.get_cache_path(article.image_url)
                            if cache_path.exists():
                                hybrid_service.pg_cache.mark_image_cached(
                                    article.title, article.universe, str(cache_path)
                                )
                                url_hash = cache_path.stem
                                try:
                                    hybrid_service.pg_cache.register_image(
                                        url=article.image_url, url_hash=url_hash,
                                        local_path=str(cache_path), size_bytes=cache_path.stat().st_size
                                    )
                                except Exception: pass
                
                await loop.run_in_executor(None, update_image_status)
                logger.info(f"      💾 PostgreSQL updated\n")
            
            logger.info(f"✅ STAGE 2 COMPLETE!")
            
        except Exception as e:
            logger.error(f"❌ Stage 2 failed: {e}", exc_info=True)
            self.progress['errors'].append(f"Image prefetch: {str(e)}")
    
    # ============================================
    # STAGE 3: Finalize
    # ============================================
    
    async def _stage_3_finalize(self, hybrid_service):
        """
        Stage 3: Finalize and log summary.
        """
        self.progress['stage'] = 'complete'
        
        duration = None

        if self.progress['started_at'] and self.progress.get('completed_at'):
            try:
                start = datetime.fromisoformat(self.progress['started_at'])
                end = datetime.fromisoformat(self.progress['completed_at'])
                duration = (end - start).total_seconds()
                logger.info(f"⏱️  Total duration: {duration:.1f}s ({duration/60:.1f}min)")
            except ValueError:
                logger.warning("Could not parse duration.")
        
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Articles total: {self.progress['articles_total']:,}")
        logger.info(f"   Articles created: {self.progress['articles_created']:,}")
        logger.info(f"   Articles updated: {self.progress['articles_updated']:,}")
        logger.info(f"   Images downloaded: {self.progress['images_downloaded']:,}")
        logger.info(f"   Images cached: {self.progress['images_cached']:,}")
        logger.info(f"   Images failed: {self.progress['images_failed']:,}")
        
        if self.progress['errors']:
            logger.warning(f"   ⚠️  Errors: {len(self.progress['errors'])}")
        
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
    """
    service = get_prefetch_service()
    

 
    if not force_refresh:
        pg_has_data = False
        db_conn = None
        try:
            db_conn = SessionLocal()
           
            pg_stats = PostgresCacheService(db_conn).get_cache_stats(universe)
            pg_has_data = pg_stats and pg_stats.get('total_articles', 0) > 0
        except Exception as e:
            logger.warning(f"Could not check PG cache (is DB running?): {e}")
        finally:
            if db_conn:
                db_conn.close()

        if pg_has_data:
            logger.info("✅ PostgreSQL cache exists")
            logger.info("   ⏩ Skipping full prefetch")
            logger.info("   💡 Use force_refresh=True to refresh\n")
            
          
            if prefetch_images:
                logger.info("  Checking for missing images...")
                hybrid_service = service._init_hybrid_service()
                if hybrid_service:
                    await service._stage_2_prefetch_images(
                        universe,
                        image_workers,
                        hybrid_service
                    )
                    service._close_hybrid_service() 
            
            return
    
    
    await service.prefetch_all(
        universe=universe,
        force_refresh=force_refresh,
        prefetch_images=prefetch_images,
        image_workers=image_workers,
        use_hybrid=True
    )