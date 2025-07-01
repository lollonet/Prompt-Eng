"""
Comprehensive unit tests for individual template engines.

Tests the specialized template generators that handle different technology stacks
and deployment scenarios (Docker, Ansible, Kubernetes, etc.).
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

# Import template engines
from src.web_research.template_engines.docker_engine import DockerTemplateEngine, DockerConfiguration
from src.web_research.template_engines.ansible_engine import AnsibleTemplateEngine, AnsibleConfiguration
from src.web_research.template_engines.kubernetes_engine import KubernetesTemplateEngine, KubernetesConfiguration
from src.web_research.template_engines.infrastructure_engine import InfrastructureTemplateEngine, CloudConfiguration
from src.web_research.template_engines.base_engine import ITemplateEngine, TemplateContext, TemplateResult


# Mock SpecificOptions for testing
@dataclass
class MockSpecificOptions:
    """Mock SpecificOptions for testing."""
    distro: Optional[str] = "ubuntu22"
    cluster_size: Optional[int] = 3
    monitoring_stack: Optional[List[str]] = None
    deployment_type: Optional[str] = "production"
    enable_tls: bool = True


class TestDockerTemplateEngine:
    """Test DockerTemplateEngine functionality."""
    
    @pytest.fixture
    def docker_engine(self):
        """Create Docker template engine for testing."""
        return DockerTemplateEngine()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample template context."""
        return TemplateContext(
            technology="docker",
            task_description="Deploy a monitoring stack with Prometheus and Grafana",
            specific_options=MockSpecificOptions(
                distro="ubuntu22",
                monitoring_stack=["prometheus", "grafana", "alertmanager"]
            ),
            research_data={
                "best_practices": ["Use multi-stage builds", "Non-root user"],
                "common_patterns": ["Health checks", "Resource limits"]
            }
        )
    
    def test_engine_properties(self, docker_engine):
        """Test basic engine properties."""
        assert docker_engine.engine_name == "docker"
        assert isinstance(docker_engine.supported_technologies, list)
        assert "docker" in docker_engine.supported_technologies
        assert "prometheus" in docker_engine.supported_technologies
        assert "grafana" in docker_engine.supported_technologies
    
    def test_can_handle_supported_technology(self, docker_engine, sample_context):
        """Test can_handle method for supported technologies."""
        docker_context = TemplateContext(
            technology="docker",
            task_description="test",
            specific_options=sample_context.specific_options
        )
        assert docker_engine.can_handle(docker_context) is True
        
        prometheus_context = TemplateContext(
            technology="prometheus",
            task_description="test",
            specific_options=sample_context.specific_options
        )
        assert docker_engine.can_handle(prometheus_context) is True
    
    def test_can_handle_unsupported_technology(self, docker_engine, sample_context):
        """Test can_handle method for unsupported technologies."""
        unknown_context = TemplateContext(
            technology="unknown_tech",
            task_description="test",
            specific_options=sample_context.specific_options
        )
        assert docker_engine.can_handle(unknown_context) is False
        
        empty_context = TemplateContext(
            technology="",
            task_description="test",
            specific_options=sample_context.specific_options
        )
        assert docker_engine.can_handle(empty_context) is False
    
    @pytest.mark.asyncio
    async def test_template_generation_basic(self, docker_engine, sample_context):
        """Test basic template generation."""
        result = await docker_engine.generate_template(sample_context)
        
        assert isinstance(result, TemplateResult)
        assert result.content is not None
        assert len(result.content) > 0
        assert result.template_type == "docker"
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.estimated_complexity in ["simple", "moderate", "complex"]
        assert isinstance(result.generated_at, datetime)
    
    @pytest.mark.asyncio
    async def test_template_contains_docker_content(self, docker_engine, sample_context):
        """Test that generated template contains Docker-specific content."""
        result = await docker_engine.generate_template(sample_context)
        content = result.content.lower()
        
        # Should contain Docker-related keywords
        assert any(keyword in content for keyword in [
            "dockerfile", "docker-compose", "version:", "services:", "image:"
        ])
    
    @pytest.mark.asyncio
    async def test_template_includes_monitoring_stack(self, docker_engine, sample_context):
        """Test that template includes requested monitoring tools."""
        result = await docker_engine.generate_template(sample_context)
        content = result.content.lower()
        
        # Should include monitoring stack components
        assert "prometheus" in content
        assert "grafana" in content
        assert "alertmanager" in content
    
    @pytest.mark.asyncio
    async def test_template_generation_with_different_context(self, docker_engine):
        """Test template generation with different context."""
        context = TemplateContext(
            technology="docker",
            task_description="Simple web application deployment",
            specific_options=MockSpecificOptions(
                distro="rhel9",
                cluster_size=1,
                monitoring_stack=None
            )
        )
        
        result = await docker_engine.generate_template(context)
        
        assert isinstance(result, TemplateResult)
        assert result.content is not None
        assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_template_quality_assessment(self, docker_engine, sample_context):
        """Test template quality assessment."""
        result = await docker_engine.generate_template(sample_context)
        
        # Test quality method
        if result.confidence_score >= 0.8:
            assert result.is_high_quality() is True
        else:
            assert result.is_high_quality() is False
        
        # Test character count
        assert result.get_character_count() == len(result.content)
        assert result.get_character_count() > 0
    
    def test_docker_configuration(self):
        """Test DockerConfiguration dataclass."""
        config = DockerConfiguration()
        
        # Test defaults
        assert config.runtime == "docker"
        assert config.compose_version == "3.8"
        assert config.registry is None
        assert config.network_mode == "bridge"
        assert config.volume_driver == "local"
        
        # Test custom values
        custom_config = DockerConfiguration(
            runtime="podman",
            compose_version="3.9",
            registry="docker.io",
            network_mode="host"
        )
        
        assert custom_config.runtime == "podman"
        assert custom_config.compose_version == "3.9"
        assert custom_config.registry == "docker.io"
        assert custom_config.network_mode == "host"


