"""
Configuration integration helpers for existing components.

Provides helper functions and adapters to integrate the centralized
configuration system with existing components.
"""

import logging
from typing import Dict, Any, Optional, Union

from .config_manager import get_config, GlobalConfig
from .result_types import Success, Error, ConfigurationError
from .types_advanced import KnowledgeManagerConfig as OldKnowledgeManagerConfig

logger = logging.getLogger(__name__)


def setup_logging_from_config() -> Union[Success[None, Any], Error[Any, ConfigurationError]]:
    """
    Configure logging based on centralized configuration.
    
    Returns:
        Result indicating success or failure.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, config.logging.level.upper()),
            format=config.logging.format,
            force=True  # Override existing configuration
        )
        
        # Configure file logging if specified
        if config.logging.file_rotation:
            # This would be implemented with RotatingFileHandler
            # For now, just log the configuration
            logger.info("File rotation enabled (not implemented in this demo)")
        
        logger.info("Logging configured from centralized config")
        return Success(None)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to setup logging: {str(e)}",
            source="config_integration.setup_logging_from_config"
        ))


def get_knowledge_manager_config_legacy() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Get knowledge manager configuration in legacy format.
    
    Returns:
        Result containing legacy KnowledgeManagerConfig or error.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        # Convert to legacy format
        legacy_config = OldKnowledgeManagerConfig(
            config_path=str(config.get_absolute_path(config.paths.tech_stack_mapping)),
            base_path=str(config.get_absolute_path(config.paths.knowledge_base_root)),
            cache_strategy=config.cache.strategy,
            cache_ttl_seconds=config.cache.ttl_seconds,
            enable_performance_tracking=config.performance.enable_performance_tracking,
            max_concurrent_operations=config.performance.max_concurrent_operations,
        )
        
        return Success(legacy_config)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to get legacy knowledge manager config: {str(e)}",
            source="config_integration.get_knowledge_manager_config_legacy"
        ))


def get_prompt_generator_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Get prompt generator configuration as dictionary.
    
    Returns:
        Result containing configuration dictionary or error.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        generator_config = {
            "prompts_dir": str(config.get_absolute_path(config.paths.prompts_dir)),
            "performance_tracking": config.performance.enable_performance_tracking,
            "template_caching": config.templates.template_caching,
            "default_template": config.templates.default_template,
            "max_concurrent_operations": config.performance.max_concurrent_operations,
        }
        
        return Success(generator_config)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to get prompt generator config: {str(e)}",
            source="config_integration.get_prompt_generator_config"
        ))


def get_web_research_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Get web research configuration as dictionary.
    
    Returns:
        Result containing configuration dictionary or error.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        web_config = {
            "enabled": config.web_research.enable_web_research,
            "max_concurrent_requests": config.web_research.max_concurrent_requests,
            "request_timeout": config.web_research.request_timeout_seconds,
            "cache_results": config.web_research.cache_web_results,
            "user_agent": config.web_research.user_agent,
            "cache_dir": str(config.get_absolute_path(config.paths.cache_dir)),
        }
        
        return Success(web_config)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to get web research config: {str(e)}",
            source="config_integration.get_web_research_config"
        ))


def get_event_system_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Get event system configuration as dictionary.
    
    Returns:
        Result containing configuration dictionary or error.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        event_config = {
            "enabled": config.event_system.enable_events,
            "max_history": config.event_system.max_event_history,
            "retention_hours": config.event_system.event_retention_hours,
            "async_processing": config.event_system.async_event_processing,
        }
        
        return Success(event_config)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to get event system config: {str(e)}",
            source="config_integration.get_event_system_config"
        ))


def get_monitoring_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Get monitoring configuration as dictionary.
    
    Returns:
        Result containing configuration dictionary or error.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        monitoring_config = {
            "health_checks_enabled": config.monitoring.enable_health_checks,
            "health_check_interval": config.monitoring.health_check_interval_seconds,
            "metrics_collection": config.monitoring.metrics_collection,
            "alert_thresholds": config.monitoring.alert_thresholds,
            "performance_threshold_ms": config.performance.performance_threshold_ms,
        }
        
        return Success(monitoring_config)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to get monitoring config: {str(e)}",
            source="config_integration.get_monitoring_config"
        ))


def is_development_mode() -> bool:
    """
    Check if the system is running in development mode.
    
    Returns:
        True if in development mode, False otherwise.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return False
        
        config = config_result.unwrap()
        return (
            config.development.debug_mode or 
            config.development.test_mode or 
            config.system.environment.lower() in ("development", "dev", "testing")
        )
        
    except Exception:
        return False


