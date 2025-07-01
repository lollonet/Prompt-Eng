#!/usr/bin/env python3
"""
Evaluation Framework Demonstration

This example shows how to use the evaluation prompt generator to create
structured prompts for evaluating other prompts across different domains.
"""

import asyncio
import json
import os
import sys

# Define paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "tech_stack_mapping.json")

# Add src to path for imports
sys.path.append(PROJECT_ROOT)

from src.knowledge_manager import KnowledgeManager
from src.evaluation.evaluation_prompt_generator import (
    EvaluationPromptGenerator, 
    EvaluationChainOrchestrator,
    EvaluationDomain
)
from src.evaluation.evaluation_types import ComplianceStandard


# Example prompt to evaluate (Docker security prompt)
EXAMPLE_DOCKER_PROMPT = """
# Docker Security Deployment

## TASK
Deploy a secure Docker application with PostgreSQL database

## IMPLEMENTATION STEPS
1. Create multi-stage Dockerfile
2. Set up Docker Compose with services
3. Configure environment variables
4. Implement health checks
5. Set up basic monitoring

## EXPECTED OUTPUT
```yaml
version: '3.8'
services:
  web:
    image: myapp:latest
    ports:
      - "80:80"
    environment:
      - DATABASE_URL=postgresql://user:password123@db:5432/myapp
    
  db:
    image: postgres:latest
    environment:
      - POSTGRES_PASSWORD=password123
    ports:
      - "5432:5432"
```

## REQUIREMENTS
- Use official Docker images
- Set up basic networking
- Include database connectivity
"""


async def mock_llm_evaluator(evaluation_prompt: str) -> dict:
    """
    Mock LLM evaluator function that simulates LLM evaluation response.
    In real implementation, this would call an actual LLM API.
    """
    # Simulate LLM processing time
    await asyncio.sleep(0.1)
    
    # Mock evaluation result based on the prompt content
    # This simulates what an LLM would return after evaluating the Docker prompt
    return {
        "overall_score": 0.4,
        "domain": "security",
        "criteria_scores": {
            "secret_management": 0.2,  # Poor - hardcoded passwords
            "privilege_escalation": 0.6,  # Moderate - no explicit user settings
            "network_security": 0.3,  # Poor - exposed ports
            "access_controls": 0.4,  # Poor - no authentication
            "encryption_usage": 0.5,  # Moderate - basic setup
            "vulnerability_mitigation": 0.3  # Poor - using latest tags
        },
        "security_strengths": [
            "Uses Docker containerization for isolation",
            "Implements basic service separation"
        ],
        "security_weaknesses": [
            "Hardcoded password 'password123' in environment variables",
            "PostgreSQL port 5432 exposed to host network",
            "Using 'latest' tags makes deployments unpredictable",
            "No non-root user configuration"
        ],
        "security_recommendations": [
            "Use Docker secrets or external secret management for passwords",
            "Remove port exposure for database service",
            "Pin specific version tags for reproducible deployments",
            "Configure non-root users for all services",
            "Add security context and capabilities dropping"
        ],
        "enterprise_readiness": "NOT_READY",
        "risk_level": "HIGH",
        "evidence": {
            "secret_management": "Found hardcoded password: POSTGRES_PASSWORD=password123",
            "network_security": "Database port 5432 exposed to host: '5432:5432'",
            "vulnerability_mitigation": "Using 'latest' tags: postgres:latest, myapp:latest"
        }
    }


async def demonstrate_security_evaluation():
    """Demonstrate security evaluation of a Docker prompt."""
    print("🔒 SECURITY EVALUATION DEMONSTRATION")
    print("=" * 60)
    
    # Initialize components
    knowledge_manager = KnowledgeManager(CONFIG_PATH)
    evaluation_generator = EvaluationPromptGenerator(knowledge_manager)
    
    # Generate security evaluation prompt
    eval_result = evaluation_generator.generate_evaluation_prompt(
        target_prompt=EXAMPLE_DOCKER_PROMPT,
        evaluation_domain=EvaluationDomain.SECURITY,
        technologies=["docker", "postgresql"],
        compliance_standards=[ComplianceStandard.SOX, ComplianceStandard.PCI_DSS]
    )
    
    print(f"📋 Generated evaluation prompt for: {eval_result.domain.value}")
    print(f"🎯 Target technologies: {', '.join(eval_result.target_technologies)}")
    print(f"📊 Evaluation criteria: {eval_result.criteria_count} criteria")
    print(f"✅ Confidence score: {eval_result.confidence_score}")
    print()
    
    # Display the generated evaluation prompt (truncated for demo)
    print("📝 GENERATED EVALUATION PROMPT (First 500 chars):")
    print("-" * 60)
    print(eval_result.evaluation_prompt[:500] + "...")
    print("-" * 60)
    print()
    
    # Simulate LLM evaluation
    print("🤖 Executing LLM evaluation...")
    evaluation_output = await mock_llm_evaluator(eval_result.evaluation_prompt)
    
    # Display results
    print("📊 EVALUATION RESULTS:")
    print("-" * 60)
    print(f"Overall Security Score: {evaluation_output['overall_score']:.2f}/1.0")
    print(f"Enterprise Readiness: {evaluation_output['enterprise_readiness']}")
    print(f"Risk Level: {evaluation_output['risk_level']}")
    print()
    
    print("🔍 DETAILED CRITERIA SCORES:")
    for criterion, score in evaluation_output['criteria_scores'].items():
        status = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
        print(f"  {status} {criterion.replace('_', ' ').title()}: {score:.2f}")
    print()
    
    print("💪 SECURITY STRENGTHS:")
    for strength in evaluation_output['security_strengths']:
        print(f"  ✅ {strength}")
    print()
    
    print("⚠️ SECURITY WEAKNESSES:")
    for weakness in evaluation_output['security_weaknesses']:
        print(f"  ❌ {weakness}")
    print()
    
    print("🔧 SECURITY RECOMMENDATIONS:")
    for recommendation in evaluation_output['security_recommendations']:
        print(f"  💡 {recommendation}")
    print()