class TestAnsibleTemplateEngine:
    """Test AnsibleTemplateEngine functionality."""
    
    @pytest.fixture
    def ansible_engine(self):
        """Create Ansible template engine for testing."""
        return AnsibleTemplateEngine()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample template context for Ansible."""
        return TemplateContext(
            technology="ansible",
            task_description="Automate server setup with security hardening",
            specific_options=MockSpecificOptions(
                distro="rhel9",
                cluster_size=5
            ),
            research_data={
                "best_practices": ["Use roles", "Idempotency", "Variable encryption"],
                "security_requirements": ["SELinux", "Firewall", "User management"]
            }
        )
    
    def test_engine_properties(self, ansible_engine):
        """Test basic engine properties."""
        assert ansible_engine.engine_name == "ansible"
        assert isinstance(ansible_engine.supported_technologies, list)
        assert "ansible" in ansible_engine.supported_technologies
        assert "automation" in ansible_engine.supported_technologies
        assert "linux" in ansible_engine.supported_technologies
    
    def test_can_handle_ansible_technologies(self, ansible_engine, sample_context):
        """Test can_handle method for Ansible technologies."""
        ansible_context = TemplateContext(
            technology="ansible",
            task_description="test",
            specific_options=sample_context.specific_options
        )
        assert ansible_engine.can_handle(ansible_context) is True
        
        automation_context = TemplateContext(
            technology="automation",
            task_description="test",
            specific_options=sample_context.specific_options
        )
        assert ansible_engine.can_handle(automation_context) is True
    
    @pytest.mark.asyncio
    async def test_ansible_template_generation(self, ansible_engine, sample_context):
        """Test Ansible template generation."""
        result = await ansible_engine.generate_template(sample_context)
        
        assert isinstance(result, TemplateResult)
        assert result.content is not None
        assert result.template_type == "ansible"
        assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_ansible_template_contains_playbook_structure(self, ansible_engine, sample_context):
        """Test that generated template contains Ansible playbook structure."""
        result = await ansible_engine.generate_template(sample_context)
        content = result.content.lower()
        
        # Should contain Ansible-specific keywords
        ansible_keywords = ["playbook", "tasks:", "name:", "hosts:", "become:", "vars:"]
        assert any(keyword in content for keyword in ansible_keywords)
    
    def test_ansible_configuration(self):
        """Test AnsibleConfiguration dataclass."""
        config = AnsibleConfiguration()
        
        # Test defaults
        assert config.ansible_version == "2.15"
        assert config.python_version == "3.9"
        assert config.inventory_type == "ini"
        assert config.vault_enabled is False
        assert config.collections is None


class TestKubernetesTemplateEngine:
    """Test KubernetesTemplateEngine functionality."""
    
    @pytest.fixture
    def k8s_engine(self):
        """Create Kubernetes template engine for testing."""
        return KubernetesTemplateEngine()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample template context for Kubernetes."""
        return TemplateContext(
            technology="kubernetes",
            task_description="Deploy microservices application with service mesh",
            specific_options=MockSpecificOptions(
                cluster_size=5,
                monitoring_stack=["prometheus", "jaeger"]
            ),
            research_data={
                "patterns": ["Deployment", "Service", "Ingress", "ConfigMap"],
                "best_practices": ["Resource limits", "Health checks", "RBAC"]
            }
        )
    
    def test_engine_properties(self, k8s_engine):
        """Test basic engine properties."""
        assert k8s_engine.engine_name == "kubernetes"
        assert isinstance(k8s_engine.supported_technologies, list)
        assert "kubernetes" in k8s_engine.supported_technologies
        assert "k8s" in k8s_engine.supported_technologies
    
    @pytest.mark.asyncio
    async def test_kubernetes_template_generation(self, k8s_engine, sample_context):
        """Test Kubernetes template generation."""
        result = await k8s_engine.generate_template(sample_context)
        
        assert isinstance(result, TemplateResult)
        assert result.content is not None
        assert result.template_type == "kubernetes"
        assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_kubernetes_template_contains_manifests(self, k8s_engine, sample_context):
        """Test that generated template contains Kubernetes manifests."""
        result = await k8s_engine.generate_template(sample_context)
        content = result.content.lower()
        
        # Should contain Kubernetes-specific keywords
        k8s_keywords = ["apiversion:", "kind:", "metadata:", "spec:", "deployment", "service"]
        assert any(keyword in content for keyword in k8s_keywords)


