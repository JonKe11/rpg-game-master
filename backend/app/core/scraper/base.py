# backend/app/core/scraper/base.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class BaseScraper(ABC):
    """Abstract base class for wiki scrapers"""
    
    @abstractmethod
    def search_character(self, character_name: str, universe: str = 'star_wars') -> Optional[str]:
        """Search for character and return URL"""
        pass
    
    @abstractmethod
    def scrape_character_data(self, url: str) -> Dict:
        """Scrape character data from URL"""
        pass