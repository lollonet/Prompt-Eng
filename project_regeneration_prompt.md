# Advanced Prompt Engineering CLI - Complete Project Regeneration Prompt

## META-PROMPT: Use This Tool to Recreate Itself

This comprehensive prompt demonstrates the Advanced Prompt Engineering CLI generating a complete specification for recreating the entire project. This is a meta-demonstration of AI-assisted project development.

---

## 🎯 PROJECT OVERVIEW

### TASK
Build: **Enterprise-grade Advanced Prompt Engineering CLI with AI-powered template generation, comprehensive evaluation frameworks, and web research capabilities**

### BUSINESS CONTEXT
Create a sophisticated command-line tool that revolutionizes infrastructure code generation through:
- **AI-Enhanced Template Generation**: Smart engines for Docker, Ansible, Patroni
- **Enterprise Evaluation**: Production readiness and security assessment  
- **Web Research Integration**: Automatic technology discovery and best practices
- **Quality Assurance**: HumanEval-DevOps benchmarking and compliance validation

---

## 🏗️ TECHNICAL ARCHITECTURE

### Core Technologies Stack
- **Language**: Python 3.11+
- **CLI Framework**: argparse with shell autocomplete
- **Template Engine**: Jinja2 for dynamic prompt generation
- **Async Operations**: asyncio for web research and template generation
- **Web Research**: aiohttp, BeautifulSoup4, lxml for content analysis
- **Quality Tools**: pytest, black, pylint, mypy for code quality
- **Enterprise Features**: Comprehensive evaluation and compliance frameworks

### Project Structure
```
📁 Advanced-Prompt-Engineering-CLI/
├── 🎯 prompts/                    # Optimized prompt templates
│   ├── base_prompts/              # Core templates (1,800 chars avg)
│   ├── language_specific/         # Python, JavaScript, etc.
│   └── framework_specific/        # React, FastAPI, etc.
├── 🧠 src/
│   ├── prompt_generator.py        # Traditional prompt generation
│   ├── prompt_generator_modern.py # AI-enhanced generation
│   ├── knowledge_manager.py       # Knowledge base management  
│   ├── knowledge_manager_async.py # Async knowledge operations
│   ├── prompt_config.py          # Configuration classes
│   ├── 🌐 web_research/           # Web research & AI engines
│   │   ├── web_researcher.py      # Technology research
│   │   ├── technology_detector.py # Auto tech detection
│   │   ├── search_providers.py    # Multi-provider search
│   │   ├── cache/                 # Research caching system
│   │   └── template_engines/      # AI template generators
│   │       ├── base_engine.py     # Base engine interface
│   │       ├── docker_engine.py   # Docker Compose AI
│   │       ├── ansible_engine.py  # Ansible playbook AI  
│   │       └── patroni_engine.py  # PostgreSQL cluster AI
│   ├── 🛡️ evaluation/             # Enterprise evaluation
│   │   ├── production_readiness.py # 5-dimensional analysis
│   │   ├── humaneval_devops.py    # DevOps benchmarking
│   │   └── evaluation_types.py    # Common types & enums
│   ├── types_advanced.py          # Advanced type definitions
│   ├── result_types.py            # Result/Error handling
│   └── performance.py             # Performance monitoring
├── 📚 knowledge_base/             # Best practices & tools
│   ├── best_practices/           # Markdown files (.md)
│   └── tools/                    # JSON files (.json)
├── ⚙️ config/                     # Technology mappings
├── 📋 examples/                   # Generated template examples
├── 🧪 test_evaluation_frameworks.py # Comprehensive tests
├── main.py                        # Traditional CLI entry
├── main_modern.py                # Modern AI-powered CLI
└── requirements.txt              # Dependencies
```

---

## 🎨 IMPLEMENTATION REQUIREMENTS

### 1. Core Prompt Generation Engine

