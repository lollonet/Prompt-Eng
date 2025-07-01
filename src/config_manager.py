"""
Centralized configuration management system.

Provides a single source of truth for all system configuration with
validation, environment overrides, and hot reload capabilities.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python versions

from .result_types import Success, Error, ConfigurationError
from typing import Union, Any


logger = logging.getLogger(__name__)


@dataclass
class SystemConfig:
    """System-level configuration."""
    name: str = "Enterprise Prompt Generator"
    version: str = "2.0.0"
    environment: str = "production"


@dataclass
class PathsConfig:
    """File paths and directories configuration."""
    prompts_dir: str = "prompts"
    knowledge_base_root: str = "knowledge_base"
    config_dir: str = "config"
    cache_dir: str = "cache"
    logs_dir: str = "logs"
    tech_stack_mapping: str = "config/tech_stack_mapping.json"
    templates_config: str = "config/templates.json"


@dataclass
class PerformanceConfig:
    """Performance and concurrency settings."""
    max_concurrent_operations: int = 10
    enable_performance_tracking: bool = True
    performance_threshold_ms: int = 1000
    memory_limit_mb: int = 512


@dataclass
class CacheConfig:
    """Caching configuration."""
    strategy: str = "memory"
    ttl_seconds: int = 3600
    max_size: int = 1000
    enable_compression: bool = False
    eviction_policy: str = "lru"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_rotation: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class KnowledgeManagerConfig:
    """Knowledge management settings."""
    preload_common_technologies: bool = True
    auto_refresh_interval_minutes: int = 60
    validation_strict_mode: bool = True
    backup_strategy: str = "daily"


@dataclass
class EventSystemConfig:
    """Event-driven architecture settings."""
    enable_events: bool = True
    max_event_history: int = 1000
    event_retention_hours: int = 24
    async_event_processing: bool = True


@dataclass
class WebResearchConfig:
    """Web research module configuration."""
    enable_web_research: bool = True
    max_concurrent_requests: int = 5
    request_timeout_seconds: int = 30
    cache_web_results: bool = True
    user_agent: str = "Enterprise-Prompt-Generator/2.0"


@dataclass
class SecurityConfig:
    """Security settings."""
    validate_inputs: bool = True
    sanitize_outputs: bool = True
    rate_limiting: bool = True
    max_requests_per_minute: int = 100


@dataclass
class TemplatesConfig:
    """Template system configuration."""
    default_template: str = "base_prompts/generic_code_prompt.txt"
    template_validation: bool = True
    custom_template_dir: str = "custom_templates"
    template_caching: bool = True


@dataclass
class MonitoringConfig:
    """System monitoring and observability."""
    enable_health_checks: bool = True
    health_check_interval_seconds: int = 30
    metrics_collection: bool = True
    alert_thresholds: Dict[str, Union[float, int]] = field(
        default_factory=lambda: {"error_rate": 0.05, "response_time_ms": 2000}
    )


@dataclass
class DevelopmentConfig:
    """Development and testing settings."""
    debug_mode: bool = False
    verbose_logging: bool = False
    test_mode: bool = False
    mock_external_services: bool = False


@dataclass
class GlobalConfig:
    """
    Global configuration container for all system settings.
    
    Provides centralized access to all configuration sections with
    validation and type safety.
    """
    system: SystemConfig = field(default_factory=SystemConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    knowledge_manager: KnowledgeManagerConfig = field(default_factory=KnowledgeManagerConfig)
    event_system: EventSystemConfig = field(default_factory=EventSystemConfig)
    web_research: WebResearchConfig = field(default_factory=WebResearchConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    templates: TemplatesConfig = field(default_factory=TemplatesConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    
    # Metadata
    loaded_at: datetime = field(default_factory=datetime.now)
    config_file: Optional[str] = None
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """
        Convert relative path to absolute path based on config location.
        
        Args:
            relative_path: Path relative to project root.
            
        Returns:
            Absolute path.
        """
        if self.config_file:
            base_dir = Path(self.config_file).parent.parent
        else:
            base_dir = Path.cwd()
        return base_dir / relative_path
    
    def get_cache_settings(self) -> Dict[str, Any]:
        """Get cache configuration as dictionary for compatibility."""
        return {
            "strategy": self.cache.strategy,
            "ttl_seconds": self.cache.ttl_seconds,
            "max_size": self.cache.max_size,
            "enable_compression": self.cache.enable_compression,
            "eviction_policy": self.cache.eviction_policy,
        }
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance configuration as dictionary for compatibility."""
        return {
            "max_concurrent_operations": self.performance.max_concurrent_operations,
            "enable_performance_tracking": self.performance.enable_performance_tracking,
            "performance_threshold_ms": self.performance.performance_threshold_ms,
            "memory_limit_mb": self.performance.memory_limit_mb,
        }


