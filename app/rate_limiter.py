"""Rate limiting with Redis support and safe in-memory fallback."""
import logging
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._memory_windows: dict[str, deque] = defaultdict(deque)
        self._redis = None

        if Redis and settings.redis_url:
            try:
                self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("Redis-backed rate limiter enabled")
            except Exception as exc:
                logger.warning("Redis unavailable for rate limiting, using memory fallback: %s", exc)
                self._redis = None

    def check(self, bucket: str) -> dict:
        if self._redis:
            try:
                return self._check_redis(bucket)
            except Exception as exc:
                logger.warning("Redis rate limit check failed, falling back to memory: %s", exc)
        return self._check_memory(bucket)

    def _raise_limit(self, retry_after: int):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": self.max_requests,
                "window_seconds": self.window_seconds,
                "retry_after_seconds": retry_after,
            },
            headers={
                "X-RateLimit-Limit": str(self.max_requests),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(retry_after),
            },
        )

    def _check_memory(self, bucket: str) -> dict:
        now = time.time()
        window = self._memory_windows[bucket]

        while window and window[0] < now - self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            oldest = window[0]
            retry_after = int(oldest + self.window_seconds - now) + 1
            self._raise_limit(retry_after)

        window.append(now)
        remaining = max(0, self.max_requests - len(window))
        return {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset_after_seconds": self.window_seconds,
            "storage": "memory",
        }

    def _check_redis(self, bucket: str) -> dict:
        now = time.time()
        key = f"rate_limit:{bucket}"
        member = f"{now}:{time.monotonic_ns()}"

        pipeline = self._redis.pipeline()
        pipeline.zremrangebyscore(key, "-inf", now - self.window_seconds)
        pipeline.zcard(key)
        _, current_count = pipeline.execute()

        if int(current_count) >= self.max_requests:
            oldest = self._redis.zrange(key, 0, 0, withscores=True)
            retry_after = self.window_seconds
            if oldest:
                retry_after = max(1, int(oldest[0][1] + self.window_seconds - now) + 1)
            self._raise_limit(retry_after)

        pipeline = self._redis.pipeline()
        pipeline.zadd(key, {member: now})
        pipeline.expire(key, self.window_seconds + 5)
        pipeline.execute()

        remaining = max(0, self.max_requests - int(current_count) - 1)
        return {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset_after_seconds": self.window_seconds,
            "storage": "redis",
        }


rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60,
)
