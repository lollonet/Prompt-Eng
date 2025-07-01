#!/usr/bin/env python3
"""
Comprehensive system health check for all major components.

Tests each component to identify what's working vs. what needs fixes
before building any new features on top.
"""

import asyncio
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config_manager import get_config, ConfigurationManager
from src.knowledge_manager_async import AsyncKnowledgeManager
from src.prompt_generator_modern import ModernPromptGenerator
from src.events import EventBus, EventType, setup_default_event_handlers
from src.types_advanced import (
    PromptConfigAdvanced, TechnologyName, TaskType, KnowledgeManagerConfig
)
from src.result_types import Success, Error


class ComponentHealthChecker:
    """Health checker for all system components."""
    
    def __init__(self):
        self.results = {}
        self.issues = []
    
    def log_result(self, component: str, status: str, details: str = ""):
        """Log component test result."""
        self.results[component] = {
            "status": status,
            "details": details
        }
        
        if status == "FAILED":
            self.issues.append(f"{component}: {details}")
    
    async def test_configuration_system(self):
        """Test centralized configuration system."""
        print("🔧 Testing Configuration System...")
        
        try:
            # Test default config loading
            config_result = get_config()
            if config_result.is_error():
                self.log_result("Configuration Loading", "FAILED", 
                               f"Error: {config_result.error}")
                return
            
            config = config_result.unwrap()
            
            # Test configuration structure
            required_sections = [
                'system', 'paths', 'performance', 'cache', 'logging',
                'knowledge_manager', 'event_system', 'web_research', 
                'security', 'templates', 'monitoring', 'development'
            ]
            
            missing_sections = []
            for section in required_sections:
                if not hasattr(config, section):
                    missing_sections.append(section)
            
            if missing_sections:
                self.log_result("Configuration Structure", "FAILED",
                               f"Missing sections: {missing_sections}")
            else:
                self.log_result("Configuration Structure", "PASSED")
            
            # Test configuration hot reload
            manager = ConfigurationManager()
            reload_result = manager.reload_config()
            if reload_result.is_error():
                self.log_result("Configuration Hot Reload", "WARNING",
                               f"Hot reload failed: {reload_result.error}")
            else:
                self.log_result("Configuration Hot Reload", "PASSED")
            
            self.log_result("Configuration System", "PASSED")
            
        except Exception as e:
            self.log_result("Configuration System", "FAILED", str(e))
    
    async def test_knowledge_manager(self):
        """Test AsyncKnowledgeManager."""
        print("📚 Testing Knowledge Manager...")
        
        try:
            # Create knowledge manager with default config
            config = KnowledgeManagerConfig(
                config_path="config/tech_stack_mapping.json",
                base_path="knowledge_base",
                cache_strategy="memory"
            )
            
            km = AsyncKnowledgeManager(config)
            
            # Test basic operations
            python_tech = TechnologyName("python")
            
            # Test best practices loading
            bp_result = await km.get_best_practices(python_tech)
            if bp_result.is_error():
                self.log_result("Knowledge Manager - Best Practices", "FAILED",
                               f"Error: {bp_result.error}")
            else:
                practices = bp_result.unwrap()
                if isinstance(practices, list) and len(practices) > 0:
                    self.log_result("Knowledge Manager - Best Practices", "PASSED")
                else:
                    self.log_result("Knowledge Manager - Best Practices", "WARNING",
                                   "Empty or invalid practices returned")
            
            # Test tools loading
            tools_result = await km.get_tools(python_tech)
            if tools_result.is_error():
                self.log_result("Knowledge Manager - Tools", "FAILED",
                               f"Error: {tools_result.error}")
            else:
                tools = tools_result.unwrap()
                if isinstance(tools, list) and len(tools) > 0:
                    self.log_result("Knowledge Manager - Tools", "PASSED")
                else:
                    self.log_result("Knowledge Manager - Tools", "WARNING",
                                   "Empty or invalid tools returned")
            
            # Test health check
            health_result = await km.health_check()
            if health_result.is_error():
                self.log_result("Knowledge Manager - Health Check", "FAILED",
                               f"Error: {health_result.error}")
            else:
                health = health_result.unwrap()
                if isinstance(health, dict) and "status" in health:
                    self.log_result("Knowledge Manager - Health Check", "PASSED")
                else:
                    self.log_result("Knowledge Manager - Health Check", "WARNING",
                                   "Invalid health check format")
            
            self.log_result("Knowledge Manager", "PASSED")
            
        except Exception as e:
            self.log_result("Knowledge Manager", "FAILED", str(e))
    
    async def test_prompt_generator(self):
        """Test ModernPromptGenerator."""
        print("✨ Testing Prompt Generator...")
        
        try:
            # Create dependencies
            km_config = KnowledgeManagerConfig(
                config_path="config/tech_stack_mapping.json",
                base_path="knowledge_base",
                cache_strategy="memory"
            )
            km = AsyncKnowledgeManager(km_config)
            
            # Create prompt generator
            generator = ModernPromptGenerator(
                prompts_dir="prompts",
                knowledge_source=km,
                performance_tracking=True
            )
            
            # Test basic prompt generation
            config = PromptConfigAdvanced(
                technologies=[TechnologyName("python")],
                task_type=TaskType("api_development"),
                task_description="Create a simple REST API",
                code_requirements="Include error handling and logging"
            )
            
            result = await generator.generate_prompt(config)
            
            if result.is_error():
                self.log_result("Prompt Generator - Basic Generation", "FAILED",
                               f"Error: {result.error}")
            else:
                prompt = result.unwrap()
                if isinstance(prompt, str) and len(prompt) > 50:
                    self.log_result("Prompt Generator - Basic Generation", "PASSED")
                else:
                    self.log_result("Prompt Generator - Basic Generation", "WARNING",
                                   "Generated prompt too short or invalid")
            
            # Test health check
            health_result = await generator.health_check()
            if health_result.is_error():
                self.log_result("Prompt Generator - Health Check", "FAILED",
                               f"Error: {health_result.error}")
            else:
                self.log_result("Prompt Generator - Health Check", "PASSED")
            
            self.log_result("Prompt Generator", "PASSED")
            
        except Exception as e:
            self.log_result("Prompt Generator", "FAILED", str(e))
    
    async def test_event_system(self):
        """Test event system."""
        print("📡 Testing Event System...")
        
        try:
            # Test event bus creation
            event_bus = EventBus()
            
            # Test event subscription and publishing
            events_received = []
            
            async def test_handler(event):
                events_received.append(event)
            
            event_bus.subscribe(EventType.PROMPT_GENERATION_STARTED, test_handler)
            
            # Test publishing
            from src.events import Event
            test_event = Event(
                event_type=EventType.PROMPT_GENERATION_STARTED,
                source="test_system_health",
                payload={
                    "test": "data",
                    "correlation_id": "test-123"
                }
            )
            await event_bus.publish(test_event)
            
            # Give events time to propagate
            await asyncio.sleep(0.1)
            
            if len(events_received) > 0:
                self.log_result("Event System - Pub/Sub", "PASSED")
            else:
                self.log_result("Event System - Pub/Sub", "FAILED",
                               "No events received")
            
            # Test default handlers setup
            try:
                setup_default_event_handlers()
                self.log_result("Event System - Default Handlers", "PASSED")
            except Exception as e:
                self.log_result("Event System - Default Handlers", "WARNING",
                               f"Default handlers error: {e}")
            
            self.log_result("Event System", "PASSED")
            
        except Exception as e:
            self.log_result("Event System", "FAILED", str(e))
    
    async def test_evaluation_system(self):
        """Test evaluation system."""
        print("🔍 Testing Evaluation System...")
        
        try:
            from src.evaluation.evaluation_prompt_generator import (
                EvaluationPromptGenerator, EvaluationDomain
            )
            from src.knowledge_manager import KnowledgeManager
            
            # Create evaluation system
            km = KnowledgeManager("config/tech_stack_mapping.json")
            eval_gen = EvaluationPromptGenerator(km)
            
            # Test basic evaluation prompt generation
            test_prompt = "Create a secure Python API"
            
            result = eval_gen.generate_evaluation_prompt(
                target_prompt=test_prompt,
                evaluation_domain=EvaluationDomain.SECURITY,
                technologies=["python"]
            )
            
            if hasattr(result, 'evaluation_prompt') and len(result.evaluation_prompt) > 50:
                self.log_result("Evaluation System - Basic Generation", "PASSED")
            else:
                self.log_result("Evaluation System - Basic Generation", "FAILED",
                               "Generated evaluation prompt too short or missing")
            
            # Test multiple domains
            domains_working = 0
            total_domains = 0
            
            # Test a comprehensive set of domains
            test_domains = [
                EvaluationDomain.SECURITY,
                EvaluationDomain.PERFORMANCE, 
                EvaluationDomain.CODE_QUALITY,
                EvaluationDomain.RELIABILITY,
                EvaluationDomain.INFRASTRUCTURE
            ]
            
            for domain in test_domains:
                total_domains += 1
                try:
                    result = eval_gen.generate_evaluation_prompt(
                        target_prompt=test_prompt,
                        evaluation_domain=domain,
                        technologies=["python"]
                    )
                    if hasattr(result, 'evaluation_prompt') and len(result.evaluation_prompt) > 50:
                        domains_working += 1
                except Exception:
                    pass
            
            if domains_working == total_domains:
                self.log_result("Evaluation System - Multi-Domain", "PASSED")
            elif domains_working > 0:
                self.log_result("Evaluation System - Multi-Domain", "WARNING",
                               f"Only {domains_working}/{total_domains} domains working")
            else:
                self.log_result("Evaluation System - Multi-Domain", "FAILED",
                               "No domains working")
            
            # Overall evaluation system status
            if domains_working == total_domains:
                self.log_result("Evaluation System", "PASSED")
            elif domains_working > 0:
                self.log_result("Evaluation System", "PARTIAL")
            else:
                self.log_result("Evaluation System", "FAILED")
            
        except Exception as e:
            self.log_result("Evaluation System", "FAILED", str(e))
    
    async def test_web_research_system(self):
        """Test web research components."""
        print("🌐 Testing Web Research System...")
        
        try:
            from src.web_research.technology_detector import TechnologyDetector
            from src.web_research.config import WebResearchConfig, Environment
            
            # Create web research components
            config = WebResearchConfig(environment=Environment.TESTING)
            detector = TechnologyDetector(config)
            
            # Test technology detection
            profile = await detector.get_technology_profile("python")
            if profile is not None:
                self.log_result("Web Research - Technology Detection", "PASSED")
            else:
                self.log_result("Web Research - Technology Detection", "WARNING",
                               "No profile returned for known technology")
            
            # Test unknown technology detection
            unknown = await detector.detect_unknown_technologies(["python", "unknown_tech_xyz"])
            if isinstance(unknown, list):
                self.log_result("Web Research - Unknown Detection", "PASSED")
            else:
                self.log_result("Web Research - Unknown Detection", "FAILED",
                               "Invalid response format")
            
            self.log_result("Web Research System", "PASSED")
            
        except Exception as e:
            self.log_result("Web Research System", "FAILED", str(e))
    
    async def test_template_system(self):
        """Test template rendering system."""
        print("📄 Testing Template System...")
        
        try:
            # Test template file existence
            template_dirs = ["prompts/base_prompts", "prompts/language_specific", "prompts/framework_specific"]
            template_files_found = 0
            
            for template_dir in template_dirs:
                template_path = Path(template_dir)
                if template_path.exists():
                    template_files = list(template_path.glob("*.txt"))
                    template_files_found += len(template_files)
            
            if template_files_found > 0:
                self.log_result("Template System - Files", "PASSED",
                               f"Found {template_files_found} template files")
            else:
                self.log_result("Template System - Files", "WARNING",
                               "No template files found")
            
            # Test template rendering would go here, but it's integrated in prompt generator
            self.log_result("Template System", "PASSED")
            
        except Exception as e:
            self.log_result("Template System", "FAILED", str(e))
    
    def print_health_report(self):
        """Print comprehensive health report."""
        print("\n" + "="*80)
        print("🏥 SYSTEM HEALTH REPORT")
        print("="*80)
        
        passed = sum(1 for r in self.results.values() if r["status"] == "PASSED")
        partial = sum(1 for r in self.results.values() if r["status"] == "PARTIAL")
        warning = sum(1 for r in self.results.values() if r["status"] == "WARNING")
        failed = sum(1 for r in self.results.values() if r["status"] == "FAILED")
        total = len(self.results)
        
        print(f"📊 Overall Status: {passed} ✅ | {partial} 🟡 | {warning} ⚠️ | {failed} ❌ (Total: {total})")
        print()
        
        # Group results by status
        for status, emoji in [("PASSED", "✅"), ("PARTIAL", "🟡"), ("WARNING", "⚠️"), ("FAILED", "❌")]:
            components = [name for name, result in self.results.items() if result["status"] == status]
            if components:
                print(f"{emoji} {status}:")
                for component in components:
                    details = self.results[component]["details"]
                    if details:
                        print(f"   • {component}: {details}")
                    else:
                        print(f"   • {component}")
                print()
        
        # Summary and recommendations
        print("🎯 RECOMMENDATIONS:")
        print("="*40)
        
        if failed == 0 and partial == 0 and warning <= 1:
            print("🌟 EXCELLENT: System is ready for advanced features")
            print("   ✅ Safe to build recursive prompt generator")
            print("   ✅ Safe to add new features")
            
        elif failed == 0 and partial <= 1:
            print("✅ GOOD: System is mostly healthy with minor issues")
            print("   ✅ Safe to build most features")
            print("   ⚠️  Address warnings before production")
            
        elif failed <= 2:
            print("⚠️  CAUTION: Some components need fixes")
            print("   🔧 Fix failed components before building on top")
            print("   ⚠️  Test thoroughly before deployment")
            
        else:
            print("❌ CRITICAL: Multiple system failures detected")
            print("   🛑 Do NOT build new features yet")
            print("   🔧 Fix core components first")
        
        print(f"\n📋 Issues to address: {len(self.issues)}")
        for issue in self.issues:
            print(f"   • {issue}")
        
        return failed == 0 and partial <= 1  # Return True if system is healthy enough


async def main():
    """Run comprehensive system health check."""
    print("🔍 COMPREHENSIVE SYSTEM HEALTH CHECK")
    print("="*80)
    print("Checking all major components before building new features...\n")
    
    checker = ComponentHealthChecker()
    
    # Run all component tests
    await checker.test_configuration_system()
    await checker.test_knowledge_manager()
    await checker.test_prompt_generator()
    await checker.test_event_system()
    await checker.test_evaluation_system()
    await checker.test_web_research_system()
    await checker.test_template_system()
    
    # Print comprehensive report
    is_healthy = checker.print_health_report()
    
    return is_healthy


if __name__ == "__main__":
    try:
        is_healthy = asyncio.run(main())
        sys.exit(0 if is_healthy else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Health check failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)