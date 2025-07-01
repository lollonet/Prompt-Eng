"""
Comprehensive tests for event-driven architecture system.

Tests event publishing, subscription, async handling, and all event patterns
to ensure reliable event-driven behavior.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from src.events import (
    Event,
    EventBus,
    EventHandler,
    EventPublishConfig,
    EventType,
    SyncEventHandler,
    event_bus,
    publish_events,
)


class TestEvent:
    """Test Event dataclass and basic functionality."""

    def test_event_creation_minimal(self):
        """Test event creation with minimal required fields."""
        event = Event(event_type=EventType.PROMPT_GENERATION_STARTED, source="test_source")

        assert event.event_type == EventType.PROMPT_GENERATION_STARTED
        assert event.source == "test_source"
        assert event.payload == {}
        assert isinstance(event.event_id, UUID)
        assert event.correlation_id is None
        assert event.timestamp > 0

    def test_event_creation_full(self):
        """Test event creation with all fields."""
        correlation_id = uuid4()
        payload = {"key": "value", "number": 42}

        event = Event(
            event_type="full_event",
            source="test_source",
            payload=payload,
            correlation_id=correlation_id,
        )

        assert event.event_type == "full_event"
        assert event.source == "test_source"
        assert event.payload == payload
        assert event.correlation_id == correlation_id
        assert isinstance(event.event_id, UUID)

    def test_event_immutability(self):
        """Test that events are immutable."""
        event = Event(event_type="test", source="source")

        with pytest.raises(AttributeError):
            event.event_type = "modified"

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        correlation_id = uuid4()
        event = Event(
            event_type=EventType.PROMPT_GENERATION_STARTED,
            source="test_source",
            payload={"data": "value"},
            correlation_id=correlation_id,
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "prompt_generation_started"
        assert event_dict["source"] == "test_source"
        assert event_dict["payload"] == {"data": "value"}
        assert event_dict["correlation_id"] == str(correlation_id)
        assert "event_id" in event_dict
        assert "timestamp" in event_dict


class TestEventBus:
    """Test EventBus functionality."""

    def setup_method(self):
        """Setup fresh event bus for each test."""
        self.event_bus = EventBus()
        self.received_events = []

    def test_event_bus_initialization(self):
        """Test event bus initialization."""
        bus = EventBus()
        assert bus._handlers == {}
        assert bus._sync_handlers == {}
        assert bus._global_handlers == []
        assert bus._event_history == []
        assert bus._max_history_size == 1000

    @pytest.mark.asyncio
    async def test_sync_event_subscription_and_publishing(self):
        """Test synchronous event subscription and publishing."""

        async def test_handler(event: Event):
            self.received_events.append(event)

        # Subscribe handler
        self.event_bus.subscribe(EventType.PROMPT_GENERATION_STARTED, test_handler)

        # Publish event
        test_event = Event(event_type=EventType.PROMPT_GENERATION_STARTED, source="test_source", payload={"data": "test"})
        await self.event_bus.publish(test_event)

        # Verify event was received
        assert len(self.received_events) == 1
        assert self.received_events[0].event_type == EventType.PROMPT_GENERATION_STARTED
        assert self.received_events[0].payload["data"] == "test"

    @pytest.mark.asyncio
    async def test_async_event_subscription_and_publishing(self):
        """Test asynchronous event subscription and publishing."""

        async def async_handler(event: Event):
            self.received_events.append(event)

        # Subscribe async handler
        self.event_bus.subscribe("async_event", async_handler)

        # Publish event asynchronously
        test_event = Event("async_event", "test_source", {"data": "async_test"})
        await self.event_bus.publish_async(test_event)

        # Verify event was received
        assert len(self.received_events) == 1
        assert self.received_events[0].event_type == "async_event"
        assert self.received_events[0].payload["data"] == "async_test"

    def test_multiple_handlers_same_event(self):
        """Test multiple handlers for the same event type."""
        handler1_calls = []
        handler2_calls = []

        def handler1(event: Event):
            handler1_calls.append(event)

        def handler2(event: Event):
            handler2_calls.append(event)

        # Subscribe both handlers
        self.event_bus.subscribe("multi_event", handler1)
        self.event_bus.subscribe("multi_event", handler2)

        # Publish event
        test_event = Event("multi_event", "test_source")
        self.event_bus.publish(test_event)

        # Both handlers should receive the event
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    def test_event_unsubscription(self):
        """Test event handler unsubscription."""

        def test_handler(event: Event):
            self.received_events.append(event)

        # Subscribe and then unsubscribe
        self.event_bus.subscribe("unsub_event", test_handler)
        success = self.event_bus.unsubscribe("unsub_event", test_handler)

        assert success is True

        # Publish event - should not be received
        test_event = Event("unsub_event", "test_source")
        self.event_bus.publish(test_event)

        assert len(self.received_events) == 0

    def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing nonexistent handler."""

        def test_handler(event: Event):
            pass

        success = self.event_bus.unsubscribe("nonexistent", test_handler)
        assert success is False

    def test_event_handler_exception_handling(self):
        """Test exception handling in event handlers."""

        def failing_handler(event: Event):
            raise ValueError("Handler failed")

        def working_handler(event: Event):
            self.received_events.append(event)

        # Subscribe both handlers
        self.event_bus.subscribe("error_event", failing_handler)
        self.event_bus.subscribe("error_event", working_handler)

        # Publish event - working handler should still receive it
        test_event = Event("error_event", "test_source")

        with patch("src.events.logger") as mock_logger:
            self.event_bus.publish(test_event)

            # Verify error was logged
            mock_logger.error.assert_called()

        # Working handler should still have received the event
        assert len(self.received_events) == 1

    @pytest.mark.asyncio
    async def test_async_handler_exception_handling(self):
        """Test exception handling in async event handlers."""

        async def failing_async_handler(event: Event):
            raise ValueError("Async handler failed")

        async def working_async_handler(event: Event):
            self.received_events.append(event)

        # Subscribe both handlers
        self.event_bus.subscribe("async_error_event", failing_async_handler)
        self.event_bus.subscribe("async_error_event", working_async_handler)

        # Publish event
        test_event = Event("async_error_event", "test_source")

        with patch("src.events.logger") as mock_logger:
            await self.event_bus.publish_async(test_event)

            # Verify error was logged
            mock_logger.error.assert_called()

        # Working handler should still have received the event
        assert len(self.received_events) == 1

    def test_event_metrics_collection(self):
        """Test event metrics are collected properly."""

        def test_handler(event: Event):
            pass

        self.event_bus.subscribe("metric_event", test_handler)

        # Publish multiple events
        for i in range(5):
            event = Event("metric_event", "test_source", {"index": i})
            self.event_bus.publish(event)

        metrics = self.event_bus.get_metrics()

        assert metrics["total_events_published"] == 5
        assert "metric_event" in metrics["events_by_type"]
        assert metrics["events_by_type"]["metric_event"] == 5
        assert "metric_event" in metrics["handler_counts"]
        assert metrics["handler_counts"]["metric_event"] == 1


