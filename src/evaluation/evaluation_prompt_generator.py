"""
Evaluation Prompt Generator - Meta-framework for creating LLM evaluation prompts.

Business Context: Generates structured prompts that instruct LLMs to evaluate
other prompts based on domain-specific criteria and quality standards.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..knowledge_manager import KnowledgeManager
from ..prompt_config import PromptConfig
from .evaluation_types import ComplianceStandard, EvalContext, RiskLevel


class EvaluationDomain(Enum):
    """Evaluation domains with specific criteria."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    COMPLIANCE = "compliance"
    CODE_QUALITY = "code_quality"
    INFRASTRUCTURE = "infrastructure"
    API_DESIGN = "api_design"


@dataclass
class EvaluationCriteria:
    """Defines evaluation criteria for a specific domain."""

    domain: EvaluationDomain
    criteria: Dict[str, float]  # criterion_name: weight
    min_threshold: float = 0.6
    max_score: float = 1.0
    description: str = ""
    examples: List[str] = field(default_factory=list)


@dataclass
class EvaluationPromptResult:
    """Result of evaluation prompt generation."""

    evaluation_prompt: str
    domain: EvaluationDomain
    criteria_count: int
    confidence_score: float
    generated_at: datetime
    target_technologies: List[str]
    evaluation_instructions: str
    scoring_rubric: Dict[str, Any]


