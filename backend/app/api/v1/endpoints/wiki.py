
"""
✅ WERSJA 4.0 - Używa wyłącznie PostgreSQL i nowego endpointu /search
"""
from fastapi import APIRouter, HTTPException, Query, Response, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, List
from io import BytesIO
import logging
from sqlalchemy.orm import Session
from pydantic import BaseModel


from app.services.hybrid_cache_service import HybridCacheService
from app.core.scraper.image_fetcher import ImageFetcher
from app.core.dependencies import get_db
from app.services.postgres_cache_service import PostgresCacheService
from app.models.wiki_article import WikiArticle

logger = logging.getLogger(__name__)
router = APIRouter()

image_fetcher = ImageFetcher()




class WikiArticleInfo(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_cached: bool = False
    source_url: Optional[str] = None 

    class Config:
        from_attributes = True

def format_article_info(article: WikiArticle) -> WikiArticleInfo:
    return WikiArticleInfo(
        name=article.title,
        description=article.content.get('description') if article.content else None,
        image_url=article.image_url,
        image_cached=article.image_cached,
        source_url=article.source_url
    )
    
class PaginatedSearchResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: List[WikiArticleInfo]





@router.get("/search", response_model=PaginatedSearchResponse, tags=["Wiki - Search (v3)"])
async def search_wiki_category(
    universe: str = Query("star_wars"),
    category: str = Query(..., description="Category (planets, characters, weapons, etc.)"),
    q: Optional[str] = Query(None, description="Search query (if null, returns all)"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    with_images: bool = Query(False, description="Filter for items with images only"), 
    db: Session = Depends(get_db)
):
    """
    🔍 Wyszukuje i paginuje artykuły bezpośrednio z bazy PostgreSQL.
    To jest nowy, główny endpoint do przeszukiwania całej bazy Wiki.
    """
    try:
        hybrid_service = HybridCacheService(db)
        
        
        
        search_result = hybrid_service.pg_cache.search_articles_paginated(
            universe=universe,
            category=category,
            query=q,
            limit=limit,
            offset=offset,
            with_images_only=with_images
        )
        
        
        items = [
            WikiArticleInfo(
                name=article.title,
                description=article.content.get('description') if article.content else None,
                image_url=article.image_url,
                image_cached=article.image_cached,
                source_url=article.source_url
            ) for article in search_result['items']
        ]
        
        return PaginatedSearchResponse(
            total=search_result['total_count'],
            offset=offset,
            limit=limit,
            items=items
        )
    except Exception as e:
        logger.error(f"Error during wiki search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error searching wiki data")







tree_router = APIRouter(prefix="/locations/tree", tags=["Wiki - Location Tree"])
@tree_router.get("/regions", response_model=List[str])
async def get_location_regions(universe: str = Query(default="star_wars"), db: Session = Depends(get_db)):
    pg_service = PostgresCacheService(db)
    return pg_service.get_distinct_jsonb_values(universe=universe, category="planets", field="Region")
@tree_router.get("/systems-by-region", response_model=List[str])
async def get_location_systems_by_region(region: str, universe: str = Query(default="star_wars"), db: Session = Depends(get_db)):
    pg_service = PostgresCacheService(db)
    filters = {"Region": region}
    return pg_service.get_distinct_jsonb_values(universe=universe, category="planets", field="System", filters=filters)
@tree_router.get("/planets-by-system", response_model=List[WikiArticleInfo])
async def get_planets_in_system(system: str, universe: str = Query(default="star_wars"), limit: int = Query(default=100), db: Session = Depends(get_db)):
    pg_service = PostgresCacheService(db)
    filters = {"System": system}
    articles = pg_service.get_articles_by_jsonb_filters(universe=universe, category="planets", filters=filters, with_images=True, limit=limit)
    return [format_article_info(art) for art in articles]
@tree_router.get("/on-planet", response_model=List[WikiArticleInfo])
async def get_locations_on_planet(planet: str, universe: str = Query(default="star_wars"), limit: int = Query(default=100), db: Session = Depends(get_db)):
    pg_service = PostgresCacheService(db)
    filters = {"Planet": planet}
    articles = pg_service.get_articles_by_jsonb_filters(universe=universe, category="locations", filters=filters, with_images=True, limit=limit)
    return [format_article_info(art) for art in articles]
router.include_router(tree_router)



@router.get("/image-proxy", tags=["Wiki - Utils"])
async def proxy_image(url: str):
    cache_path = image_fetcher.get_cache_path(url)
    if cache_path.exists():
        with open(cache_path, 'rb') as f: content = f.read()
        return StreamingResponse(BytesIO(content), media_type='image/png', headers={'Cache-Control': 'public, max-age=2592000', 'Access-Control-Allow-Origin': '*', 'X-Cache': 'HIT'})
    success, was_cached, content = image_fetcher.fetch_single(url)
    if not success or not content:
        return Response(status_code=404)
    return StreamingResponse(BytesIO(content), media_type='image/png', headers={'Cache-Control': 'public, max-age=2592000', 'Access-Control-Allow-Origin': '*', 'X-Cache': 'MISS'})


@router.get("/{universe}/{category}/{title}", tags=["Wiki - Utils"])
async def get_article_by_title(universe: str, category: str, title: str, db: Session = Depends(get_db)):
    postgres_cache = PostgresCacheService(db)
    title_normalized = title.replace('_', ' ')
    article = postgres_cache.get_article_by_title(title=title_normalized, universe=universe)
    if not article:
        article = postgres_cache.get_article_by_title(title=title, universe=universe)
    if not article:
        logger.warning(f"❌ Article not found: {title} in {category}")
        raise HTTPException(status_code=404, detail=f"Article '{title}' not found in category '{category}'")
    if article.category != category:
        logger.warning(f"⚠️ Category mismatch: requested {category}, found {article.category}")
    logger.info(f"✅ Found article: {article.title} (category: {article.category})")
    result = {"title": article.title, "category": article.category, "universe": article.universe, "image_url": article.image_url, "source_url": article.source_url, "scraped_at": article.scraped_at.isoformat() if article.scraped_at else None,}
    if article.content:
        result["content"] = article.content
        result["description"] = article.content.get('description', '')
    else:
        result["content"] = {}
        result["description"] = ""
    return result






