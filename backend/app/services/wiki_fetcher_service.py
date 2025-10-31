# backend/app/services/wiki_fetcher_service.py
"""
Wiki fetcher service using FANDOM API.

UPDATED: Uses new wiki client system with context extraction.
"""

import asyncio
from typing import Optional, Dict
import logging
import re

from app.core.wiki import create_wiki_client

logger = logging.getLogger(__name__)


class WikiFetcherService:
    """
    Service for fetching wiki articles with rich context.
    
    Features:
    - Fast FANDOM API access
    - Context extraction (capitals, terrain, etc.)
    - Structured data parsing
    """
    
    def __init__(self):
        """Initialize wiki fetcher"""
        pass
    
    def fetch_article(
        self, 
        article_name: str, 
        universe: str
    ) -> Optional[Dict]:
        """
        Fetch article data from wiki.
        
        Args:
            article_name: Name of article to fetch
            universe: Universe (e.g., 'star_wars')
            
        Returns:
            Article data dict or None
        """
        try:
            return asyncio.run(
                self._fetch_article_async(article_name, universe)
            )
        except RuntimeError:
            # Already in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self._fetch_article_async(article_name, universe)
            )
        except Exception as e:
            logger.error(f"Failed to fetch article {article_name}: {e}")
            return None
    
    async def _fetch_article_async(
        self, 
        article_name: str, 
        universe: str
    ) -> Optional[Dict]:
        """
        Fetch article asynchronously.
        
        Args:
            article_name: Article name
            universe: Universe name
            
        Returns:
            Article data
        """
        async with create_wiki_client(universe) as client:
            try:
                # Search for article
                response = await client._make_request(
                    "/SearchSuggestions/List",
                    params={"query": article_name, "limit": 1}
                )
                
                items = response.get("items", [])
                if not items:
                    logger.warning(f"Article not found: {article_name}")
                    return None
                
                article = items[0]
                article_id = article["id"]
                
                # Get details
                details = await client.get_article_details_batch([article_id])
                detail = details.get(str(article_id), {})
                
                return {
                    'title': article["title"],
                    'description': detail.get("abstract", ""),
                    'image_url': detail.get("thumbnail"),
                    'url': article.get("url", ""),
                    'is_canonical': True,
                    'wiki': client.config.name,
                    'info_box': {}  # Would need additional parsing
                }
            
            except Exception as e:
                logger.error(f"Error fetching {article_name}: {e}")
                return None
    
    def fetch_context_for_location(
        self,
        location_name: str,
        universe: str
    ) -> Dict:
        """
        Fetch rich context for a location (planet/moon).
        
        ✅ NEW: Extracts structured data:
        - Type (planet/moon)
        - Capital city
        - What it orbits (if moon)
        - Moons (if planet)
        - Terrain types
        
        Args:
            location_name: Location name
            universe: Universe name
            
        Returns:
            Dict with location data and structured info
        """
        try:
            return asyncio.run(
                self._fetch_context_async(location_name, universe)
            )
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self._fetch_context_async(location_name, universe)
            )
        except Exception as e:
            logger.error(f"Failed to fetch context for {location_name}: {e}")
            return {
                'location': None,
                'structured': {}
            }
    
    async def _fetch_context_async(
        self,
        location_name: str,
        universe: str
    ) -> Dict:
        """
        Fetch and parse location context asynchronously.
        
        Args:
            location_name: Location name
            universe: Universe name
            
        Returns:
            Dict with structured location data
        """
        # First fetch the article
        location_data = await self._fetch_article_async(location_name, universe)
        
        if not location_data:
            return {
                'location': None,
                'structured': {}
            }
        
        # Extract structured info from description
        structured = self._extract_structured_info(
            location_data.get('description', ''),
            location_name
        )
        
        return {
            'location': location_data,
            'structured': structured
        }
    
    def _extract_structured_info(self, description: str, location_name: str) -> Dict:
        """
        Extract structured information from description text.
        
        Looks for:
        - Type (planet/moon/city)
        - Capital
        - Orbits (for moons)
        - Moons (for planets)
        - Terrain
        
        Args:
            description: Article description
            location_name: Name of location
            
        Returns:
            Dict with structured data
        """
        structured = {}
        
        if not description:
            return structured
        
        desc_lower = description.lower()
        
        # 1. Determine type (planet vs moon)
        if 'moon' in desc_lower and location_name.lower() in desc_lower:
            # Check if it's described as A moon
            moon_patterns = [
                f'{location_name.lower()},? (?:a|the) moon',
                f'(?:a|the) moon (?:called|named) {location_name.lower()}',
                f'{location_name.lower()} (?:is|was) (?:a|the) moon',
            ]
            
            for pattern in moon_patterns:
                if re.search(pattern, desc_lower):
                    structured['type'] = 'moon'
                    break
        
        # Default to planet if not identified as moon
        if 'type' not in structured:
            if 'planet' in desc_lower or 'world' in desc_lower:
                structured['type'] = 'planet'
            else:
                structured['type'] = 'location'  # Generic
        
        # 2. Extract capital (if mentioned)
        capital_patterns = [
            r'capital(?:\s+city)?\s+(?:is|was|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+the capital',
            r'capital.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+is',
        ]
        
        for pattern in capital_patterns:
            matches = re.findall(pattern, description)
            if matches:
                structured['capital'] = matches[0]
                break
        
        # 3. Extract what it orbits (if moon)
        if structured.get('type') == 'moon':
            orbit_patterns = [
                r'orbit(?:s|ing)?\s+(?:the\s+)?(?:planet\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'(?:of|around)\s+(?:the\s+)?(?:planet\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'moon\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            ]
            
            for pattern in orbit_patterns:
                matches = re.findall(pattern, description)
                for match in matches:
                    # Skip if it's the location itself
                    if match.lower() != location_name.lower():
                        structured['orbits'] = match
                        break
                if 'orbits' in structured:
                    break
        
        # 4. Extract moons (if planet)
        if structured.get('type') == 'planet':
            moon_patterns = [
                r'moon(?:s)?\s+(?:called|named|including)\s+([A-Z][a-z]+(?:,?\s+(?:and\s+)?[A-Z][a-z]+)*)',
                r'([A-Z][a-z]+(?:,?\s+(?:and\s+)?[A-Z][a-z]+)*),?\s+its moon',
            ]
            
            for pattern in moon_patterns:
                matches = re.findall(pattern, description)
                if matches:
                    moon_text = matches[0]
                    # Split by comma and 'and'
                    moons = re.split(r',\s*(?:and\s+)?|\s+and\s+', moon_text)
                    moons = [m.strip() for m in moons if m.strip()]
                    if moons:
                        structured['moons'] = moons
                    break
        
        # 5. Extract terrain
        terrain_keywords = [
            'desert', 'forest', 'jungle', 'ice', 'snow', 'mountain',
            'ocean', 'swamp', 'urban', 'volcanic', 'grassland', 'tundra',
            'canyon', 'mesa', 'plains', 'hills', 'wasteland'
        ]
        
        found_terrain = []
        for terrain in terrain_keywords:
            if terrain in desc_lower:
                found_terrain.append(terrain)
        
        if found_terrain:
            structured['terrain'] = found_terrain
        
        return structured