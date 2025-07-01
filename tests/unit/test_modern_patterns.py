"""
Comprehensive tests for modern patterns implementation.

Business Context: Tests verify that all modern patterns work correctly:
Result types, async I/O, event-driven architecture, performance monitoring,
and advanced type safety.

Why this approach: Comprehensive testing ensures the modern patterns
work reliably and maintain their benefits in production.
"""

import asyncio
import json
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.events import (
    Event,
    EventType,
    PromptGenerationCompletedEvent,
    PromptGenerationStartedEvent,
    event_bus,
    setup_default_event_handlers,
)
from src.knowledge_manager_async import AsyncKnowledgeManager
from src.performance import (
    LazyEvaluator,
    async_load_json_file,
    async_read_text_file,
    lazy,
    monitor_performance,
    performance_tracker,
)
from src.prompt_generator_modern import ModernPromptGenerator
from src.result_types import (
    Error,
    KnowledgeError,
    PromptError,
    Success,
    combine_results,
    safe_call,
)
from src.types_advanced import (
    KnowledgeManagerConfig,
    PromptConfigAdvanced,
    TaskType,
    TechnologyName,
    TemplateName,
    create_task_type,
    create_technology_name,
    create_template_name,
)


class TestResultTypes:
    """Test suite for Result types functionality."""

    def test_success_creation_and_methods(self):
        """Test Success creation and method behavior."""
        result = Success("test value")

        assert result.is_success()
        assert not result.is_error()
        assert result.unwrap() == "test value"
        assert result.unwrap_or("default") == "test value"

    def test_error_creation_and_methods(self):
        """Test Error creation and method behavior."""
        error = PromptError("test error", "TEST_CODE")
        result = Error(error)

        assert result.is_error()
        assert not result.is_success()
        assert result.unwrap_or("default") == "default"
        assert result.error == error

    def test_result_map_operations(self):
        """Test Result map operations for transformations."""
        # Success map
        success = Success(5)
        mapped = success.map(lambda x: x * 2)
        assert mapped.is_success()
        assert mapped.unwrap() == 10

        # Error map (should be no-op)
        error = Error("test error")
        mapped_error = error.map(lambda x: x * 2)
        assert mapped_error.is_error()
        assert mapped_error.error == "test error"

    def test_result_and_then_chaining(self):
        """Test Result and_then for monadic chaining."""

        def divide_by_two(x: int) -> Result[float, str]:
            if x % 2 != 0:
                return Error("Cannot divide odd number cleanly")
            return Success(x / 2)

        # Success chain
        result = Success(10).and_then(divide_by_two)
        assert result.is_success()
        assert result.unwrap() == 5.0

        # Error chain
        result = Success(5).and_then(divide_by_two)
        assert result.is_error()
        assert result.error == "Cannot divide odd number cleanly"

    def test_safe_call_function(self):
        """Test safe_call utility function."""
        # Successful call
        result = safe_call(lambda: 42)
        assert result.is_success()
        assert result.unwrap() == 42

        # Failed call
        def failing_function():
            raise ValueError("Test error")

        result = safe_call(failing_function)
        assert result.is_error()
        assert isinstance(result.error, ValueError)

    def test_combine_results(self):
        """Test combining multiple Results."""
        # All success
        results = [Success(1), Success(2), Success(3)]
        combined = combine_results(results)
        assert combined.is_success()
        assert combined.unwrap() == [1, 2, 3]

        # One error
        results = [Success(1), Error("error"), Success(3)]
        combined = combine_results(results)
        assert combined.is_error()
        assert combined.error == "error"


