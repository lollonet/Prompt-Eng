"""
Recursive Prompt Generator System for complex task decomposition and composition.

Business Context: Extends ModernPromptGenerator with recursive capabilities to break down
complex, multi-component tasks into manageable subtasks and compose hierarchical solutions.

Why this approach: Leverages existing async architecture, Result types, and event system
to implement intelligent task decomposition with dependency-aware composition.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from .events import Event, EventType, event_bus
from .knowledge_manager_async import AsyncKnowledgeManager
from .prompt_generator_modern import ModernPromptGenerator
from .result_types import Error, Success
from .types_advanced import PromptConfigAdvanced, TechnologyName, create_technology_name, create_task_type
from .web_research.template_engines.template_factory import TemplateEngineFactory

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels for decomposition decisions."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class DecompositionStrategy(Enum):
    """Strategies for breaking down complex tasks."""
    BY_SERVICES = "by_services"  # Microservices architecture
    BY_TIERS = "by_tiers"       # N-tier application layers
    BY_FEATURES = "by_features"  # Feature-based decomposition
    BY_DOMAINS = "by_domains"    # Domain-driven design


@dataclass
class Subtask:
    """Represents a decomposed subtask with dependencies and context."""
    id: str
    name: str
    description: str
    technologies: List[TechnologyName]
    dependencies: List[str]  # IDs of prerequisite subtasks
    complexity: TaskComplexity
    config: PromptConfigAdvanced
    integration_points: List[str]  # API contracts, data flows, etc.


@dataclass
class ComplexTask:
    """Represents a high-level complex task for decomposition."""
    name: str
    description: str
    technologies: List[TechnologyName]
    requirements: List[str]
    constraints: Dict[str, Any]
    target_complexity: TaskComplexity


@dataclass
class CompositePrompt:
    """Result of recursive prompt generation with hierarchical structure."""
    main_prompt: str
    subtask_prompts: Dict[str, str]
    integration_guide: str
    deployment_instructions: str
    architecture_overview: str
    confidence_score: float


@dataclass
class RecursiveConfig:
    """Configuration for recursive prompt generation."""
    max_recursion_depth: int = 3
    enable_parallel_processing: bool = True
    min_subtask_complexity: float = 0.3
    composition_strategy: str = "dependency_aware"
    enable_integration_validation: bool = True


class TaskDecomposer:
    """Breaks down complex tasks into manageable subtasks."""

    def __init__(self, knowledge_manager: AsyncKnowledgeManager):
        self.knowledge_manager = knowledge_manager
        self.logger = logging.getLogger(__name__)

    async def decompose(self, task: ComplexTask) -> Union[Success[List[Subtask], str], Error[List[Subtask], str]]:
        """
        Decompose complex task into subtasks based on technology analysis.
        
        Returns Result containing list of subtasks or error message.
        """
        try:
            self.logger.info(f"Decomposing task: {task.name}")
            
            # Analyze technologies to determine decomposition strategy
            strategy = await self._determine_strategy(task)
            
            # Apply decomposition strategy
            if strategy == DecompositionStrategy.BY_SERVICES:
                subtasks = await self._decompose_by_services(task)
            elif strategy == DecompositionStrategy.BY_TIERS:
                subtasks = await self._decompose_by_tiers(task)
            elif strategy == DecompositionStrategy.BY_FEATURES:
                subtasks = await self._decompose_by_features(task)
            else:  # BY_DOMAINS
                subtasks = await self._decompose_by_domains(task)
            
            # Validate subtask dependencies
            if self._has_circular_dependencies(subtasks):
                return Error("Circular dependencies detected in task decomposition")
            
            self.logger.info(f"Successfully decomposed task into {len(subtasks)} subtasks")
            return Success(subtasks)
            
        except Exception as e:
            error_msg = f"Failed to decompose task {task.name}: {str(e)}"
            self.logger.error(error_msg)
            return Error(error_msg)

    async def _determine_strategy(self, task: ComplexTask) -> DecompositionStrategy:
        """Determine optimal decomposition strategy based on technologies."""
        tech_analysis = await self._analyze_technologies(task.technologies)
        
        # Check for microservices indicators
        if self._is_microservices_architecture(tech_analysis):
            return DecompositionStrategy.BY_SERVICES
        
        # Check for multi-tier application
        if self._is_multi_tier_application(tech_analysis):
            return DecompositionStrategy.BY_TIERS
        
        # Check for domain complexity
        if len(task.technologies) > 5 or task.target_complexity == TaskComplexity.ENTERPRISE:
            return DecompositionStrategy.BY_DOMAINS
        
        # Default to feature-based decomposition
        return DecompositionStrategy.BY_FEATURES

    async def _analyze_technologies(self, technologies: List[TechnologyName]) -> Dict[str, Any]:
        """Analyze technologies to understand architecture patterns."""
        tech_names = [str(tech) for tech in technologies]
        
        # Categorize technologies
        frontend_techs = [t for t in tech_names if t.lower() in ['react', 'vue', 'angular', 'nextjs']]
        backend_techs = [t for t in tech_names if t.lower() in ['nodejs', 'python', 'java', 'golang']]
        database_techs = [t for t in tech_names if t.lower() in ['postgresql', 'mysql', 'mongodb', 'redis']]
        container_techs = [t for t in tech_names if t.lower() in ['docker', 'kubernetes', 'compose']]
        cloud_techs = [t for t in tech_names if t.lower() in ['aws', 'azure', 'gcp', 'terraform']]
        
        return {
            'frontend': frontend_techs,
            'backend': backend_techs,
            'database': database_techs,
            'containers': container_techs,
            'cloud': cloud_techs,
            'total_count': len(tech_names),
            'has_multiple_services': len(backend_techs) > 1,
            'has_frontend_backend': len(frontend_techs) > 0 and len(backend_techs) > 0,
            'has_containerization': len(container_techs) > 0
        }

    def _is_microservices_architecture(self, analysis: Dict[str, Any]) -> bool:
        """Check if technologies indicate microservices architecture."""
        return (
            analysis['has_multiple_services'] or
            analysis['has_containerization'] or
            'kubernetes' in [t.lower() for t in analysis['containers']]
        )

    def _is_multi_tier_application(self, analysis: Dict[str, Any]) -> bool:
        """Check if technologies indicate multi-tier application."""
        return (
            analysis['has_frontend_backend'] and
            len(analysis['database']) > 0 and
            not analysis['has_multiple_services']
        )

    async def _decompose_by_services(self, task: ComplexTask) -> List[Subtask]:
        """Decompose task into microservices-based subtasks."""
        subtasks = []
        
        # Create service-specific subtasks
        services = await self._identify_services(task)
        
        for service_name, service_config in services.items():
            subtask = Subtask(
                id=str(uuid4()),
                name=f"{service_name} Service",
                description=f"Implement {service_name} microservice with {', '.join(service_config['technologies'])}",
                technologies=[create_technology_name(t) for t in service_config['technologies']],
                dependencies=service_config['dependencies'],
                complexity=TaskComplexity.MODERATE,
                config=self._create_subtask_config(task, service_config),
                integration_points=service_config['apis']
            )
            subtasks.append(subtask)
        
        # Add infrastructure subtask
        infra_subtask = await self._create_infrastructure_subtask(task, subtasks)
        subtasks.append(infra_subtask)
        
        return subtasks

    async def _decompose_by_tiers(self, task: ComplexTask) -> List[Subtask]:
        """Decompose task into application tier-based subtasks."""
        subtasks = []
        
        # Frontend tier
        if await self._has_frontend_technologies(task.technologies):
            frontend_subtask = Subtask(
                id=str(uuid4()),
                name="Frontend Layer",
                description="Implement user interface and client-side logic",
                technologies=[t for t in task.technologies if self._is_frontend_tech(t)],
                dependencies=[],
                complexity=TaskComplexity.MODERATE,
                config=self._create_subtask_config(task, {'tier': 'frontend'}),
                integration_points=['api_contracts', 'authentication']
            )
            subtasks.append(frontend_subtask)
        
        # Backend tier
        backend_subtask = Subtask(
            id=str(uuid4()),
            name="Backend Layer", 
            description="Implement business logic and API services",
            technologies=[t for t in task.technologies if self._is_backend_tech(t)],
            dependencies=[],
            complexity=TaskComplexity.MODERATE,
            config=self._create_subtask_config(task, {'tier': 'backend'}),
            integration_points=['database_access', 'external_apis']
        )
        subtasks.append(backend_subtask)
        
        # Database tier
        if await self._has_database_technologies(task.technologies):
            db_subtask = Subtask(
                id=str(uuid4()),
                name="Database Layer",
                description="Design and implement data persistence layer",
                technologies=[t for t in task.technologies if self._is_database_tech(t)],
                dependencies=[],
                complexity=TaskComplexity.SIMPLE,
                config=self._create_subtask_config(task, {'tier': 'database'}),
                integration_points=['schema_design', 'migrations', 'backup_strategy']
            )
            subtasks.append(db_subtask)
        
        return subtasks

    async def _decompose_by_features(self, task: ComplexTask) -> List[Subtask]:
        """Decompose task into feature-based subtasks."""
        subtasks = []
        
        # Extract features from requirements
        features = await self._extract_features(task.requirements)
        
        for feature in features:
            subtask = Subtask(
                id=str(uuid4()),
                name=f"{feature['name']} Feature",
                description=feature['description'],
                technologies=task.technologies,  # All features use same tech stack
                dependencies=feature['dependencies'],
                complexity=TaskComplexity.SIMPLE,
                config=self._create_subtask_config(task, feature),
                integration_points=feature['integration_points']
            )
            subtasks.append(subtask)
        
        return subtasks

    async def _decompose_by_domains(self, task: ComplexTask) -> List[Subtask]:
        """Decompose task into domain-driven subtasks."""
        # This would implement domain-driven design decomposition
        # For now, fallback to services decomposition
        return await self._decompose_by_services(task)

    def _has_circular_dependencies(self, subtasks: List[Subtask]) -> bool:
        """Check for circular dependencies in subtasks."""
        # Build dependency graph
        graph = {subtask.id: subtask.dependencies for subtask in subtasks}
        
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False

    # Helper methods for technology classification
    def _is_frontend_tech(self, tech: TechnologyName) -> bool:
        frontend_techs = ['react', 'vue', 'angular', 'nextjs', 'svelte']
        return str(tech).lower() in frontend_techs

    def _is_backend_tech(self, tech: TechnologyName) -> bool:
        backend_techs = ['nodejs', 'python', 'java', 'golang', 'ruby', 'php', 'csharp']
        return str(tech).lower() in backend_techs

    def _is_database_tech(self, tech: TechnologyName) -> bool:
        database_techs = ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch']
        return str(tech).lower() in database_techs

    async def _has_frontend_technologies(self, technologies: List[TechnologyName]) -> bool:
        return any(self._is_frontend_tech(t) for t in technologies)

    async def _has_database_technologies(self, technologies: List[TechnologyName]) -> bool:
        return any(self._is_database_tech(t) for t in technologies)

    def _create_subtask_config(self, task: ComplexTask, context: Dict[str, Any]) -> PromptConfigAdvanced:
        """Create PromptConfigAdvanced for subtask."""
        # Create proper configuration matching PromptConfigAdvanced requirements
        return PromptConfigAdvanced(
            technologies=task.technologies,
            task_type=create_task_type("deployment"),
            code_requirements=task.description,
            task_description=task.description
        )

    async def _identify_services(self, task: ComplexTask) -> Dict[str, Dict[str, Any]]:
        """Identify microservices from task requirements."""
        # Simplified service identification
        services = {
            'user': {
                'technologies': ['nodejs', 'postgresql'],
                'dependencies': [],
                'apis': ['auth', 'profile']
            },
            'product': {
                'technologies': ['python', 'redis'],
                'dependencies': [],
                'apis': ['catalog', 'inventory']
            }
        }
        return services

    async def _create_infrastructure_subtask(self, task: ComplexTask, subtasks: List[Subtask]) -> Subtask:
        """Create infrastructure deployment subtask."""
        return Subtask(
            id=str(uuid4()),
            name="Infrastructure",
            description="Deploy and orchestrate all services",
            technologies=[create_technology_name('docker'), create_technology_name('kubernetes')],
            dependencies=[s.id for s in subtasks],  # Depends on all services
            complexity=TaskComplexity.COMPLEX,
            config=self._create_subtask_config(task, {'tier': 'infrastructure'}),
            integration_points=['service_discovery', 'load_balancing', 'monitoring']
        )

    async def _extract_features(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Extract features from requirements."""
        # Simplified feature extraction
        features = [
            {
                'name': 'Authentication',
                'description': 'User login and registration',
                'dependencies': [],
                'integration_points': ['session_management', 'security']
            },
            {
                'name': 'Core Functionality',
                'description': 'Main application features',
                'dependencies': ['auth'],
                'integration_points': ['data_access', 'business_logic']
            }
        ]
        return features


