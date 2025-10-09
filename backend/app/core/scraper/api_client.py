# backend/app/core/scraper/api_client.py
"""
MediaWiki API Client z rekurencyjnym pobieraniem subcategories
"""
import requests
from typing import List, Set, Optional, Dict
import time

class WikiAPIClient:
    """
    Client dla MediaWiki API
    Supports recursive subcategory traversal
    """
    
    def __init__(self, base_url: str = "https://starwars.fandom.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RPG-GameMaster-Bot/1.0 (Educational Project)'
        })
        self._canon_cache: Optional[Set[str]] = None
        self._processed_categories: Set[str] = set()  # Prevent infinite loops
    
    def get_category_members(
        self, 
        category: str, 
        limit: int = 10000,
        namespace: int = 0,
        recursive: bool = True,
        max_depth: int = 5
    ) -> List[str]:
        """
        Pobiera wszystkie elementy kategorii przez API
        
        Args:
            category: Nazwa kategorii
            limit: Max liczba artykułów
            namespace: 0=articles, 14=categories
            recursive: Czy wchodzić do subcategories
            max_depth: Maksymalna głębokość rekurencji
        """
        if recursive:
            return self._get_category_recursive(category, limit, max_depth)
        else:
            return self._get_category_direct(category, limit, namespace)
    
    def _get_category_direct(
        self,
        category: str,
        limit: int,
        namespace: int
    ) -> List[str]:
        """Pobiera TYLKO bezpośrednie members (bez subcategories)"""
        members = []
        
        base_params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': 500,
            'cmnamespace': namespace,
            'format': 'json',
        }
        
        continue_params = {}
        requests_made = 0
        max_requests = 200
        
        while requests_made < max_requests and len(members) < limit:
            params = {**base_params, **continue_params}
            
            try:
                response = self.session.get(self.api_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'error' in data:
                    print(f"  ❌ API Error: {data['error'].get('info', 'Unknown')}")
                    break
                
                if 'query' in data and 'categorymembers' in data['query']:
                    batch = [m['title'] for m in data['query']['categorymembers']]
                    members.extend(batch)
                    requests_made += 1
                else:
                    break
                
                if 'continue' not in data:
                    break
                
                continue_params = data['continue']
                time.sleep(0.05)
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                break
        
        return members[:limit]
    
    def _get_category_recursive(
        self,
        category: str,
        limit: int,
        max_depth: int,
        current_depth: int = 0
    ) -> List[str]:
        """
        Pobiera members + wszystkie members z subcategories (rekurencyjnie)
        """
        # Prevent infinite loops
        if category in self._processed_categories:
            return []
        
        if current_depth > max_depth:
            return []
        
        self._processed_categories.add(category)
        
        indent = "  " * current_depth
        print(f"{indent}📂 Exploring: {category} (depth {current_depth})")
        
        all_members = []
        
        # STEP 1: Get direct article members (namespace 0)
        articles = self._get_category_direct(category, limit, namespace=0)
        all_members.extend(articles)
        print(f"{indent}  ✅ Found {len(articles)} articles")
        
        # STEP 2: Get subcategories (namespace 14)
        subcats = self._get_category_direct(category, limit=100, namespace=14)
        
        if subcats:
            print(f"{indent}  📁 Found {len(subcats)} subcategories")
            
            # STEP 3: Recursively process each subcategory
            for subcat in subcats:
                # Remove "Category:" prefix if present
                clean_subcat = subcat.replace('Category:', '')
                
                # Skip if already processed
                if clean_subcat in self._processed_categories:
                    continue
                
                # Recursive call
                subcat_members = self._get_category_recursive(
                    clean_subcat,
                    limit - len(all_members),  # Remaining limit
                    max_depth,
                    current_depth + 1
                )
                
                all_members.extend(subcat_members)
                
                # Stop if we hit the limit
                if len(all_members) >= limit:
                    break
        
        print(f"{indent}  ✅ Total from {category}: {len(all_members)} items")
        
        return all_members[:limit]
    
    def get_canon_articles(self, force_refresh: bool = False) -> Set[str]:
        """Pobiera wszystkie Canon articles (z cache)"""
        if self._canon_cache is not None and not force_refresh:
            return self._canon_cache
        
        print("📡 Fetching Canon articles via API...")
        
        # Canon_articles is usually flat (no deep subcategories)
        members = self._get_category_recursive(
            'Canon_articles',
            limit=600000,
            max_depth=6  # Canon_articles may have some subcats
        )
        
        canon_set = set(members)
        self._canon_cache = canon_set
        
        print(f"✅ Loaded {len(canon_set)} Canon articles")
        return canon_set
    
    def get_canon_filtered_category(
        self, 
        category: str, 
        limit: int = 60000,
        max_depth: int = 6
    ) -> List[str]:
        """
        Pobiera kategorię (rekurencyjnie) i filtruje tylko Canon
        """
        print(f"📡 Fetching {category} recursively (max depth: {max_depth})...")
        
        # Reset processed categories for this run
        self._processed_categories.clear()
        
        # Get all members recursively
        all_members = self._get_category_recursive(
            category,
            limit=limit * 3,  # Get more for filtering
            max_depth=max_depth
        )
        
        print(f"\n  📊 Total members (all depths): {len(all_members)}")
        
        # Filter Canon
        canon_members = [
            member for member in all_members 
            if not self._is_legends_article(member)
        ]
        
        legends_count = len(all_members) - len(canon_members)
        
        print(f"  ✅ Canon (by exclusion): {len(canon_members)}")
        print(f"  ❌ Legends (excluded): {legends_count}")
        
        return canon_members[:limit]
    
    def _is_legends_article(self, title: str) -> bool:
        """Sprawdza czy artykuł jest Legends"""
        return (
            title.endswith('/Legends') or 
            title.endswith('(Legends)') or
            '/Legends/' in title
        )
    
    def search_page(self, title: str) -> Optional[str]:
        """Wyszukuje stronę (preferuje Canon)"""
        clean_title = title.replace('/Legends', '').replace('(Legends)', '')
        
        params = {
            'action': 'query',
            'titles': clean_title,
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'query' in data and 'pages' in data['query']:
                pages = data['query']['pages']
                page_id = list(pages.keys())[0]
                
                if page_id != '-1':
                    page_title = pages[page_id]['title']
                    safe_title = page_title.replace(' ', '_')
                    return f"{self.base_url}/wiki/{safe_title}"
            
            return None
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return None
    
    def get_page_categories(self, title: str) -> List[str]:
        """Pobiera kategorie dla strony"""
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'categories',
            'cllimit': 'max',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'query' in data and 'pages' in data['query']:
                pages = data['query']['pages']
                page_id = list(pages.keys())[0]
                
                if page_id != '-1' and 'categories' in pages[page_id]:
                    return [
                        cat['title'].replace('Category:', '')
                        for cat in pages[page_id]['categories']
                    ]
            
            return []
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def is_canon(self, title: str) -> bool:
        """Sprawdza czy Canon"""
        if self._is_legends_article(title):
            return False
        
        categories = self.get_page_categories(title)
        return 'Canon_articles' in categories
    
    def clear_cache(self):
        """Czyści cache"""
        self._canon_cache = None
        self._processed_categories.clear()