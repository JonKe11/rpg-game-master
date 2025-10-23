
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from fastapi.responses import StreamingResponse
from app.services.scraper_service import ScraperService
import requests
from io import BytesIO
router = APIRouter()

# ============================================
# CHARACTER DATA ENDPOINTS (dla scrapowania pojedynczych postaci)
# ============================================

@router.get("/image-proxy")
async def proxy_image(url: str):
    """
    Proxy dla obrazków z Fandom (omija CORS)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        return StreamingResponse(
            BytesIO(response.content),
            media_type=response.headers.get('content-type', 'image/png'),
            headers={
                'Cache-Control': 'public, max-age=604800',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        print(f"Image proxy error: {e}")
        return Response(status_code=404)


@router.get("/search/{entity_name}")
async def search_entity(
    entity_name: str,
    universe: str = "star_wars"
):
    """Search for specific entity in wiki"""
    scraper_service = ScraperService()
    
    url = scraper_service.search_entity(entity_name, universe)
    if not url:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return {"entity": entity_name, "url": url}

@router.get("/data/{entity_name}")
async def get_entity_data(
    entity_name: str,
    universe: str = "star_wars"
):
    """Get full entity data from wiki (with scraping)"""
    scraper_service = ScraperService()
    
    try:
        data = scraper_service.get_entity_data(entity_name, universe)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ============================================
# CANON DATA ENDPOINTS (NOWY SYSTEM!)
# ============================================

@router.get("/canon/all")
async def get_all_canon_data(
    universe: str = Query(default="star_wars", description="Universe to fetch data from"),
    force_refresh: bool = Query(default=False, description="Force cache refresh")
):
    """
    Get ALL categorized canon data (58k+ items)
    
    Uses cache (7 day TTL) unless force_refresh=true
    
    Response time:
    - First call: ~2-3 minutes (one-time setup)
    - Cached calls: <100ms
    
    Returns 15 categories:
    - characters, species, organizations
    - planets, locations, battles, events
    - weapons, armor, items, vehicles, droids
    - technology, creatures, abilities
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(
        universe=universe,
        depth=3,
        force_refresh=force_refresh
    )
    
    return {
        'universe': universe,
        'total_items': sum(len(items) for items in data.values()),
        'categories': {k: len(v) for k, v in data.items()},
        'data': data
    }

@router.get("/canon/summary")
async def get_canon_summary(
    universe: str = Query(default="star_wars")
):
    """
    Get just category counts (lightweight)
    
    Perfect for checking what's available without loading full data
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
    
    return {
        'universe': universe,
        'total_items': sum(len(items) for items in data.values()),
        'categories': {k: len(v) for k, v in data.items() if v}
    }

@router.get("/canon/category/{category}")
async def get_canon_by_category(
    category: str,
    universe: str = Query(default="star_wars"),
    limit: Optional[int] = Query(default=None, description="Max items to return"),
    offset: int = Query(default=0, description="Pagination offset"),
    search: Optional[str] = Query(default=None, description="Filter by name (case-insensitive)")
):
    """
    Get items from specific category
    
    Available categories:
    - characters, species, organizations
    - planets, locations, battles, events
    - weapons, armor, items, vehicles, droids
    - technology, creatures, abilities
    
    Supports:
    - Pagination (limit/offset)
    - Search filtering
    
    Examples:
    - /canon/category/weapons?limit=50&offset=0
    - /canon/category/planets?search=tatooine
    - /canon/category/species?limit=100&offset=100
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
    
    if category not in data:
        available = list(data.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category '{category}'. Available categories: {available}"
        )
    
    items = data[category]
    
    # Search filter
    if search:
        search_lower = search.lower()
        items = [item for item in items if search_lower in item.lower()]
    
    # Pagination
    total = len(items)
    if limit:
        items = items[offset:offset+limit]
    else:
        items = items[offset:]
    
    return {
        'category': category,
        'universe': universe,
        'total': total,
        'offset': offset,
        'limit': limit,
        'returned': len(items),
        'items': items
    }

# ============================================
# FAZA 2: GM TOOLS - Location System
# ============================================