class ResultComposer:
    """Composes subtask results into cohesive hierarchical prompts."""

    def __init__(self, template_factory: TemplateEngineFactory):
        self.template_factory = template_factory
        self.logger = logging.getLogger(__name__)

    async def compose(
        self, 
        subtasks: List[Subtask], 
        results: List[str]
    ) -> Union[Success[CompositePrompt, str], Error[CompositePrompt, str]]:
        """
        Compose subtask results into hierarchical prompt structure.
        
        Returns Result containing CompositePrompt or error message.
        """
        try:
            self.logger.info(f"Composing {len(subtasks)} subtask results")
            
            # Order subtasks by dependencies
            ordered_subtasks = self._order_by_dependencies(subtasks)
            
            # Create integration guide
            integration_guide = await self._create_integration_guide(ordered_subtasks)
            
            # Create deployment instructions
            deployment_instructions = await self._create_deployment_instructions(ordered_subtasks)
            
            # Create architecture overview
            architecture_overview = await self._create_architecture_overview(ordered_subtasks)
            
            # Compose main prompt
            main_prompt = await self._compose_main_prompt(ordered_subtasks, results)
            
            # Create subtask prompt mapping
            subtask_prompts = {
                subtask.name: result 
                for subtask, result in zip(ordered_subtasks, results)
            }
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(ordered_subtasks, results)
            
            composite_prompt = CompositePrompt(
                main_prompt=main_prompt,
                subtask_prompts=subtask_prompts,
                integration_guide=integration_guide,
                deployment_instructions=deployment_instructions,
                architecture_overview=architecture_overview,
                confidence_score=confidence_score
            )
            
            self.logger.info("Successfully composed hierarchical prompt")
            return Success(composite_prompt)
            
        except Exception as e:
            error_msg = f"Failed to compose results: {str(e)}"
            self.logger.error(error_msg)
            return Error(error_msg)

    def _order_by_dependencies(self, subtasks: List[Subtask]) -> List[Subtask]:
        """Order subtasks based on dependency relationships."""
        # Topological sort implementation
        graph = {task.id: task for task in subtasks}
        in_degree = {task.id: 0 for task in subtasks}
        
        # Calculate in-degrees
        for task in subtasks:
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.id] += 1
        
        # Kahn's algorithm for topological sorting
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        ordered = []
        
        while queue:
            current_id = queue.pop(0)
            ordered.append(graph[current_id])
            
            # Update dependencies
            for task in subtasks:
                if current_id in task.dependencies:
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        queue.append(task.id)
        
        return ordered

    async def _create_integration_guide(self, subtasks: List[Subtask]) -> str:
        """Create integration guide for subtasks."""
        integration_points = []
        
        for subtask in subtasks:
            integration_points.extend(subtask.integration_points)
        
        unique_points = list(set(integration_points))
        
        guide = "# Integration Guide\n\n"
        guide += "## Integration Points\n\n"
        
        for point in unique_points:
            guide += f"- **{point}**: Integration specifications for {point}\n"
        
        guide += "\n## Dependency Flow\n\n"
        for subtask in subtasks:
            if subtask.dependencies:
                deps = ", ".join(subtask.dependencies)
                guide += f"- {subtask.name} depends on: {deps}\n"
        
        return guide

    async def _create_deployment_instructions(self, subtasks: List[Subtask]) -> str:
        """Create deployment instructions for all subtasks."""
        instructions = "# Deployment Instructions\n\n"
        instructions += "## Deployment Order\n\n"
        
        for i, subtask in enumerate(subtasks, 1):
            instructions += f"{i}. **{subtask.name}**\n"
            instructions += f"   - Technologies: {', '.join([str(t) for t in subtask.technologies])}\n"
            instructions += f"   - Complexity: {subtask.complexity.value}\n\n"
        
        instructions += "## Prerequisites\n\n"
        instructions += "- Ensure all dependencies are deployed before dependent services\n"
        instructions += "- Validate integration points between services\n"
        instructions += "- Monitor deployment progress and health checks\n"
        
        return instructions

    async def _create_architecture_overview(self, subtasks: List[Subtask]) -> str:
        """Create architecture overview of the system."""
        overview = "# Architecture Overview\n\n"
        overview += "## System Components\n\n"
        
        for subtask in subtasks:
            overview += f"### {subtask.name}\n"
            overview += f"- **Description**: {subtask.description}\n"
            overview += f"- **Technologies**: {', '.join([str(t) for t in subtask.technologies])}\n"
            overview += f"- **Integration Points**: {', '.join(subtask.integration_points)}\n\n"
        
        overview += "## Technology Stack\n\n"
        all_technologies = set()
        for subtask in subtasks:
            all_technologies.update([str(t) for t in subtask.technologies])
        
        for tech in sorted(all_technologies):
            overview += f"- {tech}\n"
        
        return overview

    async def _compose_main_prompt(self, subtasks: List[Subtask], results: List[str]) -> str:
        """Compose main hierarchical prompt."""
        main_prompt = "# Hierarchical System Implementation\n\n"
        main_prompt += "This is a comprehensive implementation guide for a complex system broken down into manageable components.\n\n"
        
        main_prompt += "## Implementation Strategy\n\n"
        main_prompt += "Follow the dependency order below to implement each component:\n\n"
        
        for i, (subtask, result) in enumerate(zip(subtasks, results), 1):
            main_prompt += f"### {i}. {subtask.name}\n\n"
            main_prompt += f"{result}\n\n"
            main_prompt += "---\n\n"
        
        return main_prompt

    def _calculate_confidence_score(self, subtasks: List[Subtask], results: List[str]) -> float:
        """Calculate confidence score for the composition."""
        # Simple confidence calculation based on result quality
        total_score = 0.0
        
        for subtask, result in zip(subtasks, results):
            # Base score on result length and complexity
            base_score = min(len(result) / 1000, 1.0)  # Normalize by expected length
            
            # Adjust for complexity
            complexity_multiplier = {
                TaskComplexity.SIMPLE: 0.9,
                TaskComplexity.MODERATE: 0.8,
                TaskComplexity.COMPLEX: 0.7,
                TaskComplexity.ENTERPRISE: 0.6
            }
            
            score = base_score * complexity_multiplier.get(subtask.complexity, 0.5)
            total_score += score
        
        return total_score / len(subtasks) if subtasks else 0.0


