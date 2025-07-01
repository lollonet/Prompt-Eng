"""
Comprehensive tests for performance and scalability.

Tests response times, memory usage, concurrent access, caching efficiency,
and system behavior under load conditions.
"""

import asyncio
import json
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.events import Event, EventBus, EventType
from src.knowledge_manager import KnowledgeManager
from src.prompt_config import PromptConfig
from src.prompt_generator import PromptGenerator


class TestPerformanceBenchmarks:
    """Test performance benchmarks and response times."""

    @pytest.fixture
    def performance_test_setup(self, tmp_path):
        """Setup comprehensive test environment for performance testing."""
        # Create directory structure
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "base_prompts").mkdir()
        (prompts_dir / "language_specific").mkdir()

        # Create multiple template files
        base_prompts_dir = prompts_dir / "base_prompts"
        (base_prompts_dir / "generic_code_prompt.txt").write_text(
            """
You are an expert {{ role }} developer working with {{ technologies | join(', ') }}.

## Task: {{ task_type }}
{{ task_description }}

## Requirements
{{ code_requirements }}

## Best Practices
{% for practice in best_practices %}
- {{ practice_details.get(practice, practice) }}
{% endfor %}

## Recommended Tools
{% for tool in tools %}
- **{{ tool.name }}**: {{ tool.description }}
{% endfor %}
        """.strip()
        )

        (base_prompts_dir / "complex_template.txt").write_text(
            """
# {{ task_type | title }} Development Guide

{% for tech in technologies %}
## {{ tech | title }} Implementation

### Best Practices for {{ tech }}
{% for practice in tech_best_practices.get(tech, []) %}
{{ loop.index }}. {{ practice_details.get(practice, practice) }}
{% endfor %}

### Tools for {{ tech }}
{% for tool in tech_tools.get(tech, []) %}
- {{ tool.name }}: {{ tool.description }}
  {% if tool.usage %}Usage: {{ tool.usage }}{% endif %}
{% endfor %}

{% endfor %}

## Implementation Steps
{% for i in range(1, 11) %}
Step {{ i }}: {{ task_description | wordwrap(60) | replace('\n', '\n         ') }}
{% endfor %}

## Quality Checklist
{% set quality_items = ['Testing', 'Documentation', 'Performance', 'Security', 'Maintainability'] %}
{% for item in quality_items %}
- [ ] {{ item }}: {{ code_requirements | truncate(50) }}
{% endfor %}
        """.strip()
        )

        # Create language-specific templates
        lang_dir = prompts_dir / "language_specific" / "python"
        lang_dir.mkdir(parents=True)
        (lang_dir / "feature_template.txt").write_text(
            """
# Python Feature Development

{{ task_description }}

## Python-Specific Guidelines
{% for practice in best_practices %}
### {{ practice }}
{{ practice_details.get(practice, 'Follow standard practices') }}
{% endfor %}

## Code Quality Tools
{% for tool in tools %}
- {{ tool.name }}: {{ tool.description }}
{% endfor %}
        """.strip()
        )

        # Create comprehensive config
        config_file = tmp_path / "config.json"
        config_data = {
            "python": {
                "best_practices": ["Clean Code", "PEP8", "Testing", "SOLID", "Performance"],
                "tools": ["pytest", "black", "mypy", "pylint", "bandit"],
            },
            "javascript": {
                "best_practices": ["ES6+", "Testing", "Code Quality", "Performance"],
                "tools": ["jest", "eslint", "prettier", "webpack"],
            },
            "react": {
                "best_practices": ["Component Design", "State Management", "Performance"],
                "tools": ["testing-library", "storybook", "react-devtools"],
            },
            "docker": {
                "best_practices": ["Multi-stage", "Security", "Optimization"],
                "tools": ["dockerfile", "compose", "buildkit"],
            },
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create knowledge base
        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        # Create comprehensive best practices
        practices = {
            "clean_code": "# Clean Code\n\n" + "Best practice content.\n" * 50,
            "pep8": "# PEP 8\n\n" + "Style guide content.\n" * 30,
            "testing": "# Testing\n\n" + "Testing guidelines.\n" * 40,
            "solid": "# SOLID Principles\n\n" + "SOLID content.\n" * 35,
            "performance": "# Performance\n\n" + "Performance tips.\n" * 45,
            "es6+": "# ES6+ Features\n\n" + "Modern JavaScript.\n" * 25,
            "component_design": "# Component Design\n\n" + "React patterns.\n" * 30,
        }

        for name, content in practices.items():
            (bp_dir / f"{name}.md").write_text(content)

        # Create comprehensive tools
        tools = {
            "pytest": {
                "name": "pytest",
                "description": "Python testing framework",
                "usage": "pytest tests/",
            },
            "black": {
                "name": "black",
                "description": "Python code formatter",
                "usage": "black src/",
            },
            "mypy": {"name": "mypy", "description": "Static type checker", "usage": "mypy src/"},
            "pylint": {
                "name": "pylint",
                "description": "Code analysis tool",
                "usage": "pylint src/",
            },
            "jest": {"name": "jest", "description": "JavaScript testing", "usage": "npm test"},
            "eslint": {
                "name": "eslint",
                "description": "JavaScript linter",
                "usage": "eslint src/",
            },
        }

        for name, data in tools.items():
            with open(tools_dir / f"{name}.json", "w") as f:
                json.dump(data, f)

        return {
            "prompts_dir": str(prompts_dir),
            "config_file": str(config_file),
            "base_path": str(tmp_path),
        }

    def test_prompt_generation_performance(self, performance_test_setup):
        """Test prompt generation performance under various conditions."""
        env = performance_test_setup
        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        # Test simple prompt generation performance
        config = PromptConfig(
            technologies=["python"],
            task_type="simple feature",
            task_description="implement a basic function",
            code_requirements="clean, tested, and well-documented code",
        )

        start_time = time.time()
        prompt = generator.generate_prompt(config)
        simple_duration = time.time() - start_time

        assert len(prompt) > 0
        assert simple_duration < 0.1  # Should complete in under 100ms

        # Test complex prompt generation performance
        config = PromptConfig(
            technologies=["python", "javascript", "react", "docker"],
            task_type="full-stack application development",
            task_description="Build a comprehensive web application with microservices architecture, real-time features, and CI/CD pipeline",
            code_requirements="Scalable, secure, well-tested, containerized, with comprehensive monitoring and logging",
            template_name="base_prompts/complex_template.txt",
        )

        start_time = time.time()
        prompt = generator.generate_prompt(config)
        complex_duration = time.time() - start_time

        assert len(prompt) > 0
        assert complex_duration < 0.5  # Should complete in under 500ms

        # Performance should scale reasonably with complexity
        assert complex_duration < simple_duration * 10

    def test_knowledge_manager_caching_performance(self, performance_test_setup):
        """Test knowledge manager caching performance."""
        env = performance_test_setup
        km = KnowledgeManager(env["config_file"], base_path=env["base_path"])

        # Measure cold cache performance
        start_time = time.time()
        practice1 = km.get_best_practice_details("Clean Code")
        cold_cache_time = time.time() - start_time

        assert practice1 is not None
        assert cold_cache_time < 0.1  # Should load in under 100ms

        # Measure warm cache performance
        start_time = time.time()
        for _ in range(100):
            practice2 = km.get_best_practice_details("Clean Code")
        warm_cache_time = time.time() - start_time

        assert practice2 == practice1
        assert warm_cache_time < 0.01  # 100 cached reads in under 10ms

        # Cache should provide significant speedup
        assert warm_cache_time < cold_cache_time / 10

    def test_concurrent_prompt_generation_performance(self, performance_test_setup):
        """Test performance under concurrent load."""
        env = performance_test_setup
        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        def generate_prompt(i):
            config = PromptConfig(
                technologies=["python"],
                task_type=f"feature {i}",
                task_description=f"implement feature number {i}",
                code_requirements="clean and well-tested code",
            )
            return generator.generate_prompt(config)

        # Test concurrent generation
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate_prompt, i) for i in range(50)]
            results = [future.result() for future in futures]
        total_time = time.time() - start_time

        assert len(results) == 50
        assert all(len(result) > 0 for result in results)
        assert total_time < 5.0  # 50 concurrent generations in under 5 seconds

        # Average time per generation should be reasonable
        avg_time = total_time / 50
        assert avg_time < 0.2  # Average under 200ms per generation


