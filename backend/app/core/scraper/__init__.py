# backend/app/core/scraper/__init__.py
from .wiki_scraper import WikiScraper
from .config import ScraperConfig

__all__ = ['WikiScraper', 'ScraperConfig']