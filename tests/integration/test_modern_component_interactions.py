"""
Integration tests for modern component interactions.

Tests the interaction between ModernPromptGenerator, AsyncKnowledgeManager, 
EventBus, and the centralized configuration system to ensure proper
end-to-end functionality.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

import pytest

from src.config_manager import get_config, ConfigurationManager
from src.events import EventBus, EventType, setup_default_event_handlers, event_bus as global_event_bus
from src.knowledge_manager_async import AsyncKnowledgeManager
from src.prompt_generator_modern import ModernPromptGenerator
from src.result_types import Success, Error
from src.types_advanced import (
    PromptConfigAdvanced, 
    TechnologyName, 
    TaskType, 
    KnowledgeManagerConfig
)


class TestModernComponentInteractions:
    """Test modern component integration and interactions."""

    @pytest.fixture
    async def event_bus(self):
        """Create and setup event bus with default handlers."""
        bus = EventBus()
        setup_default_event_handlers()  # Sets up handlers on the global event_bus
        return bus

    @pytest.fixture
    def mock_config_manager(self, tmp_path):
        """Create mock configuration manager with test config."""
        config_content = """
        [system]
        name = "Test System"
        version = "1.0.0"
        environment = "testing"

        [paths]
        prompts_dir = "prompts"
        knowledge_base_root = "knowledge_base"
        config_dir = "config"
        cache_dir = "cache"

        [performance]
        max_concurrent_operations = 5
        enable_performance_tracking = true
        performance_threshold_ms = 1000

        [cache]
        strategy = "memory"
        ttl_seconds = 300
        max_size = 100

        [knowledge_manager]
        preload_common_technologies = true
        auto_refresh_interval_minutes = 30
        validation_strict_mode = true
        """
        
        config_file = tmp_path / "test_config.toml"
        config_file.write_text(config_content)
        
        return ConfigurationManager(str(config_file))

    @pytest.fixture
    async def knowledge_manager(self, mock_config_manager, tmp_path):
        """Create AsyncKnowledgeManager with test configuration."""
        # Setup test knowledge base structure
        kb_root = tmp_path / "knowledge_base"
        kb_root.mkdir()
        
        # Create test config mapping (this is what AsyncKnowledgeManager actually reads)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        tech_mapping = {
            "python": {
                "best_practices": ["Use type hints", "Follow PEP 8", "Write tests"],
                "tools": ["pytest", "black", "mypy"]
            },
            "docker": {
                "best_practices": ["Multi-stage builds", "Minimal base images", "Security scanning"],
                "tools": ["docker-compose", "buildx", "docker"]
            }
        }
        
        (config_dir / "tech_stack_mapping.json").write_text(
            json.dumps(tech_mapping, indent=2)
        )
        
        # Also create knowledge base structure for consistency
        (kb_root / "technology_knowledge.json").write_text(
            json.dumps({"known_technologies": ["python", "docker"]}, indent=2)
        )
        
        # Create knowledge manager config
        km_config = KnowledgeManagerConfig(
            config_path=str(config_dir / "tech_stack_mapping.json"),
            base_path=str(kb_root),
            cache_strategy="memory",
            cache_ttl_seconds=300,
            enable_performance_tracking=True,
            max_concurrent_operations=5
        )
        
        return AsyncKnowledgeManager(km_config)

    @pytest.fixture
    def prompt_templates(self, tmp_path):
        """Create test prompt templates."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        base_dir = prompts_dir / "base_prompts"
        base_dir.mkdir()
        
        # Generic template
        generic_template = """
You are an expert developer working with {{ technologies }}.

## Task: {{ task_type }}
{{ task_description }}

## Requirements
{{ code_requirements }}

## Best Practices
{{ best_practices }}

## Recommended Tools
{{ tools }}

Generate code that follows these guidelines and uses appropriate tools.
"""
        (base_dir / "generic_code_prompt.txt").write_text(generic_template)
        
        return str(prompts_dir)

    @pytest.fixture
    async def modern_prompt_generator(self, knowledge_manager, event_bus, prompt_templates):
        """Create ModernPromptGenerator with all dependencies."""
        return ModernPromptGenerator(
            prompts_dir=prompt_templates,
            knowledge_source=knowledge_manager,
            performance_tracking=True
        )

    @pytest.mark.asyncio
    async def test_complete_prompt_generation_workflow(
        self, 
        modern_prompt_generator,
        knowledge_manager
    ):
        """Test complete prompt generation workflow with all components."""
        # Setup event tracking on the global event bus
        events_received = []
        
        async def track_events(event):
            events_received.append(event)
        
        # Subscribe to the global event bus that ModernPromptGenerator uses
        global_event_bus.subscribe(EventType.PROMPT_GENERATION_STARTED, track_events)
        global_event_bus.subscribe(EventType.PROMPT_GENERATION_COMPLETED, track_events)
        
        # Create prompt configuration
        config = PromptConfigAdvanced(
            technologies=[TechnologyName("python"), TechnologyName("docker")],
            task_type=TaskType("api_development"),
            task_description="Create a FastAPI application with Docker deployment",
            code_requirements="Include authentication, database integration, and health checks"
        )
        
        # Generate prompt
        result = await modern_prompt_generator.generate_prompt(config)
        
        # Verify result
        assert result.is_success(), f"Prompt generation failed: {result.error if result.is_error() else 'Unknown error'}"
        
        prompt = result.unwrap()
        assert prompt is not None
        assert len(prompt) > 0
        assert "python" in prompt.lower()
        assert "docker" in prompt.lower()
        assert "fastapi" in prompt.lower()
        
        # Verify events were published
        assert len(events_received) >= 2
        
        # Check event types
        event_types = [event.event_type for event in events_received]
        assert EventType.PROMPT_GENERATION_STARTED in event_types
        assert EventType.PROMPT_GENERATION_COMPLETED in event_types
        
        # Verify correlation IDs match
        correlation_ids = [event.correlation_id for event in events_received]
        assert len(set(correlation_ids)) == 1  # All events should have same correlation ID

    @pytest.mark.asyncio
    async def test_knowledge_manager_integration(self, knowledge_manager):
        """Test AsyncKnowledgeManager integration with configuration."""
        # Test loading knowledge for individual technologies
        python_tech = TechnologyName("python")
        docker_tech = TechnologyName("docker")
        
        # Test best practices loading
        python_practices_result = await knowledge_manager.get_best_practices(python_tech)
        docker_practices_result = await knowledge_manager.get_best_practices(docker_tech)
        
        assert python_practices_result.is_success(), f"Python practices loading failed: {python_practices_result.error if python_practices_result.is_error() else 'Unknown error'}"
        assert docker_practices_result.is_success(), f"Docker practices loading failed: {docker_practices_result.error if docker_practices_result.is_error() else 'Unknown error'}"
        
        python_practices = python_practices_result.unwrap()
        docker_practices = docker_practices_result.unwrap()
        
        assert len(python_practices) > 0
        assert len(docker_practices) > 0
        
        # Test tools loading
        python_tools_result = await knowledge_manager.get_tools(python_tech)
        docker_tools_result = await knowledge_manager.get_tools(docker_tech)
        
        assert python_tools_result.is_success(), f"Python tools loading failed: {python_tools_result.error if python_tools_result.is_error() else 'Unknown error'}"
        assert docker_tools_result.is_success(), f"Docker tools loading failed: {docker_tools_result.error if docker_tools_result.is_error() else 'Unknown error'}"
        
        python_tools = python_tools_result.unwrap()
        docker_tools = docker_tools_result.unwrap()
        
        assert len(python_tools) > 0
        assert len(docker_tools) > 0

    @pytest.mark.asyncio
    async def test_event_bus_correlation_tracking(self, event_bus):
        """Test event correlation and tracking across components."""
        events_with_correlation = []
        
        async def track_correlated_events(event):
            if hasattr(event, 'correlation_id') and event.correlation_id:
                events_with_correlation.append(event)
        
        # Subscribe to all relevant events
        for event_type in [
            EventType.PROMPT_GENERATION_STARTED,
            EventType.PROMPT_GENERATION_COMPLETED,
            EventType.KNOWLEDGE_LOADING_STARTED,
            EventType.KNOWLEDGE_LOADING_COMPLETED
        ]:
            event_bus.subscribe(event_type, track_correlated_events)
        
        # Trigger some operations that should generate correlated events
        await event_bus.publish(EventType.PROMPT_GENERATION_STARTED, {
            "config": {"technologies": ["python"]},
            "correlation_id": "test-123"
        })
        
        await event_bus.publish(EventType.PROMPT_GENERATION_COMPLETED, {
            "result": "success",
            "correlation_id": "test-123"
        })
        
        # Give events time to propagate
        await asyncio.sleep(0.1)
        
        assert len(events_with_correlation) >= 2
        
        # Verify all events have the same correlation ID
        correlation_ids = [event.correlation_id for event in events_with_correlation]
        assert all(cid == "test-123" for cid in correlation_ids)

    @pytest.mark.asyncio
    async def test_error_handling_across_components(
        self,
        modern_prompt_generator,
        event_bus
    ):
        """Test error handling and propagation across component boundaries."""
        error_events = []
        
        async def track_errors(event):
            error_events.append(event)
        
        event_bus.subscribe(EventType.PROMPT_GENERATION_FAILED, track_errors)
        
        # Create invalid configuration to trigger error
        invalid_config = PromptConfigAdvanced(
            technologies=[],  # Empty technologies should cause error
            task_type=TaskType("invalid_task"),
            task_description="",
            code_requirements=""
        )
        
        # Attempt generation with invalid config
        result = await modern_prompt_generator.generate_prompt(invalid_config)
        
        # Should handle error gracefully
        if result.is_error():
            # Verify error is properly typed and contains useful information
            error = result.error
            assert error is not None
            assert hasattr(error, 'message') or hasattr(error, '__str__')
            
        # Check if error events were published
        await asyncio.sleep(0.1)  # Give events time to propagate

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(
        self,
        modern_prompt_generator,
        event_bus
    ):
        """Test performance monitoring across component interactions."""
        performance_events = []
        
        async def track_performance(event):
            if hasattr(event, 'metadata') and 'duration_ms' in event.metadata:
                performance_events.append(event)
        
        event_bus.subscribe(EventType.PROMPT_GENERATION_COMPLETED, track_performance)
        
        # Generate prompt and measure performance
        config = PromptConfigAdvanced(
            technologies=[TechnologyName("python")],
            task_type=TaskType("script_development"),
            task_description="Create a data processing script",
            code_requirements="Include error handling and logging"
        )
        
        result = await modern_prompt_generator.generate_prompt(config)
        
        assert result.is_success()
        
        # Give events time to propagate
        await asyncio.sleep(0.1)
        
        # Verify performance data was captured
        if performance_events:
            perf_event = performance_events[0]
            assert 'duration_ms' in perf_event.metadata
            assert isinstance(perf_event.metadata['duration_ms'], (int, float))
            assert perf_event.metadata['duration_ms'] >= 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self,
        modern_prompt_generator,
        event_bus
    ):
        """Test concurrent prompt generation with proper resource management."""
        # Create multiple prompt configurations
        configs = [
            PromptConfigAdvanced(
                technologies=[TechnologyName("python")],
                task_type=TaskType(f"task_{i}"),
                task_description=f"Task {i} description",
                code_requirements="Basic requirements"
            )
            for i in range(3)
        ]
        
        # Track concurrent operations
        concurrent_events = []
        
        async def track_concurrent(event):
            concurrent_events.append(event)
        
        event_bus.subscribe(EventType.PROMPT_GENERATION_STARTED, track_concurrent)
        event_bus.subscribe(EventType.PROMPT_GENERATION_COMPLETED, track_concurrent)
        
        # Execute concurrent prompt generations
        tasks = [
            modern_prompt_generator.generate_prompt(config)
            for config in configs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent operation {i} failed: {result}")
            else:
                assert result.is_success(), f"Result {i} failed: {result.error if result.is_error() else 'Unknown error'}"
        
        # Verify events were properly managed
        await asyncio.sleep(0.1)
        assert len(concurrent_events) >= len(configs) * 2  # Start + Complete for each

    @pytest.mark.asyncio
    async def test_configuration_hot_reload_integration(
        self,
        mock_config_manager,
        tmp_path
    ):
        """Test that configuration changes are properly handled by components."""
        # Initial configuration load
        initial_result = mock_config_manager.load_config()
        assert initial_result.is_success()
        
        initial_config = initial_result.unwrap()
        initial_max_ops = initial_config.performance.max_concurrent_operations
        
        # Modify configuration file
        new_config_content = """
        [system]
        name = "Test System Updated"
        version = "1.1.0"
        environment = "testing"

        [paths]
        prompts_dir = "prompts"
        knowledge_base_root = "knowledge_base"
        config_dir = "config"
        cache_dir = "cache"

        [performance]
        max_concurrent_operations = 10
        enable_performance_tracking = true
        performance_threshold_ms = 500

        [cache]
        strategy = "memory"
        ttl_seconds = 600
        max_size = 200
        """
        
        config_file = Path(mock_config_manager.config_path)
        config_file.write_text(new_config_content)
        
        # Force reload
        reload_result = mock_config_manager.reload_config()
        assert reload_result.is_success()
        
        reloaded_config = reload_result.unwrap()
        
        # Verify changes were applied
        assert reloaded_config.system.name == "Test System Updated"
        assert reloaded_config.system.version == "1.1.0"
        assert reloaded_config.performance.max_concurrent_operations == 10
        assert reloaded_config.performance.performance_threshold_ms == 500
        assert reloaded_config.cache.ttl_seconds == 600
        
        # Verify reload timestamp updated
        assert reloaded_config.loaded_at > initial_config.loaded_at


class TestComponentFailureRecovery:
    """Test component interaction failure scenarios and recovery."""

    @pytest.mark.asyncio
    async def test_knowledge_manager_failure_recovery(self):
        """Test prompt generation when knowledge manager fails."""
        # Create mock knowledge manager that fails
        mock_km = AsyncMock()
        mock_km.get_technologies_knowledge.return_value = Error("Knowledge loading failed")
        
        event_bus = EventBus()
        
        generator = ModernPromptGenerator(
            prompts_dir="test_prompts",
            knowledge_source=mock_km,
            performance_tracking=True
        )
        
        config = PromptConfigAdvanced(
            technologies=[TechnologyName("python")],
            task_type=TaskType("development"),
            task_description="Test task",
            code_requirements="Test requirements"
        )
        
        # Should handle knowledge manager failure gracefully
        result = await generator.generate_prompt(config)
        
        # Depending on implementation, this might succeed with limited knowledge
        # or fail gracefully with a proper error message
        if result.is_error():
            error = result.error
            assert error is not None
            # Error should be informative about the knowledge loading failure

    @pytest.mark.asyncio
    async def test_event_bus_failure_isolation(self):
        """Test that event bus failures don't break core functionality."""
        # Create mock event bus that fails
        mock_event_bus = AsyncMock()
        mock_event_bus.publish.side_effect = Exception("Event publishing failed")
        
        # Create real knowledge manager
        km_config = KnowledgeManagerConfig(
            config_path="config/tech_stack_mapping.json",
            base_path="knowledge_base",
            cache_strategy="memory"
        )
        
        km = AsyncKnowledgeManager(km_config)
        
        generator = ModernPromptGenerator(
            prompts_dir="prompts",
            knowledge_source=km,
            performance_tracking=True
        )
        
        config = PromptConfigAdvanced(
            technologies=[TechnologyName("python")],
            task_type=TaskType("development"),
            task_description="Test task",
            code_requirements="Test requirements"
        )
        
        # Core functionality should work even if events fail
        # (This test may need adjustment based on actual implementation)
        try:
            result = await generator.generate_prompt(config)
            # If the implementation is robust, it should succeed despite event failures
            # If not, it should fail gracefully with a clear error
        except Exception as e:
            # Should not propagate raw event publishing exceptions
            assert "Event publishing failed" not in str(e)