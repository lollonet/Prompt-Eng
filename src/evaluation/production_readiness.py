"""
Production Readiness Evaluation Framework

Business Context: Comprehensive assessment of infrastructure templates
for enterprise production deployment across security, performance,
reliability, maintainability, and compliance dimensions.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .evaluation_types import (
    ComplianceStandard,
    EvalContext,
    EvaluationMetrics,
    EvaluationResult,
    Issue,
    Recommendation,
    RiskLevel,
    TemplateType,
)


@dataclass
class SecurityScore(EvaluationMetrics):
    """Security evaluation results"""

    secrets_exposure_score: float = 0.0
    privilege_escalation_score: float = 0.0
    network_security_score: float = 0.0
    image_security_score: float = 0.0
    access_controls_score: float = 0.0
    encryption_score: float = 0.0


@dataclass
class PerformanceScore(EvaluationMetrics):
    """Performance evaluation results"""

    resource_efficiency_score: float = 0.0
    scalability_score: float = 0.0
    optimization_score: float = 0.0
    monitoring_coverage_score: float = 0.0


@dataclass
class ReliabilityScore(EvaluationMetrics):
    """Reliability evaluation results"""

    health_checks_score: float = 0.0
    backup_strategy_score: float = 0.0
    disaster_recovery_score: float = 0.0
    failover_score: float = 0.0
    data_persistence_score: float = 0.0


@dataclass
class MaintainabilityScore(EvaluationMetrics):
    """Maintainability evaluation results"""

    documentation_score: float = 0.0
    configuration_management_score: float = 0.0
    deployment_automation_score: float = 0.0
    monitoring_observability_score: float = 0.0
    version_control_score: float = 0.0


@dataclass
class ComplianceScore(EvaluationMetrics):
    """Compliance evaluation results"""

    standards_compliance: Dict[str, float] = field(default_factory=dict)
    audit_readiness_score: float = 0.0
    data_protection_score: float = 0.0
    access_logging_score: float = 0.0


@dataclass
class ProductionScore(EvaluationResult):
    """Overall production readiness score"""

    security_score: SecurityScore
    performance_score: PerformanceScore
    reliability_score: ReliabilityScore
    maintainability_score: MaintainabilityScore
    compliance_score: ComplianceScore

    risk_assessment: str = ""
    deployment_readiness: str = ""


class SecurityAnalyzer:
    """Security best practices analysis for infrastructure templates"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._security_patterns = self._initialize_security_patterns()

    def _initialize_security_patterns(self) -> Dict[str, Dict]:
        """Initialize security patterns and checks (≤20 lines)."""
        return {
            "secrets_patterns": {
                "hardcoded_passwords": [
                    r'password["\s]*[:=]["\s]*\w+',
                    r'passwd["\s]*[:=]["\s]*\w+',
                    r'POSTGRES_PASSWORD["\s]*[:=]["\s]*\w+',
                ],
                "api_keys": [
                    r'api[_-]?key["\s]*[:=]["\s]*[\w-]+',
                    r'secret[_-]?key["\s]*[:=]["\s]*[\w-]+',
                    r'access[_-]?token["\s]*[:=]["\s]*[\w-]+',
                ],
                "private_keys": [
                    r"-----BEGIN.*PRIVATE KEY-----",
                    r"ssh-rsa \w+",
                    r"BEGIN RSA PRIVATE KEY",
                ],
            },
            "privilege_patterns": {
                "root_usage": [
                    r"user:\s*root",
                    r"USER root",
                    r"become:\s*yes.*become_user:\s*root",
                ],
                "sudo_usage": [
                    r"sudo\s+(?!dnf|apt|yum)",
                    r"privilege.*escalation",
                    r"NOPASSWD:\s*ALL",
                ],
            },
            "network_security": {
                "exposed_ports": [
                    r'ports?:\s*-\s*["\']?\d+:\d+["\']?',
                    r"expose:\s*-\s*\d+",
                    r"--publish.*\d+:\d+",
                ],
                "insecure_protocols": [
                    r"http://(?!localhost|127\.0\.0\.1)",
                    r"ftp://",
                    r"telnet://",
                ],
            },
        }

    def analyze(self, template: str, context: EvalContext) -> SecurityScore:
        """
        Comprehensive security analysis of infrastructure template.

        Business Context: Identifies security vulnerabilities and
        misconfigurations that could compromise production deployments.
        """
        self._logger.info("Starting security analysis")

        security_checks = {
            "secrets_exposure": self._check_secrets_exposure(template),
            "privilege_escalation": self._check_privilege_escalation(template),
            "network_security": self._check_network_security(template),
            "image_security": self._check_image_security(template),
            "access_controls": self._check_access_controls(template),
            "encryption": self._check_encryption_usage(template),
        }

        issues = []
        recommendations = []

        for check_name, result in security_checks.items():
            if result["score"] < 0.7:  # Below acceptable threshold
                issues.extend(result.get("issues", []))
            recommendations.extend(result.get("recommendations", []))

        overall_score = sum(result["score"] for result in security_checks.values()) / len(
            security_checks
        )

        return SecurityScore(
            score=overall_score,
            secrets_exposure_score=security_checks["secrets_exposure"]["score"],
            privilege_escalation_score=security_checks["privilege_escalation"]["score"],
            network_security_score=security_checks["network_security"]["score"],
            image_security_score=security_checks["image_security"]["score"],
            access_controls_score=security_checks["access_controls"]["score"],
            encryption_score=security_checks["encryption"]["score"],
            issues=issues,
            recommendations=recommendations,
        )

    def _check_secrets_exposure(self, template: str) -> Dict[str, Any]:
        """Check for hardcoded secrets and credentials (≤20 lines)."""
        issues = []
        score = 1.0

        # Check for hardcoded passwords
        for pattern in self._security_patterns["secrets_patterns"]["hardcoded_passwords"]:
            matches = re.findall(pattern, template, re.IGNORECASE)
            if matches:
                issues.append(
                    Issue(
                        category="secrets",
                        severity=RiskLevel.CRITICAL,
                        title="Hardcoded Password Detected",
                        description=f"Found hardcoded password: {matches[0][:20]}...",
                        recommendation="Use environment variables or secret management systems",
                    )
                )
                score -= 0.3

        # Check for API keys
        for pattern in self._security_patterns["secrets_patterns"]["api_keys"]:
            matches = re.findall(pattern, template, re.IGNORECASE)
            if matches:
                issues.append(
                    Issue(
                        category="secrets",
                        severity=RiskLevel.HIGH,
                        title="Hardcoded API Key Detected",
                        description="API keys should be stored in secure vaults",
                        recommendation="Use HashiCorp Vault or Kubernetes Secrets",
                    )
                )
                score -= 0.2

        return {
            "score": max(0.0, score),
            "issues": issues,
            "recommendations": self._generate_secrets_recommendations(),
        }

    def _check_privilege_escalation(self, template: str) -> Dict[str, Any]:
        """Check for unnecessary privilege escalation (≤15 lines)."""
        issues = []
        score = 1.0

        # Check for root user usage
        root_matches = re.findall(r"user:\s*root|USER root", template, re.IGNORECASE)
        if root_matches:
            issues.append(
                Issue(
                    category="privileges",
                    severity=RiskLevel.HIGH,
                    title="Running as Root User",
                    description="Services should not run as root user",
                    recommendation="Create dedicated service user with minimal privileges",
                )
            )
            score -= 0.4

        return {"score": max(0.0, score), "issues": issues, "recommendations": []}

    def _check_network_security(self, template: str) -> Dict[str, Any]:
        """Check network security configurations (≤15 lines)."""
        issues = []
        score = 1.0

        # Check for exposed ports
        exposed_ports = re.findall(r'ports?:\s*-\s*["\']?(\d+):\d+["\']?', template)
        sensitive_ports = [
            "22",
            "3306",
            "5432",
            "6379",
            "27017",
        ]  # SSH, MySQL, PostgreSQL, Redis, MongoDB

        for port in exposed_ports:
            if port in sensitive_ports:
                issues.append(
                    Issue(
                        category="network",
                        severity=RiskLevel.MEDIUM,
                        title=f"Sensitive Port {port} Exposed",
                        description=f"Port {port} should be restricted to internal networks",
                        recommendation="Use firewall rules or network policies to restrict access",
                    )
                )
                score -= 0.1

        return {"score": max(0.0, score), "issues": issues, "recommendations": []}

    def _check_image_security(self, template: str) -> Dict[str, Any]:
        """Check container image security (≤15 lines)."""
        issues = []
        score = 1.0

        # Check for latest tags
        latest_tags = re.findall(r"image:\s*[\w/-]+:latest", template)
        if latest_tags:
            issues.append(
                Issue(
                    category="images",
                    severity=RiskLevel.MEDIUM,
                    title="Using 'latest' Image Tags",
                    description="Using 'latest' tags makes deployments unpredictable",
                    recommendation="Pin to specific version tags for reproducible deployments",
                )
            )
            score -= 0.2

        return {"score": max(0.0, score), "issues": issues, "recommendations": []}

    def _check_access_controls(self, template: str) -> Dict[str, Any]:
        """Check access control configurations (≤10 lines)."""
        score = 0.8  # Default moderate score
        issues = []

        # Basic access control checks
        if "securityContext" not in template and "docker" in template.lower():
            issues.append(
                Issue(
                    category="access",
                    severity=RiskLevel.MEDIUM,
                    title="Missing Security Context",
                    description="Container security context not configured",
                    recommendation="Configure securityContext with non-root user",
                )
            )
            score -= 0.2

        return {"score": max(0.0, score), "issues": issues, "recommendations": []}

    def _check_encryption_usage(self, template: str) -> Dict[str, Any]:
        """Check encryption and TLS usage (≤10 lines)."""
        score = 0.7  # Default score
        issues = []

        # Check for TLS/SSL configuration
        has_tls = any(term in template.lower() for term in ["tls", "ssl", "https", "cert"])
        if not has_tls:
            issues.append(
                Issue(
                    category="encryption",
                    severity=RiskLevel.MEDIUM,
                    title="No TLS/SSL Configuration",
                    description="No encryption configuration found",
                    recommendation="Configure TLS certificates for secure communication",
                )
            )
            score = 0.3

        return {"score": score, "issues": issues, "recommendations": []}

    def _generate_secrets_recommendations(self) -> List[Recommendation]:
        """Generate recommendations for secrets management (≤10 lines)."""
        return [
            Recommendation(
                category="secrets",
                priority="immediate",
                title="Implement Secret Management",
                description="Move all secrets to external secret management system",
                implementation_effort="medium",
                impact="high",
                code_example="Use environment variables: ${POSTGRES_PASSWORD}",
            )
        ]


