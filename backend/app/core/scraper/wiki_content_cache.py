# backend/app/core/scraper/wiki_content_cache.py
"""
Cache dla PEŁNEJ zawartości wiki articles
Używany przez RAG system
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class WikiContentCache:
    """
    Rozszerzony cache - trzyma PEŁNE artykuły
    Format: {title, description, biography, info, abilities, etc.}
    """
    
    def __init__(self, cache_dir: str = 'wiki_content_cache', validity_hours: int = 168):
        """
        Args:
            cache_dir: Folder dla cache
            validity_hours: Jak długo cache ważny (default: 7 dni)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.validity = timedelta(hours=validity_hours)
    
    def get_article(self, title: str, universe: str) -> Optional[Dict]:
        """Pobierz pełny artykuł z cache"""
        safe_title = self._sanitize_filename(title)
        cache_file = self.cache_dir / f"{universe}_{safe_title}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check validity
            cached_time = datetime.fromisoformat(data['cached_at'])
            if datetime.now() - cached_time > self.validity:
                return None
            
            return data['content']
        except Exception as e:
            print(f"⚠️ Cache read error for {title}: {e}")
            return None
    
    def save_article(self, title: str, universe: str, content: Dict):
        """Zapisz pełny artykuł do cache"""
        safe_title = self._sanitize_filename(title)
        cache_file = self.cache_dir / f"{universe}_{safe_title}.json"
        
        try:
            data = {
                'title': title,
                'universe': universe,
                'cached_at': datetime.now().isoformat(),
                'content': content
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Cache write error for {title}: {e}")
    
    def get_multiple(self, titles: List[str], universe: str) -> Dict[str, Dict]:
        """Pobierz wiele artykułów naraz"""
        results = {}
        for title in titles:
            article = self.get_article(title, universe)
            if article:
                results[title] = article
        return results
    
    def search_by_keyword(self, keyword: str, universe: str, limit: int = 10) -> List[Dict]:
        """
        Prosty full-text search w cache'owanych artykułach
        Returns: Lista dict z title, relevance, content
        """
        results = []
        keyword_lower = keyword.lower()
        
        for cache_file in self.cache_dir.glob(f"{universe}_*.json"):
            if len(results) >= limit * 2:  # Search więcej, potem sortuj
                break
            
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                content = data.get('content', {})
                
                # Build searchable text
                searchable = " ".join([
                    content.get('name', ''),
                    content.get('description', ''),
                    content.get('biography', '')[:500]
                ]).lower()
                
                # Count occurrences (simple relevance)
                relevance = searchable.count(keyword_lower)
                
                if relevance > 0:
                    results.append({
                        'title': data['title'],
                        'relevance': relevance,
                        'content': content
                    })
            except:
                continue
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]
    
    def _sanitize_filename(self, title: str) -> str:
        """Bezpieczna nazwa pliku"""
        # Remove special characters
        safe = title.replace('/', '_').replace('\\', '_').replace(' ', '_')
        safe = ''.join(c for c in safe if c.isalnum() or c in '_-')
        return safe[:100]  # Max 100 chars
    
    def clear(self):
        """Wyczyść cały cache"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)