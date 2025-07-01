"""
Ansible Template Engine for automation and configuration management following SOLID principles.

Business Context: Generates Ansible playbooks, roles, and configurations
optimized for infrastructure automation and application deployment.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base_engine import ITemplateEngine, TemplateContext, TemplateResult


@dataclass
class AnsibleConfiguration:
    """Ansible-specific configuration parameters."""

    ansible_version: str = "2.15"
    python_version: str = "3.9"
    inventory_type: str = "ini"  # ini, yaml, dynamic
    vault_enabled: bool = False
    collections: List[str] = None


class AnsibleTemplateEngine(ITemplateEngine):
    """
    Specialized template engine for Ansible automation and configuration management.

    Business Context: Handles infrastructure automation, application deployment,
    and configuration management across multiple environments and platforms.

    Why this approach: Single Responsibility - focuses only on Ansible automation
    patterns while delegating specific technology configurations to specialized tasks.
    """

    @property
    def engine_name(self) -> str:
        return "ansible"

    @property
    def supported_technologies(self) -> List[str]:
        return [
            "ansible",
            "automation",
            "configuration-management",
            "deployment",
            "linux",
            "rhel",
            "ubuntu",
            "centos",
            "debian",
            "systemd",
            "nginx",
            "apache",
            "postgresql",
            "mysql",
            "redis",
            "docker",
            "prometheus",
            "grafana",
            "ssl",
            "firewall",
            "users",
            "packages",
        ]

    def __init__(self):
        self._logger = logging.getLogger(__name__)

        # Task templates for different automation scenarios
        self._automation_templates = self._initialize_automation_templates()
        self._role_templates = self._initialize_role_templates()
        self._inventory_templates = self._initialize_inventory_templates()

    def _initialize_automation_templates(self) -> Dict[str, Dict]:
        """Initialize automation scenario templates (≤20 lines)."""
        return {
            "system_setup": {
                "description": "System configuration and hardening",
                "tasks": ["users", "packages", "firewall", "ssh", "monitoring"],
            },
            "application_deployment": {
                "description": "Application installation and configuration",
                "tasks": ["dependencies", "app_install", "config", "service", "health_check"],
            },
            "monitoring_setup": {
                "description": "Monitoring stack deployment",
                "tasks": ["prometheus", "grafana", "alerting", "dashboards"],
            },
            "database_setup": {
                "description": "Database installation and configuration",
                "tasks": ["install", "config", "users", "backup", "replication"],
            },
            "web_server_setup": {
                "description": "Web server deployment and SSL configuration",
                "tasks": ["install", "vhosts", "ssl", "security", "optimization"],
            },
        }

    def _initialize_role_templates(self) -> Dict[str, Dict]:
        """Initialize reusable role templates (≤20 lines)."""
        return {
            "common": {
                "description": "Common system configuration",
                "tasks": ["update_system", "install_basics", "configure_users", "setup_ssh"],
            },
            "docker": {
                "description": "Docker installation and configuration",
                "tasks": [
                    "install_docker",
                    "configure_daemon",
                    "setup_compose",
                    "manage_containers",
                ],
            },
            "monitoring": {
                "description": "Monitoring stack deployment",
                "tasks": [
                    "install_prometheus",
                    "configure_grafana",
                    "setup_alerting",
                    "create_dashboards",
                ],
            },
            "security": {
                "description": "Security hardening and compliance",
                "tasks": ["firewall_rules", "ssl_certs", "user_policies", "audit_logging"],
            },
        }

    def _initialize_inventory_templates(self) -> Dict[str, str]:
        """Initialize inventory templates for different environments (≤15 lines)."""
        return {
            "single_host": "Single server deployment",
            "multi_tier": "Multi-tier architecture (web, app, db)",
            "cluster": "Clustered deployment with load balancing",
            "cloud": "Cloud-based infrastructure with auto-scaling",
        }

    def can_handle(self, context: TemplateContext) -> bool:
        """
        Determine if this engine can handle the context.

        Business Context: Focuses on automation, configuration management,
        and multi-host deployment scenarios.
        """
        tech_lower = context.technology.lower()
        task_lower = context.task_description.lower()

        # Direct Ansible technologies
        if any(tech in tech_lower for tech in ["ansible", "automation", "configuration"]):
            return True

        # Automation-related keywords in task description
        automation_keywords = [
            "deploy",
            "install",
            "configure",
            "setup",
            "automate",
            "provision",
            "manage",
            "orchestrate",
            "playbook",
        ]
        if any(keyword in task_lower for keyword in automation_keywords):
            return True

        # Multi-host or infrastructure scenarios
        if any(tech in tech_lower for tech in self.supported_technologies):
            cluster_size = getattr(context.specific_options, "cluster_size", 0)
            ha_setup = getattr(context.specific_options, "ha_setup", False)

            # Prefer Ansible for multi-host deployments
            if cluster_size and cluster_size > 1:
                return True
            if ha_setup:
                return True

        return False

    def estimate_complexity(self, context: TemplateContext) -> str:
        """Estimate automation complexity based on scope."""
        tech_count = len(context.technology.split())
        cluster_size = getattr(context.specific_options, "cluster_size", 1)
        ha_setup = getattr(context.specific_options, "ha_setup", False)

        complexity_score = tech_count + (cluster_size - 1) * 2
        if ha_setup:
            complexity_score += 3

        if complexity_score >= 8:
            return "complex"
        elif complexity_score >= 4:
            return "moderate"
        else:
            return "simple"

    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """
        Generate Ansible template based on context.

        Business Context: Main entry point that orchestrates playbook
        generation based on automation requirements and target infrastructure.
        """
        self._logger.info(f"Generating Ansible template for: {context.technology}")

        # Parse technologies and context
        technologies = self._parse_technologies(context.technology)
        ansible_config = self._build_ansible_config(context)

        # Determine automation scenario
        scenario = self._determine_scenario(technologies, context)

        # Generate appropriate template based on complexity
        if self.estimate_complexity(context) == "complex":
            template_content = self._generate_role_based_playbook(
                technologies, context, ansible_config, scenario
            )
        else:
            template_content = self._generate_simple_playbook(
                technologies, context, ansible_config, scenario
            )

        import hashlib
        from datetime import datetime

        context_hash = hashlib.md5(
            f"{context.technology}_{context.task_description}_{getattr(context.specific_options, 'distro', '')}".encode()
        ).hexdigest()[:8]

        return TemplateResult(
            content=template_content,
            template_type="ansible",
            confidence_score=0.85,
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
            if tech in ["rhel", "rhel9", "redhat"]:
                normalized.append("rhel")
            elif tech in ["ubuntu", "ubuntu22", "ubuntu20"]:
                normalized.append("ubuntu")
            elif tech in self.supported_technologies:
                normalized.append(tech)
            else:
                normalized.append(tech)

        return normalized

    def _build_ansible_config(self, context: TemplateContext) -> AnsibleConfiguration:
        """Build Ansible configuration from context (≤15 lines)."""
        specific_opts = context.specific_options

        collections = []
        if any(tech in context.technology.lower() for tech in ["docker", "container"]):
            collections.append("community.docker")
        if any(tech in context.technology.lower() for tech in ["kubernetes", "k8s"]):
            collections.append("kubernetes.core")

        return AnsibleConfiguration(
            ansible_version="2.15",
            python_version="3.9",
            inventory_type="ini",
            vault_enabled=getattr(specific_opts, "security_standards", []) != [],
            collections=collections or None,
        )

    def _determine_scenario(self, technologies: List[str], context: TemplateContext) -> str:
        """Determine automation scenario based on technologies (≤15 lines)."""
        task_lower = context.task_description.lower()

        if any(tech in technologies for tech in ["prometheus", "grafana", "monitoring"]):
            return "monitoring_setup"
        elif any(tech in technologies for tech in ["postgresql", "mysql", "redis", "database"]):
            return "database_setup"
        elif any(tech in technologies for tech in ["nginx", "apache", "web"]):
            return "web_server_setup"
        elif any(word in task_lower for word in ["deploy", "application", "app"]):
            return "application_deployment"
        else:
            return "system_setup"

    def _generate_simple_playbook(
        self,
        technologies: List[str],
        context: TemplateContext,
        ansible_config: AnsibleConfiguration,
        scenario: str,
    ) -> str:
        """
        Generate simple playbook for straightforward automation.

        Business Context: Creates focused playbooks for single-purpose
        automation tasks with minimal complexity.
        """
        distro = self._get_distro_name(context)
        cluster_size = getattr(context.specific_options, "cluster_size", 1)

        # Generate playbook header
        playbook_parts = [
            f"# Ansible Playbook: {scenario.replace('_', ' ').title()}",
            f"# Target: {distro} ({cluster_size} host{'s' if cluster_size > 1 else ''})",
            f"# Generated for: {context.technology}",
            "",
            "---",
            "- name: " + scenario.replace("_", " ").title(),
            "  hosts: all",
            "  become: yes",
            "  gather_facts: yes",
            "",
        ]

        # Add variables section
        playbook_parts.extend(
            [
                "  vars:",
                f"    target_distro: {distro}",
                f"    cluster_size: {cluster_size}",
            ]
        )

        # Add technology-specific variables
        if "prometheus" in technologies:
            playbook_parts.extend(
                ["    prometheus_port: 9090", "    prometheus_data_dir: /var/lib/prometheus"]
            )
        if "grafana" in technologies:
            playbook_parts.extend(
                [
                    "    grafana_port: 3000",
                    "    grafana_admin_password: '{{ vault_grafana_password | default(\"admin123\") }}'",
                ]
            )

        playbook_parts.extend(["", "  tasks:"])

        # Generate tasks based on scenario and technologies
        tasks = self._generate_tasks_for_scenario(scenario, technologies, context)
        for task in tasks:
            playbook_parts.extend([f"    {line}" for line in task.split("\n")])
            playbook_parts.append("")

        # Add inventory and execution instructions
        playbook_parts.extend(
            [
                self._generate_inventory_section(context),
                "",
                self._generate_execution_instructions(context, ansible_config),
            ]
        )

        return "\n".join(playbook_parts)

    def _generate_role_based_playbook(
        self,
        technologies: List[str],
        context: TemplateContext,
        ansible_config: AnsibleConfiguration,
        scenario: str,
    ) -> str:
        """
        Generate role-based playbook for complex automation.

        Business Context: Creates modular playbooks using roles for
        complex, multi-component deployments.
        """
        distro = self._get_distro_name(context)
        cluster_size = getattr(context.specific_options, "cluster_size", 1)

        # Generate main playbook
        playbook_parts = [
            f"# Ansible Role-Based Playbook: {scenario.replace('_', ' ').title()}",
            f"# Target: {distro} cluster ({cluster_size} hosts)",
            f"# Technologies: {', '.join(technologies)}",
            "",
            "---",
            "- name: " + scenario.replace("_", " ").title(),
            "  hosts: all",
            "  become: yes",
            "  gather_facts: yes",
            "",
            "  vars:",
            f"    target_distro: {distro}",
            f"    cluster_size: {cluster_size}",
            "    ansible_user: ansible",
            "",
            "  roles:",
        ]

        # Add roles based on technologies
        roles = self._determine_roles(technologies, context)
        for role in roles:
            playbook_parts.append(f"    - {role}")

        # Generate role structures
        playbook_parts.extend(
            [
                "",
                "# Role Structure:",
                "# roles/",
            ]
        )

        for role in roles:
            role_structure = self._generate_role_structure(role, technologies, context)
            playbook_parts.extend([f"#   {line}" for line in role_structure])

        # Add inventory and deployment instructions
        playbook_parts.extend(
            [
                "",
                self._generate_inventory_section(context),
                "",
                self._generate_role_deployment_instructions(context, ansible_config, roles),
            ]
        )

        return "\n".join(playbook_parts)

    def _generate_tasks_for_scenario(
        self, scenario: str, technologies: List[str], context: TemplateContext
    ) -> List[str]:
        """Generate specific tasks for automation scenario (≤20 lines)."""
        tasks = []
        distro = self._get_distro_name(context)

        # Common system tasks
        if scenario in ["system_setup", "application_deployment"]:
            tasks.append(self._generate_system_update_task(distro))
            tasks.append(self._generate_firewall_task(context))

        # Technology-specific tasks
        for tech in technologies:
            if tech == "prometheus":
                tasks.append(self._generate_prometheus_task(distro))
            elif tech == "grafana":
                tasks.append(self._generate_grafana_task(distro))
            elif tech == "nginx":
                tasks.append(self._generate_nginx_task(distro))
            elif tech == "docker":
                tasks.append(self._generate_docker_task(distro))

        return tasks

    def _generate_system_update_task(self, distro: str) -> str:
        """Generate system update task for specific distribution (≤15 lines)."""
        if distro.startswith("rhel") or distro.startswith("rocky") or distro.startswith("alma"):
            return """- name: Update system packages (RHEL/Rocky/Alma)
  dnf:
    name: "*"
    state: latest
  tags: system"""
        elif distro.startswith("ubuntu") or distro.startswith("debian"):
            return """- name: Update system packages (Ubuntu/Debian)
  apt:
    update_cache: yes
    upgrade: dist
  tags: system"""
        else:
            return """- name: Update system packages
  package:
    name: "*"
    state: latest
  tags: system"""

    def _generate_prometheus_task(self, distro: str) -> str:
        """Generate Prometheus installation task (≤20 lines)."""
        if distro.startswith("rhel"):
            return """- name: Install and configure Prometheus
  block:
    - name: Create prometheus user
      user:
        name: prometheus
        system: yes
        shell: /bin/false
        home: /var/lib/prometheus
    
    - name: Download and install Prometheus
      unarchive:
        src: https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
        dest: /opt
        remote_src: yes
        owner: prometheus
        group: prometheus
    
    - name: Create Prometheus systemd service
      template:
        src: prometheus.service.j2
        dest: /etc/systemd/system/prometheus.service
      notify: restart prometheus
  tags: prometheus"""
        else:
            return """- name: Install Prometheus via package manager
  package:
    name: prometheus
    state: present
  tags: prometheus"""

    def _generate_grafana_task(self, distro: str) -> str:
        """Generate Grafana installation task (≤15 lines)."""
        return """- name: Install and configure Grafana
  block:
    - name: Add Grafana repository
      yum_repository:
        name: grafana
        description: Grafana Repository
        baseurl: https://packages.grafana.com/oss/rpm
        gpgcheck: yes
        gpgkey: https://packages.grafana.com/gpg.key
      when: ansible_os_family == "RedHat"
    
    - name: Install Grafana
      package:
        name: grafana
        state: present
    
    - name: Start and enable Grafana
      systemd:
        name: grafana-server
        state: started
        enabled: yes
  tags: grafana"""

    def _generate_nginx_task(self, distro: str) -> str:
        """Generate Nginx installation task (≤15 lines)."""
        return """- name: Install and configure Nginx
  block:
    - name: Install Nginx
      package:
        name: nginx
        state: present
    
    - name: Configure Nginx
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        backup: yes
      notify: restart nginx
    
    - name: Start and enable Nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
  tags: nginx"""

    def _generate_docker_task(self, distro: str) -> str:
        """Generate Docker installation task (≤15 lines)."""
        if distro.startswith("rhel"):
            return """- name: Install Docker on RHEL
  block:
    - name: Install Docker packages
      dnf:
        name: ['docker', 'docker-compose']
        state: present
    
    - name: Start and enable Docker
      systemd:
        name: docker
        state: started
        enabled: yes
    
    - name: Add user to docker group
      user:
        name: "{{ ansible_user }}"
        groups: docker
        append: yes
  tags: docker"""
        else:
            return """- name: Install Docker
  package:
    name: docker
    state: present
  tags: docker"""

    def _generate_firewall_task(self, context: TemplateContext) -> str:
        """Generate firewall configuration task (≤15 lines)."""
        return """- name: Configure firewall
  block:
    - name: Install firewalld
      package:
        name: firewalld
        state: present
    
    - name: Start and enable firewalld
      systemd:
        name: firewalld
        state: started
        enabled: yes
    
    - name: Open required ports
      firewalld:
        port: "{{ item }}"
        permanent: yes
        state: enabled
        immediate: yes
      loop:
        - "22/tcp"    # SSH
        - "80/tcp"    # HTTP
        - "443/tcp"   # HTTPS
        - "9090/tcp"  # Prometheus
        - "3000/tcp"  # Grafana
  tags: firewall"""

    def _determine_roles(self, technologies: List[str], context: TemplateContext) -> List[str]:
        """Determine roles needed for complex deployment (≤15 lines)."""
        roles = ["common"]  # Always include common role

        if any(tech in technologies for tech in ["prometheus", "grafana", "monitoring"]):
            roles.append("monitoring")
        if any(tech in technologies for tech in ["docker", "container"]):
            roles.append("docker")
        if any(tech in technologies for tech in ["nginx", "apache"]):
            roles.append("webserver")
        if any(tech in technologies for tech in ["postgresql", "mysql"]):
            roles.append("database")

        # Always include security for enterprise deployments
        roles.append("security")

        return roles

    def _generate_role_structure(
        self, role: str, technologies: List[str], context: TemplateContext
    ) -> List[str]:
        """Generate role directory structure (≤15 lines)."""
        return [
            f"{role}/",
            f"  tasks/main.yml",
            f"  handlers/main.yml",
            f"  templates/",
            f"  vars/main.yml",
            f"  defaults/main.yml",
            f"  meta/main.yml",
        ]

    def _generate_inventory_section(self, context: TemplateContext) -> str:
        """Generate inventory configuration (≤20 lines)."""
        cluster_size = getattr(context.specific_options, "cluster_size", 1)
        distro = self._get_distro_name(context)

        if cluster_size > 1:
            inventory_lines = [
                "# inventory/hosts.ini",
                "[all:vars]",
                "ansible_user=ansible",
                "ansible_ssh_private_key_file=~/.ssh/id_rsa",
                "",
                "[cluster]",
            ]

            for i in range(cluster_size):
                inventory_lines.append(f"host{i+1:02d} ansible_host=192.168.1.{10+i}")

            inventory_lines.extend(
                ["", "[monitoring:children]", "cluster", "", f"[{distro}:children]", "cluster"]
            )
        else:
            inventory_lines = [
                "# inventory/hosts.ini",
                "[all:vars]",
                "ansible_user=ansible",
                "ansible_ssh_private_key_file=~/.ssh/id_rsa",
                "",
                "[servers]",
                "server01 ansible_host=192.168.1.10",
            ]

        return "\n".join(inventory_lines)

    def _generate_execution_instructions(
        self, context: TemplateContext, ansible_config: AnsibleConfiguration
    ) -> str:
        """Generate execution instructions (≤20 lines)."""
        distro = self._get_distro_name(context)

        instructions = [
            "## ANSIBLE EXECUTION INSTRUCTIONS",
            "",
            "```bash",
            "# Install Ansible (Control Node)",
        ]

        if distro.startswith("rhel"):
            instructions.extend(
                ["sudo dnf install -y ansible python3-pip", "pip3 install ansible-core"]
            )
        else:
            instructions.extend(
                ["sudo apt update && sudo apt install -y ansible", "pip3 install ansible"]
            )

        instructions.extend(
            [
                "",
                "# Install required collections",
            ]
        )

        if ansible_config.collections:
            for collection in ansible_config.collections:
                instructions.append(f"ansible-galaxy collection install {collection}")

        instructions.extend(
            [
                "",
                "# Test connectivity",
                "ansible all -i inventory/hosts.ini -m ping",
                "",
                "# Run playbook",
                "ansible-playbook -i inventory/hosts.ini playbook.yml",
                "",
                "# Run with vault (if using secrets)",
                "ansible-playbook -i inventory/hosts.ini playbook.yml --ask-vault-pass",
                "```",
            ]
        )

        return "\n".join(instructions)

    def _generate_role_deployment_instructions(
        self, context: TemplateContext, ansible_config: AnsibleConfiguration, roles: List[str]
    ) -> str:
        """Generate role-based deployment instructions (≤15 lines)."""
        instructions = [
            "## ROLE-BASED DEPLOYMENT",
            "",
            "```bash",
            "# Create role structure",
            "mkdir -p roles/{"
            + ",".join(roles)
            + "}/{tasks,handlers,templates,vars,defaults,meta}",
            "",
            "# Initialize roles",
        ]

        for role in roles:
            instructions.append(f"ansible-galaxy init roles/{role}")

        instructions.extend(
            [
                "",
                "# Deploy with tags",
                "ansible-playbook -i inventory/hosts.ini site.yml --tags monitoring",
                "ansible-playbook -i inventory/hosts.ini site.yml --tags security",
                "```",
            ]
        )

        return "\n".join(instructions)

    # Helper methods (≤10 lines each)
    def _get_distro_name(self, context: TemplateContext) -> str:
        """Get distribution name from context."""
        return getattr(context.specific_options, "distro", "rhel9") or "rhel9"
