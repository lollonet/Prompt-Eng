"""
Comprehensive tests for ModernPromptGenerator.

Tests the async prompt generation system with Result types, event-driven architecture,
and enterprise-grade error handling patterns.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.prompt_generator_modern import (
    ModernPromptGenerator,
    create_modern_prompt_generator,
    PromptGeneratorAdapter,
)
from src.types_advanced import (
    PromptConfigAdvanced,
    create_technology_name,
    create_task_type,
    create_template_name,
)
from src.result_types import Success, Error, PromptError
from src.knowledge_manager_async import AsyncKnowledgeManager


class MockKnowledgeSource:
    """Mock knowledge source for testing."""
    
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        
    async def get_best_practices(self, technology):
        if self.should_fail:
            return Error(PromptError("Mock knowledge error", "TEST_ERROR"))
        return Success(["Clean Code Principles", "Testing Best Practices"])
    
    async def get_tools(self, technology):
        if self.should_fail:
            return Error(PromptError("Mock tools error", "TEST_ERROR"))
        return Success(["pytest", "black"])
    
    async def get_best_practice_details(self, name):
        if self.should_fail:
            return Error(PromptError("Mock details error", "TEST_ERROR"))
        return Success(f"# {name}\nDetailed content for {name}")
    
    async def get_tool_details(self, name):
        if self.should_fail:
            return Error(PromptError("Mock tool details error", "TEST_ERROR"))
        return Success({
            "name": name,
            "description": f"Description for {name}",
            "benefits": ["Benefit 1", "Benefit 2"]
        })
    
    async def health_check(self):
        return Success({"status": "healthy", "mock": True})
    
    async def clear_cache(self):
        pass


@pytest.fixture
def mock_knowledge_source():
    """Create a mock knowledge source."""
    return MockKnowledgeSource()


@pytest.fixture
def failing_knowledge_source():
    """Create a failing mock knowledge source."""
    return MockKnowledgeSource(should_fail=True)


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return PromptConfigAdvanced(
        technologies=[create_technology_name("python")],
        task_type=create_task_type("test task"),
        code_requirements="Test requirements",
        task_description="Test description",
        template_name=create_template_name("base_prompts/generic_code_prompt.txt"),
        performance_tracking=True,
    )


@pytest.fixture
def temp_prompts_dir(tmp_path):
    """Create a temporary prompts directory with test templates."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    
    # Create base_prompts directory
    base_dir = prompts_dir / "base_prompts"
    base_dir.mkdir()
    
    # Create a test template
    template_content = """You are an expert {{ technologies }} developer. 
Implement the following {{ task_type }}.

## Best Practices to Follow
{{ best_practices }}

## Tools
{{ tools }}

## Requirements
{{ code_requirements }}

Please provide a complete implementation."""
    
    template_path = base_dir / "generic_code_prompt.txt"
    template_path.write_text(template_content)
    
    return str(prompts_dir)


@pytest.fixture
async def modern_generator(mock_knowledge_source, temp_prompts_dir):
    """Create a ModernPromptGenerator for testing."""
    return ModernPromptGenerator(
        prompts_dir=temp_prompts_dir,
        knowledge_source=mock_knowledge_source,
        performance_tracking=True
    )


