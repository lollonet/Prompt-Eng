"""
Common types and enums for evaluation framework.

Business Context: Shared data structures and enums used across
different evaluation modules for consistency and type safety.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(Enum):
    """Risk levels for security and compliance issues"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceStandard(Enum):
    """Supported compliance standards"""

    SOX = "sox"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    ISO27001 = "iso27001"
    FIPS140_2 = "fips140_2"


class TemplateType(Enum):
    """Types of infrastructure templates"""

    DOCKER_COMPOSE = "docker_compose"
    ANSIBLE_PLAYBOOK = "ansible_playbook"
    KUBERNETES_MANIFEST = "kubernetes_manifest"
    TERRAFORM = "terraform"
    SHELL_SCRIPT = "shell_script"


@dataclass
class EvalContext:
    """Context for template evaluation"""

    template_type: TemplateType
    target_environment: str  # rhel9, ubuntu22, k8s-1.28, etc.
    technology_stack: List[str]
    deployment_scale: str  # single, cluster, enterprise
    security_requirements: List[ComplianceStandard] = field(default_factory=list)
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    business_criticality: str = "medium"  # low, medium, high, critical


@dataclass
class Issue:
    """Represents an issue found during evaluation"""

    category: str
    severity: RiskLevel
    title: str
    description: str
    location: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    cvss_score: Optional[float] = None  # Common Vulnerability Scoring System


@dataclass
class Recommendation:
    """Improvement recommendation"""

    category: str
    priority: str  # immediate, high, medium, low
    title: str
    description: str
    implementation_effort: str  # low, medium, high
    impact: str  # low, medium, high
    code_example: Optional[str] = None


@dataclass
class EvaluationMetrics:
    """Common evaluation metrics"""

    score: float  # 0.0 - 1.0
    max_score: float = 1.0
    issues: List[Issue] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Base class for all evaluation results"""

    overall_score: float
    evaluation_time: datetime
    context: EvalContext
    metrics: Dict[str, EvaluationMetrics]
    summary: str

    def get_critical_issues(self) -> List[Issue]:
        """Get all critical issues across all metrics"""
        critical_issues = []
        for metric in self.metrics.values():
            critical_issues.extend(
                [issue for issue in metric.issues if issue.severity == RiskLevel.CRITICAL]
            )
        return critical_issues

    def get_high_priority_recommendations(self) -> List[Recommendation]:
        """Get high priority recommendations"""
        high_priority = []
        for metric in self.metrics.values():
            high_priority.extend(
                [rec for rec in metric.recommendations if rec.priority in ["immediate", "high"]]
            )
        return high_priority

    def is_production_ready(self, threshold: float = 0.7) -> bool:
        """Determine if template meets production readiness threshold"""
        return self.overall_score >= threshold and len(self.get_critical_issues()) == 0