async def demonstrate_multi_domain_evaluation():
    """Demonstrate evaluation across multiple domains."""
    print("\n🎯 MULTI-DOMAIN EVALUATION DEMONSTRATION")
    print("=" * 60)
    
    # Initialize orchestrator
    knowledge_manager = KnowledgeManager(CONFIG_PATH)
    evaluation_generator = EvaluationPromptGenerator(knowledge_manager)
    orchestrator = EvaluationChainOrchestrator(evaluation_generator)
    
    # Define evaluation domains
    domains = [
        EvaluationDomain.SECURITY,
        EvaluationDomain.PERFORMANCE,
        EvaluationDomain.RELIABILITY
    ]
    
    print(f"🔄 Evaluating across {len(domains)} domains:")
    for domain in domains:
        print(f"  • {domain.value}")
    print()
    
    # Execute evaluation chain
    chain_results = await orchestrator.evaluate_prompt_chain(
        target_prompt=EXAMPLE_DOCKER_PROMPT,
        domains=domains,
        technologies=["docker", "postgresql"],
        llm_evaluator_func=mock_llm_evaluator
    )
    
    # Display aggregated results
    print("📈 EVALUATION CHAIN RESULTS:")
    print("-" * 60)
    print(f"Target Prompt: Docker Security Deployment")
    print(f"Technologies: {', '.join(chain_results['technologies'])}")
    print(f"Domains Evaluated: {len(chain_results['domains_evaluated'])}")
    print(f"Evaluation Timestamp: {chain_results['evaluation_timestamp']}")
    print()
    
    print("🎯 DOMAIN-SPECIFIC RESULTS:")
    for domain, result in chain_results['individual_results'].items():
        status_emoji = "✅" if result['status'] == 'completed' else "❌"
        print(f"  {status_emoji} {domain.title()}: {result['status']}")
    print()
    
    print("📊 AGGREGATED SUMMARY:")
    summary = chain_results['aggregated_summary']
    print(f"  Status: {summary['status']}")
    print(f"  Completed: {summary.get('domains_completed', 0)}")
    print(f"  Failed: {summary.get('domains_failed', 0)}")
    print()


def demonstrate_custom_criteria():
    """Demonstrate custom evaluation criteria."""
    print("\n⚙️ CUSTOM CRITERIA DEMONSTRATION")
    print("=" * 60)
    
    # Initialize components
    knowledge_manager = KnowledgeManager(CONFIG_PATH)
    evaluation_generator = EvaluationPromptGenerator(knowledge_manager)
    
    # Define custom security criteria for Docker
    custom_security_criteria = {
        "container_isolation": 0.25,  # Custom criterion
        "image_security": 0.20,      # Custom criterion
        "runtime_security": 0.15,    # Custom criterion
        "secret_management": 0.20,   # Standard criterion
        "network_security": 0.20     # Standard criterion
    }
    
    print("🎛️ Custom Security Criteria for Docker:")
    for criterion, weight in custom_security_criteria.items():
        print(f"  • {criterion.replace('_', ' ').title()}: {weight:.0%}")
    print()
    
    # Generate evaluation prompt with custom criteria
    eval_result = evaluation_generator.generate_evaluation_prompt(
        target_prompt=EXAMPLE_DOCKER_PROMPT,
        evaluation_domain=EvaluationDomain.SECURITY,
        technologies=["docker"],
        custom_criteria=custom_security_criteria
    )
    
    print(f"📋 Generated custom evaluation prompt")
    print(f"🎯 Domain: {eval_result.domain.value}")
    print(f"📊 Custom criteria count: {eval_result.criteria_count}")
    print()


async def main():
    """Main demonstration function."""
    print("🚀 EVALUATION PROMPT GENERATOR DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Demonstrate different aspects of the evaluation framework
    await demonstrate_security_evaluation()
    await demonstrate_multi_domain_evaluation()
    demonstrate_custom_criteria()
    
    print("✅ DEMONSTRATION COMPLETED")
    print("=" * 80)
    print()
    print("💡 Key Takeaways:")
    print("  • Evaluation prompts provide structured, consistent assessment")
    print("  • Domain-specific criteria ensure comprehensive evaluation")
    print("  • Custom criteria allow flexibility for specific requirements")
    print("  • Multi-domain evaluation provides holistic quality assessment")
    print("  • Evidence-based scoring enables actionable improvements")


if __name__ == "__main__":
    asyncio.run(main())