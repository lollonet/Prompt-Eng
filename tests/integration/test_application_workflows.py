"""
Comprehensive end-to-end tests for real application workflows.

Tests complete user scenarios with realistic technology combinations,
ensuring the application delivers business value in production scenarios.
"""

import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, mock_open, patch

import pytest

from src.knowledge_manager import KnowledgeManager
from src.prompt_config import PromptConfig
from src.prompt_generator import PromptGenerator


class TestRealWorldWorkflows:
    """Test real-world development scenarios end-to-end."""

    @pytest.fixture
    def realistic_knowledge_base(self, tmp_path):
        """Create realistic knowledge base for integration testing."""
        # Create comprehensive tech stack mapping
        config_data = {
            "python": {
                "best_practices": ["PEP8", "Clean Code", "SOLID Principles", "Testing"],
                "tools": ["pytest", "black", "mypy", "pylint"],
            },
            "fastapi": {
                "best_practices": ["API Design", "Documentation", "Validation"],
                "tools": ["pydantic", "uvicorn", "swagger"],
            },
            "postgresql": {
                "best_practices": ["Database Design", "Query Optimization", "Security"],
                "tools": ["psycopg2", "alembic", "sqlalchemy"],
            },
            "react": {
                "best_practices": ["Component Design", "State Management", "Performance"],
                "tools": ["jest", "testing-library", "eslint"],
            },
            "typescript": {
                "best_practices": ["Type Safety", "Interface Design", "Error Handling"],
                "tools": ["tsc", "ts-node", "ts-jest"],
            },
            "docker": {
                "best_practices": ["Containerization", "Multi-stage Builds", "Security"],
                "tools": ["dockerfile", "docker-compose", "buildkit"],
            },
            "kubernetes": {
                "best_practices": ["Orchestration", "Resource Management", "Monitoring"],
                "tools": ["kubectl", "helm", "kustomize"],
            },
            "aws": {
                "best_practices": ["Cloud Architecture", "Cost Optimization", "Security"],
                "tools": ["terraform", "cloudformation", "aws-cli"],
            },
        }

        # Save config
        config_file = tmp_path / "config" / "tech_stack_mapping.json"
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create detailed knowledge files
        bp_dir = tmp_path / "knowledge_base" / "best_practices"
        bp_dir.mkdir(parents=True, exist_ok=True)

        # Python best practices
        (bp_dir / "pep8.md").write_text(
            """
# PEP 8 Style Guide for Python Code

## Key Principles
- Use 4 spaces for indentation
- Lines should be max 79 characters
- Use snake_case for variables and functions
- Use PascalCase for classes
- Import statements at top of file

## Code Examples
```python
def calculate_total_price(base_price: float, tax_rate: float) -> float:
    return base_price * (1 + tax_rate)
```
        """
        )

        (bp_dir / "clean_code.md").write_text(
            """
# Clean Code Principles

## Core Concepts
- Functions should do one thing
- Use meaningful names
- Keep functions small (< 20 lines)
- Minimize dependencies
- Write tests first

## Examples
- Use descriptive variable names: `user_count` not `cnt`
- Extract complex logic into separate functions
- Use type hints for clarity
        """
        )

        # FastAPI best practices
        (bp_dir / "api_design.md").write_text(
            """
# FastAPI Best Practices

## API Design
- Use RESTful conventions
- Implement proper HTTP status codes
- Use Pydantic models for validation
- Document with OpenAPI/Swagger
- Implement proper error handling

## Example Structure
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="User API", version="1.0.0")

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users/", status_code=201)
async def create_user(user: UserCreate):
    # Implementation here
    pass
```
        """
        )

        # Tools directory
        tools_dir = tmp_path / "knowledge_base" / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Python tools
        (tools_dir / "pytest.json").write_text(
            json.dumps(
                {
                    "name": "pytest",
                    "description": "Testing framework for Python",
                    "usage": "pytest tests/",
                    "features": ["fixtures", "parametrization", "mocking", "coverage"],
                }
            )
        )

        (tools_dir / "black.json").write_text(
            json.dumps(
                {
                    "name": "Black",
                    "description": "Code formatter for Python",
                    "usage": "black src/",
                    "features": ["automatic formatting", "PEP 8 compliant", "fast"],
                }
            )
        )

        # FastAPI tools
        (tools_dir / "pydantic.json").write_text(
            json.dumps(
                {
                    "name": "Pydantic",
                    "description": "Data validation using Python type hints",
                    "usage": "from pydantic import BaseModel",
                    "features": ["validation", "serialization", "IDE support"],
                }
            )
        )

        # Create realistic templates
        templates_dir = tmp_path / "prompts"
        templates_dir.mkdir(exist_ok=True)

        # Base template
        base_dir = templates_dir / "base_prompts"
        base_dir.mkdir(exist_ok=True)
        (base_dir / "generic_code_prompt.txt").write_text(
            """
You are an expert developer working with {{ technologies | join(', ') }}.

## Task: {{ task_type }}
{{ task_description }}

## Requirements
{{ code_requirements }}

## Best Practices to Follow
{% for practice in best_practices %}
- {{ practice }}
{% endfor %}

## Recommended Tools
{% for tool in tools %}
- {{ tool.name }}: {{ tool.description }}
{% endfor %}

## Implementation Guidelines
- Write clean, maintainable code
- Include comprehensive error handling
- Add appropriate documentation
- Follow security best practices
- Implement proper testing

Please provide a complete, production-ready implementation.
        """
        )

        # Language-specific template
        lang_dir = templates_dir / "language_specific" / "python"
        lang_dir.mkdir(parents=True, exist_ok=True)
        (lang_dir / "api_development.txt").write_text(
            """
You are a senior Python developer specializing in API development.

## Task: {{ task_type }}
{{ task_description }}

## Technical Requirements
{{ code_requirements }}

## Python Best Practices
{% for practice in best_practices %}
### {{ practice }}
{{ practice_details.get(practice, 'Follow standard practices') }}
{% endfor %}

## Development Tools
{% for tool in tools %}
- **{{ tool.name }}**: {{ tool.description }}
  Usage: {{ tool.usage }}
{% endfor %}

## Implementation Structure
1. Define Pydantic models for request/response
2. Implement FastAPI endpoints with proper decorators
3. Add comprehensive error handling
4. Include input validation
5. Write unit and integration tests
6. Add OpenAPI documentation

Please provide:
- Complete API implementation
- Pydantic models
- Error handling
- Basic tests
- Docker configuration if needed
        """
        )

        return str(config_file), str(tmp_path)

    def test_python_fastapi_postgresql_fullstack(self, realistic_knowledge_base):
        """Test complete fullstack Python application workflow."""
        config_file, base_path = realistic_knowledge_base

        config = PromptConfig(
            technologies=["python", "fastapi", "postgresql"],
            task_type="api_development",
            task_description="User management system with authentication",
            code_requirements="REST API with JWT authentication, user CRUD operations, PostgreSQL database, input validation, error handling, comprehensive testing",
            template_name="language_specific/python/api_development.txt",
        )

        generator = PromptGenerator(prompts_dir=f"{base_path}/prompts", config_path=config_file)

        start_time = time.perf_counter()
        prompt = generator.generate_prompt(config)
        generation_time = time.perf_counter() - start_time

        # Performance validation
        assert generation_time < 2.0, f"Generation took {generation_time:.2f}s, should be < 2s"

        # Content validation - all technologies present
        assert "python" in prompt.lower()
        assert "fastapi" in prompt.lower()
        assert "postgresql" in prompt.lower()

        # Business requirements validation
        assert "user management" in prompt.lower()
        assert "authentication" in prompt.lower()
        assert "jwt" in prompt.lower()
        assert "crud" in prompt.lower()

        # Best practices validation
        assert "PEP 8" in prompt or "pep8" in prompt.lower()
        assert "clean code" in prompt.lower()
        assert "testing" in prompt.lower()

        # Tools validation
        assert "pytest" in prompt.lower()
        assert "pydantic" in prompt.lower()
        assert "black" in prompt.lower()

        # Structure validation
        assert len(prompt) > 2000, "Prompt should be comprehensive (>2000 chars)"
        assert "implementation" in prompt.lower()
        assert "error handling" in prompt.lower()
        assert "validation" in prompt.lower()

        # Template-specific validation
        assert "senior python developer" in prompt.lower()
        assert "api development" in prompt.lower()

    def test_react_typescript_frontend_workflow(self, realistic_knowledge_base):
        """Test React TypeScript frontend development workflow."""
        config_file, base_path = realistic_knowledge_base

        config = PromptConfig(
            technologies=["react", "typescript"],
            task_type="frontend_development",
            task_description="E-commerce product catalog with shopping cart",
            code_requirements="Responsive design, TypeScript interfaces, React hooks, state management, component testing, accessibility",
            template_name="base_prompts/generic_code_prompt.txt",
        )

        generator = PromptGenerator(prompts_dir=f"{base_path}/prompts", config_path=config_file)

        prompt = generator.generate_prompt(config)

        # Technology validation
        assert "react" in prompt.lower()
        assert "typescript" in prompt.lower()

        # Business requirements validation
        assert "e-commerce" in prompt.lower()
        assert "product catalog" in prompt.lower()
        assert "shopping cart" in prompt.lower()

        # Technical requirements validation
        assert "responsive" in prompt.lower()
        assert "hooks" in prompt.lower()
        assert "accessibility" in prompt.lower()

        # Best practices validation
        assert "component design" in prompt.lower()
        assert "type safety" in prompt.lower()

        # Tools validation
        assert "jest" in prompt.lower()
        assert "testing-library" in prompt.lower()

    def test_devops_kubernetes_aws_infrastructure(self, realistic_knowledge_base):
        """Test DevOps infrastructure workflow."""
        config_file, base_path = realistic_knowledge_base

        config = PromptConfig(
            technologies=["docker", "kubernetes", "aws"],
            task_type="infrastructure_development",
            task_description="Microservices deployment pipeline",
            code_requirements="Container orchestration, auto-scaling, monitoring, CI/CD pipeline, security best practices, cost optimization",
            template_name="base_prompts/generic_code_prompt.txt",
        )

        generator = PromptGenerator(prompts_dir=f"{base_path}/prompts", config_path=config_file)

        prompt = generator.generate_prompt(config)

        # Technology validation
        assert "docker" in prompt.lower()
        assert "kubernetes" in prompt.lower()
        assert "aws" in prompt.lower()

        # Business requirements validation
        assert "microservices" in prompt.lower()
        assert "pipeline" in prompt.lower()
        assert "deployment" in prompt.lower()

        # Technical requirements validation
        assert "orchestration" in prompt.lower()
        assert "scaling" in prompt.lower()
        assert "monitoring" in prompt.lower()
        assert "ci/cd" in prompt.lower()

        # Best practices validation
        assert "containerization" in prompt.lower()
        assert "security" in prompt.lower()
        assert "optimization" in prompt.lower()

        # Tools validation
        assert "kubectl" in prompt.lower()
        assert "terraform" in prompt.lower()

    def test_complex_multi_technology_aggregation(self, realistic_knowledge_base):
        """Test complex scenario with many technologies."""
        config_file, base_path = realistic_knowledge_base

        config = PromptConfig(
            technologies=[
                "python",
                "fastapi",
                "react",
                "typescript",
                "postgresql",
                "docker",
                "kubernetes",
                "aws",
            ],
            task_type="full_stack_development",
            task_description="Complete enterprise application",
            code_requirements="Microservices architecture, containerized deployment, cloud-native, scalable, secure, monitored",
            template_name="base_prompts/generic_code_prompt.txt",
        )

        generator = PromptGenerator(prompts_dir=f"{base_path}/prompts", config_path=config_file)

        start_time = time.perf_counter()
        prompt = generator.generate_prompt(config)
        generation_time = time.perf_counter() - start_time

        # Performance with complex scenario
        assert (
            generation_time < 3.0
        ), f"Complex generation took {generation_time:.2f}s, should be < 3s"

        # All technologies should be present
        all_techs = [
            "python",
            "fastapi",
            "react",
            "typescript",
            "postgresql",
            "docker",
            "kubernetes",
            "aws",
        ]
        for tech in all_techs:
            assert tech in prompt.lower(), f"Technology {tech} missing from prompt"

        # Should aggregate best practices from all technologies
        expected_practices = [
            "PEP8",
            "API Design",
            "Component Design",
            "Type Safety",
            "Database Design",
            "Containerization",
            "Orchestration",
            "Cloud Architecture",
        ]
        practices_found = sum(
            1 for practice in expected_practices if practice.lower() in prompt.lower()
        )
        assert practices_found >= 6, f"Only {practices_found}/8 expected practices found"

        # Should include tools from all technologies
        expected_tools = [
            "pytest",
            "pydantic",
            "jest",
            "tsc",
            "psycopg2",
            "dockerfile",
            "kubectl",
            "terraform",
        ]
        tools_found = sum(1 for tool in expected_tools if tool.lower() in prompt.lower())
        assert tools_found >= 6, f"Only {tools_found}/8 expected tools found"

        # Content should be substantial for complex project
        assert len(prompt) > 3000, "Complex project prompt should be very comprehensive"


