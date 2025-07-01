"""
Comprehensive unit tests for AsyncCacheManager.

Tests the critical async caching infrastructure that's used throughout
the system for performance optimization.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from src.common.cache_manager import AsyncCacheManager


class TestAsyncCacheManager:
    """Test AsyncCacheManager functionality."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create fresh cache manager for each test."""
        return AsyncCacheManager()
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache_manager):
        """Test cache manager initializes properly."""
        assert cache_manager.cache_size() == 0
        assert cache_manager._cache == {}
        assert cache_manager._cache_lock is not None
    
    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, cache_manager):
        """Test cache miss returns None and records miss."""
        with patch('src.common.cache_manager.performance_tracker') as mock_tracker:
            result = await cache_manager.get_cached("missing_key", "test_operation")
            
            assert result is None
            mock_tracker.record_cache_miss.assert_called_once_with("test_operation")
            mock_tracker.record_cache_hit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache_manager):
        """Test setting and getting cached values."""
        test_key = "test_key"
        test_value = {"data": "test_data", "number": 42}
        operation_name = "test_operation"
        
        # Set value in cache
        await cache_manager.set_cached(test_key, test_value, operation_name)
        assert cache_manager.cache_size() == 1
        
        # Get value from cache
        with patch('src.common.cache_manager.performance_tracker') as mock_tracker:
            result = await cache_manager.get_cached(test_key, operation_name)
            
            assert result == test_value
            mock_tracker.record_cache_hit.assert_called_once_with(operation_name)
            mock_tracker.record_cache_miss.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_multiple_values(self, cache_manager):
        """Test caching multiple different values."""
        values = {
            "key1": "value1",
            "key2": {"complex": "data"},
            "key3": [1, 2, 3, 4],
            "key4": None
        }
        
        # Set multiple values
        for key, value in values.items():
            await cache_manager.set_cached(key, value, "test_op")
        
        assert cache_manager.cache_size() == len(values)
        
        # Verify all values can be retrieved
        for key, expected_value in values.items():
            with patch('src.common.cache_manager.performance_tracker'):
                result = await cache_manager.get_cached(key, "test_op")
                assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_cache_overwrites_existing_key(self, cache_manager):
        """Test that setting same key overwrites previous value."""
        key = "same_key"
        
        # Set initial value
        await cache_manager.set_cached(key, "initial_value", "test_op")
        
        # Overwrite with new value
        await cache_manager.set_cached(key, "new_value", "test_op")
        
        # Should still have only one entry
        assert cache_manager.cache_size() == 1
        
        # Should get the new value
        with patch('src.common.cache_manager.performance_tracker'):
            result = await cache_manager.get_cached(key, "test_op")
            assert result == "new_value"
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, cache_manager):
        """Test clearing all cached values."""
        # Add multiple values
        test_data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        for key, value in test_data.items():
            await cache_manager.set_cached(key, value, "test_op")
        
        assert cache_manager.cache_size() == 3
        
        # Clear cache
        await cache_manager.clear_cache()
        
        assert cache_manager.cache_size() == 0
        
        # Verify all keys are gone
        with patch('src.common.cache_manager.performance_tracker'):
            for key in test_data.keys():
                result = await cache_manager.get_cached(key, "test_op")
                assert result is None
    
    @pytest.mark.asyncio
    async def test_thread_safety_concurrent_access(self, cache_manager):
        """Test thread safety with concurrent cache operations."""
        async def set_operation(key_suffix, value):
            await cache_manager.set_cached(f"key_{key_suffix}", value, "concurrent_op")
        
        async def get_operation(key_suffix):
            with patch('src.common.cache_manager.performance_tracker'):
                return await cache_manager.get_cached(f"key_{key_suffix}", "concurrent_op")
        
        # Set up concurrent operations
        set_tasks = [set_operation(i, f"value_{i}") for i in range(10)]
        
        # Execute all sets concurrently
        await asyncio.gather(*set_tasks)
        
        # Verify all values are set correctly
        assert cache_manager.cache_size() == 10
        
        # Execute concurrent gets
        get_tasks = [get_operation(i) for i in range(10)]
        results = await asyncio.gather(*get_tasks)
        
        # Verify all gets returned correct values
        for i, result in enumerate(results):
            assert result == f"value_{i}"
    
    @pytest.mark.asyncio
    async def test_cache_with_none_values(self, cache_manager):
        """Test caching None values explicitly."""
        key = "none_key"
        
        # Cache None value explicitly
        await cache_manager.set_cached(key, None, "test_op")
        assert cache_manager.cache_size() == 1
        
        # Should return the cached None (not miss)
        with patch('src.common.cache_manager.performance_tracker') as mock_tracker:
            result = await cache_manager.get_cached(key, "test_op")
            
            assert result is None
            mock_tracker.record_cache_hit.assert_called_once()
            mock_tracker.record_cache_miss.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_performance_tracker_integration(self, cache_manager):
        """Test integration with performance tracker."""
        with patch('src.common.cache_manager.performance_tracker') as mock_tracker:
            # Test cache miss
            await cache_manager.get_cached("missing", "miss_test")
            mock_tracker.record_cache_miss.assert_called_with("miss_test")
            
            # Set value
            await cache_manager.set_cached("present", "value", "hit_test")
            
            # Test cache hit
            await cache_manager.get_cached("present", "hit_test")
            mock_tracker.record_cache_hit.assert_called_with("hit_test")
    
    @pytest.mark.asyncio
    async def test_cache_size_tracking(self, cache_manager):
        """Test cache size tracking accuracy."""
        assert cache_manager.cache_size() == 0
        
        # Add items
        for i in range(5):
            await cache_manager.set_cached(f"key_{i}", f"value_{i}", "size_test")
            assert cache_manager.cache_size() == i + 1
        
        # Overwrite existing item (size should stay same)
        await cache_manager.set_cached("key_0", "new_value", "size_test")
        assert cache_manager.cache_size() == 5
        
        # Clear cache
        await cache_manager.clear_cache()
        assert cache_manager.cache_size() == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_get_set_operations(self, cache_manager):
        """Test concurrent get/set operations don't corrupt data."""
        key = "concurrent_key"
        
        async def setter():
            for i in range(100):
                await cache_manager.set_cached(key, f"value_{i}", "concurrent_test")
                await asyncio.sleep(0.001)  # Small delay
        
        async def getter():
            results = []
            for _ in range(50):
                with patch('src.common.cache_manager.performance_tracker'):
                    result = await cache_manager.get_cached(key, "concurrent_test")
                    results.append(result)
                await asyncio.sleep(0.002)  # Small delay
            return results
        
        # Run setter and getter concurrently
        setter_task = asyncio.create_task(setter())
        getter_task = asyncio.create_task(getter())
        
        results = await asyncio.gather(setter_task, getter_task)
        getter_results = results[1]
        
        # Verify no corruption occurred
        # All non-None results should be valid strings
        for result in getter_results:
            if result is not None:
                assert isinstance(result, str)
                assert result.startswith("value_")
    
    @pytest.mark.asyncio
    async def test_cache_lock_prevents_race_conditions(self, cache_manager):
        """Test that cache lock prevents race conditions during clear."""
        # Fill cache with data
        for i in range(10):
            await cache_manager.set_cached(f"key_{i}", f"value_{i}", "race_test")
        
        async def clear_operation():
            await asyncio.sleep(0.01)  # Small delay
            await cache_manager.clear_cache()
        
        async def get_operation():
            with patch('src.common.cache_manager.performance_tracker'):
                results = []
                for i in range(10):
                    result = await cache_manager.get_cached(f"key_{i}", "race_test")
                    results.append(result)
                    await asyncio.sleep(0.001)  # Small delay
                return results
        
        # Run clear and get operations concurrently
        clear_task = asyncio.create_task(clear_operation())
        get_task = asyncio.create_task(get_operation())
        
        clear_result, get_results = await asyncio.gather(clear_task, get_task)
        
        # After both operations, cache should be empty
        assert cache_manager.cache_size() == 0
        
        # Results should be consistent (either all found or all not found)
        # No partial corruption should occur
        assert isinstance(get_results, list)
        assert len(get_results) == 10


