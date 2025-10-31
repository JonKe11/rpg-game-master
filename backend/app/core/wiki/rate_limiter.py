# backend/app/core/wiki/rate_limiter.py
"""
Advanced rate limiter with token bucket algorithm.

Features:
- Token bucket algorithm
- Async/await support
- Automatic refill
- Thread-safe
"""

import asyncio
import time


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Allows burst of requests up to max_tokens, then throttles
    to maintain steady rate.
    
    Example:
        limiter = RateLimiter(calls=150, period=60)
        
        async def make_request():
            await limiter.acquire()
            # Make request
    """
    
    def __init__(self, calls: int, period: int):
        """
        Initialize rate limiter.
        
        Args:
            calls: Number of calls allowed per period
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.rate = calls / period  # Tokens per second
        
        # Token bucket
        self.tokens = float(calls)
        self.max_tokens = float(calls)
        self.last_refill = time.monotonic()
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: float = 1.0):
        """
        Acquire tokens (wait if necessary).
        
        Args:
            tokens: Number of tokens to acquire (default: 1.0)
        """
        async with self._lock:
            # Refill tokens based on time elapsed
            now = time.monotonic()
            elapsed = now - self.last_refill
            
            # Add tokens based on time elapsed
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * self.rate
            )
            self.last_refill = now
            
            # Wait if not enough tokens
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= tokens
    
    def reset(self):
        """Reset rate limiter to full capacity"""
        self.tokens = self.max_tokens
        self.last_refill = time.monotonic()
    
    @property
    def available_tokens(self) -> float:
        """Get number of currently available tokens"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        
        return min(
            self.max_tokens,
            self.tokens + elapsed * self.rate
        )