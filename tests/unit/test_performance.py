"""
Comprehensive unit tests for Performance monitoring infrastructure.

Tests the critical performance tracking and async I/O utilities used throughout
the system for monitoring and optimization.
"""

import asyncio
import pytest
import tempfile
import json
import time
import tracemalloc
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.performance import (
    PerformanceMetrics,
    PerformanceTracker,
    performance_tracker,
    monitor_performance,
    performance_context,
    async_performance_context,
    async_read_text_file,
    async_load_json_file,
    LazyEvaluator,
    lazy
)
from src.result_types import Success, Error, KnowledgeError


class TestPerformanceMetrics:
    """Test PerformanceMetrics functionality."""

    def test_metrics_initialization(self):
        """Test metrics initialize with correct defaults."""
        metrics = PerformanceMetrics(
            operation_name="test_op",
            execution_time=1.5,
            memory_usage_mb=2.3
        )
        
        assert metrics.operation_name == "test_op"
        assert metrics.execution_time == 1.5
        assert metrics.memory_usage_mb == 2.3
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.io_operations == 0
        assert metrics.error_count == 0

    def test_cache_hit_ratio_calculation(self):
        """Test cache hit ratio calculations."""
        metrics = PerformanceMetrics(
            operation_name="test",
            execution_time=1.0,
            memory_usage_mb=1.0
        )
        
        # No cache operations
        assert metrics.cache_hit_ratio == 0.0
        
        # Some cache hits and misses
        metrics.cache_hits = 8
        metrics.cache_misses = 2
        assert metrics.cache_hit_ratio == 80.0
        
        # All hits
        metrics.cache_hits = 10
        metrics.cache_misses = 0
        assert metrics.cache_hit_ratio == 100.0
        
        # All misses
        metrics.cache_hits = 0
        metrics.cache_misses = 5
        assert metrics.cache_hit_ratio == 0.0

    def test_to_dict_conversion(self):
        """Test metrics conversion to dictionary."""
        metrics = PerformanceMetrics(
            operation_name="api_call",
            execution_time=1.234567,
            memory_usage_mb=12.3456789,
            cache_hits=5,
            cache_misses=2,
            io_operations=3,
            error_count=1
        )
        
        result_dict = metrics.to_dict()
        
        expected = {
            "operation": "api_call",
            "execution_time_ms": 1234.57,
            "memory_usage_mb": 12.35,
            "cache_hit_ratio": 71.4,
            "io_operations": 3,
            "error_count": 1
        }
        
        assert result_dict == expected


