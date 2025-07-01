#!/usr/bin/env python3
"""
Advanced Prompt Engineering CLI - Evaluation Mode

Enhanced CLI with evaluation prompt generation capabilities for meta-evaluation
of prompts using structured domain-specific criteria.
"""

import asyncio
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.knowledge_manager import KnowledgeManager
from src.evaluation.evaluation_prompt_generator import (
    EvaluationPromptGenerator,
    EvaluationChainOrchestrator, 
    EvaluationDomain
)
from src.evaluation.evaluation_types import ComplianceStandard

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EvaluationCLI:
    """CLI for evaluation prompt generation and execution."""
    
    def __init__(self):
        config_path = "config/tech_stack_mapping.json"
        self.knowledge_manager = KnowledgeManager(config_path)
        self.evaluation_generator = EvaluationPromptGenerator(self.knowledge_manager)
        self.orchestrator = EvaluationChainOrchestrator(self.evaluation_generator)
    
    def list_evaluation_domains(self):
        """List available evaluation domains."""
        print("\n📊 Available Evaluation Domains:")
        print("=" * 50)
        
        for domain in EvaluationDomain:
            criteria = self.evaluation_generator._evaluation_criteria[domain]
            print(f"\n🎯 {domain.value.upper()}")
            print(f"   Description: {criteria.description}")
            print(f"   Criteria count: {len(criteria.criteria)}")
            print(f"   Min threshold: {criteria.min_threshold}")
            
            print("   Key criteria:")
            for criterion, weight in list(criteria.criteria.items())[:3]:
                print(f"     • {criterion.replace('_', ' ').title()} ({weight:.0%})")
    
    def list_compliance_standards(self):
        """List available compliance standards."""
        print("\n📋 Available Compliance Standards:")
        print("=" * 50)
        
        for standard in ComplianceStandard:
            print(f"  • {standard.value}")
    
    async def generate_evaluation_prompt(
        self,
        target_prompt: str,
        domain: EvaluationDomain,
        technologies: List[str],
        compliance_standards: List[ComplianceStandard] = None,
        output_file: str = None
    ):
        """Generate evaluation prompt for specified domain."""
        logger.info(f"Generating evaluation prompt for domain: {domain.value}")
        
        # Generate evaluation prompt
        result = self.evaluation_generator.generate_evaluation_prompt(
            target_prompt=target_prompt,
            evaluation_domain=domain,
            technologies=technologies,
            compliance_standards=compliance_standards
        )
        
        # Format output
        output_data = {
            "evaluation_prompt": result.evaluation_prompt,
            "metadata": {
                "domain": result.domain.value,
                "technologies": result.target_technologies,
                "criteria_count": result.criteria_count,
                "confidence_score": result.confidence_score,
                "generated_at": result.generated_at.isoformat()
            },
            "instructions": result.evaluation_instructions,
            "scoring_rubric": result.scoring_rubric
        }
        
        # Output handling
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"✅ Evaluation prompt written to {output_file}")
        else:
            print("\n📝 GENERATED EVALUATION PROMPT:")
            print("=" * 80)
            print(result.evaluation_prompt)
            print("=" * 80)
        
        return result
    
    async def run_evaluation_chain(
        self,
        target_prompt: str,
        domains: List[EvaluationDomain],
        technologies: List[str],
        mock_evaluation: bool = True
    ):
        """Run complete evaluation chain across multiple domains."""
        logger.info(f"Running evaluation chain for {len(domains)} domains")
        
        async def mock_llm_evaluator(evaluation_prompt: str) -> Dict[str, Any]:
            """Mock LLM evaluator for demonstration."""
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Simple mock evaluation based on domain
            if "security" in evaluation_prompt.lower():
                return {
                    "overall_score": 0.6,
                    "domain": "security",
                    "enterprise_readiness": "CONDITIONAL",
                    "summary": "Moderate security with improvements needed"
                }
            elif "performance" in evaluation_prompt.lower():
                return {
                    "overall_score": 0.7,
                    "domain": "performance", 
                    "enterprise_readiness": "CONDITIONAL",
                    "summary": "Good performance baseline with optimization opportunities"
                }
            else:
                return {
                    "overall_score": 0.8,
                    "domain": "general",
                    "enterprise_readiness": "READY",
                    "summary": "Meets enterprise standards"
                }
        
        # Execute evaluation chain
        if mock_evaluation:
            results = await self.orchestrator.evaluate_prompt_chain(
                target_prompt=target_prompt,
                domains=domains,
                technologies=technologies,
                llm_evaluator_func=mock_llm_evaluator
            )
        else:
            print("❌ Real LLM evaluation not implemented in this demo")
            return
        
        # Display results
        print("\n📊 EVALUATION CHAIN RESULTS:")
        print("=" * 80)
        print(f"Target Technologies: {', '.join(technologies)}")
        print(f"Domains Evaluated: {len(domains)}")
        print(f"Evaluation Timestamp: {results['evaluation_timestamp']}")
        
        print(f"\n🎯 DOMAIN RESULTS:")
        for domain_name, result in results['individual_results'].items():
            status_emoji = "✅" if result['status'] == 'completed' else "❌"
            print(f"  {status_emoji} {domain_name.title()}: {result['status']}")
            
            if result['status'] == 'completed' and 'llm_output' in result:
                output = result['llm_output']
                print(f"      Score: {output.get('overall_score', 'N/A')}")
                print(f"      Status: {output.get('enterprise_readiness', 'N/A')}")
        
        return results