#### Traditional Prompt Generator (`src/prompt_generator.py`)
```python
class PromptGenerator:
    """Core prompt generation with template selection and rendering."""
    
    def __init__(self, knowledge_manager: KnowledgeManager):
        self.knowledge_manager = knowledge_manager
        self.template_loader = self._setup_jinja_environment()
    
    def generate_prompt(self, 
                       technologies: List[str], 
                       task_description: str,
                       template_name: Optional[str] = None,
                       specific_options: Optional[SpecificOptions] = None) -> PromptResult:
        """Generate optimized prompt based on technologies and task."""
        
        # 1. Intelligent template selection
        template = self._select_optimal_template(technologies, task_description)
        
        # 2. Gather technology knowledge  
        tech_knowledge = self.knowledge_manager.get_technology_knowledge(technologies)
        
        # 3. Render with context
        rendered_prompt = self._render_template(template, {
            'technologies': technologies,
            'task_description': task_description,
            'best_practices': tech_knowledge.best_practices,
            'tools': tech_knowledge.tools
        })
        
        return PromptResult(
            content=rendered_prompt,
            template_used=template.name,
            character_count=len(rendered_prompt),
            confidence_score=self._calculate_confidence(tech_knowledge)
        )
```

#### AI-Enhanced Generator (`src/prompt_generator_modern.py`)
```python
class ModernPromptGenerator:
    """AI-powered generation with web research and dynamic templates."""
    
    def __init__(self):
        self.web_researcher = WebResearcher()
        self.template_engines = [
            DockerTemplateEngine(),
            AnsibleTemplateEngine(), 
            PatroniTemplateEngine()
        ]
        self.evaluator = ProductionReadinessEvaluator()
    
    async def generate_with_research(self,
                                   technology: str,
                                   description: str,
                                   evaluate: bool = False) -> EnhancedPromptResult:
        """Generate template with real-time research and evaluation."""
        
        # 1. Research technology stack
        research_data = await self.web_researcher.research_technologies(
            technology.split()
        )
        
        # 2. Select appropriate engine
        engine = self._select_engine(technology, description)
        
        # 3. Generate template
        template_result = await engine.generate_template(
            TemplateContext(
                technology=technology,
                task_description=description,
                research_data=research_data
            )
        )
        
        # 4. Optional evaluation
        evaluation_result = None
        if evaluate:
            evaluation_result = self.evaluator.evaluate(
                template_result.content,
                self._create_eval_context(technology, description)
            )
        
        return EnhancedPromptResult(
            template=template_result,
            research_data=research_data,
            evaluation=evaluation_result
        )
```

### 2. Enterprise Evaluation Framework

#### Production Readiness Evaluator (`src/evaluation/production_readiness.py`)
```python
class ProductionReadinessEvaluator:
    """5-dimensional enterprise production readiness assessment."""
    
    def __init__(self):
        self.security_analyzer = SecurityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()  
        self.reliability_analyzer = ReliabilityAnalyzer()
        self.dimension_weights = {
            'security': 0.3,      # Critical for enterprise
            'performance': 0.2,   # Scalability requirements
            'reliability': 0.25,  # Availability targets
            'maintainability': 0.15,  # Long-term operations
            'compliance': 0.1     # Regulatory requirements
        }
    
    def evaluate(self, template: str, context: EvalContext) -> ProductionScore:
        """Comprehensive production readiness evaluation."""
        
        # Multi-dimensional analysis
        scores = {
            'security': self.security_analyzer.analyze(template, context),
            'performance': self.performance_analyzer.analyze(template, context),
            'reliability': self.reliability_analyzer.analyze(template, context),
            'maintainability': self._analyze_maintainability(template, context),
            'compliance': self._analyze_compliance(template, context)
        }
        
        # Weighted overall score
        overall_score = sum(
            score.score * self.dimension_weights[dimension]
            for dimension, score in scores.items()
        )
        
        return ProductionScore(
            overall_score=overall_score,
            security_score=scores['security'],
            performance_score=scores['performance'],
            reliability_score=scores['reliability'],
            maintainability_score=scores['maintainability'],
            compliance_score=scores['compliance'],
            risk_assessment=self._assess_risks(scores),
            deployment_readiness=self._assess_deployment_readiness(overall_score)
        )
```

