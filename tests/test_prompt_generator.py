import pytest
import os
import json
from src.prompt_generator import PromptGenerator
from src.knowledge_manager import KnowledgeManager

# Setup for tests
@pytest.fixture
def setup_generator(tmp_path):
    # Create dummy config file
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "tech_stack_mapping.json"
    config_data = {
        "python": {"best_practices": ["PEP8", "Clean Code Principles"], "tools": ["Pylint", "Black"]},
        "javascript": {"best_practices": ["ESLint Recommended"], "tools": ["Jest", "ESLint"]},
        "react": {"best_practices": ["React Best Practices"], "tools": ["ESLint-plugin-react"]}
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    # Create dummy knowledge base files
    kb_bp_dir = tmp_path / "knowledge_base" / "best_practices"
    kb_bp_dir.mkdir(parents=True)
    (kb_bp_dir / "pep8.md").write_text("PEP8 details")
    (kb_bp_dir / "clean_code_principles.md").write_text("Clean Code details")
    (kb_bp_dir / "eslint_recommended.md").write_text("ESLint Recommended details")
    (kb_bp_dir / "react_best_practices.md").write_text("React Best Practices details")

    kb_tools_dir = tmp_path / "knowledge_base" / "tools"
    kb_tools_dir.mkdir(parents=True)
    with open(kb_tools_dir / "pylint.json", 'w') as f:
        json.dump({"name": "Pylint", "description": "Pylint tool"}, f)
    with open(kb_tools_dir / "black.json", 'w') as f:
        json.dump({"name": "Black", "description": "Black tool"}, f)
    with open(kb_tools_dir / "jest.json", 'w') as f:
        json.dump({"name": "Jest", "description": "Jest tool"}, f)
    with open(kb_tools_dir / "eslint.json", 'w') as f:
        json.dump({"name": "ESLint", "description": "ESLint tool"}, f)
    with open(kb_tools_dir / "eslint_plugin_react.json", 'w') as f:
        json.dump({"name": "ESLint-plugin-react", "description": "ESLint React tool"}, f)

    # Create dummy prompt templates
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "base_prompts").mkdir()
    (prompts_dir / "base_prompts" / "generic_code_prompt.txt").write_text(
        "Come sviluppatore esperto in {{ technologies }}, implementa la seguente {{ task_type }} aderendo a queste best practice: {{ best_practices }}. Utilizza i seguenti tool per la qualità del codice: {{ tools }}. Il codice deve essere: {{ code_requirements }}."
    )
    (prompts_dir / "language_specific").mkdir()
    (prompts_dir / "language_specific" / "python").mkdir()
    (prompts_dir / "language_specific" / "python" / "feature_prompt.txt").write_text(
        "Come sviluppatore Python esperto, implementa la seguente funzionalità: {{ task_description }}. Assicurati di seguire le best practice Python ({{ best_practices }}) e di utilizzare i seguenti tool per garantire la qualità del codice: {{ tools }}. Il codice deve essere: {{ code_requirements }}. Includi docstring e type hints appropriati."
    )
    (prompts_dir / "framework_specific").mkdir()
    (prompts_dir / "framework_specific" / "react").mkdir()
    (prompts_dir / "framework_specific" / "react" / "component_prompt.txt").write_text(
        "Come sviluppatore React esperto, crea il seguente componente UI: {{ task_description }}. Assicurati di aderire alle seguenti best practice: {{ best_practices }}. Utilizza i seguenti tool per garantire la qualità e la testabilità del codice: {{ tools }}. Il componente deve essere: {{ code_requirements }}. Includi test unitari con Jest e React Testing Library."
    )

    return str(prompts_dir), str(config_file)

def test_prompt_generator_generic_prompt(setup_generator):
    prompts_dir, config_path = setup_generator
    generator = PromptGenerator(prompts_dir, config_path)

    technologies = ["python"]
    task_type = "nuova funzionalità"
    task_description = "un modulo di utilità"
    code_requirements = "Il codice deve essere pulito e ben commentato."

    prompt = generator.generate_prompt(
        technologies=technologies,
        task_type=task_type,
        task_description=task_description,
        code_requirements=code_requirements,
        template_name="base_prompts/generic_code_prompt.txt"
    )

    assert "Come sviluppatore esperto in python" in prompt
    assert "nuova funzionalità" in prompt
    assert "PEP8 details" in prompt # Check for detailed best practice
    assert "Pylint tool" in prompt # Check for detailed tool
    assert "Il codice deve essere pulito e ben commentato." in prompt

def test_prompt_generator_python_feature_prompt(setup_generator):
    prompts_dir, config_path = setup_generator
    generator = PromptGenerator(prompts_dir, config_path)

    technologies = ["python"]
    task_type = "funzionalità"
    task_description = "un endpoint API"
    code_requirements = "Deve essere RESTful."

    prompt = generator.generate_prompt(
        technologies=technologies,
        task_type=task_type,
        task_description=task_description,
        code_requirements=code_requirements,
        template_name="language_specific/python/feature_prompt.txt"
    )

    assert "Come sviluppatore Python esperto, implementa la seguente funzionalità: un endpoint API." in prompt
    assert "PEP8 details" in prompt
    assert "Pylint tool" in prompt
    assert "Il codice deve essere: Deve essere RESTful.. Includi docstring e type hints appropriati." in prompt

def test_prompt_generator_react_component_prompt(setup_generator):
    prompts_dir, config_path = setup_generator
    generator = PromptGenerator(prompts_dir, config_path)

    technologies = ["javascript", "react"]
    task_type = "componente UI"
    task_description = "un bottone riutilizzabile"
    code_requirements = "Deve essere accessibile."

    prompt = generator.generate_prompt(
        technologies=technologies,
        task_type=task_type,
        task_description=task_description,
        code_requirements=code_requirements,
        template_name="framework_specific/react/component_prompt.txt"
    )

    assert "Come sviluppatore React esperto, crea il seguente componente UI: un bottone riutilizzabile." in prompt
    assert "ESLint Recommended details" in prompt
    assert "React Best Practices details" in prompt
    assert "Jest tool" in prompt
    assert "Description: ESLint React tool" in prompt # Corrected assertion
    assert "Il componente deve essere: Deve essere accessibile.. Includi test unitari con Jest e React Testing Library." in prompt

def test_prompt_generator_empty_technologies(setup_generator):
    prompts_dir, config_path = setup_generator
    generator = PromptGenerator(prompts_dir, config_path)

    technologies = []
    task_type = "test"
    task_description = "test"
    code_requirements = "test"

    prompt = generator.generate_prompt(
        technologies=technologies,
        task_type=task_type,
        task_description=task_description,
        code_requirements=code_requirements,
        template_name="base_prompts/generic_code_prompt.txt"
    )
    assert "Come sviluppatore esperto in " in prompt # Should still render, but with empty technologies
    assert "aderendo a queste best practice: ." in prompt # No best practices
    assert "Utilizza i seguenti tool per la qualità del codice: ." in prompt # No tools

def test_prompt_generator_invalid_template(setup_generator):
    prompts_dir, config_path = setup_generator
    generator = PromptGenerator(prompts_dir, config_path)

    technologies = ["python"]
    task_type = "test"
    task_description = "test"
    code_requirements = "test"

    # Should fall back to generic template and log a warning
    prompt = generator.generate_prompt(
        technologies=technologies,
        task_type=task_type,
        task_description=task_description,
        code_requirements=code_requirements,
        template_name="non_existent_template.txt"
    )
    assert "Come sviluppatore esperto in python" in prompt # Fallback to generic
    assert "PEP8 details" in prompt
    assert "Pylint tool" in prompt