# backend/app/core/wiki/wiki_factory.py
"""
Wiki factory for creating wiki clients.
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class WikiConfig:
    """Configuration for a wiki"""
    name: str
    base_url: str
    api_path: str
    
    # Category mappings
    category_map: Dict[str, str]


# ============================================
# WIKI CONFIGURATIONS
# ============================================

WIKI_CONFIGS = {
    'star_wars': WikiConfig(
        name='Wookieepedia',
        base_url='https://starwars.fandom.com',
        api_path='/api/v1',
        category_map={
            # CORRECTED: Actual Wookieepedia category names (without "Canon_" prefix)
            'planets': 'Planets',                    # Generic category
            'species': 'Sentient_species',           # Not "Species"!
            'characters': 'Individuals',             # Not "Characters"!
            'weapons': 'Weapons',
            'armor': 'Armor',
            'vehicles': 'Vehicles',
            'droids': 'Droid_models',               # Not "Droids"!
            'items': 'Technology',                   # Broad category
            'organizations': 'Organizations',
            'locations': 'Locations',
            'battles': 'Battles',
            'creatures': 'Creatures',
            'technology': 'Technology'
        }
    ),
    
    'star_trek': WikiConfig(
        name='Memory Alpha',
        base_url='https://memory-alpha.fandom.com',
        api_path='/api/v1',
        category_map={
            'planets': 'Planets',
            'species': 'Species',
            'characters': 'Individuals',
            'weapons': 'Weapons',
            'armor': 'Protective_gear',
            'vehicles': 'Spacecraft',
            'technology': 'Technology',
            'organizations': 'Organizations',
            'locations': 'Locations'
        }
    ),
    
    'lotr': WikiConfig(
        name='Tolkien Gateway',
        base_url='https://lotr.fandom.com',
        api_path='/api/v1',
        category_map={
            'planets': 'Realms',
            'species': 'Races',
            'characters': 'Characters',
            'weapons': 'Weapons',
            'armor': 'Armour',
            'vehicles': 'Vehicles',
            'items': 'Items',
            'organizations': 'Organizations',
            'locations': 'Locations',
            'creatures': 'Creatures'
        }
    )
}


def create_wiki_client(universe: str):
    """
    Create wiki client for universe.
    
    Args:
        universe: Universe identifier (e.g., 'star_wars')
        
    Returns:
        Wiki client instance
        
    Raises:
        ValueError: If universe not supported
    """
    if universe not in WIKI_CONFIGS:
        raise ValueError(
            f"Unsupported universe: {universe}. "
            f"Available: {list(WIKI_CONFIGS.keys())}"
        )
    
    config = WIKI_CONFIGS[universe]
    
    # Import here to avoid circular imports
    from app.core.wiki.base_wiki_client import BaseWikiClient
    
    return BaseWikiClient(config)