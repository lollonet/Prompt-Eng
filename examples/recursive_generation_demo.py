"""
Recursive Prompt Generation Demo

This script demonstrates the recursive prompt generation system by creating
complex tasks and showing how they are decomposed and composed hierarchically.
"""

import asyncio
import logging
from pathlib import Path

from src.recursive_prompt_generator import (
    RecursivePromptGenerator,
    ComplexTask,
    RecursiveConfig,
    TaskComplexity
)
from src.prompt_generator_modern import ModernPromptGenerator
from src.knowledge_manager_async import create_async_knowledge_manager
from src.web_research.template_engines.template_factory import TemplateFactory
from src.types_advanced import create_technology_name
from src.common.cache_manager import AsyncCacheManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_recursive_generator() -> RecursivePromptGenerator:
    """Create and configure RecursivePromptGenerator with dependencies."""
    
    # Create base generator
    cache_manager = AsyncCacheManager()
    knowledge_manager = await create_async_knowledge_manager(cache_manager)
    base_generator = ModernPromptGenerator(knowledge_manager, cache_manager)
    
    # Create template factory
    template_factory = TemplateFactory()
    
    # Create recursive configuration
    config = RecursiveConfig(
        max_recursion_depth=3,
        enable_parallel_processing=True,
        min_subtask_complexity=0.3,
        composition_strategy="dependency_aware",
        enable_integration_validation=True
    )
    
    # Create recursive generator
    return RecursivePromptGenerator(
        base_generator=base_generator,
        knowledge_manager=knowledge_manager,
        template_factory=template_factory,
        config=config
    )


def create_ecommerce_task() -> ComplexTask:
    """Create complex e-commerce platform task."""
    return ComplexTask(
        name="E-commerce Microservices Platform",
        description="Build a complete e-commerce platform with microservices architecture, including user management, product catalog, order processing, payment integration, and real-time notifications",
        technologies=[
            create_technology_name("react"),
            create_technology_name("nodejs"),
            create_technology_name("python"),
            create_technology_name("postgresql"),
            create_technology_name("redis"),
            create_technology_name("docker"),
            create_technology_name("kubernetes"),
            create_technology_name("nginx"),
            create_technology_name("prometheus"),
            create_technology_name("grafana")
        ],
        requirements=[
            "User authentication and authorization with JWT",
            "Product catalog with search and filtering",
            "Shopping cart and order management",
            "Payment processing with Stripe integration",
            "Real-time order status notifications",
            "Admin dashboard for inventory management",
            "API gateway for service coordination",
            "Monitoring and logging infrastructure",
            "Automated CI/CD pipeline",
            "High availability and scalability"
        ],
        constraints={
            "budget": "enterprise",
            "timeline": "6_months",
            "team_size": "8_developers",
            "scalability": "100k_concurrent_users",
            "availability": "99.9_percent"
        },
        target_complexity=TaskComplexity.ENTERPRISE
    )


def create_portfolio_task() -> ComplexTask:
    """Create simple portfolio website task."""
    return ComplexTask(
        name="Personal Portfolio Website",
        description="Build a modern, responsive personal portfolio website to showcase projects and skills",
        technologies=[
            create_technology_name("react"),
            create_technology_name("nodejs"),
            create_technology_name("postgresql")
        ],
        requirements=[
            "Home page with personal introduction",
            "Portfolio section showcasing projects",
            "About page with skills and experience",
            "Contact form with email integration",
            "Blog section for articles",
            "Responsive design for mobile devices"
        ],
        constraints={
            "budget": "low",
            "timeline": "1_month",
            "team_size": "1_developer",
            "hosting": "shared_hosting"
        },
        target_complexity=TaskComplexity.MODERATE
    )


def create_analytics_task() -> ComplexTask:
    """Create data analytics platform task."""
    return ComplexTask(
        name="Real-time Analytics Platform",
        description="Build a real-time data analytics platform for processing and visualizing large-scale data streams",
        technologies=[
            create_technology_name("python"),
            create_technology_name("kafka"),
            create_technology_name("elasticsearch"),
            create_technology_name("kibana"),
            create_technology_name("postgresql"),
            create_technology_name("redis"),
            create_technology_name("docker")
        ],
        requirements=[
            "Real-time data ingestion from multiple sources",
            "Stream processing and transformation",
            "Data storage and indexing",
            "Interactive dashboards and visualizations",
            "Alerting and notification system",
            "User management and access control",
            "Data export and reporting capabilities"
        ],
        constraints={
            "budget": "medium",
            "timeline": "4_months",
            "data_volume": "1TB_per_day",
            "latency": "sub_second"
        },
        target_complexity=TaskComplexity.COMPLEX
    )


