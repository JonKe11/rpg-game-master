# backend/app/core/scraper/rate_limiter.py
import time

class RateLimiter:
    """Single responsibility: kontrola rate limiting"""
    
    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self.last_request = 0
    
    def wait_if_needed(self):
        """Czekaj jeśli trzeba przed następnym requestem"""
        elapsed = time.time() - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.time()