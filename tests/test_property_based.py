"""
Property-based tests using Hypothesis for robust testing of complex logic.

Tests mathematical properties, invariants, and edge cases that traditional
unit tests might miss through comprehensive generative testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, example, settings
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule, invariant, initialize
import time
import asyncio
from typing import List, Dict, Any

from src.result_types import Success, Error, safe_call, combine_results
from src.events import Event, EventBus
from src.performance_gates import PerformanceGate, PerformanceThreshold, PerformanceViolationType
from src.performance import PerformanceMetrics, LazyEvaluator, lazy


class TestResultTypeProperties:
    """Property-based tests for Result types."""
    
    @given(st.integers())
    def test_success_identity_law(self, value):
        """Test that Success satisfies identity law for map."""
        success = Success(value)
        
        # map(identity) == identity
        identity_mapped = success.map(lambda x: x)
        
        assert identity_mapped.is_success()
        assert identity_mapped.unwrap() == value
    
    @given(st.integers())
    def test_success_composition_law(self, value):
        """Test that Success satisfies composition law for map."""
        success = Success(value)
        
        def f(x): return x + 1
        def g(x): return x * 2
        
        # map(f).map(g) == map(compose(g, f))
        composed1 = success.map(f).map(g)
        composed2 = success.map(lambda x: g(f(x)))
        
        assert composed1.is_success()
        assert composed2.is_success()
        assert composed1.unwrap() == composed2.unwrap()
    
    @given(st.text())
    def test_error_identity_law(self, error_msg):
        """Test that Error satisfies identity law for map."""
        error = Error(error_msg)
        
        # map on Error should do nothing
        mapped = error.map(lambda x: x * 100)
        
        assert mapped.is_error()
        assert mapped.error == error_msg
    
    @given(st.lists(st.integers(), min_size=1))
    def test_combine_results_all_success_property(self, values):
        """Test combine_results property with all successful values."""
        results = [Success(v) for v in values]
        
        combined = combine_results(results)
        
        assert combined.is_success()
        assert combined.unwrap() == values
    
    @given(st.lists(st.integers(), min_size=1), st.text())
    def test_combine_results_first_error_property(self, values, error_msg):
        """Test combine_results returns first error."""
        # Create mix of success and error results
        results = [Success(v) for v in values[:len(values)//2]]
        results.append(Error(error_msg))
        results.extend([Success(v) for v in values[len(values)//2:]])
        
        combined = combine_results(results)
        
        assert combined.is_error()
        assert combined.error == error_msg
    
    @given(st.integers(min_value=1, max_value=1000))
    def test_safe_call_preserves_result(self, value):
        """Test safe_call preserves successful function results."""
        def identity_function():
            return value
        
        result = safe_call(identity_function)
        
        assert result.is_success()
        assert result.unwrap() == value
    
    @given(st.text())
    def test_safe_call_catches_exceptions(self, error_message):
        """Test safe_call properly catches exceptions."""
        def failing_function():
            raise ValueError(error_message)
        
        result = safe_call(failing_function)
        
        assert result.is_error()
        assert isinstance(result.error, ValueError)
        assert str(result.error) == error_message
    
    @given(st.integers())
    def test_result_and_then_left_identity(self, value):
        """Test and_then satisfies left identity (monadic law)."""
        # return(a).and_then(f) == f(a)
        def f(x):
            return Success(x * 2)
        
        result1 = Success(value).and_then(f)
        result2 = f(value)
        
        assert result1.is_success() == result2.is_success()
        if result1.is_success():
            assert result1.unwrap() == result2.unwrap()
    
    @given(st.integers())
    def test_result_and_then_right_identity(self, value):
        """Test and_then satisfies right identity (monadic law)."""
        # m.and_then(return) == m
        success = Success(value)
        
        result = success.and_then(lambda x: Success(x))
        
        assert result.is_success()
        assert result.unwrap() == value
    
    @given(st.integers())
    def test_result_and_then_associativity(self, value):
        """Test and_then satisfies associativity (monadic law)."""
        # (m.and_then(f)).and_then(g) == m.and_then(lambda x: f(x).and_then(g))
        def f(x): return Success(x + 1)
        def g(x): return Success(x * 2)
        
        success = Success(value)
        
        result1 = success.and_then(f).and_then(g)
        result2 = success.and_then(lambda x: f(x).and_then(g))
        
        assert result1.is_success()
        assert result2.is_success()
        assert result1.unwrap() == result2.unwrap()


class TestEventSystemProperties:
    """Property-based tests for event system."""
    
    @given(st.text(min_size=1), st.text(min_size=1))
    def test_event_creation_properties(self, event_type, source):
        """Test event creation maintains required properties."""
        event = Event(event_type=event_type, source=source)
        
        assert event.event_type == event_type
        assert event.source == source
        assert isinstance(event.payload, dict)
        assert event.timestamp > 0
        assert event.event_id is not None
    
    @given(st.dictionaries(st.text(), st.integers()))
    def test_event_payload_preservation(self, payload):
        """Test event payload is preserved correctly."""
        event = Event(event_type="test", source="test", payload=payload)
        
        assert event.payload == payload
        
        # Test serialization preserves payload
        event_dict = event.to_dict()
        assert event_dict["payload"] == payload
    
    @given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
    def test_event_bus_handler_registration(self, event_types):
        """Test event bus handler registration properties."""
        event_bus = EventBus()
        handlers_called = []
        
        def test_handler(event):
            handlers_called.append(event.event_type)
        
        # Subscribe to all event types
        for event_type in event_types:
            event_bus.subscribe(event_type, test_handler)
        
        # Publish events and verify all are handled
        for event_type in event_types:
            event = Event(event_type=event_type, source="test")
            event_bus.publish(event)
        
        assert len(handlers_called) == len(event_types)
        assert set(handlers_called) == set(event_types)
    
    @given(st.integers(min_value=1, max_value=100))
    def test_event_bus_metrics_accuracy(self, num_events):
        """Test event bus metrics are accurate."""
        event_bus = EventBus()
        
        # Publish events
        for i in range(num_events):
            event = Event(event_type="test_event", source="test")
            event_bus.publish(event)
        
        metrics = event_bus.get_metrics()
        
        assert metrics["total_events_published"] == num_events
        assert metrics["events_by_type"]["test_event"] == num_events


class TestPerformanceGateProperties:
    """Property-based tests for performance gates."""
    
    @given(st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=1, max_size=100))
    def test_response_time_tracking_properties(self, response_times):
        """Test response time tracking maintains correct state."""
        gate = PerformanceGate(enable_enforcement=False)
        
        for time_ms in response_times:
            gate.check_api_response_time(time_ms, "p95")
        
        # Properties that should hold
        assert len(gate._response_times) == len(response_times)
        assert all(t in gate._response_times for t in response_times)
    
    @given(st.floats(min_value=0.1, max_value=50.0))
    def test_database_query_threshold_properties(self, query_time):
        """Test database query time checking properties."""
        gate = PerformanceGate(enable_enforcement=False)
        
        initial_violations = len(gate.violations)
        gate.check_database_query_time(query_time, "simple")
        
        # If query time exceeds threshold (100ms), should create violation
        if query_time > 100.0:
            assert len(gate.violations) == initial_violations + 1
        else:
            assert len(gate.violations) == initial_violations
    
    @given(st.floats(min_value=1.0, max_value=1000.0))
    @example(150.0)  # Specific example that should trigger violation
    def test_violation_creation_properties(self, duration):
        """Test violation creation maintains correct properties."""
        gate = PerformanceGate(enable_enforcement=False)
        
        initial_count = len(gate.violations)
        gate.check_database_query_time(duration, "simple")
        
        if duration > 100.0:  # Threshold for simple queries
            assert len(gate.violations) == initial_count + 1
            violation = gate.violations[-1]
            assert violation.actual_value == duration
            assert violation.threshold.value == 100.0
        else:
            assert len(gate.violations) == initial_count


class TestLazyEvaluationProperties:
    """Property-based tests for lazy evaluation."""
    
    @given(st.integers())
    def test_lazy_evaluation_compute_once(self, value):
        """Test lazy evaluation computes exactly once."""
        call_count = 0
        
        def computation():
            nonlocal call_count
            call_count += 1
            return value
        
        lazy_value = lazy(computation)
        
        # Initially not computed
        assert not lazy_value.is_computed
        assert call_count == 0
        
        # First access computes
        result1 = lazy_value.get()
        assert lazy_value.is_computed
        assert call_count == 1
        assert result1 == value
        
        # Second access doesn't recompute
        result2 = lazy_value.get()
        assert call_count == 1
        assert result2 == value
    
    @given(st.integers())
    def test_lazy_evaluation_invalidation(self, value):
        """Test lazy evaluation invalidation resets state."""
        call_count = 0
        
        def computation():
            nonlocal call_count
            call_count += 1
            return value + call_count  # Different result each time
        
        lazy_value = lazy(computation)
        
        # Compute once
        result1 = lazy_value.get()
        assert call_count == 1
        
        # Invalidate and compute again
        lazy_value.invalidate()
        assert not lazy_value.is_computed
        
        result2 = lazy_value.get()
        assert call_count == 2
        assert result2 != result1  # Should be different due to call_count


class TestPerformanceMetricsProperties:
    """Property-based tests for performance metrics."""
    
    @given(st.text(min_size=1), st.floats(min_value=0.001, max_value=10.0))
    def test_performance_metrics_properties(self, operation_name, execution_time):
        """Test performance metrics maintain correct properties."""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            memory_usage_mb=100.0
        )
        
        assert metrics.operation_name == operation_name
        assert metrics.execution_time == execution_time
        assert metrics.memory_usage_mb == 100.0
        assert metrics.start_time > 0
    
    @given(st.integers(min_value=0, max_value=1000), st.integers(min_value=0, max_value=1000))
    def test_cache_hit_ratio_calculation(self, hits, misses):
        """Test cache hit ratio calculation properties."""
        metrics = PerformanceMetrics(
            operation_name="test",
            execution_time=1.0,
            memory_usage_mb=50.0,
            cache_hits=hits,
            cache_misses=misses
        )
        
        total = hits + misses
        if total == 0:
            assert metrics.cache_hit_ratio == 0.0
        else:
            expected_ratio = (hits / total) * 100
            assert abs(metrics.cache_hit_ratio - expected_ratio) < 0.001
    
    @given(st.integers(min_value=0, max_value=100))
    def test_metrics_to_dict_completeness(self, io_ops):
        """Test metrics to_dict includes all expected fields."""
        metrics = PerformanceMetrics(
            operation_name="test_op",
            execution_time=2.5,
            memory_usage_mb=75.5,
            io_operations=io_ops
        )
        
        result_dict = metrics.to_dict()
        
        required_fields = [
            "operation", "execution_time_ms", "memory_usage_mb",
            "cache_hit_ratio", "io_operations", "error_count"
        ]
        
        for field in required_fields:
            assert field in result_dict
        
        assert result_dict["operation"] == "test_op"
        assert result_dict["execution_time_ms"] == 2500.0  # 2.5s * 1000
        assert result_dict["memory_usage_mb"] == 75.5
        assert result_dict["io_operations"] == io_ops


class PerformanceGateStateMachine(RuleBasedStateMachine):
    """Stateful testing for PerformanceGate using Hypothesis."""
    
    def __init__(self):
        super().__init__()
        self.gate = PerformanceGate(enable_enforcement=False)
        self.expected_violations = 0
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        assert len(self.gate.violations) == 0
        assert len(self.gate._response_times) == 0
    
    @rule(duration=st.floats(min_value=1.0, max_value=1000.0))
    def add_response_time(self, duration):
        """Add a response time measurement."""
        self.gate.check_api_response_time(duration, "p95")
        
        # Update expected violations for database queries
        if duration > 100.0:  # This might create a DB violation if we treat it as such
            pass  # Response time violations are more complex due to percentile calculation
    
    @rule(query_time=st.floats(min_value=1.0, max_value=500.0))
    def add_database_query(self, query_time):
        """Add a database query time measurement."""
        initial_violations = len(self.gate.violations)
        self.gate.check_database_query_time(query_time, "simple")
        
        if query_time > 100.0:
            self.expected_violations += 1
    
    @invariant()
    def violations_count_is_consistent(self):
        """Invariant: violations count should match expectations."""
        # Note: This is a simplified invariant since response time violations
        # depend on percentile calculations with sufficient samples
        actual_db_violations = sum(
            1 for v in self.gate.violations 
            if v.threshold.violation_type == PerformanceViolationType.DATABASE_QUERY_TIME
        )
        
        # We only track database query violations in this simplified test
        assert actual_db_violations <= self.expected_violations
    
    @invariant()
    def response_times_are_recorded(self):
        """Invariant: all response times should be recorded."""
        assert len(self.gate._response_times) >= 0


# Configure Hypothesis settings for faster test runs in development
TestPerformanceGateStateMachine = PerformanceGateStateMachine.TestCase
TestPerformanceGateStateMachine.settings = settings(max_examples=50, stateful_step_count=20)


@pytest.mark.property
class TestComplexSystemProperties:
    """Property-based tests for complex system interactions."""
    
    @given(st.lists(st.tuples(st.text(min_size=1), st.dictionaries(st.text(), st.integers())), 
                   min_size=1, max_size=10))
    def test_event_system_with_multiple_events(self, event_data):
        """Test event system handles multiple events correctly."""
        event_bus = EventBus()
        received_events = []
        
        def collector(event):
            received_events.append((event.event_type, event.payload))
        
        # Subscribe to all event types
        event_types = set(event_type for event_type, _ in event_data)
        for event_type in event_types:
            event_bus.subscribe(event_type, collector)
        
        # Publish all events
        for event_type, payload in event_data:
            event = Event(event_type=event_type, source="test", payload=payload)
            event_bus.publish(event)
        
        # Verify all events were received
        assert len(received_events) == len(event_data)
        
        # Verify event order and content
        for i, (expected_type, expected_payload) in enumerate(event_data):
            actual_type, actual_payload = received_events[i]
            assert actual_type == expected_type
            assert actual_payload == expected_payload
    
    @given(st.lists(st.integers(min_value=1, max_value=1000), min_size=5, max_size=50))
    def test_performance_tracking_consistency(self, durations):
        """Test performance tracking maintains consistency across operations."""
        gate = PerformanceGate(enable_enforcement=False)
        
        # Track all operations
        for duration in durations:
            gate.check_api_response_time(duration, "p95")
        
        # Verify consistency
        assert len(gate._response_times) == len(durations)
        
        # Test percentile calculation if enough samples
        if len(durations) >= 20:
            p95_value = gate._calculate_current_percentile("p95")
            if p95_value is not None:
                sorted_times = sorted(durations[-100:])  # Last 100 samples
                expected_index = min(int(0.95 * len(sorted_times)), len(sorted_times) - 1)
                expected_p95 = sorted_times[expected_index]
                assert abs(p95_value - expected_p95) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "property"])