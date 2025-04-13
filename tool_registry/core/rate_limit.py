from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from redis import Redis
import time

class RateLimiter:
    def __init__(self, redis_client: Redis = None, rate_limit: int = 100, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client for storing rate limit data
            rate_limit: Maximum number of requests allowed in the time window
            time_window: Time window in seconds (default: 60 seconds)
        """
        self.redis = redis_client
        self.rate_limit = rate_limit
        self.time_window = time_window
        
        # In-memory fallback for when Redis is not available
        self._memory_storage = {}
        self._use_memory = redis_client is None
    
    def _get_key(self, identifier: str) -> str:
        """Get Redis key for rate limiting."""
        return f"rate_limit:{identifier}"
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if a request is allowed based on rate limiting.
        
        Args:
            identifier: Unique identifier for the rate limit (e.g., IP address or agent ID)
        
        Returns:
            bool: True if request is allowed, False otherwise
        """
        now = time.time()
        
        if self._use_memory or self.redis is None:
            # Use in-memory storage
            return self._is_allowed_memory(identifier, now)
        
        try:
            key = self._get_key(identifier)
            
            # Remove old entries
            self.redis.zremrangebyscore(key, 0, now - self.time_window)
            
            # Get current count
            count = self.redis.zcard(key)
            
            if count >= self.rate_limit:
                return False
            
            # Add new entry
            self.redis.zadd(key, {str(now): now})
            self.redis.expire(key, self.time_window)
            
            return True
        except Exception as e:
            # Fallback to in-memory if Redis fails
            self._use_memory = True
            return self._is_allowed_memory(identifier, now)
    
    def _is_allowed_memory(self, identifier: str, now: float) -> bool:
        """In-memory implementation of rate limiting."""
        key = self._get_key(identifier)
        
        if key not in self._memory_storage:
            self._memory_storage[key] = []
        
        # Remove old entries
        self._memory_storage[key] = [
            ts for ts in self._memory_storage[key] 
            if ts > now - self.time_window
        ]
        
        # Check current count
        if len(self._memory_storage[key]) >= self.rate_limit:
            return False
        
        # Add new entry
        self._memory_storage[key].append(now)
        
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """
        Get remaining requests in the current time window.
        
        Args:
            identifier: Unique identifier for the rate limit
        
        Returns:
            int: Number of remaining requests
        """
        now = time.time()
        
        if self._use_memory or self.redis is None:
            # Use in-memory storage
            key = self._get_key(identifier)
            if key not in self._memory_storage:
                return self.rate_limit
            
            # Remove old entries
            self._memory_storage[key] = [
                ts for ts in self._memory_storage[key] 
                if ts > now - self.time_window
            ]
            
            return max(0, self.rate_limit - len(self._memory_storage[key]))
        
        try:
            key = self._get_key(identifier)
            
            # Remove old entries
            self.redis.zremrangebyscore(key, 0, now - self.time_window)
            
            # Get current count
            count = self.redis.zcard(key)
            
            return max(0, self.rate_limit - count)
        except Exception:
            # Fallback to in-memory if Redis fails
            self._use_memory = True
            return self.get_remaining(identifier)
    
    def get_reset_time(self, identifier: str) -> datetime:
        """
        Get the time when the rate limit will reset.
        
        Args:
            identifier: Unique identifier for the rate limit
        
        Returns:
            datetime: Time when the rate limit will reset
        """
        now = time.time()
        
        if self._use_memory or self.redis is None:
            # Use in-memory storage
            key = self._get_key(identifier)
            if key not in self._memory_storage or not self._memory_storage[key]:
                return datetime.fromtimestamp(now)
            
            oldest = min(self._memory_storage[key])
            reset_time = oldest + self.time_window
            return datetime.fromtimestamp(reset_time)
        
        try:
            key = self._get_key(identifier)
            
            # Get the oldest entry
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            
            if not oldest:
                return datetime.fromtimestamp(now)
            
            reset_time = oldest[0][1] + self.time_window
            return datetime.fromtimestamp(reset_time)
        except Exception:
            # Fallback to in-memory if Redis fails
            self._use_memory = True
            return self.get_reset_time(identifier)

def rate_limit_middleware(limiter: RateLimiter):
    """FastAPI middleware for rate limiting."""
    async def middleware(request, call_next):
        # Get identifier (e.g., IP address or agent ID)
        if request.client is None:
            # In test environment, client might be None
            identifier = "test_client"
        else:
            identifier = request.client.host
        
        if not limiter.is_allowed(identifier):
            reset_time = limiter.get_reset_time(identifier)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "reset_time": reset_time.isoformat(),
                    "remaining": limiter.get_remaining(identifier)
                }
            )
        
        response = await call_next(request)
        return response
    
    return middleware 