class RecursivePromptGenerator:
    """
    Recursive prompt generation system that breaks down complex tasks
    into manageable subtasks and composes results hierarchically.
    """

    def __init__(
        self, 
        base_generator: ModernPromptGenerator,
        knowledge_manager: AsyncKnowledgeManager,
        template_factory: TemplateEngineFactory,
        config: RecursiveConfig
    ):
        self.base_generator = base_generator
        self.knowledge_manager = knowledge_manager
        self.template_factory = template_factory
        self.config = config
        self.task_decomposer = TaskDecomposer(knowledge_manager)
        self.result_composer = ResultComposer(template_factory)
        self.logger = logging.getLogger(__name__)

    async def generate_recursive_prompt(
        self, 
        complex_task: ComplexTask
    ) -> Union[Success[CompositePrompt, str], Error[CompositePrompt, str]]:
        """
        Generate prompts recursively by breaking down complex tasks.
        
        Main entry point for recursive prompt generation.
        """
        try:
            self.logger.info(f"Starting recursive prompt generation for: {complex_task.name}")
            
            # Publish start event
            start_event = Event(
                event_type=EventType.PROMPT_GENERATION_STARTED,
                source="recursive_prompt_generator",
                payload={
                    "task_name": complex_task.name,
                    "technologies": [str(t) for t in complex_task.technologies],
                    "correlation_id": str(uuid4())
                }
            )
            await event_bus.publish(start_event)
            
            # 1. Decompose high-level task into subtasks
            decomposition_result = await self.task_decomposer.decompose(complex_task)
            if decomposition_result.is_error():
                return decomposition_result
            
            subtasks = decomposition_result.unwrap()
            self.logger.info(f"Decomposed into {len(subtasks)} subtasks")
            
            # 2. Generate prompts for each subtask
            if self.config.enable_parallel_processing:
                # Concurrent generation
                results = await self._generate_subtasks_concurrent(subtasks)
            else:
                # Sequential generation
                results = await self._generate_subtasks_sequential(subtasks)
            
            # 3. Compose results hierarchically
            composition_result = await self.result_composer.compose(subtasks, results)
            if composition_result.is_error():
                return composition_result
            
            composite_prompt = composition_result.unwrap()
            
            # Publish completion event
            completion_event = Event(
                event_type=EventType.PROMPT_GENERATION_COMPLETED,
                source="recursive_prompt_generator",
                payload={
                    "task_name": complex_task.name,
                    "subtask_count": len(subtasks),
                    "confidence_score": composite_prompt.confidence_score,
                    "correlation_id": start_event.payload["correlation_id"]
                }
            )
            await event_bus.publish(completion_event)
            
            self.logger.info(f"Successfully generated recursive prompt with confidence {composite_prompt.confidence_score:.2f}")
            return Success(composite_prompt)
            
        except Exception as e:
            error_msg = f"Failed to generate recursive prompt for {complex_task.name}: {str(e)}"
            self.logger.error(error_msg)
            return Error(error_msg)

    async def _generate_subtasks_concurrent(self, subtasks: List[Subtask]) -> List[str]:
        """Generate prompts for subtasks concurrently."""
        tasks = [
            self.base_generator.generate_prompt(subtask.config)
            for subtask in subtasks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert results to strings, handling errors
        prompt_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"Failed to generate prompt for subtask {subtasks[i].name}: {result}")
                prompt_results.append(f"# Error generating prompt for {subtasks[i].name}\n\n{str(result)}")
            elif hasattr(result, 'unwrap'):
                # Handle Result type
                if result.is_success():
                    prompt_results.append(result.unwrap())
                else:
                    prompt_results.append(f"# Error: {result.unwrap_error()}")
            else:
                prompt_results.append(str(result))
        
        return prompt_results

    async def _generate_subtasks_sequential(self, subtasks: List[Subtask]) -> List[str]:
        """Generate prompts for subtasks sequentially."""
        results = []
        
        for subtask in subtasks:
            try:
                result = await self.base_generator.generate_prompt(subtask.config)
                if hasattr(result, 'unwrap') and result.is_success():
                    results.append(result.unwrap())
                else:
                    results.append(str(result))
            except Exception as e:
                self.logger.warning(f"Failed to generate prompt for subtask {subtask.name}: {e}")
                results.append(f"# Error generating prompt for {subtask.name}\n\n{str(e)}")
        
        return results