class PerformanceAnalyzer:
    """Performance and efficiency analysis for infrastructure templates"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def analyze(self, template: str, context: EvalContext) -> PerformanceScore:
        """
        Analyze template for performance and efficiency.

        Business Context: Ensures generated infrastructure can handle
        production workloads efficiently with proper resource management.
        """
        self._logger.info("Starting performance analysis")

        performance_checks = {
            "resource_efficiency": self._check_resource_limits(template),
            "scalability": self._check_scaling_configs(template),
            "optimization": self._check_optimizations(template),
            "monitoring": self._check_monitoring_setup(template),
        }

        issues = []
        recommendations = []

        for check_name, result in performance_checks.items():
            if result["score"] < 0.6:
                issues.extend(result.get("issues", []))
            recommendations.extend(result.get("recommendations", []))

        overall_score = sum(result["score"] for result in performance_checks.values()) / len(
            performance_checks
        )

        return PerformanceScore(
            score=overall_score,
            resource_efficiency_score=performance_checks["resource_efficiency"]["score"],
            scalability_score=performance_checks["scalability"]["score"],
            optimization_score=performance_checks["optimization"]["score"],
            monitoring_coverage_score=performance_checks["monitoring"]["score"],
            issues=issues,
            recommendations=recommendations,
        )

    def _check_resource_limits(self, template: str) -> Dict[str, Any]:
        """Check if resource limits are configured (≤15 lines)."""
        issues = []
        score = 0.5  # Default moderate score

        # Check for memory limits
        has_memory_limits = "memory" in template.lower() and (
            "limit" in template.lower() or "mem_limit" in template.lower()
        )
        if not has_memory_limits:
            issues.append(
                Issue(
                    category="resources",
                    severity=RiskLevel.MEDIUM,
                    title="Missing Memory Limits",
                    description="No memory limits configured for services",
                    recommendation="Configure memory limits to prevent OOM issues",
                )
            )
        else:
            score += 0.3

        # Check for CPU limits
        has_cpu_limits = "cpu" in template.lower() and "limit" in template.lower()
        if has_cpu_limits:
            score += 0.2

        return {"score": score, "issues": issues, "recommendations": []}

    def _check_scaling_configs(self, template: str) -> Dict[str, Any]:
        """Check scaling and high availability configurations (≤10 lines)."""
        score = 0.6  # Default score
        issues = []

        # Check for replicas or scaling configs
        has_scaling = any(
            term in template.lower() for term in ["replicas", "scale", "cluster_size"]
        )
        if has_scaling:
            score = 0.8
        else:
            issues.append(
                Issue(
                    category="scalability",
                    severity=RiskLevel.LOW,
                    title="No Scaling Configuration",
                    description="No horizontal scaling configuration found",
                    recommendation="Configure replicas for high availability",
                )
            )

        return {"score": score, "issues": issues, "recommendations": []}

    def _check_optimizations(self, template: str) -> Dict[str, Any]:
        """Check for performance optimizations (≤10 lines)."""
        score = 0.7  # Default score
        issues = []

        # Check for caching
        has_caching = any(term in template.lower() for term in ["cache", "redis", "memcached"])
        if has_caching:
            score += 0.2

        # Check for connection pooling
        has_pooling = "pool" in template.lower()
        if has_pooling:
            score += 0.1

        return {"score": min(1.0, score), "issues": issues, "recommendations": []}

    def _check_monitoring_setup(self, template: str) -> Dict[str, Any]:
        """Check monitoring and observability setup (≤10 lines)."""
        score = 0.5  # Default score
        issues = []

        # Check for health checks
        has_health_checks = any(
            term in template.lower() for term in ["healthcheck", "health", "readiness", "liveness"]
        )
        if has_health_checks:
            score += 0.3

        # Check for metrics
        has_metrics = any(
            term in template.lower() for term in ["prometheus", "metrics", "monitoring"]
        )
        if has_metrics:
            score += 0.2

        return {"score": min(1.0, score), "issues": issues, "recommendations": []}


class ReliabilityAnalyzer:
    """Reliability and resilience analysis for infrastructure templates"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def analyze(self, template: str, context: EvalContext) -> ReliabilityScore:
        """
        Analyze template for reliability and resilience.

        Business Context: Ensures infrastructure can recover from failures
        and maintain service availability in production environments.
        """
        self._logger.info("Starting reliability analysis")

        reliability_checks = {
            "health_checks": self._check_health_monitoring(template),
            "backup_strategy": self._check_backup_configs(template),
            "disaster_recovery": self._check_dr_configs(template),
            "failover": self._check_failover_mechanisms(template),
            "data_persistence": self._check_persistence_configs(template),
        }

        issues = []
        recommendations = []

        for check_name, result in reliability_checks.items():
            if result["score"] < 0.6:
                issues.extend(result.get("issues", []))
            recommendations.extend(result.get("recommendations", []))

        overall_score = sum(result["score"] for result in reliability_checks.values()) / len(
            reliability_checks
        )

        return ReliabilityScore(
            score=overall_score,
            health_checks_score=reliability_checks["health_checks"]["score"],
            backup_strategy_score=reliability_checks["backup_strategy"]["score"],
            disaster_recovery_score=reliability_checks["disaster_recovery"]["score"],
            failover_score=reliability_checks["failover"]["score"],
            data_persistence_score=reliability_checks["data_persistence"]["score"],
            issues=issues,
            recommendations=recommendations,
        )

    def _check_health_monitoring(self, template: str) -> Dict[str, Any]:
        """Check health monitoring configurations (≤10 lines)."""
        score = 0.3  # Default low score
        issues = []

        # Check for health checks
        health_patterns = ["healthcheck", "health", "readiness", "liveness"]
        if any(pattern in template.lower() for pattern in health_patterns):
            score = 0.8
        else:
            issues.append(
                Issue(
                    category="reliability",
                    severity=RiskLevel.MEDIUM,
                    title="Missing Health Checks",
                    description="No health monitoring configured",
                    recommendation="Add health check endpoints for all services",
                )
            )

        return {"score": score, "issues": issues, "recommendations": []}

    def _check_backup_configs(self, template: str) -> Dict[str, Any]:
        """Check backup strategy configurations (≤10 lines)."""
        score = 0.4  # Default moderate-low score
        issues = []

        # Check for backup configurations
        backup_patterns = ["backup", "snapshot", "dump", "archive"]
        if any(pattern in template.lower() for pattern in backup_patterns):
            score = 0.7
        else:
            issues.append(
                Issue(
                    category="backup",
                    severity=RiskLevel.MEDIUM,
                    title="No Backup Strategy",
                    description="No backup configuration found",
                    recommendation="Implement automated backup strategy for data persistence",
                )
            )

        return {"score": score, "issues": issues, "recommendations": []}

    def _check_dr_configs(self, template: str) -> Dict[str, Any]:
        """Check disaster recovery configurations (≤10 lines)."""
        score = 0.5  # Default moderate score
        issues = []

        # Check for DR configurations
        dr_patterns = ["disaster", "recovery", "failover", "replication"]
        if any(pattern in template.lower() for pattern in dr_patterns):
            score = 0.8

        return {"score": score, "issues": issues, "recommendations": []}

    def _check_failover_mechanisms(self, template: str) -> Dict[str, Any]:
        """Check failover mechanisms (≤10 lines)."""
        score = 0.6  # Default moderate score
        issues = []

        # Check for clustering or replication
        failover_patterns = ["cluster", "replica", "standby", "slave", "secondary"]
        if any(pattern in template.lower() for pattern in failover_patterns):
            score = 0.8

        return {"score": score, "issues": issues, "recommendations": []}

    def _check_persistence_configs(self, template: str) -> Dict[str, Any]:
        """Check data persistence configurations (≤10 lines)."""
        score = 0.3  # Default low score
        issues = []

        # Check for volumes or persistent storage
        persistence_patterns = ["volume", "persistent", "storage", "mount"]
        if any(pattern in template.lower() for pattern in persistence_patterns):
            score = 0.8
        else:
            issues.append(
                Issue(
                    category="persistence",
                    severity=RiskLevel.HIGH,
                    title="No Data Persistence",
                    description="No persistent storage configured",
                    recommendation="Configure persistent volumes for stateful services",
                )
            )

        return {"score": score, "issues": issues, "recommendations": []}


