# backend/app/core/scraper/character_scraper.py
from typing import Dict, Optional
from bs4 import BeautifulSoup
from .http_client import WikiHttpClient
from .parsers.base_parser import BaseParser
import requests

class CharacterScraper:
    """Single responsibility: scraping danych postaci"""
    
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
    
    def scrape_character(self, url: str) -> Dict:
        """Scrapuje pełne dane postaci"""
        response = self.http_client.get(url)
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        return self.parser.parse_character_data(soup)
    
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