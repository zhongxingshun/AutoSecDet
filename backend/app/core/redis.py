"""
Redis connection configuration.
"""
import redis

from app.core.config import settings


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


redis_client = get_redis_client()
