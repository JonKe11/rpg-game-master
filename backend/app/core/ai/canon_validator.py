# backend/app/core/ai/canon_validator.py
"""
Dynamic canon validation using wiki cache as source of truth.

UPDATED: Works with new FANDOM API system.
Maintains backward compatibility.
"""

from typing import Set, List, Dict, Optional
import logging

from app.core.scraper.wiki_content_cache import WikiContentCache
from app.core.scraper.wiki_scraper import WikiScraper

logger = logging.getLogger(__name__)


class CanonValidator:
    """
    Validates content against wiki cache.
    
    NO hardcoded lists - everything from Wookieepedia!
    
    UPDATED: Uses new FANDOM API-based WikiScraper.
    """
    
    def __init__(self, universe: str = 'star_wars'):
        self.universe = universe
        self.cache = WikiContentCache()
        self.scraper = WikiScraper()
        
        # Lazy-loaded sets (filled on first use)
        self._canon_species: Optional[Set[str]] = None
        self._canon_planets: Optional[Set[str]] = None
        self._canon_organizations: Optional[Set[str]] = None
        
        # Full categorized data (lazy loaded)
        self._categorized_data: Optional[Dict[str, List[str]]] = None
    
    def _load_categorized_data(self) -> Dict[str, List[str]]:
        """
        Load all categorized canon data from wiki.
        
        This is the main data source - fetched once and cached.
        
        Returns:
            Dict: category -> list of article titles
        """
        if self._categorized_data is None:
            logger.info(f"📡 Loading canon data for {self.universe}...")
            
            try:
                # Use new WikiScraper (FANDOM API based)
                self._categorized_data = self.scraper.get_canon_categorized_data(
                    universe=self.universe,
                    depth=3,
                    limit=60000,
                    force_refresh=False,  # Use cache if available
                    prefetch_images=False  # Don't need images here
                )
                
                total = sum(len(items) for items in self._categorized_data.values())
                logger.info(f"✅ Loaded {total:,} canon articles")
                
            except Exception as e:
                logger.error(f"❌ Failed to load canon data: {e}")
                # Fallback to empty dict
                self._categorized_data = {}
        
        return self._categorized_data
    
    def _load_canon_species(self) -> Set[str]:
        """Load all canon species from wiki categories"""
        if self._canon_species is None:
            logger.debug(f"Loading canon species for {self.universe}...")
            
            try:
                categorized = self._load_categorized_data()
                species_list = categorized.get('species', [])
                self._canon_species = set(species_list)
                
                logger.info(f"✅ Loaded {len(self._canon_species):,} canon species")
                
            except Exception as e:
                logger.error(f"⚠️ Failed to load species: {e}")
                # Fallback to minimal safe list
                self._canon_species = {'Human', 'Twi\'lek', 'Rodian', 'Wookiee'}
        
        return self._canon_species
    
    def _load_canon_planets(self) -> Set[str]:
        """Load all canon planets from wiki categories"""
        if self._canon_planets is None:
            logger.debug(f"Loading canon planets for {self.universe}...")
            
            try:
                categorized = self._load_categorized_data()
                planets_list = categorized.get('planets', [])
                self._canon_planets = set(planets_list)
                
                logger.info(f"✅ Loaded {len(self._canon_planets):,} canon planets")
                
            except Exception as e:
                logger.error(f"⚠️ Failed to load planets: {e}")
                # Fallback
                self._canon_planets = {'Tatooine', 'Coruscant', 'Naboo', 'Endor'}
        
        return self._canon_planets
    
    def _load_canon_organizations(self) -> Set[str]:
        """Load all canon organizations from wiki categories"""
        if self._canon_organizations is None:
            logger.debug(f"Loading canon organizations for {self.universe}...")
            
            try:
                categorized = self._load_categorized_data()
                orgs_list = categorized.get('organizations', [])
                self._canon_organizations = set(orgs_list)
                
                logger.info(f"✅ Loaded {len(self._canon_organizations):,} canon organizations")
                
            except Exception as e:
                logger.error(f"⚠️ Failed to load organizations: {e}")
                # Fallback
                self._canon_organizations = {'Jedi Order', 'Sith', 'Galactic Empire'}
        
        return self._canon_organizations
    
    def get_canon_species(self, limit: int = None) -> List[str]:
        """
        Get list of canon species (optionally limited).
        
        Args:
            limit: Max number to return
            
        Returns:
            Sorted list of species names
        """
        species = self._load_canon_species()
        species_list = sorted(list(species))
        return species_list[:limit] if limit else species_list
    
    def get_canon_planets(self, limit: int = None) -> List[str]:
        """
        Get list of canon planets (optionally limited).
        
        Args:
            limit: Max number to return
            
        Returns:
            Sorted list of planet names
        """
        planets = self._load_canon_planets()
        planets_list = sorted(list(planets))
        return planets_list[:limit] if limit else planets_list
    
    def get_canon_organizations(self, limit: int = None) -> List[str]:
        """
        Get list of canon organizations (optionally limited).
        
        Args:
            limit: Max number to return
            
        Returns:
            Sorted list of organization names
        """
        orgs = self._load_canon_organizations()
        orgs_list = sorted(list(orgs))
        return orgs_list[:limit] if limit else orgs_list
    
    def get_canon_category(self, category: str, limit: int = None) -> List[str]:
        """
        Get list of canon items for any category.
        
        Args:
            category: Category name (e.g., 'weapons', 'vehicles')
            limit: Max number to return
            
        Returns:
            Sorted list of item names
        """
        try:
            categorized = self._load_categorized_data()
            items = categorized.get(category, [])
            items_list = sorted(items)
            return items_list[:limit] if limit else items_list
        except Exception as e:
            logger.error(f"Failed to get category {category}: {e}")
            return []
    
    def validate_species(self, species: str) -> bool:
        """
        Check if species exists in wiki.
        
        Args:
            species: Species name to validate
            
        Returns:
            True if species is canon
        """
        if not species:
            return True
        canon_species = self._load_canon_species()
        return species in canon_species
    
    def validate_planet(self, planet: str) -> bool:
        """
        Check if planet exists in wiki.
        
        Args:
            planet: Planet name to validate
            
        Returns:
            True if planet is canon
        """
        if not planet:
            return True
        canon_planets = self._load_canon_planets()
        return planet in canon_planets
    
    def validate_organization(self, org: str) -> bool:
        """
        Check if organization exists in wiki.
        
        Args:
            org: Organization name to validate
            
        Returns:
            True if organization is canon
        """
        if not org:
            return True
        canon_orgs = self._load_canon_organizations()
        return org in canon_orgs
    
    def get_wiki_article(self, entity: str) -> Optional[Dict]:
        """
        Get cached wiki article for entity.
        
        Args:
            entity: Entity name
            
        Returns:
            Article dict or None
        """
        return self.cache.get_article(entity, self.universe)
    
    def search_similar_canon(
        self, 
        term: str, 
        category: str = 'species'
    ) -> List[str]:
        """
        Search for similar canon terms.
        
        Useful when AI invents something close to real.
        e.g., "Gorvothian" → suggests "Geonosian", "Corellian"
        
        Args:
            term: Term to search for
            category: Category to search in
            
        Returns:
            List of similar canon terms
        """
        term_lower = term.lower()
        
        if category == 'species':
            canon_set = self._load_canon_species()
        elif category == 'planet':
            canon_set = self._load_canon_planets()
        elif category == 'organization':
            canon_set = self._load_canon_organizations()
        else:
            return []
        
        # Simple similarity: starts with same letters
        similar = [
            item for item in canon_set 
            if item.lower().startswith(term_lower[:3])
        ]
        
        return similar[:5]  # Top 5 matches
    
    def scan_and_validate(self, text: str) -> Dict[str, List[str]]:
        """
        Scan text for entities and validate against wiki.
        
        Returns dict with valid/invalid entities.
        
        Args:
            text: Text to scan
            
        Returns:
            Dict with categorized entities
        """
        import re
        
        # Extract proper nouns
        proper_nouns = set(re.findall(r'\b[A-Z][a-z]+(?:\'[a-z]+)?\b', text))
        
        # Remove possessives (apostrophe-s) before checking
        cleaned_nouns = set()
        for noun in proper_nouns:
            # Remove 's from possessives (e.g., "Aldhani's" → "Aldhani")
            cleaned = re.sub(r"'s$", '', noun)
            cleaned_nouns.add(cleaned)
        
        proper_nouns = cleaned_nouns
        
        # MASSIVELY EXPANDED skip list
        skip_words = {
            # Articles, pronouns, demonstratives
            'The', 'A', 'An', 'This', 'That', 'These', 'Those',
            'You', 'Your', 'He', 'She', 'It', 'We', 'They', 'Them',
            'His', 'Her', 'Their', 'My', 'Our', 'Me', 'Him',
            
            # Question words
            'What', 'Where', 'When', 'Why', 'How', 'Who', 'Which',
            
            # Common verbs (capitalized at start of sentence)
            'As', 'Is', 'Are', 'Was', 'Were', 'Be', 'Been', 'Being',
            'Have', 'Has', 'Had', 'Do', 'Does', 'Did',
            'Will', 'Would', 'Could', 'Should', 'May', 'Might',
            'Can', 'Must', 'Shall',
            
            # Discourse markers
            'Meanwhile', 'However', 'Therefore', 'Thus', 'Hence',
            'Welcome', 'Indeed', 'Perhaps', 'Maybe', 'Actually',
            'Currently', 'Recently', 'Previously', 'Eventually',
            
            # Generic fantasy/sci-fi terms (NOT proper nouns)
            'Force', 'Temple', 'District', 'City', 'Planet', 'System',
            'Republic', 'Empire', 'Alliance', 'Order', 'Council',
            'Master', 'Knight', 'Lord', 'Captain', 'Commander',
            'Jedi', 'Sith',  # These are organizations
            'Spice', 'Credits', 'Ship', 'Vessel', 'Station',
            'Market', 'Cantina', 'Port', 'Bay', 'Sector',
            
            # Numbers and quantifiers
            'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven',
            'First', 'Second', 'Third', 'Fourth', 'Fifth',
            'Many', 'Few', 'Some', 'All', 'None', 'Several', 'Both',
            
            # Directions and locations (generic)
            'North', 'South', 'East', 'West', 'Above', 'Below',
            'Here', 'There', 'Nearby', 'Far', 'Near', 'Around',
            'Outside', 'Inside', 'Beyond',
            
            # Time words
            'Today', 'Tomorrow', 'Yesterday', 'Now', 'Then',
            'Before', 'After', 'During', 'While', 'Until',
            'Night', 'Day', 'Morning', 'Evening', 'Dawn', 'Dusk',
            
            # Meta/debug words
            'Turn', 'Beat', 'Act', 'Session', 'Campaign',
            'Data', 'Status', 'State', 'World', 'Context',
            
            # Polish words (if any slip through)
            'Narrator', 'Player', 'Miejsce', 'Godzina', 'Data',
            
            # Common adjectives
            'Large', 'Small', 'Great', 'Grand', 'Old', 'New',
            'Ancient', 'Modern', 'Dark', 'Light', 'Deep', 'High',
            'Long', 'Short', 'Wide', 'Narrow', 'Thick', 'Thin',
        }
        proper_nouns -= skip_words
        
        validated = {
            'valid_species': [],
            'valid_planets': [],
            'valid_organizations': [],
            'invalid': [],
            'unknown': []
        }
        
        for noun in proper_nouns:
            # Check all categories
            if self.validate_species(noun):
                validated['valid_species'].append(noun)
            elif self.validate_planet(noun):
                validated['valid_planets'].append(noun)
            elif self.validate_organization(noun):
                validated['valid_organizations'].append(noun)
            else:
                # Additional checks before marking as invalid
                
                # 1. Is it a likely NPC name? (short, simple)
                if len(noun) <= 7 and noun[0].isupper() and noun[1:].islower():
                    # Check if it doesn't have sci-fi suffixes
                    suspicious_endings = ('ian', 'ite', 'ese', 'ish', 'oid', 'an')
                    if not any(noun.lower().endswith(end) for end in suspicious_endings):
                        # Likely NPC name like "Kael", "Zara", "Thek"
                        validated['unknown'].append(noun)
                        continue
                
                # 2. Check if it's in cache at all
                article = self.get_wiki_article(noun)
                if article:
                    validated['unknown'].append(noun)  # Exists but unknown category
                else:
                    # 3. Only mark as INVALID if it's complex/suspicious
                    if len(noun) > 7 or any(noun.lower().endswith(end) for end in ('ian', 'ite', 'ese', 'ish', 'oid', 'an')):
                        validated['invalid'].append(noun)
                    else:
                        # Short unknown word - probably fine
                        validated['unknown'].append(noun)
        
        return validated
    
    def get_fallback_species(self) -> str:
        """
        Get safe fallback species.
        
        Returns:
            Safe species name
        """
        common = ['Human', 'Twi\'lek', 'Rodian', 'Zabrak']
        import random
        species_set = self._load_canon_species()
        available = [s for s in common if s in species_set]
        return random.choice(available) if available else 'Human'
    
    def get_fallback_planet(self) -> str:
        """
        Get safe fallback planet.
        
        Returns:
            Safe planet name
        """
        common = ['Tatooine', 'Coruscant', 'Naboo', 'Corellia']
        import random
        planets_set = self._load_canon_planets()
        available = [p for p in common if p in planets_set]
        return random.choice(available) if available else 'Tatooine'
    
    def get_all_categories(self) -> List[str]:
        """
        Get list of all available categories.
        
        Returns:
            List of category names
        """
        try:
            categorized = self._load_categorized_data()
            return list(categorized.keys())
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Get validator statistics.
        
        Returns:
            Dict with stats
        """
        try:
            categorized = self._load_categorized_data()
            
            return {
                'universe': self.universe,
                'total_categories': len(categorized),
                'total_articles': sum(len(items) for items in categorized.values()),
                'categories': {
                    cat: len(items)
                    for cat, items in categorized.items()
                },
                'species_loaded': len(self._canon_species) if self._canon_species else 0,
                'planets_loaded': len(self._canon_planets) if self._canon_planets else 0,
                'organizations_loaded': len(self._canon_organizations) if self._canon_organizations else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}