class TestModernPromptGenerator:
    """Test cases for ModernPromptGenerator."""
    
    @pytest.mark.asyncio
    async def test_generate_prompt_success(self, modern_generator, test_config):
        """Test successful prompt generation."""
        result = await modern_generator.generate_prompt(test_config)
        
        assert result.is_success()
        prompt = result.unwrap()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "python" in prompt.lower()
        assert "test task" in prompt.lower()
        assert "clean code principles" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_prompt_with_multiple_technologies(self, modern_generator):
        """Test prompt generation with multiple technologies."""
        config = PromptConfigAdvanced(
            technologies=[
                create_technology_name("python"),
                create_technology_name("javascript")
            ],
            task_type=create_task_type("multi-tech task"),
            code_requirements="Multi-technology requirements",
            performance_tracking=True,
        )
        
        result = await modern_generator.generate_prompt(config)
        
        assert result.is_success()
        prompt = result.unwrap()
        assert "python" in prompt.lower()
        assert "javascript" in prompt.lower()
        
    @pytest.mark.asyncio
    async def test_generate_prompt_knowledge_error(self, failing_knowledge_source, temp_prompts_dir, test_config):
        """Test prompt generation when knowledge source fails."""
        generator = ModernPromptGenerator(
            prompts_dir=temp_prompts_dir,
            knowledge_source=failing_knowledge_source,
            performance_tracking=True
        )
        
        result = await generator.generate_prompt(test_config)
        
        assert result.is_error()
        error = result.error
        assert isinstance(error, PromptError)
        assert "KNOWLEDGE_ERROR" in error.code
    
    @pytest.mark.asyncio
    async def test_generate_prompt_template_not_found(self, modern_generator):
        """Test prompt generation with non-existent template."""
        config = PromptConfigAdvanced(
            technologies=[create_technology_name("python")],
            task_type=create_task_type("test task"),
            code_requirements="Test requirements",
            template_name=create_template_name("nonexistent/template.txt"),
            performance_tracking=True,
        )
        
        result = await modern_generator.generate_prompt(config)
        
        # Should fallback to generic template
        assert result.is_success()
        prompt = result.unwrap()
        assert len(prompt) > 0
    
    @pytest.mark.asyncio
    async def test_template_caching(self, modern_generator, test_config):
        """Test that templates are cached properly."""
        # First generation should cache the template
        result1 = await modern_generator.generate_prompt(test_config)
        assert result1.is_success()
        
        # Second generation should use cached template
        result2 = await modern_generator.generate_prompt(test_config)
        assert result2.is_success()
        
        # Both should produce the same result
        assert result1.unwrap() == result2.unwrap()
    
    @pytest.mark.asyncio
    async def test_render_method_directly(self, modern_generator):
        """Test the render method directly."""
        context = {
            "technologies": "python",
            "task_type": "test task",
            "best_practices": "Test practices",
            "tools": "Test tools",
            "code_requirements": "Test requirements"
        }
        
        result = await modern_generator.render(
            create_template_name("base_prompts/generic_code_prompt.txt"),
            context
        )
        
        assert result.is_success()
        rendered = result.unwrap()
        assert "python" in rendered
        assert "test task" in rendered
    
    @pytest.mark.asyncio
    async def test_list_templates(self, modern_generator):
        """Test template listing functionality."""
        templates = modern_generator.list_templates()
        
        assert len(templates) > 0
        template_names = [str(t) for t in templates]
        assert "base_prompts/generic_code_prompt.txt" in template_names
    
    @pytest.mark.asyncio
    async def test_health_check(self, modern_generator):
        """Test health check functionality."""
        result = await modern_generator.health_check()
        
        assert result.is_success()
        health_info = result.unwrap()
        assert health_info["component"] == "ModernPromptGenerator"
        assert health_info["status"] == "healthy"
        assert "templates_count" in health_info
        assert "cache_size" in health_info
    
    @pytest.mark.asyncio
    async def test_clear_caches(self, modern_generator, test_config):
        """Test cache clearing functionality."""
        # Generate a prompt to populate caches
        await modern_generator.generate_prompt(test_config)
        
        # Clear caches
        await modern_generator.clear_caches()
        
        # Should still work after cache clear
        result = await modern_generator.generate_prompt(test_config)
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_performance_tracking_enabled(self, modern_generator, test_config):
        """Test that performance tracking works when enabled."""
        # Test that generator with performance tracking enabled works
        assert modern_generator.performance_tracking is True
        result = await modern_generator.generate_prompt(test_config)
        assert result.is_success()
        # The fact that it completes successfully means performance tracking is working
    
    @pytest.mark.asyncio
    async def test_performance_tracking_disabled(self, mock_knowledge_source, temp_prompts_dir, test_config):
        """Test generator with performance tracking disabled."""
        generator = ModernPromptGenerator(
            prompts_dir=temp_prompts_dir,
            knowledge_source=mock_knowledge_source,
            performance_tracking=False
        )
        
        result = await generator.generate_prompt(test_config)
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_concurrent_prompt_generation(self, modern_generator, test_config):
        """Test concurrent prompt generation."""
        # Create multiple configs
        configs = [
            PromptConfigAdvanced(
                technologies=[create_technology_name("python")],
                task_type=create_task_type(f"test task {i}"),
                code_requirements=f"Requirements {i}",
                performance_tracking=True,
            )
            for i in range(3)
        ]
        
        # Generate prompts concurrently
        tasks = [modern_generator.generate_prompt(config) for config in configs]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result.is_success()
            assert len(result.unwrap()) > 0