class EvaluationPromptGenerator:
    """
    Main generator for creating structured evaluation prompts.

    Business Context: Creates meta-prompts that standardize how LLMs
    evaluate content based on enterprise quality standards.
    """

    def __init__(self, knowledge_manager: KnowledgeManager):
        self.knowledge_manager = knowledge_manager
        self._logger = logging.getLogger(__name__)

        # Initialize domain-specific criteria
        self._evaluation_criteria = self._initialize_evaluation_criteria()
        self._prompt_templates = self._initialize_prompt_templates()

    def _initialize_evaluation_criteria(self) -> Dict[EvaluationDomain, EvaluationCriteria]:
        """Initialize standard evaluation criteria for each domain."""
        return {
            EvaluationDomain.SECURITY: EvaluationCriteria(
                domain=EvaluationDomain.SECURITY,
                criteria={
                    "secret_management": 0.25,
                    "privilege_escalation": 0.20,
                    "network_security": 0.15,
                    "access_controls": 0.15,
                    "encryption_usage": 0.15,
                    "vulnerability_mitigation": 0.10,
                },
                min_threshold=0.8,  # High bar for security
                description="Security best practices and vulnerability prevention",
            ),
            EvaluationDomain.PERFORMANCE: EvaluationCriteria(
                domain=EvaluationDomain.PERFORMANCE,
                criteria={
                    "resource_efficiency": 0.30,
                    "scalability_design": 0.25,
                    "optimization_techniques": 0.20,
                    "monitoring_coverage": 0.15,
                    "bottleneck_identification": 0.10,
                },
                min_threshold=0.6,
                description="Performance optimization and scalability patterns",
            ),
            EvaluationDomain.RELIABILITY: EvaluationCriteria(
                domain=EvaluationDomain.RELIABILITY,
                criteria={
                    "error_handling": 0.25,
                    "failover_mechanisms": 0.20,
                    "health_monitoring": 0.20,
                    "data_persistence": 0.15,
                    "recovery_procedures": 0.10,
                    "redundancy_design": 0.10,
                },
                min_threshold=0.7,
                description="System reliability and fault tolerance",
            ),
            EvaluationDomain.CODE_QUALITY: EvaluationCriteria(
                domain=EvaluationDomain.CODE_QUALITY,
                criteria={
                    "readability": 0.25,
                    "maintainability": 0.20,
                    "testability": 0.20,
                    "documentation": 0.15,
                    "design_patterns": 0.10,
                    "error_handling": 0.10,
                },
                min_threshold=0.6,
                description="Code quality and software engineering best practices",
            ),
            EvaluationDomain.INFRASTRUCTURE: EvaluationCriteria(
                domain=EvaluationDomain.INFRASTRUCTURE,
                criteria={
                    "deployment_automation": 0.25,
                    "configuration_management": 0.20,
                    "monitoring_setup": 0.20,
                    "security_hardening": 0.15,
                    "backup_strategy": 0.10,
                    "disaster_recovery": 0.10,
                },
                min_threshold=0.7,
                description="Infrastructure automation and operational excellence",
            ),
        }

    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """Initialize evaluation prompt templates."""
        templates = {}

        # Try to load external template files
        prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts",
            "evaluation_prompts",
        )

        # Load security template
        security_template_path = os.path.join(prompts_dir, "security_evaluation_prompt.txt")
        try:
            with open(security_template_path, "r") as f:
                templates["security_focused"] = f.read()
        except FileNotFoundError:
            self._logger.warning(
                f"Security template not found at {security_template_path}, using fallback"
            )
            templates["security_focused"] = self._get_fallback_security_template()

        # Load performance template
        performance_template_path = os.path.join(prompts_dir, "performance_evaluation_prompt.txt")
        try:
            with open(performance_template_path, "r") as f:
                templates["performance_focused"] = f.read()
        except FileNotFoundError:
            self._logger.warning(
                f"Performance template not found at {performance_template_path}, using fallback"
            )
            templates["performance_focused"] = self._get_fallback_security_template()  # Use security as fallback

        # Base evaluation template
        templates[
            "base_evaluation"
        ] = """# PROMPT EVALUATION FRAMEWORK

## EVALUATION OBJECTIVE
You are an expert evaluator specializing in {domain} assessment. Your task is to evaluate the given prompt based on enterprise-grade {domain} standards.

## EVALUATION CRITERIA
{criteria_section}

## SCORING METHODOLOGY
- Score each criterion from 0.0 to 1.0
- Provide specific evidence for each score
- Calculate weighted overall score
- Minimum acceptable threshold: {min_threshold}

## EVALUATION TARGET
**Technologies:** {technologies}
**Domain Focus:** {domain}

## PROMPT TO EVALUATE
```
{target_prompt}
```

## REQUIRED OUTPUT FORMAT
```json
{{
  "overall_score": 0.0,
  "domain": "{domain}",
  "criteria_scores": {{
    {criteria_json_template}
  }},
  "strengths": ["specific strength 1", "specific strength 2"],
  "weaknesses": ["specific weakness 1", "specific weakness 2"],
  "recommendations": ["improvement 1", "improvement 2"],
  "evidence": {{
    {evidence_json_template}
  }}
}}
```

{evaluation_instructions}"""

        return templates

    def generate_evaluation_prompt(
        self,
        target_prompt: str,
        evaluation_domain: EvaluationDomain,
        technologies: List[str],
        custom_criteria: Optional[Dict[str, float]] = None,
        compliance_standards: Optional[List[ComplianceStandard]] = None,
    ) -> EvaluationPromptResult:
        """
        Generate evaluation prompt for specific domain and technologies.

        Business Context: Creates structured evaluation prompts that ensure
        consistent quality assessment across different LLM evaluators.
        """
        self._logger.info(f"Generating evaluation prompt for domain: {evaluation_domain.value}")

        # Get domain criteria
        criteria = self._evaluation_criteria[evaluation_domain]
        if custom_criteria:
            # Merge custom criteria with defaults
            merged_criteria = criteria.criteria.copy()
            merged_criteria.update(custom_criteria)
            criteria.criteria = merged_criteria

        # Build technology-specific knowledge
        tech_knowledge = self._get_technology_evaluation_knowledge(technologies, evaluation_domain)

        # Generate criteria section
        criteria_section = self._generate_criteria_section(criteria, tech_knowledge)

        # Generate evaluation instructions
        evaluation_instructions = self._generate_evaluation_instructions(
            evaluation_domain, technologies, criteria, compliance_standards
        )

        # Generate scoring rubric
        scoring_rubric = self._generate_scoring_rubric(criteria, technologies)

        # Select appropriate template
        template_key = self._select_evaluation_template(evaluation_domain)
        template = self._prompt_templates[template_key]

        # For external templates (like security_focused, performance_focused), use as-is with target prompt appended
        if template_key in ["security_focused", "performance_focused"]:
            # External template doesn't use placeholders, append evaluation context
            evaluation_prompt = f"""{template}

## TARGET PROMPT TO EVALUATE
```
{target_prompt}
```

## EVALUATION CONTEXT
- **Technologies**: {", ".join(technologies)}
- **Domain**: {evaluation_domain.value}
- **Criteria**: {", ".join(criteria.criteria.keys())}
- **Minimum Threshold**: {criteria.min_threshold}

{evaluation_instructions}
"""
        else:
            # Format template with placeholders
            evaluation_prompt = template.format(
                domain=evaluation_domain.value,
                technologies=", ".join(technologies),
                target_prompt=target_prompt,
                criteria_section=criteria_section,
                min_threshold=criteria.min_threshold,
                criteria_json_template=self._generate_criteria_json_template(criteria),
                evidence_json_template=self._generate_evidence_json_template(criteria),
                evaluation_instructions=evaluation_instructions,
            )

        return EvaluationPromptResult(
            evaluation_prompt=evaluation_prompt,
            domain=evaluation_domain,
            criteria_count=len(criteria.criteria),
            confidence_score=0.9,  # High confidence in structured evaluation
            generated_at=datetime.now(),
            target_technologies=technologies,
            evaluation_instructions=evaluation_instructions,
            scoring_rubric=scoring_rubric,
        )

    def _get_technology_evaluation_knowledge(
        self, technologies: List[str], domain: EvaluationDomain
    ) -> Dict[str, Any]:
        """Get domain-specific knowledge for technologies."""
        knowledge = {}

        for tech in technologies:
            # Get available information using existing KnowledgeManager methods
            best_practices = self.knowledge_manager.get_best_practices(tech)
            tools = self.knowledge_manager.get_tools(tech)

            if best_practices or tools:
                # Extract domain-specific best practices
                domain_practices = []
                for practice in best_practices:
                    if domain.value.lower() in practice.lower():
                        domain_practices.append(practice)

                knowledge[tech] = {
                    "best_practices": domain_practices
                    or best_practices[:3],  # Use some practices if none domain-specific
                    "tools": tools,
                    "common_issues": [],  # Could be enhanced later
                }

        return knowledge

    def _get_fallback_security_template(self) -> str:
        """Fallback security template when external file is not available."""
        return """# ENTERPRISE SECURITY EVALUATION FRAMEWORK

## EVALUATION OBJECTIVE
You are a cybersecurity expert conducting enterprise-grade security assessment. Evaluate the provided prompt against industry-leading security standards.

## TARGET PROMPT TO EVALUATE
```
{target_prompt}
```

## SECURITY EVALUATION CRITERIA
{criteria_section}

## EVALUATION INSTRUCTIONS
Assess each security criterion and provide evidence-based scoring from 0.0 to 1.0.
Minimum threshold: {min_threshold}

Provide detailed analysis with specific examples and actionable recommendations."""

    def _generate_criteria_section(
        self, criteria: EvaluationCriteria, tech_knowledge: Dict[str, Any]
    ) -> str:
        """Generate detailed criteria section for evaluation."""
        sections = [f"### {criteria.domain.value.upper()} EVALUATION CRITERIA\n"]

        for criterion, weight in criteria.criteria.items():
            sections.append(f"**{criterion.replace('_', ' ').title()}** (Weight: {weight:.0%})")
            sections.append(f"- Evaluate {criterion.replace('_', ' ')} implementation")
            sections.append(f"- Consider enterprise best practices")

            # Add technology-specific guidance
            for tech, knowledge in tech_knowledge.items():
                relevant_practices = [
                    p
                    for p in knowledge["best_practices"]
                    if criterion.replace("_", " ") in p.lower()
                ]
                if relevant_practices:
                    sections.append(f"- {tech.title()}: {relevant_practices[0][:100]}...")

            sections.append("")

        return "\n".join(sections)

    def _generate_evaluation_instructions(
        self,
        domain: EvaluationDomain,
        technologies: List[str],
        criteria: EvaluationCriteria,
        compliance_standards: Optional[List[ComplianceStandard]],
    ) -> str:
        """Generate specific evaluation instructions."""
        instructions = [
            f"1. **Domain Focus**: Evaluate specifically for {domain.value} excellence",
            f"2. **Technology Context**: Consider {', '.join(technologies)} specific patterns",
            f"3. **Enterprise Standards**: Apply enterprise-grade {domain.value} requirements",
            f"4. **Evidence Required**: Cite specific examples from the prompt",
            f"5. **Scoring Precision**: Use the full 0.0-1.0 range with decimal precision",
        ]

        if domain == EvaluationDomain.SECURITY:
            instructions.extend(
                [
                    "6. **Threat Modeling**: Consider common attack vectors",
                    "7. **Defense Depth**: Evaluate layered security measures",
                    "8. **Compliance**: Check regulatory requirement coverage",
                ]
            )
        elif domain == EvaluationDomain.PERFORMANCE:
            instructions.extend(
                [
                    "6. **Scalability**: Assess horizontal and vertical scaling",
                    "7. **Bottlenecks**: Identify potential performance constraints",
                    "8. **Monitoring**: Evaluate observability implementation",
                ]
            )

        if compliance_standards:
            instructions.append(
                f"9. **Compliance Check**: Verify alignment with {', '.join([std.value for std in compliance_standards])}"
            )

        return "\n".join(instructions)

    def _generate_scoring_rubric(
        self, criteria: EvaluationCriteria, technologies: List[str]
    ) -> Dict[str, Any]:
        """Generate detailed scoring rubric."""
        return {
            "scoring_scale": {
                "0.9-1.0": "Excellent - Exceeds enterprise standards",
                "0.8-0.89": "Good - Meets enterprise standards",
                "0.7-0.79": "Acceptable - Minor improvements needed",
                "0.6-0.69": "Conditional - Significant improvements required",
                "0.0-0.59": "Inadequate - Major revisions required",
            },
            "weighted_calculation": "Sum of (criterion_score * weight) for all criteria",
            "min_threshold": criteria.min_threshold,
            "pass_criteria": f"Overall score >= {criteria.min_threshold} AND no criterion < 0.5",
        }

    def _select_evaluation_template(self, domain: EvaluationDomain) -> str:
        """Select appropriate template based on domain."""
        if domain == EvaluationDomain.SECURITY:
            return "security_focused"
        elif domain == EvaluationDomain.PERFORMANCE:
            return "performance_focused"
        else:
            return "base_evaluation"

    def _generate_criteria_json_template(self, criteria: EvaluationCriteria) -> str:
        """Generate JSON template for criteria scoring."""
        template_items = []
        for criterion in criteria.criteria.keys():
            template_items.append(f'"{criterion}": 0.0')
        return ",\n    ".join(template_items)

    def _generate_evidence_json_template(self, criteria: EvaluationCriteria) -> str:
        """Generate JSON template for evidence documentation."""
        template_items = []
        for criterion in criteria.criteria.keys():
            template_items.append(f'"{criterion}": "specific evidence from prompt"')
        return ",\n    ".join(template_items)


