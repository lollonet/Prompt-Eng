#!/usr/bin/env python3
"""
Quick test to evaluate the quality of our evaluation system.

Tests the evaluation prompt generator and checks if it produces
useful evaluation prompts for different domains.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.evaluation.evaluation_prompt_generator import (
    EvaluationPromptGenerator,
    EvaluationDomain,
    EvaluationCriteria
)
from src.knowledge_manager import KnowledgeManager


async def test_evaluation_system_quality():
    """Test the evaluation system's ability to generate useful prompts."""
    
    print("🔍 TESTING EVALUATION SYSTEM QUALITY")
    print("=" * 60)
    
    # Initialize components
    knowledge_manager = KnowledgeManager("config/tech_stack_mapping.json")
    evaluation_generator = EvaluationPromptGenerator(knowledge_manager)
    
    # Test prompt to evaluate
    test_prompt = """
# Docker Security Deployment

Create a secure Docker application with these requirements:
- Use minimal base images
- Run as non-root user
- Implement health checks
- Use secrets management
- Enable security scanning

## Expected Output
```dockerfile
FROM alpine:3.19
RUN adduser -D appuser
USER appuser
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8080/health
```
"""
    
    # Test 1: Basic functionality
    print("\n📋 Test 1: Basic Security Evaluation Generation")
    try:
        criteria = EvaluationCriteria(
            domain=EvaluationDomain.SECURITY,
            criteria={
                "secret_management": 0.3,
                "privilege_escalation": 0.2,
                "network_security": 0.2,
                "access_controls": 0.15,
                "encryption": 0.15
            },
            min_threshold=0.7,
            description="Security evaluation for Docker deployments"
        )
        
        result = evaluation_generator.generate_evaluation_prompt(
            evaluation_domain=EvaluationDomain.SECURITY,
            technologies=["docker"],
            target_prompt=test_prompt,
            criteria=criteria
        )
        
        print("✅ Security evaluation prompt generated successfully")
        print(f"📏 Prompt length: {len(result.evaluation_prompt)} characters")
        print(f"🎯 Domain: {result.domain.value}")
        print(f"📊 Criteria count: {result.criteria_count}")
        
        # Check if the prompt contains key elements
        prompt = result.evaluation_prompt
        essential_elements = [
            "security",
            "score",
            "criteria",
            "evaluation",
            "docker"
        ]
        
        missing_elements = []
        for element in essential_elements:
            if element.lower() not in prompt.lower():
                missing_elements.append(element)
        
        if missing_elements:
            print(f"⚠️  Missing elements: {missing_elements}")
        else:
            print("✅ All essential elements present")
            
    except Exception as e:
        print(f"❌ Error generating security evaluation: {e}")
        return False
    
    # Test 2: Multiple domains
    print("\n📋 Test 2: Multiple Domain Support")
    domains_tested = 0
    domains_working = 0
    
    for domain in [EvaluationDomain.PERFORMANCE, EvaluationDomain.CODE_QUALITY]:
        try:
            criteria = EvaluationCriteria(
                domain=domain,
                criteria={
                    "criterion_1": 0.5,
                    "criterion_2": 0.5
                },
                min_threshold=0.6
            )
            
            result = evaluation_generator.generate_evaluation_prompt(
                evaluation_domain=domain,
                technologies=["python"],
                target_prompt="Simple test prompt",
                criteria=criteria
            )
            
            domains_tested += 1
            if len(result.evaluation_prompt) > 100:  # Basic sanity check
                domains_working += 1
                print(f"✅ {domain.value} evaluation working")
            else:
                print(f"⚠️  {domain.value} evaluation too short")
                
        except Exception as e:
            print(f"❌ {domain.value} evaluation failed: {e}")
            domains_tested += 1
    
    print(f"📊 Domain coverage: {domains_working}/{domains_tested} working")
    
    # Test 3: Evaluation quality analysis
    print("\n📋 Test 3: Evaluation Quality Analysis")
    
    try:
        # Generate a security evaluation prompt
        security_criteria = EvaluationCriteria(
            domain=EvaluationDomain.SECURITY,
            criteria={
                "authentication": 0.25,
                "authorization": 0.25,
                "data_protection": 0.25,
                "input_validation": 0.25
            },
            min_threshold=0.8
        )
        
        result = evaluation_generator.generate_evaluation_prompt(
            evaluation_domain=EvaluationDomain.SECURITY,
            technologies=["python", "flask"],
            target_prompt="Create a secure Flask API with authentication",
            criteria=security_criteria
        )
        
        prompt = result.evaluation_prompt
        
        # Quality indicators
        quality_indicators = {
            "structured_format": "json" in prompt.lower() or "format" in prompt.lower(),
            "clear_instructions": "evaluate" in prompt.lower() and "prompt" in prompt.lower(),
            "scoring_guidance": "score" in prompt.lower() and ("0" in prompt or "1" in prompt),
            "technology_specific": "flask" in prompt.lower() or "python" in prompt.lower(),
            "criteria_mentioned": len([c for c in security_criteria.criteria.keys() if c in prompt.lower()]) > 0
        }
        
        quality_score = sum(quality_indicators.values()) / len(quality_indicators)
        
        print(f"📊 Quality Score: {quality_score:.2f} ({quality_score*100:.0f}%)")
        
        for indicator, present in quality_indicators.items():
            status = "✅" if present else "❌"
            print(f"  {status} {indicator.replace('_', ' ').title()}")
        
        # Overall assessment
        print(f"\n🎯 EVALUATION SYSTEM QUALITY ASSESSMENT")
        print("=" * 60)
        
        if quality_score >= 0.8:
            print("🌟 EXCELLENT: Evaluation system produces high-quality prompts")
            print("   Ready for recursive prompt generation system")
        elif quality_score >= 0.6:
            print("✅ GOOD: Evaluation system works well with minor improvements needed")
            print("   Suitable for recursive system with some enhancements")
        elif quality_score >= 0.4:
            print("⚠️  FAIR: Evaluation system needs improvements before recursive use")
            print("   Recommend fixing issues before building recursive system")
        else:
            print("❌ POOR: Evaluation system needs major improvements")
            print("   Must fix evaluation system before recursive implementation")
        
        return quality_score >= 0.6
        
    except Exception as e:
        print(f"❌ Quality analysis failed: {e}")
        return False


