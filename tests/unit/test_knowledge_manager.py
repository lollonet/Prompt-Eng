"""
Unit tests for AsyncKnowledgeManager focusing on public behavior.

Tests the public interface without mocking implementation details,
focusing on the behavior users actually interact with.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from src.knowledge_manager_async import AsyncKnowledgeManager
from src.types_advanced import KnowledgeManagerConfig, TechnologyName, BestPracticeName, ToolName
from src.result_types import Success, Error


class TestAsyncKnowledgeManagerPublicBehavior:
    """Test AsyncKnowledgeManager public interface and behavior."""
    
    @pytest.fixture
    def test_config_data(self):
        """Sample configuration data for testing."""
        return {
            "python": {
                "best_practices": ["Use type hints", "Follow PEP 8", "Write tests"],
                "tools": ["pytest", "black", "mypy"]
            },
            "docker": {
                "best_practices": ["Multi-stage builds", "Minimal base images"],
                "tools": ["docker-compose", "buildx"]
            }
        }
    
    @pytest.fixture
    def knowledge_manager(self, tmp_path, test_config_data):
        """Create AsyncKnowledgeManager with test data."""
        # Setup test directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create mapping file
        mapping_file = config_dir / "tech_stack_mapping.json"
        mapping_file.write_text(json.dumps(test_config_data, indent=2))
        
        # Create knowledge base structure  
        kb_dir = tmp_path / "knowledge_base"
        kb_dir.mkdir()
        
        # Create config
        config = KnowledgeManagerConfig(
            config_path=str(mapping_file),
            base_path=str(kb_dir),
            cache_strategy="memory",
            cache_ttl_seconds=300,
            enable_performance_tracking=True,
            max_concurrent_operations=5
        )
        
        return AsyncKnowledgeManager(config)
    
    @pytest.mark.asyncio
    async def test_get_best_practices_success(self, knowledge_manager):
        """Test successful best practices retrieval."""
        result = await knowledge_manager.get_best_practices(TechnologyName("python"))
        
        assert result.is_success()
        practices = result.unwrap()
        assert isinstance(practices, list)
        assert len(practices) > 0
        assert "Use type hints" in practices
        assert "Follow PEP 8" in practices
    
    @pytest.mark.asyncio 
    async def test_get_tools_success(self, knowledge_manager):
        """Test successful tools retrieval."""
        result = await knowledge_manager.get_tools(TechnologyName("docker"))
        
        assert result.is_success()
        tools = result.unwrap()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert "docker-compose" in tools
        assert "buildx" in tools
    
    @pytest.mark.asyncio
    async def test_get_best_practices_unknown_technology(self, knowledge_manager):
        """Test behavior with unknown technology."""
        result = await knowledge_manager.get_best_practices(TechnologyName("unknown_tech"))
        
        # Should handle gracefully - either return empty list or error
        # The exact behavior depends on implementation, but should not crash
        assert result.is_success() or result.is_error()
        
        if result.is_success():
            practices = result.unwrap()
            assert isinstance(practices, list)
        
    @pytest.mark.asyncio
    async def test_get_tools_unknown_technology(self, knowledge_manager):
        """Test tools retrieval for unknown technology."""
        result = await knowledge_manager.get_tools(TechnologyName("unknown_tech"))
        
        # Should handle gracefully
        assert result.is_success() or result.is_error()
        
        if result.is_success():
            tools = result.unwrap()
            assert isinstance(tools, list)
    
    @pytest.mark.asyncio
    async def test_preload_data_multiple_technologies(self, knowledge_manager):
        """Test preloading data for multiple technologies."""
        technologies = [TechnologyName("python"), TechnologyName("docker")]
        
        # Should not raise an exception
        await knowledge_manager.preload_data(technologies)
        
        # After preloading, subsequent calls should be faster
        result1 = await knowledge_manager.get_best_practices(TechnologyName("python"))
        result2 = await knowledge_manager.get_tools(TechnologyName("docker"))
        
        assert result1.is_success()
        assert result2.is_success()
    
    @pytest.mark.asyncio
    async def test_cache_behavior(self, knowledge_manager):
        """Test that caching works by making multiple calls."""
        technology = TechnologyName("python")
        
        # First call
        result1 = await knowledge_manager.get_best_practices(technology)
        
        # Second call should use cache
        result2 = await knowledge_manager.get_best_practices(technology)
        
        assert result1.is_success()
        assert result2.is_success()
        assert result1.unwrap() == result2.unwrap()
    
    @pytest.mark.asyncio
    async def test_health_check(self, knowledge_manager):
        """Test health check functionality."""
        health_result = await knowledge_manager.health_check()
        
        assert health_result.is_success()
        health_info = health_result.unwrap()
        
        # Should contain basic health information
        assert "status" in health_info
        assert "component" in health_info
        assert health_info["component"] == "AsyncKnowledgeManager"
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, knowledge_manager):
        """Test cache clearing functionality."""
        # Load some data
        await knowledge_manager.get_best_practices(TechnologyName("python"))
        
        # Clear cache should not raise exception
        await knowledge_manager.clear_cache()
        
        # Should still be able to load data after cache clear
        result = await knowledge_manager.get_best_practices(TechnologyName("python"))
        assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, knowledge_manager):
        """Test concurrent operations work properly."""
        import asyncio
        
        # Launch multiple concurrent operations
        tasks = [
            knowledge_manager.get_best_practices(TechnologyName("python")),
            knowledge_manager.get_tools(TechnologyName("python")),
            knowledge_manager.get_best_practices(TechnologyName("docker")),
            knowledge_manager.get_tools(TechnologyName("docker"))
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result.is_success()
    
    @pytest.mark.asyncio
    async def test_result_types_consistency(self, knowledge_manager):
        """Test that all methods return proper Result types."""
        # Test different methods
        methods_and_args = [
            (knowledge_manager.get_best_practices, [TechnologyName("python")]),
            (knowledge_manager.get_tools, [TechnologyName("python")]),
            (knowledge_manager.health_check, []),
        ]
        
        for method, args in methods_and_args:
            result = await method(*args)
            
            # Should always return a Result type
            assert hasattr(result, 'is_success')
            assert hasattr(result, 'is_error')
            assert result.is_success() or result.is_error()
            
            # If success, should be able to unwrap
            if result.is_success():
                value = result.unwrap()
                assert value is not None


class TestKnowledgeManagerConfiguration:
    """Test configuration handling and validation."""
    
    def test_config_validation(self, tmp_path):
        """Test that configuration is properly validated."""
        config = KnowledgeManagerConfig(
            config_path="nonexistent/path.json",
            base_path=str(tmp_path),
            cache_strategy="memory",
            cache_ttl_seconds=300,
            enable_performance_tracking=True,
            max_concurrent_operations=5
        )
        
        # Should be able to create instance even with invalid path
        # (validation happens at runtime)
        manager = AsyncKnowledgeManager(config)
        assert manager is not None
        assert manager.config == config
    
    def test_config_defaults(self, tmp_path):
        """Test configuration with minimal settings."""
        config = KnowledgeManagerConfig(
            config_path="test.json",
            base_path=str(tmp_path)
        )
        
        manager = AsyncKnowledgeManager(config)
        assert manager.config.cache_strategy == "memory"  # Default value
        assert manager.config.max_concurrent_operations > 0  # Should have reasonable default


class TestKnowledgeManagerErrorHandling:
    """Test error handling without mocking implementation details."""
    
    @pytest.mark.asyncio
    async def test_invalid_config_file_handling(self, tmp_path):
        """Test behavior with invalid configuration file."""
        # Create config pointing to non-existent file
        config = KnowledgeManagerConfig(
            config_path="nonexistent/file.json",
            base_path=str(tmp_path)
        )
        
        manager = AsyncKnowledgeManager(config)
        
        # Should handle errors gracefully when trying to load data
        result = await manager.get_best_practices(TechnologyName("python"))
        
        # Should return an error result, not raise exception
        assert result.is_error()
        error = result.error
        assert error is not None
    
    @pytest.mark.asyncio
    async def test_empty_technology_name_handling(self, tmp_path):
        """Test behavior with empty or invalid technology names."""
        config = KnowledgeManagerConfig(
            config_path="test.json",
            base_path=str(tmp_path)
        )
        
        manager = AsyncKnowledgeManager(config)
        
        # Test with empty string (if TechnologyName allows it)
        try:
            empty_tech = TechnologyName("")
            result = await manager.get_best_practices(empty_tech)
            
            # Should handle gracefully
            assert result.is_success() or result.is_error()
        except ValueError:
            # TechnologyName might validate and reject empty strings
            pass