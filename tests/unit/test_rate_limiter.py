"""Unit tests for rate limiter module."""

import asyncio
import time

import pytest

from data4ai.rate_limiter import (
    AdaptiveRateLimiter,
    RateLimitConfig,
    RequestMetrics,
    TokenBucket,
)


class TestTokenBucket:
    """Test token bucket rate limiter."""

    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test that token bucket enforces rate limit."""
        # 10 tokens per second, capacity of 10
        bucket = TokenBucket(rate=10, capacity=10)

        # Should be able to acquire 10 tokens immediately
        wait_time = await bucket.acquire(10)
        assert wait_time == 0

        # Should have to wait for more tokens
        start = time.monotonic()
        wait_time = await bucket.acquire(5)
        elapsed = time.monotonic() - start

        # Should wait approximately 0.5 seconds for 5 tokens at rate of 10/sec
        assert elapsed >= 0.4  # Allow some tolerance
        assert wait_time > 0

    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens refill over time."""
        bucket = TokenBucket(rate=10, capacity=10)

        # Consume all tokens
        await bucket.acquire(10)
        assert bucket.tokens == 0

        # Wait for refill
        await asyncio.sleep(0.5)

        # Should have ~5 tokens now (10 per second * 0.5 seconds)
        bucket._refill()
        assert 4 <= bucket.tokens <= 6  # Allow tolerance

    @pytest.mark.asyncio
    async def test_capacity_limit(self):
        """Test that bucket doesn't exceed capacity."""
        bucket = TokenBucket(rate=10, capacity=5)

        # Wait to ensure full capacity
        await asyncio.sleep(1)
        bucket._refill()

        # Should not exceed capacity even with time passing
        assert bucket.tokens <= 5


class TestAdaptiveRateLimiter:
    """Test adaptive rate limiter."""

    @pytest.mark.asyncio
    async def test_basic_acquire_release(self):
        """Test basic acquire and release operations."""
        config = RateLimitConfig(requests_per_minute=60, max_concurrent=2)
        limiter = AdaptiveRateLimiter(config)

        # Should be able to acquire
        await limiter.acquire()

        # Release should work
        limiter.release()

    @pytest.mark.asyncio
    async def test_concurrent_limit(self):
        """Test that concurrent request limit is enforced."""
        config = RateLimitConfig(max_concurrent=2)
        limiter = AdaptiveRateLimiter(config)

        # Acquire 2 slots
        await limiter.acquire()
        await limiter.acquire()

        # Third should block (test with timeout)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(limiter.acquire(), timeout=0.1)

        # Release one and try again
        limiter.release()
        await asyncio.wait_for(limiter.acquire(), timeout=0.1)  # Should succeed

    @pytest.mark.asyncio
    async def test_handle_429_backoff(self):
        """Test that 429 errors trigger backoff."""
        config = RateLimitConfig()
        limiter = AdaptiveRateLimiter(config)

        initial_rate = limiter.bucket.rate

        # Handle 429 error
        await limiter.handle_429(retry_after=1)

        # Rate should be reduced
        assert limiter.bucket.rate < initial_rate
        assert limiter.consecutive_429s == 1
        assert limiter.backoff_until > time.time()

    @pytest.mark.asyncio
    async def test_handle_success_recovery(self):
        """Test that successful requests restore rate."""
        config = RateLimitConfig()
        limiter = AdaptiveRateLimiter(config)

        # Simulate previous 429
        limiter.current_rate_multiplier = 0.5
        limiter.bucket.rate = (config.requests_per_minute / 60.0) * 0.5
        limiter.consecutive_429s = 3

        # Handle success
        limiter.handle_success()

        # Should start recovering
        assert limiter.consecutive_429s == 0
        assert limiter.current_rate_multiplier > 0.5

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test rate limiter as context manager."""
        config = RateLimitConfig()
        limiter = AdaptiveRateLimiter(config)

        async with limiter:
            # Should have acquired
            pass

        # Should have released and handled success
        assert limiter.consecutive_429s == 0


class TestRequestMetrics:
    """Test request metrics tracking."""

    def test_record_request(self):
        """Test recording request metrics."""
        metrics = RequestMetrics(window_size=60)

        # Record some requests
        metrics.record_request(success=True, latency=1.0, tokens=100)
        metrics.record_request(success=False, latency=2.0, tokens=0)
        metrics.record_request(success=True, latency=1.5, tokens=150)

        assert metrics.total_requests == 3
        assert metrics.total_errors == 1
        assert metrics.total_tokens == 250

    def test_get_metrics(self):
        """Test getting aggregated metrics."""
        metrics = RequestMetrics()

        # Record requests
        for i in range(10):
            metrics.record_request(success=(i % 2 == 0), latency=1.0, tokens=10)

        stats = metrics.get_metrics()

        assert stats["total_requests"] == 10
        assert stats["total_errors"] == 5
        assert stats["success_rate"] == 0.5
        assert stats["avg_latency"] == 1.0
        assert stats["total_tokens"] == 100

    def test_window_cleanup(self):
        """Test that old entries are cleaned up."""
        metrics = RequestMetrics(window_size=1)  # 1 second window

        # Record old request
        metrics.record_request(success=True, latency=1.0)

        # Wait for window to pass
        time.sleep(1.1)

        # Record new request
        metrics.record_request(success=True, latency=2.0)

        # Old request should be cleaned
        stats = metrics.get_metrics()
        assert stats["requests_per_minute"] == 1  # Only the new request

    def test_empty_metrics(self):
        """Test metrics when no requests recorded."""
        metrics = RequestMetrics()
        stats = metrics.get_metrics()

        assert stats["requests_per_minute"] == 0
        assert stats["success_rate"] == 0
        assert stats["avg_latency"] == 0
        assert stats["total_requests"] == 0
