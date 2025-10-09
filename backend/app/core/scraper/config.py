# backend/app/core/scraper/config.py
from dataclasses import dataclass

@dataclass
class ScraperConfig:
    """Configuration for wiki scraper"""
    
    # Limits - BARDZO WYSOKIE aby nie obcinać Canon articles
    max_category_items: int = 50000  # ✅ ZWIĘKSZONE z 10000 do 50000
    max_pages_per_category: int = 500  # ✅ ZWIĘKSZONE z 200 do 500
    
    # Rate limiting
    request_delay: float = 0.05  # seconds (szybsze)
    request_timeout: int = 30  # seconds
    
    # Recursion
    max_subcategory_depth: int = 6  # ✅ ZWIĘKSZONE z 5 do 6