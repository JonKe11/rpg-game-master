# backend/app/core/scraper/image_fetcher.py
"""
Shared image fetching logic - used by both wiki endpoints and prefetch service.
Follows DRY principle - single source of truth for image operations.
"""

import requests
from pathlib import Path
from hashlib import md5
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

# Global cache directory
CACHE_DIR = Path("./image_cache")
CACHE_DIR.mkdir(exist_ok=True)


class ImageFetcher:
    """
    Handles image downloading and caching.
    
    Features:
    - File-based caching (persistent across restarts)
    - URL validation
    - Thread-safe operations
    - Retry logic with exponential backoff
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize ImageFetcher.
        
        Args:
            cache_dir: Custom cache directory (defaults to ./image_cache)
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_cache_path(self, url: str) -> Path:
        """
        Generate cache file path from URL using MD5 hash.
        
        Args:
            url: Image URL
            
        Returns:
            Path to cached image file
        """
        url_hash = md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.img"
    
    def validate_url(self, url: str) -> bool:
        """
        Validate image URL before fetching.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url:
            return False
        
        if not url.startswith('http'):
            return False
        
        # Fix for corrupted URLs (from logs: "'d" prefix)
        if url.startswith("'d") or url.startswith('"d'):
            return False
        
        return True
    
    def is_cached(self, url: str) -> bool:
        """
        Check if image is already cached.
        
        Args:
            url: Image URL
            
        Returns:
            True if cached, False otherwise
        """
        cache_path = self.get_cache_path(url)
        return cache_path.exists()
    
    def fetch_single(
        self, 
        url: str, 
        timeout: int = 15,
        max_retries: int = 2
    ) -> Tuple[bool, bool, Optional[bytes]]:
        """
        Fetch single image with retry logic.
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (success, was_cached, content)
            - success: True if image was fetched/cached successfully
            - was_cached: True if image was already in cache
            - content: Image binary content (None if failed)
        """
        # Validate URL
        if not self.validate_url(url):
            logger.warning(f"Invalid URL: {url[:50]}")
            return (False, False, None)
        
        cache_path = self.get_cache_path(url)
        
        # Check cache first
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    content = f.read()
                return (True, True, content)
            except Exception as e:
                logger.error(f"Cache read error: {e}")
                # Continue to fetch from source
        
        # Fetch from source with retry
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    stream=True, 
                    timeout=timeout
                )
                response.raise_for_status()
                
                content = response.content
                
                # Save to cache
                try:
                    with open(cache_path, 'wb') as f:
                        f.write(content)
                except Exception as e:
                    logger.error(f"Cache write error: {e}")
                
                return (True, False, content)
                
            except requests.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"Timeout (attempt {attempt + 1}/{max_retries}): {url[:50]}")
                    continue
                else:
                    logger.error(f"Timeout after {max_retries} attempts: {url[:50]}")
                    return (False, False, None)
                    
            except requests.HTTPError as e:
                logger.error(f"HTTP Error {e.response.status_code}: {url[:50]}")
                return (False, False, None)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return (False, False, None)
        
        return (False, False, None)
    
    def fetch_batch_parallel(
        self,
        urls_with_names: list,
        max_workers: int = 10,
        show_progress: bool = True
    ) -> dict:
        """
        Fetch multiple images in parallel.
        
        Args:
            urls_with_names: List of tuples (name, url, index, total)
            max_workers: Number of parallel workers
            show_progress: Whether to print progress
            
        Returns:
            Dict with statistics: {
                'downloaded': int,
                'cached': int,
                'failed': int,
                'total': int
            }
        """
        stats = {
            'downloaded': 0,
            'cached': 0,
            'failed': 0,
            'total': len(urls_with_names)
        }
        
        if not urls_with_names:
            return stats
        
        def process_single(args):
            name, url, idx, total = args
            
            if not url:
                return (name, False, False)
            
            success, was_cached, content = self.fetch_single(url)
            
            if show_progress:
                if success and was_cached:
                    print(f"  ✅ [{idx:3d}/{total}] {name[:40]:40s} - cached")
                elif success:
                    size_kb = len(content) / 1024 if content else 0
                    print(f"  💾 [{idx:3d}/{total}] {name[:40]:40s} - {size_kb:6.1f}KB")
                else:
                    print(f"  ❌ [{idx:3d}/{total}] {name[:40]:40s} - failed")
            
            return (name, success, was_cached)
        
        # Process in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {
                executor.submit(process_single, args): args[0]
                for args in urls_with_names
            }
            
            for future in as_completed(future_to_name):
                name, success, was_cached = future.result()
                
                if success:
                    if was_cached:
                        stats['cached'] += 1
                    else:
                        stats['downloaded'] += 1
                else:
                    stats['failed'] += 1
        
        return stats
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear image cache.
        
        Args:
            older_than_days: Only clear files older than N days (None = all)
        """
        from datetime import datetime, timedelta
        
        deleted = 0
        
        for cache_file in self.cache_dir.glob("*.img"):
            should_delete = True
            
            if older_than_days is not None:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = datetime.now() - file_time
                should_delete = age > timedelta(days=older_than_days)
            
            if should_delete:
                cache_file.unlink()
                deleted += 1
        
        logger.info(f"Cleared {deleted} cached images")
        return deleted
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.img"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'files': len(cache_files),
            'size_bytes': total_size,
            'size_mb': total_size / 1024 / 1024,
            'cache_dir': str(self.cache_dir)
        }