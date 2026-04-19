# app/auth/redis.py

import logging

logger = logging.getLogger(__name__)

# Redis is optional. If unavailable, token blacklisting is simply skipped.
_redis = None


async def get_redis():
    """Return a Redis connection, or None if Redis is not configured."""
    global _redis
    if _redis is None:
        try:
            import aioredis
            from app.core.config import get_settings
            s = get_settings()
            if s.REDIS_URL:
                _redis = await aioredis.from_url(s.REDIS_URL)
        except Exception as e:
            logger.warning(f"Redis unavailable, token blacklisting disabled: {e}")
    return _redis


async def add_to_blacklist(jti: str, exp: int):
    """Add a token JTI to the Redis blacklist."""
    redis = await get_redis()
    if redis:
        await redis.set(f"blacklist:{jti}", "1", ex=exp)


async def is_blacklisted(jti: str) -> bool:
    """Check whether a token JTI is blacklisted."""
    redis = await get_redis()
    if redis:
        return bool(await redis.exists(f"blacklist:{jti}"))
    return False
