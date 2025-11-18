# backend/app/core/ai/canon_validator.py
"""
Dynamic canon validation using PostgreSQL as the source of truth.
"""

from typing import Set, List, Dict, Optional
import logging
import re

# ⛔️ USUNIĘTE: Stare importy cache'a plików JSON
# from app.core.scraper.wiki_content_cache import WikiContentCache
# from app.core.scraper.wiki_scraper import WikiScraper

# ✅ NOWE IMPORTY:
from app.models.database import SessionLocal
from app.services.postgres_cache_service import PostgresCacheService
from app.models.wiki_article import article_to_dict # Załóżmy, że ta funkcja istnieje lub przenieś ją tutaj

logger = logging.getLogger(__name__)

# ✅ NOWA FUNKCJA POMOCNICZA (jeśli nie masz jej globalnie)
def article_to_dict(article) -> Dict:
    """Konwertuje obiekt WikiArticle SQLAlchemy na słownik."""
    if not article: return {}
    data = {
        'id': article.id, 'name': article.title, 'title': article.title,
        'description': article.content.get('description') if article.content else None,
        'abstract': article.content.get('abstract') if article.content else None,
        'image_url': article.image_url, 'url': article.source_url,
        'source_url': article.source_url, 'is_canon': True,
        'info_box': article.content or {}
    }
    if article.content:
        structured_data = {}
        if article.content.get('Region'): structured_data['region'] = article.content['Region']
        if article.content.get('System'): structured_data['system'] = article.content['System']
        if article.content.get('capital'): structured_data['capital'] = article.content['capital']
        if article.content.get('Capital'): structured_data['capital'] = article.content['Capital']
        if structured_data: data['structured'] = structured_data
    return data


