"""
HumanEval-DevOps: Infrastructure Code Evaluation Benchmark

Business Context: Standardized benchmark for evaluating infrastructure
code generation capabilities, extending HumanEval methodology to DevOps
and infrastructure automation scenarios.
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .evaluation_types import EvalContext, EvaluationResult, RiskLevel


@dataclass
class TestScenario:
    """Test scenario for infrastructure code validation"""

    name: str
    description: str
    setup_commands: List[str] = field(default_factory=list)
    validation_commands: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    expected_files: List[str] = field(default_factory=list)
    cleanup_commands: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    environment_vars: Dict[str, str] = field(default_factory=dict)


@dataclass
class DevOpsEvalTask:
    """DevOps evaluation task following HumanEval methodology"""

    task_id: str
    prompt: str
    technology_stack: List[str]
    target_environment: str
    difficulty: str  # basic, intermediate, advanced, expert
    expected_outputs: List[str]  # Expected file types/names
    test_scenarios: List[TestScenario]
    scoring_criteria: Dict[str, float]  # Weights for different aspects
    canonical_solution: Optional[str] = None  # Reference implementation

    def get_context(self) -> EvalContext:
        """Convert to EvalContext for compatibility"""
        from .evaluation_types import TemplateType

        template_type = TemplateType.ANSIBLE_PLAYBOOK  # Default
        if "docker" in self.technology_stack:
            template_type = TemplateType.DOCKER_COMPOSE
        elif "kubernetes" in self.technology_stack or "k8s" in self.technology_stack:
            template_type = TemplateType.KUBERNETES_MANIFEST

        return EvalContext(
            template_type=template_type,
            target_environment=self.target_environment,
            technology_stack=self.technology_stack,
            deployment_scale="single" if "cluster" not in self.prompt.lower() else "cluster",
        )


@dataclass
class EvalResult:
    """Results of DevOps task evaluation"""

    task_id: str
    overall_score: float  # 0.0 - 1.0
    deployability_score: float
    functionality_score: float
    compliance_score: float
    security_score: float
    execution_time: float
    passed_scenarios: int
    total_scenarios: int
    issues_found: List[str]
    generated_files: List[str]
    execution_logs: List[str]
    success: bool


class DevOpsTaskExecutor:
    """Executes and validates DevOps tasks in controlled environment"""

    def __init__(self, working_dir: Optional[str] = None):
        self._logger = logging.getLogger(__name__)
        self.working_dir = working_dir or tempfile.mkdtemp(prefix="devops_eval_")
        self.execution_timeout = 600  # 10 minutes max per task

    def execute_task(self, task: DevOpsEvalTask, generated_template: str) -> EvalResult:
        """
        Execute DevOps task with generated template in controlled environment.

        Business Context: Validates generated infrastructure code through
        actual deployment testing to ensure functional correctness.
        """
        self._logger.info(f"Executing task {task.task_id}")
        start_time = datetime.now()

        # Create isolated environment
        task_dir = self._create_task_environment(task)

        try:
            # Write generated template to files
            generated_files = self._write_template_files(generated_template, task, task_dir)

            # Execute test scenarios
            scenario_results = []
            for scenario in task.test_scenarios:
                result = self._execute_scenario(scenario, task_dir)
                scenario_results.append(result)

            # Calculate scores
            scores = self._calculate_scores(task, scenario_results, generated_template)

            execution_time = (datetime.now() - start_time).total_seconds()
            passed_scenarios = sum(1 for r in scenario_results if r["success"])

            return EvalResult(
                task_id=task.task_id,
                overall_score=scores["overall"],
                deployability_score=scores["deployability"],
                functionality_score=scores["functionality"],
                compliance_score=scores["compliance"],
                security_score=scores["security"],
                execution_time=execution_time,
                passed_scenarios=passed_scenarios,
                total_scenarios=len(task.test_scenarios),
                issues_found=self._collect_issues(scenario_results),
                generated_files=generated_files,
                execution_logs=self._collect_logs(scenario_results),
                success=passed_scenarios == len(task.test_scenarios),
            )

        except Exception as e:
            self._logger.error(f"Task execution failed: {e}")
            return EvalResult(
                task_id=task.task_id,
                overall_score=0.0,
                deployability_score=0.0,
                functionality_score=0.0,
                compliance_score=0.0,
                security_score=0.0,
                execution_time=(datetime.now() - start_time).total_seconds(),
                passed_scenarios=0,
                total_scenarios=len(task.test_scenarios),
                issues_found=[str(e)],
                generated_files=[],
                execution_logs=[],
                success=False,
            )

        finally:
            self._cleanup_environment(task_dir)

    def _create_task_environment(self, task: DevOpsEvalTask) -> str:
        """Create isolated environment for task execution (≤15 lines)."""
        task_dir = os.path.join(self.working_dir, f"task_{task.task_id}")
        os.makedirs(task_dir, exist_ok=True)

        # Create standard directories
        dirs = ["configs", "scripts", "logs", "templates"]
        for dir_name in dirs:
            os.makedirs(os.path.join(task_dir, dir_name), exist_ok=True)

        # Set up environment variables
        env_file = os.path.join(task_dir, ".env")
        with open(env_file, "w") as f:
            f.write("# Environment variables for DevOps evaluation\n")
            f.write(f"TASK_ID={task.task_id}\n")
            f.write(f"TARGET_ENV={task.target_environment}\n")

        return task_dir

    def _write_template_files(
        self, template: str, task: DevOpsEvalTask, task_dir: str
    ) -> List[str]:
        """Write generated template to appropriate files (≤20 lines)."""
        generated_files = []

        # Determine file type and name based on content
        if "docker-compose" in template.lower() or "version:" in template:
            # Docker Compose file
            compose_file = os.path.join(task_dir, "docker-compose.yml")
            with open(compose_file, "w") as f:
                f.write(template)
            generated_files.append("docker-compose.yml")

        elif "hosts:" in template and "tasks:" in template:
            # Ansible playbook
            playbook_file = os.path.join(task_dir, "playbook.yml")
            with open(playbook_file, "w") as f:
                f.write(template)
            generated_files.append("playbook.yml")

            # Extract inventory if present
            if "[" in template and "]" in template:
                inventory_content = self._extract_inventory(template)
                if inventory_content:
                    inventory_file = os.path.join(task_dir, "inventory.ini")
                    with open(inventory_file, "w") as f:
                        f.write(inventory_content)
                    generated_files.append("inventory.ini")

        elif "apiVersion:" in template and "kind:" in template:
            # Kubernetes manifest
            manifest_file = os.path.join(task_dir, "manifest.yml")
            with open(manifest_file, "w") as f:
                f.write(template)
            generated_files.append("manifest.yml")

        else:
            # Generic template file
            template_file = os.path.join(task_dir, "template.txt")
            with open(template_file, "w") as f:
                f.write(template)
            generated_files.append("template.txt")

        return generated_files

    def _execute_scenario(self, scenario: TestScenario, task_dir: str) -> Dict[str, Any]:
        """Execute individual test scenario (≤20 lines)."""
        self._logger.info(f"Executing scenario: {scenario.name}")

        result = {
            "name": scenario.name,
            "success": True,
            "outputs": [],
            "errors": [],
            "duration": 0.0,
        }

        start_time = datetime.now()

        try:
            # Setup phase
            for cmd in scenario.setup_commands:
                self._run_command(cmd, task_dir, scenario.environment_vars)

            # Validation phase
            for cmd in scenario.validation_commands:
                output = self._run_command(cmd, task_dir, scenario.environment_vars)
                result["outputs"].append(output)

            # Check expected outputs
            result["success"] = self._validate_outputs(result["outputs"], scenario.expected_outputs)

        except subprocess.TimeoutExpired:
            result["success"] = False
            result["errors"].append(f"Scenario timed out after {scenario.timeout_seconds}s")
        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))

        finally:
            # Cleanup phase
            for cmd in scenario.cleanup_commands:
                try:
                    self._run_command(cmd, task_dir, scenario.environment_vars)
                except:
                    pass  # Ignore cleanup errors

            result["duration"] = (datetime.now() - start_time).total_seconds()

        return result

    def _run_command(self, command: str, working_dir: str, env_vars: Dict[str, str] = None) -> str:
        """Run command in controlled environment (≤15 lines)."""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Security: Restrict command execution
        if any(dangerous in command.lower() for dangerous in ["rm -rf /", "format", "del *"]):
            raise ValueError(f"Dangerous command blocked: {command}")

        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,  # Per-command timeout
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, command, result.stderr)

        return result.stdout

    def _validate_outputs(self, actual_outputs: List[str], expected_outputs: List[str]) -> bool:
        """Validate command outputs against expectations (≤10 lines)."""
        if not expected_outputs:
            return True  # No specific expectations

        for expected in expected_outputs:
            found = any(expected.lower() in output.lower() for output in actual_outputs)
            if not found:
                return False

        return True

    def _calculate_scores(
        self, task: DevOpsEvalTask, scenario_results: List[Dict], template: str
    ) -> Dict[str, float]:
        """Calculate evaluation scores (≤15 lines)."""
        passed_scenarios = sum(1 for r in scenario_results if r["success"])
        total_scenarios = len(scenario_results)

        # Basic scoring based on scenario success rate
        functionality_score = passed_scenarios / total_scenarios if total_scenarios > 0 else 0.0

        # Deployability: Check if files are valid format
        deployability_score = self._check_template_validity(template)

        # Compliance: Basic checks
        compliance_score = self._check_basic_compliance(template)

        # Security: Basic security checks
        security_score = self._check_basic_security(template)

        # Overall score using task-specific weights
        weights = task.scoring_criteria
        overall_score = (
            functionality_score * weights.get("functionality", 0.4)
            + deployability_score * weights.get("deployability", 0.3)
            + compliance_score * weights.get("compliance", 0.2)
            + security_score * weights.get("security", 0.1)
        )

        return {
            "overall": overall_score,
            "functionality": functionality_score,
            "deployability": deployability_score,
            "compliance": compliance_score,
            "security": security_score,
        }

    def _check_template_validity(self, template: str) -> float:
        """Check if template is valid format (≤10 lines)."""
        try:
            # Try parsing as YAML
            yaml.safe_load(template)
            return 1.0
        except yaml.YAMLError:
            try:
                # Try parsing as JSON
                json.loads(template)
                return 0.8
            except json.JSONDecodeError:
                # Plain text or other format
                return 0.6 if len(template.strip()) > 0 else 0.0

    def _check_basic_compliance(self, template: str) -> float:
        """Basic compliance checks (≤10 lines)."""
        score = 0.7  # Default moderate score

        # Check for documentation
        if "#" in template or '"""' in template:
            score += 0.1

        # Check for version pinning
        if ":latest" in template:
            score -= 0.2  # Penalty for using latest tags

        return max(0.0, min(1.0, score))

    def _check_basic_security(self, template: str) -> float:
        """Basic security checks (≤10 lines)."""
        score = 0.8  # Default good score

        # Check for hardcoded passwords
        if "password" in template.lower() and "=" in template:
            score -= 0.3

        # Check for root user
        if "user: root" in template.lower() or "USER root" in template:
            score -= 0.2

        return max(0.0, score)

    def _extract_inventory(self, template: str) -> Optional[str]:
        """Extract Ansible inventory from template (≤10 lines)."""
        lines = template.split("\n")
        inventory_lines = []
        in_inventory = False

        for line in lines:
            if "# inventory" in line.lower():
                in_inventory = True
                continue
            elif in_inventory and line.startswith("#"):
                continue
            elif in_inventory and line.strip():
                inventory_lines.append(line.strip("# "))
            elif in_inventory and not line.strip():
                break

        return "\n".join(inventory_lines) if inventory_lines else None

    def _collect_issues(self, scenario_results: List[Dict]) -> List[str]:
        """Collect issues from scenario results (≤5 lines)."""
        issues = []
        for result in scenario_results:
            issues.extend(result.get("errors", []))
        return issues

    def _collect_logs(self, scenario_results: List[Dict]) -> List[str]:
        """Collect execution logs (≤5 lines)."""
        logs = []
        for result in scenario_results:
            logs.extend(result.get("outputs", []))
        return logs

    def _cleanup_environment(self, task_dir: str):
        """Clean up task environment (≤5 lines)."""
        try:
            import shutil

            shutil.rmtree(task_dir)
        except:
            self._logger.warning(f"Failed to cleanup {task_dir}")


