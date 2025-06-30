# Web Research System - Refactoring TODO

## 🚧 Status: PARTIAL COMPLETION (70% done)

### ✅ Completed (following code-best-practice.md):
- [x] DynamicTemplateGenerator refactored (342 lines vs 1261, -73%)
- [x] PatroniTemplateEngine implemented with RHEL9/Ubuntu22/Debian11 support
- [x] Base template engine architecture (interfaces, factory pattern)
- [x] Enterprise dependency injection container
- [x] Circuit breaker pattern with exponential backoff
- [x] Multi-provider search orchestration
- [x] Research validation with ML-based quality assessment
- [x] Template caching with versioning
- [x] CLI specific options integration
- [x] Core web research workflow

### ❌ Remaining Tasks (CRITICAL for production):

#### 1. Template Engines (Single Responsibility, ≤20 lines each)
- [ ] KubernetesTemplateEngine - for `--orchestrator k8s`
- [ ] AnsibleTemplateEngine - for `--ci-cd-platform ansible`  
- [ ] DockerTemplateEngine - for `--container-runtime docker`
- [ ] InfrastructureTemplateEngine - for `--cloud-provider aws/azure/gcp`

#### 2. Integration Fixes
- [ ] Fix import errors in main.py (`from .template_engines.base_engine import TemplateContext`)
- [ ] Add proper async error handling in CLI
- [ ] Fix TYPE_CHECKING imports for SpecificOptions
- [ ] Update template_factory registration for all engines

#### 3. Quality Assurance
- [ ] Unit tests for each template engine (following TDD)
- [ ] Integration test for full workflow (CLI -> Research -> Template)
- [ ] Performance tests (≤100ms per template generation)
- [ ] Type checking validation

#### 4. Documentation
- [ ] Update USAGE.md with new specific options
- [ ] Add engine development guide
- [ ] Create troubleshooting section

## 🎯 Expected Outcomes:

When completed, the command:
```bash
python main.py --tech patroni postgresql etcd --task "database cluster" \
  --distro rhel9 --db-engine patroni --cluster-size 3 \
  --monitoring-stack prometheus nagios --auto-research
```

Should generate a **context-specific** template with:
- ✅ RHEL9-specific installation commands (NOT Ubuntu/Docker)
- ✅ 3-node Patroni cluster configuration  
- ✅ Prometheus + Nagios monitoring integration
- ✅ NO generic/hardcoded examples
- ✅ 1800-2000 character focused template (vs 3500+ generic)

## 🔧 Quick Fix Commands:

```bash
# Complete remaining engines
cd src/web_research/template_engines/
touch kubernetes_engine.py ansible_engine.py docker_engine.py infrastructure_engine.py

# Fix imports
grep -r "from .template_engines" ../.. --include="*.py"

# Test integration 
python main.py --tech patroni --distro rhel9 --db-engine patroni --auto-research
```

## 📋 Definition of Done:
- [ ] All 4 template engines implemented
- [ ] No import errors in CLI
- [ ] Context-specific examples generated correctly
- [ ] No hardcoded technology examples (Docker when not requested)
- [ ] All functions ≤20 lines following best practices
- [ ] Integration test passes end-to-end