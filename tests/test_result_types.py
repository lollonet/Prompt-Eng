"""
Comprehensive tests for Result types and error handling patterns.

Tests Success/Error monadic patterns, chaining operations, and all
functional programming patterns for robust error handling.
"""

import pytest
from typing import Union
from unittest.mock import Mock

from src.result_types import (
    Success,
    Error,
    Result,
    PromptError,
    KnowledgeError,
    ValidationError,
    safe_call,
    combine_results,
    _example_usage
)


class TestSuccessType:
    """Test Success type functionality."""
    
    def test_success_creation(self):
        """Test Success creation with value."""
        success = Success("test_value")
        
        assert success.value == "test_value"
        assert success.is_success() is True
        assert success.is_error() is False
    
    def test_success_unwrap(self):
        """Test Success unwrap method."""
        success = Success(42)
        
        assert success.unwrap() == 42
    
    def test_success_unwrap_or(self):
        """Test Success unwrap_or method."""
        success = Success("actual")
        
        assert success.unwrap_or("default") == "actual"
    
    def test_success_map(self):
        """Test Success map transformation."""
        success = Success(10)
        
        # Map to double the value
        mapped = success.map(lambda x: x * 2)
        
        assert mapped.is_success()
        assert mapped.unwrap() == 20
    
    def test_success_map_with_exception(self):
        """Test Success map when transformation raises exception."""
        success = Success("text")
        
        # Map with function that raises exception
        mapped = success.map(lambda x: int(x))  # Will raise ValueError
        
        assert mapped.is_error()
        assert isinstance(mapped.error, ValueError)
    
    def test_success_map_error(self):
        """Test Success map_error (should be no-op)."""
        success = Success("value")
        
        # map_error should do nothing for Success
        mapped = success.map_error(lambda e: "transformed_error")
        
        assert mapped.is_success()
        assert mapped.unwrap() == "value"
    
    def test_success_and_then(self):
        """Test Success and_then chaining."""
        success = Success(5)
        
        # Chain with function that returns another Result
        def double_if_positive(x):
            if x > 0:
                return Success(x * 2)
            else:
                return Error("negative_number")
        
        chained = success.and_then(double_if_positive)
        
        assert chained.is_success()
        assert chained.unwrap() == 10
    
    def test_success_and_then_returns_error(self):
        """Test Success and_then when chained function returns error."""
        success = Success(-5)
        
        def double_if_positive(x):
            if x > 0:
                return Success(x * 2)
            else:
                return Error("negative_number")
        
        chained = success.and_then(double_if_positive)
        
        assert chained.is_error()
        assert chained.error == "negative_number"


class TestErrorType:
    """Test Error type functionality."""
    
    def test_error_creation(self):
        """Test Error creation with error value."""
        error = Error("error_message")
        
        assert error.error == "error_message"
        assert error.is_success() is False
        assert error.is_error() is True
    
    def test_error_unwrap_raises(self):
        """Test Error unwrap raises exception."""
        error = Error(ValueError("test error"))
        
        with pytest.raises(ValueError, match="test error"):
            error.unwrap()
    
    def test_error_unwrap_non_exception(self):
        """Test Error unwrap with non-exception error."""
        error = Error("string_error")
        
        with pytest.raises(ValueError, match="Result contains error: string_error"):
            error.unwrap()
    
    def test_error_unwrap_or(self):
        """Test Error unwrap_or returns default."""
        error = Error("error_message")
        
        assert error.unwrap_or("default_value") == "default_value"
    
    def test_error_map(self):
        """Test Error map (should be no-op)."""
        error = Error("error_message")
        
        # map should do nothing for Error
        mapped = error.map(lambda x: x * 2)
        
        assert mapped.is_error()
        assert mapped.error == "error_message"
    
    def test_error_map_error(self):
        """Test Error map_error transformation."""
        error = Error("original_error")
        
        # Transform the error
        mapped = error.map_error(lambda e: f"transformed_{e}")
        
        assert mapped.is_error()
        assert mapped.error == "transformed_original_error"
    
    def test_error_and_then(self):
        """Test Error and_then (should be no-op)."""
        error = Error("error_message")
        
        def some_operation(x):
            return Success(x * 2)
        
        chained = error.and_then(some_operation)
        
        assert chained.is_error()
        assert chained.error == "error_message"


