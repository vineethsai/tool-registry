from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from redis import Redis
import time
import logging
import json

# Initialize logger for this module
logger = logging.getLogger(__name__)

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
        
        logger.info(f"RateLimiter initialized with limit: {rate_limit}/{time_window}s, Redis: {'Enabled' if not self._use_memory else 'Disabled'}")
        if self._use_memory:
            logger.warning("Redis client not provided. Using in-memory rate limiting (not distributed).")
    
    def _get_key(self, identifier: str) -> str:
        """Get Redis key for rate limiting."""
        key = f"rate_limit:{identifier}"
        logger.debug(f"Generated rate limit key: {key}")
        return key
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if a request is allowed based on rate limiting.
        
        Args:
            identifier: Unique identifier for the rate limit (e.g., IP address or agent ID)
        
        Returns:
            bool: True if request is allowed, False otherwise
        """
        now = time.time()
        now_dt = datetime.fromtimestamp(now).isoformat()
        logger.debug(f"Checking rate limit for {identifier} at {now_dt}")
        
        if self._use_memory or self.redis is None:
            logger.debug(f"Using in-memory rate limiting for: {identifier}")
            # Use in-memory storage
            return self._is_allowed_memory(identifier, now)
        
        try:
            key = self._get_key(identifier)
            
            # Remove old entries
            removed = self.redis.zremrangebyscore(key, 0, now - self.time_window)
            if removed > 0:
                logger.debug(f"Removed {removed} expired entries for {identifier} (window: {self.time_window}s)")
            
            # Get current count
            count = self.redis.zcard(key)
            logger.debug(f"Current request count for {identifier}: {count}/{self.rate_limit}")
            
            if count >= self.rate_limit:
                logger.warning(f"Rate limit exceeded for {identifier}: {count}/{self.rate_limit} at {now_dt} (window: {self.time_window}s)")
                return False
            
            # Add new entry
            self.redis.zadd(key, {str(now): now})
            self.redis.expire(key, self.time_window)
            
            # Log remaining capacity
            remaining = self.rate_limit - count - 1
            logger.debug(f"Request allowed for {identifier}, remaining: {remaining}/{self.rate_limit}, reset window: {self.time_window}s")
            return True
        except Exception as e:
            # Fallback to in-memory if Redis fails
            logger.error(f"Redis error in rate limiter: {str(e)}. Falling back to in-memory storage. Identifier: {identifier}")
            self._use_memory = True
            return self._is_allowed_memory(identifier, now)
    
    def _is_allowed_memory(self, identifier: str, now: float) -> bool:
        """In-memory implementation of rate limiting."""
        key = self._get_key(identifier)
        now_dt = datetime.fromtimestamp(now).isoformat()
        
        if key not in self._memory_storage:
            logger.debug(f"First request for {identifier}, initializing in-memory storage at {now_dt}")
            self._memory_storage[key] = []
        
        # Remove old entries
        original_len = len(self._memory_storage[key])
        self._memory_storage[key] = [
            ts for ts in self._memory_storage[key] 
            if ts > now - self.time_window
        ]
        removed = original_len - len(self._memory_storage[key])
        if removed > 0:
            logger.debug(f"Removed {removed} expired in-memory entries for {identifier} (window: {self.time_window}s)")
        
        # Check current count
        current_count = len(self._memory_storage[key])
        if current_count >= self.rate_limit:
            logger.warning(f"In-memory rate limit exceeded for {identifier}: {current_count}/{self.rate_limit} at {now_dt}")
            return False
        
        # Add new entry
        self._memory_storage[key].append(now)
        
        # Log remaining capacity
        remaining = self.rate_limit - len(self._memory_storage[key])
        logger.debug(f"In-memory request allowed for {identifier}, remaining: {remaining}/{self.rate_limit}, count: {len(self._memory_storage[key])}")
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
                logger.debug(f"No in-memory data for {identifier}, full limit available: {self.rate_limit}")
                return self.rate_limit
            
            # Remove old entries
            original_len = len(self._memory_storage[key])
            self._memory_storage[key] = [
                ts for ts in self._memory_storage[key] 
                if ts > now - self.time_window
            ]
            removed = original_len - len(self._memory_storage[key])
            if removed > 0:
                logger.debug(f"Cleaned up {removed} expired entries when checking remaining for {identifier}")
            
            remaining = max(0, self.rate_limit - len(self._memory_storage[key]))
            logger.debug(f"In-memory remaining for {identifier}: {remaining}/{self.rate_limit}, used: {len(self._memory_storage[key])}")
            return remaining
        
        try:
            key = self._get_key(identifier)
            
            # Remove old entries
            removed = self.redis.zremrangebyscore(key, 0, now - self.time_window)
            if removed > 0:
                logger.debug(f"Cleaned up {removed} expired Redis entries when checking remaining for {identifier}")
            
            # Get current count
            count = self.redis.zcard(key)
            
            remaining = max(0, self.rate_limit - count)
            logger.debug(f"Redis remaining for {identifier}: {remaining}/{self.rate_limit}, used: {count}")
            return remaining
        except Exception as e:
            # Fallback to in-memory if Redis fails
            logger.error(f"Redis error in get_remaining: {str(e)}. Falling back to in-memory storage for {identifier}")
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
                now_dt = datetime.fromtimestamp(now)
                logger.debug(f"No in-memory rate limit data for {identifier}, reset time is now: {now_dt.isoformat()}")
                return now_dt
            
            oldest = min(self._memory_storage[key])
            reset_time = oldest + self.time_window
            reset_datetime = datetime.fromtimestamp(reset_time)
            logger.debug(f"In-memory reset time for {identifier}: {reset_datetime.isoformat()}, oldest request: {datetime.fromtimestamp(oldest).isoformat()}")
            return reset_datetime
        
        try:
            key = self._get_key(identifier)
            
            # Get the oldest entry
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            
            if not oldest:
                now_dt = datetime.fromtimestamp(now)
                logger.debug(f"No Redis rate limit data for {identifier}, reset time is now: {now_dt.isoformat()}")
                return now_dt
            
            oldest_time = oldest[0][1]
            reset_time = oldest_time + self.time_window
            reset_datetime = datetime.fromtimestamp(reset_time)
            logger.debug(f"Redis reset time for {identifier}: {reset_datetime.isoformat()}, oldest request: {datetime.fromtimestamp(oldest_time).isoformat()}")
            return reset_datetime
        except Exception as e:
            # Fallback to in-memory if Redis fails
            logger.error(f"Redis error in get_reset_time: {str(e)}. Falling back to in-memory storage for {identifier}")
            self._use_memory = True
            return self.get_reset_time(identifier)

def rate_limit_middleware(limiter: RateLimiter):
    """FastAPI middleware for rate limiting."""
    async def middleware(request, call_next):
        # Get identifier (e.g., IP address or agent ID)
        if request.client is None:
            # In test environment, client might be None
            identifier = "test_client"
            logger.debug("Using test_client identifier for rate limiting (no client IP)")
        else:
            identifier = request.client.host
            logger.info(f"Rate limiting check for IP: {identifier}, path: {request.url.path}, method: {request.method}")
        
        if not limiter.is_allowed(identifier):
            reset_time = limiter.get_reset_time(identifier)
            remaining = limiter.get_remaining(identifier)
            
            logger.warning(
                f"Rate limit exceeded for {identifier}. "
                f"Reset at {reset_time.isoformat()}, "
                f"path: {request.url.path}, "
                f"method: {request.method}, "
                f"remaining: {remaining}/{limiter.rate_limit}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "reset_time": reset_time.isoformat(),
                    "remaining": remaining,
                    "limit": limiter.rate_limit
                }
            )
        
        # Log request allowed
        logger.debug(f"Request allowed for {identifier}, proceeding with handler, path: {request.url.path}")
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = limiter.get_remaining(identifier)
        reset_time = limiter.get_reset_time(identifier)
        
        response.headers["X-RateLimit-Limit"] = str(limiter.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = reset_time.isoformat()
        
        logger.debug(
            f"Response for {identifier}, "
            f"status: {response.status_code}, "
            f"remaining: {remaining}/{limiter.rate_limit}, "
            f"reset: {reset_time.isoformat()}"
        )
        
        return response
    
    return middleware 