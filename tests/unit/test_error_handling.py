"""
Comprehensive tests for error handling and edge cases.

Tests error conditions, validation failures, resource constraints,
and system resilience across all components.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import List
from unittest.mock import Mock, mock_open, patch

import pytest

from src.events import Event, EventBus, EventType
from src.knowledge_manager import KnowledgeManager
from src.prompt_config import PromptConfig
from src.prompt_generator import PromptGenerator
from src.utils import load_json_file, read_text_file, safe_path_join


class TestErrorHandlingValidation:
    """Test validation and error handling in core components."""

    def test_prompt_config_validation_errors(self):
        """Test PromptConfig validation error scenarios."""
        # Test empty technologies
        with pytest.raises(ValueError, match="At least one technology must be specified"):
            PromptConfig(
                technologies=[],
                task_type="valid task",
                code_requirements="valid requirements that are long enough",
            )

        # Test short task type
        with pytest.raises(ValueError, match="Task type must be descriptive"):
            PromptConfig(
                technologies=["python"],
                task_type="ab",
                code_requirements="valid requirements that are long enough",
            )

        # Test short code requirements
        with pytest.raises(ValueError, match="Code requirements must be detailed"):
            PromptConfig(
                technologies=["python"], task_type="valid task type", code_requirements="short"
            )

        # Test invalid technology types
        with pytest.raises(TypeError):
            PromptConfig(
                technologies=["python", 123],  # Invalid type
                task_type="valid task",
                code_requirements="valid requirements",
            )

        # Test None values
        with pytest.raises(TypeError):
            PromptConfig(
                technologies=None, task_type="valid task", code_requirements="valid requirements"
            )

    def test_prompt_generator_initialization_errors(self, tmp_path):
        """Test PromptGenerator initialization error scenarios."""
        # Test with non-existent prompts directory
        with pytest.raises(FileNotFoundError):
            PromptGenerator("/non/existent/path", "config.json")

        # Test with non-existent config file
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            PromptGenerator(str(prompts_dir), "/non/existent/config.json")

        # Test with invalid config file format
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json content {")

        with pytest.raises(json.JSONDecodeError):
            PromptGenerator(str(prompts_dir), str(config_file))

        # Test with empty config file
        config_file.write_text("{}")
        generator = PromptGenerator(str(prompts_dir), str(config_file))

        # Should handle empty config gracefully
        assert generator is not None

    def test_knowledge_manager_file_access_errors(self, tmp_path):
        """Test KnowledgeManager file access error scenarios."""
        config_file = tmp_path / "config.json"
        config_data = {
            "python": {"best_practices": ["Nonexistent Practice"], "tools": ["Nonexistent Tool"]}
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Test missing best practice file
        with patch("src.knowledge_manager.logger") as mock_logger:
            result = km.get_best_practice_details("Nonexistent Practice")
            assert result is None
            mock_logger.warning.assert_called()

        # Test missing tool file
        with patch("src.knowledge_manager.logger") as mock_logger:
            result = km.get_tool_details("Nonexistent Tool")
            assert result is None
            mock_logger.warning.assert_called()

        # Test corrupted JSON file
        tools_dir = tmp_path / "knowledge_base" / "tools"
        tools_dir.mkdir(parents=True)

        corrupted_file = tools_dir / "corrupted.json"
        corrupted_file.write_text("{ invalid json")

        with patch("src.knowledge_manager.logger") as mock_logger:
            result = km.get_tool_details("corrupted")
            assert result is None
            mock_logger.error.assert_called()

    def test_template_rendering_error_recovery(self, tmp_path):
        """Test template rendering error recovery mechanisms."""
        # Setup basic environment
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        base_prompts_dir = prompts_dir / "base_prompts"
        base_prompts_dir.mkdir()

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create generic template
        generic_template = base_prompts_dir / "generic_code_prompt.txt"
        generic_template.write_text("Generic template: {{ role }} with {{ technologies }}")

        # Create template with syntax error
        bad_template = base_prompts_dir / "bad_template.txt"
        bad_template.write_text("{{ unclosed_variable")

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        config = PromptConfig(
            technologies=["python"],
            task_type="test error recovery",
            code_requirements="test template error handling gracefully",
            template_name="base_prompts/bad_template.txt",
        )

        with patch("src.prompt_generator.logger") as mock_logger:
            prompt = generator.generate_prompt(config)

            # Should log error
            mock_logger.error.assert_called()
            error_msg = mock_logger.error.call_args[0][0]
            assert "Template rendering error" in error_msg

            # Should still generate a prompt using fallback
            assert len(prompt) > 0
            assert "expert" in prompt.lower()  # From fallback template

    def test_circular_template_inheritance(self, tmp_path):
        """Test handling of circular template inheritance."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Create circular inheritance: A extends B, B extends A
        template_a = prompts_dir / "template_a.txt"
        template_a.write_text('{% extends "template_b.txt" %}\nTemplate A content')

        template_b = prompts_dir / "template_b.txt"
        template_b.write_text('{% extends "template_a.txt" %}\nTemplate B content')

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        config = PromptConfig(
            technologies=["python"],
            task_type="test circular inheritance",
            code_requirements="handle circular template inheritance properly",
            template_name="template_a.txt",
        )

        # Should handle circular inheritance error
        with patch("src.prompt_generator.logger") as mock_logger:
            prompt = generator.generate_prompt(config)

            # Should log error about template rendering
            mock_logger.error.assert_called()

            # Should still generate fallback content
            assert len(prompt) > 0


