#!/usr/bin/env python3
"""
Enterprise Prompt Generator CLI

A modern command-line interface for generating enterprise-grade technical prompts
using async architecture, Result types, and comprehensive error handling.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from src.prompt_generator_modern import create_modern_prompt_generator
from src.types_advanced import (
    PromptConfigAdvanced,
    create_technology_name,
    create_task_type,
    create_template_name,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PromptGeneratorCLI:
    """
    Command-line interface for the Enterprise Prompt Generator.
    
    Provides a user-friendly interface for generating technical prompts
    with comprehensive configuration options and quality controls.
    """
    
    def __init__(self):
        self.generator = None
        self.prompts_dir = Path("prompts")
        self.config_path = Path("config/tech_stack_mapping.json")
    
    async def initialize(self) -> bool:
        """
        Initialize the prompt generator with enterprise configurations.
        
        Returns:
            bool: True if initialization successful, False otherwise.
        """
        try:
            self.generator = await create_modern_prompt_generator(
                prompts_dir=str(self.prompts_dir),
                config_path=str(self.config_path),
                performance_tracking=True,
                enable_performance_tracking=True,
                max_concurrent_operations=10,
            )
            logger.info("Enterprise Prompt Generator initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize prompt generator: %s", e)
            return False
    
    async def generate_prompt(
        self,
        technologies: List[str],
        task_type: str,
        task_description: str = "",
        code_requirements: str = "",
        template_name: str = "base_prompts/generic_code_prompt.txt",
        verbose: bool = False
    ) -> Optional[str]:
        """
        Generate a comprehensive technical prompt.
        
        Args:
            technologies: List of technologies to include
            task_type: Type of task to implement
            task_description: Detailed description of the task
            code_requirements: Specific code quality requirements
            template_name: Template to use for generation
            verbose: Enable verbose output
            
        Returns:
            Generated prompt string or None if failed
        """
        try:
            # Validate and convert technologies
            typed_technologies = []
            for tech in technologies:
                try:
                    typed_technologies.append(create_technology_name(tech.lower().strip()))
                except ValueError as e:
                    logger.error("Invalid technology name '%s': %s", tech, e)
                    return None
            
            # Create typed task
            try:
                typed_task = create_task_type(task_type.strip())
            except ValueError as e:
                logger.error("Invalid task type '%s': %s", task_type, e)
                return None
            
            # Create typed template name
            try:
                typed_template = create_template_name(template_name)
            except ValueError as e:
                logger.error("Invalid template name '%s': %s", template_name, e)
                return None
            
            # Create configuration
            config = PromptConfigAdvanced(
                technologies=typed_technologies,
                task_type=typed_task,
                task_description=task_description,
                code_requirements=code_requirements or 
                    "Follow enterprise best practices, include comprehensive testing, "
                    "implement proper error handling, and ensure code quality.",
                template_name=typed_template,  # type: ignore
                performance_tracking=True,
            )
            
            if verbose:
                logger.info("Generating prompt for technologies: %s", technologies)
                logger.info("Task type: %s", task_type)
            
            # Generate prompt
            result = await self.generator.generate_prompt(config)
            
            if result.is_success():
                prompt = result.unwrap()
                if verbose:
                    logger.info("Generated prompt: %d characters", len(prompt))
                return prompt
            else:
                logger.error("Prompt generation failed: %s", result.error)
                return None
                
        except Exception as e:
            logger.error("Unexpected error during prompt generation: %s", e)
            return None
    
    async def list_available_templates(self) -> List[str]:
        """List all available prompt templates."""
        try:
            templates = self.generator.list_templates()
            return [str(template) for template in templates]
        except Exception as e:
            logger.error("Failed to list templates: %s", e)
            return []
    
    async def health_check(self) -> bool:
        """Perform system health check."""
        try:
            result = await self.generator.health_check()
            if result.is_success():
                health_info = result.unwrap()
                logger.info("System health check passed")
                logger.info("Templates available: %d", health_info.get("templates_count", 0))
                return True
            else:
                logger.error("Health check failed: %s", result.error)
                return False
        except Exception as e:
            logger.error("Health check error: %s", e)
            return False


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Enterprise Prompt Generator CLI",
        epilog="Generate enterprise-grade technical prompts with comprehensive best practices.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a technical prompt"
    )
    generate_parser.add_argument(
        "--technologies", "-t",
        nargs="+",
        required=True,
        help="Technologies to include (e.g., python postgresql ansible)"
    )
    generate_parser.add_argument(
        "--task-type", "-k",
        required=True,
        help="Type of task to implement"
    )
    generate_parser.add_argument(
        "--task-description", "-d",
        default="",
        help="Detailed description of the task"
    )
    generate_parser.add_argument(
        "--code-requirements", "-r",
        default="",
        help="Specific code quality requirements"
    )
    generate_parser.add_argument(
        "--template", "-T",
        default="base_prompts/generic_code_prompt.txt",
        help="Template to use for generation"
    )
    generate_parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    generate_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    # List templates command
    list_parser = subparsers.add_parser(
        "list-templates",
        help="List available prompt templates"
    )
    
    # Health check command
    health_parser = subparsers.add_parser(
        "health",
        help="Perform system health check"
    )
    
    # Example commands
    examples_parser = subparsers.add_parser(
        "examples",
        help="Show example usage patterns"
    )
    
    return parser


def show_examples():
    """Display example usage patterns."""
    examples = """
