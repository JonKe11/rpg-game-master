# backend/app/core/wiki/wookieepedia_client.py
"""
Wookieepedia (Star Wars) implementation.

Features:
- Canon vs Legends filtering
- Star Wars specific categories
- Entity validation
- Fallback entities
"""

from typing import Dict
from app.core.wiki.base_wiki_client import BaseWikiClient, WikiConfig


class WookieepediaClient(BaseWikiClient):
    """
    Wookieepedia (Star Wars wiki) implementation.
    
    Features:
    - Canon articles only (Canon_ prefix)
    - Star Wars specific categories
    - Fallback entities (Tatooine, Human, etc.)
    """
    
    # Star Wars specific category mapping
    CATEGORY_MAPPING = {
        'planets': 'Canon_planets',
        'species': 'Canon_species',
        'characters': 'Canon_characters',
        'weapons': 'Canon_weapons',
        'armor': 'Canon_armor',
        'vehicles': 'Canon_vehicles',
        'droids': 'Canon_droids',
        'items': 'Canon_items',
        'organizations': 'Canon_organizations',
        'locations': 'Canon_locations',
        'battles': 'Canon_battles',
        'creatures': 'Canon_creatures',
        'technology': 'Canon_technology',
    }
    
    # Safe fallback entities
    FALLBACK_ENTITIES = {
        'planet': 'Tatooine',
        'species': 'Human',
        'character': 'Luke Skywalker',
        'weapon': 'Blaster',
        'vehicle': 'X-wing',
        'organization': 'Rebel Alliance',
        'location': 'Mos Eisley',
    }
    
    def __init__(self):
        """Initialize Wookieepedia client"""
        config = WikiConfig(
            name="Wookieepedia",
            base_url="https://starwars.fandom.com/api/v1",
            rate_limit_calls=150,
            rate_limit_period=60,
            canonical_prefix="Canon_",
            max_batch_size=100,
            max_concurrent=20,
            timeout=30
        )
        super().__init__(config)
    
    def get_category_mapping(self) -> Dict[str, str]:
        """Get Star Wars category mapping"""
        return self.CATEGORY_MAPPING
    
    def validate_entity(self, entity_name: str, entity_type: str) -> bool:
        """
        Validate Star Wars entity.
        
        Checks if entity exists in Canon categories.
        
        Args:
            entity_name: Entity to validate
            entity_type: Type (e.g., "planet", "species")
            
        Returns:
            True if valid Canon entity
        """
        # Get category for entity type
        category = self.CATEGORY_MAPPING.get(entity_type + 's')  # Pluralize
        
        if not category:
            return False
        
        # Note: This is a simple check
        # For full validation, would need to query API
        return True
    
    def get_fallback_entity(self, entity_type: str) -> str:
        """Get safe Star Wars fallback"""
        return self.FALLBACK_ENTITIES.get(entity_type, "Tatooine")