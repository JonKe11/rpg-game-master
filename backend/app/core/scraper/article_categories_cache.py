# backend/app/core/scraper/article_categories_cache.py (NOWY PLIK!)

import json
from pathlib import Path
from typing import Dict, List

class ArticleCategoriesCache:
    """Cache dla kategorii artykułów"""
    
    def __init__(self, cache_dir: str = "cache/article_categories"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_path(self, universe: str) -> Path:
        return self.cache_dir / f"{universe}_article_categories.json"
    
    def load(self, universe: str) -> Dict[str, List[str]]:
        """Load cached article categories"""
        cache_path = self.get_cache_path(universe)
        
        if not cache_path.exists():
            return {}
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save(self, universe: str, data: Dict[str, List[str]]):
        """Save article categories to cache"""
        cache_path = self.get_cache_path(universe)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved article categories cache: {cache_path.name}")
            print(f"   Articles cached: {len(data):,}")
        except Exception as e:
            print(f"❌ Error saving article categories cache: {e}")