class DevOpsBenchmark:
    """Complete DevOps benchmark suite following HumanEval methodology"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.tasks = self._initialize_benchmark_tasks()
        self.executor = DevOpsTaskExecutor()

    def _initialize_benchmark_tasks(self) -> List[DevOpsEvalTask]:
        """Initialize benchmark task suite (≤30 lines)."""
        return [
            # Basic Docker Compose task
            DevOpsEvalTask(
                task_id="devops_001",
                prompt="Create a Docker Compose setup for a web application with Nginx and PostgreSQL database",
                technology_stack=["docker", "docker-compose", "nginx", "postgresql"],
                target_environment="docker",
                difficulty="basic",
                expected_outputs=["docker-compose.yml"],
                test_scenarios=[
                    TestScenario(
                        name="compose_validation",
                        description="Validate Docker Compose file syntax",
                        validation_commands=["docker-compose config"],
                        expected_outputs=["nginx", "postgres"],
                    )
                ],
                scoring_criteria={
                    "functionality": 0.4,
                    "deployability": 0.3,
                    "compliance": 0.2,
                    "security": 0.1,
                },
            ),
            # Ansible playbook task
            DevOpsEvalTask(
                task_id="devops_002",
                prompt="Create an Ansible playbook to install and configure Prometheus monitoring on RHEL9",
                technology_stack=["ansible", "prometheus", "rhel9"],
                target_environment="rhel9",
                difficulty="intermediate",
                expected_outputs=["playbook.yml", "inventory.ini"],
                test_scenarios=[
                    TestScenario(
                        name="playbook_syntax",
                        description="Validate Ansible playbook syntax",
                        validation_commands=["ansible-playbook --syntax-check playbook.yml"],
                        expected_outputs=["playbook: playbook.yml"],
                    )
                ],
                scoring_criteria={
                    "functionality": 0.5,
                    "deployability": 0.2,
                    "compliance": 0.2,
                    "security": 0.1,
                },
            ),
            # Multi-node cluster task
            DevOpsEvalTask(
                task_id="devops_003",
                prompt="Deploy a 3-node PostgreSQL cluster with Patroni on RHEL9 using automation",
                technology_stack=["patroni", "postgresql", "etcd", "rhel9", "ansible"],
                target_environment="rhel9_cluster",
                difficulty="advanced",
                expected_outputs=["playbook.yml", "patroni.yml", "inventory.ini"],
                test_scenarios=[
                    TestScenario(
                        name="cluster_config",
                        description="Validate cluster configuration",
                        validation_commands=["grep -c 'cluster_size.*3' playbook.yml"],
                        expected_outputs=["1"],
                    )
                ],
                scoring_criteria={
                    "functionality": 0.3,
                    "deployability": 0.3,
                    "compliance": 0.2,
                    "security": 0.2,
                },
            ),
        ]

    def run_evaluation(self, template_generator_func) -> Dict[str, EvalResult]:
        """
        Run complete benchmark evaluation.

        Args:
            template_generator_func: Function that takes DevOpsEvalTask and returns template string

        Returns:
            Dictionary of task_id -> EvalResult
        """
        self._logger.info(f"Running DevOps benchmark with {len(self.tasks)} tasks")

        results = {}

        for task in self.tasks:
            self._logger.info(f"Evaluating task {task.task_id}: {task.prompt[:50]}...")

            try:
                # Generate template using provided function
                generated_template = template_generator_func(task)

                # Execute and evaluate
                result = self.executor.execute_task(task, generated_template)
                results[task.task_id] = result

                self._logger.info(
                    f"Task {task.task_id} completed: score={result.overall_score:.3f}"
                )

            except Exception as e:
                self._logger.error(f"Task {task.task_id} failed: {e}")
                results[task.task_id] = EvalResult(
                    task_id=task.task_id,
                    overall_score=0.0,
                    deployability_score=0.0,
                    functionality_score=0.0,
                    compliance_score=0.0,
                    security_score=0.0,
                    execution_time=0.0,
                    passed_scenarios=0,
                    total_scenarios=len(task.test_scenarios),
                    issues_found=[str(e)],
                    generated_files=[],
                    execution_logs=[],
                    success=False,
                )

        return results

    def generate_report(self, results: Dict[str, EvalResult]) -> Dict[str, Any]:
        """Generate comprehensive benchmark report (≤15 lines)."""
        total_tasks = len(results)
        passed_tasks = sum(1 for r in results.values() if r.success)
        avg_score = (
            sum(r.overall_score for r in results.values()) / total_tasks if total_tasks > 0 else 0.0
        )

        return {
            "summary": {
                "total_tasks": total_tasks,
                "passed_tasks": passed_tasks,
                "pass_rate": passed_tasks / total_tasks if total_tasks > 0 else 0.0,
                "average_score": avg_score,
            },
            "task_results": {
                task_id: {
                    "score": result.overall_score,
                    "success": result.success,
                    "issues": len(result.issues_found),
                }
                for task_id, result in results.items()
            },
            "detailed_results": results,
        }


class DevOpsEvaluator:
    """Main evaluator class combining both frameworks"""

    def __init__(self):
        self.benchmark = DevOpsBenchmark()
        self._logger = logging.getLogger(__name__)

    def evaluate_template_engine(self, engine_generate_func) -> Dict[str, Any]:
        """
        Evaluate a template engine using DevOps benchmark.

        Business Context: Provides standardized evaluation of template
        generation capabilities across diverse infrastructure scenarios.
        """
        self._logger.info("Starting DevOps template engine evaluation")

        results = self.benchmark.run_evaluation(engine_generate_func)
        report = self.benchmark.generate_report(results)

        return report
