#!/usr/bin/env python3
"""
Advanced Prompt Engineering CLI Tool

A comprehensive command-line interface for generating context-aware prompts
for AI-assisted code development across multiple technology stacks.

Features:
- Multi-technology prompt generation
- Comprehensive help system with examples
- Shell autocomplete support (bash, zsh, fish)
- Multiple output formats (text, JSON, markdown)
- Interactive mode for guided prompt creation
- Built-in example scenarios for common use cases
- Enterprise-ready technology stack support

Usage Examples:
  python main.py --tech python fastapi --task "REST API development"
  python main.py --example django-app --format json
  python main.py --interactive
  python main.py --list-tech
"""

from src.prompt_generator import PromptGenerator
from src.prompt_config import PromptConfig
from typing import List, Tuple, Dict, Any, Optional
import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "tech_stack_mapping.json")

def generate_example_prompt(generator: PromptGenerator, config: PromptConfig, title: str) -> None:
    """
    Generates and displays a single example prompt.
    
    Eliminates code duplication in main() by extracting common pattern.
    
    Args:
        generator: The PromptGenerator instance.
        config: Configuration for prompt generation.
        title: Display title for the example.
    """
    logger.info(f"Generating prompt for: {title}")
    prompt = generator.generate_prompt(config)
    
    separator = "-" * (len(title) + 8)
    print(f"\n--- {title} ---")
    print(prompt)
    print(separator)

def create_example_configs() -> List[Tuple[PromptConfig, str]]:
    """
    Creates list of example configurations for demonstration.
    
    Returns:
        List of tuples containing (config, title) pairs.
    """
    return [
        (
            PromptConfig(
                technologies=["python"],
                task_type="authentication API development",
                task_description="API endpoint for user registration with input validation and password hashing",
                code_requirements="The code must be modular, testable, and follow SOLID principles. Use an ORM for database interaction.",
                template_name="language_specific/python/production_api_prompt.txt"
            ),
            "Generated Prompt (Python API)"
        ),
        (
            PromptConfig(
                technologies=["javascript", "react"],
                task_type="UI component development",
                task_description="React component for a login form with client-side validation",
                code_requirements="The component must be reusable, accessible, and use React Hooks. Manage form state efficiently.",
                template_name="framework_specific/react/production_component_prompt.txt"
            ),
            "Generated Prompt (React Component)"
        ),
        (
            PromptConfig(
                technologies=["python", "docker", "docker_compose", "ansible"],
                task_type="infrastructure deployment automation",
                task_description="local development environment with Docker Compose and Ansible script for deployment to remote server",
                code_requirements="The environment must be reproducible, easy to configure, and deployment must be automated and idempotent.",
                template_name="base_prompts/production_devops_prompt.txt"
            ),
            "Generated Prompt (DevOps Infrastructure)"
        )
    ]

