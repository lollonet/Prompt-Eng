"""
Template Engine System following SOLID principles and modern patterns.

Business Context: Generates technology-specific code examples and configurations
based on user requirements and research data, using a plugin-based architecture
for maintainability and extensibility.
"""

from .base_engine import ITemplateEngine, TemplateContext, TemplateResult
from .patroni_engine import PatroniTemplateEngine
from .kubernetes_engine import KubernetesTemplateEngine
from .ansible_engine import AnsibleTemplateEngine
from .docker_engine import DockerTemplateEngine
from .infrastructure_engine import InfrastructureTemplateEngine
from .template_factory import TemplateEngineFactory

__all__ = [
    'ITemplateEngine',
    'TemplateContext', 
    'TemplateResult',
    'PatroniTemplateEngine',
    'KubernetesTemplateEngine',
    'AnsibleTemplateEngine',
    'DockerTemplateEngine',
    'InfrastructureTemplateEngine',
    'TemplateEngineFactory'
]