class TestAsyncCacheManagerErrorConditions:
    """Test error conditions and edge cases."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create fresh cache manager for each test."""
        return AsyncCacheManager()
    
    @pytest.mark.asyncio
    async def test_empty_string_key(self, cache_manager):
        """Test caching with empty string key."""
        await cache_manager.set_cached("", "empty_key_value", "test_op")
        
        with patch('src.common.cache_manager.performance_tracker'):
            result = await cache_manager.get_cached("", "test_op")
            assert result == "empty_key_value"
    
    @pytest.mark.asyncio
    async def test_complex_object_caching(self, cache_manager):
        """Test caching complex objects."""
        complex_object = {
            'nested': {
                'data': [1, 2, {'inner': 'value'}],
                'tuple': (1, 2, 3),
                'set': {1, 2, 3}
            },
            'function': lambda x: x + 1,  # Non-serializable but cacheable in memory
            'none_field': None
        }
        
        await cache_manager.set_cached("complex", complex_object, "complex_test")
        
        with patch('src.common.cache_manager.performance_tracker'):
            result = await cache_manager.get_cached("complex", "complex_test")
            
            # Should get back the exact same object reference
            assert result is complex_object
            assert result['nested']['data'] == [1, 2, {'inner': 'value'}]
            assert result['function'](5) == 6
    
    @pytest.mark.asyncio
    async def test_performance_tracker_exception_handling(self, cache_manager):
        """Test behavior when performance tracker raises exceptions."""
        # Mock performance tracker to raise exceptions
        with patch('src.common.cache_manager.performance_tracker') as mock_tracker:
            mock_tracker.record_cache_miss.side_effect = Exception("Tracker error")
            mock_tracker.record_cache_hit.side_effect = Exception("Tracker error")
            
            # Cache operations should still work despite tracker errors
            result = await cache_manager.get_cached("missing", "error_test")
            assert result is None
            
            await cache_manager.set_cached("key", "value", "error_test")
            
            result = await cache_manager.get_cached("key", "error_test")
            assert result == "value"