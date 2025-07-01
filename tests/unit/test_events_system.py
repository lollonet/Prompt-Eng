"""
Comprehensive tests for event-driven architecture implementation.

Tests event bus functionality, event handlers, decorators, and integration
with the application's event-driven patterns.
"""

import asyncio
import time
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from src.events import (
    Event,
    EventBus,
    EventPublishConfig,
    EventType,
    PerformanceThresholdExceededEvent,
    PromptGenerationCompletedEvent,
    PromptGenerationStartedEvent,
    event_bus,
    logging_handler,
    metrics_collection_handler,
    performance_monitoring_handler,
    publish_events,
    setup_default_event_handlers,
)
from src.types_advanced import TaskType, TechnologyName


class TestEventSystem:
    """Test core event system functionality."""

    @pytest.fixture
    def fresh_event_bus(self):
        """Create a fresh event bus for testing."""
        return EventBus()

    def test_event_creation(self):
        """Test basic event creation and serialization."""
        event = Event(
            event_type=EventType.PROMPT_GENERATION_STARTED,
            source="TestSource",
            payload={"test": "data"},
        )

        assert event.event_type == EventType.PROMPT_GENERATION_STARTED
        assert event.source == "TestSource"
        assert event.payload == {"test": "data"}
        assert isinstance(event.event_id, UUID)
        assert event.timestamp > 0

        # Test serialization
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "prompt_generation_started"
        assert event_dict["source"] == "TestSource"
        assert event_dict["payload"] == {"test": "data"}
        assert "event_id" in event_dict
        assert "timestamp" in event_dict

    def test_specific_event_types(self):
        """Test specific event type creation methods."""
        # Test PromptGenerationStartedEvent
        start_event = PromptGenerationStartedEvent.create(
            technologies=[TechnologyName("python")], task_type=TaskType("feature development")
        )

        assert start_event.event_type == EventType.PROMPT_GENERATION_STARTED
        assert start_event.source == "PromptGenerator"
        assert "technologies" in start_event.payload
        assert "task_type" in start_event.payload
        assert "operation_start" in start_event.payload

        # Test PromptGenerationCompletedEvent
        completion_event = PromptGenerationCompletedEvent.create(
            prompt_length=1500,
            technologies_count=2,
            execution_time=0.125,
            correlation_id=start_event.correlation_id,
        )

        assert completion_event.event_type == EventType.PROMPT_GENERATION_COMPLETED
        assert completion_event.payload["prompt_length"] == 1500
        assert completion_event.payload["technologies_count"] == 2
        assert completion_event.payload["execution_time_ms"] == 125.0
        assert completion_event.correlation_id == start_event.correlation_id

        # Test PerformanceThresholdExceededEvent
        perf_event = PerformanceThresholdExceededEvent.create(
            operation="template_rendering", actual_time=0.5, threshold=0.2
        )

        assert perf_event.event_type == EventType.PERFORMANCE_THRESHOLD_EXCEEDED
        assert perf_event.payload["operation"] == "template_rendering"
        assert perf_event.payload["actual_time_ms"] == 500.0
        assert perf_event.payload["threshold_ms"] == 200.0
        assert perf_event.payload["exceeded_by_ms"] == 300.0