EXAMPLE USAGE PATTERNS:

1. PostgreSQL Cluster with Patroni:
   python cli.py generate \\
     --technologies postgresql ansible docker python linux \\
     --task-type "PostgreSQL Patroni cluster deployment on RHEL 9" \\
     --task-description "Deploy HA PostgreSQL cluster with etcd coordination" \\
     --code-requirements "Use pgdg/crb/epel packages, include monitoring"

2. React Application:
   python cli.py generate \\
     --technologies react javascript typescript \\
     --task-type "User dashboard with authentication" \\
     --template "framework_specific/react/component_prompt.txt"

3. Python API Service:
   python cli.py generate \\
     --technologies python fastapi postgresql \\
     --task-type "REST API with authentication and monitoring" \\
     --code-requirements "Include OpenAPI docs, async operations, comprehensive testing"

4. DevOps Infrastructure:
   python cli.py generate \\
     --technologies ansible terraform kubernetes \\
     --task-type "Container orchestration platform deployment" \\
     --task-description "Deploy production-ready Kubernetes cluster"

5. List Available Templates:
   python cli.py list-templates

6. System Health Check:
   python cli.py health
"""
    print(examples)


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "examples":
        show_examples()
        return 0
    
    # Initialize CLI
    cli = PromptGeneratorCLI()
    
    if not await cli.initialize():
        logger.error("Failed to initialize system")
        return 1
    
    # Handle commands
    if args.command == "generate":
        prompt = await cli.generate_prompt(
            technologies=args.technologies,
            task_type=args.task_type,
            task_description=args.task_description,
            code_requirements=args.code_requirements,
            template_name=args.template,
            verbose=args.verbose
        )
        
        if prompt:
            if args.output:
                try:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(prompt)
                    logger.info("Prompt saved to: %s", args.output)
                except Exception as e:
                    logger.error("Failed to write output file: %s", e)
                    return 1
            else:
                print("=" * 60)
                print("GENERATED PROMPT")
                print("=" * 60)
                print(prompt)
                print("=" * 60)
            return 0
        else:
            return 1
    
    elif args.command == "list-templates":
        templates = await cli.list_available_templates()
        if templates:
            print("Available Templates:")
            print("-" * 40)
            for template in sorted(templates):
                print(f"  {template}")
        else:
            print("No templates found")
        return 0
    
    elif args.command == "health":
        if await cli.health_check():
            print("✅ System health check passed")
            return 0
        else:
            print("❌ System health check failed")
            return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sys.exit(1)