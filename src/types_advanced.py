"""
Advanced type system with Protocols, Literal types, and NewTypes.

Business Context: Implements rich type system following modern Python best practices
for compile-time safety, better IDE support, and self-documenting APIs.

Why this approach: Strong typing catches errors at development time, improves
code documentation, and enables better tooling support for large codebases.
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    NewType,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from typing_extensions import NotRequired, TypedDict

from .result_types import Error, KnowledgeError, PromptError, Success

# NewTypes for domain-specific type safety
TechnologyName = NewType("TechnologyName", str)
TaskType = NewType("TaskType", str)
TemplateName = NewType("TemplateName", str)
BestPracticeName = NewType("BestPracticeName", str)
ToolName = NewType("ToolName", str)

# Literal types for constrained choices
TemplateCategory = Literal["base_prompts", "language_specific", "framework_specific"]

PredefinedTemplates = Literal[
    "base_prompts/generic_code_prompt.txt",
    "language_specific/python/feature_prompt.txt",
    "framework_specific/react/component_prompt.txt",
]

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

CacheStrategy = Literal["memory", "disk", "distributed", "none"]


# TypedDict for structured data
class TechnologyMapping(TypedDict):
    """Type definition for technology stack mapping."""

    best_practices: List[str]
    tools: List[str]


class ToolDetails(TypedDict):
    """Type definition for tool details structure."""

    name: str
    description: str
    benefits: NotRequired[List[str]]
    usage_notes: NotRequired[List[str]]
    example_command: NotRequired[str]


class PerformanceConfig(TypedDict):
    """Configuration for performance monitoring."""

    enable_monitoring: bool
    track_memory: bool
    track_io: bool
    log_level: LogLevel
    cache_strategy: CacheStrategy


# Protocol definitions for interface segregation


class BestPracticeProvider(Protocol):
    """Protocol for best practice data providers."""

    @abstractmethod
    async def get_best_practices(self, technology: TechnologyName):
        """Get list of best practice names for a technology."""
        ...

    @abstractmethod
    async def get_best_practice_details(self, name: BestPracticeName):
        """Get detailed content for a specific best practice."""
        ...


class ToolProvider(Protocol):
    """Protocol for tool data providers."""

    @abstractmethod
    async def get_tools(self, technology: TechnologyName):
        """Get list of tool names for a technology."""
        ...

    @abstractmethod
    async def get_tool_details(self, name: ToolName):
        """Get detailed information for a specific tool."""
        ...


class KnowledgeSource(BestPracticeProvider, ToolProvider, Protocol):
    """Combined protocol for complete knowledge sources."""

    pass


class TemplateRenderer(Protocol):
    """Protocol for template rendering engines."""

    @abstractmethod
    async def render(self, template_name: TemplateName, context: Dict[str, Any]):
        """Render a template with the given context."""
        ...

    @abstractmethod
    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[TemplateName]:
        """List available templates, optionally filtered by category."""
        ...


class CacheProvider(Protocol):
    """Protocol for caching implementations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        ...


class MetricsCollector(Protocol):
    """Protocol for metrics collection systems."""

    @abstractmethod
    def record_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric."""
        ...

    @abstractmethod
    def record_timer(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric."""
        ...

    @abstractmethod
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric."""
        ...


class EventPublisher(Protocol):
    """Protocol for event publishing systems."""

    @abstractmethod
    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event."""
        ...


# Generic type for async operations
T = TypeVar("T")
E = TypeVar("E")

AsyncResult = Awaitable[Any]


# Configuration types with validation


@dataclass(frozen=True)
class PromptConfigAdvanced:
    """
    Advanced configuration with rich type safety and validation.

    Uses NewTypes and Literal types for better compile-time safety.
    """

    technologies: List[TechnologyName]
    task_type: TaskType
    code_requirements: str
    task_description: str = ""
    template_name: PredefinedTemplates = "base_prompts/generic_code_prompt.txt"
    cache_strategy: CacheStrategy = "memory"
    performance_tracking: bool = True

    def __post_init__(self):
        """Validate configuration with rich error messages."""
        if not self.technologies:
            raise ValueError("At least one technology must be specified")

        if len(self.task_type) < 3:
            raise ValueError(f"Task type must be at least 3 characters, got: '{self.task_type}'")

        if len(self.code_requirements) < 10:
            raise ValueError(
                f"Code requirements must be detailed (≥10 chars), got {len(self.code_requirements)} chars"
            )

        # Validate technology names format
        for tech in self.technologies:
            if not tech.strip():
                raise ValueError("Technology names cannot be empty or whitespace")
            if not tech.islower():
                raise ValueError(f"Technology names must be lowercase: '{tech}'")


