"""
Patroni PostgreSQL Template Engine following Single Responsibility Principle.

Business Context: Generates production-ready Patroni cluster configurations
with proper distribution-specific commands and monitoring integration.
"""

from datetime import datetime
from typing import Dict, List

from .base_engine import BaseTemplateEngine, TemplateContext, TemplateResult


class PatroniTemplateEngine(BaseTemplateEngine):
    """
    Specialized engine for Patroni PostgreSQL cluster templates.

    Why this approach: Single Responsibility - only handles Patroni,
    making it easier to test, maintain, and extend.
    """

    def __init__(self):
        super().__init__(
            name="patroni", technologies=["patroni", "postgresql-cluster", "postgres-ha"]
        )

        # Distribution-specific commands (immutable configuration)
        self._distro_commands = {
            "rhel9": {
                "install": "sudo dnf install -y postgresql-server python3-pip",
                "pip_install": "sudo pip3 install patroni[etcd] psycopg2-binary",
                "service": "sudo systemctl enable --now patroni",
            },
            "ubuntu22": {
                "install": "sudo apt update && sudo apt install -y postgresql python3-pip",
                "pip_install": "sudo pip3 install patroni[etcd] psycopg2-binary",
                "service": "sudo systemctl enable --now patroni",
            },
            "debian11": {
                "install": "sudo apt update && sudo apt install -y postgresql python3-pip",
                "pip_install": "sudo pip3 install patroni[etcd] psycopg2-binary",
                "service": "sudo systemctl enable --now patroni",
            },
        }

    def can_handle(self, context: TemplateContext) -> bool:
        """Check if this engine should handle the context."""
        return (
            context.specific_options.db_engine == "patroni"
            or "patroni" in context.technology.lower()
            or ("postgresql" in context.technology.lower() and context.get_cluster_size() > 1)
        )

    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """Generate Patroni cluster template."""
        content_parts = [
            self._generate_header(context),
            self._generate_patroni_config(context),
            self._generate_installation_script(context),
            self._generate_systemd_service(context),
            self._generate_footer(context),
        ]

        content = "\n".join(content_parts)

        return TemplateResult(
            content=content,
            template_type="patroni_cluster",
            confidence_score=self.get_quality_score(content, context),
            estimated_complexity=self.estimate_complexity(context),
            generated_at=datetime.now(),
            context_hash=self._calculate_context_hash(context),
        )

    def _generate_patroni_config(self, context: TemplateContext) -> str:
        """Generate Patroni YAML configuration."""
        cluster_size = context.get_cluster_size()
        distro = context.get_distro()

        # Generate etcd hosts
        etcd_hosts = ", ".join([f"192.168.1.{10+i}:2379" for i in range(cluster_size)])

        # Monitoring configuration
        monitoring_config = self._generate_monitoring_config(context)

        return f"""```yaml
# patroni.yml - {cluster_size}-node cluster configuration for {distro.upper()}
scope: postgres-cluster
namespace: /db/
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 192.168.1.10:8008

etcd:
  hosts: {etcd_hosts}

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 200
        shared_preload_libraries: 'pg_stat_statements'
        wal_level: replica
        hot_standby: on
        max_wal_senders: {cluster_size + 1}
        max_replication_slots: {cluster_size + 1}{monitoring_config}

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 192.168.1.10:5432
  data_dir: /var/lib/postgresql/data
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: replicator_password
    superuser:
      username: postgres
      password: postgres_password
  parameters:
    unix_socket_directories: '/var/run/postgresql'

{self._generate_ha_config(context)}
{self._generate_backup_config(context)}
```"""

    def _generate_monitoring_config(self, context: TemplateContext) -> str:
        """Generate monitoring-specific configuration."""
        if not context.specific_options.monitoring_stack:
            return ""

        config_parts = []

        if context.has_monitoring("prometheus"):
            config_parts.append(
                """
# Prometheus metrics endpoint
tags:
  prometheus_port: 8008"""
            )

        if context.has_monitoring("nagios"):
            config_parts.append(
                """
  nagios_checks: true"""
            )

        return "".join(config_parts)

    def _generate_ha_config(self, context: TemplateContext) -> str:
        """Generate high availability configuration."""
        if not context.specific_options.ha_setup:
            return ""

        return """# High Availability Configuration
# - Automatic failover enabled
# - Synchronous replication for consistency
# - Leader election via etcd consensus"""

    def _generate_backup_config(self, context: TemplateContext) -> str:
        """Generate backup strategy configuration."""
        if not context.specific_options.backup_strategy:
            return ""

        strategy = context.specific_options.backup_strategy
        return f"# Backup Strategy: {strategy}"

    def _generate_installation_script(self, context: TemplateContext) -> str:
        """Generate distribution-specific installation commands."""
        distro = context.get_distro()
        commands = self._distro_commands.get(distro, self._distro_commands["rhel9"])

        return f"""```bash
# Installation and setup for {distro.upper()}
{commands["install"]}
{commands["pip_install"]}

# Create patroni configuration directory
sudo mkdir -p /etc/patroni
sudo cp patroni.yml /etc/patroni/
```"""

    def _generate_systemd_service(self, context: TemplateContext) -> str:
        """Generate systemd service configuration."""
        commands = self._distro_commands.get(context.get_distro(), self._distro_commands["rhel9"])

        return f"""```bash
# Create systemd service
sudo tee /etc/systemd/system/patroni.service > /dev/null <<EOF
[Unit]
Description=Runners to orchestrate a high-availability PostgreSQL
After=syslog.target network.target

[Service]
Type=simple
User=postgres
Group=postgres
ExecStart=/usr/local/bin/patroni /etc/patroni/patroni.yml
KillMode=process
TimeoutSec=30
Restart=no

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
{commands["service"]}
```"""

    def estimate_complexity(self, context: TemplateContext) -> str:
        """Estimate complexity specific to Patroni deployments."""
        complexity_factors = 0

        # Cluster size factor
        if context.get_cluster_size() > 3:
            complexity_factors += 1

        # Monitoring integration
        if context.specific_options.monitoring_stack:
            complexity_factors += len(context.specific_options.monitoring_stack)

        # High availability features
        if context.specific_options.ha_setup:
            complexity_factors += 1

        # Security standards
        if context.specific_options.security_standards:
            complexity_factors += 1

        # Backup strategy
        if context.specific_options.backup_strategy:
            complexity_factors += 1

        if complexity_factors <= 1:
            return "simple"
        elif complexity_factors <= 3:
            return "moderate"
        else:
            return "complex"

    def get_quality_score(self, content: str, context: TemplateContext) -> float:
        """Calculate Patroni-specific quality score."""
        base_score = super().get_quality_score(content, context)

        # Patroni-specific quality indicators
        patroni_indicators = [
            "scope:",
            "etcd:",
            "postgresql:",
            "bootstrap:",
            "authentication:",
            "replication:",
        ]

        present_indicators = sum(1 for indicator in patroni_indicators if indicator in content)

        # Bonus for Patroni completeness
        completeness_bonus = (present_indicators / len(patroni_indicators)) * 0.2

        # Distribution-specific commands bonus
        if context.get_distro() in content:
            base_score += 0.1

        return min(1.0, base_score + completeness_bonus)
