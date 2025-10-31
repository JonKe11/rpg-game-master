# backend/app/core/wiki/memory_alpha_client.py
"""
Memory Alpha (Star Trek) implementation.

Different from Wookieepedia:
- No Canon/Legends split
- Different category names
- Different entity validation
"""

from typing import Dict
from app.core.wiki.base_wiki_client import BaseWikiClient, WikiConfig


class MemoryAlphaClient(BaseWikiClient):
    """
    Memory Alpha (Star Trek wiki) implementation.
    
    Differences from Wookieepedia:
    - No Canon prefix (all articles are canon)
    - Different category structure
    - Star Trek specific entities
    """
    
    # Star Trek category mapping
    CATEGORY_MAPPING = {
        'planets': 'Planets',
        'species': 'Species',
        'characters': 'Individuals',
        'weapons': 'Weapons',
        'vehicles': 'Starships',
        'organizations': 'Organizations',
        'locations': 'Locations',
        'technology': 'Technology',
    }
    
    # Safe fallback entities
    FALLBACK_ENTITIES = {
        'planet': 'Earth',
        'species': 'Human',
        'character': 'James T. Kirk',
        'weapon': 'Phaser',
        'vehicle': 'USS Enterprise',
        'organization': 'Starfleet',
    }
    
    def __init__(self):
        """Initialize Memory Alpha client"""
        config = WikiConfig(
            name="Memory Alpha",
            base_url="https://memory-alpha.fandom.com/api/v1",
            rate_limit_calls=150,
            rate_limit_period=60,
            canonical_prefix="",  # No prefix - all canon!
            max_batch_size=100,
            max_concurrent=20,
            timeout=30
        )
        super().__init__(config)
    
    def get_category_mapping(self) -> Dict[str, str]:
        """Get Star Trek category mapping"""
        return self.CATEGORY_MAPPING
    
    def validate_entity(self, entity_name: str, entity_type: str) -> bool:
        """Validate Star Trek entity"""
        category = self.CATEGORY_MAPPING.get(entity_type + 's')
        return category is not None
    
    def get_fallback_entity(self, entity_type: str) -> str:
        """Get safe Star Trek fallback"""
        return self.FALLBACK_ENTITIES.get(entity_type, "Earth")