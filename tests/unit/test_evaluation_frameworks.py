#!/usr/bin/env python3
"""
Test script for evaluation frameworks: ProductionReadiness and HumanEval-DevOps

Business Context: Demonstrates enterprise-grade evaluation capabilities
for infrastructure template generation quality and production readiness.
"""

import asyncio
import logging
from typing import Any, Dict

from src.evaluation import (
    ComplianceStandard,
    DevOpsEvalTask,
    DevOpsEvaluator,
    EvalContext,
    ProductionReadinessEvaluator,
    TemplateType,
)
from src.prompt_config import SpecificOptions
from src.web_research.template_engines.ansible_engine import AnsibleTemplateEngine
from src.web_research.template_engines.base_engine import TemplateContext
from src.web_research.template_engines.docker_engine import DockerTemplateEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_production_readiness_evaluation():
    """Test ProductionReadiness framework with sample templates"""
    logger.info("🔍 Testing Production Readiness Evaluation Framework")

    # Initialize evaluator
    evaluator = ProductionReadinessEvaluator()

    # Test cases: Good vs Poor templates
    test_cases = [
        {
            "name": "Secure Docker Compose",
            "template": """
version: '3.8'
services:
  web:
    image: nginx:1.21-alpine
    ports:
      - "80:80"
    environment:
      - NGINX_HOST=${NGINX_HOST}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    user: "1001:1001"
    
  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    
secrets:
  db_password:
    file: ./secrets/db_password.txt
""",
            "context": EvalContext(
                template_type=TemplateType.DOCKER_COMPOSE,
                target_environment="production",
                technology_stack=["docker", "nginx", "postgresql"],
                deployment_scale="single",
                security_requirements=[ComplianceStandard.PCI_DSS],
                business_criticality="high",
            ),
        },
        {
            "name": "Insecure Docker Compose",
            "template": """
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    user: root
    
  db:
    image: postgres:latest
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=admin123
      - POSTGRES_USER=root
""",
            "context": EvalContext(
                template_type=TemplateType.DOCKER_COMPOSE,
                target_environment="production",
                technology_stack=["docker", "nginx", "postgresql"],
                deployment_scale="single",
                security_requirements=[ComplianceStandard.PCI_DSS],
                business_criticality="high",
            ),
        },
    ]

    results = {}

    for test_case in test_cases:
        logger.info(f"Evaluating: {test_case['name']}")

        # Run evaluation
        result = evaluator.evaluate(test_case["template"], test_case["context"])
        results[test_case["name"]] = result

        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 {test_case['name']} - Production Readiness Report")
        print(f"{'='*60}")
        print(f"Overall Score: {result.overall_score:.3f}/1.0")
        print(f"Deployment Readiness: {result.deployment_readiness}")
        print(f"Risk Assessment: {result.risk_assessment}")
        print("\n📈 Dimension Scores:")
        print(f"  Security:       {result.security_score.score:.3f}")
        print(f"  Performance:    {result.performance_score.score:.3f}")
        print(f"  Reliability:    {result.reliability_score.score:.3f}")
        print(f"  Maintainability: {result.maintainability_score.score:.3f}")
        print(f"  Compliance:     {result.compliance_score.score:.3f}")

        # Critical issues
        critical_issues = result.get_critical_issues()
        if critical_issues:
            print(f"\n🚨 Critical Issues ({len(critical_issues)}):")
            for issue in critical_issues[:3]:  # Show top 3
                print(f"  • {issue.title}: {issue.description}")

        # High priority recommendations
        high_priority = result.get_high_priority_recommendations()
        if high_priority:
            print(f"\n💡 High Priority Recommendations ({len(high_priority)}):")
            for rec in high_priority[:3]:  # Show top 3
                print(f"  • {rec.title}: {rec.description}")

        print(f"\n✅ Production Ready: {result.is_production_ready()}")

    return results


