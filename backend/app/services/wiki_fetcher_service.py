# backend/app/services/wiki_fetcher_service.py
"""
Service do pobierania PEŁNYCH artykułów z wiki
Używa WikiScraper + WikiContentCache + STRUCTURED EXTRACTION
"""
from typing import Dict, List, Optional
from app.core.scraper.wiki_scraper import WikiScraper
from app.core.scraper.wiki_content_cache import WikiContentCache
import re

class WikiFetcherService:
    """
    Pobiera pełne artykuły (nie tylko nazwy) i cache'uje
    RAG-ready: przygotowuje dane dla AI z wyekstraktowaną strukturą
    """
    
    def __init__(self):
        self.scraper = WikiScraper()
        self.content_cache = WikiContentCache()
    
    def fetch_article(
        self, 
        title: str, 
        universe: str = 'star_wars'
    ) -> Optional[Dict]:
        """
        Pobiera PEŁNY artykuł z wiki
        
        Returns:
            Dict z: name, description, biography, info, abilities, etc.
        """
        # 1. Check cache first
        cached = self.content_cache.get_article(title, universe)
        if cached:
            print(f"✓ '{title}' from content cache")
            return cached
        
        # 2. Fetch from wiki
        print(f"📡 Fetching '{title}' from wiki...")
        url = self.scraper.search_character(title, universe)
        
        if not url:
            print(f"⚠️ '{title}' not found on wiki")
            return None
        
        # 3. Scrape full data
        data = self.scraper.scrape_character_data(url)
        
        if not data or not data.get('name'):
            print(f"⚠️ Failed to scrape '{title}'")
            return None
        
        # 4. Save to cache
        self.content_cache.save_article(title, universe, data)
        print(f"✅ Cached '{title}'")
        
        return data
    
    def fetch_multiple(
        self, 
        titles: List[str], 
        universe: str = 'star_wars'
    ) -> Dict[str, Dict]:
        """Pobiera wiele artykułów naraz"""
        results = {}
        
        for title in titles:
            article = self.fetch_article(title, universe)
            if article:
                results[title] = article
        
        return results
    
    def fetch_context_for_location(
        self, 
        location: str, 
        universe: str = 'star_wars'
    ) -> Dict:
        """
        Pobiera RICH context dla lokacji:
        - Artykuł o lokacji
        - Structured data (capital, moons, terrain, type)
        - Powiązane rasy/organizacje
        """
        context = {
            'location': None,
            'structured': None,
            'related_species': {},
            'related_organizations': {}
        }
        
        # Fetch main location article
        location_data = self.fetch_article(location, universe)
        if not location_data:
            return context
        
        context['location'] = location_data
        
        # 🆕 EXTRACT STRUCTURED INFO
        structured_info = self._extract_structured_info(location_data)
        context['structured'] = structured_info
        
        # Extract related entities from infobox
        info = location_data.get('info', {})
        
        # Get species mentioned
        species_keys = ['species', 'native_species', 'inhabitants']
        for key in species_keys:
            if key in info:
                species_text = info[key]
                species_names = [s.strip() for s in species_text.split(',')[:3]]
                context['related_species'] = self.fetch_multiple(species_names, universe)
                break
        
        # Get organizations mentioned
        org_keys = ['affiliation', 'government', 'owner']
        for key in org_keys:
            if key in info:
                org_text = info[key]
                org_names = [o.strip() for o in org_text.split(',')[:3]]
                context['related_organizations'] = self.fetch_multiple(org_names, universe)
                break
        
        return context
    
    def _extract_structured_info(self, article: Dict) -> Dict:
        """
        🆕 Extract structured information from wiki article:
        - Planet/moon relationships
        - Capital cities
        - Terrain types
        - Notable locations
        """
        info = {
            'type': None,  # 'planet', 'moon', 'system'
            'capital': None,
            'orbits': None,  # What it orbits (for moons)
            'moons': [],     # What orbits it (for planets)
            'terrain': [],
            'notable_locations': []
        }
        
        description = article.get('description', '').lower()
        
        # Determine type
        if 'moon' in description:
            info['type'] = 'moon'
            
            # Extract what it orbits
            orbit_patterns = [
                r'moon.*?(?:of|orbiting).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'orbits.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'satellite.*?of.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            ]
            
            for pattern in orbit_patterns:
                orbit_match = re.search(pattern, article.get('description', ''))
                if orbit_match:
                    info['orbits'] = orbit_match.group(1)
                    break
        elif 'planet' in description:
            info['type'] = 'planet'
        
        # Extract capital
        capital_patterns = [
            r'capital.*?(?:city|was|is).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?).*?(?:capital|seat of government)',
        ]
        
        for pattern in capital_patterns:
            match = re.search(pattern, article.get('description', ''))
            if match:
                potential_capital = match.group(1)
                # Exclude planet name itself
                if potential_capital.lower() != article.get('name', '').lower():
                    info['capital'] = potential_capital
                    break
        
        # Check info_box for capital
        if not info['capital'] and 'info_box' in article:
            info_box = article['info_box']
            if isinstance(info_box, dict):
                for key, value in info_box.items():
                    if 'capital' in key.lower():
                        info['capital'] = str(value).strip()
                        break
        
        # Extract terrain types
        terrain_keywords = ['desert', 'forest', 'swamp', 'ocean', 'mountain', 'urban', 'ice', 'jungle', 'plains', 'hills', 'volcanic', 'temperate', 'tropical']
        for terrain in terrain_keywords:
            if terrain in description:
                info['terrain'].append(terrain)
        
        # Extract moons (for planets)
        if info['type'] == 'planet':
            moon_pattern = r'moon[s]?.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            moons = re.findall(moon_pattern, article.get('description', ''))
            info['moons'] = list(set(moons))[:5]  # Max 5
        
        return info
    
    def search_relevant_articles(
        self, 
        query: str, 
        universe: str = 'star_wars', 
        limit: int = 5
    ) -> List[Dict]:
        """
        Wyszukuje artykuły relevantne do query
        Prosty keyword search (w przyszłości: embeddings)
        """
        return self.content_cache.search_by_keyword(query, universe, limit)