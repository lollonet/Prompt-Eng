"""
Comprehensive tests for RecursivePromptGenerator system.

Tests the recursive task decomposition, subtask generation, and hierarchical composition
functionality with various complexity levels and decomposition strategies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List

from src.recursive_prompt_generator import (
    RecursivePromptGenerator,
    TaskDecomposer,
    ResultComposer,
    ComplexTask,
    Subtask,
    CompositePrompt,
    RecursiveConfig,
    TaskComplexity,
    DecompositionStrategy
)
from src.result_types import Success, Error
from src.types_advanced import create_technology_name, PromptConfigAdvanced


class TestTaskDecomposer:
    """Test TaskDecomposer functionality."""

    @pytest.fixture
    def mock_knowledge_manager(self):
        """Create mock AsyncKnowledgeManager."""
        return AsyncMock()

    @pytest.fixture
    def task_decomposer(self, mock_knowledge_manager):
        """Create TaskDecomposer for testing."""
        return TaskDecomposer(mock_knowledge_manager)

    @pytest.fixture
    def complex_microservices_task(self):
        """Create complex microservices task for testing."""
        return ComplexTask(
            name="E-commerce Platform",
            description="Build complete e-commerce platform with microservices",
            technologies=[
                create_technology_name("react"),
                create_technology_name("nodejs"),
                create_technology_name("python"),
                create_technology_name("postgresql"),
                create_technology_name("redis"),
                create_technology_name("docker"),
                create_technology_name("kubernetes")
            ],
            requirements=[
                "User authentication and management",
                "Product catalog and inventory",
                "Order processing and payment",
                "Real-time notifications",
                "Admin dashboard"
            ],
            constraints={"budget": "medium", "timeline": "6_months"},
            target_complexity=TaskComplexity.ENTERPRISE
        )

    @pytest.fixture
    def simple_web_app_task(self):
        """Create simple web application task for testing."""
        return ComplexTask(
            name="Portfolio Website",
            description="Build personal portfolio website",
            technologies=[
                create_technology_name("react"),
                create_technology_name("nodejs"),
                create_technology_name("postgresql")
            ],
            requirements=[
                "About page",
                "Portfolio showcase",
                "Contact form"
            ],
            constraints={"budget": "low", "timeline": "1_month"},
            target_complexity=TaskComplexity.SIMPLE
        )

    @pytest.mark.asyncio
    async def test_decompose_microservices_task(self, task_decomposer, complex_microservices_task):
        """Test decomposition of complex microservices task."""
        result = await task_decomposer.decompose(complex_microservices_task)
        
        assert result.is_success()
        subtasks = result.unwrap()
        
        # Should create multiple subtasks for microservices
        assert len(subtasks) >= 3
        
        # Should include infrastructure subtask
        infra_subtasks = [t for t in subtasks if "infrastructure" in t.name.lower()]
        assert len(infra_subtasks) >= 1
        
        # Infrastructure should depend on service subtasks
        infra_task = infra_subtasks[0]
        assert len(infra_task.dependencies) > 0

    @pytest.mark.asyncio
    async def test_decompose_simple_task(self, task_decomposer, simple_web_app_task):
        """Test decomposition of simple web application task."""
        result = await task_decomposer.decompose(simple_web_app_task)
        
        assert result.is_success()
        subtasks = result.unwrap()
        
        # Simple task should create fewer subtasks
        assert len(subtasks) >= 1
        assert len(subtasks) <= 5

    @pytest.mark.asyncio
    async def test_determine_strategy_microservices(self, task_decomposer, complex_microservices_task):
        """Test strategy determination for microservices architecture."""
        strategy = await task_decomposer._determine_strategy(complex_microservices_task)
        
        # Should choose microservices strategy for complex task with containers
        assert strategy == DecompositionStrategy.BY_SERVICES

    @pytest.mark.asyncio
    async def test_determine_strategy_multi_tier(self, task_decomposer, simple_web_app_task):
        """Test strategy determination for multi-tier application."""
        strategy = await task_decomposer._determine_strategy(simple_web_app_task)
        
        # Should choose appropriate strategy (tiers or features)
        assert strategy in [DecompositionStrategy.BY_TIERS, DecompositionStrategy.BY_FEATURES]

    @pytest.mark.asyncio
    async def test_analyze_technologies(self, task_decomposer, complex_microservices_task):
        """Test technology analysis functionality."""
        analysis = await task_decomposer._analyze_technologies(complex_microservices_task.technologies)
        
        assert "frontend" in analysis
        assert "backend" in analysis
        assert "database" in analysis
        assert "containers" in analysis
        
        # Should detect multiple backend services
        assert analysis["has_multiple_services"] or len(analysis["backend"]) > 1
        
        # Should detect containerization
        assert analysis["has_containerization"]

    def test_is_microservices_architecture(self, task_decomposer):
        """Test microservices architecture detection."""
        # Analysis with containerization
        analysis_with_containers = {
            "has_multiple_services": False,
            "has_containerization": True,
            "containers": ["docker", "kubernetes"]
        }
        assert task_decomposer._is_microservices_architecture(analysis_with_containers)
        
        # Analysis with multiple services
        analysis_with_services = {
            "has_multiple_services": True,
            "has_containerization": False,
            "containers": []
        }
        assert task_decomposer._is_microservices_architecture(analysis_with_services)
        
        # Analysis without microservices indicators
        analysis_simple = {
            "has_multiple_services": False,
            "has_containerization": False,
            "containers": []
        }
        assert not task_decomposer._is_microservices_architecture(analysis_simple)

    def test_has_circular_dependencies(self, task_decomposer):
        """Test circular dependency detection."""
        # Create subtasks with circular dependencies
        task1 = Subtask(
            id="task1",
            name="Task 1",
            description="First task",
            technologies=[],
            dependencies=["task2"],  # Depends on task2
            complexity=TaskComplexity.SIMPLE,
            config=MagicMock(),
            integration_points=[]
        )
        
        task2 = Subtask(
            id="task2",
            name="Task 2", 
            description="Second task",
            technologies=[],
            dependencies=["task1"],  # Depends on task1 - circular!
            complexity=TaskComplexity.SIMPLE,
            config=MagicMock(),
            integration_points=[]
        )
        
        # Should detect circular dependency
        assert task_decomposer._has_circular_dependencies([task1, task2])
        
        # Create subtasks without circular dependencies
        task3 = Subtask(
            id="task3",
            name="Task 3",
            description="Third task",
            technologies=[],
            dependencies=[],  # No dependencies
            complexity=TaskComplexity.SIMPLE,
            config=MagicMock(),
            integration_points=[]
        )
        
        task4 = Subtask(
            id="task4",
            name="Task 4",
            description="Fourth task", 
            technologies=[],
            dependencies=["task3"],  # Depends on task3 only
            complexity=TaskComplexity.SIMPLE,
            config=MagicMock(),
            integration_points=[]
        )
        
        # Should not detect circular dependency
        assert not task_decomposer._has_circular_dependencies([task3, task4])

    def test_technology_classification(self, task_decomposer):
        """Test technology classification methods."""
        # Frontend technologies
        assert task_decomposer._is_frontend_tech(create_technology_name("react"))
        assert task_decomposer._is_frontend_tech(create_technology_name("vue"))
        assert not task_decomposer._is_frontend_tech(create_technology_name("nodejs"))
        
        # Backend technologies
        assert task_decomposer._is_backend_tech(create_technology_name("nodejs"))
        assert task_decomposer._is_backend_tech(create_technology_name("python"))
        assert not task_decomposer._is_backend_tech(create_technology_name("react"))
        
        # Database technologies
        assert task_decomposer._is_database_tech(create_technology_name("postgresql"))
        assert task_decomposer._is_database_tech(create_technology_name("redis"))
        assert not task_decomposer._is_database_tech(create_technology_name("react"))


class TestResultComposer:
    """Test ResultComposer functionality."""

    @pytest.fixture
    def mock_template_factory(self):
        """Create mock TemplateFactory."""
        return MagicMock()

    @pytest.fixture
    def result_composer(self, mock_template_factory):
        """Create ResultComposer for testing."""
        return ResultComposer(mock_template_factory)

    @pytest.fixture
    def sample_subtasks(self):
        """Create sample subtasks for testing."""
        return [
            Subtask(
                id="frontend",
                name="Frontend Service",
                description="React frontend application",
                technologies=[create_technology_name("react")],
                dependencies=[],
                complexity=TaskComplexity.MODERATE,
                config=MagicMock(),
                integration_points=["api_contracts", "authentication"]
            ),
            Subtask(
                id="backend",
                name="Backend Service",
                description="Node.js API service",
                technologies=[create_technology_name("nodejs")],
                dependencies=[],
                complexity=TaskComplexity.MODERATE,
                config=MagicMock(),
                integration_points=["database_access", "external_apis"]
            ),
            Subtask(
                id="database",
                name="Database Service",
                description="PostgreSQL database setup",
                technologies=[create_technology_name("postgresql")],
                dependencies=[],
                complexity=TaskComplexity.SIMPLE,
                config=MagicMock(),
                integration_points=["schema_design", "migrations"]
            ),
            Subtask(
                id="infrastructure",
                name="Infrastructure",
                description="Docker and Kubernetes deployment",
                technologies=[create_technology_name("docker"), create_technology_name("kubernetes")],
                dependencies=["frontend", "backend", "database"],
                complexity=TaskComplexity.COMPLEX,
                config=MagicMock(),
                integration_points=["service_discovery", "load_balancing"]
            )
        ]

    @pytest.fixture
    def sample_results(self):
        """Create sample results for testing."""
        return [
            "# Frontend Implementation\n\nReact application with modern hooks and state management.",
            "# Backend API\n\nNode.js Express server with RESTful endpoints.",
            "# Database Schema\n\nPostgreSQL database with normalized tables.",
            "# Infrastructure Deployment\n\nDocker containers orchestrated with Kubernetes."
        ]

    @pytest.mark.asyncio
    async def test_compose_success(self, result_composer, sample_subtasks, sample_results):
        """Test successful composition of subtask results."""
        result = await result_composer.compose(sample_subtasks, sample_results)
        
        assert result.is_success()
        composite_prompt = result.unwrap()
        
        assert isinstance(composite_prompt, CompositePrompt)
        assert composite_prompt.main_prompt is not None
        assert len(composite_prompt.main_prompt) > 0
        assert len(composite_prompt.subtask_prompts) == len(sample_subtasks)
        assert composite_prompt.integration_guide is not None
        assert composite_prompt.deployment_instructions is not None
        assert composite_prompt.architecture_overview is not None
        assert 0.0 <= composite_prompt.confidence_score <= 1.0

    def test_order_by_dependencies(self, result_composer, sample_subtasks):
        """Test dependency-based ordering of subtasks."""
        ordered = result_composer._order_by_dependencies(sample_subtasks)
        
        # Infrastructure should come last (has dependencies)
        infra_task = next(t for t in ordered if t.id == "infrastructure")
        infra_index = ordered.index(infra_task)
        
        # All dependencies should come before infrastructure
        for dep_id in infra_task.dependencies:
            dep_task = next(t for t in ordered if t.id == dep_id)
            dep_index = ordered.index(dep_task)
            assert dep_index < infra_index

    @pytest.mark.asyncio
    async def test_create_integration_guide(self, result_composer, sample_subtasks):
        """Test integration guide creation."""
        guide = await result_composer._create_integration_guide(sample_subtasks)
        
        assert "Integration Guide" in guide
        assert "Integration Points" in guide
        assert "Dependency Flow" in guide
        
        # Should contain integration points from subtasks
        assert "api_contracts" in guide
        assert "authentication" in guide
        assert "database_access" in guide

    @pytest.mark.asyncio
    async def test_create_deployment_instructions(self, result_composer, sample_subtasks):
        """Test deployment instructions creation."""
        instructions = await result_composer._create_deployment_instructions(sample_subtasks)
        
        assert "Deployment Instructions" in instructions
        assert "Deployment Order" in instructions
        assert "Prerequisites" in instructions
        
        # Should include all subtask names
        for subtask in sample_subtasks:
            assert subtask.name in instructions

    @pytest.mark.asyncio
    async def test_create_architecture_overview(self, result_composer, sample_subtasks):
        """Test architecture overview creation."""
        overview = await result_composer._create_architecture_overview(sample_subtasks)
        
        assert "Architecture Overview" in overview
        assert "System Components" in overview
        assert "Technology Stack" in overview
        
        # Should include all technologies
        assert "react" in overview
        assert "nodejs" in overview
        assert "postgresql" in overview

    def test_calculate_confidence_score(self, result_composer, sample_subtasks, sample_results):
        """Test confidence score calculation."""
        score = result_composer._calculate_confidence_score(sample_subtasks, sample_results)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)


class TestRecursivePromptGenerator:
    """Test RecursivePromptGenerator integration."""

    @pytest.fixture
    def mock_base_generator(self):
        """Create mock ModernPromptGenerator."""
        generator = AsyncMock()
        generator.generate_prompt.return_value = Success("Generated prompt content")
        return generator

    @pytest.fixture
    def mock_knowledge_manager(self):
        """Create mock AsyncKnowledgeManager."""
        return AsyncMock()

    @pytest.fixture
    def mock_template_factory(self):
        """Create mock TemplateFactory."""
        return MagicMock()

    @pytest.fixture
    def recursive_config(self):
        """Create recursive configuration."""
        return RecursiveConfig(
            max_recursion_depth=3,
            enable_parallel_processing=True,
            min_subtask_complexity=0.3,
            composition_strategy="dependency_aware",
            enable_integration_validation=True
        )

    @pytest.fixture
    def recursive_generator(self, mock_base_generator, mock_knowledge_manager, 
                           mock_template_factory, recursive_config):
        """Create RecursivePromptGenerator for testing."""
        return RecursivePromptGenerator(
            base_generator=mock_base_generator,
            knowledge_manager=mock_knowledge_manager,
            template_factory=mock_template_factory,
            config=recursive_config
        )

    @pytest.fixture
    def complex_task(self):
        """Create complex task for testing."""
        return ComplexTask(
            name="Microservices Platform",
            description="Build complete microservices platform",
            technologies=[
                create_technology_name("react"),
                create_technology_name("nodejs"),
                create_technology_name("postgresql"),
                create_technology_name("docker")
            ],
            requirements=[
                "User management",
                "Product catalog",
                "Order processing"
            ],
            constraints={"timeline": "3_months"},
            target_complexity=TaskComplexity.COMPLEX
        )

    @pytest.mark.asyncio
    async def test_generate_recursive_prompt_success(self, recursive_generator, complex_task):
        """Test successful recursive prompt generation."""
        with patch.object(recursive_generator.task_decomposer, 'decompose') as mock_decompose, \
             patch.object(recursive_generator.result_composer, 'compose') as mock_compose:
            
            # Mock decomposition result
            mock_subtasks = [
                Subtask(
                    id="task1",
                    name="Frontend",
                    description="React frontend",
                    technologies=[create_technology_name("react")],
                    dependencies=[],
                    complexity=TaskComplexity.MODERATE,
                    config=MagicMock(),
                    integration_points=[]
                )
            ]
            mock_decompose.return_value = Success(mock_subtasks)
            
            # Mock composition result
            mock_composite = CompositePrompt(
                main_prompt="Main prompt content",
                subtask_prompts={"Frontend": "Frontend prompt"},
                integration_guide="Integration guide",
                deployment_instructions="Deployment instructions",
                architecture_overview="Architecture overview",
                confidence_score=0.85
            )
            mock_compose.return_value = Success(mock_composite)
            
            # Test generation
            result = await recursive_generator.generate_recursive_prompt(complex_task)
            
            assert result.is_success()
            composite_prompt = result.unwrap()
            assert isinstance(composite_prompt, CompositePrompt)
            assert composite_prompt.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_generate_recursive_prompt_decomposition_error(self, recursive_generator, complex_task):
        """Test recursive prompt generation with decomposition error."""
        with patch.object(recursive_generator.task_decomposer, 'decompose') as mock_decompose:
            
            # Mock decomposition error
            mock_decompose.return_value = Error("Decomposition failed")
            
            # Test generation
            result = await recursive_generator.generate_recursive_prompt(complex_task)
            
            assert result.is_error()
            assert "Decomposition failed" in result.unwrap_error()

    @pytest.mark.asyncio
    async def test_generate_recursive_prompt_composition_error(self, recursive_generator, complex_task):
        """Test recursive prompt generation with composition error."""
        with patch.object(recursive_generator.task_decomposer, 'decompose') as mock_decompose, \
             patch.object(recursive_generator.result_composer, 'compose') as mock_compose:
            
            # Mock successful decomposition
            mock_subtasks = [MagicMock()]
            mock_decompose.return_value = Success(mock_subtasks)
            
            # Mock composition error
            mock_compose.return_value = Error("Composition failed")
            
            # Test generation
            result = await recursive_generator.generate_recursive_prompt(complex_task)
            
            assert result.is_error()

    @pytest.mark.asyncio
    async def test_generate_subtasks_concurrent(self, recursive_generator):
        """Test concurrent subtask generation."""
        mock_subtasks = [
            Subtask(
                id="task1",
                name="Task 1",
                description="First task",
                technologies=[],
                dependencies=[],
                complexity=TaskComplexity.SIMPLE,
                config=MagicMock(),
                integration_points=[]
            ),
            Subtask(
                id="task2", 
                name="Task 2",
                description="Second task",
                technologies=[],
                dependencies=[],
                complexity=TaskComplexity.SIMPLE,
                config=MagicMock(),
                integration_points=[]
            )
        ]
        
        results = await recursive_generator._generate_subtasks_concurrent(mock_subtasks)
        
        assert len(results) == len(mock_subtasks)
        for result in results:
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_subtasks_sequential(self, recursive_generator):
        """Test sequential subtask generation."""
        mock_subtasks = [
            Subtask(
                id="task1",
                name="Task 1", 
                description="First task",
                technologies=[],
                dependencies=[],
                complexity=TaskComplexity.SIMPLE,
                config=MagicMock(),
                integration_points=[]
            )
        ]
        
        results = await recursive_generator._generate_subtasks_sequential(mock_subtasks)
        
        assert len(results) == len(mock_subtasks)
        for result in results:
            assert isinstance(result, str)
            assert len(result) > 0


class TestComplexTaskDataStructures:
    """Test data structures used in recursive generation."""

    def test_complex_task_creation(self):
        """Test ComplexTask creation and properties."""
        task = ComplexTask(
            name="Test Task",
            description="Test description",
            technologies=[create_technology_name("python")],
            requirements=["req1", "req2"],
            constraints={"budget": "low"},
            target_complexity=TaskComplexity.MODERATE
        )
        
        assert task.name == "Test Task"
        assert task.description == "Test description"
        assert len(task.technologies) == 1
        assert len(task.requirements) == 2
        assert task.constraints["budget"] == "low"
        assert task.target_complexity == TaskComplexity.MODERATE

    def test_subtask_creation(self):
        """Test Subtask creation and properties."""
        subtask = Subtask(
            id="test-id",
            name="Test Subtask",
            description="Test subtask description",
            technologies=[create_technology_name("nodejs")],
            dependencies=["dep1", "dep2"],
            complexity=TaskComplexity.SIMPLE,
            config=MagicMock(),
            integration_points=["api", "database"]
        )
        
        assert subtask.id == "test-id"
        assert subtask.name == "Test Subtask"
        assert len(subtask.technologies) == 1
        assert len(subtask.dependencies) == 2
        assert len(subtask.integration_points) == 2
        assert subtask.complexity == TaskComplexity.SIMPLE

    def test_composite_prompt_creation(self):
        """Test CompositePrompt creation and properties."""
        composite = CompositePrompt(
            main_prompt="Main content",
            subtask_prompts={"task1": "content1", "task2": "content2"},
            integration_guide="Integration info",
            deployment_instructions="Deployment info",
            architecture_overview="Architecture info",
            confidence_score=0.75
        )
        
        assert composite.main_prompt == "Main content"
        assert len(composite.subtask_prompts) == 2
        assert composite.integration_guide == "Integration info"
        assert composite.deployment_instructions == "Deployment info"
        assert composite.architecture_overview == "Architecture info"
        assert composite.confidence_score == 0.75

    def test_recursive_config_defaults(self):
        """Test RecursiveConfig default values."""
        config = RecursiveConfig()
        
        assert config.max_recursion_depth == 3
        assert config.enable_parallel_processing is True
        assert config.min_subtask_complexity == 0.3
        assert config.composition_strategy == "dependency_aware"
        assert config.enable_integration_validation is True

    def test_task_complexity_enum(self):
        """Test TaskComplexity enum values."""
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.MODERATE.value == "moderate"
        assert TaskComplexity.COMPLEX.value == "complex"
        assert TaskComplexity.ENTERPRISE.value == "enterprise"

    def test_decomposition_strategy_enum(self):
        """Test DecompositionStrategy enum values."""
        assert DecompositionStrategy.BY_SERVICES.value == "by_services"
        assert DecompositionStrategy.BY_TIERS.value == "by_tiers"
        assert DecompositionStrategy.BY_FEATURES.value == "by_features"
        assert DecompositionStrategy.BY_DOMAINS.value == "by_domains"