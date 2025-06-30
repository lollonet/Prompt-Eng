"""
Performance gates with automatic threshold enforcement.

Business Context: Implements strict performance thresholds as specified in
code-best-practice.md to ensure production-ready performance characteristics.

Why this approach: Automatic threshold enforcement prevents performance
degradation and ensures SLA compliance in production environments.
"""

import time
import asyncio
import logging
import tracemalloc
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager, asynccontextmanager
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class PerformanceViolationType(Enum):
    """Types of performance violations."""
    API_RESPONSE_TIME = "api_response_time"
    MEMORY_GROWTH = "memory_growth"
    CPU_USAGE = "cpu_usage"
    DATABASE_QUERY_TIME = "database_query_time"
    BUNDLE_SIZE = "bundle_size"


@dataclass(frozen=True)
class PerformanceThreshold:
    """Performance threshold definition."""
    name: str
    value: float
    unit: str
    violation_type: PerformanceViolationType
    description: str


@dataclass
class PerformanceViolation(Exception):
    """Exception raised when performance thresholds are exceeded."""
    threshold: PerformanceThreshold
    actual_value: float
    violation_severity: str = "HIGH"
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __str__(self) -> str:
        return (f"Performance violation: {self.threshold.name} "
                f"exceeded {self.threshold.value}{self.threshold.unit} "
                f"(actual: {self.actual_value:.2f}{self.threshold.unit})")