#### HumanEval-DevOps Benchmark (`src/evaluation/humaneval_devops.py`)
```python
class DevOpsEvaluator:
    """Standardized infrastructure code evaluation framework."""
    
    def __init__(self):
        self.benchmark = DevOpsBenchmark()
        self.executor = DevOpsTaskExecutor()
    
    def evaluate_template_engine(self, 
                               engine_generate_func: Callable) -> Dict[str, Any]:
        """Run standardized DevOps benchmark evaluation."""
        
        results = {}
        
        for task in self.benchmark.tasks:
            # Generate template using provided function
            generated_template = engine_generate_func(task)
            
            # Execute in controlled environment
            result = self.executor.execute_task(task, generated_template)
            results[task.task_id] = result
        
        return self.benchmark.generate_report(results)

class DevOpsTaskExecutor:
    """Controlled execution environment for infrastructure testing."""
    
    def execute_task(self, task: DevOpsEvalTask, template: str) -> EvalResult:
        """Execute task with security isolation and validation."""
        
        # Create isolated environment
        task_dir = self._create_task_environment(task)
        
        try:
            # Write template files
            generated_files = self._write_template_files(template, task, task_dir)
            
            # Execute test scenarios
            scenario_results = []
            for scenario in task.test_scenarios:
                result = self._execute_scenario(scenario, task_dir)
                scenario_results.append(result)
            
            # Calculate scores
            scores = self._calculate_scores(task, scenario_results, template)
            
            return EvalResult(
                task_id=task.task_id,
                overall_score=scores['overall'],
                success=len([r for r in scenario_results if r['success']]) == len(scenario_results)
            )
            
        finally:
            self._cleanup_environment(task_dir)
```

### 3. AI-Powered Template Engines

#### Docker Template Engine (`src/web_research/template_engines/docker_engine.py`)
```python
class DockerTemplateEngine(BaseTemplateEngine):
    """AI-powered Docker Compose template generation."""
    
    def can_handle(self, context: TemplateContext) -> bool:
        """Determine if this engine can handle the request."""
        docker_keywords = ['docker', 'compose', 'container', 'nginx', 'postgres']
        return any(keyword in context.technology.lower() for keyword in docker_keywords)
    
    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """Generate production-ready Docker Compose configuration."""
        
        # 1. Analyze requirements
        services = self._extract_services(context.technology)
        
        # 2. Build base structure
        compose_config = {
            'version': '3.8',
            'services': {},
            'networks': {'app_network': {'driver': 'bridge'}},
            'volumes': {}
        }
        
        # 3. Generate services
        for service in services:
            service_config = await self._generate_service_config(
                service, context
            )
            compose_config['services'][service] = service_config
        
        # 4. Apply security best practices
        self._apply_security_hardening(compose_config)
        
        # 5. Add monitoring and health checks
        self._add_observability(compose_config, context)
        
        # 6. Render final template
        template_content = self._render_yaml(compose_config)
        
        return TemplateResult(
            content=template_content,
            confidence_score=self._calculate_confidence(context),
            metadata={
                'services_generated': len(services),
                'security_features': self._count_security_features(compose_config),
                'estimated_complexity': self._assess_complexity(compose_config)
            }
        )
    
    def _apply_security_hardening(self, config: Dict):
        """Apply enterprise security best practices."""
        for service_name, service in config['services'].items():
            # Non-root users
            if 'user' not in service:
                service['user'] = '1001:1001'
            
            # Security options
            service.setdefault('security_opt', []).append('no-new-privileges:true')
            
            # Health checks
            if 'healthcheck' not in service:
                service['healthcheck'] = self._generate_health_check(service_name)
```

