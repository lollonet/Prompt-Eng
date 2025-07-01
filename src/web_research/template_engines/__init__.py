"""
Template Engine System following SOLID principles and modern patterns.

Business Context: Generates technology-specific code examples and configurations
based on user requirements and research data, using a plugin-based architecture
for maintainability and extensibility.
"""

from .ansible_engine import AnsibleTemplateEngine
from .base_engine import ITemplateEngine, TemplateContext, TemplateResult
from .docker_engine import DockerTemplateEngine
from .mysql_engine import MySQLTemplateEngine
from .patroni_engine import PatroniTemplateEngine
from .template_factory import TemplateEngineFactory

# TODO: Import remaining engines when implemented
# from .kubernetes_engine import KubernetesTemplateEngine
# from .infrastructure_engine import InfrastructureTemplateEngine

__all__ = [
    "ITemplateEngine",
    "TemplateContext",
    "TemplateResult",
    "PatroniTemplateEngine",
    "DockerTemplateEngine",
    "AnsibleTemplateEngine",
    "MySQLTemplateEngine",
    "TemplateEngineFactory",
]
