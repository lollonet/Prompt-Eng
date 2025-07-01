"""
Comprehensive tests for template rendering system.

Tests Jinja2 template loading, rendering, error handling, and integration
with the prompt generation system.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from src.knowledge_manager import KnowledgeManager
from src.prompt_config import PromptConfig
from src.prompt_generator import PromptGenerator


class TestTemplateSystem:
    """Test template loading and rendering functionality."""

    @pytest.fixture
    def setup_template_environment(self, tmp_path):
        """Create comprehensive template test environment."""
        # Create directory structure
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        base_prompts_dir = prompts_dir / "base_prompts"
        base_prompts_dir.mkdir()

        language_specific_dir = prompts_dir / "language_specific"
        language_specific_dir.mkdir()

        framework_specific_dir = prompts_dir / "framework_specific"
        framework_specific_dir.mkdir()

        # Config setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "tech_stack_mapping.json"

        config_data = {
            "python": {
                "best_practices": ["Clean Code", "PEP8", "Testing"],
                "tools": ["pytest", "black", "mypy"],
            },
            "javascript": {
                "best_practices": ["ES6+", "Testing", "Code Quality"],
                "tools": ["jest", "eslint", "prettier"],
            },
            "react": {
                "best_practices": ["Component Design", "State Management"],
                "tools": ["testing-library", "storybook"],
            },
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Knowledge base setup
        kb_dir = tmp_path / "knowledge_base"
        kb_bp_dir = kb_dir / "best_practices"
        kb_bp_dir.mkdir(parents=True)
        kb_tools_dir = kb_dir / "tools"
        kb_tools_dir.mkdir(parents=True)

        # Best practices files
        (kb_bp_dir / "clean_code.md").write_text(
            """
# Clean Code Principles

## Key Guidelines
- Functions should do one thing
- Use meaningful names
- Keep it simple
- Write tests

## Examples
```python
def calculate_total(items):
    return sum(item.price for item in items)
```
        """.strip()
        )

        (kb_bp_dir / "pep8.md").write_text(
            """
# PEP 8 Style Guide

## Formatting Rules
- 4 spaces for indentation
- Line length max 79 characters
- Use snake_case for functions
- Use PascalCase for classes
        """.strip()
        )

        (kb_bp_dir / "testing.md").write_text(
            """
# Testing Best Practices

## Guidelines
- Write tests first (TDD)
- Use descriptive test names
- Test edge cases
- Mock external dependencies
        """.strip()
        )

        # Tools files
        with open(kb_tools_dir / "pytest.json", "w") as f:
            json.dump(
                {
                    "name": "pytest",
                    "description": "Python testing framework",
                    "usage": "pytest tests/",
                    "features": ["fixtures", "parametrization", "mocking"],
                },
                f,
            )

        with open(kb_tools_dir / "black.json", "w") as f:
            json.dump(
                {
                    "name": "black",
                    "description": "Python code formatter",
                    "usage": "black src/",
                    "features": ["automatic formatting", "PEP8 compliance"],
                },
                f,
            )

        return {
            "prompts_dir": str(prompts_dir),
            "config_file": str(config_file),
            "base_path": str(tmp_path),
        }

    def test_basic_template_rendering(self, setup_template_environment):
        """Test basic template rendering with simple substitution."""
        env = setup_template_environment

        # Create a simple template
        template_file = Path(env["prompts_dir"]) / "base_prompts" / "simple.txt"
        template_file.write_text(
            """
You are a {{ role }} developer working with {{ technologies }}.

Task: {{ task_description }}
Requirements: {{ code_requirements }}

Best Practices:
{% for practice in best_practices %}
- {{ practice }}
{% endfor %}