class TestPerformanceTracker:
    """Test PerformanceTracker functionality."""

    @pytest.fixture
    def tracker(self):
        """Create fresh performance tracker for testing."""
        return PerformanceTracker()

    def test_tracker_initialization(self, tracker):
        """Test tracker initializes correctly."""
        assert tracker._metrics == {}
        assert tracker._memory_baseline == 0

    @patch('src.performance.tracemalloc')
    def test_start_tracking(self, mock_tracemalloc, tracker):
        """Test starting performance tracking."""
        mock_tracemalloc.is_tracing.return_value = False
        mock_tracemalloc.get_traced_memory.return_value = (1024 * 1024, 2048 * 1024)  # 1MB current, 2MB peak
        
        with patch.object(tracker, '_get_memory_usage', return_value=1.0):
            operation_id = tracker.start_tracking("test_operation")
        
        assert operation_id == "test_operation"
        assert "test_operation" in tracker._metrics
        
        metrics = tracker._metrics["test_operation"]
        assert metrics.operation_name == "test_operation"
        assert metrics.memory_usage_mb == 1.0  # 1MB converted to MB
        
        mock_tracemalloc.start.assert_called_once()

    @patch('src.performance.tracemalloc')
    def test_stop_tracking(self, mock_tracemalloc, tracker):
        """Test stopping performance tracking."""
        # Setup mocks
        mock_tracemalloc.is_tracing.return_value = True
        
        # Start tracking with fixed memory and time
        with patch.object(tracker, '_get_memory_usage', return_value=1.0):
            operation_id = tracker.start_tracking("test_op")
            
        # Manually set start time to control timing
        start_time = tracker._metrics[operation_id].start_time
        
        # Mock stop tracking with different memory and calculate proper execution time
        with patch.object(tracker, '_get_memory_usage', return_value=3.0):  # 3MB total, 2MB increase
            with patch('time.perf_counter', return_value=start_time + 2.5):  # 2.5 seconds later
                metrics = tracker.stop_tracking(operation_id)
        
        assert metrics.execution_time == 2.5
        assert metrics.memory_usage_mb == 2.0  # 3.0 - 1.0 = 2MB increase

    def test_stop_tracking_nonexistent_operation(self, tracker):
        """Test stopping tracking for non-existent operation raises error."""
        with pytest.raises(ValueError, match="No tracking started for operation: nonexistent"):
            tracker.stop_tracking("nonexistent")

    def test_record_cache_operations(self, tracker):
        """Test recording cache operations."""
        with patch.object(tracker, '_get_memory_usage', return_value=1.0):
            tracker.start_tracking("cache_test")
        
        # Record some cache operations
        tracker.record_cache_hit("cache_test")
        tracker.record_cache_hit("cache_test")
        tracker.record_cache_miss("cache_test")
        
        metrics = tracker._metrics["cache_test"]
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1
        assert abs(metrics.cache_hit_ratio - 66.7) < 0.1  # 2/3 * 100, allow small precision difference

    def test_record_io_operations(self, tracker):
        """Test recording I/O operations."""
        with patch.object(tracker, '_get_memory_usage', return_value=1.0):
            tracker.start_tracking("io_test")
        
        tracker.record_io_operation("io_test")
        tracker.record_io_operation("io_test")
        tracker.record_io_operation("io_test")
        
        metrics = tracker._metrics["io_test"]
        assert metrics.io_operations == 3

    def test_record_errors(self, tracker):
        """Test recording errors."""
        with patch.object(tracker, '_get_memory_usage', return_value=1.0):
            tracker.start_tracking("error_test")
        
        tracker.record_error("error_test")
        tracker.record_error("error_test")
        
        metrics = tracker._metrics["error_test"]
        assert metrics.error_count == 2

    def test_record_operations_for_nonexistent_tracking(self, tracker):
        """Test recording operations for non-tracked operation doesn't crash."""
        # These should not raise errors, just be no-ops
        tracker.record_cache_hit("nonexistent")
        tracker.record_cache_miss("nonexistent")
        tracker.record_io_operation("nonexistent")
        tracker.record_error("nonexistent")
        
        assert "nonexistent" not in tracker._metrics


