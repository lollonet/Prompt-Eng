"""
Enterprise configuration management with validation and environment support.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import os
from enum import Enum
import json
import logging


class Environment(Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class SearchProviderConfig:
    """Configuration for search providers."""
    provider_type: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit_per_minute: int = 30
    timeout_seconds: int = 10
    max_retries: int = 3
    enabled: bool = True


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    provider: str = "file"  # file, redis, memory
    ttl_seconds: int = 3600
    max_size_mb: int = 100
    cleanup_interval_minutes: int = 60
    redis_url: Optional[str] = None
    file_cache_path: str = "cache/research"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60
    max_timeout_seconds: int = 300
    exponential_backoff: bool = True


@dataclass
class ResearchConfig:
    """Research process configuration."""
    max_concurrent_requests: int = 3
    research_timeout_seconds: int = 120
    min_quality_threshold: float = 0.6
    max_search_results_per_query: int = 10
    research_queries_per_technology: int = 5
    enable_code_extraction: bool = True
    enable_best_practices_extraction: bool = True


@dataclass
class TemplateConfig:
    """Template generation configuration."""
    min_template_length: int = 500
    max_template_length: int = 5000
    include_code_examples: bool = True
    include_best_practices: bool = True
    template_format: str = "jinja2"
    auto_enhancement: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    allowed_domains: List[str] = field(default_factory=lambda: [
        "github.com", "stackoverflow.com", "docs.python.org",
        "developer.mozilla.org", "aws.amazon.com", "kubernetes.io"
    ])
    blocked_domains: List[str] = field(default_factory=list)
    max_url_length: int = 2048
    sanitize_html: bool = True
    validate_ssl: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "logs/web_research.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_structured_logging: bool = True


@dataclass
class WebResearchConfig:
    """Main configuration container."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # Component configurations
    search_providers: Dict[str, SearchProviderConfig] = field(default_factory=dict)
    cache: CacheConfig = field(default_factory=CacheConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    template: TemplateConfig = field(default_factory=TemplateConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Runtime settings
    project_root: Path = field(default_factory=lambda: Path.cwd())
    config_file_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_configuration()
        self._setup_default_providers()
    
    def _validate_configuration(self) -> None:
        """Validate configuration values."""
        if self.research.max_concurrent_requests <= 0:
            raise ValueError("max_concurrent_requests must be positive")
        
        if self.cache.ttl_seconds <= 0:
            raise ValueError("cache TTL must be positive")
        
        if self.research.min_quality_threshold < 0 or self.research.min_quality_threshold > 1:
            raise ValueError("quality threshold must be between 0 and 1")
        
        # Ensure cache directory exists
        cache_path = Path(self.cache.file_cache_path)
        cache_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_default_providers(self) -> None:
        """Setup default search providers if none configured."""
        if not self.search_providers:
            self.search_providers = {
                "duckduckgo": SearchProviderConfig(
                    provider_type="duckduckgo",
                    rate_limit_per_minute=30,
                    enabled=True
                ),
                "bing": SearchProviderConfig(
                    provider_type="bing",
                    api_key=os.getenv("BING_API_KEY"),
                    rate_limit_per_minute=100,
                    enabled=bool(os.getenv("BING_API_KEY"))
                )
            }
    
    @classmethod
    def from_file(cls, config_path: str) -> 'WebResearchConfig':
        """Load configuration from JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'WebResearchConfig':
        """Create configuration from dictionary."""
        # Convert nested dictionaries to dataclass instances
        config = cls()
        
        for key, value in config_dict.items():
            if hasattr(config, key):
                if key == 'search_providers' and isinstance(value, dict):
                    providers = {}
                    for provider_name, provider_config in value.items():
                        providers[provider_name] = SearchProviderConfig(**provider_config)
                    setattr(config, key, providers)
                elif key in ['cache', 'circuit_breaker', 'research', 'template', 'security', 'logging']:
                    dataclass_type = {
                        'cache': CacheConfig,
                        'circuit_breaker': CircuitBreakerConfig,
                        'research': ResearchConfig,
                        'template': TemplateConfig,
                        'security': SecurityConfig,
                        'logging': LoggingConfig
                    }[key]
                    setattr(config, key, dataclass_type(**value))
                else:
                    setattr(config, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, (CacheConfig, CircuitBreakerConfig, ResearchConfig, 
                                TemplateConfig, SecurityConfig, LoggingConfig)):
                result[key] = value.__dict__
            elif key == 'search_providers':
                result[key] = {name: provider.__dict__ for name, provider in value.items()}
            elif isinstance(value, (Path, Environment)):
                result[key] = str(value)
            else:
                result[key] = value
        return result
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    def get_search_provider_config(self, provider_name: str) -> Optional[SearchProviderConfig]:
        """Get configuration for specific search provider."""
        return self.search_providers.get(provider_name)
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is allowed for research."""
        if domain in self.security.blocked_domains:
            return False
        
        if not self.security.allowed_domains:
            return True
        
        return any(allowed in domain for allowed in self.security.allowed_domains)


class ConfigurationManager:
    """Singleton configuration manager."""
    
    _instance: Optional[WebResearchConfig] = None
    _logger = logging.getLogger(__name__)
    
    @classmethod
    def get_config(cls) -> WebResearchConfig:
        """Get singleton configuration instance."""
        if cls._instance is None:
            cls._instance = cls._load_configuration()
        return cls._instance
    
    @classmethod
    def _load_configuration(cls) -> WebResearchConfig:
        """Load configuration from environment and files."""
        # Try to load from environment variable
        config_path = os.getenv('WEB_RESEARCH_CONFIG')
        if config_path and Path(config_path).exists():
            cls._logger.info(f"Loading configuration from: {config_path}")
            return WebResearchConfig.from_file(config_path)
        
        # Try to load from default locations
        default_locations = [
            'config/web_research.json',
            'web_research_config.json',
            os.path.expanduser('~/.web_research_config.json')
        ]
        
        for location in default_locations:
            if Path(location).exists():
                cls._logger.info(f"Loading configuration from: {location}")
                return WebResearchConfig.from_file(location)
        
        # Use default configuration
        cls._logger.info("Using default configuration")
        config = WebResearchConfig()
        
        # Override with environment variables
        if os.getenv('WEB_RESEARCH_DEBUG'):
            config.debug = os.getenv('WEB_RESEARCH_DEBUG').lower() == 'true'
        
        if os.getenv('WEB_RESEARCH_ENV'):
            config.environment = Environment(os.getenv('WEB_RESEARCH_ENV'))
        
        return config
    
    @classmethod
    def reload_config(cls, config_path: Optional[str] = None) -> WebResearchConfig:
        """Reload configuration."""
        cls._instance = None
        if config_path:
            os.environ['WEB_RESEARCH_CONFIG'] = config_path
        return cls.get_config()