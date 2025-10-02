# backend/app/api/v1/endpoints/wiki.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any
from pydantic import BaseModel
from app.services.scraper_service import ScraperService

router = APIRouter()

# Pydantic models dla responses
class CategoryResponse(BaseModel):
    universe: str
    category: str
    count: int
    items: List[str]

class EntitySearchResponse(BaseModel):
    entity: str
    url: str

@router.get("/categories/{universe}/{category}", response_model=CategoryResponse)
async def get_category_items(
    universe: str,
    category: str,
    search: str = Query(None, description="Search query to filter results"),
    limit: int = Query(200, ge=1, le=500)
):
    """Pobiera listę elementów z danej kategorii wiki"""
    scraper_service = ScraperService()
    
    # Walidacja uniwersum
    valid_universes = ['star_wars', 'lotr', 'harry_potter']
    if universe not in valid_universes:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid universe. Must be one of: {valid_universes}"
        )
    
    # Walidacja kategorii
    valid_categories = ['species', 'planets', 'organizations', 'colors', 'genders']
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {valid_categories}"
        )
    
    try:
        if search:
            items = scraper_service.search_category(universe, category, search)
        else:
            items = scraper_service.get_category_list(universe, category, limit)
        
        return CategoryResponse(
            universe=universe,
            category=category,
            count=len(items),
            items=items
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching category data: {str(e)}"
        )

@router.get("/search/{entity_name}", response_model=EntitySearchResponse)
async def search_entity(
    entity_name: str,
    universe: str = "star_wars"
):
    """Wyszukuje encję w wiki"""
    scraper_service = ScraperService()
    
    url = scraper_service.search_entity(entity_name, universe)
    if not url:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return EntitySearchResponse(entity=entity_name, url=url)

@router.get("/data/{entity_name}")
async def get_entity_data(
    entity_name: str,
    universe: str = "star_wars"
) -> Dict[str, Any]:
    """Pobiera pełne dane o encji z wiki"""
    scraper_service = ScraperService()
    
    try:
        data = scraper_service.get_entity_data(entity_name, universe)
        
        # Dodatkowe mapowanie dla formularza
        if data.get('info'):
            info = data['info']
            
            # Wyciągnij rok urodzenia i erę
            if 'born' in info:
                born_str = str(info['born'])
                if 'BBY' in born_str or 'ABY' in born_str:
                    import re
                    match = re.search(r'(\d+)\s*(BBY|ABY)', born_str)
                    if match:
                        data['born_year'] = int(match.group(1))
                        data['born_era'] = match.group(2)
            
            # Mapuj specyficzne pola
            data['homeworld'] = info.get('homeworld', '')
            data['gender'] = info.get('gender', '')
            data['height_cm'] = info.get('height', '')
            data['mass_kg'] = info.get('mass', '')
            data['skin_color'] = info.get('skin_color', info.get('skin', ''))
            data['eye_color'] = info.get('eye_color', info.get('eyes', ''))
            data['hair_color'] = info.get('hair_color', info.get('hair', ''))
        
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/planet/{planet_name}")
async def get_planet_data(
    planet_name: str,
    universe: str = "star_wars"
) -> Dict[str, Any]:
    """Pobiera szczegółowe dane o planecie"""
    scraper_service = ScraperService()
    
    try:
        data = scraper_service.get_planet_info(planet_name, universe)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/affiliation/{affiliation_name}")
async def get_affiliation_data(
    affiliation_name: str,
    universe: str = "star_wars"
) -> Dict[str, Any]:
    """Pobiera dane o organizacji/afilacji"""
    scraper_service = ScraperService()
    
    try:
        data = scraper_service.get_affiliation_info(affiliation_name, universe)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/clear-cache")
async def clear_wiki_cache() -> Dict[str, str]:
    """Czyści cache scrapowanych danych"""
    scraper_service = ScraperService()
    scraper_service.clear_cache()
    return {"message": "Cache cleared successfully"}

@router.get("/canon/{universe}")
async def get_canon_elements(universe: str = "star_wars") -> Dict[str, Any]:
    """Pobiera podstawowe kanoniczne elementy dla uniwersum"""
    scraper_service = ScraperService()
    return scraper_service.get_canon_elements(universe)