class EvaluationChainOrchestrator:
    """
    Orchestrates the complete evaluation chain workflow.

    Business Context: Manages the full cycle from evaluation prompt generation
    to result aggregation and quality reporting.
    """

    def __init__(self, evaluation_generator: EvaluationPromptGenerator):
        self.evaluation_generator = evaluation_generator
        self._logger = logging.getLogger(__name__)

    async def evaluate_prompt_chain(
        self,
        target_prompt: str,
        domains: List[EvaluationDomain],
        technologies: List[str],
        llm_evaluator_func: callable,
    ) -> Dict[str, Any]:
        """
        Execute full evaluation chain across multiple domains.

        Args:
            target_prompt: The prompt to evaluate
            domains: List of evaluation domains to assess
            technologies: Technologies involved in the prompt
            llm_evaluator_func: Function that executes LLM evaluation
        """
        self._logger.info(f"Starting evaluation chain for {len(domains)} domains")

        evaluation_results = {}

        for domain in domains:
            # Generate evaluation prompt
            eval_prompt_result = self.evaluation_generator.generate_evaluation_prompt(
                target_prompt=target_prompt, evaluation_domain=domain, technologies=technologies
            )

            # Execute LLM evaluation
            try:
                evaluation_output = await llm_evaluator_func(eval_prompt_result.evaluation_prompt)
                evaluation_results[domain.value] = {
                    "evaluation_prompt": eval_prompt_result,
                    "llm_output": evaluation_output,
                    "status": "completed",
                }
            except Exception as e:
                self._logger.error(f"Evaluation failed for domain {domain.value}: {e}")
                evaluation_results[domain.value] = {
                    "evaluation_prompt": eval_prompt_result,
                    "error": str(e),
                    "status": "failed",
                }

        # Aggregate results
        aggregated_results = self._aggregate_evaluation_results(evaluation_results)

        return {
            "target_prompt": target_prompt,
            "technologies": technologies,
            "domains_evaluated": [d.value for d in domains],
            "individual_results": evaluation_results,
            "aggregated_summary": aggregated_results,
            "evaluation_timestamp": datetime.now(),
        }

    def _aggregate_evaluation_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results across domains."""
        successful_evaluations = [r for r in results.values() if r["status"] == "completed"]

        if not successful_evaluations:
            return {"status": "all_failed", "overall_score": 0.0}

        # This would parse LLM outputs and aggregate scores
        # Implementation depends on LLM output format
        return {
            "status": "completed",
            "domains_completed": len(successful_evaluations),
            "domains_failed": len(results) - len(successful_evaluations),
            "summary": "Evaluation chain completed with domain-specific assessments",
        }
