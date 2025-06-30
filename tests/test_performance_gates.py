"""
Comprehensive tests for performance gates system.

Tests all performance threshold enforcement, violation handling,
and integration patterns to ensure enterprise-grade reliability.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.performance_gates import (
    PerformanceGate,
    PerformanceThreshold,
    PerformanceViolation,
    PerformanceViolationType,
    performance_gate,
    enforce_api_response_time,
    enforce_database_query_time,
    performance_gate_context,
    async_performance_gate_context,
    integrate_with_existing_monitoring,
    initialize_performance_gates
)


class TestPerformanceThreshold:
    """Test PerformanceThreshold dataclass."""
    
    def test_threshold_creation(self):
        """Test threshold creation with all fields."""
        threshold = PerformanceThreshold(
            name="Test Threshold",
            value=200.0,
            unit="ms",
            violation_type=PerformanceViolationType.API_RESPONSE_TIME,
            description="Test description"
        )
        
        assert threshold.name == "Test Threshold"
        assert threshold.value == 200.0
        assert threshold.unit == "ms"
        assert threshold.violation_type == PerformanceViolationType.API_RESPONSE_TIME
        assert threshold.description == "Test description"
    
    def test_threshold_immutability(self):
        """Test that thresholds are immutable."""
        threshold = PerformanceThreshold(
            name="Test",
            value=100.0,
            unit="ms",
            violation_type=PerformanceViolationType.API_RESPONSE_TIME,
            description="Test"
        )
        
        with pytest.raises(AttributeError):
            threshold.value = 200.0


class TestPerformanceViolation:
    """Test PerformanceViolation exception and data structure."""
    
    def test_violation_creation(self):
        """Test violation creation with all fields."""
        threshold = PerformanceThreshold(
            name="Test Threshold",
            value=200.0,
            unit="ms",
            violation_type=PerformanceViolationType.API_RESPONSE_TIME,
            description="Test"
        )
        
        violation = PerformanceViolation(
            threshold=threshold,
            actual_value=300.0,
            violation_severity="HIGH",
            context={"test": "data"}
        )
        
        assert violation.threshold == threshold
        assert violation.actual_value == 300.0
        assert violation.violation_severity == "HIGH"
        assert violation.context == {"test": "data"}
        assert violation.timestamp > 0
    
    def test_violation_string_representation(self):
        """Test violation string representation."""
        threshold = PerformanceThreshold(
            name="API Response Time",
            value=200.0,
            unit="ms",
            violation_type=PerformanceViolationType.API_RESPONSE_TIME,
            description="Test"
        )
        
        violation = PerformanceViolation(
            threshold=threshold,
            actual_value=300.0
        )
        
        expected = "Performance violation: API Response Time exceeded 200.0ms (actual: 300.00ms)"
        assert str(violation) == expected


class TestPerformanceGate:
    """Test PerformanceGate class functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.gate = PerformanceGate(enable_enforcement=False)
    
    def test_gate_initialization(self):
        """Test gate initialization with default thresholds."""
        gate = PerformanceGate()
        
        assert gate.enable_enforcement is True
        assert 'api_response_p95' in gate.thresholds
        assert 'api_response_p99' in gate.thresholds
        assert 'memory_growth_hourly' in gate.thresholds
        assert gate.violations == []
    
    def test_custom_thresholds(self):
        """Test gate with custom thresholds."""
        custom_threshold = PerformanceThreshold(
            name="Custom Threshold",
            value=100.0,
            unit="ms",
            violation_type=PerformanceViolationType.API_RESPONSE_TIME,
            description="Custom test threshold"
        )
        
        gate = PerformanceGate(
            enable_enforcement=False,
            custom_thresholds={'custom': custom_threshold}
        )
        
        assert 'custom' in gate.thresholds
        assert gate.thresholds['custom'] == custom_threshold
    
    def test_api_response_time_tracking(self):
        """Test API response time tracking without violations."""
        # Add multiple response times
        for duration in [150, 180, 160, 170, 165]:
            self.gate.check_api_response_time(duration, "p95")
        
        assert len(self.gate._response_times) == 5
        assert self.gate._response_times == [150, 180, 160, 170, 165]
    
    def test_api_response_time_percentile_calculation(self):
        """Test percentile calculation with sufficient samples."""
        # Add 25 samples to trigger percentile calculation
        response_times = [100 + i * 5 for i in range(25)]  # 100, 105, 110, ..., 220
        
        for duration in response_times:
            self.gate.check_api_response_time(duration, "p95")
        
        # With 25 samples, p95 should be around index 23 (0.95 * 25 = 23.75)
        sorted_times = sorted(response_times)
        expected_p95 = sorted_times[23]  # Should be 215
        
        # Verify no violation since 215 > 200 but enforcement is disabled
        assert len(self.gate.violations) == 0
    
    def test_api_response_time_violation_enforcement(self):
        """Test API response time violation with enforcement enabled."""
        gate = PerformanceGate(enable_enforcement=True)
        
        # Add samples that will trigger p95 violation
        high_response_times = [300, 350, 400, 450, 500] * 5  # 25 samples, all > 200ms
        
        with pytest.raises(PerformanceViolation):
            for duration in high_response_times:
                gate.check_api_response_time(duration, "p95")
    
    def test_unknown_percentile_handling(self):
        """Test handling of unknown percentile values."""
        with patch('src.performance_gates.logger') as mock_logger:
            self.gate.check_api_response_time(150, "p90")
            mock_logger.warning.assert_called_with("Unknown percentile threshold: p90")
    
    def test_database_query_time_check(self):
        """Test database query time checking."""
        # Fast query should pass
        self.gate.check_database_query_time(50.0, "simple")
        assert len(self.gate.violations) == 0
        
        # Slow query should create violation but not raise (enforcement disabled)
        self.gate.check_database_query_time(150.0, "simple")
        assert len(self.gate.violations) == 1
        
        violation = self.gate.violations[0]
        assert violation.actual_value == 150.0
        assert violation.threshold.value == 100.0
    
    def test_database_query_time_with_enforcement(self):
        """Test database query time with enforcement enabled."""
        gate = PerformanceGate(enable_enforcement=True)
        
        with pytest.raises(PerformanceViolation):
            gate.check_database_query_time(150.0, "simple")
    
    def test_memory_growth_baseline_setting(self):
        """Test memory growth baseline initialization."""
        with patch('tracemalloc.is_tracing', return_value=True), \
             patch('tracemalloc.get_traced_memory', return_value=(1024*1024, 2048*1024)):
            
            self.gate.check_memory_growth()
            
            assert self.gate._memory_baseline == 1.0  # 1MB in MB
            assert self.gate._memory_start_time is not None
    
    def test_memory_growth_calculation(self):
        """Test memory growth rate calculation."""
        with patch('tracemalloc.is_tracing', return_value=True), \
             patch('tracemalloc.get_traced_memory') as mock_memory, \
             patch('time.time') as mock_time:
            
            # Set up baseline
            mock_memory.return_value = (1024*1024, 2048*1024)  # 1MB current
            mock_time.return_value = 1000.0
            self.gate.check_memory_growth()
            
            # Simulate memory growth after 1 hour
            mock_memory.return_value = (1024*1024*1.2, 2048*1024)  # 1.2MB current (20% growth)
            mock_time.return_value = 1000.0 + 3600.0  # 1 hour later
            
            self.gate.check_memory_growth()
            
            # Should create violation for 20% growth rate (> 10% threshold)
            assert len(self.gate.violations) == 1
            violation = self.gate.violations[0]
            assert violation.actual_value == 20.0  # 20% growth rate per hour
    
    def test_memory_growth_no_tracemalloc(self):
        """Test memory growth check when tracemalloc is not enabled."""
        with patch('tracemalloc.is_tracing', return_value=False), \
             patch('src.performance_gates.logger') as mock_logger:
            
            self.gate.check_memory_growth()
            
            mock_logger.warning.assert_called_with(
                "Memory tracking not enabled, cannot check memory growth"
            )
    
    def test_violation_summary(self):
        """Test performance violation summary generation."""
        # Create some violations
        self.gate.check_database_query_time(150.0, "simple")
        self.gate.check_database_query_time(200.0, "simple")
        
        summary = self.gate.get_violation_summary()
        
        assert summary['total_violations'] == 2
        assert 'violations_by_type' in summary
        assert 'database_query_time' in summary['violations_by_type']
        assert len(summary['violations_by_type']['database_query_time']) == 2
        assert summary['enforcement_enabled'] is False
        assert 'thresholds' in summary
    
    def test_percentile_helper_methods(self):
        """Test percentile calculation helper methods."""
        # Test p95 calculation
        index_p95 = self.gate._get_percentile_index("p95", 100)
        assert index_p95 == 95
        
        # Test p99 calculation  
        index_p99 = self.gate._get_percentile_index("p99", 100)
        assert index_p99 == 99
        
        # Test unknown percentile
        index_unknown = self.gate._get_percentile_index("p90", 100)
        assert index_unknown == 99  # Defaults to max
    
    def test_calculate_current_percentile_insufficient_samples(self):
        """Test percentile calculation with insufficient samples."""
        # Add only 10 samples (< 20 required)
        for i in range(10):
            self.gate._response_times.append(100 + i * 10)
        
        result = self.gate._calculate_current_percentile("p95")
        assert result is None
    
    def test_calculate_current_percentile_sufficient_samples(self):
        """Test percentile calculation with sufficient samples."""
        # Add 25 samples
        for i in range(25):
            self.gate._response_times.append(100 + i * 10)
        
        result = self.gate._calculate_current_percentile("p95")
        assert result is not None
        assert isinstance(result, float)


