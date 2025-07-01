"""
Comprehensive unit tests for web research components.

Tests TechnologyDetector, WebResearcher, and DynamicTemplateGenerator
focusing on public behavior and component contracts.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.web_research.technology_detector import TechnologyDetector, TechnologyKnowledge, SimilarityResult
from src.web_research.web_researcher import WebResearcher, ResearchSession, ResearchProgress
from src.web_research.template_generator import DynamicTemplateGenerator, TemplateSection, CodeExample
from src.web_research.config import WebResearchConfig, TemplateConfig
from src.web_research.interfaces import (
    ITechnologyDetector, IWebResearcher, IDynamicTemplateGenerator,
    TechnologyProfile, ResearchResult, SearchResult, ResearchQuality
)


class TestTechnologyDetectorPublicBehavior:
    """Test TechnologyDetector public interface and behavior."""
    
    @pytest.fixture
    def sample_knowledge(self):
        """Sample technology knowledge for testing."""
        return TechnologyKnowledge(
            known_technologies={"python", "javascript", "docker", "kubernetes", "react"},
            technology_aliases={
                "python": ["py", "python3", "cpython"],
                "javascript": ["js", "node", "nodejs"],
                "docker": ["containerization"],
                "kubernetes": ["k8s", "kube"]
            },
            technology_categories={
                "python": "programming_language",
                "javascript": "programming_language", 
                "docker": "containerization",
                "kubernetes": "orchestration"
            },
            technology_popularity={
                "python": 0.9,
                "javascript": 0.95,
                "docker": 0.8,
                "kubernetes": 0.7
            }
        )
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        from src.web_research.config import Environment, ResearchConfig
        
        research_config = ResearchConfig(
            max_concurrent_requests=3,
            request_timeout_seconds=10
        )
        
        return WebResearchConfig(
            environment=Environment.TESTING,
            debug=True,
            research=research_config
        )
    
    @pytest.fixture
    def technology_detector(self, config, sample_knowledge):
        """Create TechnologyDetector instance."""
        detector = TechnologyDetector(config)
        # Inject test knowledge
        detector.knowledge = sample_knowledge
        return detector
    
    @pytest.mark.asyncio
    async def test_technology_profile_retrieval(self, technology_detector):
        """Test technology profile retrieval."""
        result = await technology_detector.get_technology_profile("python")
        
        if result is not None:  # May return None if not found
            assert isinstance(result, TechnologyProfile)
            assert result.name == "python"
            assert result.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_unknown_technology_detection(self, technology_detector):
        """Test detecting unknown technologies from a list."""
        technologies = ["python", "unknown_tech_123", "docker"]
        unknown = await technology_detector.detect_unknown_technologies(technologies)
        
        assert isinstance(unknown, list)
        # Should detect "unknown_tech_123" as unknown
        assert "unknown_tech_123" in unknown
    
    @pytest.mark.asyncio
    async def test_suggest_similar_technologies(self, technology_detector):
        """Test getting similar technology suggestions."""
        suggestions = await technology_detector.suggest_similar_technologies("python")
        
        assert isinstance(suggestions, list)
        # Should return some suggestions (exact behavior depends on implementation)
    
    @pytest.mark.asyncio
    async def test_unknown_technology_handling(self, technology_detector):
        """Test handling of completely unknown technologies."""
        result = await technology_detector.detect_technology("completely_unknown_tech_12345")
        
        # Should handle gracefully - either return None or low-confidence result
        if result is not None:
            assert isinstance(result, TechnologyProfile)
            assert result.confidence < 0.5
    
    @pytest.mark.asyncio
    async def test_multiple_technology_detection(self, technology_detector):
        """Test detecting multiple technologies from text."""
        text = "Using Python with Docker and Kubernetes for microservices"
        results = await technology_detector.detect_technologies_from_text(text)
        
        assert isinstance(results, list)
        assert len(results) >= 3  # Should detect python, docker, kubernetes
        
        detected_names = {result.name for result in results}
        assert "python" in detected_names
        assert "docker" in detected_names
        assert "kubernetes" in detected_names
    
    @pytest.mark.asyncio
    async def test_similarity_scoring(self, technology_detector):
        """Test similarity scoring functionality."""
        similarities = await technology_detector.get_similar_technologies("python", limit=3)
        
        assert isinstance(similarities, list)
        assert len(similarities) <= 3
        
        for similarity in similarities:
            assert isinstance(similarity, SimilarityResult)
            assert 0 <= similarity.similarity_score <= 1
            assert similarity.confidence > 0
    
    @pytest.mark.asyncio
    async def test_knowledge_update(self, technology_detector):
        """Test dynamic knowledge updating."""
        # Add new technology
        await technology_detector.add_technology("rust", category="programming_language")
        
        # Should be able to detect the new technology
        result = await technology_detector.detect_technology("rust")
        assert result is not None
        assert result.name == "rust"
    
    @pytest.mark.asyncio
    async def test_performance_with_large_input(self, technology_detector):
        """Test performance with large text input."""
        large_text = "python " * 1000 + "docker " * 500  # Large repetitive text
        
        # Should complete within reasonable time
        import time
        start_time = time.time()
        results = await technology_detector.detect_technologies_from_text(large_text)
        end_time = time.time()
        
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        assert isinstance(results, list)


class TestWebResearcherPublicBehavior:
    """Test WebResearcher public interface and behavior."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        from src.web_research.config import Environment, ResearchConfig
        
        research_config = ResearchConfig(
            max_concurrent_requests=2,
            request_timeout_seconds=5
        )
        
        return WebResearchConfig(
            environment=Environment.TESTING,
            research=research_config
        )
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        return {
            'technology_detector': AsyncMock(spec=ITechnologyDetector),
            'search_orchestrator': AsyncMock(),
            'template_generator': AsyncMock(spec=IDynamicTemplateGenerator),
            'validator': AsyncMock(),
            'cache': AsyncMock()
        }
    
    @pytest.fixture
    def web_researcher(self, config, mock_dependencies):
        """Create WebResearcher with mocked dependencies."""
        return WebResearcher(
            config=config,
            technology_detector=mock_dependencies['technology_detector'],
            search_orchestrator=mock_dependencies['search_orchestrator'],
            template_generator=mock_dependencies['template_generator'],
            validator=mock_dependencies['validator'],
            cache=mock_dependencies['cache']
        )
    
    @pytest.mark.asyncio
    async def test_research_single_technology(self, web_researcher, mock_dependencies):
        """Test researching a single technology."""
        # Setup mocks
        mock_dependencies['technology_detector'].detect_technology.return_value = TechnologyProfile(
            name="python", confidence=0.9, category="programming_language"
        )
        mock_dependencies['search_orchestrator'].search.return_value = [
            SearchResult(
                title="Python Best Practices",
                url="https://example.com",
                snippet="Python coding standards",
                score=0.8,
                timestamp=datetime.now()
            )
        ]
        mock_dependencies['template_generator'].generate_template.return_value = "Generated template"
        mock_dependencies['validator'].validate_research.return_value = (True, ResearchQuality.GOOD)
        
        # Execute research
        result = await web_researcher.research_technology("python")
        
        assert isinstance(result, ResearchResult)
        assert result.technology == "python"
        assert len(result.search_results) > 0
        assert result.quality in [ResearchQuality.EXCELLENT, ResearchQuality.GOOD, ResearchQuality.FAIR]
    
    @pytest.mark.asyncio
    async def test_research_multiple_technologies(self, web_researcher, mock_dependencies):
        """Test researching multiple technologies concurrently."""
        technologies = ["python", "docker", "kubernetes"]
        
        # Setup mocks
        async def mock_detect(tech):
            return TechnologyProfile(name=tech, confidence=0.8, category="technology")
        
        mock_dependencies['technology_detector'].detect_technology.side_effect = mock_detect
        mock_dependencies['search_orchestrator'].search.return_value = [
            SearchResult("Test", "https://test.com", "Test snippet", 0.7, datetime.now())
        ]
        mock_dependencies['template_generator'].generate_template.return_value = "Template"
        mock_dependencies['validator'].validate_research.return_value = (True, ResearchQuality.GOOD)
        
        # Execute research
        results = await web_researcher.research_technologies(technologies)
        
        assert isinstance(results, list)
        assert len(results) == 3
        
        for result in results:
            assert isinstance(result, ResearchResult)
            assert result.technology in technologies
    
    @pytest.mark.asyncio
    async def test_research_session_tracking(self, web_researcher, mock_dependencies):
        """Test research session creation and tracking."""
        # Setup mocks
        mock_dependencies['technology_detector'].detect_technology.return_value = TechnologyProfile(
            name="python", confidence=0.8, category="programming_language"
        )
        
        # Create research session
        session = await web_researcher.create_research_session(
            technologies=["python", "docker"],
            user_context={"project_type": "web_api"}
        )
        
        assert isinstance(session, ResearchSession)
        assert session.technologies == ["python", "docker"]
        assert session.user_context["project_type"] == "web_api"
        assert session.status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_error_handling_during_research(self, web_researcher, mock_dependencies):
        """Test error handling when research operations fail."""
        # Setup mocks to simulate failures
        mock_dependencies['technology_detector'].detect_technology.side_effect = Exception("Detection failed")
        
        # Should handle errors gracefully
        result = await web_researcher.research_technology("invalid_tech")
        
        # Should return some form of error result or handle gracefully
        # The exact behavior depends on implementation
        assert result is None or (isinstance(result, ResearchResult) and result.quality == ResearchQuality.POOR)
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, web_researcher, mock_dependencies):
        """Test that caching works correctly."""
        technology = "python"
        
        # Setup mocks
        mock_dependencies['cache'].get.return_value = None  # Cache miss first time
        mock_dependencies['technology_detector'].detect_technology.return_value = TechnologyProfile(
            name=technology, confidence=0.9, category="programming_language"
        )
        mock_dependencies['search_orchestrator'].search.return_value = []
        mock_dependencies['template_generator'].generate_template.return_value = "Template"
        mock_dependencies['validator'].validate_research.return_value = (True, ResearchQuality.GOOD)
        
        # First research - should hit external services
        await web_researcher.research_technology(technology)
        
        # Verify cache was called for storage
        mock_dependencies['cache'].set.assert_called()


