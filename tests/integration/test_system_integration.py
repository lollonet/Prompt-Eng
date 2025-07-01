"""
Comprehensive integration tests for component interactions.

Tests full system integration, component communication, workflow orchestration,
and end-to-end functionality across all system layers.
"""

import pytest
import json
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.prompt_generator import PromptGenerator
from src.knowledge_manager import KnowledgeManager
from src.prompt_config import PromptConfig
from src.events import EventBus, Event, EventType, event_bus, setup_default_event_handlers
from src.performance_gates import PerformanceGate


class TestFullSystemIntegration:
    """Test complete system integration scenarios."""
    
    @pytest.fixture
    def integrated_system_setup(self, tmp_path):
        """Setup complete integrated system for testing."""
        # Create comprehensive directory structure
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        # Create template directories
        (prompts_dir / "base_prompts").mkdir()
        (prompts_dir / "language_specific").mkdir()
        (prompts_dir / "framework_specific").mkdir()
        
        # Create base templates
        base_dir = prompts_dir / "base_prompts"
        (base_dir / "generic_code_prompt.txt").write_text("""
You are an expert {{ role }} developer working with {{ technologies | join(', ') }}.

## Task: {{ task_type }}
{{ task_description }}

## Requirements
{{ code_requirements }}

## Best Practices to Follow
{% for practice in best_practices %}
### {{ practice }}
{{ practice_details.get(practice, 'Follow standard practices for ' + practice) }}
{% endfor %}

## Recommended Tools
{% for tool in tools %}
- **{{ tool.name }}**: {{ tool.description }}
  {% if tool.usage %}Usage: `{{ tool.usage }}`{% endif %}
  {% if tool.features %}Features: {{ tool.features | join(', ') }}{% endif %}
{% endfor %}

## Implementation Guidelines
- Write clean, maintainable code
- Include comprehensive error handling
- Add appropriate documentation
- Follow security best practices
- Implement proper testing

Please provide a complete, production-ready implementation.
        """.strip())
        
        # Create comprehensive configuration
        config_file = tmp_path / "config" / "tech_stack_mapping.json"
        config_file.parent.mkdir(exist_ok=True)
        
        config_data = {
            "python": {
                "best_practices": ["Clean Code", "PEP8", "Testing", "SOLID Principles"],
                "tools": ["pytest", "black", "mypy", "pylint"]
            },
            "javascript": {
                "best_practices": ["ES6+ Features", "Code Quality", "Testing"],
                "tools": ["jest", "eslint", "prettier"]
            },
            "react": {
                "best_practices": ["Component Design", "State Management"],
                "tools": ["testing-library", "storybook"]
            },
            "docker": {
                "best_practices": ["Multi-stage Builds", "Security"],
                "tools": ["dockerfile", "docker-compose"]
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Create comprehensive knowledge base
        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)
        
        # Create best practice files
        (bp_dir / "clean_code.md").write_text("""
# Clean Code Principles

## Core Concepts
- Functions should do one thing and do it well
- Use descriptive and meaningful names
- Keep functions and classes small

## Code Examples
```python
def calculate_order_total(items: List[OrderItem]) -> Decimal:
    return sum(item.price * item.quantity for item in items)
```
        """.strip())
        
        (bp_dir / "pep8.md").write_text("""
# PEP 8 Style Guide for Python Code

## Key Formatting Rules
- Use 4 spaces per indentation level
- Limit lines to 79 characters
- Use snake_case for variables and functions
        """.strip())
        
        (bp_dir / "testing.md").write_text("""
# Testing Best Practices

## Test-Driven Development (TDD)
1. Write a failing test
2. Write minimal code to make it pass
3. Refactor while keeping tests green
        """.strip())
        
        # Create tool files
        tools = {
            "pytest": {
                "name": "pytest",
                "description": "Powerful Python testing framework",
                "usage": "pytest tests/ -v --cov=src",
                "features": ["fixtures", "parametrization", "test discovery"]
            },
            "black": {
                "name": "black",
                "description": "Python code formatter",
                "usage": "black src/ tests/",
                "features": ["automatic formatting", "PEP 8 compliance"]
            },
            "jest": {
                "name": "jest",
                "description": "JavaScript testing framework",
                "usage": "npm test",
                "features": ["snapshot testing", "built-in mocking"]
            }
        }
        
        for name, data in tools.items():
            with open(tools_dir / f"{name}.json", 'w') as f:
                json.dump(data, f, indent=2)
        
        return {
            "prompts_dir": str(prompts_dir),
            "config_file": str(config_file),
            "base_path": str(tmp_path)
        }
    
    def test_complete_workflow_python_feature(self, integrated_system_setup):
        """Test complete workflow for Python feature development."""
        env = integrated_system_setup
        
        # Initialize system components
        generator = PromptGenerator(env["prompts_dir"], env["config_file"], base_path=env["base_path"])
        
        # Test comprehensive Python feature development workflow
        config = PromptConfig(
            technologies=["python"],
            task_type="feature development",
            task_description="Implement a caching system for database queries with TTL support",
            code_requirements="The system should support configurable TTL, automatic memory cleanup, and thread safety"
        )
        
        prompt = generator.generate_prompt(config)
        
        # Verify comprehensive integration
        assert len(prompt) > 1000
        
        # Verify role and technologies
        assert "expert" in prompt.lower()
        assert "python" in prompt.lower()
        
        # Verify task integration
        assert "caching system" in prompt
        assert "TTL support" in prompt
        
        # Verify requirements integration
        assert "configurable TTL" in prompt
        assert "memory cleanup" in prompt
        assert "thread safety" in prompt
        
        # Verify best practices integration
        assert "Clean Code" in prompt
        assert "Functions should do one thing" in prompt
        
        # Verify tools integration
        assert "pytest" in prompt
        assert "testing framework" in prompt
        assert "black" in prompt
        assert "code formatter" in prompt
    
    def test_multi_technology_integration(self, integrated_system_setup):
        """Test integration with multiple technologies."""
        env = integrated_system_setup
        
        generator = PromptGenerator(env["prompts_dir"], env["config_file"], base_path=env["base_path"])
        
        config = PromptConfig(
            technologies=["python", "javascript", "react"],
            task_type="full-stack application",
            task_description="Build a web application with Python backend and React frontend",
            code_requirements="Scalable architecture, RESTful API design, and responsive UI"
        )
        
        prompt = generator.generate_prompt(config)
        
        # Verify all technologies are represented
        assert "python" in prompt.lower()
        assert "javascript" in prompt.lower() 
        assert "react" in prompt.lower()
        
        # Verify technology-specific best practices
        assert "Clean Code" in prompt  # Python
        assert "ES6+" in prompt  # JavaScript
        assert "Component Design" in prompt  # React
        
        # Verify tools from all technologies
        assert "pytest" in prompt  # Python
        assert "jest" in prompt  # JavaScript
        assert "testing-library" in prompt  # React
        
        # Verify comprehensive integration
        assert len(prompt) > 1500  # Should be substantial with 3 technologies


class TestEventSystemIntegration:
    """Test integration of event system with other components."""
    
    @pytest.mark.asyncio
    async def test_event_bus_basic_integration(self):
        """Test basic event bus integration."""
        # Setup event tracking
        test_event_bus = EventBus()
        received_events = []
        
        async def event_collector(event):
            received_events.append(event)
        
        test_event_bus.subscribe_all(event_collector)
        
        # Publish test event
        test_event = Event(EventType.SYSTEM_ERROR, "TestSource")
        await test_event_bus.publish(test_event)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0].source == "TestSource"