class TestPerformanceDecorators:
    """Test performance monitoring decorators."""
    
    def test_api_response_time_decorator_sync(self):
        """Test API response time decorator on sync function."""
        @enforce_api_response_time("p95")
        def fast_function():
            time.sleep(0.01)  # 10ms
            return "success"
        
        result = fast_function()
        assert result == "success"
    
    def test_api_response_time_decorator_slow_sync(self):
        """Test API response time decorator on slow sync function."""
        @enforce_api_response_time("p95")
        def slow_function():
            time.sleep(0.05)  # 50ms
            return "success"
        
        # Should not raise exception with default global gate (enforcement disabled)
        result = slow_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_api_response_time_decorator_async(self):
        """Test API response time decorator on async function."""
        @enforce_api_response_time("p95")
        async def fast_async_function():
            await asyncio.sleep(0.01)  # 10ms
            return "async_success"
        
        result = await fast_async_function()
        assert result == "async_success"
    
    def test_database_query_decorator_sync(self):
        """Test database query time decorator on sync function."""
        @enforce_database_query_time("simple")
        def fast_query():
            time.sleep(0.02)  # 20ms
            return {"data": "result"}
        
        result = fast_query()
        assert result == {"data": "result"}
    
    @pytest.mark.asyncio
    async def test_database_query_decorator_async(self):
        """Test database query time decorator on async function."""
        @enforce_database_query_time("simple")
        async def fast_async_query():
            await asyncio.sleep(0.02)  # 20ms
            return {"data": "async_result"}
        
        result = await fast_async_query()
        assert result == {"data": "async_result"}


