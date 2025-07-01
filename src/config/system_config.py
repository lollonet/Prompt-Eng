"""
Centralized configuration system for Enterprise Prompt Generator.

Provides a unified configuration interface that loads from TOML files,
environment variables, and provides validation and type safety.
"""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SystemConfig:
    """System-level configuration."""
    name: str = "Enterprise Prompt Generator"
    version: str = "2.0.0"
    environment: str = "production"


@dataclass(frozen=True)
class PathsConfig:
    """Path configuration for directories and files."""
    prompts_dir: str = "prompts"
    knowledge_base_root: str = "knowledge_base"
    config_dir: str = "config"
    cache_dir: str = "cache"
    logs_dir: str = "logs"
    tech_stack_mapping: str = "config/tech_stack_mapping.json"
    templates_config: str = "config/templates.json"

    def get_absolute_path(self, relative_path: str, base_dir: Optional[Path] = None) -> Path:
        """Convert relative path to absolute path."""
        if base_dir is None:
            base_dir = Path.cwd()
        return base_dir / relative_path


@dataclass(frozen=True)
class PerformanceConfig:
    """Performance and concurrency configuration."""
    max_concurrent_operations: int = 10
    enable_performance_tracking: bool = True
    performance_threshold_ms: int = 1000
    memory_limit_mb: int = 512


@dataclass(frozen=True)
class CacheConfig:
    """Caching configuration."""
    strategy: str = "memory"
    ttl_seconds: int = 3600
    max_size: int = 1000
    enable_compression: bool = False
    eviction_policy: str = "lru"


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_rotation: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass(frozen=True)
class KnowledgeManagerConfig:
    """Knowledge manager configuration."""
    preload_common_technologies: bool = True
    auto_refresh_interval_minutes: int = 60
    validation_strict_mode: bool = True
    backup_strategy: str = "daily"


@dataclass(frozen=True)
class EventSystemConfig:
    """Event system configuration."""
    enable_events: bool = True
    max_event_history: int = 1000
    event_retention_hours: int = 24
    async_event_processing: bool = True


@dataclass(frozen=True)
class WebResearchConfig:
    """Web research module configuration."""
    enable_web_research: bool = True
    max_concurrent_requests: int = 5
    request_timeout_seconds: int = 30
    cache_web_results: bool = True
    user_agent: str = "Enterprise-Prompt-Generator/2.0"


@dataclass(frozen=True)
class SecurityConfig:
    """Security configuration."""
    validate_inputs: bool = True
    sanitize_outputs: bool = True
    rate_limiting: bool = True
    max_requests_per_minute: int = 100


@dataclass(frozen=True)
class TemplatesConfig:
    """Template system configuration."""
    default_template: str = "base_prompts/generic_code_prompt.txt"
    template_validation: bool = True
    custom_template_dir: str = "custom_templates"
    template_caching: bool = True


@dataclass(frozen=True)
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enable_health_checks: bool = True
    health_check_interval_seconds: int = 30
    metrics_collection: bool = True
    alert_thresholds: Dict[str, Union[float, int]] = field(
        default_factory=lambda: {"error_rate": 0.05, "response_time_ms": 2000}
    )


@dataclass(frozen=True)
class DevelopmentConfig:
    """Development and testing configuration."""
    debug_mode: bool = False
    verbose_logging: bool = False
    test_mode: bool = False
    mock_external_services: bool = False


