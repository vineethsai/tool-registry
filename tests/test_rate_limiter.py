import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import Request, Response, HTTPException

from tool_registry.core.rate_limit import RateLimiter, rate_limit_middleware


class TestRateLimiter:
    """Test suite for the RateLimiter module."""
    
    def test_init(self):
        """Test initialization of the rate limiter."""
        redis_mock = MagicMock()
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=100, time_window=60)
        
        assert limiter.redis == redis_mock
        assert limiter.rate_limit == 100
        assert limiter.time_window == 60
        assert limiter._memory_storage == {}
        assert limiter._use_memory is False
    
    def test_init_no_redis(self):
        """Test initialization without Redis client."""
        limiter = RateLimiter(redis_client=None, rate_limit=100, time_window=60)
        
        assert limiter.redis is None
        assert limiter.rate_limit == 100
        assert limiter.time_window == 60
        assert limiter._memory_storage == {}
        assert limiter._use_memory is True
    
    def test_get_key(self):
        """Test key generation."""
        limiter = RateLimiter(redis_client=None, rate_limit=100, time_window=60)
        key = limiter._get_key("test-identifier")
        
        assert key == "rate_limit:test-identifier"
    
    def test_is_allowed_memory_first_request(self):
        """Test that the first request is allowed in memory mode."""
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=60)
        allowed = limiter.is_allowed("test-identifier")
        
        assert allowed is True
        assert len(limiter._memory_storage["rate_limit:test-identifier"]) == 1
    
    def test_is_allowed_memory_within_limit(self):
        """Test that requests within the rate limit are allowed in memory mode."""
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=60)
        
        # Make 4 requests (under the limit of 5)
        for _ in range(4):
            allowed = limiter.is_allowed("test-identifier")
            assert allowed is True
        
        assert len(limiter._memory_storage["rate_limit:test-identifier"]) == 4
    
    def test_is_allowed_memory_exceeds_limit(self):
        """Test that requests exceeding the rate limit are blocked in memory mode."""
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=60)
        
        # Make 5 requests (at the limit)
        for _ in range(5):
            allowed = limiter.is_allowed("test-identifier")
            assert allowed is True
        
        # The 6th request should be blocked
        allowed = limiter.is_allowed("test-identifier")
        assert allowed is False
    
    def test_is_allowed_memory_window_reset(self):
        """Test that the rate limit resets after the time window in memory mode."""
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=1)  # 1 second window
        
        # Make 5 requests (at the limit)
        for _ in range(5):
            allowed = limiter.is_allowed("test-identifier")
            assert allowed is True
        
        # The 6th request should be blocked
        allowed = limiter.is_allowed("test-identifier")
        assert allowed is False
        
        # Wait for the window to reset
        time.sleep(1.1)
        
        # Now requests should be allowed again
        allowed = limiter.is_allowed("test-identifier")
        assert allowed is True
    
    def test_is_allowed_redis(self):
        """Test that requests are properly rate limited using Redis."""
        redis_mock = MagicMock()
        # Mock successful Redis operations
        redis_mock.zremrangebyscore.return_value = 0
        redis_mock.zcard.return_value = 3  # 3 requests made so far
        redis_mock.zadd.return_value = 1
        redis_mock.expire.return_value = True
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        allowed = limiter.is_allowed("test-identifier")
        
        assert allowed is True
        redis_mock.zremrangebyscore.assert_called_once()
        redis_mock.zcard.assert_called_once()
        redis_mock.zadd.assert_called_once()
        redis_mock.expire.assert_called_once()
    
    def test_is_allowed_redis_exceeds_limit(self):
        """Test that requests exceeding the rate limit are blocked using Redis."""
        redis_mock = MagicMock()
        # Mock Redis returning a count at the limit
        redis_mock.zremrangebyscore.return_value = 0
        redis_mock.zcard.return_value = 5  # 5 requests made so far (at the limit)
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        allowed = limiter.is_allowed("test-identifier")
        
        assert allowed is False
        redis_mock.zremrangebyscore.assert_called_once()
        redis_mock.zcard.assert_called_once()
        redis_mock.zadd.assert_not_called()
    
    def test_is_allowed_redis_error_fallback(self):
        """Test fallback to memory storage when Redis errors."""
        redis_mock = MagicMock()
        # Make Redis throw an exception
        redis_mock.zremrangebyscore.side_effect = Exception("Redis error")
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        
        # Should fall back to in-memory storage
        allowed = limiter.is_allowed("test-identifier")
        
        assert allowed is True
        assert limiter._use_memory is True
        assert len(limiter._memory_storage["rate_limit:test-identifier"]) == 1
    
    def test_get_remaining_memory(self):
        """Test getting remaining requests count in memory mode."""
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=60)
        
        # Make 3 requests
        for _ in range(3):
            limiter.is_allowed("test-identifier")
        
        # Should have 2 remaining
        remaining = limiter.get_remaining("test-identifier")
        assert remaining == 2
    
    def test_get_remaining_memory_no_data(self):
        """Test getting remaining requests when no requests have been made."""
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=60)
        
        # No requests made yet
        remaining = limiter.get_remaining("test-identifier")
        assert remaining == 5
    
    def test_get_remaining_redis(self):
        """Test getting remaining requests count using Redis."""
        redis_mock = MagicMock()
        redis_mock.zremrangebyscore.return_value = 0
        redis_mock.zcard.return_value = 3  # 3 requests made so far
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        remaining = limiter.get_remaining("test-identifier")
        
        assert remaining == 2
        redis_mock.zremrangebyscore.assert_called_once()
        redis_mock.zcard.assert_called_once()
    
    def test_get_remaining_redis_error_fallback(self):
        """Test fallback to memory storage for get_remaining when Redis errors."""
        redis_mock = MagicMock()
        # Make Redis throw an exception
        redis_mock.zremrangebyscore.side_effect = Exception("Redis error")
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        
        # Should fall back to in-memory storage
        remaining = limiter.get_remaining("test-identifier")
        
        assert remaining == 5  # Full limit available
        assert limiter._use_memory is True
    
    @patch('tool_registry.core.rate_limit.datetime')
    def test_get_reset_time_memory(self, mock_datetime):
        """Test getting reset time in memory mode."""
        # Mock datetime.utcnow to return consistent values
        now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_datetime.fromtimestamp.side_effect = datetime.fromtimestamp
        
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=60)
        
        # Set a timestamp in the storage
        now_ts = time.time()
        limiter._memory_storage["rate_limit:test-identifier"] = [now_ts]
        
        reset_time = limiter.get_reset_time("test-identifier")
        
        # Should be about 60 seconds after the entry
        expected_reset = datetime.fromtimestamp(now_ts + 60)
        assert reset_time == expected_reset
    
    def test_get_reset_time_memory_no_data(self):
        """Test getting reset time when no requests have been made."""
        limiter = RateLimiter(redis_client=None, rate_limit=5, time_window=60)
        
        # No requests made yet
        reset_time = limiter.get_reset_time("test-identifier")
        
        # Should be a datetime instance
        assert isinstance(reset_time, datetime)
    
    def test_get_reset_time_redis(self):
        """Test getting reset time using Redis."""
        current_time = time.time()
        redis_mock = MagicMock()
        # Redis will return this value as the oldest timestamp
        redis_mock.zrange.return_value = [(b"entry", current_time)]
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        reset_time = limiter.get_reset_time("test-identifier")
        
        # Should be about 60 seconds after the oldest entry
        expected_reset = datetime.fromtimestamp(current_time + 60)
        delta = (reset_time - expected_reset).total_seconds()
        assert -1 <= delta <= 1
    
    def test_get_reset_time_redis_no_data(self):
        """Test getting reset time when no data exists in Redis."""
        redis_mock = MagicMock()
        redis_mock.zrange.return_value = []  # No entries
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        reset_time = limiter.get_reset_time("test-identifier")
        
        # Should be a datetime instance
        assert isinstance(reset_time, datetime)
    
    def test_get_reset_time_redis_error_fallback(self):
        """Test fallback to memory storage for get_reset_time when Redis errors."""
        redis_mock = MagicMock()
        # Make Redis throw an exception
        redis_mock.zrange.side_effect = Exception("Redis error")
        
        limiter = RateLimiter(redis_client=redis_mock, rate_limit=5, time_window=60)
        
        # Should fall back to in-memory storage
        reset_time = limiter.get_reset_time("test-identifier")
        
        # Should be a datetime instance
        assert isinstance(reset_time, datetime)
        assert limiter._use_memory is True