class TestEventMiddleware:
    """Test event middleware functionality."""

    def setup_method(self):
        """Setup event bus and tracking."""
        self.event_bus = EventBus()
        self.middleware_calls = []
        self.received_events = []

    def test_middleware_execution_order(self):
        """Test middleware executes in correct order."""

        def middleware1(event: Event, next_handler):
            self.middleware_calls.append("middleware1_before")
            result = next_handler(event)
            self.middleware_calls.append("middleware1_after")
            return result

        def middleware2(event: Event, next_handler):
            self.middleware_calls.append("middleware2_before")
            result = next_handler(event)
            self.middleware_calls.append("middleware2_after")
            return result

        def handler(event: Event):
            self.middleware_calls.append("handler")
            self.received_events.append(event)

        # Add middleware in order
        self.event_bus.add_middleware(middleware1)
        self.event_bus.add_middleware(middleware2)
        self.event_bus.subscribe("middleware_test", handler)

        # Publish event
        test_event = Event("middleware_test", "test_source")
        self.event_bus.publish(test_event)

        # Verify execution order
        expected_order = [
            "middleware1_before",
            "middleware2_before",
            "handler",
            "middleware2_after",
            "middleware1_after",
        ]
        assert self.middleware_calls == expected_order
        assert len(self.received_events) == 1

    def test_middleware_event_modification(self):
        """Test middleware can modify events."""

        def enrichment_middleware(event: Event, next_handler):
            # Add metadata to event
            enriched_payload = {**event.payload, "enriched": True, "timestamp": time.time()}
            enriched_event = Event(
                event_type=event.event_type,
                source=event.source,
                payload=enriched_payload,
                correlation_id=event.correlation_id,
            )
            return next_handler(enriched_event)

        def handler(event: Event):
            self.received_events.append(event)

        # Add middleware and handler
        self.event_bus.add_middleware(enrichment_middleware)
        self.event_bus.subscribe("enrich_test", handler)

        # Publish event
        test_event = Event("enrich_test", "test_source", {"original": "data"})
        self.event_bus.publish(test_event)

        # Verify event was enriched
        received_event = self.received_events[0]
        assert received_event.payload["original"] == "data"
        assert received_event.payload["enriched"] is True
        assert "timestamp" in received_event.payload

    def test_middleware_short_circuit(self):
        """Test middleware can short-circuit event processing."""

        def filtering_middleware(event: Event, next_handler):
            # Filter out events with blocked=True
            if event.payload.get("blocked"):
                return None  # Short-circuit
            return next_handler(event)

        def handler(event: Event):
            self.received_events.append(event)

        # Add middleware and handler
        self.event_bus.add_middleware(filtering_middleware)
        self.event_bus.subscribe("filter_test", handler)

        # Publish normal event
        normal_event = Event("filter_test", "test_source", {"data": "normal"})
        self.event_bus.publish(normal_event)

        # Publish blocked event
        blocked_event = Event("filter_test", "test_source", {"blocked": True})
        self.event_bus.publish(blocked_event)

        # Only normal event should reach handler
        assert len(self.received_events) == 1
        assert self.received_events[0].payload["data"] == "normal"


