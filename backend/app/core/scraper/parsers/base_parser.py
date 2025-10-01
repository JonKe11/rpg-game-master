# backend/app/core/scraper/parsers/base_parser.py
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import List, Dict

class BaseParser(ABC):
    """Abstract base - można łatwo testować i wymienić implementację"""
    
    @abstractmethod
    def parse_category_items(self, soup: BeautifulSoup) -> List[str]:
        """Parsuje listę elementów z kategorii"""
        pass
    
    @abstractmethod
    def parse_character_data(self, soup: BeautifulSoup) -> Dict:
        """Parsuje dane postaci ze strony"""
        pass
    
    @abstractmethod
    def find_next_page_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """Znajduje URL następnej strony paginacji"""
        pass