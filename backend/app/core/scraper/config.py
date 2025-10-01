# backend/app/core/scraper/config.py
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class ScraperConfig:
    """Konfiguracja scrapera - wszystkie magic numbers w jednym miejscu"""
    request_delay: float = 0.5  # sekundy między requestami
    cache_validity: timedelta = timedelta(hours=24)
    request_timeout: int = 15
    max_category_items: int = 1000
    max_retries: int = 3
    max_pages_per_category: int = 50