class TestDomainErrorTypes:
    """Test domain-specific error types."""
    
    def test_prompt_error_creation(self):
        """Test PromptError creation and fields."""
        error = PromptError(
            message="Template not found",
            code="TEMPLATE_NOT_FOUND",
            context={"template_name": "nonexistent.txt", "attempted_path": "/templates/nonexistent.txt"}
        )
        
        assert error.message == "Template not found"
        assert error.code == "TEMPLATE_NOT_FOUND"
        assert error.context["template_name"] == "nonexistent.txt"
        assert error.context["attempted_path"] == "/templates/nonexistent.txt"
    
    def test_prompt_error_string_representation(self):
        """Test PromptError string representation."""
        error = PromptError(
            message="Invalid template syntax",
            code="SYNTAX_ERROR",
            context={"template_name": "test.txt", "line_number": 15}
        )
        
        error_str = str(error)
        assert "Invalid template syntax" in error_str
        assert "SYNTAX_ERROR" in error_str
        assert "test.txt" in error_str
        assert "15" in error_str
    
    def test_knowledge_error_creation(self):
        """Test KnowledgeError creation and fields."""
        error = KnowledgeError(
            message="Knowledge base connection failed",
            source="knowledge_manager",
            details="Connection timeout after 30 seconds"
        )
        
        assert error.message == "Knowledge base connection failed"
        assert error.source == "knowledge_manager"
        assert error.details == "Connection timeout after 30 seconds"
    
    def test_knowledge_error_string_representation(self):
        """Test KnowledgeError string representation."""
        error = KnowledgeError(
            message="Data not found",
            source="cache_layer",
            details="Cache miss for key 'user_123'"
        )
        
        error_str = str(error)
        assert "Data not found" in error_str
        assert "cache_layer" in error_str
        assert "Cache miss for key 'user_123'" in error_str
    
    def test_validation_error_creation(self):
        """Test ValidationError creation and fields."""
        error = ValidationError(
            field="email",
            value="invalid-email",
            constraint="Must be valid email address"
        )
        
        assert error.field == "email" 
        assert error.value == "invalid-email"
        assert error.constraint == "Must be valid email address"
    
    def test_validation_error_string_representation(self):
        """Test ValidationError string representation."""
        error = ValidationError(
            field="age",
            value=150,
            constraint="Must be between 0 and 120"
        )
        
        error_str = str(error)
        expected = "Validation failed for 'age' with value '150': Must be between 0 and 120"
        assert error_str == expected


