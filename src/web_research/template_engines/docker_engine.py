"""
Docker Template Engine for containerized deployments following SOLID principles.

Business Context: Generates Docker and Docker Compose configurations
optimized for specific distributions and container orchestration scenarios.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base_engine import ITemplateEngine, TemplateContext, TemplateResult


@dataclass
class DockerConfiguration:
    """Docker-specific configuration parameters."""

    runtime: str = "docker"  # docker, podman
    compose_version: str = "3.8"
    registry: Optional[str] = None
    network_mode: str = "bridge"
    volume_driver: str = "local"


class DockerTemplateEngine(ITemplateEngine):
    """
    Specialized template engine for Docker and Docker Compose deployments.

    Business Context: Handles containerized applications with focus on
    monitoring stacks, web applications, and microservices architectures.

    Why this approach: Single Responsibility - focuses only on Docker/container
    orchestration patterns while delegating specific technology configurations
    to specialized methods.
    """

    @property
    def engine_name(self) -> str:
        return "docker"

    @property
    def supported_technologies(self) -> List[str]:
        return [
            "docker",
            "docker-compose",
            "prometheus",
            "grafana",
            "alertmanager",
            "victoria-metrics",
            "nginx",
            "redis",
            "postgresql",
            "mysql",
            "elasticsearch",
            "kibana",
        ]

    def __init__(self):
        self._logger = logging.getLogger(__name__)

        # Technology-specific configurations
        self._monitoring_configs = self._initialize_monitoring_configs()
        self._database_configs = self._initialize_database_configs()
        self._web_configs = self._initialize_web_configs()

    def _initialize_monitoring_configs(self) -> Dict[str, Dict]:
        """Initialize monitoring stack configurations (≤20 lines)."""
        return {
            "prometheus": {
                "image": "prom/prometheus:latest",
                "port": 9090,
                "config_path": "/etc/prometheus/prometheus.yml",
                "data_path": "/prometheus",
                "command": [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/etc/prometheus/console_libraries",
                    "--web.console.templates=/etc/prometheus/consoles",
                ],
            },
            "grafana": {
                "image": "grafana/grafana:latest",
                "port": 3000,
                "data_path": "/var/lib/grafana",
                "env_vars": {"GF_SECURITY_ADMIN_PASSWORD": "admin123"},
            },
            "victoria-metrics": {
                "image": "victoriametrics/victoria-metrics:latest",
                "port": 8428,
                "data_path": "/victoria-metrics-data",
                "command": ["-storageDataPath=/victoria-metrics-data", "-retentionPeriod=1y"],
            },
            "alertmanager": {
                "image": "prom/alertmanager:latest",
                "port": 9093,
                "config_path": "/etc/alertmanager/alertmanager.yml",
            },
        }

    def _initialize_database_configs(self) -> Dict[str, Dict]:
        """Initialize database configurations (≤20 lines)."""
        return {
            "postgresql": {
                "image": "postgres:14-alpine",
                "port": 5432,
                "env_vars": {
                    "POSTGRES_DB": "myapp",
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "postgres_password",
                },
                "data_path": "/var/lib/postgresql/data",
            },
            "redis": {
                "image": "redis:7-alpine",
                "port": 6379,
                "data_path": "/data",
                "command": ["redis-server", "--appendonly", "yes"],
            },
        }

    def _initialize_web_configs(self) -> Dict[str, Dict]:
        """Initialize web server configurations (≤20 lines)."""
        return {
            "nginx": {"image": "nginx:alpine", "port": 80, "config_path": "/etc/nginx/nginx.conf"}
        }

    def can_handle(self, context: TemplateContext) -> bool:
        """
        Determine if this engine can handle the context.

        Business Context: Focuses on containerized deployments and
        orchestration scenarios.
        """
        tech_lower = context.technology.lower()

        # Direct Docker/container technologies
        if any(tech in tech_lower for tech in ["docker", "compose", "container"]):
            return True

        # Containerizable technologies - Docker can handle most monitoring and web technologies
        if any(tech in tech_lower for tech in self.supported_technologies):
            # Always handle monitoring technologies via Docker
            if any(tech in tech_lower for tech in ["prometheus", "grafana", "alertmanager", "victoria-metrics"]):
                return True
                
            # Handle other technologies when Docker is preferred
            orchestrator = getattr(context.specific_options, "orchestrator", "")
            container_runtime = getattr(context.specific_options, "container_runtime", "")

            # Prefer when Docker/compose is explicitly specified
            if any(keyword in orchestrator.lower() for keyword in ["docker", "compose"]):
                return True
            if any(keyword in container_runtime.lower() for keyword in ["docker", "podman"]):
                return True

        return False

    def estimate_complexity(self, context: TemplateContext) -> str:
        """Estimate deployment complexity."""
        tech_count = len(context.technology.split())

        if tech_count >= 4:
            return "complex"
        elif tech_count >= 2:
            return "moderate"
        else:
            return "simple"

    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """
        Generate Docker/Docker Compose template.

        Business Context: Main entry point that orchestrates template
        generation based on technology stack and deployment requirements.
        """
        self._logger.info(f"Generating Docker template for: {context.technology}")

        # Parse technologies and context
        technologies = self._parse_technologies(context.technology)
        docker_config = self._build_docker_config(context)

        # Check if monitoring stack is specified
        monitoring_stack = getattr(context.specific_options, "monitoring_stack", [])
        if monitoring_stack:
            # Include monitoring tools in technologies
            technologies.extend([tool for tool in monitoring_stack if tool not in technologies])

        # Generate appropriate template based on technology count
        if len(technologies) > 1 or monitoring_stack:
            template_content = self._generate_compose_template(technologies, context, docker_config)
        else:
            template_content = self._generate_dockerfile_template(
                technologies[0], context, docker_config
            )

        import hashlib
        from datetime import datetime

        context_hash = hashlib.md5(
            f"{context.technology}_{context.task_description}_{getattr(context.specific_options, 'distro', '')}".encode()
        ).hexdigest()[:8]

        return TemplateResult(
            content=template_content,
            template_type="docker",
            confidence_score=0.9,
            estimated_complexity=self.estimate_complexity(context),
            generated_at=datetime.now(),
            context_hash=context_hash,
        )

    def _parse_technologies(self, tech_string: str) -> List[str]:
        """Parse and normalize technology names (≤10 lines)."""
        techs = [tech.strip().lower() for tech in tech_string.split()]

        # Normalize common variations
        normalized = []
        for tech in techs:
            if "victoria" in tech or "vm" in tech:
                normalized.append("victoria-metrics")
            elif tech in self.supported_technologies:
                normalized.append(tech)
            else:
                normalized.append(tech)

        return normalized

    def _build_docker_config(self, context: TemplateContext) -> DockerConfiguration:
        """Build Docker configuration from context (≤15 lines)."""
        specific_opts = context.specific_options

        return DockerConfiguration(
            runtime=getattr(specific_opts, "container_runtime", "docker"),
            compose_version="3.8",
            registry=None,
            network_mode="bridge",
            volume_driver="local",
        )

    def _generate_compose_template(
        self, technologies: List[str], context: TemplateContext, docker_config: DockerConfiguration
    ) -> str:
        """
        Generate Docker Compose template for multiple services.

        Business Context: Creates multi-service deployments with proper
        networking, volumes, and service dependencies.
        """
        services = []
        volumes = []
        configs = []

        # Generate services for each technology
        for tech in technologies:
            if tech in self._monitoring_configs:
                service_def = self._generate_monitoring_service(tech, context)
                services.append(service_def)

                # Add volumes for persistent data
                if self._monitoring_configs[tech].get("data_path"):
                    volumes.append(f"{tech}_data:")

                # Add configuration files
                if tech == "prometheus":
                    configs.append(self._generate_prometheus_config(context))
                elif tech == "alertmanager":
                    configs.append(self._generate_alertmanager_config(context))

        # Build complete docker-compose.yml
        template_parts = [
            f"# {self._get_stack_description(technologies)} on {self._get_distro_name(context)}",
            f"version: '{docker_config.compose_version}'",
            "",
            "services:",
            *[f"  {service}" for service in services],
        ]

        if volumes:
            template_parts.extend(["", "volumes:", *[f"  {vol}" for vol in volumes]])

        # Add configuration sections
        template_parts.extend(["", "# Configuration files:", *configs])

        # Add deployment instructions
        template_parts.extend(["", self._generate_deployment_instructions(context)])

        return "\n".join(template_parts)

    def _generate_monitoring_service(self, tech: str, context: TemplateContext) -> str:
        """Generate service definition for monitoring technology (≤20 lines)."""
        config = self._monitoring_configs[tech]
        distro = self._get_distro_name(context)

        service_lines = [
            f"{tech}:",
            f"    image: {config['image']}",
            f"    container_name: {tech}",
            f"    ports:",
            f"      - \"{config['port']}:{config['port']}\"",
        ]

        # Add restart policy
        service_lines.append("    restart: unless-stopped")

        # Add volumes if needed
        if config.get("data_path"):
            service_lines.extend(["    volumes:", f"      - {tech}_data:{config['data_path']}"])

        # Add configuration volume for Prometheus
        if tech == "prometheus":
            service_lines.append("      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro")
        elif tech == "alertmanager":
            service_lines.append("      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro")

        # Add environment variables
        if config.get("env_vars"):
            service_lines.append("    environment:")
            for key, value in config["env_vars"].items():
                service_lines.append(f"      - {key}={value}")

        # Add custom commands
        if config.get("command"):
            service_lines.append("    command:")
            for cmd in config["command"]:
                service_lines.append(f"      - {cmd}")

        return "\n".join(service_lines)

    def _generate_prometheus_config(self, context: TemplateContext) -> str:
        """Generate Prometheus configuration file (≤20 lines)."""
        cluster_size = getattr(context.specific_options, "cluster_size", 1)

        return """
