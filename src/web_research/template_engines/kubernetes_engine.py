"""
Kubernetes Template Engine for container orchestration following SOLID principles.

Business Context: Generates Kubernetes manifests, Helm charts, and deployment
configurations optimized for cloud-native applications and microservices.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .base_engine import ITemplateEngine, TemplateContext, TemplateResult


@dataclass
class KubernetesConfiguration:
    """Kubernetes-specific configuration parameters."""
    api_version: str = "apps/v1"
    namespace: str = "default"
    replicas: int = 3
    image_pull_policy: str = "IfNotPresent"
    service_type: str = "ClusterIP"


class KubernetesTemplateEngine(ITemplateEngine):
    """
    Specialized template engine for Kubernetes deployments and orchestration.
    
    Business Context: Handles cloud-native applications with focus on
    scalability, resilience, and cloud deployment patterns.
    
    Why this approach: Single Responsibility - focuses only on Kubernetes
    orchestration patterns while providing production-ready manifests.
    """
    
    @property
    def engine_name(self) -> str:
        return "kubernetes"
    
    @property  
    def supported_technologies(self) -> List[str]:
        return [
            "kubernetes", "k8s", "helm", "deployment", "service", "ingress",
            "prometheus", "grafana", "postgresql", "redis", "nginx",
            "microservices", "cloud-native"
        ]
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._workload_types = self._initialize_workload_types()
        self._service_configs = self._initialize_service_configs()
    
    def _initialize_workload_types(self) -> Dict[str, Dict]:
        """Initialize Kubernetes workload configurations (≤15 lines)."""
        return {
            "deployment": {
                "api_version": "apps/v1",
                "kind": "Deployment",
                "strategy": "RollingUpdate"
            },
            "statefulset": {
                "api_version": "apps/v1", 
                "kind": "StatefulSet",
                "strategy": "RollingUpdate"
            },
            "daemonset": {
                "api_version": "apps/v1",
                "kind": "DaemonSet",
                "strategy": "RollingUpdate"
            }
        }
    
    def _initialize_service_configs(self) -> Dict[str, Dict]:
        """Initialize service configurations (≤15 lines)."""
        return {
            "prometheus": {"port": 9090, "type": "monitoring"},
            "grafana": {"port": 3000, "type": "monitoring"},
            "postgresql": {"port": 5432, "type": "database"},
            "redis": {"port": 6379, "type": "cache"},
            "nginx": {"port": 80, "type": "web"}
        }
    
    def can_handle(self, context: TemplateContext) -> bool:
        """
        Determine if this engine can handle the context.
        
        Business Context: Focuses on cloud-native deployments and
        container orchestration scenarios.
        """
        tech_lower = context.technology.lower()
        task_lower = context.task_description.lower()
        
        # Direct Kubernetes technologies
        if any(tech in tech_lower for tech in ["kubernetes", "k8s", "helm"]):
            return True
        
        # Check orchestrator preference
        orchestrator = getattr(context.specific_options, 'orchestrator', '')
        if "k8s" in orchestrator.lower() or "kubernetes" in orchestrator.lower():
            return True
        
        # Cloud deployment scenarios
        cloud_keywords = ["deploy", "orchestrate", "scale", "microservice"]
        if any(keyword in task_lower for keyword in cloud_keywords):
            cluster_size = getattr(context.specific_options, 'cluster_size', 0)
            if cluster_size and cluster_size > 3:  # Prefer K8s for larger clusters
                return True
        
        return False
    
    def estimate_complexity(self, context: TemplateContext) -> str:
        """Estimate deployment complexity based on requirements."""
        tech_count = len(context.technology.split())
        cluster_size = getattr(context.specific_options, 'cluster_size', 1)
        ha_setup = getattr(context.specific_options, 'ha_setup', False)
        
        complexity_score = tech_count + (cluster_size // 3)
        if ha_setup:
            complexity_score += 2
        
        if complexity_score >= 6:
            return "complex"
        elif complexity_score >= 3:
            return "moderate"
        else:
            return "simple"
    
    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """
        Generate Kubernetes template based on context.
        
        Business Context: Main entry point that orchestrates manifest
        generation based on deployment requirements and scaling needs.
        """
        self._logger.info(f"Generating Kubernetes template for: {context.technology}")
        
        # Parse technologies and build configuration
        technologies = self._parse_technologies(context.technology)
        k8s_config = self._build_k8s_config(context)
        
        # Generate appropriate template based on complexity
        if self.estimate_complexity(context) == "complex":
            template_content = self._generate_helm_chart(technologies, context, k8s_config)
        else:
            template_content = self._generate_manifest_template(technologies, context, k8s_config)
        
        from datetime import datetime
        import hashlib
        
        context_hash = hashlib.md5(
            f"{context.technology}_{context.task_description}_{getattr(context.specific_options, 'distro', '')}".encode()
        ).hexdigest()[:8]
        
        return TemplateResult(
            content=template_content,
            template_type="kubernetes",
            confidence_score=0.88,
            estimated_complexity=self.estimate_complexity(context),
            generated_at=datetime.now(),
            context_hash=context_hash
        )
    
    def _parse_technologies(self, tech_string: str) -> List[str]:
        """Parse and normalize technology names (≤10 lines)."""
        techs = [tech.strip().lower() for tech in tech_string.split()]
        
        # Normalize K8s variations
        normalized = []
        for tech in techs:
            if tech in ["k8s", "kube"]:
                normalized.append("kubernetes")
            elif tech in self.supported_technologies:
                normalized.append(tech)
            else:
                normalized.append(tech)
        
        return normalized
    
    def _build_k8s_config(self, context: TemplateContext) -> KubernetesConfiguration:
        """Build Kubernetes configuration from context (≤10 lines)."""
        cluster_size = getattr(context.specific_options, 'cluster_size', 3)
        
        return KubernetesConfiguration(
            api_version="apps/v1",
            namespace="default",
            replicas=min(cluster_size, 5),  # Cap at 5 replicas
            image_pull_policy="IfNotPresent",
            service_type="ClusterIP"
        )
    
    def _generate_manifest_template(
        self,
        technologies: List[str],
        context: TemplateContext,
        k8s_config: KubernetesConfiguration
    ) -> str:
        """
        Generate Kubernetes manifest template for simple deployments.
        
        Business Context: Creates focused manifests for straightforward
        cloud-native deployments with essential K8s resources.
        """
        manifests = []
        
        # Generate manifests for each technology
        for tech in technologies:
            if tech in self._service_configs:
                deployment = self._generate_deployment_manifest(tech, context, k8s_config)
                service = self._generate_service_manifest(tech, context, k8s_config)
                manifests.extend([deployment, service, "---"])
        
        # Add deployment instructions
        instructions = self._generate_deployment_instructions(context)
        
        return "\n".join([
            f"# Kubernetes Manifests for {context.technology}",
            f"# Target: {getattr(context.specific_options, 'distro', 'kubernetes')} cluster",
            "",
            *manifests,
            "",
            instructions
        ])
    
    def _generate_deployment_manifest(
        self,
        tech: str,
        context: TemplateContext,
        k8s_config: KubernetesConfiguration
    ) -> str:
        """Generate Deployment manifest for technology (≤20 lines)."""
        config = self._service_configs.get(tech, {"port": 8080, "type": "app"})
        
        return f"""apiVersion: {k8s_config.api_version}