def get_security_settings() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Get security configuration as dictionary.
    
    Returns:
        Result containing security configuration or error.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        security_config = {
            "validate_inputs": config.security.validate_inputs,
            "sanitize_outputs": config.security.sanitize_outputs,
            "rate_limiting": config.security.rate_limiting,
            "max_requests_per_minute": config.security.max_requests_per_minute,
        }
        
        return Success(security_config)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to get security config: {str(e)}",
            source="config_integration.get_security_settings"
        ))


# Configuration validation helpers

def validate_required_paths() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Validate that required paths exist and are accessible.
    
    Returns:
        Result indicating validation success or failure.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        # Check required directories
        required_paths = [
            (config.paths.prompts_dir, "prompts directory"),
            (config.paths.knowledge_base_root, "knowledge base directory"),
            (config.paths.config_dir, "config directory"),
        ]
        
        for path_str, description in required_paths:
            path = config.get_absolute_path(path_str)
            if not path.exists():
                return Error(ConfigurationError(
                    message=f"Required {description} does not exist: {path}",
                    source="config_integration.validate_required_paths"
                ))
            
            if not path.is_dir():
                return Error(ConfigurationError(
                    message=f"Required {description} is not a directory: {path}",
                    source="config_integration.validate_required_paths"
                ))
        
        # Check configuration files
        tech_mapping_path = config.get_absolute_path(config.paths.tech_stack_mapping)
        if not tech_mapping_path.exists():
            return Error(ConfigurationError(
                message=f"Technology stack mapping file does not exist: {tech_mapping_path}",
                source="config_integration.validate_required_paths"
            ))
        
        logger.info("All required paths validated successfully")
        return Success(None)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Path validation failed: {str(e)}",
            source="config_integration.validate_required_paths"
        ))


def create_missing_directories() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Create missing optional directories based on configuration.
    
    Returns:
        Result indicating success or failure.
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return config_result  # type: ignore
        
        config = config_result.unwrap()
        
        # Optional directories that can be created
        optional_dirs = [
            config.paths.cache_dir,
            config.paths.logs_dir,
        ]
        
        for dir_str in optional_dirs:
            dir_path = config.get_absolute_path(dir_str)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info("Created directory: %s", dir_path)
                except OSError as e:
                    logger.warning("Could not create directory %s: %s", dir_path, e)
        
        return Success(None)
        
    except Exception as e:
        return Error(ConfigurationError(
            message=f"Failed to create directories: {str(e)}",
            source="config_integration.create_missing_directories"
        ))


# Environment-specific configuration

def get_environment_name() -> str:
    """
    Get the current environment name.
    
    Returns:
        Environment name (development, production, testing, etc.)
    """
    try:
        config_result = get_config()
        if config_result.is_error():
            return "unknown"
        
        return config_result.unwrap().system.environment
        
    except Exception:
        return "unknown"


def is_production() -> bool:
    """Check if running in production environment."""
    return get_environment_name().lower() == "production"


def is_testing() -> bool:
    """Check if running in testing environment."""
    env = get_environment_name().lower()
    return env in ("testing", "test")


# Configuration change detection

_last_config_hash: Optional[int] = None


def has_config_changed() -> bool:
    """
    Check if configuration has changed since last check.
    
    Returns:
        True if configuration has changed, False otherwise.
    """
    global _last_config_hash
    
    try:
        config_result = get_config()
        if config_result.is_error():
            return False
        
        config = config_result.unwrap()
        current_hash = hash(str(config))
        
        if _last_config_hash is None:
            _last_config_hash = current_hash
            return False
        
        if current_hash != _last_config_hash:
            _last_config_hash = current_hash
            return True
        
        return False
        
    except Exception:
        return False