"""
Shared health check utilities.

Consolidates duplicated health check patterns across the codebase.
"""

import time
from typing import Any, Dict, Protocol, Union

from ..result_types import Error, PromptError, Success


class HealthCheckable(Protocol):
    """Protocol for components that support health checks."""
    
    async def health_check(self) -> Union[Success[Dict[str, Any], Any], Error[Any, Any]]:
        """Perform a health check on the component."""
        ...


def create_standard_health_info(
    component_name: str, 
    status: str = "healthy",
    **metrics: Any
) -> Dict[str, Any]:
    """
    Create standardized health check information.
    
    Consolidates the common health check response pattern.
    
    Args:
        component_name: Name of the component being checked.
        status: Health status (default: "healthy").
        **metrics: Additional component-specific metrics.
        
    Returns:
        Standardized health info dictionary.
    """
    health_info = {
        "component": component_name,
        "status": status,
        "timestamp": time.time(),
        **metrics
    }
    return health_info


async def aggregate_health_checks(*checkables: HealthCheckable) -> Union[Success[Dict[str, Any], Any], Error[Any, Any]]:
    """
    Aggregate health checks from multiple components.
    
    Args:
        checkables: Components that implement HealthCheckable.
        
    Returns:
        Aggregated health status or first error encountered.
    """
    results = {}
    overall_status = "healthy"
    
    for i, checkable in enumerate(checkables):
        try:
            result = await checkable.health_check()
            if result.is_error():
                return Error(
                    PromptError(
                        message=f"Health check failed for component {i}",
                        code="HEALTH_CHECK_FAILED",
                        context={"component_index": i, "error": str(result.error)}
                    )
                )
            
            component_health = result.unwrap()
            component_name = component_health.get("component", f"component_{i}")
            results[component_name] = component_health
            
            if component_health.get("status") != "healthy":
                overall_status = "degraded"
                
        except Exception as e:
            return Error(
                PromptError(
                    message=f"Health check exception for component {i}: {str(e)}",
                    code="HEALTH_CHECK_EXCEPTION",
                    context={"component_index": i}
                )
            )
    
    aggregate_health = create_standard_health_info(
        component_name="system",
        status=overall_status,
        components=results,
        total_components=len(checkables)
    )
    
    return Success(aggregate_health)