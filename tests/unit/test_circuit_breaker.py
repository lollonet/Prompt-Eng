"""
Comprehensive unit tests for CircuitBreaker and CircuitBreakerManager.

Tests the critical resilience infrastructure that protects against
cascading failures in distributed systems.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.web_research.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager, 
    CircuitBreakerException,
    CircuitState,
    CircuitMetrics
)
from src.web_research.config import CircuitBreakerConfig


class TestCircuitMetrics:
    """Test CircuitMetrics calculations."""
    
    def test_metrics_initialization(self):
        """Test metrics start with correct defaults."""
        metrics = CircuitMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.consecutive_failures == 0
        assert metrics.consecutive_successes == 0
        assert metrics.last_failure_time is None
        assert metrics.last_success_time is None
        assert metrics.response_times == []
    
    def test_failure_rate_calculation(self):
        """Test failure rate calculations."""
        metrics = CircuitMetrics()
        
        # No requests = 0% failure rate
        assert metrics.failure_rate == 0.0
        assert metrics.success_rate == 1.0
        
        # Add some requests
        metrics.total_requests = 10
        metrics.failed_requests = 3
        metrics.successful_requests = 7
        
        assert metrics.failure_rate == 0.3
        assert metrics.success_rate == 0.7
        
        # All failures
        metrics.total_requests = 5
        metrics.failed_requests = 5
        metrics.successful_requests = 0
        
        assert metrics.failure_rate == 1.0
        assert metrics.success_rate == 0.0
    
    def test_average_response_time(self):
        """Test average response time calculation."""
        metrics = CircuitMetrics()
        
        # No response times = 0.0
        assert metrics.average_response_time == 0.0
        
        # Add response times
        metrics.response_times = [0.1, 0.2, 0.3, 0.4, 0.5]
        assert metrics.average_response_time == 0.3
        
        # Test last 100 limit
        metrics.response_times = list(range(200))  # 0-199
        # Should only use last 100: 100-199, average = 149.5
        assert metrics.average_response_time == 149.5


class TestCircuitBreaker:
    """Test CircuitBreaker core functionality."""
    
    @pytest.fixture
    def config(self):
        """Default test configuration."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0,
            max_timeout_seconds=10.0,
            exponential_backoff=True
        )
    
    @pytest.fixture
    def circuit_breaker(self, config):
        """Create circuit breaker for testing."""
        return CircuitBreaker("test_breaker", config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_initialization(self, circuit_breaker, config):
        """Test circuit breaker initializes correctly."""
        assert circuit_breaker.name == "test_breaker"
        assert circuit_breaker.config == config
        assert circuit_breaker.is_closed()
        assert not circuit_breaker.is_open()
        assert not circuit_breaker.is_half_open()
        
        metrics = circuit_breaker.get_metrics()
        assert metrics.total_requests == 0
        assert metrics.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_successful_function_execution(self, circuit_breaker):
        """Test successful function execution through circuit breaker."""
        def test_function(x, y):
            return x + y
        
        result = await circuit_breaker.call(test_function, 5, 10)
        
        assert result == 15
        assert circuit_breaker.is_closed()
        
        metrics = circuit_breaker.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.consecutive_successes == 1
        assert metrics.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_async_function_execution(self, circuit_breaker):
        """Test async function execution through circuit breaker."""
        async def async_test_function(value):
            await asyncio.sleep(0.01)
            return value * 2
        
        result = await circuit_breaker.call(async_test_function, 21)
        
        assert result == 42
        assert circuit_breaker.is_closed()
        
        metrics = circuit_breaker.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
    
    @pytest.mark.asyncio
    async def test_function_failure_handling(self, circuit_breaker):
        """Test handling of function failures."""
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await circuit_breaker.call(failing_function)
        
        assert circuit_breaker.is_closed()  # Should still be closed after 1 failure
        
        metrics = circuit_breaker.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.failed_requests == 1
        assert metrics.consecutive_failures == 1
        assert metrics.consecutive_successes == 0
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failure_threshold(self, circuit_breaker):
        """Test circuit opens after exceeding failure threshold."""
        def failing_function():
            raise RuntimeError("Simulated failure")
        
        # Should fail 3 times (threshold) before opening
        for i in range(3):
            with pytest.raises(RuntimeError):
                await circuit_breaker.call(failing_function)
            
            if i < 2:  # First 2 failures
                assert circuit_breaker.is_closed()
            else:  # 3rd failure should open circuit
                assert circuit_breaker.is_open()
        
        metrics = circuit_breaker.get_metrics()
        assert metrics.consecutive_failures == 3
        assert metrics.failed_requests == 3
    
    @pytest.mark.asyncio
    async def test_circuit_blocks_requests_when_open(self, circuit_breaker):
        """Test circuit blocks requests when open."""
        # Force circuit to open
        await self._force_circuit_open(circuit_breaker)
        
        def any_function():
            return "should not execute"
        
        # Should block request and raise CircuitBreakerException
        with pytest.raises(CircuitBreakerException, match="is open"):
            await circuit_breaker.call(any_function)
        
        # Function should not have been called
        metrics = circuit_breaker.get_metrics()
        # Metrics shouldn't change from blocking
        assert metrics.total_requests == 3  # From force_open method
    
    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self, circuit_breaker):
        """Test circuit transitions from open to half-open after timeout."""
        # Force circuit open
        await self._force_circuit_open(circuit_breaker)
        assert circuit_breaker.is_open()
        
        # Wait for timeout (using short timeout for test)
        circuit_breaker._current_timeout = 0.1
        await asyncio.sleep(0.15)
        
        # Should transition to half-open on next state update
        def test_function():
            return "test"
        
        # This call should transition to half-open and execute
        result = await circuit_breaker.call(test_function)
        
        assert result == "test"
        assert circuit_breaker.is_half_open()
    
    @pytest.mark.asyncio
    async def test_half_open_closes_after_successes(self, circuit_breaker):
        """Test half-open circuit closes after success threshold."""
        # Force to half-open state
        await self._force_circuit_to_half_open(circuit_breaker)
        
        def successful_function():
            return "success"
        
        # Need success_threshold (2) successes to close
        for i in range(2):
            result = await circuit_breaker.call(successful_function)
            assert result == "success"
            
            if i < 1:  # First success
                assert circuit_breaker.is_half_open()
            else:  # Second success should close
                assert circuit_breaker.is_closed()
    
    @pytest.mark.asyncio
    async def test_half_open_reopens_on_failure(self, circuit_breaker):
        """Test half-open circuit reopens immediately on failure."""
        # Force to half-open state
        await self._force_circuit_to_half_open(circuit_breaker)
        
        def failing_function():
            raise ConnectionError("Service still down")
        
        # Single failure in half-open should reopen circuit
        with pytest.raises(ConnectionError):
            await circuit_breaker.call(failing_function)
        
        assert circuit_breaker.is_open()
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, circuit_breaker):
        """Test exponential backoff increases timeout."""
        initial_timeout = circuit_breaker._current_timeout
        
        # Force circuit to open
        await self._force_circuit_open(circuit_breaker)
        
        first_timeout = circuit_breaker._current_timeout
        assert first_timeout == initial_timeout * 2
        
        # Force open again (simulate repeated failures)
        await circuit_breaker._open_circuit()
        
        second_timeout = circuit_breaker._current_timeout
        assert second_timeout == first_timeout * 2
        
        # Should not exceed max timeout
        circuit_breaker._current_timeout = circuit_breaker.config.max_timeout_seconds
        await circuit_breaker._open_circuit()
        
        final_timeout = circuit_breaker._current_timeout
        assert final_timeout == circuit_breaker.config.max_timeout_seconds
    
    @pytest.mark.asyncio
    async def test_circuit_reset(self, circuit_breaker):
        """Test circuit reset functionality."""
        # Add some failures and open circuit
        await self._force_circuit_open(circuit_breaker)
        
        original_metrics = circuit_breaker.get_metrics()
        assert original_metrics.total_requests > 0
        assert circuit_breaker.is_open()
        
        # Reset circuit
        await circuit_breaker.reset()
        
        assert circuit_breaker.is_closed()
        assert circuit_breaker._current_timeout == circuit_breaker.config.timeout_seconds
        
        reset_metrics = circuit_breaker.get_metrics()
        assert reset_metrics.total_requests == 0
        assert reset_metrics.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_health_check_functionality(self, circuit_breaker):
        """Test health check integration."""
        # Test without health check function
        result = await circuit_breaker.health_check()
        assert result is True
        
        # Set sync health check
        def sync_health_check():
            return False
        
        circuit_breaker.set_health_check(sync_health_check)
        result = await circuit_breaker.health_check()
        assert result is False
        
        # Set async health check
        async def async_health_check():
            return True
        
        circuit_breaker.set_health_check(async_health_check)
        result = await circuit_breaker.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, circuit_breaker):
        """Test health check handles exceptions gracefully."""
        def failing_health_check():
            raise RuntimeError("Health check failed")
        
        circuit_breaker.set_health_check(failing_health_check)
        
        result = await circuit_breaker.health_check()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_response_time_tracking(self, circuit_breaker):
        """Test response time tracking."""
        async def slow_function():
            await asyncio.sleep(0.05)
            return "slow result"
        
        start_time = time.time()
        result = await circuit_breaker.call(slow_function)
        end_time = time.time()
        
        assert result == "slow result"
        
        metrics = circuit_breaker.get_metrics()
        assert len(metrics.response_times) == 1
        
        recorded_time = metrics.response_times[0]
        actual_time = end_time - start_time
        
        # Response time should be reasonably close to actual time
        assert 0.04 <= recorded_time <= actual_time + 0.01
        assert metrics.average_response_time == recorded_time
    
    @pytest.mark.asyncio
    async def test_concurrent_access_thread_safety(self, circuit_breaker):
        """Test thread safety with concurrent access."""
        call_count = 0
        
        def counting_function():
            nonlocal call_count
            call_count += 1
            return call_count
        
        # Execute many concurrent calls
        tasks = [circuit_breaker.call(counting_function) for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # All calls should succeed
        assert len(results) == 50
        assert call_count == 50
        
        # Results should be unique (no race conditions)
        assert len(set(results)) == 50
        
        # Metrics should be accurate
        metrics = circuit_breaker.get_metrics()
        assert metrics.total_requests == 50
        assert metrics.successful_requests == 50
    
    @pytest.mark.asyncio
    async def test_string_representation(self, circuit_breaker):
        """Test string representation of circuit breaker."""
        str_repr = str(circuit_breaker)
        
        assert "CircuitBreaker" in str_repr
        assert "test_breaker" in str_repr
        assert "state=closed" in str_repr
        assert "failures=0" in str_repr
        assert "successes=0" in str_repr
    
    # Helper methods
    async def _force_circuit_open(self, circuit_breaker):
        """Helper to force circuit into open state."""
        def failing_function():
            raise RuntimeError("Force failure")
        
        # Trigger failures to open circuit
        for _ in range(circuit_breaker.config.failure_threshold):
            with pytest.raises(RuntimeError):
                await circuit_breaker.call(failing_function)
    
    async def _force_circuit_to_half_open(self, circuit_breaker):
        """Helper to force circuit into half-open state."""
        # Manually set the circuit to half-open state for testing
        circuit_breaker._state = CircuitState.HALF_OPEN
        circuit_breaker._timeout_start_time = None
        
        # Reset consecutive failures to 0 for half-open state
        # (since half-open means we're testing if service recovered)
        circuit_breaker._metrics.total_requests = 3
        circuit_breaker._metrics.failed_requests = 3
        circuit_breaker._metrics.consecutive_failures = 0  # Reset for half-open
        circuit_breaker._metrics.consecutive_successes = 0


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager functionality."""
    
    @pytest.fixture
    def config(self):
        """Default test configuration."""
        return CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=1,
            timeout_seconds=0.5
        )
    
    @pytest.fixture
    def manager(self, config):
        """Create circuit breaker manager for testing."""
        return CircuitBreakerManager(config)
    
    def test_manager_initialization(self, manager, config):
        """Test manager initializes correctly."""
        assert manager.default_config == config
        assert manager._breakers == {}
    
    def test_get_breaker_creates_new(self, manager):
        """Test getting breaker creates new one if not exists."""
        breaker = manager.get_breaker("test_service")
        
        assert isinstance(breaker, CircuitBreaker)
        assert breaker.name == "test_service"
        assert "test_service" in manager._breakers
    
    def test_get_breaker_returns_existing(self, manager):
        """Test getting existing breaker returns same instance."""
        breaker1 = manager.get_breaker("service1")
        breaker2 = manager.get_breaker("service1")
        
        assert breaker1 is breaker2
    
    def test_get_breaker_with_custom_config(self, manager):
        """Test creating breaker with custom config."""
        custom_config = CircuitBreakerConfig(failure_threshold=10)
        
        breaker = manager.get_breaker("custom_service", custom_config)
        
        assert breaker.config.failure_threshold == 10
        assert breaker.config != manager.default_config
    
    @pytest.mark.asyncio
    async def test_reset_all_breakers(self, manager):
        """Test resetting all circuit breakers."""
        # Create multiple breakers and add some failures
        breaker1 = manager.get_breaker("service1")
        breaker2 = manager.get_breaker("service2")
        
        def failing_function():
            raise ValueError("Test failure")
        
        # Add failures to both breakers
        with pytest.raises(ValueError):
            await breaker1.call(failing_function)
        with pytest.raises(ValueError):
            await breaker2.call(failing_function)
        
        # Verify they have failures
        assert breaker1.get_metrics().failed_requests > 0
        assert breaker2.get_metrics().failed_requests > 0
        
        # Reset all
        await manager.reset_all()
        
        # Verify reset
        assert breaker1.get_metrics().failed_requests == 0
        assert breaker2.get_metrics().failed_requests == 0
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, manager):
        """Test health checking all breakers."""
        # Create breakers with different health states
        breaker1 = manager.get_breaker("healthy_service")
        breaker2 = manager.get_breaker("unhealthy_service")
        
        breaker1.set_health_check(lambda: True)
        breaker2.set_health_check(lambda: False)
        
        results = await manager.health_check_all()
        
        assert results["healthy_service"] is True
        assert results["unhealthy_service"] is False
    
    def test_get_all_metrics(self, manager):
        """Test getting metrics for all breakers."""
        # Create breakers
        breaker1 = manager.get_breaker("service1")
        breaker2 = manager.get_breaker("service2")
        
        # Get all metrics
        all_metrics = manager.get_all_metrics()
        
        assert "service1" in all_metrics
        assert "service2" in all_metrics
        assert isinstance(all_metrics["service1"], CircuitMetrics)
        assert isinstance(all_metrics["service2"], CircuitMetrics)
    
    @pytest.mark.asyncio
    async def test_protected_call_context_manager(self, manager):
        """Test protected call context manager."""
        def test_function(value):
            return value * 2
        
        async with manager.protected_call("test_service", test_function, 21) as result:
            assert result == 42
        
        # Verify breaker was created and used
        assert "test_service" in manager._breakers
        breaker = manager.get_breaker("test_service")
        assert breaker.get_metrics().successful_requests == 1
    
    @pytest.mark.asyncio
    async def test_protected_call_handles_circuit_breaker_exception(self, manager):
        """Test protected call handles circuit breaker exceptions."""
        # Force breaker to open
        breaker = manager.get_breaker("failing_service")
        breaker._state = CircuitState.OPEN
        breaker._timeout_start_time = time.time()
        
        def any_function():
            return "should not execute"
        
        with pytest.raises(CircuitBreakerException):
            async with manager.protected_call("failing_service", any_function):
                pass
    
    @pytest.mark.asyncio
    async def test_protected_call_handles_function_exceptions(self, manager):
        """Test protected call handles function exceptions."""
        def failing_function():
            raise ValueError("Function failed")
        
        with pytest.raises(ValueError, match="Function failed"):
            async with manager.protected_call("error_service", failing_function):
                pass
        
        # Verify failure was recorded
        breaker = manager.get_breaker("error_service")
        assert breaker.get_metrics().failed_requests == 1


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_realistic_service_failure_recovery_scenario(self):
        """Test realistic failure and recovery scenario."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=0.1,
            exponential_backoff=True
        )
        
        circuit_breaker = CircuitBreaker("payment_service", config)
        
        # Simulate service working normally
        def working_service():
            return {"status": "success", "payment_id": "12345"}
        
        result = await circuit_breaker.call(working_service)
        assert result["status"] == "success"
        assert circuit_breaker.is_closed()
        
        # Simulate service starting to fail
        def failing_service():
            raise ConnectionError("Payment service unavailable")
        
        # Fail 3 times to open circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await circuit_breaker.call(failing_service)
        
        assert circuit_breaker.is_open()
        
        # Requests should be blocked
        with pytest.raises(CircuitBreakerException):
            await circuit_breaker.call(working_service)
        
        # Wait for timeout (need to wait for the actual timeout used)
        await asyncio.sleep(0.25)  # Wait longer than the initial timeout
        
        # Service recovers - should transition to half-open and then closed
        result1 = await circuit_breaker.call(working_service)
        assert circuit_breaker.is_half_open()
        
        result2 = await circuit_breaker.call(working_service)
        assert circuit_breaker.is_closed()
        
        # Verify service is fully operational
        result3 = await circuit_breaker.call(working_service)
        assert result3["status"] == "success"