@router.get("/locations/planets")
async def get_planets_with_images(
    universe: str = Query(default="star_wars"),
    limit: int = Query(default=100, le=500)
):
    """
    Get planets for GM Location System (Faza 2)
    
    Returns:
    - Planet names
    - Image URLs (INFOBOX IMAGE from wiki!)
    - Brief descriptions
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
    
    planets = data['planets'][:limit]
    
    # Scrape images for each planet (ONLY INFOBOX IMAGE!)
    planets_with_images = []
    for idx, planet_name in enumerate(planets):
        print(f"Fetching planet {idx+1}/{len(planets)}: {planet_name}")
        
        try:
            planet_data = scraper_service.get_entity_data(planet_name, universe)
            
            # Get ONLY infobox image (pierwsze zdjęcie po prawej)
            image_url = planet_data.get('image_url')  # Ta metoda już pobiera infobox image!
            
            planets_with_images.append({
                'name': planet_name,
                'image_url': image_url,  # Z infoboxa
                'description': planet_data.get('description', '')[:200] if planet_data.get('description') else None
            })
        except Exception as e:
            print(f"Error fetching {planet_name}: {e}")
            planets_with_images.append({
                'name': planet_name,
                'image_url': None,
                'description': None
            })
    
    return {
        'universe': universe,
        'total': len(planets_with_images),
        'planets': planets_with_images
    }

@router.get("/locations/by-planet")
async def get_locations_by_planet(
    universe: str = Query(default="star_wars"),
    planet: Optional[str] = Query(default=None, description="Filter by planet name"),
    limit: int = Query(default=500, le=2000)
):
    """
    Get all locations (optionally filtered by planet)
    
    Examples:
    - /locations/by-planet?planet=Tatooine
    - /locations/by-planet (all locations)
    
    Used by: GM Location dropdown
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
    
    locations = data['locations']
    
    # Filter by planet if specified
    if planet:
        locations = [
            loc for loc in locations 
            if planet.lower() in loc.lower()
        ]
    
    return {
        'universe': universe,
        'planet_filter': planet,
        'total': len(locations),
        'locations': locations[:limit]
    }

# ============================================
# FAZA 3: INVENTORY - Item Browser
# ============================================

@router.get("/items/all")
async def get_all_items_categorized(
    universe: str = Query(default="star_wars")
):
    """
    Get ALL items categorized for Item Browser (FAZA 3)
    
    Returns:
    - weapons (1200+)
    - armor (300+)
    - items (4000+)
    - vehicles (2000+)
    - droids (400+)
    
    Used by: Item Browser initial load
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
    
    return {
        'universe': universe,
        'categories': {
            'weapons': {
                'count': len(data['weapons']),
                'items': data['weapons']
            },
            'armor': {
                'count': len(data['armor']),
                'items': data['armor']
            },
            'items': {
                'count': len(data['items']),
                'items': data['items']
            },
            'vehicles': {
                'count': len(data['vehicles']),
                'items': data['vehicles']
            },
            'droids': {
                'count': len(data['droids']),
                'items': data['droids']
            }
        }
    }

@router.get("/items/category/{category}")
async def get_items_by_category(
    category: str,
    universe: str = Query(default="star_wars"),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
    search: Optional[str] = Query(default=None),
    with_images: bool = Query(default=False, description="Scrape images (slower!)")
):
    """
    Get items from specific category
    
    Categories: weapons, armor, items, vehicles, droids
    
    If with_images=true, scrapes image URLs from wiki (much slower!)
    
    Used by: Item Browser with category filtering
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
    
    valid_categories = ['weapons', 'armor', 'items', 'vehicles', 'droids']
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Valid: {valid_categories}"
        )
    
    items = data[category]
    
    # Search filter
    if search:
        search_lower = search.lower()
        items = [item for item in items if search_lower in item.lower()]
    
    # Pagination
    total = len(items)
    paginated_items = items[offset:offset+limit]
    
    # Optionally scrape images
    if with_images:
        items_with_images = []
        for item_name in paginated_items:
            try:
                item_data = scraper_service.get_entity_data(item_name, universe)
                items_with_images.append({
                    'name': item_name,
                    'image_url': item_data.get('image_url'),
                    'description': item_data.get('description', '')[:200]
                })
            except Exception:
                items_with_images.append({
                    'name': item_name,
                    'image_url': None,
                    'description': None
                })
        
        return {
            'category': category,
            'universe': universe,
            'total': total,
            'offset': offset,
            'limit': limit,
            'returned': len(items_with_images),
            'items': items_with_images
        }
    else:
        return {
            'category': category,
            'universe': universe,
            'total': total,
            'offset': offset,
            'limit': limit,
            'returned': len(paginated_items),
            'items': paginated_items
        }