class TestMemoryUsage:
    """Test memory usage and efficiency."""

    def test_knowledge_manager_memory_efficiency(self, tmp_path):
        """Test memory efficiency of knowledge manager caching."""
        # Create large knowledge base
        config_file = tmp_path / "config.json"
        config_data = {}

        # Create 100 technologies with multiple practices each
        for i in range(100):
            tech_name = f"tech_{i}"
            config_data[tech_name] = {
                "best_practices": [f"practice_{j}" for j in range(10)],
                "tools": [f"tool_{j}" for j in range(5)],
            }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create knowledge files
        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        # Create many practice files
        for i in range(100):
            for j in range(10):
                practice_name = f"practice_{j}"
                content = f"# Practice {j}\n\n" + "Content line.\n" * 100
                (bp_dir / f"{practice_name}.md").write_text(content)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Measure memory usage before caching
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Load many knowledge items
        for i in range(10):
            for j in range(10):
                practice_name = f"practice_{j}"
                km.get_best_practice_details(practice_name)

        # Measure memory after caching
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB for this test)
        assert memory_increase < 50 * 1024 * 1024

    def test_template_rendering_memory_efficiency(self, tmp_path):
        """Test memory efficiency of template rendering."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        base_prompts_dir = prompts_dir / "base_prompts"
        base_prompts_dir.mkdir()

        # Create template with large output
        large_template = base_prompts_dir / "large_template.txt"
        template_content = """
{% for tech in technologies %}
## Technology: {{ tech }}
{% for i in range(100) %}
Line {{ i }}: Processing {{ tech }} with detailed information and extensive content.
{% endfor %}
{% endfor %}