class PromptEngineeringCLI:
    """
    Advanced CLI for prompt engineering with comprehensive features.
    """
    
    def __init__(self):
        self.generator = None
        self.available_technologies = []
        self.predefined_examples = self._load_predefined_examples()
        
    def _select_optimal_template(self, technologies: List[str], task_type: str) -> str:
        """Intelligently select the best focused template based on technologies and task type."""
        task_lower = task_type.lower()
        
        # API development
        if any(word in task_lower for word in ['api', 'endpoint', 'rest', 'service', 'backend']) and 'python' in technologies:
            return "base_prompts/focused_api_prompt.txt"
        
        # React component development  
        if any(word in task_lower for word in ['component', 'ui', 'frontend', 'form', 'interface']) and 'react' in technologies:
            return "framework_specific/react/focused_component_prompt.txt"
        
        # DevOps/Infrastructure tasks
        if any(word in task_lower for word in ['infrastructure', 'deployment', 'devops', 'container', 'environment', 'automation']):
            return "base_prompts/focused_devops_prompt.txt"
            
        # Default to focused API template (most common use case)
        return "base_prompts/focused_api_prompt.txt"

    def _load_predefined_examples(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined example scenarios for quick access."""
        return {
            "python-api": {
                "technologies": ["python", "fastapi"],
                "task_type": "REST API development",
                "task_description": "user management API with JWT authentication and CRUD operations",
                "code_requirements": "Include password hashing, input validation, error handling, and basic tests",
                "template_name": "base_prompts/focused_api_prompt.txt"
            },
            "react-app": {
                "technologies": ["javascript", "react"],
                "task_type": "frontend component development", 
                "task_description": "login form component with validation and TypeScript",
                "code_requirements": "Include form validation, loading states, accessibility features, and error handling",
                "template_name": "framework_specific/react/focused_component_prompt.txt"
            },
            "django-app": {
                "technologies": ["python", "django"],
                "task_type": "web API development",
                "task_description": "Django REST API for blog posts with user authentication",
                "code_requirements": "Include Django REST framework, JWT authentication, serializers, and basic tests",
                "template_name": "base_prompts/focused_api_prompt.txt"
            },
            "devops-setup": {
                "technologies": ["docker", "docker_compose", "ansible"],
                "task_type": "infrastructure deployment automation",
                "task_description": "containerized web application with database and automated deployment",
                "code_requirements": "Include multi-stage Docker builds, health checks, environment configuration, and Ansible playbooks",
                "template_name": "base_prompts/focused_devops_prompt.txt"
            },
            "enterprise-stack": {
                "technologies": ["python", "postgresql", "redis", "docker"],
                "task_type": "REST API development",
                "task_description": "scalable microservice with database and caching",
                "code_requirements": "Include PostgreSQL integration, Redis caching, Docker containerization, and monitoring",
                "template_name": "base_prompts/focused_api_prompt.txt"
            }
        }
    
    def _load_available_technologies(self) -> List[str]:
        """Load available technologies from configuration."""
        try:
            import json
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                return sorted(list(config.keys()))
        except Exception as e:
            logger.warning(f"Could not load technologies from config: {e}")
            return ["python", "javascript", "react", "django", "fastapi", "docker", "postgresql"]
    
    def _initialize_generator(self):
        """Initialize the prompt generator if not already done."""
        if self.generator is None:
            self.generator = PromptGenerator(PROMPTS_DIR, CONFIG_PATH)
            self.available_technologies = self._load_available_technologies()
    
    def list_technologies(self) -> None:
        """Display all available technologies."""
        self._initialize_generator()
        print("\n🔧 Available Technologies:")
        print("=" * 50)
        
        # Group technologies by category for better readability
        categories = {
            "Languages": ["python", "javascript", "typescript", "java", "go"],
            "Frameworks": ["react", "django", "fastapi", "spring_boot", "express"],
            "Databases": ["postgresql", "mysql", "mongodb", "redis"],
            "DevOps": ["docker", "docker_compose", "ansible", "kubernetes"],
            "Cloud": ["aws", "azure", "gcp"],
            "Other": []
        }
        
        # Categorize available technologies
        categorized = {cat: [] for cat in categories}
        uncategorized = []
        
        for tech in self.available_technologies:
            found = False
            for category, tech_list in categories.items():
                if tech in tech_list:
                    categorized[category].append(tech)
                    found = True
                    break
            if not found:
                uncategorized.append(tech)
        
        # Display categorized technologies
        for category, techs in categorized.items():
            if techs:
                print(f"\n{category}:")
                for tech in sorted(techs):
                    print(f"  - {tech}")
        
        if uncategorized:
            print(f"\nOther:")
            for tech in sorted(uncategorized):
                print(f"  - {tech}")
        
        print(f"\nTotal: {len(self.available_technologies)} technologies available")
    
    def list_examples(self) -> None:
        """Display all predefined examples."""
        print("\n📋 Predefined Example Scenarios:")
        print("=" * 50)
        
        for name, config in self.predefined_examples.items():
            print(f"\n🚀 {name}")
            print(f"   Technologies: {', '.join(config['technologies'])}")
            print(f"   Task: {config['task_type']}")
            print(f"   Description: {config['task_description'][:100]}...")
        
        print(f"\nUsage: python main.py --example <name> [--format json|markdown]")
    
    def interactive_prompt_creation(self) -> PromptConfig:
        """Interactive mode for creating prompts."""
        print("\n🤖 Interactive Prompt Creation")
        print("=" * 50)
        
        # Technology selection
        print(f"\nAvailable technologies: {', '.join(self.available_technologies[:10])}...")
        print("(Use --list-tech to see all available technologies)")
        
        tech_input = input("\nEnter technologies (space-separated): ").strip()
        technologies = [t.strip() for t in tech_input.split() if t.strip()]
        
        if not technologies:
            print("❌ No technologies specified. Using 'python' as default.")
            technologies = ["python"]
        
        # Task type
        task_type = input("\nEnter task type (e.g., 'web application development'): ").strip()
        if not task_type:
            task_type = "software development"
        
        # Task description
        print("\nEnter detailed task description:")
        task_description = input("Description: ").strip()
        if not task_description:
            task_description = "Implement the requested functionality following best practices"
        
        # Code requirements
        print("\nEnter specific code requirements (optional):")
        code_requirements = input("Requirements: ").strip()
        if not code_requirements:
            code_requirements = "Follow best practices and write clean, maintainable code"
        
        return PromptConfig(
            technologies=technologies,
            task_type=task_type,
            task_description=task_description,
            code_requirements=code_requirements,
            template_name="base_prompts/generic_code_prompt.txt"
        )
    
    def generate_from_example(self, example_name: str) -> Optional[PromptConfig]:
        """Generate prompt from predefined example."""
        if example_name not in self.predefined_examples:
            print(f"❌ Example '{example_name}' not found.")
            print("Available examples:", ", ".join(self.predefined_examples.keys()))
            return None
        
        example = self.predefined_examples[example_name]
        return PromptConfig(**example)
    
    def format_output(self, prompt: str, format_type: str, config: PromptConfig) -> str:
        """Format output based on requested format."""
        if format_type == "json":
            return json.dumps({
                "prompt": prompt,
                "configuration": {
                    "technologies": config.technologies,
                    "task_type": config.task_type,
                    "task_description": config.task_description,
                    "code_requirements": config.code_requirements,
                    "template_name": config.template_name
                },
                "metadata": {
                    "generated_at": "2025-06-30",
                    "tool_version": "1.0.0",
                    "character_count": len(prompt)
                }
            }, indent=2)
        
        elif format_type == "markdown":
            return f"""# Generated Prompt

## Configuration
- **Technologies**: {', '.join(config.technologies)}
- **Task Type**: {config.task_type}
- **Template**: {config.template_name}

## Task Description
{config.task_description}

## Code Requirements
{config.code_requirements}

## Generated Prompt

```
{prompt}
```

---
*Generated by Advanced Prompt Engineering CLI*
"""
        
        else:  # text format (default)
            return f"""
🚀 Generated Prompt
{'=' * 50}

Technologies: {', '.join(config.technologies)}
Task Type: {config.task_type}
Template: {config.template_name}

{prompt}

{'=' * 50}
Character Count: {len(prompt)}
"""

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="prompt-engineer",
        description="Advanced Prompt Engineering CLI Tool - Generate context-aware prompts for AI-assisted development",
        epilog="""
Example Usage:
  %(prog)s --tech python fastapi --task "REST API development"
  %(prog)s --example django-app --format json
  %(prog)s --interactive
  %(prog)s --list-tech
  %(prog)s --list-examples
  
For shell autocomplete:
  # Bash
  eval "$(%(prog)s --print-completion bash)"
  
  # Zsh  
  eval "$(%(prog)s --print-completion zsh)"
  
  # Fish
  %(prog)s --print-completion fish | source
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main command groups
    main_group = parser.add_argument_group('Main Commands')
    
    main_group.add_argument(
        '--tech', '--technologies',
        nargs='+',
        metavar='TECH',
        help='Technologies to include (e.g., python react docker). Use --list-tech to see available options.'
    )
    
    main_group.add_argument(
        '--task',
        metavar='DESCRIPTION',
        help='Task type or description (e.g., "web application development")'
    )
    
    main_group.add_argument(
        '--description',
        metavar='TEXT',
        help='Detailed task description'
    )
    
    main_group.add_argument(
        '--requirements',
        metavar='TEXT',
        help='Specific code requirements and constraints'
    )
    
    main_group.add_argument(
        '--template',
        metavar='PATH',
        default='base_prompts/production_ready_prompt.txt',
        help='Template file to use (default: %(default)s)'
    )
    
    # Predefined examples
    examples_group = parser.add_argument_group('Predefined Examples')
    
    examples_group.add_argument(
        '--example',
        metavar='NAME',
        help='Use predefined example (python-api, react-app, django-app, devops-setup, enterprise-stack)'
    )
    
    examples_group.add_argument(
        '--list-examples',
        action='store_true',
        help='List all predefined example scenarios'
    )
    
    # Output and formatting
    output_group = parser.add_argument_group('Output Options')
    
    output_group.add_argument(
        '--format',
        choices=['text', 'json', 'markdown'],
        default='text',
        help='Output format (default: %(default)s)'
    )
    
    output_group.add_argument(
        '--output', '-o',
        metavar='FILE',
        help='Write output to file instead of stdout'
    )
    
    output_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress info messages, only show generated prompt'
    )
    
    # Information commands
    info_group = parser.add_argument_group('Information Commands')
    
    info_group.add_argument(
        '--list-tech',
        action='store_true',
        help='List all available technologies'
    )
    
    info_group.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode for guided prompt creation'
    )
    
    info_group.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0 - Advanced Prompt Engineering CLI'
    )
    
    # Shell completion (hidden from help but functional)
    parser.add_argument(
        '--print-completion',
        choices=['bash', 'zsh', 'fish'],
        help=argparse.SUPPRESS  # Hide from help but keep functional
    )
    
    return parser

