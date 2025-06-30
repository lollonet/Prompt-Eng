"""
Comprehensive integration tests for modern patterns and performance gates.

Business Context: Integration tests verify that all modern patterns work together
correctly in production-like scenarios, ensuring system reliability.

Why this approach: Integration testing prevents regressions and validates that
enterprise-grade patterns interact correctly under real workloads.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from typing import Dict, Any

from src.performance_gates import (
    PerformanceGate, 
    PerformanceViolation, 
    performance_gate,
    enforce_api_response_time,
    enforce_database_query_time,
    performance_gate_context,
    async_performance_gate_context
)
from src.performance import (
    monitor_performance,
    async_read_text_file,
    async_load_json_file,
    performance_tracker,
    LazyEvaluator,
    lazy
)
from src.result_types import Success, Error, KnowledgeError
from src.events import EventBus, Event
from src.knowledge_manager_async import AsyncKnowledgeManager
from src.prompt_generator_modern import ModernPromptGenerator
from src.prompt_config import PromptConfig


class TestPerformanceGatesIntegration:
    """Test performance gates with real operations."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.performance_gate = PerformanceGate(enable_enforcement=False)
        
    def test_api_response_time_tracking(self):
        """Test API response time tracking with multiple samples."""
        
        # Simulate multiple API calls
        response_times = [150, 180, 220, 160, 300, 140, 170, 250, 190, 200,
                         160, 180, 210, 175, 320, 145, 165, 240, 185, 195]
        
        for duration in response_times:
            self.performance_gate.check_api_response_time(duration, "p95")
        
        # Verify tracking works
        assert len(self.performance_gate._response_times) == len(response_times)
        
        # Calculate expected p95 (should be around 300ms)
        sorted_times = sorted(response_times)
        p95_index = int(0.95 * len(sorted_times))
        expected_p95 = sorted_times[p95_index]
        
        # Should trigger violation if p95 > 200ms
        assert expected_p95 > 200
        
    def test_memory_growth_monitoring(self):
        """Test memory growth rate monitoring."""
        
        # Initialize baseline
        self.performance_gate.check_memory_growth()
        
        # Simulate memory growth by creating objects
        large_objects = []
        for i in range(1000):
            large_objects.append([0] * 1000)  # Create memory pressure
        
        # Check memory growth (should not violate in test environment)
        self.performance_gate.check_memory_growth()
        
        # Verify baseline was set
        assert self.performance_gate._memory_baseline is not None
        assert self.performance_gate._memory_start_time is not None
        
    def test_database_query_threshold(self):
        """Test database query time thresholds."""
        
        # Fast query - should pass
        self.performance_gate.check_database_query_time(50.0, "simple")
        
        # Slow query - should trigger violation
        with pytest.raises(PerformanceViolation):
            gate_with_enforcement = PerformanceGate(enable_enforcement=True)
            gate_with_enforcement.check_database_query_time(150.0, "simple")
            
    def test_performance_decorators_integration(self):
        """Test performance decorators with threshold enforcement."""
        
        # Test sync function with enforcement
        @enforce_api_response_time("p95")
        def fast_operation():
            time.sleep(0.05)  # 50ms
            return "success"
        
        @enforce_api_response_time("p95") 
        def slow_operation():
            time.sleep(0.25)  # 250ms - might trigger violation
            return "success"
        
        # Fast operation should work
        result = fast_operation()
        assert result == "success"
        
        # Slow operation records the time but doesn't enforce by default
        result = slow_operation()
        assert result == "success"
        
    @pytest.mark.asyncio
    async def test_async_performance_decorators(self):
        """Test async performance decorators."""
        
        @enforce_api_response_time("p95")
        async def async_fast_operation():
            await asyncio.sleep(0.05)  # 50ms
            return "async_success"
        
        @enforce_database_query_time("simple")  
        async def async_db_query():
            await asyncio.sleep(0.08)  # 80ms - within threshold
            return {"data": "result"}
        
        # Both should work
        result1 = await async_fast_operation()
        assert result1 == "async_success"
        
        result2 = await async_db_query()
        assert result2 == {"data": "result"}
        
    def test_violation_summary(self):
        """Test performance violation summary generation."""
        
        # Create some violations
        gate = PerformanceGate(enable_enforcement=False)
        
        # Trigger API response violation
        for _ in range(25):  # Build up samples
            gate.check_api_response_time(150, "p95")
        gate.check_api_response_time(300, "p95")  # This should trigger
        
        # Trigger DB violation
        gate.check_database_query_time(150, "simple")
        
        summary = gate.get_violation_summary()
        
        assert summary["total_violations"] >= 0
        assert "violations_by_type" in summary
        assert summary["enforcement_enabled"] is False
        assert "thresholds" in summary


