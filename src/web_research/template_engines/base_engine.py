"""
Base Template Engine Interface following Interface Segregation Principle.

Business Context: Defines the contract for technology-specific template generators,
enabling consistent behavior while allowing specialized implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TemplateContext:
    """
    Context object containing all information needed for template generation.

    Why this approach: Parameter Object pattern reduces parameter count
    and provides type safety while maintaining backward compatibility.
    """

    technology: str
    task_description: str
    specific_options: "SpecificOptions"
    research_data: Optional[Dict[str, Any]] = None
    user_requirements: Optional[List[str]] = None

    def get_distro(self) -> str:
        """Get target distribution with sensible default."""
        return self.specific_options.distro or "rhel9"

    def get_cluster_size(self) -> int:
        """Get cluster size with sensible default."""
        return self.specific_options.cluster_size or 3

    def has_monitoring(self, tool: str) -> bool:
        """Check if specific monitoring tool is requested."""
        if not self.specific_options.monitoring_stack:
            return False
        return tool in self.specific_options.monitoring_stack


@dataclass
class TemplateResult:
    """
    Result of template generation with metadata.

    Business Context: Encapsulates both the generated content and
    metadata for quality tracking and caching decisions.
    """

    content: str
    template_type: str
    confidence_score: float
    estimated_complexity: str  # simple, moderate, complex
    generated_at: datetime
    context_hash: str  # For caching and change detection

    def is_high_quality(self) -> bool:
        """Determine if template meets quality threshold."""
        return self.confidence_score >= 0.8

    def get_character_count(self) -> int:
        """Get template length for metrics."""
        return len(self.content)


class ITemplateEngine(ABC):
    """
    Interface for technology-specific template generators.

    Why this design: Interface Segregation Principle - each engine only
    implements what it needs, while maintaining consistent behavior.
    """

    @property
    @abstractmethod
    def supported_technologies(self) -> List[str]:
        """List of technologies this engine supports."""
        pass

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Unique identifier for this engine."""
        pass

    @abstractmethod
    def can_handle(self, context: TemplateContext) -> bool:
        """
        Determine if this engine can handle the given context.

        Business Context: Allows for flexible engine selection based
        on technology, options, or other contextual information.
        """
        pass

    @abstractmethod
    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """
        Generate template for the given context.

        Returns TemplateResult with content and metadata for quality assessment.
        """
        pass

    @abstractmethod
    def estimate_complexity(self, context: TemplateContext) -> str:
        """
        Estimate template complexity for user guidance.

        Returns: 'simple', 'moderate', or 'complex'
        """
        pass

    def get_quality_score(self, content: str, context: TemplateContext) -> float:
        """
        Calculate quality score for generated content.

        Default implementation - engines can override for specific logic.
        """
        base_score = 0.7

        # Length appropriateness
        if 500 <= len(content) <= 3000:
            base_score += 0.1

        # Technology relevance
        if context.technology.lower() in content.lower():
            base_score += 0.1

        # Code examples present
        if "```" in content:
            base_score += 0.1

        return min(1.0, base_score)


class BaseTemplateEngine(ITemplateEngine):
    """
    Base implementation providing common functionality.

    Business Context: Reduces code duplication while allowing
    specialized engines to focus on their specific logic.
    """

    def __init__(self, name: str, technologies: List[str]):
        self._name = name
        self._technologies = technologies

    @property
    def engine_name(self) -> str:
        return self._name

    @property
    def supported_technologies(self) -> List[str]:
        return self._technologies

    def can_handle(self, context: TemplateContext) -> bool:
        """Default implementation checks technology list."""
        return any(tech in context.technology.lower() for tech in self._technologies)

    def estimate_complexity(self, context: TemplateContext) -> str:
        """Default complexity estimation based on options."""
        complexity_factors = 0

        if context.specific_options.cluster_size and context.specific_options.cluster_size > 1:
            complexity_factors += 1

        if context.specific_options.monitoring_stack:
            complexity_factors += 1

        if context.specific_options.ha_setup:
            complexity_factors += 1

        if context.specific_options.security_standards:
            complexity_factors += 1

        if complexity_factors == 0:
            return "simple"
        elif complexity_factors <= 2:
            return "moderate"
        else:
            return "complex"

    def _generate_header(self, context: TemplateContext) -> str:
        """Generate consistent template header."""
        return f"## EXPECTED OUTPUT EXAMPLE\n\n"

    def _generate_footer(self, context: TemplateContext) -> str:
        """Generate consistent template footer."""
        return f"\n\nConfiguration for {context.technology} on {context.get_distro().upper()}"

    def _calculate_context_hash(self, context: TemplateContext) -> str:
        """Generate hash for caching and change detection."""
        import hashlib

        context_str = (
            f"{context.technology}"
            f"{context.task_description}"
            f"{context.specific_options.__dict__}"
        )

        return hashlib.md5(context_str.encode()).hexdigest()[:8]
