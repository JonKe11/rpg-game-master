# backend/app/core/scraper/cache_manager.py
import json
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path

class CacheManager:
    """Single responsibility: zarządzanie cache'em"""
    
    def __init__(self, cache_dir: str, validity_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.validity = timedelta(hours=validity_hours)
    
    def get(self, key: str) -> Optional[List[str]]:
        """Pobierz z cache jeśli aktualny"""
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time > self.validity:
                return None
            
            return data['items']
        except Exception as e:
            print(f"Cache read error for {key}: {e}")
            return None
    
    def set(self, key: str, items: List[str]):
        """Zapisz do cache"""
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'items': items,
                'count': len(items)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Cache write error for {key}: {e}")
    
    def clear(self, pattern: Optional[str] = None):
        """Wyczyść cache"""
        for file in self.cache_dir.glob('*.json'):
            if pattern is None or file.stem.startswith(pattern):
                file.unlink()