class TestResultUtilityFunctions:
    """Test utility functions for Result types."""
    
    def test_safe_call_success(self):
        """Test safe_call with successful function."""
        def successful_function():
            return "success_result"
        
        result = safe_call(successful_function)
        
        assert result.is_success()
        assert result.unwrap() == "success_result"
    
    def test_safe_call_with_exception(self):
        """Test safe_call with function that raises exception."""
        def failing_function():
            raise ValueError("Function failed")
        
        result = safe_call(failing_function)
        
        assert result.is_error()
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Function failed"
    
    def test_safe_call_with_error_mapper(self):
        """Test safe_call with custom error mapper."""
        def failing_function():
            raise ValueError("Original error")
        
        def error_mapper(exception):
            return f"Mapped: {exception}"
        
        result = safe_call(failing_function, error_mapper)
        
        assert result.is_error()
        assert result.error == "Mapped: Original error"
    
    def test_combine_results_all_success(self):
        """Test combine_results with all successful results."""
        results = [
            Success("first"),
            Success("second"), 
            Success("third")
        ]
        
        combined = combine_results(results)
        
        assert combined.is_success()
        assert combined.unwrap() == ["first", "second", "third"]
    
    def test_combine_results_with_error(self):
        """Test combine_results with one error (fail fast)."""
        results = [
            Success("first"),
            Error("error_occurred"),
            Success("third")
        ]
        
        combined = combine_results(results)
        
        assert combined.is_error()
        assert combined.error == "error_occurred"
    
    def test_combine_results_empty_list(self):
        """Test combine_results with empty list."""
        results = []
        
        combined = combine_results(results)
        
        assert combined.is_success()
        assert combined.unwrap() == []
    
    def test_combine_results_first_error_returned(self):
        """Test combine_results returns first error encountered."""
        results = [
            Success("first"),
            Error("first_error"),
            Error("second_error"),
            Success("last")
        ]
        
        combined = combine_results(results)
        
        assert combined.is_error()
        assert combined.error == "first_error"


class TestResultChaining:
    """Test complex Result chaining operations."""
    
    def test_complex_chaining_success_path(self):
        """Test complex chaining with all successful operations."""
        def parse_int(s: str) -> Union[Success, Error]:
            try:
                return Success(int(s))
            except ValueError:
                return Error(f"Cannot parse '{s}' as integer")
        
        def validate_positive(n: int) -> Union[Success, Error]:
            if n > 0:
                return Success(n)
            else:
                return Error(f"Number {n} is not positive")
        
        def square(n: int) -> Union[Success, Error]:
            return Success(n * n)
        
        # Chain operations
        result = (parse_int("5")
                 .and_then(validate_positive)
                 .and_then(square))
        
        assert result.is_success()
        assert result.unwrap() == 25
    
    def test_complex_chaining_error_path(self):
        """Test complex chaining with error in middle."""
        def parse_int(s: str) -> Union[Success, Error]:
            try:
                return Success(int(s))
            except ValueError:
                return Error(f"Cannot parse '{s}' as integer")
        
        def validate_positive(n: int) -> Union[Success, Error]:
            if n > 0:
                return Success(n)
            else:
                return Error(f"Number {n} is not positive")
        
        def square(n: int) -> Union[Success, Error]:
            return Success(n * n)
        
        # Chain with negative number (will fail at validate_positive)
        result = (parse_int("-5")
                 .and_then(validate_positive)
                 .and_then(square))
        
        assert result.is_error()
        assert result.error == "Number -5 is not positive"
    
    def test_chaining_with_map_operations(self):
        """Test chaining with map operations."""
        result = (Success(10)
                 .map(lambda x: x + 5)      # 15
                 .map(lambda x: x * 2)      # 30
                 .map(lambda x: str(x)))    # "30"
        
        assert result.is_success()
        assert result.unwrap() == "30"
    
    def test_chaining_map_with_and_then(self):
        """Test mixing map and and_then operations."""
        def safe_divide(x: int, y: int) -> Union[Success, Error]:
            if y == 0:
                return Error("Division by zero")
            return Success(x / y)
        
        result = (Success(20)
                 .map(lambda x: x + 10)     # 30
                 .and_then(lambda x: safe_divide(x, 3))  # 10.0
                 .map(lambda x: int(x)))    # 10
        
        assert result.is_success()
        assert result.unwrap() == 10