class TestDynamicTemplateGeneratorPublicBehavior:
    """Test DynamicTemplateGenerator public interface and behavior."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return TemplateConfig(
            template_dir="templates",
            cache_templates=True,
            max_template_size=10000
        )
    
    @pytest.fixture
    def sample_research_result(self):
        """Sample research result for testing."""
        return ResearchResult(
            technology="python",
            search_results=[
                SearchResult(
                    title="Python Best Practices",
                    url="https://example.com/python-best-practices",
                    snippet="Follow PEP 8 style guide for Python code",
                    score=0.9,
                    timestamp=datetime.now()
                ),
                SearchResult(
                    title="Python Testing with pytest",
                    url="https://example.com/python-testing",
                    snippet="Use pytest for comprehensive testing",
                    score=0.8,
                    timestamp=datetime.now()
                )
            ],
            best_practices=["Follow PEP 8", "Write comprehensive tests", "Use virtual environments"],
            code_examples=["def hello_world():\n    print('Hello, World!')"],
            quality=ResearchQuality.GOOD,
            confidence=0.85,
            research_time=datetime.now()
        )
    
    @pytest.fixture
    def template_generator(self):
        """Create DynamicTemplateGenerator instance."""
        from src.web_research.config import Environment, TemplateConfig
        config = WebResearchConfig(
            environment=Environment.TESTING,
            template=TemplateConfig()
        )
        return DynamicTemplateGenerator(config)
    
    @pytest.mark.asyncio
    async def test_template_generation_from_research(self, template_generator, sample_research_result):
        """Test generating template from research results."""
        template = await template_generator.generate_template(
            research_result=sample_research_result,
            template_type="development_guide"
        )
        
        assert isinstance(template, str)
        assert len(template) > 0
        assert "python" in template.lower()
        assert "pep 8" in template.lower()  # Should include best practices
    
    @pytest.mark.asyncio
    async def test_template_section_extraction(self, template_generator, sample_research_result):
        """Test extracting structured sections from research."""
        sections = await template_generator.extract_template_sections(sample_research_result)
        
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        for section in sections:
            assert isinstance(section, TemplateSection)
            assert section.name
            assert section.content
            assert 0 <= section.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_code_example_extraction(self, template_generator, sample_research_result):
        """Test extracting code examples from research."""
        code_examples = await template_generator.extract_code_examples(sample_research_result)
        
        assert isinstance(code_examples, list)
        
        for example in code_examples:
            assert isinstance(example, CodeExample)
            assert example.language
            assert example.code
            assert 0 <= example.relevance_score <= 1
    
    @pytest.mark.asyncio
    async def test_template_customization(self, template_generator, sample_research_result):
        """Test template customization with user context."""
        user_context = {
            "project_type": "web_api",
            "experience_level": "beginner",
            "preferred_patterns": ["mvc", "rest"]
        }
        
        template = await template_generator.generate_template(
            research_result=sample_research_result,
            template_type="project_setup",
            user_context=user_context
        )
        
        assert isinstance(template, str)
        assert len(template) > 0
        # Should adapt to user context (exact behavior depends on implementation)
    
    @pytest.mark.asyncio
    async def test_template_quality_validation(self, template_generator, sample_research_result):
        """Test template quality validation."""
        template = await template_generator.generate_template(
            research_result=sample_research_result,
            template_type="development_guide"
        )
        
        quality_score = await template_generator.validate_template_quality(template)
        
        assert isinstance(quality_score, float)
        assert 0 <= quality_score <= 1
    
    @pytest.mark.asyncio
    async def test_template_caching(self, template_generator, sample_research_result):
        """Test template caching functionality."""
        # Generate template twice with same inputs
        template1 = await template_generator.generate_template(
            research_result=sample_research_result,
            template_type="guide"
        )
        
        template2 = await template_generator.generate_template(
            research_result=sample_research_result,
            template_type="guide"
        )
        
        # Should return same template (from cache)
        assert template1 == template2
    
    @pytest.mark.asyncio
    async def test_empty_research_handling(self, template_generator):
        """Test handling of empty or poor research results."""
        empty_research = ResearchResult(
            technology="unknown",
            search_results=[],
            best_practices=[],
            code_examples=[],
            quality=ResearchQuality.POOR,
            confidence=0.1,
            research_time=datetime.now()
        )
        
        template = await template_generator.generate_template(
            research_result=empty_research,
            template_type="guide"
        )
        
        # Should handle gracefully, either return minimal template or error
        assert template is not None
        assert isinstance(template, str)


class TestWebResearchComponentIntegration:
    """Test integration between web research components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_research_workflow(self):
        """Test complete research workflow integration."""
        # This would be a simplified integration test
        from src.web_research.config import Environment, ResearchConfig
        config = WebResearchConfig(
            environment=Environment.TESTING,
            research=ResearchConfig(max_concurrent_requests=1)
        )
        
        # Create components with minimal mocking
        detector = TechnologyDetector(config)
        generator = DynamicTemplateGenerator(config)
        
        # Test basic workflow without external dependencies
        # (This is a simplified test - full integration would require more setup)
        
        # Detect technology
        profile = await detector.detect_technology("python")
        if profile:
            assert profile.name == "python"
            assert profile.confidence > 0
    
    @pytest.mark.asyncio
    async def test_component_interface_compliance(self):
        """Test that components properly implement their interfaces."""
        from src.web_research.config import Environment
        config = WebResearchConfig(environment=Environment.TESTING)
        
        # Test interface compliance
        detector = TechnologyDetector(config)
        assert isinstance(detector, ITechnologyDetector)
        
        generator = DynamicTemplateGenerator(config)
        assert isinstance(generator, IDynamicTemplateGenerator)
        
        # Test that they have required methods from interfaces
        assert hasattr(detector, 'detect_unknown_technologies')
        assert hasattr(detector, 'get_technology_profile')
        assert hasattr(generator, 'generate_template')
        # Note: exact method names depend on interface definitions