#### Ansible Template Engine (`src/web_research/template_engines/ansible_engine.py`)
```python
class AnsibleTemplateEngine(BaseTemplateEngine):
    """AI-powered Ansible playbook generation."""
    
    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """Generate comprehensive Ansible automation."""
        
        # 1. Analyze target environment
        target_os = self._detect_target_os(context)
        
        # 2. Build playbook structure
        playbook = {
            'name': f"Deploy {context.technology}",
            'hosts': self._determine_host_groups(context),
            'become': True,
            'vars': self._generate_variables(context),
            'tasks': []
        }
        
        # 3. Generate installation tasks
        install_tasks = await self._generate_install_tasks(context, target_os)
        playbook['tasks'].extend(install_tasks)
        
        # 4. Add configuration tasks
        config_tasks = await self._generate_config_tasks(context)
        playbook['tasks'].extend(config_tasks)
        
        # 5. Security hardening
        security_tasks = self._generate_security_tasks(context, target_os)
        playbook['tasks'].extend(security_tasks)
        
        # 6. Service management
        service_tasks = self._generate_service_tasks(context)
        playbook['tasks'].extend(service_tasks)
        
        # 7. Render final playbook
        template_content = self._render_ansible_yaml([playbook])
        
        return TemplateResult(
            content=template_content,
            confidence_score=self._calculate_ansible_confidence(context),
            metadata={
                'tasks_generated': len(playbook['tasks']),
                'target_os': target_os,
                'idempotency_score': self._assess_idempotency(playbook)
            }
        )
```

### 4. Web Research Integration

#### Web Researcher (`src/web_research/web_researcher.py`)
```python
class WebResearcher:
    """Intelligent web research for technology discovery."""
    
    def __init__(self):
        self.search_orchestrator = MultiProviderSearchOrchestrator()
        self.cache_manager = ResearchCacheManager()
        self.validator = ResearchValidator()
    
    async def research_technologies(self, 
                                  technologies: List[str]) -> ResearchData:
        """Research latest best practices and configurations."""
        
        research_results = {}
        
        for tech in technologies:
            # Check cache first
            cached_result = await self.cache_manager.get(tech)
            if cached_result and not cached_result.is_expired():
                research_results[tech] = cached_result
                continue
            
            # Perform fresh research
            search_queries = self._generate_search_queries(tech)
            
            search_results = await self.search_orchestrator.search_multiple(
                search_queries
            )
            
            # Extract and validate information
            tech_info = await self._extract_technology_info(
                tech, search_results
            )
            
            # Validate quality
            validated_info = await self.validator.validate_research(tech_info)
            
            # Cache results
            await self.cache_manager.store(tech, validated_info)
            
            research_results[tech] = validated_info
        
        return ResearchData(
            technologies=research_results,
            research_timestamp=datetime.now(),
            confidence_score=self._calculate_research_confidence(research_results)
        )
    
    def _generate_search_queries(self, technology: str) -> List[str]:
        """Generate targeted search queries for technology research."""
        return [
            f"{technology} best practices 2024",
            f"{technology} production deployment guide",
            f"{technology} security configuration",
            f"{technology} performance optimization",
            f"{technology} docker compose example",
            f"{technology} ansible playbook automation"
        ]
```

### 5. CLI Interface Implementation