class TestResourceConstraints:
    """Test system behavior under resource constraints."""

    def test_large_knowledge_base_handling(self, tmp_path):
        """Test handling of very large knowledge base files."""
        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["Large Practice"], "tools": ["Large Tool"]}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        # Create very large best practice file
        large_content = "# Large Practice\n" + "This is a line of content.\n" * 10000
        (bp_dir / "large_practice.md").write_text(large_content)

        # Create large tool file
        large_tool_data = {
            "name": "Large Tool",
            "description": "A" * 100000,  # Very long description
            "features": ["feature" + str(i) for i in range(1000)],
        }
        with open(tools_dir / "large_tool.json", "w") as f:
            json.dump(large_tool_data, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Should handle large files without issues
        practice_details = km.get_best_practice_details("Large Practice")
        assert practice_details is not None
        assert len(practice_details) > 100000

        tool_details = km.get_tool_details("Large Tool")
        assert tool_details is not None
        assert len(tool_details["description"]) == 100000
        assert len(tool_details["features"]) == 1000

    def test_memory_efficient_caching(self, tmp_path):
        """Test that caching doesn't cause memory issues with repeated access."""
        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["Test Practice"], "tools": ["Test Tool"]}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        kb_dir = tmp_path / "knowledge_base"
        bp_dir = kb_dir / "best_practices"
        tools_dir = kb_dir / "tools"
        bp_dir.mkdir(parents=True)
        tools_dir.mkdir(parents=True)

        # Create test files
        (bp_dir / "test_practice.md").write_text("Test practice content")
        with open(tools_dir / "test_tool.json", "w") as f:
            json.dump({"name": "Test Tool", "description": "Test tool"}, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Access the same content many times
        with patch("src.knowledge_manager.read_text_file") as mock_read:
            mock_read.return_value = "Test practice content"

            # First access should read from file
            result1 = km.get_best_practice_details("Test Practice")
            assert mock_read.call_count == 1

            # Subsequent accesses should use cache
            for i in range(100):
                result = km.get_best_practice_details("Test Practice")
                assert result == result1

            # Should still only have called read_text_file once
            assert mock_read.call_count == 1

    def test_concurrent_access_safety(self, tmp_path):
        """Test thread safety of knowledge manager caching."""
        import threading
        import time

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": ["Concurrent Practice"], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        kb_dir = tmp_path / "knowledge_base" / "best_practices"
        kb_dir.mkdir(parents=True)
        (kb_dir / "concurrent_practice.md").write_text("Concurrent access test")

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        results = []
        errors = []

        def access_knowledge():
            try:
                for i in range(10):
                    result = km.get_best_practice_details("Concurrent Practice")
                    results.append(result)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(e)

        # Create multiple threads accessing the same knowledge
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_knowledge)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent access errors: {errors}"

        # Verify all results are consistent
        assert len(results) == 50  # 5 threads * 10 accesses each
        assert all(result == "Concurrent access test" for result in results)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_technologies_list_handling(self, tmp_path):
        """Test handling of edge cases in technology lists."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "base_prompts").mkdir()

        config_file = tmp_path / "config.json"
        config_data = {"": {"best_practices": [], "tools": []}}  # Empty technology key
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Test with whitespace-only technology
        config = PromptConfig(
            technologies=["  "],  # Whitespace technology
            task_type="test edge case",
            code_requirements="handle whitespace technology names properly",
        )

        # Should handle gracefully
        prompt = generator.generate_prompt(config)
        assert len(prompt) > 0

    def test_very_long_inputs(self, tmp_path):
        """Test handling of very long input strings."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "base_prompts").mkdir()

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Create very long inputs
        very_long_description = "Very long task description. " * 1000
        very_long_requirements = "Very detailed requirements. " * 2000

        config = PromptConfig(
            technologies=["python"],
            task_type="test very long inputs",
            task_description=very_long_description,
            code_requirements=very_long_requirements,
        )

        # Should handle very long inputs without issues
        prompt = generator.generate_prompt(config)
        assert len(prompt) > 0
        assert very_long_description in prompt
        assert very_long_requirements in prompt

    def test_special_characters_in_inputs(self, tmp_path):
        """Test handling of special characters and unicode in inputs."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "base_prompts").mkdir()

        config_file = tmp_path / "config.json"
        config_data = {"python": {"best_practices": [], "tools": []}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        generator = PromptGenerator(str(prompts_dir), str(config_file), base_path=str(tmp_path))

        # Test with special characters and unicode
        config = PromptConfig(
            technologies=["python"],
            task_type="test with émojis 🚀 and spëcial chars: <>&\"'",
            task_description="Implement función with ñoñó characters and 中文 text",
            code_requirements="Handle UTF-8: αβγδε, symbols: ±×÷≤≥, and quotes: 'single' \"double\"",
        )

        # Should handle special characters properly
        prompt = generator.generate_prompt(config)
        assert len(prompt) > 0
        assert "émojis 🚀" in prompt
        assert "función" in prompt
        assert "中文" in prompt
        assert "αβγδε" in prompt
        assert '"double"' in prompt or "'double'" in prompt  # May be escaped

    def test_path_traversal_protection(self, tmp_path):
        """Test protection against path traversal attacks."""
        base_dir = str(tmp_path)

        # Test various path traversal attempts
        dangerous_paths = [
            "../etc/passwd",
            "..\\windows\\system32",
            "../../sensitive_file",
            "../../../root",
            "subdir/../../../etc/hosts",
            "./../outside_dir/file.txt",
        ]

        for dangerous_path in dangerous_paths:
            with pytest.raises(ValueError, match="Attempted directory traversal"):
                safe_path_join(base_dir, dangerous_path)

        # Test legitimate paths
        safe_paths = [
            "subdir/file.txt",
            "knowledge_base/best_practices/python.md",
            "tools/pytest.json",
        ]

        for safe_path in safe_paths:
            result = safe_path_join(base_dir, safe_path)
            assert result.startswith(os.path.abspath(base_dir))
            assert ".." not in result

    def test_filename_edge_cases(self, tmp_path):
        """Test handling of edge cases in filenames."""
        config_file = tmp_path / "config.json"
        config_data = {
            "test": {
                "best_practices": ["Weird-Name_123", "Name With Spaces", "name.with.dots"],
                "tools": ["tool-with-dashes", "tool_with_underscores"],
            }
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

        # Test filename normalization
        test_cases = [
            ("Weird-Name_123", "weird-name_123"),
            ("Name With Spaces", "name_with_spaces"),
            ("name.with.dots", "name.with.dots"),
        ]

        for original, expected_filename in test_cases:
            # The knowledge manager should handle filename normalization
            result = km.get_best_practice_details(original)
            # Should return None for non-existent files, but not crash
            assert result is None


class TestEventSystemErrorHandling:
    """Test error handling in the event system."""

    @pytest.mark.asyncio
    async def test_event_handler_exceptions(self):
        """Test that event handler exceptions don't break the event system."""
        event_bus = EventBus()
        successful_calls = []

        async def failing_handler(event: Event):
            raise RuntimeError("Handler failed")

        async def successful_handler(event: Event):
            successful_calls.append(event)

        # Subscribe both handlers
        event_bus.subscribe(EventType.SYSTEM_ERROR, failing_handler)
        event_bus.subscribe(EventType.SYSTEM_ERROR, successful_handler)

        test_event = Event(EventType.SYSTEM_ERROR, "TestSource")

        # Should not raise exception despite handler failure
        with patch("src.events.logger"):
            await event_bus.publish(test_event)

        # Successful handler should still have been called
        assert len(successful_calls) == 1
        assert successful_calls[0] == test_event

    def test_event_bus_history_overflow(self):
        """Test event bus history size management."""
        event_bus = EventBus()
        event_bus._max_history_size = 3  # Set small limit for testing

        # Publish more events than the limit
        events = []
        for i in range(5):
            event = Event(EventType.TEMPLATE_RENDERED, f"Source{i}")
            events.append(event)
            import asyncio

            asyncio.run(event_bus.publish(event))

        # History should be limited to max size
        history = event_bus.get_event_history()
        assert len(history) == 3

        # Should contain the most recent events
        sources = [event.source for event in history]
        assert "Source2" in sources
        assert "Source3" in sources
        assert "Source4" in sources
        assert "Source0" not in sources
        assert "Source1" not in sources


