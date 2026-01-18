# backend/app/services/postgres_cache_service.py


from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.dialects.postgresql import insert
import logging

from app.models.wiki_article import WikiArticle, ImageCache, ScrapingLog, CategoryCache

logger = logging.getLogger(__name__)


class PostgresCacheService:
    """
    PostgreSQL-backed cache for wiki articles.
    
    Replaces file-based JSON cache with queryable database.
    """
    
    def __init__(self, db: Session, ttl_days: int = 7):
        """
        Initialize service.
        """
        self.db = db
        self.ttl_days = ttl_days
    
    # ============================================
    # GŁÓWNA NOWA FUNKCJA ODCZYTU
    # ============================================
    
    def search_articles_paginated(
        self,
        universe: str,
        category: str,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        with_images_only: bool = False
    ) -> Dict:
        """
        Uniwersalna funkcja wyszukiwania i paginacji dla kategorii.
        
        Jeśli 'query' jest None, zwraca paginowaną listę wszystkich artykułów.
        Jeśli 'query' jest podane, filtruje po nazwie (ILIKE).
        
        Zwraca:
            {
                'items': List[WikiArticle],
                'total_count': int
            }
        """
        
        
        db_query = self.db.query(WikiArticle).filter(
            WikiArticle.universe == universe,
            WikiArticle.category == category,
            WikiArticle.expires_at > datetime.now(timezone.utc)
        )
        
        
        if query:
            db_query = db_query.filter(WikiArticle.title.ilike(f'%{query}%'))
            
        
        if with_images_only:
            db_query = db_query.filter(
                WikiArticle.image_url != None,
                WikiArticle.image_url != ''
            )

        
        
        total_count = db_query.count()

       
        articles = db_query.order_by(
            WikiArticle.title
        ).offset(
            offset
        ).limit(
            limit
        ).all()
        
        return {
            'items': articles,
            'total_count': total_count
        }

    # ============================================
    # ISTNIEJĄCE METODY (BEZ ZMIAN)
    # ============================================
    
    def get_articles_by_category(
        self,
        universe: str,
        category: str,
        limit: Optional[int] = None,
        offset: int = 0,
        include_expired: bool = False
    ) -> List[WikiArticle]:
        """
        Get articles from category.
        Uses composite index (universe, category) for fast query!
        """
        query = self.db.query(WikiArticle).filter(
            WikiArticle.universe == universe,
            WikiArticle.category == category
        )
        
        if not include_expired:
            query = query.filter(WikiArticle.expires_at > datetime.now(timezone.utc))
        
        query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_article_by_title(
        self,
        title: str,
        universe: str
    ) -> Optional[WikiArticle]:
        """
        Get single article by title.
        Uses unique index (title, universe).
        """
        return self.db.query(WikiArticle).filter(
            WikiArticle.title == title,
            WikiArticle.universe == universe
        ).first()
    
    def search_articles(
        self,
        universe: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[WikiArticle]:
        """
        Full-text search in articles. (Legacy - prefer search_articles_paginated)
        Uses ILIKE with index for fast search.
        """
        db_query = self.db.query(WikiArticle).filter(
            WikiArticle.universe == universe,
            WikiArticle.title.ilike(f'%{query}%'),
            WikiArticle.expires_at > datetime.now(timezone.utc)
        )
        
        if category:
            db_query = db_query.filter(WikiArticle.category == category)
        
        return db_query.limit(limit).all()
    
    def upsert_article(
        self,
        title: str,
        universe: str,
        category: str,
        content: Dict,
        image_url: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> WikiArticle:
        """Insert or update article."""
        existing = self.get_article_by_title(title, universe)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.ttl_days)
        
        if existing:
            existing.category = category
            existing.content = content
            existing.image_url = image_url
            existing.source_url = source_url
            existing.scraped_at = datetime.now(timezone.utc)
            existing.expires_at = expires_at
            existing.last_accessed = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            article = WikiArticle(
                title=title,
                universe=universe,
                category=category,
                content=content,
                image_url=image_url,
                source_url=source_url,
                expires_at=expires_at
            )
            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)
            return article
    
    def bulk_upsert_articles(
        self,
        articles: List[Dict],
        batch_size: int = 500
    ) -> Dict[str, int]:
        """
        Bulk insert/update articles with PostgreSQL native upsert.
        """
        if not articles:
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        seen = {}
        unique_articles = []
        for article in articles:
            key = (article['title'], article['universe'])
            if key not in seen:
                seen[key] = True
                unique_articles.append(article)
        
        if len(unique_articles) < len(articles):
            logger.warning(
                f"⚠️  Removed {len(articles) - len(unique_articles)} duplicate articles"
            )
        
        articles = unique_articles
        stats = {'created': 0, 'updated': 0, 'failed': 0}
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.ttl_days)
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            try:
                batch_data = []
                for article_data in batch:
                    batch_data.append({
                        'title': article_data['title'],
                        'universe': article_data['universe'],
                        'category': article_data['category'],
                        'content': article_data.get('content', {}),
                        'image_url': article_data.get('image_url'),
                        'image_cached': article_data.get('image_cached', False),
                        'image_cache_path': article_data.get('image_cache_path'),
                        'source_url': article_data.get('source_url'),
                        'expires_at': expires_at,
                        'access_count': 0
                    })
                
                stmt = insert(WikiArticle).values(batch_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['title', 'universe'],
                    set_={
                        'category': stmt.excluded.category,
                        'content': stmt.excluded.content,
                        'image_url': stmt.excluded.image_url,
                        'image_cached': stmt.excluded.image_cached,
                        'image_cache_path': stmt.excluded.image_cache_path,
                        'source_url': stmt.excluded.source_url,
                        'expires_at': stmt.excluded.expires_at,
                        'last_accessed': datetime.now(timezone.utc)
                    }
                )
                
                result = self.db.execute(stmt)
                self.db.commit()
                
                
                
              
              
                
                stats['created'] += len(batch_data) 
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Batch commit error: {e}")
                
          
                stats['failed'] += len(batch)
        
        logger.info(f"Bulk upsert complete (approx stats): {stats}")
        return stats
    
    def mark_image_cached(
        self,
        title: str,
        universe: str,
        cache_path: str
    ) -> bool:
        """Mark article's image as cached."""
        article = self.get_article_by_title(title, universe)
        
        if not article:
            return False
        
        article.image_cached = True
        article.image_cache_path = cache_path
        article.last_accessed = datetime.now(timezone.utc)
        
        self.db.commit()
        return True
    
    # ============================================
    # CATEGORY OPERATIONS
    # ============================================
    
    def get_category_counts(self, universe: str) -> Dict[str, int]:
        """Get article counts per category."""
        results = self.db.query(
            WikiArticle.category,
            func.count(WikiArticle.id)
        ).filter(
            WikiArticle.universe == universe,
            WikiArticle.expires_at > datetime.now(timezone.utc)
        ).group_by(
            WikiArticle.category
        ).all()
        
        return {category: count for category, count in results}
    
    def update_category_cache(self, universe: str):
        """Update category cache with current stats."""
        counts = self.get_category_counts(universe)
        
        for category, count in counts.items():
            with_images = self.db.query(func.count(WikiArticle.id)).filter(
                WikiArticle.universe == universe,
                WikiArticle.category == category,
                WikiArticle.image_cached == True,
                WikiArticle.expires_at > datetime.now(timezone.utc)
            ).scalar()
            
            cache = self.db.query(CategoryCache).filter(
                CategoryCache.universe == universe,
                CategoryCache.category == category
            ).first()
            
            if cache:
                cache.article_count = count
                cache.articles_with_images = with_images
                cache.last_updated = datetime.now(timezone.utc)
            else:
                cache = CategoryCache(
                    universe=universe,
                    category=category,
                    article_count=count,
                    articles_with_images=with_images
                )
                self.db.add(cache)
            
            self.db.commit()
        
        logger.info(f"Category cache updated for {universe}")
    
    def get_category_cache(self, universe: str) -> Dict:
        """Get cached category stats."""
        results = self.db.query(CategoryCache).filter(
            CategoryCache.universe == universe
        ).all()
        
        return {
            cache.category: {
                'count': cache.article_count,
                'with_images': cache.articles_with_images,
                'last_updated': cache.last_updated.isoformat()
            }
            for cache in results
        }
    
    # ============================================
    # IMAGE CACHE
    # ============================================
    
    def register_image(
        self,
        url: str,
        url_hash: str,
        local_path: str,
        size_bytes: Optional[int] = None,
        format: Optional[str] = None
    ) -> ImageCache:
        """Register downloaded image in database."""
        existing = self.db.query(ImageCache).filter(
            ImageCache.url_hash == url_hash
        ).first()
        
        if existing:
            existing.last_accessed = datetime.now(timezone.utc)
            existing.access_count += 1
            self.db.commit()
            return existing
        
        image = ImageCache(
            url=url,
            url_hash=url_hash,
            local_path=local_path,
            size_bytes=size_bytes,
            format=format
        )
        
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image
    
    def is_image_cached(self, url_hash: str) -> bool:
        """Check if image is in cache."""
        return self.db.query(ImageCache).filter(
            ImageCache.url_hash == url_hash,
            ImageCache.is_valid == True
        ).first() is not None
    
    def get_image_cache_stats(self) -> Dict:
        """Get image cache statistics."""
        total = self.db.query(func.count(ImageCache.id)).scalar()
        valid = self.db.query(func.count(ImageCache.id)).filter(
            ImageCache.is_valid == True
        ).scalar()
        total_size = self.db.query(func.sum(ImageCache.size_bytes)).scalar() or 0
        
        return {
            'total_images': total,
            'valid_images': valid,
            'invalid_images': total - valid,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2)
        }
    
    # ============================================
    # SCRAPING LOGS
    # ============================================
    
    def create_scraping_log(
        self,
        universe: str,
        operation_type: str
    ) -> ScrapingLog:
        """Start new scraping operation log."""
        log = ScrapingLog(
            universe=universe,
            operation_type=operation_type,
            status='running',
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        logger.info(f"Started scraping log #{log.id}: {operation_type}")
        return log
    
    def complete_scraping_log(
        self,
        log_id: int,
        stats: Dict,
        status: str = 'completed',
        error_message: Optional[str] = None # 
    ):
        """Complete scraping operation log."""
        log = self.db.query(ScrapingLog).filter(
            ScrapingLog.id == log_id
        ).first()
        
        if not log:
            logger.warning(f"Scraping log #{log_id} not found")
            return
        
        log.status = status
        log.completed_at = datetime.now(timezone.utc)
        
        if log.completed_at and log.started_at:
            completed = log.completed_at
            started = log.started_at
            if completed.tzinfo is None: completed = completed.replace(tzinfo=timezone.utc)
            if started.tzinfo is None: started = started.replace(tzinfo=timezone.utc)
            log.duration_seconds = int((completed - started).total_seconds())
        else:
            log.duration_seconds = 0
        
        log.articles_fetched = stats.get('articles_total', 0)
        log.articles_cached = (
            stats.get('articles_created', 0) + 
            stats.get('articles_updated', 0)
        )
        log.images_downloaded = stats.get('images_downloaded', 0)
        log.images_cached = stats.get('images_cached', 0)
        
      
        if error_message:
            log.errors = (log.errors or []) + [error_message]
        elif stats.get('errors'):
             log.errors = (log.errors or []) + stats.get('errors', [])
            
        try:
            self.db.commit()
            logger.info(f"✅ Scraping log #{log_id} completed: {status}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete scraping log: {e}")
    
    def get_recent_logs(
        self,
        universe: Optional[str] = None,
        limit: int = 10
    ) -> List[ScrapingLog]:
        """Get recent scraping logs."""
        query = self.db.query(ScrapingLog).order_by(
            ScrapingLog.started_at.desc()
        )
        if universe:
            query = query.filter(ScrapingLog.universe == universe)
        return query.limit(limit).all()
    
    # ============================================
    # MAINTENANCE
    # ============================================
    
    def cleanup_expired(self, universe: Optional[str] = None) -> int:
        """Delete expired articles."""
        query = self.db.query(WikiArticle).filter(
            WikiArticle.expires_at < datetime.now(timezone.utc)
        )
        if universe:
            query = query.filter(WikiArticle.universe == universe)
        count = query.count()
        query.delete()
        self.db.commit()
        logger.info(f"🗑️ Cleaned up {count} expired articles")
        return count
    
    def get_cache_stats(self, universe: str) -> Dict:
        """Get comprehensive cache statistics."""
        total_articles = self.db.query(func.count(WikiArticle.id)).filter(
            WikiArticle.universe == universe,
            WikiArticle.expires_at > datetime.now(timezone.utc)
        ).scalar()
        articles_with_images = self.db.query(func.count(WikiArticle.id)).filter(
            WikiArticle.universe == universe,
            WikiArticle.image_cached == True,
            WikiArticle.expires_at > datetime.now(timezone.utc)
        ).scalar()
        category_counts = self.get_category_counts(universe)
        image_stats = self.get_image_cache_stats()
        return {
            'universe': universe,
            'total_articles': total_articles,
            'articles_with_images': articles_with_images,
            'categories': category_counts,
            'images': image_stats
        }

    # ============================================
    # HIERARCHY/JSONB FUNCTIONS
    # ============================================

    def get_distinct_jsonb_values(
        self,
        universe: str,
        category: str,
        field: str,
        filters: Dict[str, str] = None
    ) -> List[str]:
        """Get distinct values from a JSONB field, with optional filters."""
        try:
            query = self.db.query(
                WikiArticle.content[field].astext.label("value")
            ).filter(
                WikiArticle.universe == universe,
                WikiArticle.category == category,
                WikiArticle.content.has_key(field),
                WikiArticle.expires_at > datetime.now(timezone.utc)
            )
            if filters:
                for key, value in filters.items():
                    query = query.filter(
                        WikiArticle.content.has_key(key),
                        WikiArticle.content[key].astext == value
                    )
            results = query.distinct().order_by("value").all()
            return [row.value for row in results if row.value]
        except Exception as e:
            logger.error(f"Error getting distinct JSONB values for field '{field}': {e}")
            return []

    def get_articles_by_jsonb_filters(
        self,
        universe: str,
        category: str,
        filters: Dict[str, str],
        with_images: bool = False,
        limit: int = 100
    ) -> List[WikiArticle]:
        """Get articles by filtering on JSONB content fields."""
        try:
            query = self.db.query(WikiArticle).filter(
                WikiArticle.universe == universe,
                WikiArticle.category == category,
                WikiArticle.expires_at > datetime.now(timezone.utc)
            )
            if filters:
                for key, value in filters.items():
                    query = query.filter(
                        WikiArticle.content.has_key(key),
                        WikiArticle.content[key].astext == value
                    )
            if with_images:
                query = query.filter(
                    WikiArticle.image_url != None,
                    WikiArticle.image_url != ''
                )
            return query.order_by(WikiArticle.title).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting articles by JSONB filter: {e}")
            return []