def create_evaluation_cli_parser() -> argparse.ArgumentParser:
    """Create CLI parser for evaluation mode."""
    parser = argparse.ArgumentParser(
        prog="prompt-engineer-eval",
        description="Advanced Prompt Engineering CLI - Evaluation Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-domains
  %(prog)s --target-file prompt.txt --domain security --tech docker postgresql
  %(prog)s --target-file prompt.txt --chain security performance --tech docker
  %(prog)s --target-text "Docker setup" --domain reliability --tech docker --output eval.json
        """
    )
    
    # Information commands
    info_group = parser.add_argument_group('Information Commands')
    info_group.add_argument(
        '--list-domains',
        action='store_true',
        help='List available evaluation domains'
    )
    info_group.add_argument(
        '--list-compliance',
        action='store_true', 
        help='List available compliance standards'
    )
    
    # Target prompt input
    target_group = parser.add_argument_group('Target Prompt Input')
    target_group.add_argument(
        '--target-file',
        metavar='FILE',
        help='File containing the prompt to evaluate'
    )
    target_group.add_argument(
        '--target-text',
        metavar='TEXT',
        help='Direct text of the prompt to evaluate'
    )
    
    # Evaluation configuration
    eval_group = parser.add_argument_group('Evaluation Configuration')
    eval_group.add_argument(
        '--domain',
        choices=[d.value for d in EvaluationDomain],
        help='Single evaluation domain'
    )
    eval_group.add_argument(
        '--chain',
        nargs='+',
        choices=[d.value for d in EvaluationDomain],
        help='Multiple domains for evaluation chain'
    )
    eval_group.add_argument(
        '--tech', '--technologies',
        nargs='+',
        metavar='TECH',
        help='Technologies involved in the prompt'
    )
    eval_group.add_argument(
        '--compliance',
        nargs='+',
        choices=[s.value for s in ComplianceStandard],
        help='Compliance standards to check against'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output', '-o',
        metavar='FILE',
        help='Output file for evaluation prompt (JSON format)'
    )
    output_group.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    output_group.add_argument(
        '--mock-evaluation',
        action='store_true',
        default=True,
        help='Use mock LLM evaluation for demonstration'
    )
    
    return parser


async def main():
    """Main CLI entry point for evaluation mode."""
    parser = create_evaluation_cli_parser()
    args = parser.parse_args()
    
    # Initialize CLI
    cli = EvaluationCLI()
    
    # Handle information commands
    if args.list_domains:
        cli.list_evaluation_domains()
        return
    
    if args.list_compliance:
        cli.list_compliance_standards()
        return
    
    # Validate target prompt input
    target_prompt = None
    if args.target_file:
        try:
            with open(args.target_file, 'r') as f:
                target_prompt = f.read().strip()
        except FileNotFoundError:
            print(f"❌ Target file not found: {args.target_file}")
            return
    elif args.target_text:
        target_prompt = args.target_text
    else:
        print("❌ No target prompt provided. Use --target-file or --target-text")
        print("Use --help for usage information")
        return
    
    # Validate technologies
    if not args.tech:
        print("❌ No technologies specified. Use --tech to specify technologies")
        return
    
    # Parse compliance standards
    compliance_standards = None
    if args.compliance:
        compliance_standards = [ComplianceStandard(std) for std in args.compliance]
    
    # Execute evaluation
    if args.chain:
        # Multi-domain evaluation chain
        domains = [EvaluationDomain(d) for d in args.chain]
        await cli.run_evaluation_chain(
            target_prompt=target_prompt,
            domains=domains,
            technologies=args.tech,
            mock_evaluation=args.mock_evaluation
        )
    elif args.domain:
        # Single domain evaluation
        domain = EvaluationDomain(args.domain)
        await cli.generate_evaluation_prompt(
            target_prompt=target_prompt,
            domain=domain,
            technologies=args.tech,
            compliance_standards=compliance_standards,
            output_file=args.output
        )
    else:
        print("❌ No evaluation mode specified. Use --domain or --chain")
        print("Use --help for usage information")


if __name__ == "__main__":
    asyncio.run(main())