@dataclass(frozen=True)
class KnowledgeManagerConfig:
    """Configuration for KnowledgeManager with type safety."""

    config_path: str
    base_path: Optional[str] = None
    cache_strategy: CacheStrategy = "memory"
    cache_ttl_seconds: int = 3600
    enable_performance_tracking: bool = True
    max_concurrent_operations: int = 10

    def __post_init__(self):
        """Validate configuration."""
        if self.cache_ttl_seconds <= 0:
            raise ValueError("Cache TTL must be positive")

        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")


# Factory functions with type safety


def create_technology_name(name: str) -> TechnologyName:
    """
    Create a validated TechnologyName.

    Args:
        name: Technology name string.

    Returns:
        Validated TechnologyName.

    Raises:
        ValueError: If name doesn't meet requirements.
    """
    cleaned = name.strip().lower()
    if not cleaned:
        raise ValueError("Technology name cannot be empty")

    if not cleaned.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"Technology name must be alphanumeric with _ or -: '{name}'")

    return TechnologyName(cleaned)


def create_task_type(task: str) -> TaskType:
    """
    Create a validated TaskType.

    Args:
        task: Task type string.

    Returns:
        Validated TaskType.

    Raises:
        ValueError: If task doesn't meet requirements.
    """
    cleaned = task.strip()
    if len(cleaned) < 3:
        raise ValueError(f"Task type must be at least 3 characters: '{task}'")

    return TaskType(cleaned)


def create_template_name(template: str) -> TemplateName:
    """
    Create a validated TemplateName.

    Args:
        template: Template name string.

    Returns:
        Validated TemplateName.

    Raises:
        ValueError: If template name is invalid.
    """
    if not template.endswith(".txt"):
        raise ValueError(f"Template name must end with .txt: '{template}'")

    if ".." in template or template.startswith("/"):
        raise ValueError(f"Template name contains invalid path components: '{template}'")

    return TemplateName(template)


# Type guards for runtime type checking


def is_valid_technology_mapping(data: Any) -> bool:
    """Type guard for TechnologyMapping."""
    if not isinstance(data, dict):
        return False

    required_keys = {"best_practices", "tools"}
    if not all(key in data for key in required_keys):
        return False

    return (
        isinstance(data["best_practices"], list)
        and isinstance(data["tools"], list)
        and all(isinstance(item, str) for item in data["best_practices"])
        and all(isinstance(item, str) for item in data["tools"])
    )


def is_valid_tool_details(data: Any) -> bool:
    """Type guard for ToolDetails."""
    if not isinstance(data, dict):
        return False

    required_keys = {"name", "description"}
    if not all(key in data for key in required_keys):
        return False

    if not all(isinstance(data[key], str) for key in required_keys):
        return False

    # Check optional fields if present
    optional_list_fields = {"benefits", "usage_notes"}
    for field in optional_list_fields:
        if field in data and not (
            isinstance(data[field], list) and all(isinstance(item, str) for item in data[field])
        ):
            return False

    if "example_command" in data and not isinstance(data["example_command"], str):
        return False

    return True


# Example usage with rich typing
def _example_typed_usage():
    """Examples of advanced type system usage."""

    # Creating typed values
    python_tech = create_technology_name("python")
    feature_task = create_task_type("implement authentication feature")
    template = create_template_name("language_specific/python/feature_prompt.txt")

    # Type-safe configuration
    config = PromptConfigAdvanced(
        technologies=[python_tech],
        task_type=feature_task,
        code_requirements="Must follow SOLID principles and include comprehensive tests",
        template_name="language_specific/python/feature_prompt.txt",  # type: ignore
        cache_strategy="memory",
    )

    # Protocol usage would be handled by concrete implementations
    # knowledge_source: KnowledgeSource = ConcreteKnowledgeManager(...)
    # template_renderer: TemplateRenderer = ConcreteTemplateEngine(...)

    return config
