# backend/app/core/scraper/http_client.py
import requests
from typing import Optional
from .rate_limiter import RateLimiter

class WikiHttpClient:
    """Single responsibility: HTTP requests z error handling"""
    
    def __init__(self, rate_limiter: RateLimiter, timeout: int = 15):
        self.rate_limiter = rate_limiter
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def get(self, url: str) -> Optional[requests.Response]:
        """Wykonaj GET request z rate limiting i error handling"""
        self.rate_limiter.wait_if_needed()
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None