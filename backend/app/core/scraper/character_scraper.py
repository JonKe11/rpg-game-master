# backend/app/core/scraper/character_scraper.py
from typing import Dict, Optional
from bs4 import BeautifulSoup, Comment
from .http_client import WikiHttpClient
from .parsers.base_parser import BaseParser
import requests

class CharacterScraper:
    """Single responsibility: scraping danych postaci + NON-CANON detection"""
    
    def __init__(self, http_client: WikiHttpClient, parser: BaseParser):
        self.http_client = http_client
        self.parser = parser
    
    def search_character(self, character_name: str, base_url: str) -> Optional[str]:
        """Wyszukaj postać i zwróć URL"""
        # Metoda 1: Bezpośredni URL
        character_url = character_name.replace(' ', '_')
        full_url = f"{base_url}/wiki/{character_url}"
        
        response = self.http_client.get(full_url)
        if response and response.status_code == 200:
            return full_url
        
        # Metoda 2: Search API Fandom
        return self._search_via_api(character_name, base_url)
    
    def scrape_character(self, url: str, universe: str = 'star_wars') -> Dict:
        """Scrapuje pełne dane postaci + sprawdza NON-CANON"""
        from .wiki_content_cache import WikiContentCache
        
        response = self.http_client.get(url)
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ✅ Sprawdź NON-CANON
        if self._is_non_canon(soup):
            print(f"  ⚠️ Article is NON-CANON - skipping")
            return {}
        
        data = self.parser.parse_character_data(soup)
        
        # ✅ Zapisz do WikiContentCache (z obrazkiem!)
        if data.get('name'):
            content_cache = WikiContentCache('wiki_content_cache', validity_hours=168)
            content_cache.save_article(data['name'], universe, data)
        
        return data
    
    def _is_non_canon(self, soup: BeautifulSoup) -> bool:
        """Sprawdza czy artykuł jest NON-CANON"""
        # Metoda 1: Comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'noncanon' in comment.lower():
                return True
        
        # Metoda 2: Banner
        notices = soup.find_all(['div', 'table'], class_='notice')
        for notice in notices:
            text = notice.get_text().lower()
            if 'non-canon' in text or 'noncanon' in text:
                return True
        
        # Metoda 3: Infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            canon_field = infobox.find('div', attrs={'data-source': 'canon'})
            if canon_field and 'no' in canon_field.get_text().lower():
                return True
        
        return False
    
    def _search_via_api(self, query: str, base_url: str) -> Optional[str]:
        """Wyszukaj przez Fandom Search API"""
        search_url = f"{base_url}/api.php"
        params = {
            'action': 'opensearch',
            'search': query,
            'limit': 5,
            'format': 'json'
        }
        
        try:
            response = requests.get(
                search_url, 
                params=params, 
                headers=self.http_client.headers,
                timeout=self.http_client.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if len(data) > 3 and data[3]:
                    return data[3][0]  # Pierwszy wynik
        except Exception as e:
            print(f"Search API error: {e}")
        
        return None