import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[Any, float]] = {}


def get_cached(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        del _cache[key]
        return None
    return value


def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    expires_at = time.time() + ttl
    _cache[key] = (value, expires_at)


def clear_cache(pattern: Optional[str] = None) -> None:
    global _cache
    if pattern is None:
        _cache.clear()
        logger.info("Cache cleared entirely")
        return
    keys_to_delete = [k for k in _cache if pattern in k]
    for k in keys_to_delete:
        del _cache[k]
    if keys_to_delete:
        logger.info("Cache cleared for pattern '%s': %d keys", pattern, len(keys_to_delete))


class CacheManager:
    ANALYTICS_TTL = 300
    FORECAST_TTL = 3600
    BUDGET_TTL = 1800

    @staticmethod
    def analytics_key(user_id: str, method: str, *args) -> str:
        return f"analytics:{user_id}:{method}:{':'.join(str(a) for a in args)}"

    @staticmethod
    def forecast_key(user_id: str, method: str, *args) -> str:
        return f"forecast:{user_id}:{method}:{':'.join(str(a) for a in args)}"

    @staticmethod
    def budget_key(user_id: str, month: str = "") -> str:
        return f"budget:{user_id}:{month}"

    @classmethod
    def get_analytics(cls, user_id: str, method: str, *args) -> Optional[Any]:
        return get_cached(cls.analytics_key(user_id, method, *args))

    @classmethod
    def set_analytics(cls, user_id: str, method: str, value: Any, *args) -> None:
        set_cache(cls.analytics_key(user_id, method, *args), value, cls.ANALYTICS_TTL)

    @classmethod
    def get_forecast(cls, user_id: str, method: str, *args) -> Optional[Any]:
        return get_cached(cls.forecast_key(user_id, method, *args))

    @classmethod
    def set_forecast(cls, user_id: str, method: str, value: Any, *args) -> None:
        set_cache(cls.forecast_key(user_id, method, *args), value, cls.FORECAST_TTL)

    @classmethod
    def get_budget(cls, user_id: str, month: str = "") -> Optional[Any]:
        return get_cached(cls.budget_key(user_id, month))

    @classmethod
    def set_budget(cls, user_id: str, value: Any, month: str = "") -> None:
        set_cache(cls.budget_key(user_id, month), value, cls.BUDGET_TTL)

    @classmethod
    def invalidate_analytics(cls, user_id: str) -> None:
        clear_cache(f"analytics:{user_id}:")

    @classmethod
    def invalidate_forecast(cls, user_id: str) -> None:
        clear_cache(f"forecast:{user_id}:")

    @classmethod
    def invalidate_budget(cls, user_id: str) -> None:
        clear_cache(f"budget:{user_id}:")