class TestAdvancedTypes:
    """Test suite for advanced type system."""

    def test_technology_name_creation(self):
        """Test TechnologyName creation and validation."""
        # Valid names
        python = create_technology_name("Python")
        assert python == "python"  # Should be normalized to lowercase

        react = create_technology_name("React")
        assert react == "react"

        # Invalid names
        with pytest.raises(ValueError, match="Technology name cannot be empty"):
            create_technology_name("")

        with pytest.raises(ValueError, match="Technology name must be alphanumeric"):
            create_technology_name("invalid@name")

    def test_task_type_creation(self):
        """Test TaskType creation and validation."""
        # Valid task type
        task = create_task_type("implement authentication feature")
        assert task == "implement authentication feature"

        # Invalid task type (too short)
        with pytest.raises(ValueError, match="Task type must be at least 3 characters"):
            create_task_type("ab")

    def test_template_name_creation(self):
        """Test TemplateName creation and validation."""
        # Valid template name
        template = create_template_name("base_prompts/generic.txt")
        assert template == "base_prompts/generic.txt"

        # Invalid template name (wrong extension)
        with pytest.raises(ValueError, match="Template name must end with .txt"):
            create_template_name("template.html")

        # Invalid template name (path traversal)
        with pytest.raises(ValueError, match="Template name contains invalid path components"):
            create_template_name("../outside.txt")

    def test_prompt_config_advanced_validation(self):
        """Test PromptConfigAdvanced validation."""
        # Valid configuration
        config = PromptConfigAdvanced(
            technologies=[create_technology_name("python")],
            task_type=create_task_type("implement feature"),
            code_requirements="Must follow SOLID principles and include comprehensive tests",
        )
        assert len(config.technologies) == 1
        assert config.technologies[0] == "python"

        # Invalid configuration (empty technologies)
        with pytest.raises(ValueError, match="At least one technology must be specified"):
            PromptConfigAdvanced(
                technologies=[],
                task_type=create_task_type("test task"),
                code_requirements="test requirements that are long enough",
            )

        # Invalid configuration (short code requirements)
        with pytest.raises(ValueError, match="Code requirements must be detailed"):
            PromptConfigAdvanced(
                technologies=[create_technology_name("python")],
                task_type=create_task_type("test task"),
                code_requirements="short",
            )


