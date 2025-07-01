"""
Shared Result type handling utilities.

Consolidates duplicated Result error handling patterns across the codebase.
"""

import logging
from typing import Optional, TypeVar, Union

from ..result_types import Error, Success

T = TypeVar("T")
E = TypeVar("E")


def unwrap_or_return(result: Union[Success[T, E], Error[T, E]]) -> Union[T, Union[Success[T, E], Error[T, E]]]:
    """
    Unwrap a Result or return it if it's an error.
    
    Consolidates the common pattern:
    if result.is_error():
        return result
    data = result.unwrap()
    
    Args:
        result: Result to unwrap.
        
    Returns:
        Unwrapped value if Success, or the original Result if Error.
    """
    if result.is_error():
        return result
    return result.unwrap()


def unwrap_or_log_error(
    result: Union[Success[T, E], Error[T, E]], 
    logger: logging.Logger, 
    operation_name: str = "operation"
) -> Optional[T]:
    """
    Unwrap a Result or log the error and return None.
    
    Consolidates the common pattern:
    if result.is_error():
        logger.error(f"Operation failed: {result.error}")
        return None
    return result.unwrap()
    
    Args:
        result: Result to unwrap.
        logger: Logger instance for error logging.
        operation_name: Name of the operation for logging context.
        
    Returns:
        Unwrapped value if Success, None if Error.
    """
    if result.is_error():
        logger.error(f"{operation_name} failed: {result.error}")
        return None
    return result.unwrap()


def chain_results(*results: Union[Success[T, E], Error[T, E]]) -> Union[Success[T, E], Error[T, E]]:
    """
    Chain multiple Results, returning the first Error encountered or the last Success.
    
    Args:
        results: Results to chain.
        
    Returns:
        First Error or last Success.
    """
    for result in results:
        if result.is_error():
            return result
    return results[-1] if results else Success(None)  # type: ignore