def generate_shell_completion(shell: str) -> str:
    """Generate shell completion script."""
    if shell == 'bash':
        return '''
_prompt_engineer_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    case ${prev} in
        --tech|--technologies)
            opts="python javascript react django fastapi docker postgresql redis ansible"
            ;;
        --example)
            opts="python-api react-app django-app devops-setup enterprise-stack"
            ;;
        --format)
            opts="text json markdown"
            ;;
        --print-completion)
            opts="bash zsh fish"
            ;;
        *)
            opts="--tech --task --description --requirements --template --example --list-examples --format --output --quiet --list-tech --interactive --version --help"
            ;;
    esac
    
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}
complete -F _prompt_engineer_completion prompt-engineer
complete -F _prompt_engineer_completion python main.py
        '''
    elif shell == 'zsh':
        return '''
#compdef prompt-engineer

_prompt_engineer() {
    local context state line
    _arguments -C \
        '--tech[Technologies to include]:technology:_technologies' \
        '--task[Task description]:task:' \
        '--description[Detailed description]:description:' \
        '--requirements[Code requirements]:requirements:' \
        '--template[Template file]:template:_files' \
        '--example[Predefined example]:example:_examples' \
        '--list-examples[List examples]' \
        '--format[Output format]:format:(text json markdown)' \
        '--output[Output file]:file:_files' \
        '--quiet[Quiet mode]' \
        '--list-tech[List technologies]' \
        '--interactive[Interactive mode]' \
        '--version[Show version]' \
        '--help[Show help]'
}

_technologies() {
    local -a technologies
    technologies=(python javascript react django fastapi docker postgresql redis ansible)
    _describe 'technology' technologies
}

_examples() {
    local -a examples
    examples=(python-api react-app django-app devops-setup enterprise-stack)
    _describe 'example' examples
}

_prompt_engineer "$@"
        '''
    elif shell == 'fish':
        return '''
# Fish shell completion for prompt-engineer

complete -c prompt-engineer -s h -l help -d "Show help message"
complete -c prompt-engineer -l tech -d "Technologies to include" -xa "python javascript react django fastapi docker postgresql redis ansible"
complete -c prompt-engineer -l task -d "Task description"
complete -c prompt-engineer -l description -d "Detailed task description"
complete -c prompt-engineer -l requirements -d "Code requirements"
complete -c prompt-engineer -l template -d "Template file" -F
complete -c prompt-engineer -l example -d "Predefined example" -xa "python-api react-app django-app devops-setup enterprise-stack"
complete -c prompt-engineer -l list-examples -d "List all examples"
complete -c prompt-engineer -l format -d "Output format" -xa "text json markdown"
complete -c prompt-engineer -s o -l output -d "Output file" -F
complete -c prompt-engineer -s q -l quiet -d "Quiet mode"
complete -c prompt-engineer -l list-tech -d "List available technologies"
complete -c prompt-engineer -s i -l interactive -d "Interactive mode"
complete -c prompt-engineer -l version -d "Show version"
        '''
    
    return ""

