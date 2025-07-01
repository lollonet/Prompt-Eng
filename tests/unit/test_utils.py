"""
Comprehensive unit tests for utils module.

Tests the critical utility functions used throughout the system for
safe file operations and security.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils import (
    safe_path_join,
    load_json_file,
    read_text_file
)


class TestSafePathJoin:
    """Test safe_path_join security function."""

    def test_safe_path_join_normal_paths(self):
        """Test safe path joining with normal paths."""
        base_dir = "/home/user/project"
        
        # Normal subdirectory
        result = safe_path_join(base_dir, "subdir", "file.txt")
        expected = os.path.abspath(os.path.join(base_dir, "subdir", "file.txt"))
        assert result == expected

    def test_safe_path_join_single_component(self):
        """Test safe path joining with single component."""
        base_dir = "/home/user/project"
        
        result = safe_path_join(base_dir, "file.txt")
        expected = os.path.abspath(os.path.join(base_dir, "file.txt"))
        assert result == expected

    def test_safe_path_join_multiple_components(self):
        """Test safe path joining with multiple components."""
        base_dir = "/home/user/project"
        
        result = safe_path_join(base_dir, "config", "data", "settings.json")
        expected = os.path.abspath(os.path.join(base_dir, "config", "data", "settings.json"))
        assert result == expected

    def test_safe_path_join_prevents_directory_traversal(self):
        """Test safe path joining prevents directory traversal attacks."""
        base_dir = "/home/user/project"
        
        # Classic directory traversal attempt
        with pytest.raises(ValueError, match="Attempted directory traversal"):
            safe_path_join(base_dir, "..", "..", "etc", "passwd")

    def test_safe_path_join_prevents_absolute_path_injection(self):
        """Test safe path joining prevents absolute path injection."""
        base_dir = "/home/user/project"
        
        # Absolute path injection attempt
        with pytest.raises(ValueError, match="Attempted directory traversal"):
            safe_path_join(base_dir, "/etc/passwd")

    def test_safe_path_join_prevents_complex_traversal(self):
        """Test safe path joining prevents complex traversal patterns."""
        base_dir = "/home/user/project"
        
        # Complex traversal with mixed components
        with pytest.raises(ValueError, match="Attempted directory traversal"):
            safe_path_join(base_dir, "subdir", "..", "..", "..", "etc", "passwd")

    def test_safe_path_join_allows_same_level_access(self):
        """Test safe path joining allows same-level directory access."""
        base_dir = "/home/user/project"
        
        # Going into subdirectory and back up to same level
        result = safe_path_join(base_dir, "subdir", "..", "file.txt")
        expected = os.path.abspath(os.path.join(base_dir, "file.txt"))
        assert result == expected

    def test_safe_path_join_normalizes_paths(self):
        """Test safe path joining normalizes path separators."""
        base_dir = "/home/user/project"
        
        # Path with redundant separators and dots
        result = safe_path_join(base_dir, "subdir//./file.txt")
        expected = os.path.abspath(os.path.join(base_dir, "subdir", "file.txt"))
        assert result == expected

    def test_safe_path_join_with_relative_base_dir(self):
        """Test safe path joining with relative base directory."""
        base_dir = "project"
        
        result = safe_path_join(base_dir, "subdir", "file.txt")
        expected = os.path.abspath(os.path.join(base_dir, "subdir", "file.txt"))
        assert result == expected

    def test_safe_path_join_empty_components(self):
        """Test safe path joining handles empty components."""
        base_dir = "/home/user/project"
        
        result = safe_path_join(base_dir, "", "file.txt", "")
        expected = os.path.abspath(os.path.join(base_dir, "file.txt"))
        assert result == expected


class TestLoadJsonFile:
    """Test load_json_file function."""

    def test_load_json_file_success(self):
        """Test successful JSON file loading."""
        test_data = {
            "name": "test_project",
            "version": "1.0.0",
            "dependencies": ["package1", "package2"],
            "config": {
                "debug": True,
                "timeout": 30
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(test_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            result = load_json_file(temp_file_path)
            assert result == test_data
        finally:
            Path(temp_file_path).unlink()

    def test_load_json_file_not_found(self):
        """Test JSON file loading with non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_json_file("/nonexistent/path/file.json")

    def test_load_json_file_invalid_json(self):
        """Test JSON file loading with invalid JSON content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write("{ invalid json content without closing brace")
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_json_file(temp_file_path)
        finally:
            Path(temp_file_path).unlink()

    def test_load_json_file_empty_file(self):
        """Test JSON file loading with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Write nothing to file
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_json_file(temp_file_path)
        finally:
            Path(temp_file_path).unlink()

    def test_load_json_file_permission_denied(self):
        """Test JSON file loading with permission denied."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump({"test": "data"}, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Remove read permissions
            Path(temp_file_path).chmod(0o000)
            
            with pytest.raises(IOError):
                load_json_file(temp_file_path)
        finally:
            # Restore permissions and cleanup
            Path(temp_file_path).chmod(0o644)
            Path(temp_file_path).unlink()

    def test_load_json_file_with_unicode(self):
        """Test JSON file loading with Unicode content."""
        test_data = {
            "message": "Hello, 世界! 🌍",
            "symbols": "αβγδε",
            "emoji": "😀🎉🚀"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_file:
            json.dump(test_data, temp_file, ensure_ascii=False)
            temp_file_path = temp_file.name
        
        try:
            result = load_json_file(temp_file_path)
            assert result == test_data
        finally:
            Path(temp_file_path).unlink()

    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_load_json_file_io_error(self, mock_open):
        """Test JSON file loading with generic I/O error."""
        with pytest.raises(IOError, match="Disk full"):
            load_json_file("/some/path/file.json")


class TestReadTextFile:
    """Test read_text_file function."""

    def test_read_text_file_success(self):
        """Test successful text file reading."""
        test_content = """This is a test file.