@router.get("/items/popular/{category}")
async def get_popular_items(
    category: str,
    universe: str = Query(default="star_wars"),
    limit: int = Query(default=20, le=100)
):
    """
    Get "popular" items from category (first N items)
    
    Perfect for quick suggestions/autocomplete
    
    Used by: Item search autocomplete
    """
    scraper_service = ScraperService()
    data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
    
    valid_categories = ['weapons', 'armor', 'items', 'vehicles', 'droids']
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Valid: {valid_categories}"
        )
    
    items = data[category][:limit]
    
    return {
        'category': category,
        'universe': universe,
        'count': len(items),
        'items': items
    }

# ============================================
# CACHE MANAGEMENT
# ============================================

@router.post("/cache/invalidate")
async def invalidate_cache(
    universe: str = Query(default="star_wars")
):
    """
    Force cache refresh
    
    Next request will fetch fresh data from wiki (~2-3 minutes)
    """
    scraper_service = ScraperService()
    scraper_service.scraper.canon_cache.invalidate(universe, depth=3)
    
    return {
        'success': True,
        'message': f'Cache invalidated for {universe}',
        'note': 'Next request will fetch fresh data (~2-3 minutes)'
    }

@router.get("/cache/stats")
async def get_cache_stats(
    universe: str = Query(default="star_wars")
):
    """
    Get cache metadata
    
    Shows:
    - Cache age
    - Expiration time
    - Total items
    - Category breakdown
    """
    scraper_service = ScraperService()
    stats = scraper_service.scraper.canon_cache.get_stats(universe, depth=3)
    
    if not stats:
        return {
            'cached': False,
            'message': 'No cache available',
            'note': 'First request will take ~2-3 minutes to build cache'
        }
    
    from datetime import datetime
    created = datetime.fromisoformat(stats['created_at'])
    expires = datetime.fromisoformat(stats['expires_at'])
    age = datetime.now() - created
    remaining = expires - datetime.now()
    
    return {
        'cached': True,
        'created_at': stats['created_at'],
        'expires_at': stats['expires_at'],
        'age_hours': round(age.total_seconds() / 3600, 1),
        'remaining_hours': round(remaining.total_seconds() / 3600, 1),
        'ttl_days': stats['ttl_days'],
        'total_items': stats['total_items'],
        'categories': stats['categories']
    }
    
@router.get("/items/category/{category}/with-images")
async def get_items_with_images(
        category: str,
        universe: str = Query(default="star_wars"),
        limit: int = Query(default=50, le=200),
        offset: int = Query(default=0),
        search: Optional[str] = Query(default=None)
    ):
        """
        Get items from specific category WITH IMAGES
        
        Categories: weapons, armor, items, vehicles, droids
        
        Returns items with:
        - Name
        - Image URL (from wiki infobox)
        - Description
        
        Used by: GM Item Browser with images
        """
        scraper_service = ScraperService()
        data = scraper_service.scraper.get_canon_categorized_data(universe=universe)
        
        valid_categories = ['weapons', 'armor', 'items', 'vehicles', 'droids']
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category '{category}'. Valid: {valid_categories}"
            )
        
        items = data[category]
        
        # Search filter
        if search:
            search_lower = search.lower()
            items = [item for item in items if search_lower in item.lower()]
        
        # Pagination
        total = len(items)
        paginated_items = items[offset:offset+limit]
        
        # Scrape images for items
        items_with_images = []
        for idx, item_name in enumerate(paginated_items):
            print(f"Fetching item {idx+1}/{len(paginated_items)}: {item_name}")
            
            try:
                item_data = scraper_service.get_entity_data(item_name, universe)
                
                items_with_images.append({
                    'name': item_name,
                    'image_url': item_data.get('image_url'),  # Infobox image
                    'description': item_data.get('description', '')[:200] if item_data.get('description') else None
                })
            except Exception as e:
                print(f"Error fetching {item_name}: {e}")
                items_with_images.append({
                    'name': item_name,
                    'image_url': None,
                    'description': None
                })
        
        return {
            'category': category,
            'universe': universe,
            'total': total,
            'offset': offset,
            'limit': limit,
            'returned': len(items_with_images),
            'items': items_with_images
        }