class TestResultUsagePatterns:
    """Test real-world usage patterns for Result types."""
    
    def test_file_processing_pattern(self):
        """Test file processing pattern with Results."""
        def read_file(filename: str) -> Union[Success, Error]:
            if filename == "valid.txt":
                return Success("file content")
            else:
                return Error(f"File not found: {filename}")
        
        def process_content(content: str) -> Union[Success, Error]:
            if "error" in content:
                return Error("Content contains error")
            return Success(content.upper())
        
        def save_result(content: str) -> Union[Success, Error]:
            return Success(f"Saved: {content}")
        
        # Valid file processing
        result = (read_file("valid.txt")
                 .and_then(process_content)
                 .and_then(save_result))
        
        assert result.is_success()
        assert result.unwrap() == "Saved: FILE CONTENT"
        
        # Invalid file processing
        result = read_file("missing.txt").and_then(process_content)
        
        assert result.is_error()
        assert "File not found" in result.error
    
    def test_validation_pattern(self):
        """Test validation pattern with Results."""
        def validate_email(email: str) -> Union[Success, Error]:
            if "@" in email and "." in email:
                return Success(email)
            return Error(ValidationError(
                field="email",
                value=email,
                constraint="Must contain @ and ."
            ))
        
        def validate_age(age: int) -> Union[Success, Error]:
            if 0 <= age <= 120:
                return Success(age)
            return Error(ValidationError(
                field="age", 
                value=age,
                constraint="Must be between 0 and 120"
            ))
        
        # Valid inputs
        email_result = validate_email("user@example.com")
        age_result = validate_age(25)
        
        assert email_result.is_success()
        assert age_result.is_success()
        
        # Invalid inputs
        bad_email = validate_email("invalid-email")
        bad_age = validate_age(150)
        
        assert bad_email.is_error()
        assert bad_age.is_error()
        assert isinstance(bad_email.error, ValidationError)
        assert isinstance(bad_age.error, ValidationError)
    
    def test_api_call_pattern(self):
        """Test API call pattern with Results."""
        def make_api_call(endpoint: str) -> Union[Success, Error]:
            if endpoint == "/users":
                return Success({"users": [{"id": 1, "name": "John"}]})
            elif endpoint == "/timeout":
                return Error("Request timeout")
            else:
                return Error("Endpoint not found")
        
        def extract_users(response: dict) -> Union[Success, Error]:
            if "users" in response:
                return Success(response["users"])
            return Error("No users in response")
        
        def count_users(users: list) -> Union[Success, Error]:
            return Success(len(users))
        
        # Successful API call
        result = (make_api_call("/users")
                 .and_then(extract_users)
                 .and_then(count_users))
        
        assert result.is_success()
        assert result.unwrap() == 1
        
        # Failed API call
        result = make_api_call("/timeout").and_then(extract_users)
        
        assert result.is_error()
        assert result.error == "Request timeout"


class TestExampleUsage:
    """Test the example usage patterns in the module."""
    
    def test_example_usage_runs(self):
        """Test that example usage function runs without error."""
        # The _example_usage function is mainly for documentation
        # but we can verify it doesn't crash
        try:
            _example_usage()
        except Exception as e:
            pytest.fail(f"Example usage function raised {e}")


class TestResultTypeHints:
    """Test Result type hint patterns."""
    
    def test_result_as_return_type(self):
        """Test using Result as return type annotation."""
        def divide_safely(a: float, b: float) -> Union[Success, Error]:
            if b == 0:
                return Error("Division by zero")
            return Success(a / b)
        
        # Test successful division
        result = divide_safely(10, 2)
        assert result.is_success()
        assert result.unwrap() == 5.0
        
        # Test division by zero
        result = divide_safely(10, 0)
        assert result.is_error()
        assert result.error == "Division by zero"
    
    def test_nested_result_operations(self):
        """Test nested Result operations."""
        def parse_and_validate(s: str) -> Union[Success, Error]:
            return (safe_call(lambda: int(s))
                   .and_then(lambda x: Success(x) if x > 0 else Error("Must be positive")))
        
        # Valid positive number
        result = parse_and_validate("42")
        assert result.is_success()
        assert result.unwrap() == 42
        
        # Invalid number format
        result = parse_and_validate("not_a_number")
        assert result.is_error()
        
        # Valid number but not positive
        result = parse_and_validate("-5")
        assert result.is_error()
        assert result.error == "Must be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])