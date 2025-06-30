# QUALITY GATES AUTOMATION - ENTERPRISE GRADE
.PHONY: help install quality test coverage lint type-check complexity doc-coverage format clean all

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Quality Gates Automation$(NC)"
	@echo "========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

# ==================== QUALITY GATES ====================

quality: ## Run all quality checks (FAIL FAST)
	@echo "$(BLUE)Running comprehensive quality gates...$(NC)"
	@$(MAKE) format-check
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) complexity
	@$(MAKE) doc-coverage
	@$(MAKE) test
	@echo "$(GREEN)✓ ALL QUALITY GATES PASSED$(NC)"

test: ## Run tests with coverage enforcement (≥80%)
	@echo "$(BLUE)Running tests with coverage enforcement...$(NC)"
	pytest tests/ --cov=src --cov-fail-under=80 --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Tests passed with ≥80% coverage$(NC)"

coverage: ## Generate detailed coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(YELLOW)Coverage report: htmlcov/index.html$(NC)"

lint: ## Run pylint with strict rules
	@echo "$(BLUE)Running pylint...$(NC)"
	pylint src/ --fail-under=8.0 --rcfile=pyproject.toml
	@echo "$(GREEN)✓ Pylint passed$(NC)"

type-check: ## Run mypy type checking
	@echo "$(BLUE)Running mypy type checking...$(NC)"
	mypy src/ --config-file=pyproject.toml --strict
	@echo "$(GREEN)✓ Type checking passed$(NC)"

complexity: ## Check code complexity (CC ≤ 10, MI > B)
	@echo "$(BLUE)Checking code complexity...$(NC)"
	radon cc src/ --min B --show-complexity --average
	radon mi src/ --min B --show
	xenon src/ --max-absolute B --max-modules A --max-average A
	@echo "$(GREEN)✓ Complexity within limits$(NC)"

doc-coverage: ## Check documentation coverage (≥90%)
	@echo "$(BLUE)Checking documentation coverage...$(NC)"
	interrogate src/ --fail-under 90 --verbose 2
	@echo "$(GREEN)✓ Documentation coverage ≥90%$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black src/ tests/
	isort src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check if code is properly formatted
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check src/ tests/
	isort --check-only src/ tests/
	@echo "$(GREEN)✓ Code formatting is correct$(NC)"

# ==================== PERFORMANCE GATES ====================

performance-test: ## Run performance tests with thresholds
	@echo "$(BLUE)Running performance tests...$(NC)"
	pytest tests/test_performance.py -v --tb=short
	@echo "$(GREEN)✓ Performance tests passed$(NC)"

benchmark: ## Run benchmarks  
	@echo "$(BLUE)Running benchmarks...$(NC)"
	pytest tests/ -k "benchmark" --benchmark-only --benchmark-sort=mean
	@echo "$(GREEN)✓ Benchmarks completed$(NC)"

# ==================== INTEGRATION TESTS ====================

integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/test_integration*.py -v --tb=short
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

property: ## Run property-based tests
	@echo "$(BLUE)Running property-based tests...$(NC)"
	pytest tests/ -m property -v --tb=short
	@echo "$(GREEN)✓ Property-based tests passed$(NC)"

# ==================== CONTINUOUS QUALITY ====================

pre-commit: ## Run all checks before commit
	@echo "$(BLUE)Pre-commit quality checks...$(NC)"
	@$(MAKE) format
	@$(MAKE) quality
	@echo "$(GREEN)✓ Ready for commit$(NC)"

ci: ## Continuous Integration checks
	@echo "$(BLUE)CI Quality Pipeline...$(NC)"
	@$(MAKE) install
	@$(MAKE) quality
	@$(MAKE) integration
	@$(MAKE) performance-test
	@echo "$(GREEN)✓ CI Pipeline passed$(NC)"

# ==================== CLEANUP ====================

clean: ## Clean generated files
	@echo "$(BLUE)Cleaning generated files...$(NC)"
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

# ==================== DEVELOPMENT ====================

dev-setup: ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@$(MAKE) install
	@$(MAKE) format
	@echo "$(GREEN)✓ Development environment ready$(NC)"

quick-check: ## Quick quality check (fast)
	@echo "$(BLUE)Quick quality check...$(NC)"
	black --check src/ tests/
	mypy src/ --config-file=pyproject.toml
	pytest tests/ --cov=src --cov-fail-under=80 -q
	@echo "$(GREEN)✓ Quick check passed$(NC)"

# Default target
all: quality ## Run all quality checks (default)