class TestPerformanceContextManagers:
    """Test performance context managers."""
    
    def test_performance_gate_context_manager(self):
        """Test sync performance gate context manager."""
        with performance_gate_context(check_memory=True) as gate:
            assert gate is not None
            time.sleep(0.01)  # Small delay
    
    @pytest.mark.asyncio
    async def test_async_performance_gate_context_manager(self):
        """Test async performance gate context manager."""
        async with async_performance_gate_context(check_memory=True) as gate:
            assert gate is not None
            await asyncio.sleep(0.01)  # Small delay
    
    def test_performance_context_slow_operation_warning(self):
        """Test slow operation warning in context manager."""
        with patch('src.performance_gates.logger') as mock_logger:
            with performance_gate_context():
                time.sleep(1.1)  # > 1 second should trigger warning
            
            # Check if warning was logged
            mock_logger.warning.assert_called()
            args = mock_logger.warning.call_args[0]
            assert "Slow operation detected" in args[0]


class TestIntegrationAndInitialization:
    """Test system integration and initialization."""
    
    def test_integration_with_monitoring_success(self):
        """Test successful integration with existing monitoring."""
        with patch('src.performance_gates.logger') as mock_logger:
            result = integrate_with_existing_monitoring()
            
            assert result is True
            mock_logger.info.assert_called_with(
                "Performance gates successfully integrated with existing monitoring"
            )
    
    def test_integration_import_error(self):
        """Test integration failure due to import error."""
        with patch('src.performance_gates.logger') as mock_logger, \
             patch('builtins.__import__', side_effect=ImportError("Test import error")):
            
            result = integrate_with_existing_monitoring()
            
            assert result is False
            mock_logger.error.assert_called()
    
    def test_integration_unexpected_error(self):
        """Test integration failure due to unexpected error."""
        with patch('src.performance_gates.logger') as mock_logger, \
             patch('src.performance_gates._patch_monitoring_system', side_effect=RuntimeError("Test error")):
            
            result = integrate_with_existing_monitoring()
            
            assert result is False
            mock_logger.error.assert_called()
    
    def test_initialize_performance_gates_success(self):
        """Test successful performance gates initialization."""
        with patch('src.performance_gates.integrate_with_existing_monitoring', return_value=True), \
             patch('src.performance_gates.logger') as mock_logger:
            
            result = initialize_performance_gates()
            
            assert result is True
            mock_logger.info.assert_called_with("Performance gates system initialized successfully")
    
    def test_initialize_performance_gates_integration_failure(self):
        """Test initialization with integration failure."""
        with patch('src.performance_gates.integrate_with_existing_monitoring', return_value=False), \
             patch('src.performance_gates.logger') as mock_logger:
            
            result = initialize_performance_gates()
            
            assert result is True  # Still returns True but logs warning
            mock_logger.warning.assert_called_with("Performance gates initialized but integration failed")
    
    def test_initialize_performance_gates_exception(self):
        """Test initialization with exception."""
        with patch('src.performance_gates.integrate_with_existing_monitoring', side_effect=RuntimeError("Test error")), \
             patch('src.performance_gates.logger') as mock_logger:
            
            result = initialize_performance_gates()
            
            assert result is False
            mock_logger.error.assert_called()


class TestGlobalPerformanceGate:
    """Test global performance gate instance."""
    
    def test_global_performance_gate_exists(self):
        """Test that global performance gate instance exists."""
        from src.performance_gates import performance_gate
        
        assert performance_gate is not None
        assert isinstance(performance_gate, PerformanceGate)
        assert performance_gate.enable_enforcement is True
    
    def test_global_gate_thresholds(self):
        """Test global gate has all required thresholds."""
        from src.performance_gates import performance_gate
        
        required_thresholds = [
            'api_response_p95',
            'api_response_p99', 
            'memory_growth_hourly',
            'cpu_usage_average',
            'db_query_simple',
            'bundle_size_gzipped'
        ]
        
        for threshold_key in required_thresholds:
            assert threshold_key in performance_gate.thresholds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])