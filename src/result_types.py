"""
Modern Result types implementation following best practices.

Business Context: Implements Result/Either pattern for explicit error handling
without exceptions, improving code reliability and making error states explicit.

Why this approach: Result types eliminate hidden exceptions, make error handling
explicit at compile time, and follow functional programming principles for
better composability and testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Transformation target type


class ResultBase(ABC, Generic[T, E]):
    """Abstract base for Result types."""

    @abstractmethod
    def is_success(self) -> bool:
        """Check if this is a success result."""
        ...

    @abstractmethod
    def is_error(self) -> bool:
        """Check if this is an error result."""
        ...

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> "Union[Success[U, E], Error[T, E]]":
        """Transform the success value if present."""
        ...

    @abstractmethod
    def map_error(self, func: Callable[[E], U]) -> "Union[Success[T, U], Error[T, U]]":
        """Transform the error value if present."""
        ...

    @abstractmethod
    def and_then(
        self, func: Callable[[T], "Union[Success[U, E], Error[T, E]]"]
    ) -> "Union[Success[U, E], Error[T, E]]":
        """Chain another Result-returning operation."""
        ...


@dataclass(frozen=True)
class Success(ResultBase[T, E]):
    """Represents a successful result."""

    value: T

    def is_success(self) -> bool:
        return True

    def is_error(self) -> bool:
        return False

    def map(self, func: Callable[[T], U]) -> "Union[Success[U, E], Error[T, E]]":
        """Transform the success value."""
        try:
            return Success(func(self.value))
        except Exception as e:
            # Convert exceptions to Error type
            return Error(e)  # type: ignore

    def map_error(self, func: Callable[[E], U]) -> "Union[Success[T, U], Error[T, U]]":
        """No-op for success values."""
        return Success(self.value)

    def and_then(
        self, func: Callable[[T], "Union[Success[U, E], Error[T, E]]"]
    ) -> "Union[Success[U, E], Error[T, E]]":
        """Chain another Result-returning operation."""
        return func(self.value)

    def unwrap(self) -> T:
        """Get the success value (safe for Success)."""
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get the success value or default."""
        return self.value


@dataclass(frozen=True)
class Error(ResultBase[T, E]):
    """Represents an error result."""

    error: E

    def is_success(self) -> bool:
        return False

    def is_error(self) -> bool:
        return True

    def map(self, func: Callable[[T], U]) -> "Union[Success[U, E], Error[T, E]]":
        """No-op for error values."""
        return Error(self.error)

    def map_error(self, func: Callable[[E], U]) -> "Union[Success[T, U], Error[T, U]]":
        """Transform the error value."""
        return Error(func(self.error))

    def and_then(
        self, func: Callable[[T], "Union[Success[U, E], Error[T, E]]"]
    ) -> "Union[Success[U, E], Error[T, E]]":
        """No-op for error values."""
        return Error(self.error)

    def unwrap(self) -> T:
        """Unsafe operation - raises the error."""
        if isinstance(self.error, Exception):
            raise self.error
        raise ValueError(f"Result contains error: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """Get the default value for errors."""
        return default


# Note: We use Union[Success[T], Error[E]] directly instead of a type alias
# to avoid generic type complications


# Domain-specific error types
@dataclass(frozen=True)
class PromptError:
    """Error in prompt generation process."""

    message: str
    code: str
    context: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        if self.context:
            return f"{self.code}: {self.message} (context: {self.context})"
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class KnowledgeError:
    """Error in knowledge base operations."""

    message: str
    source: str
    details: Optional[str] = None

    def __str__(self) -> str:
        if self.details:
            return f"Knowledge error in {self.source}: {self.message} - {self.details}"
        return f"Knowledge error in {self.source}: {self.message}"


@dataclass(frozen=True)
class ValidationError:
    """Error in data validation."""

    field: str
    value: Any
    constraint: str

    def __str__(self) -> str:
        return f"Validation failed for '{self.field}' with value '{self.value}': {self.constraint}"


@dataclass(frozen=True)
class ConfigurationError:
    """Error in configuration loading or validation."""

    message: str
    source: str = "ConfigurationManager"
    details: Optional[str] = None

    def __str__(self) -> str:
        base = f"Configuration error in {self.source}: {self.message}"
        return f"{base} - {self.details}" if self.details else base


# Utility functions for Result construction
def safe_call(
    func: Callable[[], T],
    error_mapper: Optional[Callable[[Exception], E]] = None
) -> Union[Success[T, Any], Error[T, Any]]:
    """
    Safely call a function and wrap result in Result type.

    Args:
        func: Function to call safely.
        error_mapper: Optional function to transform exceptions.

    Returns:
        Result containing either the function result or error.
    """
    try:
        return Success(func())
    except Exception as e:
        if error_mapper:
            return Error(error_mapper(e))
        return Error(e)


def combine_results(
    results: list[Union[Success[T, E], Error[T, E]]]
) -> Union[Success[list[T], E], Error[T, E]]:
    """
    Combine multiple Results into a single Result containing a list.

    Returns Success with all values if all Results are Success,
    otherwise returns the first Error encountered.
    """
    values = []
    for result in results:
        if result.is_error():
            return result  # type: ignore
        values.append(result.unwrap())
    return Success(values)


# Example usage patterns for documentation
def _example_usage() -> None:
    """Examples of Result type usage patterns."""

    # Basic usage
    def divide(a: int, b: int) -> Union[Success[float, str], Error[float, str]]:
        if b == 0:
            return Error("Division by zero")
        return Success(a / b)

    # Chaining operations
    result = (
        divide(10, 2).map(lambda x: x * 2).map(lambda x: round(x, 2))  # Transform success value
    )  # Chain transformations

    # Error handling
    if result.is_success():
        print(f"Result: {result.unwrap()}")
    else:
        # For MyPy compatibility, use isinstance check
        if isinstance(result, Error):
            print(f"Error: {result.error}")

    # Using and_then for chaining Result-returning operations
    def sqrt_safe(x: float) -> Union[Success[float, str], Error[float, str]]:
        if x < 0:
            return Error("Cannot take square root of negative number")
        return Success(x**0.5)

    # Example of chaining operations
    _ = divide(16, 4).and_then(sqrt_safe)  # Union[Success[float, str], Error[float, str]]