class TestUtilityErrorHandling:
    """Test error handling in utility functions."""

    def test_read_text_file_errors(self):
        """Test read_text_file error handling."""
        # Test non-existent file
        with patch("src.utils.logger") as mock_logger:
            result = read_text_file("/non/existent/file.txt")
            assert result is None
            mock_logger.error.assert_called()

        # Test permission denied
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("src.utils.logger") as mock_logger:
                result = read_text_file("/restricted/file.txt")
                assert result is None
                mock_logger.error.assert_called()

        # Test Unicode decode error
        with patch("builtins.open", mock_open(read_data=b"\x80\x81\x82")):
            with patch("src.utils.logger") as mock_logger:
                result = read_text_file("/binary/file.txt")
                assert result is None
                mock_logger.error.assert_called()

    def test_load_json_file_errors(self):
        """Test load_json_file error handling."""
        # Test invalid JSON
        with patch("builtins.open", mock_open(read_data="{ invalid json")):
            with patch("src.utils.logger") as mock_logger:
                result = load_json_file("/invalid/json.json")
                assert result is None
                mock_logger.error.assert_called()

        # Test empty file
        with patch("builtins.open", mock_open(read_data="")):
            with patch("src.utils.logger") as mock_logger:
                result = load_json_file("/empty/file.json")
                assert result is None
                mock_logger.error.assert_called()

        # Test file not found
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with patch("src.utils.logger") as mock_logger:
                result = load_json_file("/missing/file.json")
                assert result is None
                mock_logger.error.assert_called()