async def test_evaluation_consistency():
    """Test if evaluation system produces consistent results."""
    
    print("\n🔄 TESTING EVALUATION CONSISTENCY")
    print("=" * 60)
    
    knowledge_manager = KnowledgeManager("config/tech_stack_mapping.json")
    evaluation_generator = EvaluationPromptGenerator(knowledge_manager)
    
    test_prompt = "Create a secure Python API with proper error handling"
    
    criteria = EvaluationCriteria(
        domain=EvaluationDomain.SECURITY,
        criteria={"security": 1.0},
        min_threshold=0.7
    )
    
    # Generate the same evaluation prompt multiple times
    results = []
    for i in range(3):
        try:
            result = evaluation_generator.generate_evaluation_prompt(
                evaluation_domain=EvaluationDomain.SECURITY,
                technologies=["python"],
                target_prompt=test_prompt,
                criteria=criteria
            )
            results.append(result.evaluation_prompt)
        except Exception as e:
            print(f"❌ Consistency test {i+1} failed: {e}")
            return False
    
    # Check consistency
    if len(set(results)) == 1:
        print("✅ Perfect consistency: All generations identical")
        return True
    elif len(set(results)) <= 2:
        print("✅ Good consistency: Minor variations")
        return True
    else:
        print("⚠️  Inconsistent results across generations")
        return False


async def main():
    """Main test runner."""
    print("🧪 EVALUATION SYSTEM QUALITY CHECK")
    print("=" * 80)
    print("Testing the evaluation system before building recursive prompt generator")
    print()
    
    # Run quality tests
    quality_good = await test_evaluation_system_quality()
    consistency_good = await test_evaluation_consistency()
    
    print(f"\n📋 FINAL ASSESSMENT")
    print("=" * 60)
    
    if quality_good and consistency_good:
        print("🎉 EVALUATION SYSTEM IS READY!")
        print("✅ Quality is sufficient for recursive prompt generation")
        print("✅ Consistency is good across multiple runs")
        print("\n🚀 RECOMMENDATION: Proceed with recursive prompt generator implementation")
    elif quality_good:
        print("⚠️  EVALUATION SYSTEM NEEDS MINOR FIXES")
        print("✅ Quality is sufficient")
        print("❌ Consistency needs improvement")
        print("\n🔧 RECOMMENDATION: Fix consistency issues, then proceed")
    else:
        print("❌ EVALUATION SYSTEM NEEDS IMPROVEMENT")
        print("❌ Quality issues detected")
        print("\n🛠️  RECOMMENDATION: Fix evaluation system before recursive implementation")
    
    return quality_good and consistency_good


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)