class PerformanceGate:
    """
    Enterprise-grade performance gate enforcement.
    
    Implements thresholds from code-best-practice.md:
    - API Response Time: p95 < 200ms, p99 < 500ms
    - Memory Growth: < 10% per hour
    - CPU Usage: < 70% average under normal load
    - Database Query Time: < 100ms for simple queries
    - Bundle Size: < 250KB gzipped
    """
    
    # Performance thresholds as specified in best practices
    THRESHOLDS = {
        'api_response_p95': PerformanceThreshold(
            name="API Response Time P95",
            value=200.0,
            unit="ms",
            violation_type=PerformanceViolationType.API_RESPONSE_TIME,
            description="95th percentile API response time must be under 200ms"
        ),
        'api_response_p99': PerformanceThreshold(
            name="API Response Time P99", 
            value=500.0,
            unit="ms",
            violation_type=PerformanceViolationType.API_RESPONSE_TIME,
            description="99th percentile API response time must be under 500ms"
        ),
        'memory_growth_hourly': PerformanceThreshold(
            name="Memory Growth Rate",
            value=10.0,
            unit="%",
            violation_type=PerformanceViolationType.MEMORY_GROWTH,
            description="Memory growth must be less than 10% per hour"
        ),
        'cpu_usage_average': PerformanceThreshold(
            name="CPU Usage Average",
            value=70.0,
            unit="%",
            violation_type=PerformanceViolationType.CPU_USAGE,
            description="Average CPU usage must be under 70%"
        ),
        'db_query_simple': PerformanceThreshold(
            name="Database Query Time",
            value=100.0,
            unit="ms",
            violation_type=PerformanceViolationType.DATABASE_QUERY_TIME,
            description="Simple database queries must complete under 100ms"
        ),
        'bundle_size_gzipped': PerformanceThreshold(
            name="Bundle Size Gzipped",
            value=250.0,
            unit="KB",
            violation_type=PerformanceViolationType.BUNDLE_SIZE,
            description="Gzipped bundle size must be under 250KB"
        )
    }
    
    def __init__(self, enable_enforcement: bool = True, custom_thresholds: Optional[Dict[str, PerformanceThreshold]] = None):
        """
        Initialize performance gate.
        
        Args:
            enable_enforcement: Whether to enforce thresholds (fail on violations).
            custom_thresholds: Optional custom threshold overrides.
        """
        self.enable_enforcement = enable_enforcement
        self.thresholds = {**self.THRESHOLDS}
        if custom_thresholds:
            self.thresholds.update(custom_thresholds)
        
        self.violations: list[PerformanceViolation] = []
        self._response_times: list[float] = []
        self._memory_baseline: Optional[float] = None
        self._memory_start_time: Optional[float] = None
        
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        logger.info(f"PerformanceGate initialized with enforcement: {enable_enforcement}")
    
    def _get_percentile_index(self, percentile: str, sample_size: int) -> int:
        """Calculate percentile index for given sample size."""
        if percentile == "p95":
            return int(0.95 * sample_size)
        elif percentile == "p99":
            return int(0.99 * sample_size)
        else:
            return sample_size - 1
    
    def _calculate_current_percentile(self, percentile: str) -> Optional[float]:
        """Calculate current percentile from response time samples."""
        if len(self._response_times) < 20:  # Need sufficient samples
            return None
            
        sorted_times = sorted(self._response_times[-100:])  # Use last 100 samples
        index = self._get_percentile_index(percentile, len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def _create_percentile_violation(self, threshold: PerformanceThreshold, 
                                   current_percentile: float, duration_ms: float, 
                                   percentile: str, sample_size: int) -> PerformanceViolation:
        """Create performance violation for percentile threshold breach."""
        return PerformanceViolation(
            threshold=threshold,
            actual_value=current_percentile,
            context={
                'current_duration_ms': duration_ms,
                'sample_size': sample_size,
                'percentile': percentile
            }
        )
    
    def _check_individual_threshold(self, duration_ms: float, threshold: PerformanceThreshold, percentile: str) -> None:
        """Check individual request against threshold."""
        if duration_ms > threshold.value:
            logger.warning(f"Individual request exceeded {percentile} threshold: {duration_ms:.2f}ms > {threshold.value}ms")
    
    def check_api_response_time(self, duration_ms: float, percentile: str = "p95") -> None:
        """
        Check API response time against thresholds.
        
        Args:
            duration_ms: Response time in milliseconds.
            percentile: Percentile to check against ("p95" or "p99").
            
        Raises:
            PerformanceViolation: If threshold is exceeded and enforcement is enabled.
        """
        threshold_key = f"api_response_{percentile}"
        
        if threshold_key not in self.thresholds:
            logger.warning(f"Unknown percentile threshold: {percentile}")
            return
        
        threshold = self.thresholds[threshold_key]
        
        # Record response time for percentile calculation
        self._response_times.append(duration_ms)
        
        # Calculate and check current percentile
        current_percentile = self._calculate_current_percentile(percentile)
        if current_percentile and current_percentile > threshold.value:
            violation = self._create_percentile_violation(
                threshold, current_percentile, duration_ms, percentile, 
                len(self._response_times[-100:])
            )
            self._handle_violation(violation)
        
        # Check individual request against threshold
        self._check_individual_threshold(duration_ms, threshold, percentile)
    
    def check_memory_growth(self) -> None:
        """
        Check memory growth rate against threshold.
        
        Raises:
            PerformanceViolation: If memory growth exceeds 10% per hour.
        """
        if not tracemalloc.is_tracing():
            logger.warning("Memory tracking not enabled, cannot check memory growth")
            return
        
        current_memory, _ = tracemalloc.get_traced_memory()
        current_memory_mb = current_memory / 1024 / 1024
        current_time = time.time()
        
        if self._memory_baseline is None:
            self._memory_baseline = current_memory_mb
            self._memory_start_time = current_time
            return
        
        time_elapsed_hours = (current_time - self._memory_start_time) / 3600
        
        if time_elapsed_hours > 0.1:  # Check after at least 6 minutes
            memory_growth = ((current_memory_mb - self._memory_baseline) / self._memory_baseline) * 100
            growth_rate_per_hour = memory_growth / time_elapsed_hours
            
            threshold = self.thresholds['memory_growth_hourly']
            
            if growth_rate_per_hour > threshold.value:
                violation = PerformanceViolation(
                    threshold=threshold,
                    actual_value=growth_rate_per_hour,
                    context={
                        'current_memory_mb': current_memory_mb,
                        'baseline_memory_mb': self._memory_baseline,
                        'time_elapsed_hours': time_elapsed_hours,
                        'total_growth_percent': memory_growth
                    }
                )
                
                self._handle_violation(violation)
    
    def check_database_query_time(self, duration_ms: float, query_type: str = "simple") -> None:
        """
        Check database query time against threshold.
        
        Args:
            duration_ms: Query execution time in milliseconds.
            query_type: Type of query ("simple" or "complex").
            
        Raises:
            PerformanceViolation: If query time exceeds threshold.
        """
        if query_type == "simple":
            threshold = self.thresholds['db_query_simple']
            
            if duration_ms > threshold.value:
                violation = PerformanceViolation(
                    threshold=threshold,
                    actual_value=duration_ms,
                    context={
                        'query_type': query_type,
                        'duration_ms': duration_ms
                    }
                )
                
                self._handle_violation(violation)
    
    def _handle_violation(self, violation: PerformanceViolation) -> None:
        """
        Handle a performance violation.
        
        Args:
            violation: The performance violation that occurred.
            
        Raises:
            PerformanceViolation: If enforcement is enabled.
        """
        self.violations.append(violation)
        
        logger.error(f"Performance violation detected: {violation}")
        
        if self.enable_enforcement:
            raise violation
        else:
            logger.warning(f"Performance violation ignored (enforcement disabled): {violation}")
    
    def get_violation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all performance violations.
        
        Returns:
            Dictionary containing violation statistics.
        """
        violations_by_type = {}
        for violation in self.violations:
            violation_type = violation.threshold.violation_type.value
            if violation_type not in violations_by_type:
                violations_by_type[violation_type] = []
            violations_by_type[violation_type].append({
                'threshold': violation.threshold.name,
                'actual_value': violation.actual_value,
                'expected_value': violation.threshold.value,
                'timestamp': violation.timestamp,
                'context': violation.context
            })
        
        return {
            'total_violations': len(self.violations),
            'violations_by_type': violations_by_type,
            'enforcement_enabled': self.enable_enforcement,
            'thresholds': {k: {
                'name': v.name,
                'value': v.value,
                'unit': v.unit,
                'description': v.description
            } for k, v in self.thresholds.items()}
        }


# Global performance gate instance
performance_gate = PerformanceGate(enable_enforcement=True)


# Decorators for automatic threshold enforcement

def enforce_api_response_time(percentile: str = "p95"):
    """
    Decorator to automatically enforce API response time thresholds.
    
    Args:
        percentile: Percentile to enforce ("p95" or "p99").
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    performance_gate.check_api_response_time(duration_ms, percentile)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    performance_gate.check_api_response_time(duration_ms, percentile)
            return sync_wrapper
    
    return decorator


def enforce_database_query_time(query_type: str = "simple"):
    """
    Decorator to automatically enforce database query time thresholds.
    
    Args:
        query_type: Type of query ("simple" or "complex").
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    performance_gate.check_database_query_time(duration_ms, query_type)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    performance_gate.check_database_query_time(duration_ms, query_type)
            return sync_wrapper
    
    return decorator


@contextmanager
def performance_gate_context(check_memory: bool = True):
    """
    Context manager for performance gate monitoring.
    
    Args:
        check_memory: Whether to check memory growth.
    """
    start_time = time.perf_counter()
    
    try:
        yield performance_gate
    finally:
        if check_memory:
            performance_gate.check_memory_growth()
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        if duration_ms > 1000:  # Log slow operations
            logger.warning(f"Slow operation detected: {duration_ms:.2f}ms")


@asynccontextmanager
async def async_performance_gate_context(check_memory: bool = True):
    """
    Async context manager for performance gate monitoring.
    
    Args:
        check_memory: Whether to check memory growth.
    """
    start_time = time.perf_counter()
    
    try:
        yield performance_gate
    finally:
        if check_memory:
            performance_gate.check_memory_growth()
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        if duration_ms > 1000:  # Log slow operations
            logger.warning(f"Slow async operation detected: {duration_ms:.2f}ms")


# Integration with existing performance monitoring
def _create_enhanced_async_wrapper(monitored_func, op_name: str):
    """Create async wrapper with performance gate integration."""
    @wraps(monitored_func)
    async def async_wrapper(*args, **kwargs):
        async with async_performance_gate_context():
            start_time = time.perf_counter()
            try:
                result = await monitored_func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                performance_gate.check_api_response_time(duration_ms, "p95")
    return async_wrapper


def _create_enhanced_sync_wrapper(monitored_func, op_name: str):
    """Create sync wrapper with performance gate integration."""
    @wraps(monitored_func)
    def sync_wrapper(*args, **kwargs):
        with performance_gate_context():
            start_time = time.perf_counter()
            try:
                result = monitored_func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                performance_gate.check_api_response_time(duration_ms, "p95")
    return sync_wrapper


def _patch_monitoring_system(original_monitor):
    """Patch the original monitoring system with performance gates."""
    def enhanced_monitor_performance(operation_name: Optional[str] = None):
        """Enhanced monitor_performance with automatic threshold enforcement."""
        def decorator(func):
            # Apply original monitoring first
            monitored_func = original_monitor(operation_name)(func)
            op_name = operation_name or func.__name__
            
            # Add threshold enforcement
            if asyncio.iscoroutinefunction(func):
                return _create_enhanced_async_wrapper(monitored_func, op_name)
            else:
                return _create_enhanced_sync_wrapper(monitored_func, op_name)
        
        return decorator
    return enhanced_monitor_performance


def integrate_with_existing_monitoring():
    """Integrate performance gates with existing monitoring system."""
    try:
        from .performance import monitor_performance as original_monitor
        
        enhanced_monitor = _patch_monitoring_system(original_monitor)
        
        # Replace the original function
        import src.performance
        src.performance.monitor_performance = enhanced_monitor
        
        logger.info("Performance gates successfully integrated with existing monitoring")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to integrate with existing monitoring: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during integration: {e}")
        return False


# Automatic initialization
def initialize_performance_gates():
    """Initialize performance gates system."""
    try:
        # Integrate with existing monitoring
        if integrate_with_existing_monitoring():
            logger.info("Performance gates system initialized successfully")
        else:
            logger.warning("Performance gates initialized but integration failed")
        
        # Start memory tracking
        performance_gate.check_memory_growth()
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize performance gates: {e}")
        return False


# Auto-initialize when module is imported
if __name__ != "__main__":
    initialize_performance_gates()