class TestPerformanceIntegration:
    """Test integration with performance monitoring."""
    
    def test_performance_gates_integration(self, integrated_system_setup):
        """Test integration with performance gates."""
        env = integrated_system_setup
        
        # Create performance gate
        perf_gate = PerformanceGate(
            api_response_threshold_ms=200,
            memory_growth_threshold_percent=10
        )
        
        generator = PromptGenerator(env["prompts_dir"], env["config_file"], base_path=env["base_path"])
        
        # Test prompt generation with performance monitoring
        config = PromptConfig(
            technologies=["python"],
            task_type="performance test",
            task_description="test performance integration",
            code_requirements="ensure performance gates are respected during generation"
        )
        
        import time
        start_time = time.time()
        prompt = generator.generate_prompt(config)
        duration = time.time() - start_time
        
        # Verify prompt generation
        assert len(prompt) > 0
        
        # Test performance gate validation
        duration_ms = duration * 1000
        api_result = perf_gate.check_api_response_time(duration_ms)
        
        # Should pass performance checks for this simple case
        assert api_result.passed
        assert api_result.actual_value == duration_ms
        assert api_result.threshold == 200


class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""
    
    def test_graceful_degradation_missing_knowledge(self, integrated_system_setup):
        """Test graceful degradation when knowledge files are missing."""
        env = integrated_system_setup
        
        # Create config with non-existent knowledge
        config_file = Path(env["base_path"]) / "config" / "partial_config.json"
        partial_config = {
            "python": {
                "best_practices": ["Nonexistent Practice"],
                "tools": ["Nonexistent Tool"]
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(partial_config, f)
        
        generator = PromptGenerator(env["prompts_dir"], str(config_file), base_path=env["base_path"])
        
        config = PromptConfig(
            technologies=["python"],
            task_type="error handling test",
            task_description="test graceful degradation with missing knowledge",
            code_requirements="system should handle missing knowledge gracefully"
        )
        
        # Should generate prompt despite missing knowledge
        with patch('src.knowledge_manager.logger'):  # Suppress warning logs
            prompt = generator.generate_prompt(config)
        
        assert len(prompt) > 0
        assert "error handling test" in prompt
        assert "graceful degradation" in prompt
        
        # Should contain basic template content even without knowledge details
        assert "expert" in prompt.lower()
        assert "python" in prompt.lower()


class TestConfigurationIntegration:
    """Test configuration integration across components."""
    
    def test_configuration_consistency(self, integrated_system_setup):
        """Test configuration consistency across all components."""
        env = integrated_system_setup
        
        # Initialize components with same configuration
        generator = PromptGenerator(env["prompts_dir"], env["config_file"], base_path=env["base_path"])
        km = KnowledgeManager(env["config_file"], base_path=env["base_path"])
        
        # Test that both components see same configuration
        python_practices_gen = generator.knowledge_manager.get_best_practices("python")
        python_practices_km = km.get_best_practices("python")
        
        assert python_practices_gen == python_practices_km
        
        python_tools_gen = generator.knowledge_manager.get_tools("python")
        python_tools_km = km.get_tools("python")
        
        assert python_tools_gen == python_tools_km
        
        # Test configuration reflects in generated prompts
        config = PromptConfig(
            technologies=["python"],
            task_type="configuration test",
            task_description="verify configuration consistency",
            code_requirements="all components should use same configuration"
        )
        
        prompt = generator.generate_prompt(config)
        
        # Verify configured tools appear in prompt  
        for tool_name in python_tools_gen:
            tool_details = km.get_tool_details(tool_name)
            if tool_details:
                assert tool_details["name"] in prompt


class TestWorkflowOrchestration:
    """Test end-to-end workflow orchestration."""
    
    def test_complete_development_workflow(self, integrated_system_setup):
        """Test complete development workflow orchestration."""
        env = integrated_system_setup
        
        # Simulate complete development workflow
        workflows = [
            {
                "phase": "planning",
                "config": PromptConfig(
                    technologies=["python"],
                    task_type="project planning",
                    task_description="Plan a web scraping application architecture",
                    code_requirements="scalable, maintainable, and well-tested architecture"
                )
            },
            {
                "phase": "implementation",
                "config": PromptConfig(
                    technologies=["python"],
                    task_type="feature implementation",
                    task_description="Implement web scraping engine with rate limiting",
                    code_requirements="robust error handling and configurable rate limits"
                )
            },
            {
                "phase": "testing",
                "config": PromptConfig(
                    technologies=["python"],
                    task_type="test implementation",
                    task_description="Create comprehensive test suite for web scraping engine",
                    code_requirements="unit tests, integration tests, and performance tests"
                )
            }
        ]
        
        generator = PromptGenerator(env["prompts_dir"], env["config_file"], base_path=env["base_path"])
        
        # Execute complete workflow
        workflow_results = []
        for workflow in workflows:
            prompt = generator.generate_prompt(workflow["config"])
            workflow_results.append({
                "phase": workflow["phase"],
                "prompt": prompt,
                "length": len(prompt)
            })
        
        # Verify all phases completed successfully
        assert len(workflow_results) == 3
        
        # Verify each phase has substantial content
        for result in workflow_results:
            assert result["length"] > 500
            assert result["phase"] in result["prompt"].lower()
        
        # Verify phase-specific content
        planning_prompt = workflow_results[0]["prompt"]
        assert "architecture" in planning_prompt.lower()
        
        implementation_prompt = workflow_results[1]["prompt"]
        assert "rate limiting" in implementation_prompt
        
        testing_prompt = workflow_results[2]["prompt"]
        assert "test" in testing_prompt.lower()
        assert "pytest" in testing_prompt  # Python testing tool
    
    def test_cross_technology_workflow(self, integrated_system_setup):
        """Test workflow spanning multiple technologies."""
        env = integrated_system_setup
        
        generator = PromptGenerator(env["prompts_dir"], env["config_file"], base_path=env["base_path"])
        
        # Multi-technology project workflow
        full_stack_config = PromptConfig(
            technologies=["python", "javascript", "react"],
            task_type="full-stack development",
            task_description="Build a real-time chat application with Python backend and React frontend",
            code_requirements="real-time communication, scalable architecture, and responsive UI"
        )
        
        prompt = generator.generate_prompt(full_stack_config)
        
        # Verify comprehensive integration
        assert len(prompt) > 2000  # Should be substantial
        
        # Verify all technologies represented
        assert "python" in prompt.lower()
        assert "javascript" in prompt.lower()
        assert "react" in prompt.lower()
        
        # Verify technology-specific guidance
        assert "pytest" in prompt  # Python testing
        assert "jest" in prompt  # JavaScript testing
        assert "testing-library" in prompt  # React testing
        
        # Verify best practices from all technologies
        assert "Clean Code" in prompt  # Python
        assert "ES6+" in prompt  # JavaScript
        assert "Component Design" in prompt  # React
        
        # Verify workflow coherence
        assert "real-time chat application" in prompt
        assert "responsive UI" in prompt