## Task Description
{{ task_description }}

## Requirements
{{ code_requirements }}
        """.strip()
        large_template.write_text(template_content)

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Measure memory during large template rendering
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        config = PromptConfig(
            technologies=["python", "javascript", "react"],
            task_type="large template test",
            task_description="Test memory efficiency with large template output",
            code_requirements="Memory usage should remain reasonable even with large outputs",
            template_name="base_prompts/large_template.txt",
        )

        prompt = generator.generate_prompt(config)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        assert len(prompt) > 10000  # Should produce large output
        # Memory increase should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase


class TestScalability:
    """Test system scalability and limits."""

    def test_large_technology_list_handling(self, tmp_path):
        """Test handling of large technology lists."""
        # Create config with many technologies
        config_file = tmp_path / "config.json"
        config_data = {}

        # 50 technologies
        for i in range(50):
            tech_name = f"technology_{i}"
            config_data[tech_name] = {
                "best_practices": [f"bp_{j}" for j in range(5)],
                "tools": [f"tool_{j}" for j in range(3)],
            }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Setup prompts
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        base_prompts_dir = prompts_dir / "base_prompts"
        base_prompts_dir.mkdir()

        template = base_prompts_dir / "multi_tech.txt"
        template.write_text(
            """
Technologies: {{ technologies | join(', ') }}
Task: {{ task_type }}

