# backend/app/api/v1/endpoints/wiki.py
"""
Wiki API Endpoints with Unified Cache.

Features:
- Planets, species, items with images
- Unified cache (consistent across app)
- Image prefetching with parallel downloads
- Cache management endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, List
from io import BytesIO
import logging

from app.services.unified_cache_service import UnifiedCacheService
from app.core.scraper.image_fetcher import ImageFetcher

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (singletons)
cache_service = UnifiedCacheService()
image_fetcher = ImageFetcher()


# ============================================
# HELPER: Fetch single image for endpoint
# ============================================

def fetch_single_image_for_endpoint(args: tuple) -> tuple:
    """
    Helper for parallel image fetching in endpoints.
    
    Args:
        args: (name, image_url, index, total)
        
    Returns:
        (name, success, was_cached)
    """
    name, image_url, idx, total = args
    
    if not image_url:
        return (name, False, False)
    
    success, was_cached, content = image_fetcher.fetch_single(image_url)
    
    # Log progress
    if success and was_cached:
        logger.info(f"  ✅ [{idx:3d}/{total}] {name[:40]:40s} - cached")
    elif success:
        size_kb = len(content) / 1024 if content else 0
        logger.info(f"  💾 [{idx:3d}/{total}] {name[:40]:40s} - {size_kb:6.1f}KB")
    else:
        logger.info(f"  ❌ [{idx:3d}/{total}] {name[:40]:40s} - failed")
    
    return (name, success, was_cached)


# ============================================
# IMAGE PROXY
# ============================================

@router.get("/image-proxy")
async def proxy_image(url: str):
    """
    Proxy for Fandom images (bypasses CORS).
    Uses file cache for persistence.
    """
    cache_path = image_fetcher.get_cache_path(url)
    
    # Check cache
    if cache_path.exists():
        with open(cache_path, 'rb') as f:
            content = f.read()
        
        return StreamingResponse(
            BytesIO(content),
            media_type='image/png',
            headers={
                'Cache-Control': 'public, max-age=2592000',
                'Access-Control-Allow-Origin': '*',
                'X-Cache': 'HIT'
            }
        )
    
    # Fetch from source
    success, was_cached, content = image_fetcher.fetch_single(url)
    
    if not success or not content:
        return Response(status_code=404)
    
    return StreamingResponse(
        BytesIO(content),
        media_type='image/png',
        headers={
            'Cache-Control': 'public, max-age=2592000',
            'Access-Control-Allow-Origin': '*',
            'X-Cache': 'MISS'
        }
    )


# ============================================
# CANON DATA
# ============================================

@router.get("/canon/all")
async def get_all_canon_data(
    universe: str = Query(default="star_wars"),
    force_refresh: bool = Query(default=False)
):
    """Get all categorized canon data."""
    if force_refresh:
        cache_service.force_refresh_all(universe)
    
    data = cache_service.get_all_data(universe)
    total_items = sum(len(items) for items in data.values())
    
    return {
        'universe': universe,
        'total_items': total_items,
        'categories': len(data),
        'data': data
    }


@router.get("/canon/summary")
async def get_canon_summary(universe: str = Query(default="star_wars")):
    """Get summary of canon data."""
    summary = cache_service.get_summary(universe)
    
    return {
        'universe': universe,
        'total_items': sum(summary.values()),
        'categories': summary
    }


@router.get("/canon/category/{category}")
async def get_canon_category(
    category: str,
    universe: str = Query(default="star_wars"),
    limit: int = Query(default=100, le=5000),
    offset: int = Query(default=0),
    search: Optional[str] = Query(default=None)
):
    """Get items from specific category."""
    data = cache_service.get_all_data(universe)
    
    if category not in data:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    
    items = data[category]
    
    if search:
        search_lower = search.lower()
        items = [item for item in items if search_lower in item.lower()]
    
    total = len(items)
    paginated_items = items[offset:offset+limit]
    
    return {
        'category': category,
        'universe': universe,
        'total': total,
        'offset': offset,
        'limit': limit,
        'returned': len(paginated_items),
        'items': paginated_items
    }


# ============================================
# LOCATIONS (PLANETS)
# ============================================

@router.get("/locations/planets")
async def get_planets_with_images(
    universe: str = Query(default="star_wars"),
    limit: int = Query(default=100, le=2000),
    prefetch: bool = Query(default=True),
    parallel: bool = Query(default=True),
    workers: int = Query(default=15, ge=1, le=30)
):
    """
    Get planets WITH parallel image prefetch.
    
    ✅ FIXED: Now uses 'planets' category (not 'locations'!)
    """
    logger.info(f"\n🌍 Fetching {limit} planets with images...")
    
    # ✅ FIX: Use get_planets() from UnifiedCache (not 'locations'!)
    planets_data = cache_service.get_planets(
        universe=universe,
        limit=limit,
        with_images=True
    )
    
    logger.info(f"✅ Step 1/2 complete: {len(planets_data)} planets processed\n")
    
    # Prefetch images
    if prefetch:
        tasks = [
            (p['name'], p.get('image_url'), idx + 1, len(planets_data))
            for idx, p in enumerate(planets_data)
            if p.get('image_url')
        ]
        
        if not tasks:
            logger.warning("⚠️ No images to fetch")
        elif parallel:
            logger.info(f"🚀 Step 2/2: PARALLEL image prefetch ({workers} workers)")
            logger.info(f"📦 {len(tasks)} images to process\n")
            
            stats = image_fetcher.fetch_batch_parallel(
                tasks,
                max_workers=workers,
                show_progress=True
            )
            
            logger.info(f"\n✅ Step 2/2 complete!")
            logger.info(f"   💾 Downloaded: {stats['downloaded']}")
            logger.info(f"   ✅ Cached: {stats['cached']}")
            logger.info(f"   ❌ Failed: {stats['failed']}")
        else:
            # Sequential
            logger.info(f"📥 Step 2/2: Sequential image prefetch\n")
            
            for task in tasks:
                fetch_single_image_for_endpoint(task)
    
    logger.info(f"\n🎉 All done! Returning {len(planets_data)} planets\n")
    
    return {
        'universe': universe,
        'total': len(planets_data),
        'planets': planets_data
    }


@router.get("/locations/by-planet")
async def get_locations_by_planet(
    universe: str = Query(default="star_wars"),
    planet: str = Query(...),
    limit: int = Query(default=500, le=5000)
):
    """
    Get specific locations ON a planet.
    
    Note: This uses 'locations' category (cities, bases, etc).
    """
    # Use locations category (not planets!)
    all_locations = cache_service.get_locations(universe=universe)
    
    planet_locations = [
        loc for loc in all_locations 
        if planet.lower() in loc.lower()
    ]
    
    return {
        'universe': universe,
        'planet': planet,
        'total': len(planet_locations),
        'locations': planet_locations[:limit]
    }


# ============================================
# ITEMS
# ============================================

@router.get("/items/all")
async def get_all_items_summary(universe: str = Query(default="star_wars")):
    """Get summary of all item categories."""
    return {
        'universe': universe,
        'categories': {
            'weapons': {
                'count': len(cache_service.get_weapons(universe)),
                'sample': cache_service.get_weapons(universe)[:5]
            },
            'armor': {
                'count': len(cache_service.get_armor(universe)),
                'sample': cache_service.get_armor(universe)[:5]
            },
            'items': {
                'count': len(cache_service.get_items(universe)),
                'sample': cache_service.get_items(universe)[:5]
            },
            'vehicles': {
                'count': len(cache_service.get_vehicles(universe)),
                'sample': cache_service.get_vehicles(universe)[:5]
            },
            'droids': {
                'count': len(cache_service.get_droids(universe)),
                'sample': cache_service.get_droids(universe)[:5]
            }
        }
    }


@router.get("/items/category/{category}")
async def get_items_by_category(
    category: str,
    universe: str = Query(default="star_wars"),
    limit: int = Query(default=50, le=1000),
    offset: int = Query(default=0),
    search: Optional[str] = Query(default=None)
):
    """Get items from category (without images - fast)."""
    valid_categories = ['weapons', 'armor', 'items', 'vehicles', 'droids']
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid: {valid_categories}"
        )
    
    # Get from unified cache
    getter_map = {
        'weapons': cache_service.get_weapons,
        'armor': cache_service.get_armor,
        'items': cache_service.get_items,
        'vehicles': cache_service.get_vehicles,
        'droids': cache_service.get_droids
    }
    
    all_items = getter_map[category](universe)
    
    # Convert to list of names
    if all_items and isinstance(all_items[0], dict):
        all_items = [item['name'] for item in all_items]
    
    if search:
        search_lower = search.lower()
        all_items = [item for item in all_items if search_lower in item.lower()]
    
    total = len(all_items)
    paginated_items = all_items[offset:offset+limit]
    
    return {
        'category': category,
        'universe': universe,
        'total': total,
        'offset': offset,
        'limit': limit,
        'returned': len(paginated_items),
        'items': paginated_items
    }


@router.get("/items/category/{category}/with-images")
async def get_items_with_images(
    category: str,
    universe: str = Query(default="star_wars"),
    limit: int = Query(default=50, le=1000),
    offset: int = Query(default=0),
    search: Optional[str] = Query(default=None),
    prefetch: bool = Query(default=True),
    parallel: bool = Query(default=True),
    workers: int = Query(default=15, ge=1, le=30)
):
    """Get items WITH parallel image prefetch."""
    valid_categories = ['weapons', 'armor', 'items', 'vehicles', 'droids']
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid: {valid_categories}"
        )
    
    logger.info(f"\n🎒 Fetching {category}...")
    
    # Get from unified cache with images
    getter_map = {
        'weapons': cache_service.get_weapons,
        'armor': cache_service.get_armor,
        'items': cache_service.get_items,
        'vehicles': cache_service.get_vehicles,
        'droids': cache_service.get_droids
    }
    
    all_items = getter_map[category](universe, with_images=True)
    
    # Search filter
    if search:
        search_lower = search.lower()
        all_items = [item for item in all_items if search_lower in item['name'].lower()]
    
    # Pagination
    total = len(all_items)
    items_with_images = all_items[offset:offset+limit]
    
    logger.info(f"✅ Step 1/2 complete: {len(items_with_images)} items\n")
    
    # Prefetch images
    if prefetch:
        tasks = [
            (i['name'], i.get('image_url'), idx + 1, len(items_with_images))
            for idx, i in enumerate(items_with_images)
            if i.get('image_url')
        ]
        
        if tasks and parallel:
            logger.info(f"🚀 Step 2/2: PARALLEL image prefetch ({workers} workers)")
            logger.info(f"📦 {len(tasks)} images\n")
            
            stats = image_fetcher.fetch_batch_parallel(
                tasks,
                max_workers=workers,
                show_progress=True
            )
            
            logger.info(f"\n✅ Step 2/2 complete: ↓{stats['downloaded']} ✓{stats['cached']} ✗{stats['failed']}")
    
    logger.info(f"\n🎉 Done!\n")
    
    return {
        'category': category,
        'universe': universe,
        'total': total,
        'offset': offset,
        'limit': limit,
        'returned': len(items_with_images),
        'items': items_with_images
    }


# ============================================
# CACHE MANAGEMENT
# ============================================

@router.get("/cache/stats")
async def get_cache_stats(universe: str = Query(default="star_wars")):
    """Get cache statistics."""
    cache_info = cache_service.get_cache_info(universe)
    
    return cache_info


@router.post("/cache/invalidate")
async def invalidate_cache(
    universe: str = Query(default="star_wars"),
    clear_images: bool = Query(default=False)
):
    """Force cache refresh."""
    cache_service.force_refresh_all(universe)
    
    result = {'status': 'invalidated', 'universe': universe}
    
    if clear_images:
        deleted = image_fetcher.clear_cache()
        result['images_deleted'] = deleted
    
    return result