Tools:
{% for tool in tools %}
- {{ tool.name }}: {{ tool.description }}
{% endfor %}
        """.strip()
        )

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        config = PromptConfig(
            technologies=["python"],
            task_type="feature implementation",
            task_description="user authentication system",
            code_requirements="secure, scalable, and well-tested",
            template_name="base_prompts/simple.txt",
        )

        prompt = generator.generate_prompt(config)

        # Verify template rendering
        assert "You are a expert developer working with python" in prompt
        assert "Task: user authentication system" in prompt
        assert "Requirements: secure, scalable, and well-tested" in prompt
        assert "Clean Code Principles" in prompt
        assert "pytest: Python testing framework" in prompt
        assert "black: Python code formatter" in prompt

    def test_template_with_conditional_blocks(self, setup_template_environment):
        """Test template rendering with conditional Jinja2 blocks."""
        env = setup_template_environment

        # Create template with conditionals
        template_file = Path(env["prompts_dir"]) / "base_prompts" / "conditional.txt"
        template_file.write_text(
            """
Developer Profile: {{ role }} specializing in {{ technologies | join(', ') }}

{% if task_type == "feature implementation" %}
## Feature Development Guidelines
- Follow test-driven development
- Implement comprehensive error handling
- Document API interfaces
{% elif task_type == "bug fix" %}
## Bug Fix Guidelines  
- Identify root cause
- Add regression tests
- Verify fix doesn't break existing functionality
{% else %}
## General Development Guidelines
- Follow coding standards
- Write clean, maintainable code
{% endif %}

{% if technologies | length > 1 %}
## Multi-Technology Integration
You're working with multiple technologies. Ensure:
{% for tech in technologies %}
- {{ tech }}: {{ tech_details.get(tech, {}).get('integration_notes', 'Follow standard practices') }}
{% endfor %}
{% endif %}

Task Details:
{{ task_description | title }}

Quality Requirements:
{{ code_requirements | wordwrap(80) }}
        """.strip()
        )

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        # Test feature implementation path
        config = PromptConfig(
            technologies=["python", "javascript"],
            task_type="feature implementation",
            task_description="real-time notifications system",
            code_requirements="The system must be highly scalable, handle websocket connections efficiently, and provide real-time updates with minimal latency.",
            template_name="base_prompts/conditional.txt",
        )

        prompt = generator.generate_prompt(config)

        # Verify conditional rendering
        assert "Feature Development Guidelines" in prompt
        assert "Follow test-driven development" in prompt
        assert "Multi-Technology Integration" in prompt
        assert "Real-Time Notifications System" in prompt  # title case
        assert "highly scalable" in prompt  # wordwrap preserves content

    def test_template_with_filters_and_functions(self, setup_template_environment):
        """Test template rendering with Jinja2 filters and functions."""
        env = setup_template_environment

        # Create template using various filters
        template_file = Path(env["prompts_dir"]) / "base_prompts" / "advanced.txt"
        template_file.write_text(
            """
# {{ task_type | title }} Development Guide

Developer: {{ role | upper }}
Technologies: {{ technologies | join(' + ') | upper }}
Priority: {{ priority | default('MEDIUM') }}

## Task Summary
{{ task_description | wordwrap(60) | indent(4) }}

## Requirements Analysis
{% set req_words = code_requirements.split() %}
Word count: {{ req_words | length }}
{% if req_words | length > 20 %}
This is a complex requirement specification.
{% endif %}

## Technology Stack Details
{% for tech in technologies %}
### {{ tech | title }}
Best Practices: {{ tech_best_practices.get(tech, []) | join(', ') }}
Tools Available: {{ tech_tools.get(tech, []) | length }} tools configured
{% endfor %}

## Implementation Checklist
{% for i in range(1, 6) %}
{{ i }}. Step {{ i }} of implementation
{% endfor %}