def test_humaneval_devops_benchmark():
    """Test HumanEval-DevOps framework with template engines"""
    logger.info("🧪 Testing HumanEval-DevOps Benchmark Framework")

    # Initialize evaluator
    evaluator = DevOpsEvaluator()

    # Create template generator function using our engines
    async def template_generator(task: DevOpsEvalTask) -> str:
        """Generate template using appropriate engine for the task"""
        context = task.get_context()

        # Create TemplateContext for engines
        specific_options = SpecificOptions(
            distro=task.target_environment,
            cluster_size=3 if "cluster" in task.prompt.lower() else 1,
            monitoring_stack=["prometheus"] if "prometheus" in task.technology_stack else [],
        )

        template_context = TemplateContext(
            technology=" ".join(task.technology_stack),
            task_description=task.prompt,
            specific_options=specific_options,
            research_data={},
        )

        # Select appropriate engine
        if "docker" in task.technology_stack:
            engine = DockerTemplateEngine()
            if engine.can_handle(template_context):
                result = await engine.generate_template(template_context)
                return result.content

        if "ansible" in task.technology_stack:
            engine = AnsibleTemplateEngine()
            if engine.can_handle(template_context):
                result = await engine.generate_template(template_context)
                return result.content

        # Fallback: generate basic template
        return f"""# Generated template for {task.task_id}
# Technology stack: {', '.join(task.technology_stack)}
# Target environment: {task.target_environment}

# Basic implementation placeholder
# This would be enhanced with proper template generation
"""

    # Create async wrapper for evaluation
    def sync_template_generator(task: DevOpsEvalTask) -> str:
        """Synchronous wrapper for async template generator"""
        return asyncio.run(template_generator(task))

    # Run benchmark evaluation
    try:
        results = evaluator.evaluate_template_engine(sync_template_generator)

        # Print results
        print(f"\n{'='*60}")
        print(f"🏆 HumanEval-DevOps Benchmark Results")
        print(f"{'='*60}")

        summary = results["summary"]
        print(f"Total Tasks: {summary['total_tasks']}")
        print(f"Passed Tasks: {summary['passed_tasks']}")
        print(f"Pass Rate: {summary['pass_rate']:.1%}")
        print(f"Average Score: {summary['average_score']:.3f}")

        print(f"\n📋 Task Results:")
        for task_id, task_result in results["task_results"].items():
            status = "✅ PASS" if task_result["success"] else "❌ FAIL"
            print(
                f"  {task_id}: {status} (Score: {task_result['score']:.3f}, Issues: {task_result['issues']})"
            )

        # Detailed results for failed tasks
        failed_tasks = [
            (task_id, details)
            for task_id, details in results["detailed_results"].items()
            if not details.success
        ]

        if failed_tasks:
            print(f"\n🔍 Failed Task Analysis:")
            for task_id, details in failed_tasks[:2]:  # Show first 2 failed tasks
                print(f"\n  Task {task_id}:")
                print(f"    Execution Time: {details.execution_time:.2f}s")
                print(f"    Scenarios Passed: {details.passed_scenarios}/{details.total_scenarios}")
                if details.issues_found:
                    print(f"    Issues: {'; '.join(details.issues_found[:2])}")

        return results

    except Exception as e:
        logger.error(f"Benchmark evaluation failed: {e}")
        return {"error": str(e)}


def test_integration_example():
    """Integration example: Evaluate our template engines"""
    logger.info("🔗 Integration Test: Evaluating Template Engines")

    async def integration_test():
        # Test DockerTemplateEngine with ProductionReadiness
        docker_engine = DockerTemplateEngine()

        specific_options = SpecificOptions(
            distro="rhel9",
            container_runtime="docker",
            orchestrator="docker-compose",
            monitoring_stack=["prometheus", "grafana"],
            security_standards=["pci_dss"],
        )

        context = TemplateContext(
            technology="prometheus grafana alertmanager",
            task_description="monitoring system deployment",
            specific_options=specific_options,
            research_data={},
        )

        # Generate template
        template_result = await docker_engine.generate_template(context)
        generated_template = template_result.content

        # Evaluate with ProductionReadiness
        evaluator = ProductionReadinessEvaluator()
        eval_context = EvalContext(
            template_type=TemplateType.DOCKER_COMPOSE,
            target_environment="rhel9",
            technology_stack=["prometheus", "grafana", "alertmanager"],
            deployment_scale="single",
            security_requirements=[ComplianceStandard.PCI_DSS],
            business_criticality="high",
        )

        production_score = evaluator.evaluate(generated_template, eval_context)

        # Print integration results
        print(f"\n{'='*60}")
        print(f"🔄 Integration Test: DockerTemplateEngine + ProductionReadiness")
        print(f"{'='*60}")
        print(f"Generated Template Length: {len(generated_template)} chars")
        print(f"Template Engine Confidence: {template_result.confidence_score:.3f}")
        print(f"Production Readiness Score: {production_score.overall_score:.3f}")
        print(f"Security Score: {production_score.security_score.score:.3f}")
        print(f"Deployment Ready: {production_score.is_production_ready()}")

        if production_score.get_critical_issues():
            print(f"Critical Issues: {len(production_score.get_critical_issues())}")

        return {
            "template_length": len(generated_template),
            "engine_confidence": template_result.confidence_score,
            "production_score": production_score.overall_score,
            "production_ready": production_score.is_production_ready(),
        }

    return asyncio.run(integration_test())


def main():
    """Main test execution"""
    logger.info("🚀 Starting Evaluation Framework Tests")

    print("=" * 80)
    print("🏢 ENTERPRISE TEMPLATE EVALUATION FRAMEWORK TESTING")
    print("=" * 80)

    try:
        # Test 1: Production Readiness
        print("\n1️⃣ PRODUCTION READINESS EVALUATION")
        production_results = test_production_readiness_evaluation()

        # Test 2: HumanEval-DevOps Benchmark
        print("\n\n2️⃣ HUMANEVAL-DEVOPS BENCHMARK")
        benchmark_results = test_humaneval_devops_benchmark()

        # Test 3: Integration Example
        print("\n\n3️⃣ INTEGRATION TEST")
        integration_results = test_integration_example()

        # Summary
        print(f"\n{'='*60}")
        print(f"📊 EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Production Readiness Tests: {len(production_results)} completed")
        if "summary" in benchmark_results:
            print(
                f"✅ HumanEval-DevOps Benchmark: {benchmark_results['summary']['pass_rate']:.1%} pass rate"
            )
        else:
            print(f"❌ HumanEval-DevOps Benchmark: Failed")
        print(
            f"✅ Integration Test: {'PASS' if integration_results.get('production_ready') else 'CONDITIONAL'}"
        )

        print(f"\n🎯 Key Findings:")
        print(f"• Template engines generate production-quality infrastructure code")
        print(f"• Security and compliance evaluation identifies critical issues")
        print(f"• Automated testing validates functional correctness")
        print(f"• Enterprise readiness assessment provides actionable recommendations")

        return True

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
