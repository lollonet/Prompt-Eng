"""
Shared async cache management utilities.

Consolidates duplicated cache management patterns across the codebase.
"""

import asyncio
from typing import Any, Dict, Optional

from ..performance import performance_tracker


class AsyncCacheManager:
    """
    Generic async cache manager with performance tracking.
    
    Consolidates the duplicated cache patterns found in:
    - knowledge_manager_async.py
    - prompt_generator_modern.py
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_cached(self, key: str, operation_name: str) -> Optional[Any]:
        """
        Get a value from cache with performance tracking.
        
        Args:
            key: Cache key.
            operation_name: Name for performance tracking.
            
        Returns:
            Cached value if found, None otherwise.
        """
        async with self._cache_lock:
            if key in self._cache:
                try:
                    performance_tracker.record_cache_hit(operation_name)
                except Exception:
                    pass  # Don't let performance tracking block cache operations
                return self._cache[key]
        
        try:
            performance_tracker.record_cache_miss(operation_name)
        except Exception:
            pass  # Don't let performance tracking block cache operations
        return None
    
    async def set_cached(self, key: str, value: Any, operation_name: str) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            operation_name: Name for performance tracking.
        """
        async with self._cache_lock:
            self._cache[key] = value
    
    async def clear_cache(self) -> None:
        """Clear all cached values."""
        async with self._cache_lock:
            self._cache.clear()
    
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)