## Generated Metadata
- Timestamp: {{ timestamp | default('N/A') }}
- Template: {{ template_name | basename }}
- Config Hash: {{ config_hash | default('unknown') }}
        """.strip()
        )

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        config = PromptConfig(
            technologies=["python", "react"],
            task_type="API development",
            task_description="Build a RESTful API for user management with CRUD operations, authentication, and authorization features.",
            code_requirements="The API must support JSON responses, implement JWT authentication, provide comprehensive error handling, include rate limiting, and maintain high performance with proper caching strategies.",
            template_name="base_prompts/advanced.txt",
        )

        prompt = generator.generate_prompt(config)

        # Verify filters and functions
        assert "# Api Development Development Guide" in prompt
        assert "Developer: EXPERT" in prompt
        assert "Technologies: PYTHON + REACT" in prompt
        assert "Word count: 27" in prompt  # Count of requirement words
        assert "This is a complex requirement specification" in prompt
        assert "### Python" in prompt
        assert "### React" in prompt
        assert "1. Step 1 of implementation" in prompt
        assert "5. Step 5 of implementation" in prompt

    def test_template_inheritance_and_includes(self, setup_template_environment):
        """Test Jinja2 template inheritance and include functionality."""
        env = setup_template_environment

        # Create base template
        base_template = Path(env["prompts_dir"]) / "base.txt"
        base_template.write_text(
            """
# {% block title %}Default Development Guide{% endblock %}

## Developer Information
Role: {{ role }}
Technologies: {{ technologies | join(', ') }}

{% block main_content %}
Default content block
{% endblock %}

## Footer
{% include 'footer.txt' %}
        """.strip()
        )

        # Create footer include
        footer_template = Path(env["prompts_dir"]) / "footer.txt"
        footer_template.write_text(
            """
---
Generated by Prompt Engineering System
Template: {{ template_name }}
Technologies: {{ technologies | length }} configured
        """.strip()
        )

        # Create extending template
        extended_template = Path(env["prompts_dir"]) / "language_specific" / "python_feature.txt"
        extended_template.parent.mkdir(exist_ok=True)
        extended_template.write_text(
            """
{% extends "base.txt" %}

{% block title %}Python Feature Development Guide{% endblock %}

{% block main_content %}
## Python-Specific Guidelines

### Task Requirements
{{ task_description }}

### Code Quality Standards
{{ code_requirements }}

### Best Practices to Follow
{% for practice in best_practices %}
- {{ practice_details.get(practice, practice) }}
{% endfor %}

### Recommended Tools
{% for tool in tools %}
- **{{ tool.name }}**: {{ tool.description }}
  Usage: {{ tool.usage | default('Standard usage') }}
{% endfor %}

### Implementation Steps
1. Set up virtual environment
2. Install dependencies
3. Write tests first (TDD approach)
4. Implement feature logic
5. Run quality checks
6. Update documentation
{% endblock %}
        """.strip()
        )

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        config = PromptConfig(
            technologies=["python"],
            task_type="feature development",
            task_description="Implement a caching layer for database queries",
            code_requirements="Thread-safe, configurable TTL, memory-efficient, and observable",
            template_name="language_specific/python_feature.txt",
        )

        prompt = generator.generate_prompt(config)

        # Verify template inheritance
        assert "# Python Feature Development Guide" in prompt  # Extended title block
        assert "Role: expert" in prompt  # From base template
        assert "Technologies: python" in prompt  # From base template
        assert "Implement a caching layer" in prompt  # Extended content
        assert "Thread-safe, configurable TTL" in prompt  # Extended content
        assert "pytest: Python testing framework" in prompt  # Tool details
        assert "Generated by Prompt Engineering System" in prompt  # Footer include
        assert "Technologies: 1 configured" in prompt  # Footer include with filter

    def test_template_error_handling(self, setup_template_environment):
        """Test template error handling scenarios."""
        env = setup_template_environment

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        # Test missing template - should fallback to generic
        config = PromptConfig(
            technologies=["python"],
            task_type="testing",
            task_description="write unit tests",
            code_requirements="comprehensive test coverage",
            template_name="non_existent_template.txt",
        )

        with patch("src.prompt_generator.logger") as mock_logger:
            prompt = generator.generate_prompt(config)

            # Should fallback to generic template and log warning
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "Template not found" in warning_msg
            assert "falling back to generic" in warning_msg

            # Should still generate a prompt
            assert "expert developer" in prompt.lower()
            assert "python" in prompt

    def test_template_syntax_error_handling(self, setup_template_environment):
        """Test handling of templates with syntax errors."""
        env = setup_template_environment

        # Create template with syntax error
        bad_template = Path(env["prompts_dir"]) / "base_prompts" / "syntax_error.txt"
        bad_template.write_text(
            """