#### Traditional CLI (`main.py`)
```python
def create_cli_parser() -> argparse.ArgumentParser:
    """Create comprehensive CLI parser with all options."""
    parser = argparse.ArgumentParser(
        description="Advanced Prompt Engineering CLI for enterprise development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --tech python fastapi --task "REST API development"
  %(prog)s --example python-api --format json
  %(prog)s --interactive
        """
    )
    
    # Core options
    parser.add_argument('--tech', nargs='+', 
                       help='Technologies to include in prompt')
    parser.add_argument('--task', 
                       help='Task description')
    parser.add_argument('--example', 
                       help='Use predefined example')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive mode')
    
    # Output options  
    parser.add_argument('--format', choices=['text', 'json', 'markdown'],
                       default='text', help='Output format')
    parser.add_argument('--output', 
                       help='Output file path')
    
    # Advanced options
    parser.add_argument('--template',
                       help='Specific template to use')
    parser.add_argument('--description',
                       help='Detailed task description')
    parser.add_argument('--requirements',
                       help='Specific requirements')
    
    return parser

async def main():
    """Main CLI entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Initialize components
    knowledge_manager = KnowledgeManager()
    prompt_generator = PromptGenerator(knowledge_manager)
    
    if args.interactive:
        result = await interactive_mode(prompt_generator)
    elif args.example:
        result = generate_from_example(prompt_generator, args.example)
    else:
        result = prompt_generator.generate_prompt(
            technologies=args.tech or [],
            task_description=args.task or "",
            template_name=args.template
        )
    
    # Output handling
    output_handler = OutputHandler(args.format)
    await output_handler.write_result(result, args.output)
```

#### Modern AI CLI (`main_modern.py`)
```python
async def main_modern():
    """Modern AI-powered CLI entry point."""
    parser = create_modern_cli_parser()
    args = parser.parse_args()
    
    # Initialize AI components
    modern_generator = ModernPromptGenerator()
    
    if args.interactive:
        result = await ai_interactive_mode(modern_generator)
    elif args.list_engines:
        list_available_engines()
    else:
        result = await modern_generator.generate_with_research(
            technology=args.technology,
            description=args.description,
            evaluate=args.evaluate
        )
        
        # Display results
        display_enhanced_result(result)
        
        if args.evaluate and result.evaluation:
            display_evaluation_report(result.evaluation)
```

---

## 🎨 EXPECTED OUTPUT STRUCTURE

### Generated Template Example
```yaml
# Example Docker Compose Output
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
    security_opt:
      - no-new-privileges:true
    networks:
      - app_network

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
    user: "999:999"
    security_opt:
      - no-new-privileges:true
    networks:
      - app_network

networks:
  app_network:
    driver: bridge

volumes:
  postgres_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### Evaluation Report Output
```
📊 Production Readiness Report
==============================
Overall Score: 0.847/1.0
Security Score: 0.912 (Excellent)
Performance Score: 0.784 (Good)
Reliability Score: 0.856 (Excellent)
Deployment Readiness: READY

🛡️ Security Analysis:
✅ Non-root user execution
✅ Secret management via files
✅ Network isolation configured
✅ Security options enabled