It contains multiple lines.
With various content including symbols: @#$%^&*()
And unicode: 世界 🌍"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            result = read_text_file(temp_file_path)
            assert result == test_content
        finally:
            Path(temp_file_path).unlink()

    def test_read_text_file_empty_file(self):
        """Test reading empty text file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            # Write nothing to file
            temp_file_path = temp_file.name
        
        try:
            result = read_text_file(temp_file_path)
            assert result == ""
        finally:
            Path(temp_file_path).unlink()

    def test_read_text_file_not_found(self):
        """Test text file reading with non-existent file."""
        with pytest.raises(FileNotFoundError):
            read_text_file("/nonexistent/path/file.txt")

    def test_read_text_file_permission_denied(self):
        """Test text file reading with permission denied."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name
        
        try:
            # Remove read permissions
            Path(temp_file_path).chmod(0o000)
            
            with pytest.raises(IOError):
                read_text_file(temp_file_path)
        finally:
            # Restore permissions and cleanup
            Path(temp_file_path).chmod(0o644)
            Path(temp_file_path).unlink()

    def test_read_text_file_large_file(self):
        """Test reading large text file."""
        # Create content that's reasonably large for testing
        large_content = "".join("Line {}\n".format(i) for i in range(10000))
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(large_content)
            temp_file_path = temp_file.name
        
        try:
            result = read_text_file(temp_file_path)
            assert result == large_content
            assert len(result.split('\n')) == 10001  # 10000 lines + empty line at end
        finally:
            Path(temp_file_path).unlink()

    def test_read_text_file_with_special_characters(self):
        """Test reading text file with special characters and encodings."""
        special_content = """Special characters test:
Tab:	character
Newline after this

Carriage return and various quotes:
"Double quotes"
'Single quotes'
`Backticks`
Unicode: αβγδε 世界 🚀"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(special_content)
            temp_file_path = temp_file.name
        
        try:
            result = read_text_file(temp_file_path)
            assert result == special_content
        finally:
            Path(temp_file_path).unlink()

    @patch('builtins.open', side_effect=IOError("Device not ready"))
    def test_read_text_file_io_error(self, mock_open):
        """Test text file reading with generic I/O error."""
        with pytest.raises(IOError, match="Device not ready"):
            read_text_file("/some/path/file.txt")


class TestUtilsIntegration:
    """Integration tests for utils functions."""

    def test_safe_path_join_with_file_operations(self):
        """Test safe path joining integrated with file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file using safe path joining
            safe_file_path = safe_path_join(temp_dir, "config", "test.json")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(safe_file_path), exist_ok=True)
            
            # Create test data and write to file
            test_data = {"integration": "test", "safe_paths": True}
            with open(safe_file_path, 'w') as f:
                json.dump(test_data, f)
            
            # Read back using load_json_file
            result = load_json_file(safe_file_path)
            assert result == test_data

    def test_file_operations_with_complex_directory_structure(self):
        """Test file operations with complex directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure using safe path joining
            config_dir = safe_path_join(temp_dir, "app", "config")
            data_dir = safe_path_join(temp_dir, "app", "data")
            
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(data_dir, exist_ok=True)
            
            # Create configuration file
            config_path = safe_path_join(config_dir, "settings.json")
            config_data = {
                "database": "postgresql://localhost:5432/test",
                "cache_ttl": 3600,
                "features": ["feature1", "feature2"]
            }
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            # Create data file
            data_path = safe_path_join(data_dir, "readme.txt")
            data_content = "This is the data directory readme file.\nIt contains important information."
            with open(data_path, 'w') as f:
                f.write(data_content)
            
            # Test reading both files
            loaded_config = load_json_file(config_path)
            loaded_data = read_text_file(data_path)
            
            assert loaded_config == config_data
            assert loaded_data == data_content

    def test_error_handling_across_util_functions(self):
        """Test error handling consistency across utility functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test non-existent paths
            nonexistent_json = safe_path_join(temp_dir, "nonexistent.json")
            nonexistent_txt = safe_path_join(temp_dir, "nonexistent.txt")
            
            with pytest.raises(FileNotFoundError):
                load_json_file(nonexistent_json)
            
            with pytest.raises(FileNotFoundError):
                read_text_file(nonexistent_txt)
            
            # Test directory traversal prevention
            with pytest.raises(ValueError, match="Attempted directory traversal"):
                safe_path_join(temp_dir, "..", "..", "etc", "passwd")

    def test_unicode_handling_across_functions(self):
        """Test Unicode handling consistency across utility functions."""
        unicode_content = {
            "english": "Hello World",
            "chinese": "你好世界",
            "japanese": "こんにちは世界",
            "arabic": "مرحبا بالعالم",
            "emoji": "🌍🚀🎉",
            "special_chars": "àáâãäåæçèéêë"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON with Unicode
            json_path = safe_path_join(temp_dir, "unicode_test.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(unicode_content, f, ensure_ascii=False)
            
            loaded_json = load_json_file(json_path)
            assert loaded_json == unicode_content
            
            # Test text file with Unicode
            text_content = "\n".join(f"{key}: {value}" for key, value in unicode_content.items())
            text_path = safe_path_join(temp_dir, "unicode_test.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            loaded_text = read_text_file(text_path)
            assert loaded_text == text_content