You are a {{ role }} developer.

{% for practice in best_practices %}
- {{ practice }
{% endfor %}

{% if unclosed_block %}
Some content
        """.strip()
        )  # Missing endif and closing }}

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        config = PromptConfig(
            technologies=["python"],
            task_type="development",
            task_description="test syntax error handling",
            code_requirements="handle template errors gracefully",
            template_name="base_prompts/syntax_error.txt",
        )

        # Should handle syntax error gracefully
        with patch("src.prompt_generator.logger") as mock_logger:
            prompt = generator.generate_prompt(config)

            # Should log error and fallback
            mock_logger.error.assert_called()
            error_msg = mock_logger.error.call_args[0][0]
            assert "Template rendering error" in error_msg

            # Should still produce output (fallback template)
            assert len(prompt) > 0

    def test_template_context_variables(self, setup_template_environment):
        """Test all available template context variables."""
        env = setup_template_environment

        # Create template that uses all context variables
        comprehensive_template = Path(env["prompts_dir"]) / "base_prompts" / "context_test.txt"
        comprehensive_template.write_text(
            """
# Template Context Test

## Basic Variables
- Role: {{ role }}
- Technologies: {{ technologies }}
- Task Type: {{ task_type }}
- Task Description: {{ task_description }}
- Code Requirements: {{ code_requirements }}
- Template Name: {{ template_name }}

## Technology Arrays
{% for tech in technologies %}
Technology {{ loop.index }}: {{ tech }}
{% endfor %}

## Best Practices
{% for practice in best_practices %}
Practice {{ loop.index }}: {{ practice }}
{% endfor %}

## Practice Details Dictionary
{% for practice in best_practices %}
{{ practice }}: {{ practice_details.get(practice, 'No details available') }}
{% endfor %}

## Tools Array
{% for tool in tools %}
Tool {{ loop.index }}: {{ tool.name }} - {{ tool.description }}
{% endfor %}

## Technology-Specific Data
{% for tech in technologies %}
### {{ tech | title }}
Best Practices: {{ tech_best_practices.get(tech, []) }}
Tools: {{ tech_tools.get(tech, []) }}
{% endfor %}

## Loop Variables Test
{% for tech in technologies %}
- Index: {{ loop.index }}
- Index0: {{ loop.index0 }}
- First: {{ loop.first }}
- Last: {{ loop.last }}
- Length: {{ loop.length }}
{% endfor %}
        """.strip()
        )

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        config = PromptConfig(
            technologies=["python", "javascript"],
            task_type="full-stack development",
            task_description="build a web application with backend API and frontend",
            code_requirements="responsive design, RESTful API, comprehensive testing",
            template_name="base_prompts/context_test.txt",
        )

        prompt = generator.generate_prompt(config)

        # Verify all context variables are available
        assert "Role: expert" in prompt
        assert "Technologies: ['python', 'javascript']" in prompt
        assert "Task Type: full-stack development" in prompt
        assert "Task Description: build a web application" in prompt
        assert "Code Requirements: responsive design" in prompt
        assert "Template Name: base_prompts/context_test.txt" in prompt

        # Verify loops work
        assert "Technology 1: python" in prompt
        assert "Technology 2: javascript" in prompt
        assert "Practice 1: Clean Code" in prompt

        # Verify practice details lookup
        assert "Clean Code: # Clean Code Principles" in prompt

        # Verify tools
        assert "Tool 1: pytest - Python testing framework" in prompt

        # Verify technology-specific data
        assert "### Python" in prompt
        assert "Best Practices: ['Clean Code', 'PEP8', 'Testing']" in prompt

        # Verify loop variables
        assert "Index: 1" in prompt
        assert "Index0: 0" in prompt
        assert "First: True" in prompt
        assert "Last: False" in prompt
        assert "Length: 2" in prompt

    def test_template_with_missing_context_variables(self, setup_template_environment):
        """Test template behavior with missing context variables."""
        env = setup_template_environment

        # Create template that references undefined variables
        template_file = Path(env["prompts_dir"]) / "base_prompts" / "missing_vars.txt"
        template_file.write_text(
            """
Role: {{ role }}
Undefined Variable: {{ undefined_var }}
Undefined with Default: {{ undefined_var | default('fallback_value') }}
Undefined Dict Access: {{ undefined_dict.nonexistent_key | default('dict_fallback') }}

{% if undefined_condition %}
This should not appear
{% else %}
Undefined condition handled
{% endif %}

{% for item in undefined_list | default([]) %}
Item: {{ item }}
{% endfor %}
        """.strip()
        )

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        config = PromptConfig(
            technologies=["python"],
            task_type="testing undefined variables",
            task_description="test template robustness",
            code_requirements="handle missing context gracefully",
            template_name="base_prompts/missing_vars.txt",
        )

        # Should handle undefined variables gracefully
        prompt = generator.generate_prompt(config)

        # Verify defined variables work
        assert "Role: expert" in prompt

        # Verify undefined variables are handled
        assert "Undefined with Default: fallback_value" in prompt
        assert "dict_fallback" in prompt
        assert "Undefined condition handled" in prompt

        # The undefined_list should be empty, so no items should appear
        assert "Item:" not in prompt

    def test_template_custom_filters(self, setup_template_environment):
        """Test if custom Jinja2 filters work correctly."""
        env = setup_template_environment

        # Create template using various filters
        template_file = Path(env["prompts_dir"]) / "base_prompts" / "filters.txt"
        template_file.write_text(
            """
# Filter Tests

## String Filters
- Title: {{ task_type | title }}
- Upper: {{ task_type | upper }}
- Lower: {{ task_type | lower }}
- Capitalize: {{ task_type | capitalize }}

## List Filters
- Join: {{ technologies | join(' & ') }}
- Length: {{ technologies | length }}
- First: {{ technologies | first }}
- Last: {{ technologies | last }}

## Text Formatting
- Wordwrap: {{ code_requirements | wordwrap(40) }}
- Indent: {{ task_description | indent(4) }}

## Defaults
- With Default: {{ missing_var | default('default_value') }}
- Bool Default: {{ missing_bool | default(true) }}

## Advanced
- Unique: {{ (technologies + technologies) | unique | list }}
- Sort: {{ technologies | sort }}
        """.strip()
        )

        generator = PromptGenerator(
            env["prompts_dir"], env["config_file"], base_path=env["base_path"]
        )

        config = PromptConfig(
            technologies=["python", "javascript", "react"],
            task_type="full stack development",
            task_description="Create a modern web application with Python backend and React frontend",
            code_requirements="The application should be scalable, maintainable, secure, and follow modern development practices with comprehensive testing coverage",
            template_name="base_prompts/filters.txt",
        )

        prompt = generator.generate_prompt(config)

        # Verify filters work correctly
        assert "Title: Full Stack Development" in prompt
        assert "Upper: FULL STACK DEVELOPMENT" in prompt
        assert "Join: python & javascript & react" in prompt
        assert "Length: 3" in prompt
        assert "First: python" in prompt
        assert "Last: react" in prompt
        assert "With Default: default_value" in prompt

        # Verify text formatting
        lines = prompt.split("\n")
        indented_lines = [line for line in lines if line.startswith("    Create a modern")]
        assert len(indented_lines) > 0  # Should have indented content