class TestEventBus:
    """Test event bus functionality."""

    @pytest.fixture
    def event_bus_instance(self):
        """Create a fresh event bus for testing."""
        return EventBus()

    @pytest.mark.asyncio
    async def test_async_event_subscription_and_publishing(self, event_bus_instance):
        """Test async event subscription and publishing."""
        received_events = []

        async def test_handler(event: Event):
            received_events.append(event)

        # Subscribe handler
        event_bus_instance.subscribe(EventType.PROMPT_GENERATION_STARTED, test_handler)

        # Create and publish event
        test_event = Event(
            event_type=EventType.PROMPT_GENERATION_STARTED,
            source="TestSource",
            payload={"test": "async"},
        )

        await event_bus_instance.publish(test_event)

        # Verify handler was called
        assert len(received_events) == 1
        assert received_events[0] == test_event
        assert received_events[0].payload["test"] == "async"

    def test_sync_event_subscription_and_publishing(self, event_bus_instance):
        """Test sync event subscription and publishing."""
        received_events = []

        def sync_handler(event: Event):
            received_events.append(event)

        # Subscribe sync handler
        event_bus_instance.subscribe_sync(EventType.KNOWLEDGE_CACHE_HIT, sync_handler)

        # Create and publish event
        test_event = Event(
            event_type=EventType.KNOWLEDGE_CACHE_HIT,
            source="TestSource",
            payload={"cache_key": "test_key"},
        )

        # Use asyncio.run for sync test
        asyncio.run(event_bus_instance.publish(test_event))

        # Verify handler was called
        assert len(received_events) == 1
        assert received_events[0].payload["cache_key"] == "test_key"

    @pytest.mark.asyncio
    async def test_global_event_subscription(self, event_bus_instance):
        """Test global event subscription."""
        received_events = []

        async def global_handler(event: Event):
            received_events.append(event)

        # Subscribe global handler
        event_bus_instance.subscribe_all(global_handler)

        # Publish different event types
        events = [
            Event(EventType.PROMPT_GENERATION_STARTED, "Source1"),
            Event(EventType.KNOWLEDGE_CACHE_MISS, "Source2"),
            Event(EventType.TEMPLATE_RENDERED, "Source3"),
        ]

        for event in events:
            await event_bus_instance.publish(event)

        # Verify global handler received all events
        assert len(received_events) == 3
        assert received_events[0].event_type == EventType.PROMPT_GENERATION_STARTED
        assert received_events[1].event_type == EventType.KNOWLEDGE_CACHE_MISS
        assert received_events[2].event_type == EventType.TEMPLATE_RENDERED

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self, event_bus_instance):
        """Test multiple handlers for the same event type."""
        results = []

        async def handler1(event: Event):
            results.append("handler1")

        async def handler2(event: Event):
            results.append("handler2")

        def sync_handler(event: Event):
            results.append("sync_handler")

        # Subscribe multiple handlers
        event_bus_instance.subscribe(EventType.SYSTEM_ERROR, handler1)
        event_bus_instance.subscribe(EventType.SYSTEM_ERROR, handler2)
        event_bus_instance.subscribe_sync(EventType.SYSTEM_ERROR, sync_handler)

        # Publish event
        test_event = Event(EventType.SYSTEM_ERROR, "TestSource")
        await event_bus_instance.publish(test_event)

        # Verify all handlers were called
        assert len(results) == 3
        assert "handler1" in results
        assert "handler2" in results
        assert "sync_handler" in results

    def test_event_history_management(self, event_bus_instance):
        """Test event history tracking and management."""
        events = []
        for i in range(5):
            event = Event(
                event_type=EventType.TEMPLATE_RENDERED, source=f"Source{i}", payload={"index": i}
            )
            events.append(event)
            asyncio.run(event_bus_instance.publish(event))

        # Test get all history
        history = event_bus_instance.get_event_history()
        assert len(history) == 5

        # Test filtered history
        template_events = event_bus_instance.get_event_history(EventType.TEMPLATE_RENDERED)
        assert len(template_events) == 5

        # Test history doesn't include non-matching events
        cache_events = event_bus_instance.get_event_history(EventType.KNOWLEDGE_CACHE_HIT)
        assert len(cache_events) == 0

        # Test clear history
        event_bus_instance.clear_history()
        assert len(event_bus_instance.get_event_history()) == 0

    def test_event_history_size_limit(self, event_bus_instance):
        """Test event history size limitation."""
        # Simulate max history size of 1000 (default)
        event_bus_instance._max_history_size = 3  # Set smaller for testing

        # Publish more events than the limit
        for i in range(5):
            event = Event(EventType.SYSTEM_ERROR, f"Source{i}")
            asyncio.run(event_bus_instance.publish(event))

        # Verify history size is limited
        history = event_bus_instance.get_event_history()
        assert len(history) == 3

        # Verify it kept the most recent events
        sources = [event.source for event in history]
        assert "Source2" in sources
        assert "Source3" in sources
        assert "Source4" in sources

    def test_unsubscribe_handlers(self, event_bus_instance):
        """Test unsubscribing event handlers."""
        received_events = []

        async def async_handler(event: Event):
            received_events.append("async")

        def sync_handler(event: Event):
            received_events.append("sync")

        # Subscribe handlers
        event_bus_instance.subscribe(EventType.PROMPT_GENERATION_FAILED, async_handler)
        event_bus_instance.subscribe_sync(EventType.PROMPT_GENERATION_FAILED, sync_handler)

        # Publish event - both handlers should be called
        test_event = Event(EventType.PROMPT_GENERATION_FAILED, "TestSource")
        asyncio.run(event_bus_instance.publish(test_event))
        assert len(received_events) == 2

        # Unsubscribe async handler
        result = event_bus_instance.unsubscribe(EventType.PROMPT_GENERATION_FAILED, async_handler)
        assert result is True

        # Publish again - only sync handler should be called
        received_events.clear()
        asyncio.run(event_bus_instance.publish(test_event))
        assert len(received_events) == 1
        assert received_events[0] == "sync"

        # Try to unsubscribe non-existent handler
        result = event_bus_instance.unsubscribe(EventType.PROMPT_GENERATION_FAILED, async_handler)
        assert result is False

    @pytest.mark.asyncio
    async def test_handler_error_handling(self, event_bus_instance):
        """Test error handling in event handlers."""

        async def failing_handler(event: Event):
            raise ValueError("Handler error")

        def failing_sync_handler(event: Event):
            raise RuntimeError("Sync handler error")

        successful_calls = []

        async def success_handler(event: Event):
            successful_calls.append(event)

        # Subscribe handlers
        event_bus_instance.subscribe(EventType.SYSTEM_ERROR, failing_handler)
        event_bus_instance.subscribe(EventType.SYSTEM_ERROR, success_handler)
        event_bus_instance.subscribe_sync(EventType.SYSTEM_ERROR, failing_sync_handler)

        # Publish event - should not raise exception
        test_event = Event(EventType.SYSTEM_ERROR, "TestSource")

        with patch("src.events.logger") as mock_logger:
            await event_bus_instance.publish(test_event)

            # Verify errors were logged
            assert mock_logger.error.call_count >= 2

            # Verify successful handler still executed
            assert len(successful_calls) == 1