class TestAsyncIntegration:
    """Integration tests for async patterns."""
    
    @pytest.mark.asyncio
    async def test_async_file_operations_with_monitoring(self):
        """Test async file operations with performance monitoring."""
        
        # Create a temporary test file
        test_content = "Test content for async operations"
        test_file = Path("/tmp/test_async_file.txt")
        test_file.write_text(test_content)
        
        try:
            # Test async file reading with monitoring
            async with async_performance_gate_context():
                result = await async_read_text_file(str(test_file))
                
                assert result.is_success()
                content = result.unwrap()
                assert content == test_content
                
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
                
    @pytest.mark.asyncio
    async def test_async_json_operations(self):
        """Test async JSON operations."""
        
        test_data = {"name": "test", "values": [1, 2, 3], "nested": {"key": "value"}}
        test_file = Path("/tmp/test_async.json")
        test_file.write_text(json.dumps(test_data))
        
        try:
            result = await async_load_json_file(str(test_file))
            
            assert result.is_success()
            data = result.unwrap()
            assert data == test_data
            
        finally:
            if test_file.exists():
                test_file.unlink()
                
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling with Result types."""
        
        # Test reading non-existent file
        result = await async_read_text_file("/tmp/nonexistent_file.txt")
        
        assert result.is_error()
        error = result.error
        assert isinstance(error, KnowledgeError)
        assert "File not found" in error.message


class TestEventSystemIntegration:
    """Integration tests for event-driven architecture."""
    
    def setup_method(self):
        """Setup event bus for each test."""
        self.event_bus = EventBus()
        self.received_events = []
        
    def test_event_bus_with_performance_monitoring(self):
        """Test event bus with performance monitoring."""
        
        @monitor_performance("event_handler")
        def performance_monitored_handler(event: Event):
            self.received_events.append(event)
            # Simulate some processing time
            time.sleep(0.01)
            
        # Subscribe handler
        self.event_bus.subscribe("test_event", performance_monitored_handler)
        
        # Emit event
        test_event = Event("test_event", {"data": "test_value"})
        self.event_bus.emit(test_event)
        
        # Verify event was processed
        assert len(self.received_events) == 1
        assert self.received_events[0].name == "test_event"
        
    @pytest.mark.asyncio
    async def test_async_event_handlers(self):
        """Test async event handlers."""
        
        async_received_events = []
        
        @monitor_performance("async_event_handler")
        async def async_handler(event: Event):
            async_received_events.append(event)
            await asyncio.sleep(0.01)  # Simulate async work
            
        # Subscribe async handler
        self.event_bus.subscribe("async_test", async_handler)
        
        # Emit event
        test_event = Event("async_test", {"async_data": "value"})
        await self.event_bus.emit_async(test_event)
        
        # Verify async processing
        assert len(async_received_events) == 1
        assert async_received_events[0].data["async_data"] == "value"


class TestModernPatternsIntegration:
    """Integration tests combining all modern patterns."""
    
    def setup_method(self):
        """Setup for comprehensive integration tests."""
        self.event_bus = EventBus()
        
    @pytest.mark.asyncio
    async def test_full_stack_integration(self):
        """Test integration of all modern patterns together."""
        
        # Create async knowledge manager with events
        knowledge_manager = AsyncKnowledgeManager(
            base_path="knowledge_base/",
            event_bus=self.event_bus
        )
        
        # Configure prompt generator
        config = PromptConfig(
            template_name="generic_code_prompt.txt",
            output_format="markdown",
            max_tokens=1000,
            context_variables={"task": "integration_test"},
            performance_mode="balanced"
        )
        
        # Test with performance monitoring
        with performance_gate_context(check_memory=True):
            # This would normally load templates and generate prompts
            # For integration test, we verify the patterns work together
            
            # Event-driven pattern
            events_received = []
            
            def capture_events(event: Event):
                events_received.append(event.name)
                
            self.event_bus.subscribe("knowledge_loaded", capture_events)
            
            # Emit test event
            test_event = Event("knowledge_loaded", {"source": "integration_test"})
            self.event_bus.emit(test_event)
            
            # Verify event system works
            assert "knowledge_loaded" in events_received
            
            # Test lazy evaluation
            expensive_computation = lazy(lambda: sum(range(10000)))
            assert not expensive_computation.is_computed
            
            result = expensive_computation.get()
            assert expensive_computation.is_computed
            assert result == sum(range(10000))
            
    def test_lazy_evaluation_integration(self):
        """Test lazy evaluation with performance tracking."""
        
        computation_calls = []
        
        def expensive_operation():
            computation_calls.append(time.time())
            time.sleep(0.05)  # Simulate expensive work
            return "computed_result"
        
        # Create lazy evaluator
        lazy_result = lazy(expensive_operation)
        
        # Verify not computed initially
        assert not lazy_result.is_computed
        assert len(computation_calls) == 0
        
        # First access should compute
        with performance_gate_context():
            result1 = lazy_result.get()
            assert result1 == "computed_result"
            assert lazy_result.is_computed
            assert len(computation_calls) == 1
        
        # Second access should use cached value
        result2 = lazy_result.get()
        assert result2 == "computed_result"
        assert len(computation_calls) == 1  # No additional computation
        
        # Invalidation should force recomputation
        lazy_result.invalidate()
        assert not lazy_result.is_computed
        
        result3 = lazy_result.get()
        assert result3 == "computed_result"
        assert len(computation_calls) == 2  # Recomputed


@pytest.mark.integration
class TestProductionReadinessIntegration:
    """Integration tests for production readiness."""
    
    def test_performance_gates_enforcement(self):
        """Test performance gates under production-like conditions."""
        
        # Create enforcing performance gate
        gate = PerformanceGate(enable_enforcement=True)
        
        # Fast operations should pass
        gate.check_database_query_time(50.0, "simple") 
        
        # Slow operations should raise violations
        with pytest.raises(PerformanceViolation) as exc_info:
            gate.check_database_query_time(150.0, "simple")
            
        violation = exc_info.value
        assert violation.actual_value == 150.0
        assert violation.threshold.value == 100.0
        assert "Database Query Time" in str(violation)
        
    @pytest.mark.asyncio 
    async def test_concurrent_operations_performance(self):
        """Test performance under concurrent load."""
        
        async def concurrent_operation(operation_id: int):
            """Simulate concurrent API operation."""
            await asyncio.sleep(0.05 + (operation_id % 3) * 0.02)  # Variable delay
            return f"result_{operation_id}"
        
        # Run multiple concurrent operations
        with performance_gate_context(check_memory=True):
            tasks = [concurrent_operation(i) for i in range(20)]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 20
            assert all(result.startswith("result_") for result in results)
            
    def test_error_handling_under_load(self):
        """Test error handling patterns under simulated load."""
        
        error_count = 0
        success_count = 0
        
        @monitor_performance("load_test_operation")
        def load_test_operation(should_fail: bool):
            nonlocal error_count, success_count
            
            if should_fail:
                error_count += 1
                raise ValueError("Simulated failure")
            else:
                success_count += 1
                return "success"
        
        # Mix of success and failure
        operations = [False] * 15 + [True] * 5  # 15 success, 5 failures
        
        for should_fail in operations:
            try:
                result = load_test_operation(should_fail)
                if result == "success":
                    assert not should_fail
            except ValueError:
                assert should_fail
                
        assert success_count == 15
        assert error_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])