## Code Best Practices

- Always follow the `code-best-practice.md` guidelines for writing clean, maintainable code

## Recursive Prompt Generation

### Quick Usage
```python
from src.recursive_prompt_generator import RecursivePromptGenerator, ComplexTask, TaskComplexity
from src.types_advanced import create_technology_name

# Create complex task
task = ComplexTask(
    name="E-commerce Platform",
    description="Build microservices e-commerce platform",
    technologies=[
        create_technology_name("react"),
        create_technology_name("nodejs"),
        create_technology_name("postgresql"),
        create_technology_name("docker"),
        create_technology_name("kubernetes")
    ],
    requirements=["user auth", "product catalog", "order processing"],
    constraints={"timeline": "6_months"},
    target_complexity=TaskComplexity.ENTERPRISE
)

# Generate recursive prompt
result = await recursive_generator.generate_recursive_prompt(task)
if result.is_success():
    composite_prompt = result.unwrap()
    print(f"Generated {len(composite_prompt.subtask_prompts)} subtasks")
```

### Configuration
Add to `config/config.toml`:
```toml
[recursive_generation]
max_recursion_depth = 3
enable_parallel_processing = true
min_subtask_complexity = 0.3
composition_strategy = "dependency_aware"
```

### Test Commands
```bash
# Test recursive generation
python -m pytest tests/unit/test_recursive_prompt_generator.py -v

# Run demo
python examples/recursive_generation_demo.py

# Test template engines
python -m pytest tests/unit/test_template_engines.py -v
```