async def demonstrate_recursive_generation(task: ComplexTask, generator: RecursivePromptGenerator):
    """Demonstrate recursive generation for a specific task."""
    
    print(f"\n{'='*80}")
    print(f"RECURSIVE GENERATION DEMO: {task.name}")
    print(f"{'='*80}")
    
    print(f"\n📋 Task Description:")
    print(f"   {task.description}")
    
    print(f"\n🔧 Technologies ({len(task.technologies)}):")
    tech_names = [tech.value for tech in task.technologies]
    for i, tech in enumerate(tech_names, 1):
        print(f"   {i:2d}. {tech}")
    
    print(f"\n📝 Requirements ({len(task.requirements)}):")
    for i, req in enumerate(task.requirements, 1):
        print(f"   {i:2d}. {req}")
    
    print(f"\n⚙️  Constraints:")
    for key, value in task.constraints.items():
        print(f"   • {key}: {value}")
    
    print(f"\n🎯 Target Complexity: {task.target_complexity.value}")
    
    print(f"\n🔄 Starting recursive generation...")
    
    try:
        # Generate recursive prompt
        result = await generator.generate_recursive_prompt(task)
        
        if result.is_success():
            composite_prompt = result.unwrap()
            
            print(f"\n✅ Generation completed successfully!")
            print(f"📊 Confidence Score: {composite_prompt.confidence_score:.2f}")
            print(f"🧩 Subtasks Generated: {len(composite_prompt.subtask_prompts)}")
            
            print(f"\n📁 Subtask Breakdown:")
            for i, (subtask_name, _) in enumerate(composite_prompt.subtask_prompts.items(), 1):
                print(f"   {i:2d}. {subtask_name}")
            
            # Show architecture overview
            print(f"\n🏗️  Architecture Overview:")
            print("   " + "\n   ".join(composite_prompt.architecture_overview.split('\n')[:10]))
            if len(composite_prompt.architecture_overview.split('\n')) > 10:
                print("   ...")
            
            # Show integration guide summary
            print(f"\n🔗 Integration Guide:")
            print("   " + "\n   ".join(composite_prompt.integration_guide.split('\n')[:8]))
            if len(composite_prompt.integration_guide.split('\n')) > 8:
                print("   ...")
            
            # Show main prompt preview
            print(f"\n📄 Main Prompt Preview:")
            main_lines = composite_prompt.main_prompt.split('\n')[:15]
            for line in main_lines:
                print(f"   {line}")
            if len(composite_prompt.main_prompt.split('\n')) > 15:
                print("   ...")
            
            return composite_prompt
            
        else:
            error_msg = result.unwrap_error()
            print(f"\n❌ Generation failed: {error_msg}")
            return None
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        logger.exception("Unexpected error during recursive generation")
        return None


async def save_results(task_name: str, composite_prompt, output_dir: Path):
    """Save generation results to files."""
    
    if not composite_prompt:
        return
    
    # Create output directory
    task_dir = output_dir / task_name.lower().replace(' ', '_')
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main prompt
    main_file = task_dir / "main_prompt.md"
    with open(main_file, 'w') as f:
        f.write(composite_prompt.main_prompt)
    
    # Save architecture overview
    arch_file = task_dir / "architecture_overview.md"
    with open(arch_file, 'w') as f:
        f.write(composite_prompt.architecture_overview)
    
    # Save integration guide
    integration_file = task_dir / "integration_guide.md"
    with open(integration_file, 'w') as f:
        f.write(composite_prompt.integration_guide)
    
    # Save deployment instructions
    deployment_file = task_dir / "deployment_instructions.md"
    with open(deployment_file, 'w') as f:
        f.write(composite_prompt.deployment_instructions)
    
    # Save individual subtask prompts
    subtasks_dir = task_dir / "subtasks"
    subtasks_dir.mkdir(exist_ok=True)
    
    for subtask_name, prompt_content in composite_prompt.subtask_prompts.items():
        subtask_file = subtasks_dir / f"{subtask_name.lower().replace(' ', '_')}.md"
        with open(subtask_file, 'w') as f:
            f.write(f"# {subtask_name}\n\n")
            f.write(prompt_content)
    
    # Save summary
    summary_file = task_dir / "summary.md"
    with open(summary_file, 'w') as f:
        f.write(f"# {task_name} - Generation Summary\n\n")
        f.write(f"**Confidence Score:** {composite_prompt.confidence_score:.2f}\n\n")
        f.write(f"**Generated Subtasks:** {len(composite_prompt.subtask_prompts)}\n\n")
        f.write("## Subtask List\n\n")
        for i, subtask_name in enumerate(composite_prompt.subtask_prompts.keys(), 1):
            f.write(f"{i}. {subtask_name}\n")
    
    print(f"\n💾 Results saved to: {task_dir}")


async def main():
    """Main demo function."""
    
    print("🚀 Recursive Prompt Generation Demo")
    print("====================================")
    
    # Create output directory
    output_dir = Path("output/recursive_generation_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create recursive generator
        print("\n🔧 Initializing recursive prompt generator...")
        generator = await create_recursive_generator()
        print("✅ Generator initialized successfully")
        
        # Create demo tasks
        tasks = [
            ("E-commerce Platform (Enterprise)", create_ecommerce_task()),
            ("Portfolio Website (Moderate)", create_portfolio_task()),
            ("Analytics Platform (Complex)", create_analytics_task())
        ]
        
        # Generate prompts for each task
        results = []
        for task_label, task in tasks:
            print(f"\n🎯 Processing: {task_label}")
            
            result = await demonstrate_recursive_generation(task, generator)
            results.append((task.name, result))
            
            # Save results
            if result:
                await save_results(task.name, result, output_dir)
            
            # Small delay between tasks
            await asyncio.sleep(1)
        
        # Summary
        print(f"\n{'='*80}")
        print("DEMO SUMMARY")
        print(f"{'='*80}")
        
        successful_generations = sum(1 for _, result in results if result is not None)
        total_tasks = len(results)
        
        print(f"\n📊 Results:")
        print(f"   • Total tasks processed: {total_tasks}")
        print(f"   • Successful generations: {successful_generations}")
        print(f"   • Success rate: {(successful_generations/total_tasks)*100:.1f}%")
        
        print(f"\n📁 All results saved to: {output_dir}")
        
        if successful_generations > 0:
            print(f"\n✨ Demo completed successfully!")
            print(f"   Check the output directory for detailed generation results.")
        else:
            print(f"\n⚠️  No successful generations. Check logs for details.")
            
    except Exception as e:
        print(f"\n💥 Demo failed: {str(e)}")
        logger.exception("Demo execution failed")


if __name__ == "__main__":
    asyncio.run(main())