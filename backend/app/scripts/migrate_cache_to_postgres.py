# backend/scripts/migrate_cache_to_postgres.py
"""
Migration Script: File Cache → PostgreSQL

Converts existing file-based cache to PostgreSQL hybrid backend.

Usage:
    python scripts/migrate_cache_to_postgres.py
    python scripts/migrate_cache_to_postgres.py --universe star_wars --verify
"""

import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.core.scraper.wiki_scraper import WikiScraper
from app.services.postgres_cache_service import PostgresCacheService
import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_cache_to_postgres(universe: str = 'star_wars', verify: bool = True):
    """
    Migrate file cache to PostgreSQL.
    
    Args:
        universe: Universe to migrate
        verify: Verify migration after completion
    """
    logger.info("="*80)
    logger.info("🔄 CACHE MIGRATION: File → PostgreSQL")
    logger.info("="*80)
    logger.info(f"Universe: {universe}")
    logger.info(f"Verify: {verify}")
    logger.info("="*80 + "\n")
    
    # Initialize services
    scraper = WikiScraper()
    db = SessionLocal()
    pg_cache = PostgresCacheService(db)
    
    try:
        # ============================================
        # STEP 1: Load file cache
        # ============================================
        
        logger.info("📂 STEP 1: Loading file cache...")
        
        cached_data = scraper.canon_cache.load(universe, depth=3)
        
        if not cached_data:
            logger.error("❌ No file cache found!")
            logger.info("💡 Run startup_prefetch_all() first to create cache")
            return False
        
        total_articles = sum(len(items) for items in cached_data.items())
        logger.info(f"✅ Loaded {total_articles:,} articles from file cache")
        
        for category, items in sorted(cached_data.items(), key=lambda x: -len(x[1])):
            logger.info(f"   {category:15s}: {len(items):5,} items")
        
        logger.info("")
        
        # ============================================
        # STEP 2: Migrate to PostgreSQL
        # ============================================
        
        logger.info("💾 STEP 2: Migrating to PostgreSQL...")
        
        # Create scraping log
        log = pg_cache.create_scraping_log(
            universe=universe,
            operation_type='file_to_postgres_migration'
        )
        
        logger.info(f"📋 Created scraping log #{log.id}\n")
        
        total_created = 0
        total_updated = 0
        
        for category, articles in cached_data.items():
            logger.info(f"   📦 {category}: {len(articles):,} articles")
            
            # Prepare article data
            articles_data = [
                {
                    'title': article,
                    'universe': universe,
                    'category': category,
                    'content': {},
                    'image_url': None,
                    'source_url': None
                }
                for article in articles
            ]
            
            # Bulk upsert
            stats = pg_cache.bulk_upsert_articles(
                articles_data,
                batch_size=500
            )
            
            total_created += stats['created']
            total_updated += stats['updated']
            
            logger.info(f"      ✅ Created: {stats['created']:,}, Updated: {stats['updated']:,}")
        
        logger.info(f"\n✅ Migration complete!")
        logger.info(f"   ✨ Created: {total_created:,}")
        logger.info(f"   🔄 Updated: {total_updated:,}")
        
        # ============================================
        # STEP 3: Update category cache
        # ============================================
        
        logger.info(f"\n📊 STEP 3: Updating category cache...")
        
        pg_cache.update_category_cache(universe)
        
        logger.info(f"✅ Category cache updated")
        
        # ============================================
        # STEP 4: Complete scraping log
        # ============================================
        
        pg_cache.complete_scraping_log(
            log_id=log.id,
            stats={
                'articles_processed': total_articles,
                'articles_created': total_created,
                'articles_updated': total_updated
            },
            status='completed'
        )
        
        logger.info(f"\n📋 Scraping log #{log.id} completed")
        
        # ============================================
        # STEP 5: Verification (optional)
        # ============================================
        
        if verify:
            logger.info(f"\n🔍 STEP 5: Verifying migration...")
            
            success = verify_migration(pg_cache, cached_data, universe)
            
            if success:
                logger.info("✅ Verification passed!")
            else:
                logger.error("❌ Verification failed!")
                return False
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 MIGRATION COMPLETE!")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Summary:")
        logger.info(f"   Articles migrated: {total_articles:,}")
        logger.info(f"   Articles created: {total_created:,}")
        logger.info(f"   Articles updated: {total_updated:,}")
        logger.info(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        
        # Mark log as failed
        if 'log' in locals():
            pg_cache.complete_scraping_log(
                log_id=log.id,
                stats={'articles_processed': 0, 'errors_count': 1},
                status='failed',
                error_message=str(e)
            )
        
        return False
    
    finally:
        db.close()


def verify_migration(
    pg_cache: PostgresCacheService,
    cached_data: dict,
    universe: str
) -> bool:
    """
    Verify migration was successful.
    
    Args:
        pg_cache: PostgreSQL cache service
        cached_data: Original file cache data
        universe: Universe name
        
    Returns:
        True if verification passed
    """
    logger.info("\n   Verifying counts per category...")
    
    all_passed = True
    
    for category, items in cached_data.items():
        file_count = len(items)
        
        # Get count from PostgreSQL
        db_articles = pg_cache.get_articles_by_category(
            universe=universe,
            category=category
        )
        db_count = len(db_articles)
        
        if file_count == db_count:
            logger.info(f"   ✅ {category:15s}: {file_count:5,} == {db_count:5,}")
        else:
            logger.error(f"   ❌ {category:15s}: {file_count:5,} != {db_count:5,}")
            all_passed = False
    
    # Verify random samples
    logger.info("\n   Verifying random samples...")
    
    import random
    
    for category, items in list(cached_data.items())[:3]:  # Test 3 categories
        if not items:
            continue
        
        # Pick random item
        random_item = random.choice(items)
        
        # Check if in PostgreSQL
        article = pg_cache.get_article_by_title(random_item, universe)
        
        if article:
            logger.info(f"   ✅ Found '{random_item}' in PostgreSQL")
        else:
            logger.error(f"   ❌ Missing '{random_item}' in PostgreSQL")
            all_passed = False
    
    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate file cache to PostgreSQL'
    )
    
    parser.add_argument(
        '--universe',
        type=str,
        default='star_wars',
        help='Universe to migrate (default: star_wars)'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration after completion'
    )
    
    parser.add_argument(
        '--no-verify',
        dest='verify',
        action='store_false',
        help='Skip verification'
    )
    
    parser.set_defaults(verify=True)
    
    args = parser.parse_args()
    
    success = migrate_cache_to_postgres(
        universe=args.universe,
        verify=args.verify
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()