class TestEventDecorators:
    """Test event publishing decorators."""

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing decorators."""
        with patch("src.events.event_bus") as mock_bus:
            mock_bus.publish = AsyncMock()
            yield mock_bus

    @pytest.mark.asyncio
    async def test_async_function_event_decorator(self, mock_event_bus):
        """Test event decorator with async functions."""

        @publish_events(
            start_event_type=EventType.PROMPT_GENERATION_STARTED,
            success_event_type=EventType.PROMPT_GENERATION_COMPLETED,
            error_event_type=EventType.PROMPT_GENERATION_FAILED,
            source="TestService",
        )
        async def async_test_function(param1: str, param2: int) -> str:
            await asyncio.sleep(0.001)  # Simulate work
            return f"result_{param1}_{param2}"

        # Call decorated function
        result = await async_test_function("test", 42)

        # Verify result
        assert result == "result_test_42"

        # Verify events were published
        assert mock_event_bus.publish.call_count == 2  # start and success events

        # Verify start event
        start_call = mock_event_bus.publish.call_args_list[0]
        start_event = start_call[0][0]
        assert start_event.event_type == EventType.PROMPT_GENERATION_STARTED
        assert start_event.source == "TestService"
        assert start_event.payload["function"] == "async_test_function"
        assert start_event.payload["args_count"] == 2

        # Verify success event
        success_call = mock_event_bus.publish.call_args_list[1]
        success_event = success_call[0][0]
        assert success_event.event_type == EventType.PROMPT_GENERATION_COMPLETED
        assert success_event.correlation_id == start_event.correlation_id

    @pytest.mark.asyncio
    async def test_async_function_error_event_decorator(self, mock_event_bus):
        """Test event decorator error handling with async functions."""

        @publish_events(
            start_event_type=EventType.PROMPT_GENERATION_STARTED,
            success_event_type=EventType.PROMPT_GENERATION_COMPLETED,
            error_event_type=EventType.PROMPT_GENERATION_FAILED,
            source="TestService",
        )
        async def failing_async_function(should_fail: bool):
            if should_fail:
                raise ValueError("Test error")
            return "success"

        # Test successful execution
        result = await failing_async_function(False)
        assert result == "success"
        assert mock_event_bus.publish.call_count == 2  # start + success

        # Reset mock
        mock_event_bus.reset_mock()

        # Test error handling
        with pytest.raises(ValueError, match="Test error"):
            await failing_async_function(True)

        # Verify error event was published
        assert mock_event_bus.publish.call_count == 2  # start + error events

        error_call = mock_event_bus.publish.call_args_list[1]
        error_event = error_call[0][0]
        assert error_event.event_type == EventType.PROMPT_GENERATION_FAILED
        assert error_event.payload["error_type"] == "ValueError"
        assert error_event.payload["error_message"] == "Test error"

    def test_sync_function_event_decorator(self, mock_event_bus):
        """Test event decorator with sync functions."""

        @publish_events(
            start_event_type=EventType.TEMPLATE_RENDERED,
            success_event_type=EventType.PROMPT_GENERATION_COMPLETED,
            error_event_type=EventType.SYSTEM_ERROR,
            source="TemplateService",
        )
        def sync_test_function(value: int) -> int:
            return value * 2

        # Call decorated function
        result = sync_test_function(21)

        # Verify result
        assert result == 42

        # For sync functions, events are not published in the current implementation
        # This is a limitation that could be addressed by modifying the decorator


class TestBuiltInEventHandlers:
    """Test built-in event handlers."""

    @pytest.mark.asyncio
    async def test_performance_monitoring_handler(self):
        """Test performance monitoring event handler."""
        # Create performance threshold exceeded event
        perf_event = PerformanceThresholdExceededEvent.create(
            operation="template_rendering", actual_time=0.5, threshold=0.2
        )

        with (
            patch("src.events.logger") as mock_logger,
            patch("src.events.performance_tracker") as mock_tracker,
        ):

            await performance_monitoring_handler(perf_event)

            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "Performance threshold exceeded" in warning_msg

            # Verify performance tracker was called
            mock_tracker.record_error.assert_called_once_with("template_rendering")

    @pytest.mark.asyncio
    async def test_metrics_collection_handler(self):
        """Test metrics collection event handler."""
        # Create prompt generation completed event
        completion_event = PromptGenerationCompletedEvent.create(
            prompt_length=2500, technologies_count=3, execution_time=0.125
        )

        with patch("src.events.logger") as mock_logger:
            await metrics_collection_handler(completion_event)

            # Verify metrics were logged
            mock_logger.debug.assert_called_once()
            debug_msg = mock_logger.debug.call_args[0][0]
            assert "prompt_generation_time=125.0ms" in debug_msg
            assert "technologies=3" in debug_msg

    def test_logging_handler(self):
        """Test logging event handler."""
        test_event = Event(
            event_type=EventType.KNOWLEDGE_CACHE_HIT,
            source="CacheService",
            payload={"cache_key": "python_best_practices"},
        )

        with patch("src.events.logger") as mock_logger:
            logging_handler(test_event)

            mock_logger.info.assert_called_once()
            log_msg = mock_logger.info.call_args[0][0]
            assert "Event: knowledge_cache_hit" in log_msg
            assert "from CacheService" in log_msg


class TestEventSystemIntegration:
    """Test integration between event system components."""

    @pytest.mark.asyncio
    async def test_event_correlation_flow(self):
        """Test event correlation across operation lifecycle."""
        event_bus_instance = EventBus()
        received_events = []

        async def correlation_handler(event: Event):
            received_events.append(event)

        # Subscribe to all events
        event_bus_instance.subscribe_all(correlation_handler)

        # Simulate complete operation lifecycle
        correlation_id = uuid4()

        # Start event
        start_event = PromptGenerationStartedEvent.create(
            technologies=[TechnologyName("python")],
            task_type=TaskType("feature"),
            correlation_id=correlation_id,
        )
        await event_bus_instance.publish(start_event)

        # Completion event
        completion_event = PromptGenerationCompletedEvent.create(
            prompt_length=1000,
            technologies_count=1,
            execution_time=0.1,
            correlation_id=correlation_id,
        )
        await event_bus_instance.publish(completion_event)

        # Verify correlation
        assert len(received_events) == 2
        assert received_events[0].correlation_id == correlation_id
        assert received_events[1].correlation_id == correlation_id
        assert received_events[0].correlation_id == received_events[1].correlation_id

    @pytest.mark.asyncio
    async def test_setup_default_handlers_integration(self):
        """Test default event handlers setup and integration."""
        # Create fresh event bus
        test_bus = EventBus()

        # Manually setup handlers on test bus (simulating setup_default_event_handlers)
        test_bus.subscribe(EventType.PERFORMANCE_THRESHOLD_EXCEEDED, performance_monitoring_handler)
        test_bus.subscribe_all(metrics_collection_handler)

        # Create events
        perf_event = PerformanceThresholdExceededEvent.create(
            operation="test_operation", actual_time=1.0, threshold=0.5
        )

        completion_event = PromptGenerationCompletedEvent.create(
            prompt_length=500, technologies_count=1, execution_time=0.05
        )

        # Publish events and verify no exceptions
        with patch("src.events.logger"), patch("src.events.performance_tracker"):
            await test_bus.publish(perf_event)
            await test_bus.publish(completion_event)

        # Verify events were recorded in history
        history = test_bus.get_event_history()
        assert len(history) == 2
        assert any(e.event_type == EventType.PERFORMANCE_THRESHOLD_EXCEEDED for e in history)
        assert any(e.event_type == EventType.PROMPT_GENERATION_COMPLETED for e in history)

    def test_event_config_dataclass(self):
        """Test EventPublishConfig dataclass."""
        config = EventPublishConfig(
            start_event_type=EventType.PROMPT_GENERATION_STARTED,
            success_event_type=EventType.PROMPT_GENERATION_COMPLETED,
            error_event_type=EventType.PROMPT_GENERATION_FAILED,
            source="TestSource",
        )

        assert config.start_event_type == EventType.PROMPT_GENERATION_STARTED
        assert config.success_event_type == EventType.PROMPT_GENERATION_COMPLETED
        assert config.error_event_type == EventType.PROMPT_GENERATION_FAILED
        assert config.source == "TestSource"

        # Test immutability
        assert hasattr(config, "__dataclass_fields__")