class TestInfrastructureTemplateEngine:
    """Test InfrastructureTemplateEngine functionality."""
    
    @pytest.fixture
    def infra_engine(self):
        """Create Infrastructure template engine for testing."""
        return InfrastructureTemplateEngine()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample template context for Infrastructure."""
        return TemplateContext(
            technology="terraform",
            task_description="Provision cloud infrastructure with monitoring",
            specific_options=MockSpecificOptions(
                distro="cloud",
                cluster_size=3
            ),
            research_data={
                "cloud_provider": "aws",
                "resources": ["vpc", "ec2", "rds", "s3"]
            }
        )
    
    def test_engine_properties(self, infra_engine):
        """Test basic engine properties."""
        assert infra_engine.engine_name == "infrastructure"
        assert isinstance(infra_engine.supported_technologies, list)
        assert "terraform" in infra_engine.supported_technologies
        assert "aws" in infra_engine.supported_technologies
    
    @pytest.mark.asyncio
    async def test_infrastructure_template_generation(self, infra_engine, sample_context):
        """Test Infrastructure template generation."""
        result = await infra_engine.generate_template(sample_context)
        
        assert isinstance(result, TemplateResult)
        assert result.content is not None
        assert result.template_type == "infrastructure"
        assert len(result.content) > 0


class TestTemplateContext:
    """Test TemplateContext utility methods."""
    
    @pytest.fixture
    def context(self):
        """Create test context."""
        return TemplateContext(
            technology="test_tech",
            task_description="Test task",
            specific_options=MockSpecificOptions(
                distro="ubuntu22",
                cluster_size=5,
                monitoring_stack=["prometheus", "grafana"]
            )
        )
    
    def test_get_distro(self, context):
        """Test get_distro method."""
        assert context.get_distro() == "ubuntu22"
        
        # Test default fallback
        context_no_distro = TemplateContext(
            technology="test",
            task_description="test",
            specific_options=MockSpecificOptions(distro=None)
        )
        assert context_no_distro.get_distro() == "rhel9"
    
    def test_get_cluster_size(self, context):
        """Test get_cluster_size method."""
        assert context.get_cluster_size() == 5
        
        # Test default fallback
        context_no_size = TemplateContext(
            technology="test",
            task_description="test", 
            specific_options=MockSpecificOptions(cluster_size=None)
        )
        assert context_no_size.get_cluster_size() == 3
    
    def test_has_monitoring(self, context):
        """Test has_monitoring method."""
        assert context.has_monitoring("prometheus") is True
        assert context.has_monitoring("grafana") is True
        assert context.has_monitoring("elasticsearch") is False
        
        # Test with no monitoring stack
        context_no_monitoring = TemplateContext(
            technology="test",
            task_description="test",
            specific_options=MockSpecificOptions(monitoring_stack=None)
        )
        assert context_no_monitoring.has_monitoring("prometheus") is False


class TestTemplateEngineIntegration:
    """Test integration scenarios across multiple template engines."""
    
    def test_all_engines_implement_interface(self):
        """Test that all engines properly implement the interface."""
        engines = [
            DockerTemplateEngine(),
            AnsibleTemplateEngine(),
            KubernetesTemplateEngine(),
            InfrastructureTemplateEngine()
        ]
        
        for engine in engines:
            assert isinstance(engine, ITemplateEngine)
            assert hasattr(engine, 'engine_name')
            assert hasattr(engine, 'supported_technologies')
            assert hasattr(engine, 'can_handle')
            assert hasattr(engine, 'generate_template')
    
    def test_engines_have_unique_names(self):
        """Test that each engine has a unique name."""
        engines = [
            DockerTemplateEngine(),
            AnsibleTemplateEngine(),
            KubernetesTemplateEngine(),
            InfrastructureTemplateEngine()
        ]
        
        names = [engine.engine_name for engine in engines]
        assert len(names) == len(set(names))  # All names are unique
    
    def test_engines_support_different_technologies(self):
        """Test that engines support different technologies."""
        docker_engine = DockerTemplateEngine()
        ansible_engine = AnsibleTemplateEngine()
        
        test_options = MockSpecificOptions()
        
        # Docker should handle containerization
        docker_context = TemplateContext(
            technology="docker",
            task_description="test",
            specific_options=test_options
        )
        assert docker_engine.can_handle(docker_context) is True
        assert ansible_engine.can_handle(docker_context) is True  # Ansible also supports Docker
        
        # Ansible should handle automation
        ansible_context = TemplateContext(
            technology="ansible",
            task_description="test",
            specific_options=test_options
        )
        assert ansible_engine.can_handle(ansible_context) is True
        assert docker_engine.can_handle(ansible_context) is False
    
    @pytest.mark.parametrize("engine_class,test_technology", [
        (DockerTemplateEngine, "docker"),
        (AnsibleTemplateEngine, "ansible"),
        (KubernetesTemplateEngine, "kubernetes"),
        (InfrastructureTemplateEngine, "terraform")
    ])
    @pytest.mark.asyncio
    async def test_engine_template_generation_consistency(self, engine_class, test_technology):
        """Test that all engines generate consistent template results."""
        engine = engine_class()
        context = TemplateContext(
            technology=test_technology,
            task_description="Test deployment",
            specific_options=MockSpecificOptions()
        )
        
        result = await engine.generate_template(context)
        
        # All engines should return valid TemplateResult
        assert isinstance(result, TemplateResult)
        assert result.content is not None
        assert len(result.content) > 0
        assert result.template_type is not None
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.estimated_complexity in ["simple", "moderate", "complex"]
        assert isinstance(result.generated_at, datetime)
        assert result.context_hash is not None
    
    @pytest.mark.asyncio
    async def test_template_caching_hash_consistency(self):
        """Test that same context produces same hash for caching."""
        engine = DockerTemplateEngine()
        
        context1 = TemplateContext(
            technology="docker",
            task_description="Deploy app",
            specific_options=MockSpecificOptions(distro="ubuntu22")
        )
        
        context2 = TemplateContext(
            technology="docker", 
            task_description="Deploy app",
            specific_options=MockSpecificOptions(distro="ubuntu22")
        )
        
        result1 = await engine.generate_template(context1)
        result2 = await engine.generate_template(context2)
        
        # Same context should produce same hash
        assert result1.context_hash == result2.context_hash


class TestTemplateEngineErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_technology_handling(self):
        """Test handling of empty technology strings."""
        engine = DockerTemplateEngine()
        test_options = MockSpecificOptions()
        
        empty_context = TemplateContext(
            technology="",
            task_description="test",
            specific_options=test_options
        )
        assert engine.can_handle(empty_context) is False
    
    @pytest.mark.asyncio
    async def test_invalid_context_handling(self):
        """Test handling of invalid context."""
        engine = DockerTemplateEngine()
        
        # Context with minimal information
        minimal_context = TemplateContext(
            technology="docker",
            task_description="",
            specific_options=MockSpecificOptions()
        )
        
        result = await engine.generate_template(minimal_context)
        
        # Should still produce valid result
        assert isinstance(result, TemplateResult)
        assert result.content is not None
    
    @pytest.mark.asyncio
    async def test_context_with_none_values(self):
        """Test handling of context with None values."""
        engine = DockerTemplateEngine()
        
        context = TemplateContext(
            technology="docker",
            task_description="Test",
            specific_options=MockSpecificOptions(),
            research_data=None,
            user_requirements=None
        )
        
        result = await engine.generate_template(context)
        
        # Should handle None values gracefully
        assert isinstance(result, TemplateResult)
        assert result.content is not None