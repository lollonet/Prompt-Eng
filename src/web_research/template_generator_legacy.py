"""
Enterprise Dynamic Template Generator with AI-driven content creation.
"""

import asyncio
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import hashlib
from pathlib import Path

from .interfaces import IDynamicTemplateGenerator, ResearchResult, SearchResult
from .config import WebResearchConfig, TemplateConfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..prompt_config import SpecificOptions


@dataclass
class TemplateSection:
    """Represents a section of a generated template."""
    name: str
    content: str
    priority: int
    confidence: float


@dataclass
class CodeExample:
    """Represents a code example extracted from research."""
    language: str
    code: str
    description: str
    source_url: str
    relevance_score: float


@dataclass
class BestPractice:
    """Represents a best practice extracted from research."""
    title: str
    description: str
    category: str
    source_url: str
    confidence: float


class DynamicTemplateGenerator(IDynamicTemplateGenerator):
    """
    Enterprise template generator following Single Responsibility Principle.
    
    Business Context: Orchestrates template generation by delegating to
    specialized engines, focusing only on research data extraction and
    quality validation.
    
    Why this approach: Composition over inheritance - uses specialized
    engines rather than implementing all template logic internally.
    """
    
    def __init__(self, config: WebResearchConfig):
        self.config = config
        self.template_config = config.template
        self._logger = logging.getLogger(__name__)
        
        # Template engine factory (dependency injection)
        from .template_engines.template_factory import get_template_factory
        self._template_factory = get_template_factory()
        
        # Content extractors (focused responsibility)
        self._code_extractors = self._initialize_code_extractors()
        self._practice_extractors = self._initialize_practice_extractors()
        
        # Quality thresholds (configuration)
        self._min_code_length = 20
        self._min_practice_length = 50
        self._relevance_threshold = 0.6
    
    def _load_template_structure(self) -> Dict[str, Any]:
        """Load base template structure patterns."""
        return {
            "focused_structure": {
                "header": "# {technology} {task_type}",
                "sections": [
                    "task_description",
                    "expected_output",
                    "requirements", 
                    "implementation_steps",
                    "best_practices",
                    "quality_checklist"
                ]
            },
            "comprehensive_structure": {
                "header": "# Complete {technology} {task_type} Guide",
                "sections": [
                    "overview",
                    "task_description",
                    "architecture_considerations",
                    "expected_output",
                    "requirements",
                    "implementation_steps",
                    "best_practices",
                    "testing_strategy",
                    "deployment_guide",
                    "monitoring_setup",
                    "quality_checklist"
                ]
            }
        }
    
    def _initialize_code_extractors(self) -> Dict[str, Any]:
        """Initialize code extraction patterns."""
        return {
            "code_block_patterns": [
                r'```(\w+)?\n(.*?)\n```',  # Markdown code blocks
                r'<code[^>]*>(.*?)</code>',  # HTML code tags
                r'`([^`\n]+)`',  # Inline code
                r'^\s{4,}(.+)$',  # Indented code (multiline)
            ],
            "language_indicators": {
                'python': ['def ', 'import ', 'from ', 'class ', 'pip install'],
                'javascript': ['function', 'const ', 'let ', 'var ', 'npm install'],
                'typescript': ['interface ', 'type ', 'export ', 'import '],
                'yaml': ['---', 'apiVersion:', 'kind:', 'metadata:'],
                'dockerfile': ['FROM ', 'RUN ', 'COPY ', 'EXPOSE '],
                'sql': ['SELECT ', 'INSERT ', 'CREATE TABLE', 'ALTER '],
                'bash': ['#!/bin/bash', '$ ', 'sudo ', 'apt-get'],
                'ansible': ['- name:', 'tasks:', 'playbook:', 'hosts:']
            },
            "quality_indicators": [
                'error handling',
                'validation',
                'testing',
                'logging',
                'configuration',
                'security',
                'performance'
            ]
        }
    
    def _initialize_practice_extractors(self) -> Dict[str, Any]:
        """Initialize best practice extraction patterns."""
        return {
            "practice_indicators": [
                r'best practice[s]?[:\-]?\s*(.+)',
                r'recommendation[s]?[:\-]?\s*(.+)',
                r'should\s+(always|never|use|avoid)\s+(.+)',
                r'important[:\-]?\s*(.+)',
                r'security[:\-]?\s*(.+)',
                r'performance[:\-]?\s*(.+)',
                r'tip[s]?[:\-]?\s*(.+)'
            ],
            "categories": {
                'security': ['auth', 'encrypt', 'validate', 'sanitiz', 'permission'],
                'performance': ['cache', 'optimize', 'fast', 'efficient', 'memory'],
                'maintainability': ['clean', 'readable', 'document', 'test', 'modular'],
                'reliability': ['error', 'exception', 'robust', 'fault', 'recover'],
                'scalability': ['scale', 'distribute', 'load', 'horizontal', 'cluster']
            },
            "quality_signals": [
                'production',
                'enterprise',
                'industry standard',
                'proven',
                'recommended'
            ]
        }
    
    async def generate_template(
        self, 
        research: ResearchResult, 
        specific_options: Optional['SpecificOptions'] = None
    ) -> str:
        """
        Generate dynamic template using specialized engines.
        
        Business Context: Main entry point that orchestrates research analysis
        and delegates to appropriate template engines for generation.
        """
        self._logger.info(f"Generating template for technology: {research.technology}")
        
        # Try engine-based generation first (preferred path)
        if specific_options:
            engine_result = await self._try_engine_generation(research, specific_options)
            if engine_result and engine_result.is_high_quality():
                return engine_result.content
        
        # Fallback to legacy generation for unknown technologies
        return await self._generate_legacy_template(research, specific_options)
    
    async def _try_engine_generation(
        self, 
        research: ResearchResult, 
        specific_options: 'SpecificOptions'
    ) -> Optional['TemplateResult']:
        """
        Attempt template generation using specialized engines.
        
        Why this approach: Delegation to specialized engines following
        Single Responsibility Principle.
        """
        from .template_engines.base_engine import TemplateContext
        
        context = TemplateContext(
            technology=research.technology,
            task_description=research.technology + " implementation",
            specific_options=specific_options,
            research_data=research.__dict__
        )
        
        try:
            return await self._template_factory.generate_template(context)
        except Exception as e:
            self._logger.warning(f"Engine generation failed: {e}")
            return None
    
    async def _generate_legacy_template(
        self, 
        research: ResearchResult, 
        specific_options: Optional['SpecificOptions']
    ) -> str:
        """
        Legacy template generation for unsupported technologies.
        
        Business Context: Maintains backward compatibility while
        new engines are being developed.
        """
        # Extract content using existing methods
        code_examples = await self._extract_code_examples(research)
        best_practices = await self._extract_best_practices(research)
        
        # Simple template assembly
        return self._assemble_simple_template(research, code_examples, best_practices)
    
    def _assemble_simple_template(
        self,
        research: ResearchResult,
        code_examples: List[CodeExample],
        best_practices: List[BestPractice]
    ) -> str:
        """
        Assemble simple template from extracted content.
        
        Why this approach: Focused function with single responsibility
        and clear parameter list (≤3 parameters).
        """
        sections = [
            f"# {research.technology.title()} Implementation",
            "",
            "## TASK", 
            f"Implement: **{research.technology} functionality**",
            "",
            self._generate_simple_examples_section(code_examples),
            "",
            self._generate_simple_practices_section(best_practices),
            "",
            "## IMPLEMENTATION STEPS",
            "1. Setup environment following official documentation",
            "2. Implement core functionality with error handling", 
            "3. Add comprehensive testing and monitoring",
            "",
            "Please implement following best practices."
        ]
        
        return "\n".join(sections)
    
    def _generate_simple_examples_section(self, examples: List[CodeExample]) -> str:
        """Generate simple examples section (≤20 lines)."""
        if not examples:
            return "## EXPECTED OUTPUT\n```\n# Implementation examples will be provided\n```"
        
        best_example = examples[0]
        return f"""## EXPECTED OUTPUT
```{best_example.language}
{best_example.code[:500]}...
```"""
    
    def _generate_simple_practices_section(self, practices: List[BestPractice]) -> str:
        """Generate simple best practices section (≤20 lines)."""
        if not practices:
            return "## BEST PRACTICES\n- Follow official documentation\n- Write comprehensive tests"
        
        practice_items = []
        for practice in practices[:3]:  # Limit to top 3
            practice_items.append(f"- {practice.title}")
        
        return "## BEST PRACTICES\n" + "\n".join(practice_items)
    
    async def _extract_code_examples(self, research: ResearchResult) -> List[CodeExample]:
        """Extract relevant code examples from research results."""
        code_examples = []
        
        for search_result in research.search_results:
            content = search_result.snippet
            
            # Extract code blocks using patterns
            for pattern in self._code_extractors["code_block_patterns"]:
                matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
                
                for match in matches:
                    code = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    
                    # Skip if too short
                    if len(code.strip()) < self._min_code_length:
                        continue
                    
                    # Detect language
                    language = self._detect_code_language(code)
                    
                    # Calculate relevance
                    relevance = self._calculate_code_relevance(
                        code, research.technology, search_result.title
                    )
                    
                    if relevance >= self._relevance_threshold:
                        code_examples.append(CodeExample(
                            language=language,
                            code=code.strip(),
                            description=self._generate_code_description(code, search_result.title),
                            source_url=search_result.url,
                            relevance_score=relevance
                        ))
        
        # Sort by relevance and remove duplicates
        code_examples = self._deduplicate_code_examples(code_examples)
        code_examples.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return code_examples[:5]  # Top 5 most relevant examples
    
    async def _extract_best_practices(self, research: ResearchResult) -> List[BestPractice]:
        """Extract best practices from research results."""
        best_practices = []
        
        for search_result in research.search_results:
            content = search_result.snippet + " " + search_result.title
            
            # Extract practices using patterns
            for pattern in self._practice_extractors["practice_indicators"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    practice_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    
                    # Skip if too short
                    if len(practice_text.strip()) < self._min_practice_length:
                        continue
                    
                    # Categorize practice
                    category = self._categorize_practice(practice_text)
                    
                    # Calculate confidence
                    confidence = self._calculate_practice_confidence(
                        practice_text, search_result, research.technology
                    )
                    
                    if confidence >= 0.5:  # Minimum confidence threshold
                        best_practices.append(BestPractice(
                            title=self._generate_practice_title(practice_text),
                            description=practice_text.strip(),
                            category=category,
                            source_url=search_result.url,
                            confidence=confidence
                        ))
        
        # Deduplicate and sort
        best_practices = self._deduplicate_best_practices(best_practices)
        best_practices.sort(key=lambda x: x.confidence, reverse=True)
        
        return best_practices[:8]  # Top 8 practices
    
    async def _extract_documentation_insights(self, research: ResearchResult) -> Dict[str, Any]:
        """Extract insights from official documentation."""
        insights = {
            "official_sources": [],
            "community_resources": [],
            "tutorials": [],
            "key_concepts": [],
            "common_patterns": []
        }
        
        for search_result in research.search_results:
            # Identify source type
            source_type = self._classify_source_type(search_result.url)
            
            if source_type == "official":
                insights["official_sources"].append({
                    "title": search_result.title,
                    "url": search_result.url,
                    "snippet": search_result.snippet
                })
            elif source_type == "community":
                insights["community_resources"].append({
                    "title": search_result.title,
                    "url": search_result.url,
                    "snippet": search_result.snippet
                })
            elif source_type == "tutorial":
                insights["tutorials"].append({
                    "title": search_result.title,
                    "url": search_result.url,
                    "snippet": search_result.snippet
                })
        
        return insights
    
    def _determine_template_type(
        self, 
        research: ResearchResult, 
        code_examples: List[CodeExample], 
        best_practices: List[BestPractice]
    ) -> str:
        """Determine appropriate template type based on content richness."""
        content_score = (
            len(code_examples) * 0.3 + 
            len(best_practices) * 0.2 + 
            len(research.search_results) * 0.1 +
            research.quality_score * 0.4
        )
        
        if content_score >= 3.0:
            return "comprehensive"
        else:
            return "focused"
    
    async def _generate_template_sections(
        self,
        research: ResearchResult,
        code_examples: List[CodeExample],
        best_practices: List[BestPractice],
        documentation_insights: Dict[str, Any],
        template_type: str
    ) -> List[TemplateSection]:
        """Generate individual template sections."""
        sections = []
        structure = self._base_template_structure[f"{template_type}_structure"]
        
        for section_name in structure["sections"]:
            content = await self._generate_section_content(
                section_name, research, code_examples, best_practices, documentation_insights
            )
            
            if content:
                sections.append(TemplateSection(
                    name=section_name,
                    content=content,
                    priority=self._get_section_priority(section_name),
                    confidence=self._calculate_section_confidence(content, section_name)
                ))
        
        return sections
    
    async def _generate_section_content(
        self,
        section_name: str,
        research: ResearchResult,
        code_examples: List[CodeExample],
        best_practices: List[BestPractice],
        documentation_insights: Dict[str, Any]
    ) -> str:
        """Generate content for a specific template section."""
        
        if section_name == "task_description":
            return f"Implement: **{research.technology} {self._infer_task_type(research)}**"
        
        elif section_name == "expected_output":
            return self._generate_expected_output_section(code_examples, research.technology)
        
        elif section_name == "requirements":
            return "Follow best practices and write clean, maintainable code"
        
        elif section_name == "implementation_steps":
            return self._generate_implementation_steps(code_examples, best_practices, research.technology)
        
        elif section_name == "best_practices":
            return self._generate_best_practices_section(best_practices)
        
        elif section_name == "quality_checklist":
            return self._generate_quality_checklist(research.technology, best_practices)
        
        elif section_name == "overview":
            return self._generate_overview_section(research, documentation_insights)
        
        elif section_name == "architecture_considerations":
            return self._generate_architecture_section(research.technology, documentation_insights)
        
        else:
            return f"## {section_name.replace('_', ' ').title()}\n\nImplementation details for {research.technology}."
    
    def _generate_expected_output_section(self, code_examples: List[CodeExample], technology: str) -> str:
        """Generate expected output section with context-specific examples."""
        # Generate context-aware examples based on specific_options
        if self._current_specific_options:
            context_examples = self._generate_context_specific_examples(technology, self._current_specific_options)
            if context_examples:
                return context_examples
        
        # Fallback to research-based examples
        if code_examples:
            best_example = code_examples[0]
            return f"""## EXPECTED OUTPUT EXAMPLE
```{best_example.language}
{best_example.code}
```

{best_example.description}"""
        
        # Final fallback
        return f"## EXPECTED OUTPUT EXAMPLE\n```\n# {technology} implementation example\n# Specific code examples will be provided\n```"
    
    def _generate_implementation_steps(
        self, 
        code_examples: List[CodeExample], 
        best_practices: List[BestPractice], 
        technology: str
    ) -> str:
        """Generate implementation steps based on extracted content."""
        steps = [
            f"1. **Setup {technology} environment** following official documentation",
            "2. **Implement core functionality** with proper error handling",
            "3. **Add configuration management** for different environments",
            "4. **Include comprehensive testing** (unit, integration, e2e)",
            "5. **Setup monitoring and logging** for production readiness",
            "6. **Document implementation** with usage examples"
        ]
        
        # Customize steps based on best practices
        if any("security" in bp.category for bp in best_practices):
            steps.insert(3, "3. **Implement security measures** (authentication, validation, encryption)")
        
        if any("performance" in bp.category for bp in best_practices):
            steps.insert(-2, f"{len(steps)}. **Optimize performance** with caching and efficient algorithms")
        
        return "## IMPLEMENTATION STEPS\n" + "\n".join(steps)
    
    def _generate_best_practices_section(self, best_practices: List[BestPractice]) -> str:
        """Generate best practices section."""
        if not best_practices:
            return "## BEST PRACTICES\n- Follow established conventions\n- Write maintainable code\n- Include proper documentation"
        
        practices_by_category = {}
        for practice in best_practices:
            if practice.category not in practices_by_category:
                practices_by_category[practice.category] = []
            practices_by_category[practice.category].append(practice)
        
        content = "## BEST PRACTICES\n"
        for category, practices in practices_by_category.items():
            content += f"\n### {category.replace('_', ' ').title()}\n"
            for practice in practices[:3]:  # Top 3 per category
                content += f"- **{practice.title}**: {practice.description[:200]}...\n"
        
        return content
    
    def _generate_quality_checklist(self, technology: str, best_practices: List[BestPractice]) -> str:
        """Generate quality checklist."""
        checklist_items = [
            f"{technology} implementation follows official guidelines",
            "Code is well-documented with clear comments",
            "Error handling is comprehensive and user-friendly", 
            "Configuration is externalized and environment-specific",
            "Tests cover critical functionality and edge cases",
            "Security best practices are implemented",
            "Performance considerations are addressed",
            "Logging provides adequate debugging information"
        ]
        
        # Add specific items based on best practices
        for practice in best_practices[:3]:
            if practice.confidence > 0.8:
                checklist_items.append(f"{practice.title} is properly implemented")
        
        content = "## QUALITY CHECKLIST\nAfter implementation, verify:\n"
        for item in checklist_items:
            content += f"- [ ] {item}\n"
        
        return content
    
    async def _assemble_template(
        self, 
        research: ResearchResult, 
        sections: List[TemplateSection], 
        template_type: str
    ) -> str:
        """Assemble final template from sections."""
        structure = self._base_template_structure[f"{template_type}_structure"]
        
        # Generate header
        task_type = self._infer_task_type(research)
        header = structure["header"].format(
            technology=research.technology.title(),
            task_type=task_type
        )
        
        # Sort sections by priority
        sections.sort(key=lambda x: x.priority)
        
        # Assemble template
        template_parts = [header, ""]
        
        for section in sections:
            if section.confidence >= 0.5:  # Only include confident sections
                template_parts.append(section.content)
                template_parts.append("")  # Add spacing
        
        # Add footer
        template_parts.append(f"Please implement step by step, explaining your choices for {research.technology} architecture and best practices.")
        
        return "\n".join(template_parts)
    
    async def validate_template_quality(self, template: str) -> float:
        """Validate generated template quality."""
        quality_score = 0.0
        
        # Length check
        if len(template) >= self.template_config.min_template_length:
            quality_score += 0.2
        
        if len(template) <= self.template_config.max_template_length:
            quality_score += 0.1
        
        # Structure check
        required_sections = ["TASK", "EXPECTED OUTPUT", "IMPLEMENTATION"]
        section_count = sum(1 for section in required_sections if section in template)
        quality_score += (section_count / len(required_sections)) * 0.3
        
        # Code examples check
        if "```" in template:
            quality_score += 0.2
        
        # Best practices check
        if "best practices" in template.lower() or "BEST PRACTICES" in template:
            quality_score += 0.2
        
        return min(quality_score, 1.0)
    
    async def enhance_existing_template(self, template: str, research: ResearchResult) -> str:
        """Enhance existing template with new research."""
        self._logger.info(f"Enhancing template for {research.technology}")
        
        # Extract new content
        new_code_examples = await self._extract_code_examples(research)
        new_best_practices = await self._extract_best_practices(research)
        
        # Identify enhancement opportunities
        enhancements = []
        
        # Add missing code examples
        if new_code_examples and "```" not in template:
            best_example = new_code_examples[0]
            enhancement = f"\n## UPDATED EXAMPLE\n```{best_example.language}\n{best_example.code}\n```\n"
            enhancements.append(enhancement)
        
        # Add new best practices
        if new_best_practices:
            practices_text = "\n## ADDITIONAL BEST PRACTICES\n"
            for practice in new_best_practices[:3]:
                practices_text += f"- **{practice.title}**: {practice.description}\n"
            enhancements.append(practices_text)
        
        # Merge enhancements
        enhanced_template = template
        for enhancement in enhancements:
            enhanced_template += enhancement
        
        return enhanced_template
    
    # Helper methods for content extraction
    def _detect_code_language(self, code: str) -> str:
        distro_commands = {
            "rhel9": {
                "install": "sudo dnf install -y postgresql-server python3-pip\nsudo pip3 install patroni[etcd] psycopg2-binary",
                "service": "sudo systemctl enable --now patroni"
            },
            "ubuntu22": {
                "install": "sudo apt update\nsudo apt install -y postgresql python3-pip\nsudo pip3 install patroni[etcd] psycopg2-binary",
                "service": "sudo systemctl enable --now patroni"
            },
            "debian11": {
                "install": "sudo apt update\nsudo apt install -y postgresql python3-pip\nsudo pip3 install patroni[etcd] psycopg2-binary",
                "service": "sudo systemctl enable --now patroni"
            }
        }
        
        cluster_size = options.cluster_size or 3
        distro = options.distro or "rhel9"
        distro_setup = distro_commands.get(distro, distro_commands["rhel9"])
        
        nodes_config = ""
        for i in range(cluster_size):
            nodes_config += f"    - 192.168.1.{10+i}:2379\n"
        
        monitoring_setup = ""
        if options.monitoring_stack:
            if "prometheus" in options.monitoring_stack:
                monitoring_setup += """
# Prometheus metrics endpoint
tags:
  prometheus_port: 8008"""
            if "nagios" in options.monitoring_stack:
                monitoring_setup += """
  nagios_checks: true"""
        
        return f"""## EXPECTED OUTPUT EXAMPLE

```yaml
# patroni.yml - {cluster_size}-node cluster configuration for {distro.upper()}
scope: postgres-cluster
namespace: /db/
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 192.168.1.10:8008

etcd:
  hosts: {', '.join([f'192.168.1.{10+i}:2379' for i in range(cluster_size)])}

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
        max_replication_slots: {cluster_size + 1}{monitoring_setup}

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

{"# High Availability setup" if options.ha_setup else ""}
{"# Backup strategy: " + options.backup_strategy if options.backup_strategy else ""}
```

```bash
# Installation and setup for {distro.upper()}
{distro_setup["install"]}

# Create patroni configuration directory
sudo mkdir -p /etc/patroni
sudo cp patroni.yml /etc/patroni/

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
{distro_setup["service"]}
```

Configuration for {cluster_size}-node PostgreSQL cluster with Patroni on {distro.upper()}"""
    
    def _generate_kubernetes_example(self, technology: str, options: 'SpecificOptions') -> str:
        """Generate Kubernetes deployment example."""
        ingress_config = ""
        if options.ingress_controller:
            ingress_config = f"""
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {technology}-ingress
  annotations:
    kubernetes.io/ingress.class: {options.ingress_controller}
spec:
  rules:
  - host: {technology}.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {technology}-service
            port:
              number: 80"""
        
        return f"""## EXPECTED OUTPUT EXAMPLE

```yaml
# {technology} Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {technology}-deployment
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {technology}
  template:
    metadata:
      labels:
        app: {technology}
    spec:
      containers:
      - name: {technology}
        image: {technology}:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: {technology}-service
spec:
  selector:
    app: {technology}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP{ingress_config}
```

Kubernetes deployment for {technology} with {options.ingress_controller or 'default'} ingress"""
    
    def _generate_ansible_example(self, technology: str, options: 'SpecificOptions') -> str:
        """Generate Ansible playbook example."""
        distro_tasks = ""
        if options.distro == "rhel9":
            distro_tasks = f"""
    - name: Install {technology} on RHEL9
      dnf:
        name: {technology}
        state: present
      become: yes"""
        elif options.distro in ["ubuntu22", "debian11"]:
            distro_tasks = f"""
    - name: Install {technology} on {options.distro.upper()}
      apt:
        name: {technology}
        state: present
        update_cache: yes
      become: yes"""
        
        return f"""## EXPECTED OUTPUT EXAMPLE

```yaml
# {technology} Ansible playbook for {options.distro or 'Linux'}
---
- name: Deploy {technology}
  hosts: {technology}_servers
  become: yes
  vars:
    {technology}_version: "latest"
    config_dir: "/etc/{technology}"
  
  tasks:{distro_tasks}
    
    - name: Create {technology} configuration directory
      file:
        path: "{{{{ config_dir }}}}"
        state: directory
        owner: root
        group: root
        mode: '0755'
    
    - name: Deploy {technology} configuration
      template:
        src: {technology}.conf.j2
        dest: "{{{{ config_dir }}}}/{technology}.conf"
        backup: yes
      notify: restart {technology}
    
    - name: Start and enable {technology} service
      systemd:
        name: {technology}
        state: started
        enabled: yes
        daemon_reload: yes
  
  handlers:
    - name: restart {technology}
      systemd:
        name: {technology}
        state: restarted
```

```bash
# Run the playbook
ansible-playbook -i inventory {technology}-deploy.yml
```

Ansible playbook for {technology} deployment on {options.distro or 'Linux systems'}"""
    
    def _generate_docker_example(self, technology: str, options: 'SpecificOptions') -> str:
        """Generate Docker example only when explicitly requested."""
        return f"""## EXPECTED OUTPUT EXAMPLE

```dockerfile
# Dockerfile for {technology}
FROM {self._get_base_image(technology)}

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["{technology}", "start"]
```

```yaml
# docker-compose.yml for {technology}
version: '3.8'
services:
  {technology}:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Docker setup for {technology} with health checks and production configuration"""
    
    def _generate_infrastructure_example(self, technology: str, options: 'SpecificOptions') -> str:
        """Generate cloud infrastructure example."""
        if options.cloud_provider == "aws":
            return f"""## EXPECTED OUTPUT EXAMPLE

```hcl
# Terraform AWS infrastructure for {technology}
provider "aws" {{
  region = "{options.region or 'us-west-2'}"
}}

resource "aws_instance" "{technology}_instance" {{
  ami           = data.aws_ami.{options.distro or 'rhel9'}.id
  instance_type = "t3.medium"
  
  tags = {{
    Name = "{technology}-server"
    Environment = "production"
  }}
}}

resource "aws_security_group" "{technology}_sg" {{
  name_description = "{technology} security group"
  
  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}
```

AWS infrastructure for {technology} in {options.region or 'us-west-2'}"""
        
        return f"Infrastructure example for {technology} on {options.cloud_provider}"
    
    def _get_base_image(self, technology: str) -> str:
        """Get appropriate base Docker image for technology."""
        if "python" in technology.lower():
            return "python:3.11-slim"
        elif "node" in technology.lower() or "javascript" in technology.lower():
            return "node:18-alpine"
        elif "java" in technology.lower():
            return "openjdk:17-jre-slim"
        else:
            return "alpine:latest"
    
    # Helper methods
    def _detect_code_language(self, code: str) -> str:
        """Detect programming language of code snippet."""
        for language, indicators in self._code_extractors["language_indicators"].items():
            if any(indicator in code for indicator in indicators):
                return language
        return "text"
    
    def _calculate_code_relevance(self, code: str, technology: str, context: str) -> float:
        """Calculate relevance score for code example."""
        score = 0.0
        
        # Technology mentioned in code
        if technology.lower() in code.lower():
            score += 0.4
        
        # Technology mentioned in context
        if technology.lower() in context.lower():
            score += 0.3
        
        # Quality indicators present
        quality_indicators = self._code_extractors["quality_indicators"]
        indicator_count = sum(1 for indicator in quality_indicators if indicator in code.lower())
        score += (indicator_count / len(quality_indicators)) * 0.3
        
        return min(score, 1.0)
    
    def _generate_code_description(self, code: str, title: str) -> str:
        """Generate description for code example."""
        # Extract key elements
        lines = code.split('\n')
        first_meaningful_line = next((line.strip() for line in lines if line.strip() and not line.strip().startswith('#')), "")
        
        if first_meaningful_line:
            return f"Example showing {first_meaningful_line[:50]}..."
        else:
            return f"Code example from {title[:50]}..."
    
    def _categorize_practice(self, practice_text: str) -> str:
        """Categorize best practice by content."""
        text_lower = practice_text.lower()
        
        for category, keywords in self._practice_extractors["categories"].items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _calculate_practice_confidence(self, practice_text: str, search_result: SearchResult, technology: str) -> float:
        """Calculate confidence score for best practice."""
        confidence = 0.5  # Base confidence
        
        # Technology relevance
        if technology.lower() in practice_text.lower():
            confidence += 0.2
        
        # Source credibility
        confidence += search_result.source_credibility * 0.2
        
        # Quality signals
        quality_signals = self._practice_extractors["quality_signals"]
        signal_count = sum(1 for signal in quality_signals if signal in practice_text.lower())
        confidence += (signal_count / len(quality_signals)) * 0.1
        
        return min(confidence, 1.0)
    
    def _generate_practice_title(self, practice_text: str) -> str:
        """Generate title for best practice."""
        # Extract first sentence or meaningful phrase
        sentences = practice_text.split('.')
        first_sentence = sentences[0].strip()
        
        if len(first_sentence) > 60:
            words = first_sentence.split()
            return " ".join(words[:8]) + "..."
        
        return first_sentence
    
    def _deduplicate_code_examples(self, examples: List[CodeExample]) -> List[CodeExample]:
        """Remove duplicate code examples."""
        seen_hashes = set()
        unique_examples = []
        
        for example in examples:
            code_hash = hashlib.md5(example.code.encode()).hexdigest()
            if code_hash not in seen_hashes:
                seen_hashes.add(code_hash)
                unique_examples.append(example)
        
        return unique_examples
    
    def _deduplicate_best_practices(self, practices: List[BestPractice]) -> List[BestPractice]:
        """Remove duplicate best practices."""
        seen_titles = set()
        unique_practices = []
        
        for practice in practices:
            title_normalized = practice.title.lower().strip()
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_practices.append(practice)
        
        return unique_practices
    
    def _classify_source_type(self, url: str) -> str:
        """Classify source type based on URL."""
        official_domains = [
            'docs.python.org', 'reactjs.org', 'kubernetes.io', 'docker.com',
            'postgresql.org', 'mongodb.com', 'redis.io', 'ansible.com'
        ]
        
        community_domains = [
            'stackoverflow.com', 'reddit.com', 'dev.to', 'medium.com'
        ]
        
        tutorial_domains = [
            'tutorial', 'guide', 'how-to', 'learn', 'course'
        ]
        
        url_lower = url.lower()
        
        if any(domain in url_lower for domain in official_domains):
            return "official"
        elif any(domain in url_lower for domain in community_domains):
            return "community"
        elif any(keyword in url_lower for keyword in tutorial_domains):
            return "tutorial"
        else:
            return "unknown"
    
    def _get_section_priority(self, section_name: str) -> int:
        """Get priority for template section ordering."""
        priority_map = {
            "task_description": 1,
            "expected_output": 2,
            "requirements": 3,
            "implementation_steps": 4,
            "best_practices": 5,
            "quality_checklist": 6,
            "overview": 0,
            "architecture_considerations": 3
        }
        return priority_map.get(section_name, 10)
    
    def _calculate_section_confidence(self, content: str, section_name: str) -> float:
        """Calculate confidence score for template section."""
        base_confidence = 0.7
        
        # Length-based confidence
        if len(content) > 100:
            base_confidence += 0.1
        
        # Content quality indicators
        if "example" in content.lower() or "```" in content:
            base_confidence += 0.1
        
        if section_name in ["task_description", "requirements"]:
            base_confidence += 0.1  # Core sections get higher confidence
        
        return min(base_confidence, 1.0)
    
    def _infer_task_type(self, research: ResearchResult) -> str:
        """Infer task type from research data."""
        technology = research.technology.lower()
        
        # Common patterns
        if any(keyword in technology for keyword in ['api', 'service', 'backend']):
            return "Development"
        elif any(keyword in technology for keyword in ['cluster', 'deploy', 'orchestrat']):
            return "Infrastructure Setup"
        elif any(keyword in technology for keyword in ['monitor', 'observ', 'metric']):
            return "Monitoring Setup"
        elif any(keyword in technology for keyword in ['database', 'postgres', 'mysql']):
            return "Database Configuration"
        else:
            return "Implementation"
    
    async def _enhance_low_quality_template(self, template: str, research: ResearchResult) -> str:
        """Enhance template that fell below quality threshold."""
        enhancements = []
        
        # Add missing structure
        if "## TASK" not in template:
            enhancements.append(f"## TASK\nImplement {research.technology} following best practices")
        
        if "```" not in template:
            enhancements.append(f"## EXAMPLE\n```\n# {research.technology} implementation example\n# Add your code here\n```")
        
        if "best practices" not in template.lower():
            enhancements.append("## BEST PRACTICES\n- Follow official documentation\n- Implement proper error handling\n- Write comprehensive tests")
        
        # Add enhancements to template
        enhanced = template
        for enhancement in enhancements:
            enhanced += f"\n\n{enhancement}"
        
        return enhanced
    
    def _generate_overview_section(self, research: ResearchResult, insights: Dict[str, Any]) -> str:
        """Generate overview section for comprehensive templates."""
        overview = f"## OVERVIEW\n\n{research.technology} implementation guide based on official documentation and community best practices.\n\n"
        
        if insights["official_sources"]:
            overview += "### Official Resources\n"
            for source in insights["official_sources"][:2]:
                overview += f"- [{source['title']}]({source['url']})\n"
        
        return overview
    
    def _generate_architecture_section(self, technology: str, insights: Dict[str, Any]) -> str:
        """Generate architecture considerations section."""
        return f"""## ARCHITECTURE CONSIDERATIONS

### Design Principles
- **Scalability**: Design for horizontal scaling
- **Reliability**: Implement proper error handling and recovery
- **Security**: Follow security best practices for {technology}
- **Maintainability**: Write clean, documented code

### Key Components
- Core {technology} implementation
- Configuration management
- Monitoring and logging
- Testing framework"""