@pytest.fixture
def mock_request():
    """Create a mock request for testing middleware."""
    request = MagicMock(spec=Request)
    client = MagicMock()
    client.host = "127.0.0.1"
    request.client = client
    request.url = MagicMock()
    request.url.path = "/test-path"
    request.method = "GET"
    return request


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function for testing middleware."""
    async def call_next(request):
        response = MagicMock()
        response.headers = {}
        response.status_code = 200
        return response
    return call_next


@pytest.mark.asyncio
class TestRateLimitMiddleware:
    """Test suite for the rate limit middleware."""
    
    async def test_middleware_allowed(self, mock_request, mock_call_next):
        """Test middleware allows requests within rate limit."""
        limiter = MagicMock(spec=RateLimiter)
        limiter.is_allowed.return_value = True
        limiter.get_remaining.return_value = 99
        reset_time = datetime.utcnow() + timedelta(seconds=60)
        limiter.get_reset_time.return_value = reset_time
        limiter.rate_limit = 100
        limiter.time_window = 60
        
        middleware_func = rate_limit_middleware(limiter)
        response = await middleware_func(mock_request, mock_call_next)
        
        assert response is not None
        limiter.is_allowed.assert_called_once_with("127.0.0.1")
        
        # Headers should be set
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "99"
        assert response.headers["X-RateLimit-Reset"] == reset_time.isoformat()
    
    async def test_middleware_blocked(self, mock_request, mock_call_next):
        """Test middleware blocks requests that exceed rate limit."""
        limiter = MagicMock(spec=RateLimiter)
        limiter.is_allowed.return_value = False
        limiter.get_remaining.return_value = 0
        reset_time = datetime.utcnow() + timedelta(seconds=60)
        limiter.get_reset_time.return_value = reset_time
        limiter.rate_limit = 100
        limiter.time_window = 60
        
        middleware_func = rate_limit_middleware(limiter)
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware_func(mock_request, mock_call_next)
        
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value.detail)
        limiter.is_allowed.assert_called_once_with("127.0.0.1")
    
    async def test_middleware_no_client(self, mock_call_next):
        """Test middleware handles case when client info is not available."""
        mock_request = MagicMock(spec=Request)
        mock_request.client = None  # No client info
        mock_request.url = MagicMock()
        mock_request.url.path = "/test-path"
        mock_request.method = "GET"
        
        limiter = MagicMock(spec=RateLimiter)
        limiter.is_allowed.return_value = True
        limiter.get_remaining.return_value = 99
        reset_time = datetime.utcnow() + timedelta(seconds=60)
        limiter.get_reset_time.return_value = reset_time
        limiter.rate_limit = 100
        limiter.time_window = 60
        
        middleware_func = rate_limit_middleware(limiter)
        response = await middleware_func(mock_request, mock_call_next)
        
        assert response is not None
        limiter.is_allowed.assert_called_once_with("test_client")  # Should use default test_client identifier 