class TestKnowledgeAggregationLogic:
    """Test knowledge aggregation and deduplication logic."""

    @pytest.fixture
    def overlapping_knowledge_base(self, tmp_path):
        """Create knowledge base with overlapping technologies."""
        config_data = {
            "python": {
                "best_practices": ["Clean Code", "Testing", "PEP8"],
                "tools": ["pytest", "black"],
            },
            "django": {
                "best_practices": ["Clean Code", "Testing", "MVC Pattern"],  # Overlap with python
                "tools": ["pytest", "django-test"],  # Overlap with python
            },
            "fastapi": {
                "best_practices": [
                    "Clean Code",
                    "API Design",
                    "Documentation",
                ],  # Overlap with python
                "tools": ["pytest", "pydantic"],  # Overlap with python
            },
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        return str(config_file), str(tmp_path)

    def test_knowledge_deduplication(self, overlapping_knowledge_base):
        """Test that overlapping knowledge is properly deduplicated."""
        config_file, base_path = overlapping_knowledge_base

        generator = PromptGenerator(config_path=config_file)

        # Test with overlapping technologies
        tech_data = generator._collect_technology_data(["python", "django", "fastapi"])

        # Verify best practices deduplication
        best_practices = tech_data.get("best_practices", [])
        unique_practices = set(best_practices)
        assert len(best_practices) == len(unique_practices), "Best practices should be deduplicated"

        # Should contain all unique practices
        expected_practices = {
            "Clean Code",
            "Testing",
            "PEP8",
            "MVC Pattern",
            "API Design",
            "Documentation",
        }
        actual_practices = set(best_practices)
        assert expected_practices.issubset(
            actual_practices
        ), f"Missing practices: {expected_practices - actual_practices}"

        # Verify tools deduplication
        tools = tech_data.get("tools", [])
        unique_tools = set(tool["name"] if isinstance(tool, dict) else tool for tool in tools)
        assert len(tools) == len(unique_tools), "Tools should be deduplicated"

        # Should contain all unique tools
        expected_tools = {"pytest", "black", "django-test", "pydantic"}
        actual_tool_names = {tool["name"] if isinstance(tool, dict) else tool for tool in tools}
        assert expected_tools.issubset(
            actual_tool_names
        ), f"Missing tools: {expected_tools - actual_tool_names}"

    def test_knowledge_aggregation_order_consistency(self, overlapping_knowledge_base):
        """Test that knowledge aggregation order is consistent."""
        config_file, base_path = overlapping_knowledge_base

        generator = PromptGenerator(config_path=config_file)

        # Test same technologies in different orders
        tech_data_1 = generator._collect_technology_data(["python", "django", "fastapi"])
        tech_data_2 = generator._collect_technology_data(["fastapi", "python", "django"])
        tech_data_3 = generator._collect_technology_data(["django", "fastapi", "python"])

        # Results should be equivalent regardless of input order
        practices_1 = set(tech_data_1.get("best_practices", []))
        practices_2 = set(tech_data_2.get("best_practices", []))
        practices_3 = set(tech_data_3.get("best_practices", []))

        assert (
            practices_1 == practices_2 == practices_3
        ), "Best practices should be consistent regardless of technology order"

        # Tools should also be consistent
        tools_1 = {
            tool["name"] if isinstance(tool, dict) else tool
            for tool in tech_data_1.get("tools", [])
        }
        tools_2 = {
            tool["name"] if isinstance(tool, dict) else tool
            for tool in tech_data_2.get("tools", [])
        }
        tools_3 = {
            tool["name"] if isinstance(tool, dict) else tool
            for tool in tech_data_3.get("tools", [])
        }

        assert (
            tools_1 == tools_2 == tools_3
        ), "Tools should be consistent regardless of technology order"


class TestTemplateSystemComprehensive:
    """Comprehensive tests for template system functionality."""

    @pytest.fixture
    def complex_template_setup(self, tmp_path):
        """Create complex template hierarchy for testing."""
        templates_dir = tmp_path / "prompts"

        # Base template with inheritance
        base_dir = templates_dir / "base_prompts"
        base_dir.mkdir(parents=True)
        (base_dir / "base_template.txt").write_text(
            """
{% block header %}
You are an expert developer.
{% endblock %}

## Task: {{ task_type }}
{% block task_description %}
{{ task_description }}
{% endblock %}

{% block requirements %}
## Requirements
{{ code_requirements }}
{% endblock %}

{% block best_practices %}
## Best Practices
{% for practice in best_practices %}
- {{ practice }}
{% endfor %}
{% endblock %}

{% block tools %}
## Tools
{% for tool in tools %}
- {{ tool.name if tool.name is defined else tool }}: {{ tool.description if tool.description is defined else 'Professional development tool' }}
{% endfor %}
{% endblock %}

{% block footer %}
Provide a complete, production-ready solution.
{% endblock %}
        """
        )

        # Generic template
        (base_dir / "generic_code_prompt.txt").write_text(
            """
You are an expert developer working with {{ technologies | join(', ') }}.

## Task: {{ task_type }}
{{ task_description }}

## Requirements
{{ code_requirements }}

## Best Practices to Follow
{% for practice in best_practices %}
- {{ practice }}
{% endfor %}

## Recommended Tools
{% for tool in tools %}
- {{ tool.name if tool.name is defined else tool }}: {{ tool.description if tool.description is defined else 'Development tool' }}
{% endfor %}

Please provide a complete implementation following these guidelines.
        """
        )

        # Language-specific templates
        python_dir = templates_dir / "language_specific" / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "web_development.txt").write_text(
            """
{% extends "base_prompts/base_template.txt" %}

{% block header %}
You are a senior Python web developer with expertise in {{ technologies | join(', ') }}.
{% endblock %}

{% block task_description %}
{{ task_description }}

### Python-specific considerations:
- Follow PEP 8 style guidelines
- Use type hints for better code clarity
- Implement proper error handling
- Include comprehensive docstrings
{% endblock %}

{% block footer %}
Provide:
1. Complete Python implementation
2. Requirements.txt file
3. Basic tests with pytest
4. Documentation
{% endblock %}
        """
        )

        # Framework-specific templates
        framework_dir = templates_dir / "framework_specific"
        react_dir = framework_dir / "react"
        react_dir.mkdir(parents=True)
        (react_dir / "component_development.txt").write_text(
            """
You are a React specialist focusing on {{ technologies | join(', ') }}.

## Component Development: {{ task_type }}
{{ task_description }}

## Technical Requirements
{{ code_requirements }}

## React Best Practices
{% for practice in best_practices %}
- {{ practice }}
{% endfor %}

## Development Tools
{% for tool in tools %}
- **{{ tool.name if tool.name is defined else tool }}**: {{ tool.description if tool.description is defined else 'React development tool' }}
{% endfor %}

## Implementation Guidelines
1. Use functional components with hooks
2. Implement proper TypeScript interfaces
3. Add comprehensive PropTypes or TypeScript types
4. Include accessibility features
5. Write unit tests with React Testing Library
6. Optimize for performance (memo, useMemo, useCallback)

Please provide:
- Component implementation
- TypeScript interfaces
- Unit tests
- Storybook stories (if applicable)
        """
        )

        return str(templates_dir)

    def test_template_fallback_mechanism(self, complex_template_setup):
        """Test template fallback when specific templates don't exist."""
        templates_dir = complex_template_setup

        generator = PromptGenerator(prompts_dir=templates_dir)

        config = PromptConfig(
            technologies=["python"],
            task_type="test_task",
            task_description="test description",
            code_requirements="test requirements that are long enough",
            template_name="non_existent_template.txt",  # This doesn't exist
        )

        # Should fall back to generic template
        prompt = generator.generate_prompt(config)

        assert prompt is not None
        assert len(prompt) > 100
        assert "expert developer working with python" in prompt.lower()
        assert "test_task" in prompt
        assert "test description" in prompt

    def test_template_with_complex_data_structures(self, complex_template_setup):
        """Test template rendering with complex nested data."""
        templates_dir = complex_template_setup

        generator = PromptGenerator(prompts_dir=templates_dir)

        # Mock complex knowledge data
        with patch.object(generator, "_collect_technology_data") as mock_collect:
            mock_collect.return_value = {
                "best_practices": ["Clean Code", "Testing", "Documentation"],
                "tools": [
                    {
                        "name": "pytest",
                        "description": "Testing framework",
                        "usage": "pytest tests/",
                    },
                    {"name": "black", "description": "Code formatter", "usage": "black src/"},
                    "simple_tool_name",  # Mix of objects and strings
                ],
            }

            config = PromptConfig(
                technologies=["python"],
                task_type="complex_testing",
                task_description="Complex data structure handling",
                code_requirements="Handle mixed data types in templates",
                template_name="base_prompts/generic_code_prompt.txt",
            )

            prompt = generator.generate_prompt(config)

            # Verify complex data is handled correctly
            assert "pytest: Testing framework" in prompt
            assert "black: Code formatter" in prompt
            assert "simple_tool_name: Development tool" in prompt  # Fallback for string
            assert "Clean Code" in prompt
            assert "Testing" in prompt
            assert "Documentation" in prompt

    def test_template_context_building_comprehensive(self, complex_template_setup):
        """Test comprehensive template context building."""
        templates_dir = complex_template_setup

        generator = PromptGenerator(prompts_dir=templates_dir)

        config = PromptConfig(
            technologies=["python", "django"],
            task_type="web_application",
            task_description="E-commerce platform",
            code_requirements="Scalable, secure, well-tested application",
            template_name="language_specific/python/web_development.txt",
        )

        # Mock knowledge data
        mock_tech_data = {
            "best_practices": ["Clean Code", "Security", "Performance"],
            "tools": [
                {"name": "pytest", "description": "Testing framework"},
                {"name": "django", "description": "Web framework"},
            ],
        }

        context = generator._build_template_context(config, mock_tech_data)

        # Verify all expected context keys
        expected_keys = [
            "technologies",
            "task_type",
            "task_description",
            "code_requirements",
            "best_practices",
            "tools",
        ]

        for key in expected_keys:
            assert key in context, f"Missing context key: {key}"

        # Verify context values
        assert context["technologies"] == ["python", "django"]
        assert context["task_type"] == "web_application"
        assert context["task_description"] == "E-commerce platform"
        assert context["code_requirements"] == "Scalable, secure, well-tested application"
        assert context["best_practices"] == ["Clean Code", "Security", "Performance"]
        assert len(context["tools"]) == 2

    def test_template_inheritance_and_blocks(self, complex_template_setup):
        """Test template inheritance functionality."""
        templates_dir = complex_template_setup

        generator = PromptGenerator(prompts_dir=templates_dir)

        config = PromptConfig(
            technologies=["python", "django"],
            task_type="web_development",
            task_description="Django application",
            code_requirements="Follow Django best practices",
            template_name="language_specific/python/web_development.txt",
        )

        # Note: This test depends on the template system supporting inheritance
        # If Jinja2 inheritance is not set up, this will test the non-inheritance version
        prompt = generator.generate_prompt(config)

        assert "senior Python web developer" in prompt
        assert "PEP 8 style guidelines" in prompt
        assert "type hints" in prompt
        assert "Requirements.txt file" in prompt
        assert "pytest" in prompt