class CanonValidator:
    """
    Waliduje treść, odpytując bezpośrednio bazę danych PostgreSQL.
    Koniec z ładowaniem wszystkiego do pamięci RAM.
    """
    
    def __init__(self, universe: str = 'star_wars'):
        self.universe = universe
        
        # ✅ NOWA LOGIKA: Dostęp do bazy danych
        try:
            self.db = SessionLocal()
            self.pg_cache = PostgresCacheService(self.db)
            logger.info(f"✅ CanonValidator połączony z PostgresCacheService dla {universe}")
        except Exception as e:
            logger.error(f"❌ CanonValidator nie mógł połączyć się z DB: {e}")
            self.db = None
            self.pg_cache = None
        
        # ⛔️ USUNIĘTE: Wszystkie stare, leniwie ładowane zestawy (_canon_species, _categorized_data itp.)

    def __del__(self):
        """Zamknij sesję bazy danych, gdy walidator jest niszczony"""
        if self.db:
            self.db.close()

    def _get_paginated_category(self, category: str, limit: Optional[int] = None, query: Optional[str] = None) -> List[str]:
        """Pobiera paginowane dane kategorii z PostgreSQL"""
        if not self.pg_cache:
            logger.error("Brak pg_cache. Nie można pobrać danych.")
            return []
        
        try:
            results = self.pg_cache.search_articles_paginated(
                universe=self.universe,
                category=category,
                query=query,
                limit=limit or 1000, # Domyślny limit, jeśli nie podano
                offset=0
            )
            return [article.title for article in results['items']]
        except Exception as e:
            logger.error(f"Nie udało się pobrać kategorii {category} z PostgreSQL: {e}")
            return []

    def get_canon_species(self, limit: int = None) -> List[str]:
        """Pobiera listę gatunków z PostgreSQL"""
        return self._get_paginated_category('species', limit)
    
    def get_canon_planets(self, limit: int = None) -> List[str]:
        """Pobiera listę planet z PostgreSQL"""
        return self._get_paginated_category('planets', limit)
    
    def get_canon_organizations(self, limit: int = None) -> List[str]:
        """Pobiera listę organizacji z PostgreSQL"""
        return self._get_paginated_category('organizations', limit)
    
    def get_canon_category(self, category: str, limit: int = None) -> List[str]:
        """Pobiera listę elementów dla dowolnej kategorii z PostgreSQL"""
        return self._get_paginated_category(category, limit)
    
    def _check_entity_exists(self, entity: str, category: str) -> bool:
        """Sprawdza, czy encja istnieje w danej kategorii w PostgreSQL"""
        if not entity or not self.pg_cache:
            return True # Zawsze zakładaj, że jest poprawna, jeśli nie ma encji lub bazy
        
        try:
            # Użyj szybkiego wyszukiwania po tytule
            article = self.pg_cache.get_article_by_title(entity, self.universe)
            # Jeśli znaleziono i kategoria pasuje
            if article and article.category == category:
                return True
            # Jeśli znaleziono, ale kategoria nie pasuje (np. "Luke" to 'character', a nie 'planet')
            elif article:
                return False
            # Jeśli nie znaleziono po tytule (może być literówka lub AI coś wymyśliło)
            return False
        except Exception as e:
            logger.error(f"Błąd walidacji encji {entity}: {e}")
            return True # W razie błędu lepiej przepuścić

    def validate_species(self, species: str) -> bool:
        """Sprawdza, czy gatunek istnieje w bazie"""
        return self._check_entity_exists(species, 'species')
    
    def validate_planet(self, planet: str) -> bool:
        """Sprawdza, czy planeta istnieje w bazie"""
        return self._check_entity_exists(planet, 'planets')
    
    def validate_organization(self, org: str) -> bool:
        """Sprawdza, czy organizacja istnieje w bazie"""
        return self._check_entity_exists(org, 'organizations')
    
    def get_wiki_article(self, entity: str) -> Optional[Dict]:
        """Pobiera artykuł z PostgreSQL"""
        if not self.pg_cache:
            return None
        
        article = self.pg_cache.get_article_by_title(entity, self.universe)
        return article_to_dict(article)
    
    def search_similar_canon(
        self, 
        term: str, 
        category: str = 'species'
    ) -> List[str]:
        """Wyszukuje podobne terminy kanoniczne w PostgreSQL"""
        if not self.pg_cache:
            return []
            
        try:
            results = self.pg_cache.search_articles_paginated(
                universe=self.universe,
                category=category,
                query=term, # Użyj wyszukiwania ILIKE
                limit=5
            )
            return [article.title for article in results['items']]
        except Exception as e:
            logger.error(f"Błąd search_similar_canon dla {term}: {e}")
            return []
    
    def scan_and_validate(self, text: str) -> Dict[str, List[str]]:
        """
        Skanuje tekst w poszukiwaniu encji i waliduje je w bazie.
        (Ta funkcja jest teraz znacznie wolniejsza, ponieważ wykonuje wiele zapytań do bazy, 
        ale nie zużywa RAM-u)
        """
        import re
        
        proper_nouns = set(re.findall(r'\b[A-Z][a-z]+(?:\'[a-z]+)?\b', text))
        cleaned_nouns = set(re.sub(r"'s$", '', noun) for noun in proper_nouns)
        
        skip_words = {
            'The', 'A', 'An', 'This', 'That', 'You', 'Your', 'He', 'She', 'It', 'We', 'They',
            'What', 'Where', 'When', 'Why', 'How', 'Who', 'Which',
            'As', 'Is', 'Are', 'Was', 'Were', 'Be', 'Been', 'Being', 'Have', 'Has', 'Had',
            'Will', 'Would', 'Could', 'Should', 'May', 'Might', 'Can', 'Must',
            'Meanwhile', 'However', 'Therefore', 'Welcome', 'Indeed', 'Perhaps', 'Maybe',
            'Force', 'Temple', 'District', 'City', 'Planet', 'System',
            'Republic', 'Empire', 'Alliance', 'Order', 'Council',
            'Master', 'Knight', 'Lord', 'Captain', 'Commander',
            'Jedi', 'Sith', 'Spice', 'Credits', 'Ship', 'Vessel', 'Station',
            'Market', 'Cantina', 'Port', 'Bay', 'Sector',
            'One', 'Two', 'Three', 'First', 'Second', 'Third',
            'North', 'South', 'East', 'West', 'Above', 'Below',
            'Here', 'There', 'Nearby', 'Far', 'Near', 'Around',
            'Today', 'Tomorrow', 'Yesterday', 'Now', 'Then',
            'Night', 'Day', 'Morning', 'Evening', 'Dawn', 'Dusk',
            'Turn', 'Beat', 'Act', 'Session', 'Campaign',
            'Data', 'Status', 'State', 'World', 'Context',
            'Narrator', 'Player', 'Miejsce', 'Godzina', 'Data',
        }
        proper_nouns = cleaned_nouns - skip_words
        
        validated = {
            'valid_species': [],
            'valid_planets': [],
            'valid_organizations': [],
            'invalid': [],
            'unknown': []
        }
        
        if not self.pg_cache:
            logger.warning("Brak pg_cache, walidacja pominięta.")
            validated['unknown'] = list(proper_nouns)
            return validated
            
        # Sprawdzanie każdej encji w bazie danych
        for noun in proper_nouns:
            try:
                article = self.pg_cache.get_article_by_title(noun, self.universe)
                if article:
                    category = article.category
                    if category == 'species':
                        validated['valid_species'].append(noun)
                    elif category == 'planets':
                        validated['valid_planets'].append(noun)
                    elif category == 'organizations':
                        validated['valid_organizations'].append(noun)
                    else:
                        validated['unknown'].append(noun) # Znaleziono, ale to inna kategoria
                else:
                    # Nie znaleziono
                    if len(noun) > 7 or any(noun.lower().endswith(end) for end in ('ian', 'ite', 'ese', 'ish', 'oid', 'an')):
                        validated['invalid'].append(noun) # Prawdopodobnie wymyślone
                    else:
                        validated['unknown'].append(noun) # Prawdopodobnie nazwa własna (NPC)
            except Exception as e:
                logger.error(f"Błąd walidacji {noun}: {e}")
                validated['unknown'].append(noun)
        
        return validated
    
    def get_fallback_species(self) -> str:
        """Get safe fallback species."""
        return 'Human' # Uproszczono - Human jest zawsze bezpieczny
    
    def get_fallback_planet(self) -> str:
        """Get safe fallback planet."""
        return 'Tatooine' # Uproszczono - Tatooine jest zawsze bezpieczna
    
    def get_all_categories(self) -> List[str]:
        """Pobiera listę wszystkich kategorii z bazy"""
        if not self.pg_cache:
            return []
        try:
            counts = self.pg_cache.get_category_counts(self.universe)
            return list(counts.keys())
        except Exception as e:
            logger.error(f"Nie udało się pobrać kategorii: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Pobiera statystyki bezpośrednio z bazy"""
        if not self.pg_cache:
            return {'error': 'No pg_cache connection'}
        try:
            stats = self.pg_cache.get_cache_stats(self.universe)
            return {
                'universe': self.universe,
                'total_articles': stats.get('total_articles', 0),
                'categories': stats.get('categories', {}),
            }
        except Exception as e:
            logger.error(f"Nie udało się pobrać statystyk: {e}")
            return {'error': str(e)}