def main():
    """
    Main CLI entry point with comprehensive argument handling.
    """
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle shell completion
    if args.print_completion:
        print(generate_shell_completion(args.print_completion))
        return
    
    # Configure logging based on quiet flag
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Initialize CLI
    cli = PromptEngineeringCLI()
    
    # Handle information commands
    if args.list_tech:
        cli.list_technologies()
        return
    
    if args.list_examples:
        cli.list_examples()
        return
    
    # Initialize generator for prompt generation
    cli._initialize_generator()
    
    # Determine prompt configuration
    config = None
    
    if args.interactive:
        config = cli.interactive_prompt_creation()
    elif args.example:
        config = cli.generate_from_example(args.example)
        if config is None:
            return
    elif args.tech:
        # Build config from command line arguments with intelligent template selection
        task_type = args.task or "software development"
        template_name = args.template
        
        # Use intelligent template selection if default template is being used
        if template_name == "base_prompts/production_ready_prompt.txt":
            template_name = cli._select_optimal_template(args.tech, task_type)
        
        config = PromptConfig(
            technologies=args.tech,
            task_type=task_type,
            task_description=args.description or "Implement the requested functionality following best practices",
            code_requirements=args.requirements or "Follow best practices and write clean, maintainable code",
            template_name=template_name
        )
    else:
        # No configuration provided, show help
        print("❌ No configuration provided. Use --help for usage information.")
        print("\nQuick start options:")
        print("  --interactive          # Interactive mode")
        print("  --example python-api   # Use predefined example")
        print("  --tech python --task 'API development'  # Direct configuration")
        return
    
    # Generate prompt
    try:
        if not args.quiet:
            logger.info(f"Generating prompt for technologies: {config.technologies}")
        
        prompt = cli.generator.generate_prompt(config)
        formatted_output = cli.format_output(prompt, args.format, config)
        
        # Output handling
        if args.output:
            with open(args.output, 'w') as f:
                f.write(formatted_output)
            if not args.quiet:
                print(f"✅ Prompt written to {args.output}")
        else:
            print(formatted_output)
        
        if not args.quiet:
            logger.info("Prompt generation completed successfully")
    
    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
        sys.exit(1)

# Legacy compatibility function
def run_legacy_examples():
    """Run the original example scenarios for backward compatibility."""
    logger.info("Running legacy examples for backward compatibility...")
    generator = PromptGenerator(PROMPTS_DIR, CONFIG_PATH)
    
    example_configs = create_example_configs()
    
    for config, title in example_configs:
        generate_example_prompt(generator, config, title)

if __name__ == "__main__":
    # Check if running in legacy mode (no arguments)
    if len(sys.argv) == 1:
        print("🚀 Advanced Prompt Engineering CLI")
        print("=" * 50)
        print("Use --help for comprehensive usage information")
        print("Use --interactive for guided prompt creation")
        print("Use --list-examples to see predefined scenarios")
        print("\nRunning legacy examples for demonstration...")
        run_legacy_examples()
    else:
        main()