class TestSpecializedEventHandlers:
    """Test specialized event handler implementations."""

    def setup_method(self):
        """Setup for specialized handler tests."""
        self.event_bus = EventBus()
        self.received_events = []

    def test_conditional_event_handler(self):
        """Test conditional event handler."""

        def condition(event: Event) -> bool:
            return event.payload.get("process", False)

        def handler(event: Event):
            self.received_events.append(event)

        conditional_handler = ConditionalEventHandler(condition, handler)
        self.event_bus.subscribe("conditional_test", conditional_handler)

        # Publish event that meets condition
        good_event = Event("conditional_test", "source", {"process": True})
        self.event_bus.publish(good_event)

        # Publish event that doesn't meet condition
        bad_event = Event("conditional_test", "source", {"process": False})
        self.event_bus.publish(bad_event)

        # Only event meeting condition should be processed
        assert len(self.received_events) == 1
        assert self.received_events[0].payload["process"] is True

    def test_batch_event_handler(self):
        """Test batch event handler."""

        def batch_handler(events: list[Event]):
            self.received_events.extend(events)

        batch = BatchEventHandler(batch_handler, batch_size=3, timeout_seconds=1.0)
        self.event_bus.subscribe("batch_test", batch)

        # Publish events one by one
        for i in range(5):
            event = Event("batch_test", "source", {"index": i})
            self.event_bus.publish(event)

        # Should have processed first batch of 3
        assert len(self.received_events) == 3

        # Wait for timeout to process remaining events
        time.sleep(1.1)
        batch._process_timeout()

        # Now should have all 5 events
        assert len(self.received_events) == 5

    def test_retry_event_handler(self):
        """Test retry event handler."""
        call_count = 0

        def failing_handler(event: Event):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Failure {call_count}")
            self.received_events.append(event)

        retry_handler = RetryEventHandler(failing_handler, max_retries=3, delay_seconds=0.1)
        self.event_bus.subscribe("retry_test", retry_handler)

        # Publish event
        test_event = Event("retry_test", "source", {"data": "retry_test"})
        self.event_bus.publish(test_event)

        # Handler should have been called 3 times and finally succeeded
        assert call_count == 3
        assert len(self.received_events) == 1

    def test_retry_handler_max_retries_exceeded(self):
        """Test retry handler when max retries exceeded."""

        def always_failing_handler(event: Event):
            raise ValueError("Always fails")

        retry_handler = RetryEventHandler(always_failing_handler, max_retries=2, delay_seconds=0.01)
        self.event_bus.subscribe("retry_fail_test", retry_handler)

        # Publish event
        test_event = Event("retry_fail_test", "source")

        with patch("src.events.logger") as mock_logger:
            self.event_bus.publish(test_event)

            # Should log final failure
            mock_logger.error.assert_called()


