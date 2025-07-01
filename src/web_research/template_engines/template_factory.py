"""
Template Engine Factory following Factory Pattern and Open/Closed Principle.

Business Context: Centralized engine selection and instantiation, allowing
new template engines to be added without modifying existing code.
"""

import logging
from typing import Dict, List, Optional, Type

from .ansible_engine import AnsibleTemplateEngine
from .base_engine import ITemplateEngine, TemplateContext, TemplateResult
from .docker_engine import DockerTemplateEngine
from .infrastructure_engine import InfrastructureTemplateEngine
from .kubernetes_engine import KubernetesTemplateEngine
from .mysql_engine import MySQLTemplateEngine
from .patroni_engine import PatroniTemplateEngine


class TemplateEngineFactory:
    """
    Factory for creating and managing template engines.

    Why this approach: Open/Closed Principle - open for extension (new engines)
    but closed for modification (existing selection logic unchanged).
    """

    def __init__(self):
        self._engines: List[ITemplateEngine] = []
        self._logger = logging.getLogger(__name__)
        self._register_default_engines()

    def _register_default_engines(self) -> None:
        """Register built-in template engines."""
        try:
            self.register_engine(PatroniTemplateEngine())
            self.register_engine(DockerTemplateEngine())
            self.register_engine(AnsibleTemplateEngine())
            self.register_engine(MySQLTemplateEngine())
            self.register_engine(KubernetesTemplateEngine())
            self.register_engine(InfrastructureTemplateEngine())

            self._logger.info(f"Registered {len(self._engines)} template engines")

        except Exception as e:
            self._logger.error(f"Failed to register default engines: {e}")

    def register_engine(self, engine: ITemplateEngine) -> None:
        """
        Register a new template engine.

        Business Context: Allows plugins/extensions to add new engines
        without modifying core factory logic.
        """
        if not isinstance(engine, ITemplateEngine):
            raise TypeError(f"Engine must implement ITemplateEngine interface")

        # Check for name conflicts
        existing_names = [e.engine_name for e in self._engines]
        if engine.engine_name in existing_names:
            raise ValueError(f"Engine with name '{engine.engine_name}' already registered")

        self._engines.append(engine)
        self._logger.debug(f"Registered engine: {engine.engine_name}")

    def get_compatible_engines(self, context: TemplateContext) -> List[ITemplateEngine]:
        """
        Find all engines that can handle the given context.

        Business Context: Allows for fallback engines or multiple
        template options for the same technology.
        """
        compatible = []

        for engine in self._engines:
            try:
                if engine.can_handle(context):
                    compatible.append(engine)
            except Exception as e:
                self._logger.warning(f"Engine {engine.engine_name} failed compatibility check: {e}")

        return compatible

    def select_best_engine(self, context: TemplateContext) -> Optional[ITemplateEngine]:
        """
        Select the most appropriate engine for the context.

        Business Context: Implements intelligent engine selection based
        on technology specificity and engine capabilities.
        """
        compatible_engines = self.get_compatible_engines(context)

        if not compatible_engines:
            self._logger.warning(
                f"No compatible engines found for technology: {context.technology}"
            )
            return None

        if len(compatible_engines) == 1:
            return compatible_engines[0]

        # Engine selection priority logic
        return self._rank_engines(compatible_engines, context)[0]

    def _rank_engines(
        self, engines: List[ITemplateEngine], context: TemplateContext
    ) -> List[ITemplateEngine]:
        """
        Rank engines by their suitability for the context.

        Business Context: Ensures most specialized engines are preferred
        over generic ones for better template quality.
        """

        def engine_score(engine: ITemplateEngine) -> float:
            score = 0.0

            # Specificity bonus - more specific technologies rank higher
            technology_matches = sum(
                1 for tech in engine.supported_technologies if tech in context.technology.lower()
            )
            score += technology_matches * 10

            # Exact technology match bonus
            if context.technology.lower() in engine.supported_technologies:
                score += 20

            # Complexity handling bonus
            try:
                complexity = engine.estimate_complexity(context)
                if complexity in ["moderate", "complex"]:
                    score += 5  # Bonus for handling complex scenarios
            except:
                pass

            return score

        # Sort by score (highest first)
        ranked = sorted(engines, key=engine_score, reverse=True)

        self._logger.debug(
            f"Engine ranking for {context.technology}: " f"{[e.engine_name for e in ranked]}"
        )

        return ranked

    async def generate_template(self, context: TemplateContext) -> Optional[TemplateResult]:
        """
        Generate template using the best available engine.

        Business Context: Main entry point for template generation with
        automatic engine selection and error handling.
        """
        engine = self.select_best_engine(context)

        if not engine:
            self._logger.error(f"No suitable engine found for technology: {context.technology}")
            return None

        try:
            self._logger.info(f"Generating template using engine: {engine.engine_name}")
            result = await engine.generate_template(context)

            self._logger.info(
                f"Template generated successfully: "
                f"quality={result.confidence_score:.2f}, "
                f"complexity={result.estimated_complexity}, "
                f"length={result.get_character_count()}"
            )

            return result

        except Exception as e:
            self._logger.error(f"Template generation failed with engine {engine.engine_name}: {e}")
            return None

    def get_supported_technologies(self) -> List[str]:
        """Get all technologies supported by registered engines."""
        all_technologies = set()

        for engine in self._engines:
            all_technologies.update(engine.supported_technologies)

        return sorted(list(all_technologies))

    def get_engine_info(self) -> Dict[str, Dict]:
        """Get information about all registered engines."""
        return {
            engine.engine_name: {
                "technologies": engine.supported_technologies,
                "class": engine.__class__.__name__,
            }
            for engine in self._engines
        }

    def clear_engines(self) -> None:
        """Clear all registered engines (mainly for testing)."""
        self._engines.clear()
        self._logger.debug("Cleared all registered engines")


# Global factory instance
_factory_instance: Optional[TemplateEngineFactory] = None


def get_template_factory() -> TemplateEngineFactory:
    """
    Get singleton template factory instance.

    Business Context: Provides global access to template generation
    while maintaining single point of configuration.
    """
    global _factory_instance

    if _factory_instance is None:
        _factory_instance = TemplateEngineFactory()

    return _factory_instance


def reset_template_factory() -> None:
    """Reset factory instance (mainly for testing)."""
    global _factory_instance
    _factory_instance = None