🚨 Recommendations:
• Add resource limits for production
• Implement backup strategy
• Configure monitoring stack
```

---

## 🏆 SUCCESS CRITERIA

### Functional Requirements
- ✅ **Traditional CLI**: Generate prompts from technology stacks
- ✅ **AI-Enhanced CLI**: Generate templates with web research
- ✅ **Template Engines**: Docker, Ansible, Patroni generation
- ✅ **Evaluation Framework**: Production readiness assessment
- ✅ **Web Research**: Automatic technology discovery
- ✅ **Quality Assurance**: Enterprise-grade code evaluation

### Quality Standards
- ✅ **Security**: 90%+ security best practices compliance
- ✅ **Documentation**: 95%+ comprehensive documentation coverage
- ✅ **Production Readiness**: 85%+ enterprise deployment standards
- ✅ **Performance**: <1s prompt generation, <15s AI template generation
- ✅ **Reliability**: Comprehensive error handling and recovery

### Enterprise Features
- ✅ **Compliance**: SOX, PCI-DSS, HIPAA, GDPR validation
- ✅ **Scalability**: Multi-provider search, caching, async operations
- ✅ **Maintainability**: Modular architecture, comprehensive testing
- ✅ **Extensibility**: Plugin architecture for new engines and evaluators

---

## 🔧 IMPLEMENTATION STEPS

### Phase 1: Core Infrastructure (Week 1-2)
1. **Project Setup**: Directory structure, dependencies, configuration
2. **Base Classes**: Result types, configuration classes, interfaces
3. **Traditional CLI**: Basic prompt generation with templates
4. **Knowledge Management**: Load and manage best practices/tools
5. **Template System**: Jinja2 integration with intelligent selection

### Phase 2: AI Enhancement (Week 3-4)
6. **Web Research**: Multi-provider search and content extraction
7. **Template Engines**: Docker, Ansible, Patroni AI generators
8. **Modern CLI**: AI-powered template generation interface
9. **Caching System**: Intelligent research result caching
10. **Technology Detection**: Automatic tech stack analysis

### Phase 3: Evaluation Framework (Week 5-6)
11. **Production Readiness**: 5-dimensional enterprise assessment
12. **Security Analysis**: Pattern-based vulnerability detection
13. **HumanEval-DevOps**: Standardized benchmarking framework
14. **Compliance Validation**: Enterprise standards verification
15. **Quality Metrics**: Performance and reliability measurement

### Phase 4: Integration & Polish (Week 7-8)
16. **End-to-End Integration**: Complete workflow implementation
17. **Comprehensive Testing**: Unit, integration, and enterprise tests
18. **Documentation**: Complete usage guides and examples
19. **Performance Optimization**: Caching, async operations
20. **Quality Assurance**: Final evaluation and refinement

---

## 📚 QUALITY CHECKLIST

### Code Quality
- [ ] **Type Safety**: Complete type annotations with mypy validation
- [ ] **Error Handling**: Comprehensive Result types, no silent failures
- [ ] **Testing**: 90%+ test coverage with pytest
- [ ] **Documentation**: Docstrings for all public APIs
- [ ] **Code Style**: Black formatting, pylint compliance

### Enterprise Standards
- [ ] **Security**: Non-root execution, secret management, input validation
- [ ] **Performance**: <1s traditional, <15s AI generation, caching
- [ ] **Reliability**: Graceful degradation, error recovery
- [ ] **Maintainability**: Modular design, clear interfaces
- [ ] **Compliance**: Enterprise security standards validation

### User Experience
- [ ] **CLI Usability**: Intuitive commands, helpful error messages
- [ ] **Documentation**: Complete usage guides with examples
- [ ] **Output Quality**: Professional, production-ready templates
- [ ] **Evaluation Feedback**: Actionable recommendations
- [ ] **Performance**: Responsive, efficient operations

---

## 🚀 DEPLOYMENT CHECKLIST

### Production Readiness
- [ ] **Dependencies**: All requirements.txt complete and pinned
- [ ] **Configuration**: Environment-based configuration management
- [ ] **Logging**: Structured logging for debugging and monitoring
- [ ] **Error Handling**: Graceful failure modes and recovery
- [ ] **Performance**: Benchmarked and optimized for enterprise use

### Quality Assurance
- [ ] **Testing**: Complete test suite with CI/CD integration
- [ ] **Security**: Security audit and vulnerability assessment
- [ ] **Documentation**: User guides, API docs, examples
- [ ] **Evaluation**: Self-evaluation using built-in frameworks
- [ ] **Compliance**: Enterprise standard validation

---

## 🎯 FINAL VALIDATION

When implementation is complete, validate using the tool itself:

```bash
# Test traditional prompt generation
python main.py --tech python cli jinja2 --task "Advanced Prompt Engineering CLI"

# Test AI-powered generation with evaluation
python main_modern.py --technology "python asyncio evaluation" \
  --description "enterprise CLI with AI template generation" --evaluate

# Run comprehensive evaluation
python test_evaluation_frameworks.py

# Generate project documentation
python main.py --tech documentation --task "comprehensive project guide" \
  --format markdown --output PROJECT_COMPLETE.md
```

---

**Meta-Generated by**: Advanced Prompt Engineering CLI  
**Confidence Score**: 0.94/1.0  
**Complexity**: Expert Enterprise Level  
**Estimated Implementation**: 6-8 weeks  
**Team Size**: 2-3 senior developers  

This prompt demonstrates the tool's capability to generate comprehensive, enterprise-grade project specifications that can recreate the entire system from scratch.