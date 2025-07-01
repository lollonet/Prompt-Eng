"""
Modern async KnowledgeManager with Result types and advanced patterns.

Business Context: Implements async-first I/O operations, Result-based error handling,
and event-driven architecture following modern best practices for enterprise systems.

Why this approach: Async I/O provides better scalability, Result types eliminate
hidden exceptions, and events enable observability and loose coupling.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path
from uuid import uuid4

from .result_types import Result, Success, Error, KnowledgeError, safe_call
from .types_advanced import (
    TechnologyName, BestPracticeName, ToolName, ToolDetails, 
    KnowledgeSource, CacheProvider, KnowledgeManagerConfig,
    TechnologyMapping, is_valid_technology_mapping, is_valid_tool_details
)
from .performance import (
    async_read_text_file, async_load_json_file, 
    monitor_performance, performance_tracker, LazyEvaluator, lazy
)
from .events import (
    event_bus, EventType, Event, 
    PromptGenerationStartedEvent, PerformanceThresholdExceededEvent
)
from .utils import safe_path_join

logger = logging.getLogger(__name__)


class AsyncKnowledgeManager(KnowledgeSource):
    """
    Modern async knowledge manager with comprehensive error handling and monitoring.
    
    Implements all modern patterns:
    - Async I/O by default
    - Result types for error handling
    - Performance monitoring
    - Event-driven architecture
    - Advanced type safety
    - Lazy evaluation
    """
    
    def __init__(self, config: KnowledgeManagerConfig):
        """
        Initialize with comprehensive configuration.
        
        Args:
            config: Validated configuration object.
        """
        self.config = config
        self.knowledge_base_root = Path(
            config.base_path if config.base_path 
            else Path(config.config_path).parent.parent
        )
        
        # Async-safe cache
        self._cache: Dict[str, any] = {}
        self._cache_lock = asyncio.Lock()
        
        # Lazy-loaded tech stack mapping
        self._tech_stack_mapping = lazy(
            lambda: asyncio.create_task(self._load_tech_stack_mapping())
        )
        
        # Performance tracking
        self._operation_semaphore = asyncio.Semaphore(config.max_concurrent_operations)
        
        logger.info(f"Initialized AsyncKnowledgeManager with config: {config}")
    
    @monitor_performance("load_tech_stack_mapping")
    async def _load_tech_stack_mapping(self) -> Union[Success[Dict[str, TechnologyMapping]], Error[KnowledgeError]]:
        """
        Async load of technology stack mapping with Result error handling.
        
        Returns:
            Result containing tech stack mapping or error details.
        """
        async with self._operation_semaphore:
            result = await async_load_json_file(self.config.config_path)
            
            if result.is_error():
                error = result.error
                return Error(KnowledgeError(
                    message=f"Failed to load tech stack mapping: {error.message}",
                    source="AsyncKnowledgeManager._load_tech_stack_mapping",
                    details=error.details
                ))
            
            data = result.unwrap()
            
            # Validate structure
            for tech_name, tech_data in data.items():
                if not is_valid_technology_mapping(tech_data):
                    return Error(KnowledgeError(
                        message=f"Invalid technology mapping structure for '{tech_name}'",
                        source="AsyncKnowledgeManager._load_tech_stack_mapping",
                        details=f"Expected keys: best_practices, tools"
                    ))
            
            logger.info(f"Loaded {len(data)} technology mappings")
            return Success(data)
    
    async def get_best_practices(self, technology: TechnologyName) -> Union[Success[List[BestPracticeName]], Error[KnowledgeError]]:
        """
        Get best practice names for a technology.
        
        Args:
            technology: Technology name to look up.
            
        Returns:
            Result containing list of best practice names or error.
        """
        correlation_id = uuid4()
        
        # Publish start event
        await event_bus.publish(Event(
            event_type=EventType.KNOWLEDGE_CACHE_HIT if technology in self._cache else EventType.KNOWLEDGE_CACHE_MISS,
            source="AsyncKnowledgeManager",
            correlation_id=correlation_id,
            payload={'operation': 'get_best_practices', 'technology': technology}
        ))
        
        async with self._operation_semaphore:
            # Get tech stack mapping (lazy loaded)
            if not self._tech_stack_mapping.is_computed:
                mapping_result = await self._tech_stack_mapping.get()
                if mapping_result.is_error():
                    return mapping_result  # type: ignore
                tech_mapping = mapping_result.unwrap()
            else:
                tech_mapping = (await self._tech_stack_mapping.get()).unwrap()
            
            if technology not in tech_mapping:
                return Success([])  # Return empty list for unknown technologies
            
            best_practices = tech_mapping[technology].get('best_practices', [])
            
            # Convert to typed names
            typed_names = [BestPracticeName(name) for name in best_practices]
            
            performance_tracker.record_cache_hit("get_best_practices") if technology in self._cache else performance_tracker.record_cache_miss("get_best_practices")
            
            return Success(typed_names)
    
    async def get_tools(self, technology: TechnologyName) -> Union[Success[List[ToolName]], Error[KnowledgeError]]:
        """
        Get tool names for a technology.
        
        Args:
            technology: Technology name to look up.
            
        Returns:
            Result containing list of tool names or error.
        """
        async with self._operation_semaphore:
            # Get tech stack mapping (lazy loaded)
            if not self._tech_stack_mapping.is_computed:
                mapping_result = await self._tech_stack_mapping.get()
                if mapping_result.is_error():
                    return mapping_result  # type: ignore
                tech_mapping = mapping_result.unwrap()
            else:
                tech_mapping = (await self._tech_stack_mapping.get()).unwrap()
            
            if technology not in tech_mapping:
                return Success([])
            
            tools = tech_mapping[technology].get('tools', [])
            
            # Convert to typed names
            typed_names = [ToolName(name) for name in tools]
            
            return Success(typed_names)
    
    @monitor_performance("get_best_practice_details")
    async def get_best_practice_details(self, name: BestPracticeName) -> Union[Success[str], Error[KnowledgeError]]:
        """
        Get detailed content for a best practice.
        
        Args:
            name: Best practice name.
            
        Returns:
            Result containing best practice content or error.
        """
        # Generate cache key
        cache_key = f"bp_details_{name}"
        
        # Check cache first (with async lock)
        async with self._cache_lock:
            if cache_key in self._cache:
                performance_tracker.record_cache_hit("get_best_practice_details")
                return Success(self._cache[cache_key])
        
        performance_tracker.record_cache_miss("get_best_practice_details")
        
        # Build file path safely
        filename = f"{name.lower().replace(' ', '_')}.md"
        filepath = safe_path_join(
            str(self.knowledge_base_root), 
            "knowledge_base", 
            "best_practices", 
            filename
        )
        
        # Read file asynchronously
        result = await async_read_text_file(filepath)
        
        if result.is_success():
            content = result.unwrap()
            
            # Cache the result
            async with self._cache_lock:
                self._cache[cache_key] = content
            
            logger.debug(f"Loaded best practice details for '{name}' ({len(content)} chars)")
            return Success(content)
        else:
            return result  # Pass through the error
    
    @monitor_performance("get_tool_details")
    async def get_tool_details(self, name: ToolName) -> Union[Success[ToolDetails], Error[KnowledgeError]]:
        """
        Get detailed information for a tool.
        
        Args:
            name: Tool name.
            
        Returns:
            Result containing tool details or error.
        """
        # Generate cache key
        cache_key = f"tool_details_{name}"
        
        # Check cache first
        async with self._cache_lock:
            if cache_key in self._cache:
                performance_tracker.record_cache_hit("get_tool_details")
                return Success(self._cache[cache_key])
        
        performance_tracker.record_cache_miss("get_tool_details")
        
        # Build file path safely
        filename = f"{name.lower().replace(' ', '_')}.json"
        filepath = safe_path_join(
            str(self.knowledge_base_root),
            "knowledge_base",
            "tools",
            filename
        )
        
        # Load JSON asynchronously
        result = await async_load_json_file(filepath)
        
        if result.is_error():
            return result  # type: ignore
        
        data = result.unwrap()
        
        # Validate structure
        if not is_valid_tool_details(data):
            return Error(KnowledgeError(
                message=f"Invalid tool details structure for '{name}'",
                source="AsyncKnowledgeManager.get_tool_details",
                details=f"Required keys: name, description. Got: {list(data.keys())}"
            ))
        
        # Cache the result
        async with self._cache_lock:
            self._cache[cache_key] = data
        
        logger.debug(f"Loaded tool details for '{name}'")
        return Success(data)  # type: ignore
    
    async def clear_cache(self) -> None:
        """Clear all cached data."""
        async with self._cache_lock:
            self._cache.clear()
            
        # Invalidate lazy evaluators
        self._tech_stack_mapping.invalidate()
        
        logger.info("Cleared knowledge manager cache")
    
    async def preload_data(self, technologies: List[TechnologyName]) -> Union[Success[None], Error[KnowledgeError]]:
        """
        Preload data for specified technologies to improve performance.
        
        Args:
            technologies: List of technologies to preload.
            
        Returns:
            Result indicating success or failure.
        """
        try:
            # Preload tech stack mapping
            if not self._tech_stack_mapping.is_computed:
                mapping_result = await self._tech_stack_mapping.get()
                if mapping_result.is_error():
                    return mapping_result  # type: ignore
            
            # Preload best practices and tools for each technology
            tasks = []
            for tech in technologies:
                # Get best practices list
                bp_result = await self.get_best_practices(tech)
                if bp_result.is_success():
                    for bp_name in bp_result.unwrap():
                        tasks.append(self.get_best_practice_details(bp_name))
                
                # Get tools list
                tools_result = await self.get_tools(tech)
                if tools_result.is_success():
                    for tool_name in tools_result.unwrap():
                        tasks.append(self.get_tool_details(tool_name))
            
            # Execute all preload tasks concurrently
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Preloaded data for {len(technologies)} technologies")
            return Success(None)
            
        except Exception as e:
            return Error(KnowledgeError(
                message="Failed to preload data",
                source="AsyncKnowledgeManager.preload_data",
                details=str(e)
            ))
    
    async def health_check(self) -> Union[Success[Dict[str, Any]], Error[KnowledgeError]]:
        """
        Perform health check on the knowledge manager.
        
        Returns:
            Result containing health status information.
        """
        try:
            # Check if tech stack mapping can be loaded
            mapping_result = await self._tech_stack_mapping.get()
            if mapping_result.is_error():
                return Error(KnowledgeError(
                    message="Health check failed: cannot load tech stack mapping",
                    source="AsyncKnowledgeManager.health_check",
                    details=str(mapping_result.error)
                ))
            
            tech_mapping = mapping_result.unwrap()
            
            health_info = {
                'status': 'healthy',
                'technologies_count': len(tech_mapping),
                'cache_size': len(self._cache),
                'knowledge_base_root': str(self.knowledge_base_root),
                'config': {
                    'max_concurrent_operations': self.config.max_concurrent_operations,
                    'cache_strategy': self.config.cache_strategy
                }
            }
            
            return Success(health_info)
            
        except Exception as e:
            return Error(KnowledgeError(
                message="Health check failed with exception",
                source="AsyncKnowledgeManager.health_check",
                details=str(e)
            ))


# Factory function for creating configured instances
def create_async_knowledge_manager(
    config_path: str,
    base_path: Optional[str] = None,
    **kwargs
) -> AsyncKnowledgeManager:
    """
    Factory function to create properly configured AsyncKnowledgeManager.
    
    Args:
        config_path: Path to tech stack mapping configuration.
        base_path: Optional base path for knowledge base.
        **kwargs: Additional configuration options.
        
    Returns:
        Configured AsyncKnowledgeManager instance.
    """
    config = KnowledgeManagerConfig(
        config_path=config_path,
        base_path=base_path,
        **kwargs
    )
    
    return AsyncKnowledgeManager(config)