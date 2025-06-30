"""
Enterprise Dependency Injection Container with lifecycle management.
"""

from typing import Dict, Type, Any, TypeVar, Callable, Optional, List
from abc import ABC, abstractmethod
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
import inspect
import weakref
from contextlib import asynccontextmanager

from .interfaces import *
from .config import WebResearchConfig, ConfigurationManager


T = TypeVar('T')


class ServiceScope(Enum):
    """Service lifecycle scopes."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Describes a service registration."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    scope: ServiceScope = ServiceScope.TRANSIENT
    dependencies: List[Type] = None
    initialized: bool = False


class ServiceNotRegisteredException(Exception):
    """Raised when requested service is not registered."""
    pass


class CircularDependencyException(Exception):
    """Raised when circular dependency is detected."""
    pass


class IServiceContainer(ABC):
    """Interface for dependency injection container."""
    
    @abstractmethod
    async def register_singleton(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register service as singleton."""
        pass
    
    @abstractmethod
    async def register_transient(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register service as transient."""
        pass
    
    @abstractmethod
    async def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register existing instance."""
        pass
    
    @abstractmethod
    async def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register factory function."""
        pass
    
    @abstractmethod
    async def resolve(self, service_type: Type[T]) -> T:
        """Resolve service instance."""
        pass
    
    @abstractmethod
    async def resolve_all(self, service_type: Type[T]) -> List[T]:
        """Resolve all instances of service type."""
        pass


class ServiceContainer(IServiceContainer):
    """
    Enterprise-grade dependency injection container with:
    - Automatic dependency resolution
    - Circular dependency detection
    - Lifecycle management
    - Async support
    """
    
    def __init__(self, config: Optional[WebResearchConfig] = None):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._resolving: set = set()  # For circular dependency detection
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self._logger = logging.getLogger(__name__)
        self._config = config or ConfigurationManager.get_config()
        
        # Weak references for cleanup
        self._singleton_refs: Dict[Type, weakref.ref] = {}
    
    async def register_singleton(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register service as singleton - one instance per container."""
        await self._register_service(
            service_type, 
            implementation_type, 
            ServiceScope.SINGLETON
        )
    
    async def register_transient(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register service as transient - new instance each time."""
        await self._register_service(
            service_type, 
            implementation_type, 
            ServiceScope.TRANSIENT
        )
    
    async def register_scoped(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register service as scoped - one instance per scope."""
        await self._register_service(
            service_type, 
            implementation_type, 
            ServiceScope.SCOPED
        )
    
    async def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register existing instance as singleton."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            instance=instance,
            scope=ServiceScope.SINGLETON,
            initialized=True
        )
        self._services[service_type] = descriptor
        self._logger.debug(f"Registered instance for {service_type.__name__}")
    
    async def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register factory function."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            scope=ServiceScope.TRANSIENT
        )
        self._services[service_type] = descriptor
        self._logger.debug(f"Registered factory for {service_type.__name__}")
    
    async def _register_service(
        self, 
        service_type: Type[T], 
        implementation_type: Type[T],
        scope: ServiceScope
    ) -> None:
        """Internal service registration."""
        dependencies = await self._analyze_dependencies(implementation_type)
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            scope=scope,
            dependencies=dependencies
        )
        
        self._services[service_type] = descriptor
        self._logger.debug(
            f"Registered {scope.value} service: {service_type.__name__} -> {implementation_type.__name__}"
        )
    
    async def resolve(self, service_type: Type[T]) -> T:
        """Resolve service with dependency injection."""
        if service_type in self._resolving:
            raise CircularDependencyException(
                f"Circular dependency detected for {service_type.__name__}"
            )
        
        self._resolving.add(service_type)
        try:
            return await self._resolve_internal(service_type)
        finally:
            self._resolving.discard(service_type)
    
    async def resolve_all(self, service_type: Type[T]) -> List[T]:
        """Resolve all registered implementations of service type."""
        implementations = [
            descriptor for descriptor in self._services.values()
            if issubclass(descriptor.implementation_type or type(descriptor.instance), service_type)
        ]
        
        instances = []
        for descriptor in implementations:
            instance = await self._create_instance(descriptor)
            instances.append(instance)
        
        return instances
    
    async def _resolve_internal(self, service_type: Type[T]) -> T:
        """Internal resolution logic."""
        if service_type not in self._services:
            raise ServiceNotRegisteredException(f"Service {service_type.__name__} not registered")
        
        descriptor = self._services[service_type]
        
        # Handle different scopes
        if descriptor.scope == ServiceScope.SINGLETON:
            return await self._resolve_singleton(descriptor)
        elif descriptor.scope == ServiceScope.SCOPED:
            return await self._resolve_scoped(descriptor)
        else:  # TRANSIENT
            return await self._create_instance(descriptor)
    
    async def _resolve_singleton(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve singleton instance."""
        if descriptor.instance is not None:
            return descriptor.instance
        
        # Check weak reference first
        if descriptor.service_type in self._singleton_refs:
            instance = self._singleton_refs[descriptor.service_type]()
            if instance is not None:
                return instance
        
        # Create new instance
        instance = await self._create_instance(descriptor)
        descriptor.instance = instance
        
        # Store weak reference for cleanup
        self._singleton_refs[descriptor.service_type] = weakref.ref(instance)
        
        return instance
    
    async def _resolve_scoped(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve scoped instance."""
        if self._current_scope is None:
            raise RuntimeError("No active scope for scoped service resolution")
        
        if self._current_scope not in self._scoped_instances:
            self._scoped_instances[self._current_scope] = {}
        
        scope_instances = self._scoped_instances[self._current_scope]
        
        if descriptor.service_type in scope_instances:
            return scope_instances[descriptor.service_type]
        
        instance = await self._create_instance(descriptor)
        scope_instances[descriptor.service_type] = instance
        
        return instance
    
    async def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create service instance with dependency injection."""
        if descriptor.factory is not None:
            # Use factory function
            if asyncio.iscoroutinefunction(descriptor.factory):
                return await descriptor.factory()
            else:
                return descriptor.factory()
        
        if descriptor.instance is not None:
            return descriptor.instance
        
        if descriptor.implementation_type is None:
            raise ValueError(f"No implementation registered for {descriptor.service_type.__name__}")
        
        # Resolve dependencies
        resolved_dependencies = []
        if descriptor.dependencies:
            for dep_type in descriptor.dependencies:
                dependency = await self.resolve(dep_type)
                resolved_dependencies.append(dependency)
        
        # Create instance
        if asyncio.iscoroutinefunction(descriptor.implementation_type.__init__):
            instance = descriptor.implementation_type(*resolved_dependencies)
            if hasattr(instance, '__aenter__'):
                # Async context manager
                await instance.__aenter__()
        else:
            instance = descriptor.implementation_type(*resolved_dependencies)
        
        # Call initialization if available
        if hasattr(instance, 'initialize') and asyncio.iscoroutinefunction(instance.initialize):
            await instance.initialize()
        
        descriptor.initialized = True
        self._logger.debug(f"Created instance of {descriptor.implementation_type.__name__}")
        
        return instance
    
    async def _analyze_dependencies(self, implementation_type: Type) -> List[Type]:
        """Analyze constructor dependencies."""
        if not hasattr(implementation_type, '__init__'):
            return []
        
        sig = inspect.signature(implementation_type.__init__)
        dependencies = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty:
                dependencies.append(param.annotation)
        
        return dependencies
    
    @asynccontextmanager
    async def create_scope(self, scope_name: str = None):
        """Create a new dependency scope."""
        scope_name = scope_name or f"scope_{id(self)}"
        old_scope = self._current_scope
        self._current_scope = scope_name
        
        try:
            yield self
        finally:
            # Cleanup scoped instances
            if scope_name in self._scoped_instances:
                for instance in self._scoped_instances[scope_name].values():
                    if hasattr(instance, '__aexit__'):
                        await instance.__aexit__(None, None, None)
                    elif hasattr(instance, 'dispose') and asyncio.iscoroutinefunction(instance.dispose):
                        await instance.dispose()
                
                del self._scoped_instances[scope_name]
            
            self._current_scope = old_scope
    
    async def dispose(self) -> None:
        """Dispose container and cleanup resources."""
        # Dispose all scoped instances
        for scope_instances in self._scoped_instances.values():
            for instance in scope_instances.values():
                if hasattr(instance, '__aexit__'):
                    await instance.__aexit__(None, None, None)
                elif hasattr(instance, 'dispose') and asyncio.iscoroutinefunction(instance.dispose):
                    await instance.dispose()
        
        # Dispose singletons
        for descriptor in self._services.values():
            if descriptor.scope == ServiceScope.SINGLETON and descriptor.instance:
                if hasattr(descriptor.instance, '__aexit__'):
                    await descriptor.instance.__aexit__(None, None, None)
                elif hasattr(descriptor.instance, 'dispose') and asyncio.iscoroutinefunction(descriptor.instance.dispose):
                    await descriptor.instance.dispose()
        
        self._services.clear()
        self._scoped_instances.clear()
        self._singleton_refs.clear()
        
        self._logger.info("Service container disposed")


class ServiceContainerBuilder:
    """Builder for configuring service container."""
    
    def __init__(self, config: Optional[WebResearchConfig] = None):
        self._container = ServiceContainer(config)
        self._logger = logging.getLogger(__name__)
    
    def add_singleton(self, service_type: Type[T], implementation_type: Type[T]) -> 'ServiceContainerBuilder':
        """Add singleton service."""
        asyncio.create_task(self._container.register_singleton(service_type, implementation_type))
        return self
    
    def add_transient(self, service_type: Type[T], implementation_type: Type[T]) -> 'ServiceContainerBuilder':
        """Add transient service."""
        asyncio.create_task(self._container.register_transient(service_type, implementation_type))
        return self
    
    def add_scoped(self, service_type: Type[T], implementation_type: Type[T]) -> 'ServiceContainerBuilder':
        """Add scoped service."""
        asyncio.create_task(self._container.register_scoped(service_type, implementation_type))
        return self
    
    def add_instance(self, service_type: Type[T], instance: T) -> 'ServiceContainerBuilder':
        """Add instance."""
        asyncio.create_task(self._container.register_instance(service_type, instance))
        return self
    
    def add_factory(self, service_type: Type[T], factory: Callable[[], T]) -> 'ServiceContainerBuilder':
        """Add factory."""
        asyncio.create_task(self._container.register_factory(service_type, factory))
        return self
    
    async def build(self) -> ServiceContainer:
        """Build configured container."""
        # Wait for all registrations to complete
        await asyncio.sleep(0.1)  # Allow pending registrations to complete
        
        self._logger.info(f"Built service container with {len(self._container._services)} services")
        return self._container


# Global container instance for convenience
_global_container: Optional[ServiceContainer] = None


async def get_container() -> ServiceContainer:
    """Get global service container instance."""
    global _global_container
    if _global_container is None:
        _global_container = await ServiceContainerBuilder().build()
    return _global_container


async def reset_container() -> None:
    """Reset global container."""
    global _global_container
    if _global_container:
        await _global_container.dispose()
    _global_container = None