{% for tech in technologies %}
## {{ tech }}
Best Practices: {{ tech_best_practices.get(tech, []) | join(', ') }}
{% endfor %}
        """.strip()
        )

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Test with many technologies
        many_technologies = [f"technology_{i}" for i in range(25)]

        config = PromptConfig(
            technologies=many_technologies,
            task_type="multi-technology project",
            task_description="Handle many technologies efficiently",
            code_requirements="System should scale to handle many technologies",
            template_name="base_prompts/multi_tech.txt",
        )

        start_time = time.time()
        prompt = generator.generate_prompt(config)
        duration = time.time() - start_time

        assert len(prompt) > 0
        assert duration < 2.0  # Should handle 25 technologies in under 2 seconds

        # Verify all technologies are included
        for tech in many_technologies[:10]:  # Check first 10
            assert tech in prompt

    def test_repeated_access_patterns(self, tmp_path):
        """Test performance with repeated access patterns."""
        # Setup environment
        config_file = tmp_path / "config.json"
        config_data = {
            "python": {"best_practices": ["Clean Code", "Testing"], "tools": ["pytest"]},
            "javascript": {"best_practices": ["ES6+"], "tools": ["jest"]},
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        (bp_dir / "clean_code.md").write_text("Clean code content")
        (bp_dir / "testing.md").write_text("Testing content")
        (bp_dir / "es6+.md").write_text("ES6+ content")

        with open(tools_dir / "pytest.json", "w") as f:
            json.dump({"name": "pytest", "description": "Testing framework"}, f)
        with open(tools_dir / "jest.json", "w") as f:
            json.dump({"name": "jest", "description": "JS testing"}, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Simulate repeated access patterns
        start_time = time.time()
        for i in range(1000):
            # Alternate between different access patterns
            if i % 3 == 0:
                km.get_best_practice_details("Clean Code")
                km.get_tool_details("pytest")
            elif i % 3 == 1:
                km.get_best_practice_details("Testing")
                km.get_tool_details("jest")
            else:
                km.get_best_practice_details("ES6+")

        total_time = time.time() - start_time

        # 1000 operations should complete quickly due to caching
        assert total_time < 0.5  # Under 500ms for 1000 cached operations


class TestConcurrency:
    """Test concurrent access and thread safety."""

    def test_knowledge_manager_thread_safety(self, tmp_path):
        """Test thread safety of knowledge manager."""
        # Setup
        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["Clean Code"], "tools": ["pytest"]}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        (bp_dir / "clean_code.md").write_text("Clean code practices")
        with open(tools_dir / "pytest.json", "w") as f:
            json.dump({"name": "pytest", "description": "Testing framework"}, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        results = []
        errors = []

        def worker():
            try:
                for i in range(100):
                    practice = km.get_best_practice_details("Clean Code")
                    tool = km.get_tool_details("pytest")
                    results.append((practice, tool))
            except Exception as e:
                errors.append(e)

        # Run multiple threads concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors and consistent results
        assert len(errors) == 0
        assert len(results) == 1000  # 10 threads * 100 iterations

        # All results should be consistent
        first_result = results[0]
        assert all(result == first_result for result in results)

    def test_prompt_generator_concurrent_access(self, tmp_path):
        """Test concurrent access to prompt generator."""
        # Setup
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "base_prompts").mkdir()

        template = prompts_dir / "base_prompts" / "generic_code_prompt.txt"
        template.write_text("Role: {{ role }}, Tech: {{ technologies }}, Task: {{ task_type }}")

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        results = []
        errors = []

        def generate_prompts(thread_id):
            try:
                for i in range(50):
                    config = PromptConfig(
                        technologies=["python"],
                        task_type=f"task_{thread_id}_{i}",
                        task_description=f"description for thread {thread_id} iteration {i}",
                        code_requirements="concurrent testing requirements",
                    )
                    prompt = generator.generate_prompt(config)
                    results.append((thread_id, i, prompt))
            except Exception as e:
                errors.append((thread_id, e))

        # Run concurrent prompt generation
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=generate_prompts, args=(thread_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 250  # 5 threads * 50 iterations

        # Verify each prompt is correct for its thread/iteration
        for thread_id, iteration, prompt in results:
            assert f"task_{thread_id}_{iteration}" in prompt


class TestEventSystemPerformance:
    """Test event system performance and scalability."""

    @pytest.mark.asyncio
    async def test_event_publishing_performance(self):
        """Test event publishing performance."""
        event_bus = EventBus()

        # Setup multiple handlers
        received_events = []

        async def fast_handler(event):
            received_events.append(event)

        async def slow_handler(event):
            await asyncio.sleep(0.001)  # 1ms delay
            received_events.append(event)

        # Subscribe handlers
        event_bus.subscribe(EventType.SYSTEM_ERROR, fast_handler)
        event_bus.subscribe(EventType.SYSTEM_ERROR, slow_handler)

        # Measure bulk event publishing
        events = [Event(EventType.SYSTEM_ERROR, f"Source{i}") for i in range(100)]

        start_time = time.time()
        for event in events:
            await event_bus.publish(event)
        total_time = time.time() - start_time

        # Should handle 100 events quickly
        assert total_time < 1.0  # Under 1 second for 100 events
        assert len(received_events) == 200  # 2 handlers * 100 events

    @pytest.mark.asyncio
    async def test_event_handler_concurrency(self):
        """Test concurrent event handler execution."""
        event_bus = EventBus()

        handler_times = []

        async def timed_handler(event):
            start = time.time()
            await asyncio.sleep(0.01)  # 10ms work
            handler_times.append(time.time() - start)

        # Subscribe multiple handlers
        for i in range(5):
            event_bus.subscribe(EventType.TEMPLATE_RENDERED, timed_handler)

        # Publish event
        test_event = Event(EventType.TEMPLATE_RENDERED, "TestSource")

        start_time = time.time()
        await event_bus.publish(test_event)
        total_time = time.time() - start_time

        # Handlers should run concurrently
        assert len(handler_times) == 5
        assert total_time < 0.02  # Should be closer to 10ms than 50ms due to concurrency

        # Each handler should take about 10ms
        for handler_time in handler_times:
            assert 0.005 < handler_time < 0.02  # Between 5ms and 20ms

    def test_event_history_performance(self):
        """Test event history performance with large numbers of events."""
        event_bus = EventBus()

        # Publish many events
        start_time = time.time()
        for i in range(10000):
            event = Event(EventType.KNOWLEDGE_CACHE_HIT, f"Source{i}")
            asyncio.run(event_bus.publish(event))
        publish_time = time.time() - start_time

        # Should handle 10k events reasonably quickly
        assert publish_time < 5.0  # Under 5 seconds

        # Test history retrieval performance
        start_time = time.time()
        all_history = event_bus.get_event_history()
        history_time = time.time() - start_time

        assert len(all_history) == 1000  # Limited by max_history_size
        assert history_time < 0.1  # Under 100ms to retrieve history

        # Test filtered history performance
        start_time = time.time()
        cache_events = event_bus.get_event_history(EventType.KNOWLEDGE_CACHE_HIT)
        filter_time = time.time() - start_time

        assert len(cache_events) == 1000
        assert filter_time < 0.1  # Under 100ms to filter history


class TestResourceLimits:
    """Test system behavior at resource limits."""

    def test_maximum_template_complexity(self, tmp_path):
        """Test handling of very complex templates."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        base_prompts_dir = prompts_dir / "base_prompts"
        base_prompts_dir.mkdir()

        # Create extremely complex template
        complex_template = base_prompts_dir / "extreme_template.txt"
        template_content = """
{% for tech in technologies %}
{% for i in range(50) %}
## Section {{ i }} for {{ tech }}
{% for j in range(10) %}
### Subsection {{ i }}.{{ j }}
Content for {{ tech }} section {{ i }} subsection {{ j }}
{% for k in range(5) %}
- Item {{ k }}: {{ task_description | truncate(20) }}
{% endfor %}
{% endfor %}
{% endfor %}
{% endfor %}

Final content: {{ code_requirements }}
        """.strip()
        complex_template.write_text(template_content)

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        config = PromptConfig(
            technologies=["python", "javascript"],
            task_type="extreme complexity test",
            task_description="Testing template complexity limits",
            code_requirements="System should handle complex templates gracefully",
            template_name="base_prompts/extreme_template.txt",
        )

        # Should handle complex template without hanging
        start_time = time.time()
        prompt = generator.generate_prompt(config)
        duration = time.time() - start_time

        assert len(prompt) > 0
        assert duration < 10.0  # Should complete within 10 seconds

    def test_memory_pressure_handling(self, tmp_path):
        """Test system behavior under memory pressure."""
        # This test creates memory pressure and verifies graceful handling

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["Large"], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        kb_dir = tmp_path / "knowledge_base" / "best_practices"
        kb_dir.mkdir(parents=True)

        # Create very large knowledge file
        large_content = "# Large Practice\n\n" + "Content line with data.\n" * 100000
        (kb_dir / "large.md").write_text(large_content)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Load large content multiple times
        start_time = time.time()
        for i in range(10):
            content = km.get_best_practice_details("Large")
            assert content is not None
            assert len(content) > 1000000

        duration = time.time() - start_time

        # Should handle large content efficiently due to caching
        assert duration < 1.0  # First load + 9 cached loads should be fast