@pytest.mark.asyncio
class TestAsyncPerformance:
    """Test suite for async I/O and performance monitoring."""

    async def test_async_read_text_file_success(self, tmp_path):
        """Test successful async text file reading."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "Hello, async world!"
        test_file.write_text(test_content)

        # Read file
        result = await async_read_text_file(str(test_file))

        assert result.is_success()
        assert result.unwrap() == test_content

    async def test_async_read_text_file_not_found(self):
        """Test async text file reading with non-existent file."""
        result = await async_read_text_file("/nonexistent/file.txt")

        assert result.is_error()
        assert isinstance(result.error, KnowledgeError)
        assert "File not found" in result.error.message

    async def test_async_load_json_file_success(self, tmp_path):
        """Test successful async JSON file loading."""
        # Create test JSON file
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(test_data))

        # Load JSON
        result = await async_load_json_file(str(test_file))

        assert result.is_success()
        assert result.unwrap() == test_data

    async def test_async_load_json_file_invalid_json(self, tmp_path):
        """Test async JSON loading with invalid JSON."""
        # Create invalid JSON file
        test_file = tmp_path / "invalid.json"
        test_file.write_text("invalid json content")

        # Try to load
        result = await async_load_json_file(str(test_file))

        assert result.is_error()
        assert isinstance(result.error, KnowledgeError)
        assert "Invalid JSON" in result.error.message

    def test_lazy_evaluator(self):
        """Test lazy evaluation functionality."""
        call_count = 0

        def expensive_computation():
            nonlocal call_count
            call_count += 1
            return "computed result"

        lazy_eval = lazy(expensive_computation)

        # Should not be computed yet
        assert not lazy_eval.is_computed
        assert call_count == 0

        # First access should compute
        result1 = lazy_eval.get()
        assert result1 == "computed result"
        assert lazy_eval.is_computed
        assert call_count == 1

        # Second access should use cached value
        result2 = lazy_eval.get()
        assert result2 == "computed result"
        assert call_count == 1  # No additional computation

        # Invalidation should force recomputation
        lazy_eval.invalidate()
        assert not lazy_eval.is_computed

        result3 = lazy_eval.get()
        assert result3 == "computed result"
        assert call_count == 2  # Recomputed

    def test_performance_monitor_decorator(self):
        """Test performance monitoring decorator."""
        call_count = 0

        @monitor_performance("test_operation")
        def test_function():
            nonlocal call_count
            call_count += 1
            return "result"

        result = test_function()
        assert result == "result"
        assert call_count == 1

        # Performance should be tracked (we can't easily test the exact metrics here,
        # but we can verify the function works)


@pytest.mark.asyncio
class TestEventSystem:
    """Test suite for event-driven architecture."""

    async def test_event_creation_and_serialization(self):
        """Test event creation and serialization."""
        event = Event(
            event_type=EventType.PROMPT_GENERATION_STARTED,
            source="test_source",
            payload={"test": "data"},
        )

        assert event.event_type == EventType.PROMPT_GENERATION_STARTED
        assert event.source == "test_source"
        assert event.payload == {"test": "data"}

        # Test serialization
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "prompt_generation_started"
        assert event_dict["source"] == "test_source"
        assert event_dict["payload"] == {"test": "data"}

    async def test_event_bus_subscription_and_publishing(self):
        """Test event bus subscription and publishing."""
        # Clear any existing handlers
        event_bus._handlers.clear()
        event_bus._sync_handlers.clear()
        event_bus._global_handlers.clear()

        received_events = []

        async def test_handler(event: Event):
            received_events.append(event)

        # Subscribe to specific event type
        event_bus.subscribe(EventType.PROMPT_GENERATION_STARTED, test_handler)

        # Create and publish event
        test_event = Event(
            event_type=EventType.PROMPT_GENERATION_STARTED, source="test", payload={"test": "data"}
        )

        await event_bus.publish(test_event)

        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0] == test_event

    async def test_specific_event_types(self):
        """Test specific event type creation."""
        # Test PromptGenerationStartedEvent
        start_event = PromptGenerationStartedEvent.create(
            technologies=[TechnologyName("python")], task_type=TaskType("test task")
        )

        assert start_event.event_type == EventType.PROMPT_GENERATION_STARTED
        assert start_event.source == "PromptGenerator"
        assert "technologies" in start_event.payload
        assert "task_type" in start_event.payload

        # Test PromptGenerationCompletedEvent
        completion_event = PromptGenerationCompletedEvent.create(
            prompt_length=1000, technologies_count=2, execution_time=0.15
        )

        assert completion_event.event_type == EventType.PROMPT_GENERATION_COMPLETED
        assert completion_event.payload["prompt_length"] == 1000
        assert completion_event.payload["technologies_count"] == 2


@pytest.mark.asyncio
class TestAsyncKnowledgeManager:
    """Test suite for AsyncKnowledgeManager."""

    async def test_async_knowledge_manager_creation(self, tmp_path):
        """Test AsyncKnowledgeManager creation and configuration."""
        # Create test config file
        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["PEP8"], "tools": ["Pylint"]}}
        config_file.write_text(json.dumps(config_data))

        # Create configuration
        config = KnowledgeManagerConfig(
            config_path=str(config_file),
            base_path=str(tmp_path),
            cache_strategy="memory",
            max_concurrent_operations=5,
        )

        # Create knowledge manager
        km = AsyncKnowledgeManager(config)

        assert km.config.config_path == str(config_file)
        assert km.config.max_concurrent_operations == 5
        assert km.config.cache_strategy == "memory"

    async def test_health_check(self, tmp_path):
        """Test AsyncKnowledgeManager health check."""
        # Create minimal setup
        config_file = tmp_path / "config.json"
        config_file.write_text('{"python": {"best_practices": [], "tools": []}}')

        config = KnowledgeManagerConfig(config_path=str(config_file), base_path=str(tmp_path))

        km = AsyncKnowledgeManager(config)

        # Perform health check
        health_result = await km.health_check()

        assert health_result.is_success()
        health_info = health_result.unwrap()
        assert health_info["status"] == "healthy"
        assert "technologies_count" in health_info
        assert "cache_size" in health_info


@pytest.mark.asyncio
class TestModernPromptGenerator:
    """Test suite for ModernPromptGenerator."""

    async def test_modern_prompt_generator_creation(self, tmp_path):
        """Test ModernPromptGenerator creation."""
        # Create minimal setup
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Create basic template
        base_dir = prompts_dir / "base_prompts"
        base_dir.mkdir()
        template_file = base_dir / "generic_code_prompt.txt"
        template_file.write_text("Test template: {{ technologies }}")

        # Create mock knowledge source
        knowledge_source = AsyncMock()

        # Create generator
        generator = ModernPromptGenerator(
            prompts_dir=str(prompts_dir),
            knowledge_source=knowledge_source,
            performance_tracking=True,
        )

        assert generator.prompts_dir == prompts_dir
        assert generator.knowledge_source == knowledge_source
        assert generator.performance_tracking is True

    async def test_list_templates(self, tmp_path):
        """Test template listing functionality."""
        # Create template structure
        prompts_dir = tmp_path / "prompts"
        base_dir = prompts_dir / "base_prompts"
        base_dir.mkdir(parents=True)

        # Create test templates
        (base_dir / "generic.txt").write_text("generic template")

        lang_dir = prompts_dir / "language_specific" / "python"
        lang_dir.mkdir(parents=True)
        (lang_dir / "feature.txt").write_text("python template")

        # Create generator
        knowledge_source = AsyncMock()
        generator = ModernPromptGenerator(
            prompts_dir=str(prompts_dir), knowledge_source=knowledge_source
        )

        # List templates
        templates = generator.list_templates()

        assert len(templates) == 2
        template_names = [str(t) for t in templates]
        assert "base_prompts/generic.txt" in template_names
        assert "language_specific/python/feature.txt" in template_names

        # Test category filtering
        base_templates = generator.list_templates("base_prompts")
        assert len(base_templates) == 1
        assert str(base_templates[0]) == "base_prompts/generic.txt"


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the complete modern system."""

    async def test_end_to_end_prompt_generation(self, tmp_path):
        """Test complete end-to-end prompt generation flow."""
        # Setup complete test environment

        # 1. Create config file
        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["Clean Code"], "tools": ["Pylint"]}}
        config_file.write_text(json.dumps(config_data))

        # 2. Create knowledge base files
        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        (bp_dir / "clean_code.md").write_text("# Clean Code\nWrite clean code.")
        (tools_dir / "pylint.json").write_text(
            json.dumps({"name": "Pylint", "description": "Static code analyzer"})
        )

        # 3. Create templates
        prompts_dir = tmp_path / "prompts"
        base_dir = prompts_dir / "base_prompts"
        base_dir.mkdir(parents=True)

        template_content = """Generate {{ technologies }} code for {{ task_type }}.
Requirements: {{ code_requirements }}
Best Practices: {{ best_practices }}
Tools: {{ tools }}"""

        (base_dir / "generic_code_prompt.txt").write_text(template_content)

        # 4. Create AsyncKnowledgeManager
        config = KnowledgeManagerConfig(config_path=str(config_file), base_path=str(tmp_path))
        knowledge_source = AsyncKnowledgeManager(config)

        # 5. Create ModernPromptGenerator
        generator = ModernPromptGenerator(
            prompts_dir=str(prompts_dir), knowledge_source=knowledge_source
        )

        # 6. Create prompt config
        prompt_config = PromptConfigAdvanced(
            technologies=[create_technology_name("python")],
            task_type=create_task_type("implement authentication"),
            code_requirements="Must be secure and follow best practices",
            template_name="base_prompts/generic_code_prompt.txt",  # type: ignore
        )

        # 7. Generate prompt
        result = await generator.generate_prompt(prompt_config)

        # 8. Verify result
        assert result.is_success()
        prompt = result.unwrap()

        assert "python" in prompt
        assert "implement authentication" in prompt
        assert "Must be secure and follow best practices" in prompt
        assert "Clean Code" in prompt
        assert "Pylint" in prompt
        assert "Static code analyzer" in prompt


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