kind: Deployment
metadata:
  name: {tech}
  namespace: {k8s_config.namespace}
  labels:
    app: {tech}
    type: {config['type']}
spec:
  replicas: {k8s_config.replicas}
  selector:
    matchLabels:
      app: {tech}
  template:
    metadata:
      labels:
        app: {tech}
    spec:
      containers:
      - name: {tech}
        image: {self._get_container_image(tech)}
        ports:
        - containerPort: {config['port']}
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: {config['port']}
          initialDelaySeconds: 10
          periodSeconds: 5"""
    
    def _generate_service_manifest(
        self,
        tech: str,
        context: TemplateContext,
        k8s_config: KubernetesConfiguration
    ) -> str:
        """Generate Service manifest for technology (≤15 lines)."""
        config = self._service_configs.get(tech, {"port": 8080, "type": "app"})
        
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {tech}-service
  namespace: {k8s_config.namespace}
  labels:
    app: {tech}
spec:
  type: {k8s_config.service_type}
  ports:
  - port: {config['port']}
    targetPort: {config['port']}
    protocol: TCP
  selector:
    app: {tech}"""
    
    def _generate_helm_chart(
        self,
        technologies: List[str],
        context: TemplateContext,
        k8s_config: KubernetesConfiguration
    ) -> str:
        """
        Generate Helm chart template for complex deployments.
        
        Business Context: Creates modular Helm charts for production
        deployments with templating and configuration management.
        """
        chart_name = f"{'-'.join(technologies[:2])}-stack"
        
        return f"""# Helm Chart: {chart_name}
# Chart.yaml
apiVersion: v2
name: {chart_name}
description: {context.task_description}
version: 0.1.0
appVersion: "1.0"

# values.yaml
global:
  namespace: {k8s_config.namespace}
  imageRegistry: ""
  imagePullPolicy: {k8s_config.image_pull_policy}

{self._generate_helm_values(technologies, context, k8s_config)}

# templates/deployment.yaml
{{{{- range $service := .Values.services }}}}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ $service.name }}}}
  namespace: {{{{ .Values.global.namespace }}}}
spec:
  replicas: {{{{ $service.replicas | default 3 }}}}
  selector:
    matchLabels:
      app: {{{{ $service.name }}}}
  template:
    metadata:
      labels:
        app: {{{{ $service.name }}}}
    spec:
      containers:
      - name: {{{{ $service.name }}}}
        image: {{{{ $service.image }}}}
        ports:
        - containerPort: {{{{ $service.port }}}}
        resources:
          {{{{- toYaml $service.resources | nindent 10 }}}}
{{{{- end }}}}

{self._generate_helm_deployment_instructions(context)}"""
    
    def _generate_helm_values(
        self,
        technologies: List[str],
        context: TemplateContext,
        k8s_config: KubernetesConfiguration
    ) -> str:
        """Generate Helm values for services (≤15 lines)."""
        services = []
        
        for tech in technologies:
            if tech in self._service_configs:
                config = self._service_configs[tech]
                services.append(f"""  {tech}:
    name: {tech}
    image: {self._get_container_image(tech)}
    port: {config['port']}
    replicas: {k8s_config.replicas}
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
""")
        
        return f"services:\n{''.join(services)}"
    
    def _get_container_image(self, tech: str) -> str:
        """Get appropriate container image for technology (≤10 lines)."""
        image_map = {
            "prometheus": "prom/prometheus:latest",
            "grafana": "grafana/grafana:latest",
            "postgresql": "postgres:14-alpine",
            "redis": "redis:7-alpine",
            "nginx": "nginx:alpine"
        }
        return image_map.get(tech, f"{tech}:latest")
    
    def _generate_deployment_instructions(self, context: TemplateContext) -> str:
        """Generate K8s deployment instructions (≤15 lines)."""
        return """## KUBERNETES DEPLOYMENT INSTRUCTIONS

```bash
# Apply manifests to cluster
kubectl apply -f manifests.yaml

# Check deployment status
kubectl get deployments
kubectl get services
kubectl get pods

# Port forward for local access (example)
kubectl port-forward service/prometheus-service 9090:9090
kubectl port-forward service/grafana-service 3000:3000

# Check logs
kubectl logs -l app=prometheus
```"""
    
    def _generate_helm_deployment_instructions(self, context: TemplateContext) -> str:
        """Generate Helm deployment instructions (≤10 lines)."""
        return """## HELM DEPLOYMENT INSTRUCTIONS

```bash
# Install Helm chart
helm install monitoring-stack ./chart

# Upgrade deployment
helm upgrade monitoring-stack ./chart

# Check status
helm status monitoring-stack
kubectl get all -l app.kubernetes.io/managed-by=Helm
```"""