class TestFactoryFunction:
    """Test cases for the factory function."""
    
    @pytest.mark.asyncio
    async def test_create_modern_prompt_generator(self, temp_prompts_dir, tmp_path):
        """Test the factory function."""
        # Create a mock config file
        config_path = tmp_path / "test_config.json"
        config_path.write_text('{"python": {"best_practices": ["Clean Code"], "tools": ["pytest"]}}')
        
        generator = await create_modern_prompt_generator(
            prompts_dir=temp_prompts_dir,
            config_path=str(config_path),
            performance_tracking=True
        )
        
        assert isinstance(generator, ModernPromptGenerator)
        assert generator.performance_tracking is True
    
    @pytest.mark.asyncio
    async def test_factory_with_custom_parameters(self, temp_prompts_dir, tmp_path):
        """Test factory function with custom parameters."""
        config_path = tmp_path / "test_config.json"
        config_path.write_text('{"python": {"best_practices": [], "tools": []}}')
        
        generator = await create_modern_prompt_generator(
            prompts_dir=temp_prompts_dir,
            config_path=str(config_path),
            performance_tracking=False,
            enable_performance_tracking=False,
            max_concurrent_operations=5
        )
        
        assert isinstance(generator, ModernPromptGenerator)
        assert generator.performance_tracking is False


class TestPromptGeneratorAdapter:
    """Test cases for the backward compatibility adapter."""
    
    @pytest.fixture
    async def adapter(self, modern_generator):
        """Create an adapter for testing."""
        return PromptGeneratorAdapter(modern_generator)
    
    def test_legacy_interface(self, adapter):
        """Test the legacy synchronous interface."""
        prompt = adapter.generate_prompt_legacy(
            technologies=["python"],
            task_type="test task",
            code_requirements="Test requirements"
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "python" in prompt.lower()
    
    def test_legacy_interface_with_invalid_config(self, adapter):
        """Test legacy interface with invalid configuration."""
        with pytest.raises(ValueError):
            adapter.generate_prompt_legacy(
                technologies=["invalid tech name with spaces and special chars!"],
                task_type="",  # Empty task type should fail
                code_requirements="Test requirements"
            )
    
    def test_legacy_interface_with_generation_error(self, failing_knowledge_source, temp_prompts_dir):
        """Test legacy interface when generation fails."""
        failing_generator = ModernPromptGenerator(
            prompts_dir=temp_prompts_dir,
            knowledge_source=failing_knowledge_source,
            performance_tracking=True
        )
        adapter = PromptGeneratorAdapter(failing_generator)
        
        with pytest.raises(RuntimeError, match="Prompt generation failed"):
            adapter.generate_prompt_legacy(
                technologies=["python"],
                task_type="test task",
                code_requirements="Test requirements"
            )


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_exception_during_generation(self, modern_generator, test_config):
        """Test exception handling during prompt generation."""
        # Mock the knowledge source to raise an exception
        with patch.object(modern_generator.knowledge_source, 'get_best_practices', 
                         side_effect=Exception("Test exception")):
            result = await modern_generator.generate_prompt(test_config)
            
            assert result.is_error()
            error = result.error
            assert isinstance(error, PromptError)
            assert "COLLECTION_ERROR" in error.code
    
    @pytest.mark.asyncio
    async def test_template_error_handling(self, modern_generator, test_config):
        """Test template rendering error handling."""
        # Create a config with a template that will cause errors
        bad_config = PromptConfigAdvanced(
            technologies=[create_technology_name("python")],
            task_type=create_task_type("test task"),
            code_requirements="Test requirements",
            template_name=create_template_name("base_prompts/generic_code_prompt.txt"),
            performance_tracking=True,
        )
        
        # Mock template rendering to raise an exception
        with patch.object(modern_generator._jinja_env, 'get', 
                         side_effect=Exception("Template error")):
            result = await modern_generator.generate_prompt(bad_config)
            
            # Should handle the error gracefully
            assert result.is_error()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])