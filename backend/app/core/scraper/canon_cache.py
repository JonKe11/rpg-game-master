# backend/app/core/scraper/canon_cache.py

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

class CanonCache:
    """
    Cache system dla Canon_articles
    Zapisuje do JSON, TTL 7 dni
    """
    
    def __init__(self, cache_dir: str = "canon_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_days = 7
    
    def _get_cache_path(self, universe: str, depth: int) -> Path:
        """Ścieżka do pliku cache (internal use)"""
        return self.cache_dir / f"{universe}_depth{depth}.json"
    
    def get_cache_path(self, universe: str, depth: int) -> Path:
        """Ścieżka do pliku cache (public API)"""
        return self._get_cache_path(universe, depth)
    
    def get_metadata_path(self, universe: str, depth: int) -> Path:
        """Ścieżka do metadanych cache"""
        return self.cache_dir / f"{universe}_depth{depth}_meta.json"
    
    def is_valid(self, universe: str, depth: int) -> bool:
        """Sprawdź czy cache jest aktualny"""
        cache_path = self._get_cache_path(universe, depth)
        meta_path = self.get_metadata_path(universe, depth)
        
        if not cache_path.exists() or not meta_path.exists():
            return False
        
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            
            created = datetime.fromisoformat(meta['created_at'])
            age = datetime.now() - created
            
            return age < timedelta(days=self.ttl_days)
            
        except Exception:
            return False
    
    def exists(self, universe: str, depth: int = 3) -> bool:
        """
        ✅ FIX: Check if cache file exists and is valid.
        
        Args:
            universe: Universe name
            depth: Recursion depth (default: 3)
            
        Returns:
            True if cache exists and is not expired
        """
        cache_file = self._get_cache_path(universe, depth)
        
        if not cache_file.exists():
            return False
        
        # Check if expired
        try:
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            
            if age.days > self.ttl_days:
                return False
            
            return True
        except Exception:
            return False
    
    def load(self, universe: str, depth: int) -> Optional[Dict[str, List[str]]]:
        """Załaduj z cache"""
        if not self.is_valid(universe, depth):
            return None
        
        cache_path = self._get_cache_path(universe, depth)
        meta_path = self.get_metadata_path(universe, depth)
        
        try:
            # Load data
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load metadata
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            # Display info
            age = datetime.now() - datetime.fromisoformat(meta['created_at'])
            age_str = f"{age.days}d {age.seconds // 3600}h" if age.days > 0 else f"{age.seconds // 3600}h"
            
            print(f"✅ Loaded from cache: {cache_path.name}")
            print(f"   Age: {age_str} (max {self.ttl_days} days)")
            print(f"   Total items: {meta['total_items']:,}")
            print(f"   Categories: {meta['categories_count']}")
            
            return data
            
        except Exception as e:
            print(f"❌ Cache load error: {e}")
            return None
    
    # ✅ NOWA METODA - ALIAS DLA load()
    def get(self, universe: str, depth: int = 3) -> Optional[Dict[str, List[str]]]:
        """
        Get cached data (alias for load).
        
        Args:
            universe: Universe name
            depth: Recursion depth (default: 3)
            
        Returns:
            Cached data or None
        """
        return self.load(universe, depth)
    
    def save(
        self, 
        universe: str,
        data: Dict[str, List[str]],
        depth: int = 3
    ):
        """
        Zapisz do cache z metadanymi.
        
        ✅ FIX: Depth is now optional parameter with default value
        """
        cache_path = self._get_cache_path(universe, depth)
        meta_path = self.get_metadata_path(universe, depth)
        
        try:
            # Save data
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Create metadata
            total_items = sum(len(items) for items in data.values())
            categories_with_items = {k: len(v) for k, v in data.items() if v}
            
            metadata = {
                'created_at': datetime.now().isoformat(),
                'universe': universe,
                'depth': depth,
                'total_items': total_items,
                'categories_count': len(categories_with_items),
                'categories': categories_with_items,
                'ttl_days': self.ttl_days,
                'expires_at': (datetime.now() + timedelta(days=self.ttl_days)).isoformat()
            }
            
            # Save metadata
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Display info
            print(f"\n💾 Saved to cache: {cache_path.name}")
            print(f"   Total items: {total_items:,}")
            print(f"   File size: {cache_path.stat().st_size / 1024 / 1024:.2f} MB")
            print(f"   TTL: {self.ttl_days} days")
            print(f"   Categories breakdown:")
            for category, count in sorted(categories_with_items.items(), key=lambda x: -x[1])[:10]:
                print(f"     - {category}: {count:,}")
            
        except Exception as e:
            print(f"❌ Cache save error: {e}")
    
    def invalidate(self, universe: str, depth: int):
        """Usuń cache (force refresh)"""
        cache_path = self._get_cache_path(universe, depth)
        meta_path = self.get_metadata_path(universe, depth)
        
        deleted = []
        
        if cache_path.exists():
            cache_path.unlink()
            deleted.append(cache_path.name)
        
        if meta_path.exists():
            meta_path.unlink()
            deleted.append(meta_path.name)
        
        if deleted:
            print(f"🗑️ Cache invalidated: {', '.join(deleted)}")
    
    def get_stats(self, universe: str, depth: int) -> Optional[Dict]:
        """Pobierz statystyki cache bez ładowania danych"""
        meta_path = self.get_metadata_path(universe, depth)
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None