class TestEventPublishingDecorator:
    """Test event publishing decorator functionality."""

    def setup_method(self):
        """Setup for decorator tests."""
        self.received_events = []

        def event_handler(event: Event):
            self.received_events.append(event)

        # Subscribe to all event types we'll test
        event_bus.subscribe("function_started", event_handler)
        event_bus.subscribe("function_completed", event_handler)
        event_bus.subscribe("function_failed", event_handler)

    def test_event_publish_config(self):
        """Test EventPublishConfig dataclass."""
        config = EventPublishConfig(
            start_event_type="start",
            success_event_type="success",
            error_event_type="error",
            source="test",
        )

        assert config.start_event_type == "start"
        assert config.success_event_type == "success"
        assert config.error_event_type == "error"
        assert config.source == "test"

    def test_create_function_payload(self):
        """Test function payload creation."""

        def test_func():
            pass

        payload = _create_function_payload(test_func, (1, 2, 3))

        assert payload["function"] == "test_func"
        assert payload["args_count"] == 3
        assert "result_type" not in payload

        # Test with result type
        payload_with_result = _create_function_payload(test_func, (1, 2), "str")
        assert payload_with_result["result_type"] == "str"

    def test_create_error_payload(self):
        """Test error payload creation."""

        def test_func():
            pass

        error = ValueError("Test error")
        payload = _create_error_payload(test_func, (1, 2), error)

        assert payload["function"] == "test_func"
        assert payload["args_count"] == 2
        assert payload["error_type"] == "ValueError"
        assert payload["error_message"] == "Test error"

    def test_sync_function_with_events(self):
        """Test event publishing decorator on sync function."""

        @publish_events("function_started", "function_completed", "function_failed", "test_source")
        def test_function(x, y):
            return x + y

        result = test_function(2, 3)

        assert result == 5
        # Should have start and success events
        assert len(self.received_events) >= 2

        # Check event types
        event_types = [event.event_type for event in self.received_events]
        assert "function_started" in event_types
        assert "function_completed" in event_types

    @pytest.mark.asyncio
    async def test_async_function_with_events(self):
        """Test event publishing decorator on async function."""

        @publish_events("function_started", "function_completed", "function_failed", "test_source")
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)
            return x * y

        result = await async_test_function(3, 4)

        assert result == 12
        # Should have start and success events
        assert len(self.received_events) >= 2

    def test_function_with_events_error(self):
        """Test event publishing when function raises error."""

        @publish_events("function_started", "function_completed", "function_failed", "test_source")
        def failing_function():
            raise ValueError("Test failure")

        with pytest.raises(ValueError):
            failing_function()

        # Should have start and error events
        event_types = [event.event_type for event in self.received_events]
        assert "function_started" in event_types
        assert "function_failed" in event_types
        assert "function_completed" not in event_types

    @pytest.mark.asyncio
    async def test_async_function_with_events_error(self):
        """Test async event publishing when function raises error."""

        @publish_events("function_started", "function_completed", "function_failed", "test_source")
        async def async_failing_function():
            await asyncio.sleep(0.01)
            raise RuntimeError("Async test failure")

        with pytest.raises(RuntimeError):
            await async_failing_function()

        # Should have start and error events
        event_types = [event.event_type for event in self.received_events]
        assert "function_started" in event_types
        assert "function_failed" in event_types


class TestGlobalEventBus:
    """Test global event bus instance."""

    def test_global_event_bus_exists(self):
        """Test that global event bus instance exists."""
        from src.events import event_bus

        assert event_bus is not None
        assert isinstance(event_bus, EventBus)

    def test_global_event_bus_functionality(self):
        """Test global event bus basic functionality."""
        received_events = []

        def handler(event: Event):
            received_events.append(event)

        # Use global event bus
        event_bus.subscribe("global_test", handler)

        test_event = Event("global_test", "global_source")
        event_bus.publish(test_event)

        assert len(received_events) == 1
        assert received_events[0].event_type == "global_test"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