class ConfigurationManager:
    """
    Centralized configuration manager with validation and hot reload.
    
    Features:
    - TOML-based configuration
    - Environment variable overrides
    - Configuration validation
    - Hot reload capabilities
    - Type-safe access patterns
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to TOML configuration file.
        """
        self.config_path = config_path or self._find_config_file()
        self._config: Optional[GlobalConfig] = None
        self._last_modified: Optional[float] = None
    
    def _find_config_file(self) -> str:
        """
        Find configuration file in standard locations.
        
        Returns:
            Path to configuration file.
            
        Raises:
            FileNotFoundError: If no configuration file is found.
        """
        search_paths = [
            "config/config.toml",
            "config.toml",
            "../config/config.toml",
            os.path.expanduser("~/.prompt-generator/config.toml"),
        ]
        
        for path in search_paths:
            if Path(path).exists():
                return path
        
        raise FileNotFoundError("No configuration file found in standard locations")
    
    def load_config(self, force_reload: bool = False) -> Union[Success[GlobalConfig, Any], Error[Any, ConfigurationError]]:
        """
        Load configuration from TOML file with validation.
        
        Args:
            force_reload: Force reload even if file hasn't changed.
            
        Returns:
            Result containing loaded configuration or error.
        """
        try:
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                return Error(ConfigurationError(
                    message=f"Configuration file not found: {self.config_path}",
                    source="ConfigurationManager.load_config"
                ))
            
            # Check if reload is needed
            current_modified = config_file.stat().st_mtime
            if (not force_reload and 
                self._config is not None and 
                self._last_modified is not None and 
                current_modified <= self._last_modified):
                return Success(self._config)
            
            # Load TOML file
            with open(config_file, 'rb') as f:
                toml_data = tomllib.load(f)
            
            # Create configuration object
            config = self._create_config_from_dict(toml_data)
            config.config_file = str(config_file)
            config.loaded_at = datetime.now()
            
            # Apply environment variable overrides
            self._apply_environment_overrides(config)
            
            # Validate configuration
            validation_result = self._validate_config(config)
            if validation_result.is_error():
                return validation_result  # type: ignore
            
            # Cache configuration
            self._config = config
            self._last_modified = current_modified
            
            logger.info("Configuration loaded successfully from: %s", config_file)
            return Success(config)
            
        except Exception as e:
            return Error(ConfigurationError(
                message=f"Failed to load configuration: {str(e)}",
                source="ConfigurationManager.load_config",
                details=str(e)
            ))
    
    def _create_config_from_dict(self, data: Dict[str, Any]) -> GlobalConfig:
        """
        Create GlobalConfig object from dictionary data.
        
        Args:
            data: Dictionary data from TOML file.
            
        Returns:
            GlobalConfig object.
        """
        return GlobalConfig(
            system=SystemConfig(**data.get("system", {})),
            paths=PathsConfig(**data.get("paths", {})),
            performance=PerformanceConfig(**data.get("performance", {})),
            cache=CacheConfig(**data.get("cache", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            knowledge_manager=KnowledgeManagerConfig(**data.get("knowledge_manager", {})),
            event_system=EventSystemConfig(**data.get("event_system", {})),
            web_research=WebResearchConfig(**data.get("web_research", {})),
            security=SecurityConfig(**data.get("security", {})),
            templates=TemplatesConfig(**data.get("templates", {})),
            monitoring=MonitoringConfig(**data.get("monitoring", {})),
            development=DevelopmentConfig(**data.get("development", {})),
        )
    
    def _apply_environment_overrides(self, config: GlobalConfig) -> None:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config: Configuration object to modify.
        """
        # Environment variable mapping
        env_mappings = {
            "PROMPT_GENERATOR_LOG_LEVEL": ("logging", "level"),
            "PROMPT_GENERATOR_DEBUG": ("development", "debug_mode"),
            "PROMPT_GENERATOR_MAX_CONCURRENT": ("performance", "max_concurrent_operations"),
            "PROMPT_GENERATOR_CACHE_TTL": ("cache", "ttl_seconds"),
            "PROMPT_GENERATOR_ENVIRONMENT": ("system", "environment"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                section_obj = getattr(config, section)
                current_value = getattr(section_obj, key)
                
                if isinstance(current_value, bool):
                    value = value.lower() in ("true", "1", "yes", "on")
                elif isinstance(current_value, int):
                    value = int(value)
                elif isinstance(current_value, float):
                    value = float(value)
                
                setattr(section_obj, key, value)
                logger.info("Applied environment override: %s = %s", env_var, value)
    
    def _validate_config(self, config: GlobalConfig) -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
        """
        Validate configuration values.
        
        Args:
            config: Configuration to validate.
            
        Returns:
            Result indicating validation success or failure.
        """
        try:
            # Validate performance settings
            if config.performance.max_concurrent_operations <= 0:
                return Error(ConfigurationError(
                    message="max_concurrent_operations must be positive",
                    source="ConfigurationManager._validate_config"
                ))
            
            # Validate cache settings
            if config.cache.ttl_seconds <= 0:
                return Error(ConfigurationError(
                    message="cache ttl_seconds must be positive",
                    source="ConfigurationManager._validate_config"
                ))
            
            # Validate logging level
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config.logging.level.upper() not in valid_levels:
                return Error(ConfigurationError(
                    message=f"Invalid logging level: {config.logging.level}",
                    source="ConfigurationManager._validate_config"
                ))
            
            # Validate paths exist or can be created
            required_dirs = [
                config.paths.prompts_dir,
                config.paths.knowledge_base_root,
                config.paths.config_dir,
            ]
            
            for dir_path in required_dirs:
                abs_path = config.get_absolute_path(dir_path)
                if not abs_path.exists():
                    logger.warning("Directory does not exist: %s", abs_path)
            
            return Success(None)
            
        except Exception as e:
            return Error(ConfigurationError(
                message=f"Configuration validation failed: {str(e)}",
                source="ConfigurationManager._validate_config"
            ))
    
    def get_config(self) -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
        """
        Get current configuration, loading if necessary.
        
        Returns:
            Result containing current configuration or error.
        """
        if self._config is None:
            return self.load_config()
        
        # Check for hot reload
        if self.config_path and Path(self.config_path).exists():
            current_modified = Path(self.config_path).stat().st_mtime
            if (self._last_modified is not None and 
                current_modified > self._last_modified):
                logger.info("Configuration file changed, hot reloading...")
                return self.load_config(force_reload=True)
        
        return Success(self._config)
    
    def reload_config(self) -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
        """
        Force reload configuration from file.
        
        Returns:
            Result containing reloaded configuration or error.
        """
        return self.load_config(force_reload=True)


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigurationManager:
    """
    Get global configuration manager instance.
    
    Args:
        config_path: Optional path to configuration file.
        
    Returns:
        Configuration manager instance.
    """
    global _config_manager
    
    if _config_manager is None or config_path is not None:
        _config_manager = ConfigurationManager(config_path)
    
    return _config_manager


def get_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Get current global configuration.
    
    Returns:
        Result containing current configuration or error.
    """
    return get_config_manager().get_config()


def reload_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """
    Reload global configuration from file.
    
    Returns:
        Result containing reloaded configuration or error.
    """
    return get_config_manager().reload_config()


# Configuration access helpers for common use cases

def get_cache_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """Get cache configuration."""
    config_result = get_config()
    if config_result.is_error():
        return config_result  # type: ignore
    return Success(config_result.unwrap().cache)


def get_performance_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """Get performance configuration."""
    config_result = get_config()
    if config_result.is_error():
        return config_result  # type: ignore
    return Success(config_result.unwrap().performance)


def get_paths_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """Get paths configuration."""
    config_result = get_config()
    if config_result.is_error():
        return config_result  # type: ignore
    return Success(config_result.unwrap().paths)


def get_logging_config() -> Union[Success[Any, Any], Error[Any, ConfigurationError]]:
    """Get logging configuration."""
    config_result = get_config()
    if config_result.is_error():
        return config_result  # type: ignore
    return Success(config_result.unwrap().logging)