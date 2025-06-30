"""
Event-driven architecture implementation for decoupled system design.

Business Context: Implements event-driven patterns to decouple components,
enable observability, and support extensible architectures following
modern best practices.

Why this approach: Event-driven architecture improves maintainability,
testability, and allows for loosely coupled components that can evolve
independently while maintaining system observability.
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Callable, Awaitable, Type, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
from uuid import uuid4, UUID
from functools import wraps

from .types_advanced import TechnologyName, TaskType, TemplateName
from .performance import performance_tracker

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of system event types."""
    PROMPT_GENERATION_STARTED = "prompt_generation_started"
    PROMPT_GENERATION_COMPLETED = "prompt_generation_completed"
    PROMPT_GENERATION_FAILED = "prompt_generation_failed"
    KNOWLEDGE_CACHE_HIT = "knowledge_cache_hit"
    KNOWLEDGE_CACHE_MISS = "knowledge_cache_miss"
    TEMPLATE_RENDERED = "template_rendered"
    TEMPLATE_LOAD_FAILED = "template_load_failed"
    PERFORMANCE_THRESHOLD_EXCEEDED = "performance_threshold_exceeded"
    SYSTEM_ERROR = "system_error"


@dataclass(frozen=True)
class Event:
    """Base event class with common attributes."""
    event_type: EventType
    source: str
    event_id: UUID = field(default_factory=uuid4)
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[UUID] = field(default=None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': str(self.event_id),
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'source': self.source,
            'payload': self.payload,
            'correlation_id': str(self.correlation_id) if self.correlation_id else None
        }


# Specific event types for type safety

@dataclass(frozen=True)
class PromptGenerationStartedEvent(Event):
    """Event fired when prompt generation begins."""
    event_type: EventType = field(default=EventType.PROMPT_GENERATION_STARTED, init=False)
    
    @classmethod
    def create(cls, technologies: List[TechnologyName], task_type: TaskType, 
               correlation_id: Optional[UUID] = None) -> 'PromptGenerationStartedEvent':
        return cls(
            source="PromptGenerator",
            payload={
                'technologies': technologies,
                'task_type': task_type,
                'operation_start': time.time()
            },
            correlation_id=correlation_id
        )


@dataclass(frozen=True)
class PromptGenerationCompletedEvent(Event):
    """Event fired when prompt generation completes successfully."""
    event_type: EventType = field(default=EventType.PROMPT_GENERATION_COMPLETED, init=False)
    
    @classmethod
    def create(cls, prompt_length: int, technologies_count: int, 
               execution_time: float, correlation_id: Optional[UUID] = None) -> 'PromptGenerationCompletedEvent':
        return cls(
            source="PromptGenerator",
            payload={
                'prompt_length': prompt_length,
                'technologies_count': technologies_count,
                'execution_time_ms': round(execution_time * 1000, 2),
                'operation_end': time.time()
            },
            correlation_id=correlation_id
        )


@dataclass(frozen=True)
class PerformanceThresholdExceededEvent(Event):
    """Event fired when performance thresholds are exceeded."""
    event_type: EventType = field(default=EventType.PERFORMANCE_THRESHOLD_EXCEEDED, init=False)
    
    @classmethod
    def create(cls, operation: str, actual_time: float, threshold: float,
               correlation_id: Optional[UUID] = None) -> 'PerformanceThresholdExceededEvent':
        return cls(
            source="PerformanceMonitor",
            payload={
                'operation': operation,
                'actual_time_ms': round(actual_time * 1000, 2),
                'threshold_ms': round(threshold * 1000, 2),
                'exceeded_by_ms': round((actual_time - threshold) * 1000, 2)
            },
            correlation_id=correlation_id
        )


# Event handler types
EventHandler = Callable[[Event], Awaitable[None]]
SyncEventHandler = Callable[[Event], None]


