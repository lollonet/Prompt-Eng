from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SpecificOptions:
    """Configuration for technology-specific options."""

    # Infrastructure options
    distro: Optional[str] = None  # rhel9, ubuntu22, centos8, debian11
    cloud_provider: Optional[str] = None  # aws, azure, gcp, on-premise
    region: Optional[str] = None  # eu-west-1, us-east-1, etc.

    # Database options
    db_engine: Optional[str] = None  # patroni, postgresql, mysql, mongodb
    db_version: Optional[str] = None  # 14, 15, 16 for PostgreSQL
    cluster_size: Optional[int] = None  # number of nodes

    # Container/Orchestration options
    container_runtime: Optional[str] = None  # docker, podman, containerd
    orchestrator: Optional[str] = None  # k8s, docker-compose, nomad, etcd
    ingress_controller: Optional[str] = None  # nginx, traefik, haproxy

    # Monitoring options
    monitoring_stack: Optional[List[str]] = field(
        default_factory=list
    )  # prometheus, nagios, grafana
    logging_stack: Optional[List[str]] = field(default_factory=list)  # elk, loki, fluentd

    # Security options
    security_standards: Optional[List[str]] = field(
        default_factory=list
    )  # fips140-2, pci-dss, hipaa
    encryption: Optional[str] = None  # tls1.3, aes256, rsa4096

    # Development options
    framework_version: Optional[str] = None  # specific version like "fastapi==0.104.1"
    testing_framework: Optional[str] = None  # pytest, jest, cypress
    ci_cd_platform: Optional[str] = None  # gitlab-ci, github-actions, jenkins

    # High availability options
    ha_setup: Optional[bool] = None
    backup_strategy: Optional[str] = None  # continuous, scheduled, snapshot
    disaster_recovery: Optional[bool] = None


@dataclass
class PromptConfig:
    """
    Enhanced configuration object for prompt generation with specific options.

    Business Context: Encapsulates all parameters needed for prompt generation
    including technology-specific options for precise, contextual examples.

    Why this approach: Using a configuration object with specific options
    allows for dynamic template generation with relevant examples based on
    exact technology stack requirements.
    """

    technologies: List[str]
    task_type: str
    code_requirements: str
    task_description: str = ""
    template_name: str = "base_prompts/generic_code_prompt.txt"
    specific_options: SpecificOptions = field(default_factory=SpecificOptions)

    def __post_init__(self):
        """
        Validates configuration after initialization.

        Raises:
            ValueError: If validation fails for any parameter.
        """
        if not self.technologies:
            raise ValueError("At least one technology must be specified")

        if not self.task_type or len(self.task_type.strip()) < 3:
            raise ValueError("Task type must be descriptive (minimum 3 characters)")

        if not self.code_requirements or len(self.code_requirements.strip()) < 10:
            raise ValueError("Code requirements must be detailed (minimum 10 characters)")

        # Normalize empty strings to prevent template rendering issues
        self.task_description = self.task_description.strip()
        self.task_type = self.task_type.strip()
        self.code_requirements = self.code_requirements.strip()

        # Validate technologies list contains only non-empty strings
        self.technologies = [tech.strip().lower() for tech in self.technologies if tech.strip()]
        if not self.technologies:
            raise ValueError("Technologies list cannot be empty after cleaning")