class TestMonitorPerformanceDecorator:
    """Test monitor_performance decorator functionality."""

    def test_decorator_with_sync_function(self):
        """Test decorator works with synchronous functions."""
        @monitor_performance("sync_test")
        def sync_function(x, y):
            return x + y
        
        result = sync_function(5, 3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_decorator_with_async_function(self):
        """Test decorator works with asynchronous functions."""
        @monitor_performance("async_test")
        async def async_function(x, y):
            await asyncio.sleep(0.01)
            return x * y
        
        result = await async_function(4, 6)
        assert result == 24

    @pytest.mark.asyncio
    async def test_decorator_default_operation_name(self):
        """Test decorator uses function name as default operation name."""
        @monitor_performance()
        async def my_test_function():
            return "test_result"
        
        result = await my_test_function()
        assert result == "test_result"

    def test_decorator_handles_sync_exceptions(self):
        """Test decorator properly handles exceptions in sync functions."""
        @monitor_performance("sync_error_test")
        def failing_sync_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            failing_sync_function()

    @pytest.mark.asyncio
    async def test_decorator_handles_async_exceptions(self):
        """Test decorator properly handles exceptions in async functions."""
        @monitor_performance("async_error_test")
        async def failing_async_function():
            await asyncio.sleep(0.001)
            raise RuntimeError("Async test error")
        
        with pytest.raises(RuntimeError, match="Async test error"):
            await failing_async_function()


class TestPerformanceContextManagers:
    """Test performance context managers."""

    def test_sync_performance_context(self):
        """Test synchronous performance context manager."""
        with performance_context("sync_context_test"):
            time.sleep(0.01)  # Small delay
        
        # Context manager should have completed without errors

    def test_sync_performance_context_with_exception(self):
        """Test sync context manager handles exceptions."""
        with pytest.raises(ValueError, match="Context test error"):
            with performance_context("sync_context_error"):
                raise ValueError("Context test error")

    @pytest.mark.asyncio
    async def test_async_performance_context(self):
        """Test asynchronous performance context manager."""
        async with async_performance_context("async_context_test"):
            await asyncio.sleep(0.01)
        
        # Context manager should have completed without errors

    @pytest.mark.asyncio
    async def test_async_performance_context_with_exception(self):
        """Test async context manager handles exceptions."""
        with pytest.raises(RuntimeError, match="Async context error"):
            async with async_performance_context("async_context_error"):
                await asyncio.sleep(0.001)
                raise RuntimeError("Async context error")


class TestAsyncFileOperations:
    """Test async file I/O operations."""

    @pytest.mark.asyncio
    async def test_async_read_text_file_success(self):
        """Test successful async text file reading."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("Hello, World!\nThis is a test file.")
            temp_file_path = temp_file.name
        
        try:
            result = await async_read_text_file(temp_file_path)
            
            assert result.is_success()
            content = result.unwrap()
            assert content == "Hello, World!\nThis is a test file."
        finally:
            Path(temp_file_path).unlink()

    @pytest.mark.asyncio
    async def test_async_read_text_file_not_found(self):
        """Test async text file reading with non-existent file."""
        result = await async_read_text_file("/nonexistent/path/file.txt")
        
        assert result.is_error()
        error = result.error
        assert isinstance(error, KnowledgeError)
        assert "File not found" in error.message

    @pytest.mark.asyncio
    async def test_async_read_text_file_not_a_file(self):
        """Test async text file reading with directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await async_read_text_file(temp_dir)
            
            assert result.is_error()
            error = result.error
            assert "Path is not a file" in error.message

    @pytest.mark.asyncio
    async def test_async_read_text_file_permission_denied(self):
        """Test async text file reading with permission denied."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name
        
        try:
            # Remove read permissions
            Path(temp_file_path).chmod(0o000)
            
            result = await async_read_text_file(temp_file_path)
            
            assert result.is_error()
            error = result.error
            assert "Permission denied" in error.message
        finally:
            # Restore permissions and cleanup
            Path(temp_file_path).chmod(0o644)
            Path(temp_file_path).unlink()

    @pytest.mark.asyncio
    async def test_async_load_json_file_success(self):
        """Test successful async JSON file loading."""
        test_data = {
            "name": "test",
            "version": "1.0",
            "features": ["feature1", "feature2"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(test_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            result = await async_load_json_file(temp_file_path)
            
            assert result.is_success()
            data = result.unwrap()
            assert data == test_data
        finally:
            Path(temp_file_path).unlink()

    @pytest.mark.asyncio
    async def test_async_load_json_file_invalid_json(self):
        """Test async JSON loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write("{ invalid json content")
            temp_file_path = temp_file.name
        
        try:
            result = await async_load_json_file(temp_file_path)
            
            assert result.is_error()
            error = result.error
            assert "Invalid JSON" in error.message
            assert "JSON decode error" in error.details
        finally:
            Path(temp_file_path).unlink()

    @pytest.mark.asyncio
    async def test_async_load_json_file_not_found(self):
        """Test async JSON loading with non-existent file."""
        result = await async_load_json_file("/nonexistent/file.json")
        
        assert result.is_error()
        error = result.error
        assert "File not found" in error.message


class TestLazyEvaluator:
    """Test LazyEvaluator functionality."""

    def test_lazy_evaluator_initialization(self):
        """Test lazy evaluator initializes correctly."""
        def compute_func():
            return "computed_value"
        
        lazy_eval = LazyEvaluator(compute_func)
        
        assert not lazy_eval.is_computed
        assert lazy_eval._cached_value is None

    def test_lazy_evaluator_computation(self):
        """Test lazy evaluator computes value on first access."""
        call_count = 0
        
        def compute_func():
            nonlocal call_count
            call_count += 1
            return f"computed_{call_count}"
        
        lazy_eval = LazyEvaluator(compute_func)
        
        # First access should compute
        result1 = lazy_eval.get()
        assert result1 == "computed_1"
        assert lazy_eval.is_computed
        assert call_count == 1
        
        # Second access should use cached value
        result2 = lazy_eval.get()
        assert result2 == "computed_1"  # Same value
        assert call_count == 1  # Not called again

    def test_lazy_evaluator_invalidation(self):
        """Test lazy evaluator invalidation."""
        call_count = 0
        
        def compute_func():
            nonlocal call_count
            call_count += 1
            return f"computed_{call_count}"
        
        lazy_eval = LazyEvaluator(compute_func)
        
        # First computation
        result1 = lazy_eval.get()
        assert result1 == "computed_1"
        assert call_count == 1
        
        # Invalidate and recompute
        lazy_eval.invalidate()
        assert not lazy_eval.is_computed
        
        result2 = lazy_eval.get()
        assert result2 == "computed_2"  # New value
        assert call_count == 2

    def test_lazy_evaluator_exception_handling(self):
        """Test lazy evaluator handles exceptions."""
        def failing_compute():
            raise ValueError("Computation failed")
        
        lazy_eval = LazyEvaluator(failing_compute)
        
        with pytest.raises(ValueError, match="Computation failed"):
            lazy_eval.get()
        
        # Should not be marked as computed after failure
        assert not lazy_eval.is_computed

    def test_lazy_factory_function(self):
        """Test lazy factory function."""
        def expensive_computation():
            return sum(range(1000))
        
        lazy_sum = lazy(expensive_computation)
        
        assert isinstance(lazy_sum, LazyEvaluator)
        assert not lazy_sum.is_computed
        
        result = lazy_sum.get()
        assert result == sum(range(1000))
        assert lazy_sum.is_computed


class TestPerformanceIntegration:
    """Integration tests for performance monitoring."""

    @pytest.mark.asyncio
    async def test_realistic_async_operation_monitoring(self):
        """Test realistic async operation with comprehensive monitoring."""
        @monitor_performance("database_query")
        async def simulate_database_query(query_id):
            # Simulate some database work
            await asyncio.sleep(0.02)  # 20ms query time
            
            if query_id == "complex_query":
                await asyncio.sleep(0.03)  # Additional 30ms for complex query
            
            return f"result_for_{query_id}"
        
        # Execute multiple queries
        simple_result = await simulate_database_query("simple_query")
        complex_result = await simulate_database_query("complex_query")
        
        assert simple_result == "result_for_simple_query"
        assert complex_result == "result_for_complex_query"

    @pytest.mark.asyncio
    async def test_nested_performance_contexts(self):
        """Test nested performance monitoring contexts."""
        async with async_performance_context("outer_operation"):
            await asyncio.sleep(0.01)
            
            async with async_performance_context("inner_operation"):
                await asyncio.sleep(0.01)
            
            await asyncio.sleep(0.01)

    def test_lazy_evaluation_with_performance_monitoring(self):
        """Test lazy evaluation combined with performance monitoring."""
        @monitor_performance("expensive_computation")
        def expensive_function():
            time.sleep(0.01)  # Simulate expensive work
            return sum(range(10000))
        
        # Create lazy evaluator
        lazy_result = lazy(expensive_function)
        
        # Value not computed yet
        assert not lazy_result.is_computed
        
        # First access triggers computation
        result1 = lazy_result.get()
        expected = sum(range(10000))
        assert result1 == expected
        assert lazy_result.is_computed
        
        # Second access uses cached value
        result2 = lazy_result.get()
        assert result2 == expected

    @pytest.mark.asyncio
    async def test_file_operations_with_performance_tracking(self):
        """Test file operations with automatic performance tracking."""
        test_data = {"test": "data", "numbers": [1, 2, 3, 4, 5]}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(test_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Test JSON loading (has @monitor_performance decorator)
            result = await async_load_json_file(temp_file_path)
            
            assert result.is_success()
            data = result.unwrap()
            assert data == test_data
            
            # Convert to text file for text reading test
            text_content = json.dumps(test_data, indent=2)
            with open(temp_file_path, 'w') as f:
                f.write(text_content)
            
            # Test text reading (has @monitor_performance decorator)
            text_result = await async_read_text_file(temp_file_path)
            
            assert text_result.is_success()
            content = text_result.unwrap()
            assert json.loads(content) == test_data
            
        finally:
            Path(temp_file_path).unlink()