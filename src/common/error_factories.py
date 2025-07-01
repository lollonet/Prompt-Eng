"""
Shared error construction utilities.

Consolidates duplicated error creation patterns across the codebase.
"""

from pathlib import Path
from typing import Any, Optional

from ..result_types import KnowledgeError, PromptError, ValidationError


def create_file_error(filepath: str, operation: str, error: Exception) -> KnowledgeError:
    """
    Create a standardized KnowledgeError for file operations.
    
    Consolidates the common pattern of file operation errors.
    
    Args:
        filepath: Path to the file that caused the error.
        operation: Description of the operation that failed.
        error: The underlying exception.
        
    Returns:
        Standardized KnowledgeError.
    """
    return KnowledgeError(
        message=f"File {operation} failed for '{filepath}'",
        source=f"FileOperation.{operation}",
        details=f"{type(error).__name__}: {str(error)}"
    )


def create_validation_error(field: str, value: Any, constraint: str) -> ValidationError:
    """
    Create a standardized ValidationError.
    
    Args:
        field: Name of the field that failed validation.
        value: The invalid value.
        constraint: Description of the constraint that was violated.
        
    Returns:
        Standardized ValidationError.
    """
    return ValidationError(field=field, value=value, constraint=constraint)


def create_operation_error(
    operation: str, 
    source: str, 
    error: Exception, 
    context: Optional[dict] = None
) -> PromptError:
    """
    Create a standardized PromptError for operations.
    
    Consolidates the common pattern of operation errors.
    
    Args:
        operation: Name of the operation that failed.
        source: Source component where the error occurred.
        error: The underlying exception.
        context: Optional context information.
        
    Returns:
        Standardized PromptError.
    """
    return PromptError(
        message=f"{operation} failed: {str(error)}",
        code=f"{operation.upper()}_ERROR",
        context=context
    )


def create_knowledge_error(
    message: str, 
    source: str, 
    details: Optional[str] = None
) -> KnowledgeError:
    """
    Create a standardized KnowledgeError.
    
    Args:
        message: Error message.
        source: Source component where the error occurred.
        details: Optional additional details.
        
    Returns:
        Standardized KnowledgeError.
    """
    return KnowledgeError(message=message, source=source, details=details)