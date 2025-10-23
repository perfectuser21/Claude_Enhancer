"""
CE Dashboard v2 - Caching Layer

Implements a simple time-based cache with file modification detection.

Version: 7.2.0
Performance: <5ms cache hit, invalidation based on file mtime + TTL
"""

import time
from pathlib import Path
from typing import Any, Optional, Callable
from functools import wraps


class SimpleCache:
    """
    Simple time-based cache with TTL and file modification detection.

    Usage:
        cache = SimpleCache(ttl_seconds=60)
        result = cache.get_or_compute('key', lambda: expensive_operation(), file_path)
    """

    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, dict] = {}

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        file_path: Optional[Path] = None
    ) -> Any:
        """
        Get cached value or compute and cache it.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            file_path: Optional file path for mtime-based invalidation

        Returns:
            Cached or freshly computed value
        """
        now = time.time()

        # Check if key exists in cache
        if key in self._cache:
            cached_item = self._cache[key]

            # Check TTL expiration
            if now - cached_item['timestamp'] < self.ttl_seconds:
                # Check file modification if provided
                if file_path:
                    try:
                        current_mtime = file_path.stat().st_mtime
                        if current_mtime == cached_item.get('file_mtime'):
                            # Cache hit!
                            return cached_item['value']
                    except (OSError, FileNotFoundError):
                        # File doesn't exist, invalidate cache
                        pass
                else:
                    # No file check needed, cache hit!
                    return cached_item['value']

        # Cache miss or expired - compute new value
        value = compute_fn()

        # Store in cache
        cache_entry = {
            'value': value,
            'timestamp': now
        }

        if file_path:
            try:
                cache_entry['file_mtime'] = file_path.stat().st_mtime
            except (OSError, FileNotFoundError):
                cache_entry['file_mtime'] = 0

        self._cache[key] = cache_entry

        return value

    def clear(self, key: Optional[str] = None):
        """Clear cache (specific key or all)"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'total_keys': len(self._cache),
            'keys': list(self._cache.keys())
        }


# ============================================================================
# GLOBAL CACHE INSTANCES
# ============================================================================

# Three-tier caching with different TTLs
capability_cache = SimpleCache(ttl_seconds=60)  # Slow-changing
learning_cache = SimpleCache(ttl_seconds=60)     # Slow-changing
project_cache = SimpleCache(ttl_seconds=5)       # Fast-changing (real-time)


def cached(cache_instance: SimpleCache, key_prefix: str = ''):
    """
    Decorator for caching function results.

    Usage:
        @cached(capability_cache, 'cap')
        def get_capabilities():
            return expensive_parsing()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            key_parts = [key_prefix, func.__name__]

            # Include simple args in key (avoid complex objects)
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))

            cache_key = '_'.join(filter(None, key_parts))

            # Compute function
            def compute():
                return func(*args, **kwargs)

            # Use cache
            return cache_instance.get_or_compute(cache_key, compute)

        return wrapper
    return decorator