# Create prometheus.yml configuration file
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'victoria-metrics'
    static_configs:
      - targets: ['victoria-metrics:8428']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']"""

    def _generate_alertmanager_config(self, context: TemplateContext) -> str:
        """Generate Alertmanager configuration (≤15 lines)."""
        return """
# Create alertmanager.yml configuration file  
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@example.org'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'"""

    def _generate_deployment_instructions(self, context: TemplateContext) -> str:
        """Generate deployment instructions specific to distro (≤20 lines)."""
        distro = self._get_distro_name(context)

        if distro.startswith("rhel") or distro.startswith("rocky") or distro.startswith("alma"):
            return self._generate_rhel_instructions(context)
        elif distro.startswith("ubuntu"):
            return self._generate_ubuntu_instructions(context)
        else:
            return self._generate_generic_instructions(context)

    def _generate_rhel_instructions(self, context: TemplateContext) -> str:
        """Generate RHEL-specific deployment instructions (≤15 lines)."""
        return """## DEPLOYMENT INSTRUCTIONS (RHEL9)

```bash
# Install Docker (Red Hat supported)
sudo dnf install -y docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

# Create project directory
mkdir -p monitoring-stack
cd monitoring-stack

# Save the docker-compose.yml and configuration files
# Start the monitoring stack
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs
```"""

    def _generate_ubuntu_instructions(self, context: TemplateContext) -> str:
        """Generate Ubuntu-specific deployment instructions (≤15 lines)."""
        return """## DEPLOYMENT INSTRUCTIONS (Ubuntu)

```bash
# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

# Create and deploy
mkdir -p monitoring-stack && cd monitoring-stack
docker-compose up -d
```"""

    def _generate_generic_instructions(self, context: TemplateContext) -> str:
        """Generate generic deployment instructions (≤10 lines)."""
        return """## DEPLOYMENT INSTRUCTIONS

```bash
# Ensure Docker and Docker Compose are installed
# Create project directory and save configuration files
mkdir -p monitoring-stack && cd monitoring-stack

# Deploy the stack
docker-compose up -d
docker-compose ps
```"""

    def _generate_dockerfile_template(
        self, technology: str, context: TemplateContext, docker_config: DockerConfiguration
    ) -> str:
        """
        Generate single Dockerfile template.

        Business Context: Creates optimized Dockerfile for single
        technology deployments with security and efficiency focus.
        """
        if technology in self._monitoring_configs:
            config = self._monitoring_configs[technology]

            return f"""# {technology.title()} Dockerfile for {self._get_distro_name(context)}

FROM {config['image']}

# Set working directory
WORKDIR /app

# Copy configuration files
COPY config/ /etc/{technology}/

# Expose port
EXPOSE {config['port']}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:{config['port']}/health || exit 1

# Run as non-root user
USER 1001

# Start the service
CMD {config.get('command', [f'{technology}'])}

## BUILD INSTRUCTIONS
# docker build -t {technology}:latest .
# docker run -p {config['port']}:{config['port']} {technology}:latest
"""

        return self._generate_generic_dockerfile(technology, context)

    def _generate_generic_dockerfile(self, technology: str, context: TemplateContext) -> str:
        """Generate generic Dockerfile template (≤15 lines)."""
        return f"""# Generic Dockerfile for {technology}

FROM alpine:latest

# Install dependencies
RUN apk add --no-cache {technology}

# Set working directory  
WORKDIR /app

# Copy application files
COPY . .

# Expose default port
EXPOSE 8080

# Run as non-root
USER 1001

CMD ["{technology}"]
"""

    # Helper methods (≤10 lines each)
    def _get_stack_description(self, technologies: List[str]) -> str:
        """Generate stack description."""
        if len(technologies) >= 3:
            return f"Complete monitoring stack with {', '.join(technologies[:2])} and {len(technologies)-2} more services"
        else:
            return f"Monitoring stack with {' + '.join(technologies)}"

    def _get_distro_name(self, context: TemplateContext) -> str:
        """Get distribution name from context."""
        return getattr(context.specific_options, "distro", "linux") or "linux"
