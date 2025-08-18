"""Rate limiting for API calls."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("data4ai")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    max_concurrent: int = 10
    burst_size: int = 20
    retry_after_default: int = 60


class TokenBucket:
    """Token bucket rate limiter for smooth request distribution."""

    def __init__(self, rate: float, capacity: int):
        """Initialize token bucket.

        Args:
            rate: Tokens per second to add
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> float:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Time waited in seconds
        """
        async with self.lock:
            wait_time = 0.0

            while tokens > self.tokens:
                # Calculate how long to wait for enough tokens
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate

                logger.debug(
                    f"Rate limit: waiting {wait_time:.2f}s for {tokens} tokens"
                )
                await asyncio.sleep(wait_time)

                # Update tokens
                self._refill()

            self.tokens -= tokens
            return wait_time

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update

        # Add tokens based on rate
        tokens_to_add = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_update = now


class AdaptiveRateLimiter:
    """Adaptive rate limiter that responds to 429 errors."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize adaptive rate limiter."""
        self.config = config or RateLimitConfig()

        # Convert requests per minute to tokens per second
        tokens_per_second = self.config.requests_per_minute / 60.0

        self.bucket = TokenBucket(
            rate=tokens_per_second, capacity=self.config.burst_size
        )

        # Concurrency control
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)

        # Adaptive backoff state
        self.consecutive_429s = 0
        self.backoff_until = 0
        self.current_rate_multiplier = 1.0

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        # Check if we're in backoff
        if self.backoff_until > time.time():
            wait_time = self.backoff_until - time.time()
            logger.info(f"Rate limit backoff: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

        # Acquire from token bucket
        await self.bucket.acquire()

        # Acquire concurrency slot
        await self.semaphore.acquire()

    def release(self) -> None:
        """Release concurrency slot."""
        self.semaphore.release()

    async def handle_429(self, retry_after: Optional[int] = None) -> None:
        """Handle a 429 rate limit response.

        Args:
            retry_after: Seconds to wait before retrying
        """
        self.consecutive_429s += 1

        # Use provided retry_after or exponential backoff
        if retry_after:
            wait_time = retry_after
        else:
            wait_time = min(
                self.config.retry_after_default * (2**self.consecutive_429s),
                300,  # Max 5 minutes
            )

        self.backoff_until = time.time() + wait_time

        # Reduce rate for future requests
        self.current_rate_multiplier *= 0.5
        new_rate = (
            self.config.requests_per_minute / 60.0
        ) * self.current_rate_multiplier
        self.bucket.rate = max(new_rate, 0.1)  # Minimum 6 requests per minute

        logger.warning(
            f"Got 429 (#{self.consecutive_429s}), "
            f"backing off {wait_time}s, "
            f"reducing rate to {self.bucket.rate * 60:.1f} req/min"
        )

    def handle_success(self) -> None:
        """Handle a successful request."""
        # Reset consecutive 429 counter
        self.consecutive_429s = 0

        # Gradually increase rate back to normal
        if self.current_rate_multiplier < 1.0:
            self.current_rate_multiplier = min(1.0, self.current_rate_multiplier * 1.1)
            new_rate = (
                self.config.requests_per_minute / 60.0
            ) * self.current_rate_multiplier
            self.bucket.rate = new_rate

    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Mark unused traceback as intentionally unused for linters/tools like vulture
        del exc_tb
        self.release()

        # Handle exceptions
        if exc_type is None:
            self.handle_success()
        elif (
            hasattr(exc_val, "response")
            and hasattr(exc_val.response, "status_code")
            and exc_val.response.status_code == 429
        ):
            retry_after = exc_val.response.headers.get("Retry-After")
            await self.handle_429(int(retry_after) if retry_after else None)


class RequestMetrics:
    """Track request metrics for monitoring."""

    def __init__(self, window_size: int = 60):
        """Initialize metrics tracker.

        Args:
            window_size: Seconds to track for rolling metrics
        """
        self.window_size = window_size
        self.requests = []  # List of (timestamp, success, latency)
        self.total_requests = 0
        self.total_errors = 0
        self.total_tokens = 0

    def record_request(self, success: bool, latency: float, tokens: int = 0) -> None:
        """Record a request."""
        now = time.time()
        self.requests.append((now, success, latency))

        self.total_requests += 1
        if not success:
            self.total_errors += 1
        self.total_tokens += tokens

        # Clean old entries
        cutoff = now - self.window_size
        self.requests = [
            (ts, succ, lat) for ts, succ, lat in self.requests if ts > cutoff
        ]

    def get_metrics(self) -> dict:
        """Get current metrics."""
        if not self.requests:
            return {
                "requests_per_minute": 0,
                "success_rate": 0,
                "avg_latency": 0,
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "total_tokens": self.total_tokens,
            }

        now = time.time()
        recent = [r for r in self.requests if r[0] > now - 60]

        if recent:
            success_count = sum(1 for _, success, _ in recent if success)
            avg_latency = sum(lat for _, _, lat in recent) / len(recent)
            success_rate = success_count / len(recent)
        else:
            avg_latency = 0
            success_rate = 0

        return {
            "requests_per_minute": len(recent),
            "success_rate": success_rate,
            "avg_latency": avg_latency,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_tokens": self.total_tokens,
        }
