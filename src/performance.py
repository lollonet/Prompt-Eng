"""
Performance monitoring and async utilities for enterprise-grade applications.

Business Context: Implements comprehensive performance tracking and async I/O
patterns following modern best practices for production systems.

Why this approach: Performance monitoring enables observability and optimization,
while async I/O provides better resource utilization and scalability.
"""

import time
import asyncio
import aiofiles
import logging
import tracemalloc
from typing import Any, Callable, TypeVar, Dict, Optional, AsyncContextManager
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path

from .result_types import Result, Success, Error, KnowledgeError
from typing import Union

logger = logging.getLogger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for operations."""
    operation_name: str
    execution_time: float
    memory_usage_mb: float
    cache_hits: int = 0
    cache_misses: int = 0
    io_operations: int = 0
    error_count: int = 0
    start_time: float = field(default_factory=time.perf_counter)
    
    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio as percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/serialization."""
        return {
            'operation': self.operation_name,
            'execution_time_ms': round(self.execution_time * 1000, 2),
            'memory_usage_mb': round(self.memory_usage_mb, 2),
            'cache_hit_ratio': round(self.cache_hit_ratio, 1),
            'io_operations': self.io_operations,
            'error_count': self.error_count
        }


class PerformanceTracker:
    """Centralized performance tracking system."""
    
    def __init__(self):
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._memory_baseline = 0
        
    def start_tracking(self, operation: str) -> str:
        """Start tracking performance for an operation."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        current_memory = self._get_memory_usage()
        self._metrics[operation] = PerformanceMetrics(
            operation_name=operation,
            execution_time=0.0,
            memory_usage_mb=current_memory
        )
        return operation
    
    def stop_tracking(self, operation: str) -> PerformanceMetrics:
        """Stop tracking and return metrics."""
        if operation not in self._metrics:
            raise ValueError(f"No tracking started for operation: {operation}")
        
        metrics = self._metrics[operation]
        metrics.execution_time = time.perf_counter() - metrics.start_time
        metrics.memory_usage_mb = self._get_memory_usage() - metrics.memory_usage_mb
        
        logger.info(f"Performance metrics: {metrics.to_dict()}")
        return metrics
    
    def record_cache_hit(self, operation: str) -> None:
        """Record a cache hit for an operation."""
        if operation in self._metrics:
            self._metrics[operation].cache_hits += 1
    
    def record_cache_miss(self, operation: str) -> None:
        """Record a cache miss for an operation."""
        if operation in self._metrics:
            self._metrics[operation].cache_misses += 1
    
    def record_io_operation(self, operation: str) -> None:
        """Record an I/O operation."""
        if operation in self._metrics:
            self._metrics[operation].io_operations += 1
    
    def record_error(self, operation: str) -> None:
        """Record an error occurrence."""
        if operation in self._metrics:
            self._metrics[operation].error_count += 1
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / 1024 / 1024
        return 0.0


# Global performance tracker instance
performance_tracker = PerformanceTracker()


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator for automatic performance monitoring.
    
    Args:
        operation_name: Custom name for the operation. Defaults to function name.
    """
    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                performance_tracker.start_tracking(op_name)
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    performance_tracker.record_error(op_name)
                    raise
                finally:
                    performance_tracker.stop_tracking(op_name)
            return async_wrapper  # type: ignore
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                performance_tracker.start_tracking(op_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    performance_tracker.record_error(op_name)
                    raise
                finally:
                    performance_tracker.stop_tracking(op_name)
            return sync_wrapper  # type: ignore
    
    return decorator


@contextmanager
def performance_context(operation_name: str):
    """Context manager for performance tracking."""
    performance_tracker.start_tracking(operation_name)
    try:
        yield
    except Exception as e:
        performance_tracker.record_error(operation_name)
        raise
    finally:
        performance_tracker.stop_tracking(operation_name)


# Async I/O utilities following "Async by default" principle

@monitor_performance("async_read_text_file")
async def async_read_text_file(filepath: str) -> Union[Success, Error]:
    """
    Async version of text file reading with Result type.
    
    Business Context: Follows "Async by default for I/O" principle from best practices.
    Provides non-blocking file access for better system scalability.
    
    Args:
        filepath: Path to the text file to read.
        
    Returns:
        Result containing file content or error details.
    """
    try:
        performance_tracker.record_io_operation("async_read_text_file")
        
        # Validate file exists and is readable
        path = Path(filepath)
        if not path.exists():
            return Error(KnowledgeError(
                message=f"File not found: {filepath}",
                source="async_read_text_file"
            ))
        
        if not path.is_file():
            return Error(KnowledgeError(
                message=f"Path is not a file: {filepath}",
                source="async_read_text_file"
            ))
        
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        logger.debug(f"Successfully read {len(content)} characters from {filepath}")
        return Success(content)
        
    except PermissionError as e:
        return Error(KnowledgeError(
            message=f"Permission denied reading file: {filepath}",
            source="async_read_text_file",
            details=str(e)
        ))
    except UnicodeDecodeError as e:
        return Error(KnowledgeError(
            message=f"Unicode decode error reading file: {filepath}",
            source="async_read_text_file",
            details=str(e)
        ))
    except Exception as e:
        return Error(KnowledgeError(
            message=f"Unexpected error reading file: {filepath}",
            source="async_read_text_file",
            details=str(e)
        ))


@monitor_performance("async_load_json_file")
async def async_load_json_file(filepath: str) -> Union[Success, Error]:
    """
    Async version of JSON file loading with Result type.
    
    Args:
        filepath: Path to the JSON file to load.
        
    Returns:
        Result containing parsed JSON data or error details.
    """
    import json
    
    try:
        performance_tracker.record_io_operation("async_load_json_file")
        
        # First read the file content
        read_result = await async_read_text_file(filepath)
        if read_result.is_error():
            return read_result  # type: ignore
        
        content = read_result.unwrap()
        
        # Parse JSON in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, json.loads, content)
        
        logger.debug(f"Successfully loaded JSON from {filepath}")
        return Success(data)
        
    except json.JSONDecodeError as e:
        return Error(KnowledgeError(
            message=f"Invalid JSON in file: {filepath}",
            source="async_load_json_file",
            details=f"JSON decode error at line {e.lineno}, column {e.colno}: {e.msg}"
        ))
    except Exception as e:
        return Error(KnowledgeError(
            message=f"Unexpected error loading JSON: {filepath}",
            source="async_load_json_file",
            details=str(e)
        ))


@asynccontextmanager
async def async_performance_context(operation_name: str) -> AsyncContextManager[None]:
    """Async context manager for performance tracking."""
    performance_tracker.start_tracking(operation_name)
    try:
        yield
    except Exception as e:
        performance_tracker.record_error(operation_name)
        raise
    finally:
        performance_tracker.stop_tracking(operation_name)


# Lazy evaluation utilities

class LazyEvaluator:
    """
    Lazy evaluation container following "Compute only when needed" principle.
    
    Business Context: Implements lazy loading to optimize performance by deferring
    expensive computations until actually needed.
    """
    
    def __init__(self, compute_func: Callable[[], T]):
        self._compute_func = compute_func
        self._cached_value: Optional[T] = None
        self._computed = False
    
    def get(self) -> T:
        """Get the computed value, computing it if necessary."""
        if not self._computed:
            self._cached_value = self._compute_func()
            self._computed = True
        return self._cached_value  # type: ignore
    
    def invalidate(self) -> None:
        """Invalidate the cached value, forcing recomputation on next access."""
        self._cached_value = None
        self._computed = False
    
    @property
    def is_computed(self) -> bool:
        """Check if the value has been computed."""
        return self._computed


def lazy(compute_func: Callable[[], T]) -> LazyEvaluator:
    """Create a lazy evaluator for the given computation."""
    return LazyEvaluator(compute_func)


# Example usage patterns
async def _example_async_usage():
    """Examples of async patterns usage."""
    
    # Basic async file reading
    result = await async_read_text_file("/path/to/file.txt")
    if result.is_success():
        content = result.unwrap()
        print(f"File content: {content}")
    else:
        error = result.error
        logger.error(f"Failed to read file: {error}")
    
    # Performance monitoring
    @monitor_performance("example_operation")
    async def example_async_operation():
        await asyncio.sleep(0.1)  # Simulate work
        return "result"
    
    # Lazy evaluation
    expensive_computation = lazy(lambda: sum(range(1000000)))
    # Computation happens only when .get() is called
    result = expensive_computation.get()