class ProductionReadinessEvaluator:
    """
    Main evaluator for production readiness assessment.

    Business Context: Orchestrates comprehensive evaluation across all
    dimensions to determine enterprise production deployment readiness.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.security_analyzer = SecurityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.reliability_analyzer = ReliabilityAnalyzer()

        # Dimension weights for overall scoring
        self.dimension_weights = {
            "security": 0.3,
            "performance": 0.2,
            "reliability": 0.25,
            "maintainability": 0.15,
            "compliance": 0.1,
        }

    def evaluate(self, template: str, context: EvalContext) -> ProductionScore:
        """
        Comprehensive production readiness evaluation.

        Business Context: Provides enterprise-grade assessment of template
        suitability for production deployment with actionable recommendations.
        """
        self._logger.info(f"Starting production readiness evaluation for {context.template_type}")

        # Run all dimension analyses
        security_score = self.security_analyzer.analyze(template, context)
        performance_score = self.performance_analyzer.analyze(template, context)
        reliability_score = self.reliability_analyzer.analyze(template, context)
        maintainability_score = self._analyze_maintainability(template, context)
        compliance_score = self._analyze_compliance(template, context)

        # Calculate weighted overall score
        overall_score = (
            security_score.score * self.dimension_weights["security"]
            + performance_score.score * self.dimension_weights["performance"]
            + reliability_score.score * self.dimension_weights["reliability"]
            + maintainability_score.score * self.dimension_weights["maintainability"]
            + compliance_score.score * self.dimension_weights["compliance"]
        )

        # Aggregate all metrics
        all_metrics = {
            "security": security_score,
            "performance": performance_score,
            "reliability": reliability_score,
            "maintainability": maintainability_score,
            "compliance": compliance_score,
        }

        # Generate risk assessment and deployment readiness
        risk_assessment = self._assess_risks(all_metrics)
        deployment_readiness = self._assess_deployment_readiness(overall_score, all_metrics)

        return ProductionScore(
            overall_score=overall_score,
            evaluation_time=datetime.now(),
            context=context,
            metrics=all_metrics,
            summary=self._generate_summary(overall_score, all_metrics),
            security_score=security_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            maintainability_score=maintainability_score,
            compliance_score=compliance_score,
            risk_assessment=risk_assessment,
            deployment_readiness=deployment_readiness,
        )

    def _analyze_maintainability(self, template: str, context: EvalContext) -> MaintainabilityScore:
        """Basic maintainability analysis (≤15 lines)."""
        score = 0.7  # Default moderate score
        issues = []
        recommendations = []

        # Check for documentation
        has_comments = "#" in template or '"""' in template
        if not has_comments:
            issues.append(
                Issue(
                    category="maintainability",
                    severity=RiskLevel.LOW,
                    title="Missing Documentation",
                    description="Template lacks inline documentation",
                    recommendation="Add comments explaining configuration choices",
                )
            )
            score -= 0.2

        return MaintainabilityScore(
            score=score,
            documentation_score=0.8 if has_comments else 0.3,
            issues=issues,
            recommendations=recommendations,
        )

    def _analyze_compliance(self, template: str, context: EvalContext) -> ComplianceScore:
        """Basic compliance analysis (≤10 lines)."""
        score = 0.6  # Default moderate score
        standards_compliance = {}

        # Basic compliance checks for required standards
        for standard in context.security_requirements:
            standards_compliance[standard.value] = 0.6  # Default moderate compliance

        return ComplianceScore(score=score, standards_compliance=standards_compliance)

    def _assess_risks(self, metrics: Dict[str, EvaluationMetrics]) -> str:
        """Assess overall risk level (≤10 lines)."""
        critical_issues = sum(
            len([i for i in m.issues if i.severity == RiskLevel.CRITICAL]) for m in metrics.values()
        )
        high_issues = sum(
            len([i for i in m.issues if i.severity == RiskLevel.HIGH]) for m in metrics.values()
        )

        if critical_issues > 0:
            return "HIGH RISK: Critical security or reliability issues detected"
        elif high_issues > 2:
            return "MEDIUM RISK: Multiple high-severity issues require attention"
        else:
            return "LOW RISK: Template meets basic production standards"

    def _assess_deployment_readiness(
        self, overall_score: float, metrics: Dict[str, EvaluationMetrics]
    ) -> str:
        """Assess deployment readiness (≤10 lines)."""
        if overall_score >= 0.8:
            return "READY: Template meets enterprise production standards"
        elif overall_score >= 0.6:
            return "CONDITIONAL: Ready with recommended improvements"
        else:
            return "NOT READY: Significant issues must be resolved before deployment"

    def _generate_summary(self, overall_score: float, metrics: Dict[str, EvaluationMetrics]) -> str:
        """Generate evaluation summary (≤10 lines)."""
        total_issues = sum(len(m.issues) for m in metrics.values())
        critical_issues = sum(
            len([i for i in m.issues if i.severity == RiskLevel.CRITICAL]) for m in metrics.values()
        )

        return (
            f"Production Readiness Score: {overall_score:.2f}/1.0. "
            f"Found {total_issues} total issues ({critical_issues} critical). "
            f"Primary concerns: {self._identify_primary_concerns(metrics)}"
        )

    def _identify_primary_concerns(self, metrics: Dict[str, EvaluationMetrics]) -> str:
        """Identify primary areas of concern (≤10 lines)."""
        concerns = []

        for dimension, metric in metrics.items():
            if metric.score < 0.6:
                concerns.append(dimension)

        return ", ".join(concerns) if concerns else "none"