@dataclass(frozen=True)
class ApplicationConfig:
    """
    Centralized application configuration.
    
    Aggregates all configuration sections into a single, immutable object.
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

    @classmethod
    def from_toml(cls, config_path: Union[str, Path]) -> "ApplicationConfig":
        """
        Load configuration from TOML file.
        
        Args:
            config_path: Path to TOML configuration file.
            
        Returns:
            ApplicationConfig instance with loaded settings.
            
        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config file is invalid.
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)
            
            logger.info("Loaded configuration from: %s", config_path)
            
            return cls(
                system=SystemConfig(**config_data.get("system", {})),
                paths=PathsConfig(**config_data.get("paths", {})),
                performance=PerformanceConfig(**config_data.get("performance", {})),
                cache=CacheConfig(**config_data.get("cache", {})),
                logging=LoggingConfig(**config_data.get("logging", {})),
                knowledge_manager=KnowledgeManagerConfig(**config_data.get("knowledge_manager", {})),
                event_system=EventSystemConfig(**config_data.get("event_system", {})),
                web_research=WebResearchConfig(**config_data.get("web_research", {})),
                security=SecurityConfig(**config_data.get("security", {})),
                templates=TemplatesConfig(**config_data.get("templates", {})),
                monitoring=MonitoringConfig(**config_data.get("monitoring", {})),
                development=DevelopmentConfig(**config_data.get("development", {})),
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse configuration file {config_path}: {e}") from e

    @classmethod
    def from_env(cls, prefix: str = "EPG_") -> "ApplicationConfig":
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix.
            
        Returns:
            ApplicationConfig with environment overrides.
        """
        # Start with defaults
        config = cls()
        
        # Apply environment variable overrides
        env_overrides = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert EPG_CACHE_TTL_SECONDS to cache.ttl_seconds
                config_key = key[len(prefix):].lower()
                parts = config_key.split("_")
                
                if len(parts) >= 2:
                    section = parts[0]
                    field_name = "_".join(parts[1:])
                    
                    if section not in env_overrides:
                        env_overrides[section] = {}
                    
                    # Type conversion
                    if value.lower() in ("true", "false"):
                        env_overrides[section][field_name] = value.lower() == "true"
                    elif value.isdigit():
                        env_overrides[section][field_name] = int(value)
                    else:
                        try:
                            env_overrides[section][field_name] = float(value)
                        except ValueError:
                            env_overrides[section][field_name] = value
        
        # Rebuild config with overrides
        if env_overrides:
            logger.info("Applying environment variable overrides: %s", list(env_overrides.keys()))
            
            return cls(
                system=SystemConfig(**env_overrides.get("system", {})),
                paths=PathsConfig(**env_overrides.get("paths", {})),
                performance=PerformanceConfig(**env_overrides.get("performance", {})),
                cache=CacheConfig(**env_overrides.get("cache", {})),
                logging=LoggingConfig(**env_overrides.get("logging", {})),
                knowledge_manager=KnowledgeManagerConfig(**env_overrides.get("knowledge_manager", {})),
                event_system=EventSystemConfig(**env_overrides.get("event_system", {})),
                web_research=WebResearchConfig(**env_overrides.get("web_research", {})),
                security=SecurityConfig(**env_overrides.get("security", {})),
                templates=TemplatesConfig(**env_overrides.get("templates", {})),
                monitoring=MonitoringConfig(**env_overrides.get("monitoring", {})),
                development=DevelopmentConfig(**env_overrides.get("development", {})),
            )
        
        return config

    def validate(self) -> None:
        """
        Validate configuration settings.
        
        Raises:
            ValueError: If configuration is invalid.
        """
        # Validate performance settings
        if self.performance.max_concurrent_operations < 1:
            raise ValueError("max_concurrent_operations must be >= 1")
        
        if self.performance.performance_threshold_ms < 0:
            raise ValueError("performance_threshold_ms must be >= 0")
        
        # Validate cache settings
        if self.cache.ttl_seconds < 0:
            raise ValueError("cache ttl_seconds must be >= 0")
        
        if self.cache.max_size < 0:
            raise ValueError("cache max_size must be >= 0")
        
        # Validate logging level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.logging.level.upper() not in valid_levels:
            raise ValueError(f"Invalid logging level: {self.logging.level}")
        
        # Validate security settings
        if self.security.max_requests_per_minute < 0:
            raise ValueError("max_requests_per_minute must be >= 0")
        
        # Validate monitoring thresholds
        if "error_rate" in self.monitoring.alert_thresholds:
            error_rate = self.monitoring.alert_thresholds["error_rate"]
            if not 0 <= error_rate <= 1:
                raise ValueError("error_rate threshold must be between 0 and 1")
        
        logger.info("Configuration validation passed")

    def get_absolute_paths(self, base_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        Get all configured paths as absolute paths.
        
        Args:
            base_dir: Base directory for relative paths.
            
        Returns:
            Dictionary of path names to absolute paths.
        """
        if base_dir is None:
            base_dir = Path.cwd()
            
        return {
            "prompts_dir": self.paths.get_absolute_path(self.paths.prompts_dir, base_dir),
            "knowledge_base_root": self.paths.get_absolute_path(self.paths.knowledge_base_root, base_dir),
            "config_dir": self.paths.get_absolute_path(self.paths.config_dir, base_dir),
            "cache_dir": self.paths.get_absolute_path(self.paths.cache_dir, base_dir),
            "logs_dir": self.paths.get_absolute_path(self.paths.logs_dir, base_dir),
            "tech_stack_mapping": self.paths.get_absolute_path(self.paths.tech_stack_mapping, base_dir),
            "templates_config": self.paths.get_absolute_path(self.paths.templates_config, base_dir),
        }


# Global configuration instance
_global_config: Optional[ApplicationConfig] = None


def get_config() -> ApplicationConfig:
    """
    Get the global configuration instance.
    
    Returns:
        ApplicationConfig instance.
        
    Raises:
        RuntimeError: If configuration hasn't been initialized.
    """
    global _global_config
    if _global_config is None:
        raise RuntimeError("Configuration not initialized. Call configure_application() first.")
    return _global_config


def configure_application(
    config_path: Optional[Union[str, Path]] = None,
    env_prefix: str = "EPG_",
    validate: bool = True
) -> ApplicationConfig:
    """
    Initialize the global application configuration.
    
    Args:
        config_path: Path to TOML configuration file. If None, uses defaults.
        env_prefix: Environment variable prefix for overrides.
        validate: Whether to validate the configuration.
        
    Returns:
        Configured ApplicationConfig instance.
        
    Raises:
        ValueError: If configuration is invalid.
        FileNotFoundError: If config file doesn't exist.
    """
    global _global_config
    
    if config_path:
        config = ApplicationConfig.from_toml(config_path)
    else:
        config = ApplicationConfig()
    
    # Apply environment overrides
    env_config = ApplicationConfig.from_env(env_prefix)
    if env_config != ApplicationConfig():
        # Merge environment overrides (this is simplified - in practice you'd want a proper merge)
        config = env_config
    
    if validate:
        config.validate()
    
    _global_config = config
    logger.info("Application configuration initialized successfully")
    
    return config


def reset_config() -> None:
    """Reset the global configuration. Used primarily for testing."""
    global _global_config
    _global_config = None