class TestErrorHandlingAndResilience:
    """Test error handling and system resilience."""

    def test_corrupted_knowledge_base_recovery(self, tmp_path):
        """Test graceful handling of corrupted knowledge base files."""
        # Create corrupted config file
        config_file = tmp_path / "corrupted_config.json"
        config_file.write_text('{"invalid": json syntax}')  # Invalid JSON

        generator = PromptGenerator(config_path=str(config_file))

        config = PromptConfig(
            technologies=["python"],
            task_type="test_task",
            code_requirements="test requirements that are long enough",
        )

        # Should handle corrupted config gracefully
        prompt = generator.generate_prompt(config)

        assert prompt is not None
        assert len(prompt) > 50
        assert "python" in prompt.lower()

    def test_missing_knowledge_files_graceful_degradation(self, tmp_path):
        """Test graceful degradation when knowledge files are missing."""
        # Create valid config but no knowledge files
        config_data = {
            "python": {"best_practices": ["PEP8", "Clean Code"], "tools": ["pytest", "black"]}
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Don't create the knowledge base files - they'll be missing
        generator = PromptGenerator(config_path=str(config_file), base_path=str(tmp_path))

        config = PromptConfig(
            technologies=["python"],
            task_type="test_development",
            code_requirements="test requirements that are long enough",
        )

        prompt = generator.generate_prompt(config)

        # Should still generate a prompt even with missing files
        assert prompt is not None
        assert "python" in prompt.lower()
        assert "test_development" in prompt
        # Should fall back to technology names when details are missing
        assert "PEP8" in prompt or "pytest" in prompt

    def test_template_rendering_error_recovery(self, tmp_path):
        """Test recovery from template rendering errors."""
        # Create template with invalid syntax
        templates_dir = tmp_path / "prompts"
        base_dir = templates_dir / "base_prompts"
        base_dir.mkdir(parents=True)

        # Invalid Jinja2 syntax
        (base_dir / "broken_template.txt").write_text(
            """
        Invalid template with {{ unclosed_variable
        {% invalid_block %}
        Missing closing tags
        """
        )

        # Valid fallback template
        (base_dir / "generic_code_prompt.txt").write_text(
            """
        Simple template for {{ technologies | join(', ') }}
        Task: {{ task_type }}
        Requirements: {{ code_requirements }}
        """
        )

        generator = PromptGenerator(prompts_dir=str(templates_dir))

        config = PromptConfig(
            technologies=["python"],
            task_type="error_recovery_test",
            code_requirements="test requirements that are long enough",
            template_name="broken_template.txt",
        )

        # Should fall back to working template
        prompt = generator.generate_prompt(config)

        assert prompt is not None
        assert "python" in prompt
        assert "error_recovery_test" in prompt

    def test_file_permission_error_handling(self, tmp_path):
        """Test handling of file permission errors."""
        # Create files and then make them unreadable
        config_file = tmp_path / "restricted_config.json"
        config_data = {"python": {"best_practices": ["PEP8"], "tools": ["pytest"]}}

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create knowledge base directory
        kb_dir = tmp_path / "knowledge_base"
        kb_dir.mkdir()

        # Simulate permission error with mocking
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            generator = PromptGenerator(config_path=str(config_file))

            config = PromptConfig(
                technologies=["python"],
                task_type="permission_test",
                code_requirements="test requirements that are long enough",
            )

            # Should handle permission errors gracefully
            prompt = generator.generate_prompt(config)

            assert prompt is not None
            assert "python" in prompt.lower()

    def test_large_knowledge_base_memory_handling(self, tmp_path):
        """Test handling of very large knowledge base."""
        # Create config with many technologies
        large_config = {}
        for i in range(100):  # 100 technologies
            tech_name = f"technology_{i:03d}"
            large_config[tech_name] = {
                "best_practices": [f"practice_{j}" for j in range(20)],  # 20 practices each
                "tools": [f"tool_{j}" for j in range(15)],  # 15 tools each
            }

        config_file = tmp_path / "large_config.json"
        with open(config_file, "w") as f:
            json.dump(large_config, f)

        generator = PromptGenerator(config_path=str(config_file))

        # Test with subset of technologies
        selected_techs = [f"technology_{i:03d}" for i in range(0, 50, 5)]  # Every 5th technology

        config = PromptConfig(
            technologies=selected_techs,
            task_type="large_scale_development",
            code_requirements="Handle large technology stack efficiently",
        )

        start_time = time.perf_counter()
        prompt = generator.generate_prompt(config)
        generation_time = time.perf_counter() - start_time

        # Should complete in reasonable time even with large dataset
        assert generation_time < 5.0, f"Large dataset processing took {generation_time:.2f}s"
        assert prompt is not None
        assert len(prompt) > 500

        # Should include some of the technologies
        techs_found = sum(1 for tech in selected_techs if tech in prompt)
        assert techs_found >= len(selected_techs) // 2, "Should include most selected technologies"


class TestConcurrencyAndPerformance:
    """Test concurrent access and performance characteristics."""

    def test_concurrent_prompt_generation(self, tmp_path):
        """Test concurrent prompt generation."""
        import concurrent.futures
        import threading

        # Setup shared knowledge base
        config_data = {
            "python": {"best_practices": ["PEP8"], "tools": ["pytest"]},
            "javascript": {"best_practices": ["ESLint"], "tools": ["jest"]},
            "react": {"best_practices": ["Components"], "tools": ["testing-library"]},
        }

        config_file = tmp_path / "concurrent_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(config_path=str(config_file))

        def generate_prompt_task(tech_combo):
            """Task for concurrent execution."""
            config = PromptConfig(
                technologies=tech_combo,
                task_type=f"development_with_{len(tech_combo)}_techs",
                code_requirements="Concurrent testing requirements that are long enough",
            )
            return generator.generate_prompt(config), threading.current_thread().ident

        # Different technology combinations
        tech_combinations = [
            ["python"],
            ["javascript"],
            ["react"],
            ["python", "javascript"],
            ["javascript", "react"],
            ["python", "react"],
            ["python", "javascript", "react"],
        ]

        # Execute concurrently
        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(generate_prompt_task, combo) for combo in tech_combinations]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        total_time = time.perf_counter() - start_time

        # Validate results
        assert len(results) == len(tech_combinations)
        prompts, thread_ids = zip(*results)

        # All prompts should be valid
        for prompt in prompts:
            assert prompt is not None
            assert len(prompt) > 100

        # Should use multiple threads
        unique_threads = set(thread_ids)
        assert len(unique_threads) > 1, "Should use multiple threads for concurrent execution"

        # Should complete in reasonable time
        assert total_time < 10.0, f"Concurrent execution took {total_time:.2f}s"

        # Results should be consistent (same input -> same output)
        # Test this by running same combination multiple times
        test_config = PromptConfig(
            technologies=["python"],
            task_type="consistency_test",
            code_requirements="Consistency testing requirements that are long enough",
        )

        prompt1 = generator.generate_prompt(test_config)
        prompt2 = generator.generate_prompt(test_config)
        assert prompt1 == prompt2, "Same input should produce same output"

    def test_knowledge_manager_caching_under_load(self, tmp_path):
        """Test knowledge manager caching behavior under load."""
        # Create knowledge base
        config_data = {
            "python": {"best_practices": ["PEP8", "Testing"], "tools": ["pytest", "black"]},
            "javascript": {"best_practices": ["ESLint", "Testing"], "tools": ["jest", "eslint"]},
        }

        config_file = tmp_path / "cache_test_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create knowledge files
        bp_dir = tmp_path / "knowledge_base" / "best_practices"
        bp_dir.mkdir(parents=True)
        (bp_dir / "pep8.md").write_text("PEP8 content")
        (bp_dir / "testing.md").write_text("Testing content")
        (bp_dir / "eslint.md").write_text("ESLint content")

        tools_dir = tmp_path / "knowledge_base" / "tools"
        tools_dir.mkdir(parents=True)
        for tool in ["pytest", "black", "jest", "eslint"]:
            (tools_dir / f"{tool}.json").write_text(
                json.dumps({"name": tool, "description": f"{tool} description"})
            )

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Track file access
        original_read = km._read_text_file
        read_count = {"count": 0}

        def counting_read(*args, **kwargs):
            read_count["count"] += 1
            return original_read(*args, **kwargs)

        km._read_text_file = counting_read

        # Multiple access to same data
        for _ in range(10):
            details = km.get_best_practice_details("PEP8")
            assert details == "PEP8 content"

        # Should cache after first read
        assert read_count["count"] == 1, "Should cache file content after first read"

        # Access different data
        km.get_best_practice_details("Testing")
        assert read_count["count"] == 2, "Should read new file"

        # Access cached data again
        km.get_best_practice_details("PEP8")
        assert read_count["count"] == 2, "Should use cache for repeated access"

    def test_performance_with_realistic_datasets(self, tmp_path):
        """Test performance with realistic dataset sizes."""
        # Create realistic knowledge base
        technologies = [
            "python",
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "node",
            "express",
            "fastapi",
            "django",
            "flask",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
        ]

        config_data = {}
        for tech in technologies:
            config_data[tech] = {
                "best_practices": [f"{tech}_practice_{i}" for i in range(10)],
                "tools": [f"{tech}_tool_{i}" for i in range(8)],
            }

        config_file = tmp_path / "realistic_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(config_path=str(config_file))

        # Test scenarios of increasing complexity
        test_scenarios = [
            (["python"], "Single technology"),
            (["python", "fastapi", "postgresql"], "Backend stack"),
            (["react", "typescript", "node", "express"], "Frontend + Backend"),
            (["python", "react", "postgresql", "docker", "aws"], "Full stack"),
            (technologies[:10], "Large project (10 techs)"),
            (technologies[:15], "Enterprise project (15 techs)"),
        ]

        performance_results = []

        for tech_list, description in test_scenarios:
            config = PromptConfig(
                technologies=tech_list,
                task_type="performance_test",
                code_requirements="Performance testing requirements that are long enough",
            )

            start_time = time.perf_counter()
            prompt = generator.generate_prompt(config)
            generation_time = time.perf_counter() - start_time

            performance_results.append(
                {
                    "scenario": description,
                    "tech_count": len(tech_list),
                    "generation_time": generation_time,
                    "prompt_length": len(prompt),
                }
            )

            # Basic validation
            assert prompt is not None
            assert len(prompt) > 200

            # Performance requirements
            if len(tech_list) <= 5:
                assert (
                    generation_time < 1.0
                ), f"{description} took {generation_time:.2f}s (should be < 1s)"
            elif len(tech_list) <= 10:
                assert (
                    generation_time < 2.0
                ), f"{description} took {generation_time:.2f}s (should be < 2s)"
            else:
                assert (
                    generation_time < 3.0
                ), f"{description} took {generation_time:.2f}s (should be < 3s)"

        # Performance should scale reasonably
        times = [result["generation_time"] for result in performance_results]
        tech_counts = [result["tech_count"] for result in performance_results]

        # Simple check: time shouldn't increase exponentially with tech count
        max_time = max(times)
        max_tech_count = max(tech_counts)

        # Rule of thumb: shouldn't take more than 0.2 seconds per technology
        time_per_tech = max_time / max_tech_count
        assert time_per_tech < 0.3, f"Time per technology {time_per_tech:.3f}s is too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