class EventBus:
    """
    Asynchronous event bus for decoupled component communication.
    
    Business Context: Enables loose coupling between components by allowing
    them to communicate through events rather than direct dependencies.
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._sync_handlers: Dict[EventType, List[SyncEventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []
        self._max_history_size = 1000
        
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe an async handler to a specific event type.
        
        Args:
            event_type: Type of event to listen for.
            handler: Async function to handle the event.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type.value}")
    
    def subscribe_sync(self, event_type: EventType, handler: SyncEventHandler) -> None:
        """
        Subscribe a sync handler to a specific event type.
        
        Args:
            event_type: Type of event to listen for.
            handler: Sync function to handle the event.
        """
        if event_type not in self._sync_handlers:
            self._sync_handlers[event_type] = []
        self._sync_handlers[event_type].append(handler)
        logger.debug(f"Subscribed sync handler to {event_type.value}")
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """
        Subscribe to all events (global handler).
        
        Args:
            handler: Async function to handle all events.
        """
        self._global_handlers.append(handler)
        logger.debug("Subscribed global event handler")
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: Event to publish.
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
        
        logger.debug(f"Publishing event: {event.event_type.value} from {event.source}")
        
        # Collect all handlers
        handlers_to_run = []
        
        # Type-specific async handlers
        if event.event_type in self._handlers:
            handlers_to_run.extend(self._handlers[event.event_type])
        
        # Global async handlers
        handlers_to_run.extend(self._global_handlers)
        
        # Run async handlers concurrently
        if handlers_to_run:
            try:
                await asyncio.gather(*[handler(event) for handler in handlers_to_run])
            except Exception as e:
                logger.error(f"Error in async event handler: {e}")
        
        # Run sync handlers
        if event.event_type in self._sync_handlers:
            for handler in self._sync_handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in sync event handler: {e}")
    
    def get_event_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by.
            
        Returns:
            List of events from history.
        """
        if event_type is None:
            return self._event_history.copy()
        
        return [event for event in self._event_history if event.event_type == event_type]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
    
    def unsubscribe(self, event_type: EventType, handler: Union[EventHandler, SyncEventHandler]) -> bool:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: Event type to unsubscribe from.
            handler: Handler to remove.
            
        Returns:
            True if handler was found and removed, False otherwise.
        """
        # Try async handlers
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                return True
        
        # Try sync handlers
        if event_type in self._sync_handlers:
            if handler in self._sync_handlers[event_type]:
                self._sync_handlers[event_type].remove(handler)
                return True
        
        return False


# Global event bus instance
event_bus = EventBus()


# Built-in event handlers for common functionality

async def performance_monitoring_handler(event: Event) -> None:
    """Built-in handler for performance monitoring events."""
    if event.event_type == EventType.PERFORMANCE_THRESHOLD_EXCEEDED:
        logger.warning(f"Performance threshold exceeded: {event.payload}")
        
        # Record performance metric
        operation = event.payload.get('operation', 'unknown')
        actual_time = event.payload.get('actual_time_ms', 0)
        performance_tracker.record_error(operation)


def logging_handler(event: Event) -> None:
    """Built-in handler for logging all events."""
    logger.info(f"Event: {event.event_type.value} from {event.source} - {event.payload}")


async def metrics_collection_handler(event: Event) -> None:
    """Built-in handler for collecting metrics from events."""
    # This would integrate with a metrics system like Prometheus
    if event.event_type == EventType.PROMPT_GENERATION_COMPLETED:
        execution_time = event.payload.get('execution_time_ms', 0)
        technologies_count = event.payload.get('technologies_count', 0)
        
        # Record metrics (would use actual metrics collector in production)
        logger.debug(f"Metrics: prompt_generation_time={execution_time}ms, technologies={technologies_count}")


# Event decorators for automatic event publishing

@dataclass(frozen=True)
class EventPublishConfig:
    """Configuration for event publishing decorator."""
    start_event_type: EventType
    success_event_type: EventType
    error_event_type: EventType
    source: str


def _create_function_payload(func: Callable, args: tuple, result_type: Optional[str] = None) -> Dict[str, Any]:
    """Create standardized payload for function events."""
    payload = {
        'function': func.__name__,
        'args_count': len(args)
    }
    if result_type:
        payload['result_type'] = result_type
    return payload


def _create_error_payload(func: Callable, args: tuple, error: Exception) -> Dict[str, Any]:
    """Create standardized payload for error events."""
    return {
        'function': func.__name__,
        'args_count': len(args),
        'error_type': type(error).__name__,
        'error_message': str(error)
    }


async def _publish_async_events(config: EventPublishConfig, func: Callable, args: tuple, kwargs: dict):
    """Handle async event publishing workflow."""
    correlation_id = uuid4()
    
    # Publish start event
    start_event = Event(
        event_type=config.start_event_type,
        source=config.source,
        correlation_id=correlation_id,
        payload=_create_function_payload(func, args)
    )
    await event_bus.publish(start_event)
    
    try:
        result = await func(*args, **kwargs)
        
        # Publish success event
        success_event = Event(
            event_type=config.success_event_type,
            source=config.source,
            correlation_id=correlation_id,
            payload=_create_function_payload(func, args, type(result).__name__)
        )
        await event_bus.publish(success_event)
        
        return result
        
    except Exception as e:
        # Publish error event
        error_event = Event(
            event_type=config.error_event_type,
            source=config.source,
            correlation_id=correlation_id,
            payload=_create_error_payload(func, args, e)
        )
        await event_bus.publish(error_event)
        raise


def _publish_sync_events(config: EventPublishConfig, func: Callable, args: tuple, kwargs: dict):
    """Handle sync event publishing workflow."""
    correlation_id = uuid4()
    
    try:
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        raise


def publish_events(start_event_type: EventType, success_event_type: EventType, 
                  error_event_type: EventType, source: str):
    """Decorator to automatically publish events for function execution."""
    config = EventPublishConfig(start_event_type, success_event_type, error_event_type, source)
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await _publish_async_events(config, func, args, kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return _publish_sync_events(config, func, args, kwargs)
            return sync_wrapper
    
    return decorator


# Setup default handlers
def setup_default_event_handlers():
    """Setup default event handlers for the system."""
    # Subscribe to performance events
    event_bus.subscribe(EventType.PERFORMANCE_THRESHOLD_EXCEEDED, performance_monitoring_handler)
    
    # Subscribe to all events for metrics collection
    event_bus.subscribe_all(metrics_collection_handler)
    
    # Optional: Subscribe to all events for logging (can be noisy)
    # event_bus.subscribe_sync(EventType.PROMPT_GENERATION_COMPLETED, logging_handler)


# Example usage
async def _example_event_usage():
    """Example of event-driven architecture usage."""
    
    # Setup handlers
    setup_default_event_handlers()
    
    # Custom handler
    async def custom_prompt_handler(event: Event):
        if event.event_type == EventType.PROMPT_GENERATION_COMPLETED:
            prompt_length = event.payload.get('prompt_length', 0)
            if prompt_length > 10000:
                logger.info("Generated a very long prompt!")
    
    # Subscribe custom handler
    event_bus.subscribe(EventType.PROMPT_GENERATION_COMPLETED, custom_prompt_handler)
    
    # Publish events
    start_event = PromptGenerationStartedEvent.create(
        technologies=[TechnologyName("python")],
        task_type=TaskType("feature implementation")
    )
    await event_bus.publish(start_event)
    
    completion_event = PromptGenerationCompletedEvent.create(
        prompt_length=5000,
        technologies_count=1,
        execution_time=0.15,
        correlation_id=start_event.correlation_id
    )
    await event_bus.publish(completion_event)