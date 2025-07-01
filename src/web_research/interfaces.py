"""
Enterprise-grade interfaces following SOLID principles and dependency inversion.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime


class SearchProviderType(Enum):
    """Enumeration of available search providers."""
    DUCKDUCKGO = "duckduckgo"
    BING = "bing"
    GOOGLE = "google"
    CUSTOM = "custom"


class ResearchQuality(Enum):
    """Quality levels for research results."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class SearchResult:
    """Data transfer object for search results."""
    title: str
    url: str
    snippet: str
    score: float
    timestamp: datetime
    source_credibility: float = 0.5


@dataclass
class ResearchResult:
    """Comprehensive research result for a technology."""
    technology: str
    search_results: List[SearchResult]
    best_practices: List[str]
    code_examples: List[str]
    documentation_urls: List[str]
    quality_score: float
    research_timestamp: datetime
    confidence_level: float


@dataclass
class TechnologyProfile:
    """Profile of a technology with metadata."""
    name: str
    category: str
    maturity_level: str
    popularity_score: float
    official_docs_url: Optional[str] = None
    github_repo: Optional[str] = None
    stack_overflow_tag: Optional[str] = None


class ISearchProvider(ABC):
    """Interface for web search providers."""
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Perform web search for given query."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass


class ICacheProvider(ABC):
    """Interface for caching mechanisms."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve cached item."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store item in cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        pass


class ITechnologyDetector(ABC):
    """Interface for detecting unknown technologies."""
    
    @abstractmethod
    async def detect_unknown_technologies(self, technologies: List[str]) -> List[str]:
        """Identify technologies not in knowledge base."""
        pass
    
    @abstractmethod
    async def get_technology_profile(self, technology: str) -> Optional[TechnologyProfile]:
        """Get detailed profile for a technology."""
        pass
    
    @abstractmethod
    async def suggest_similar_technologies(self, technology: str) -> List[str]:
        """Suggest similar known technologies."""
        pass


class IResearchValidator(ABC):
    """Interface for validating research quality."""
    
    @abstractmethod
    async def validate_research_result(self, result: ResearchResult) -> ResearchQuality:
        """Validate quality of research result."""
        pass
    
    @abstractmethod
    async def validate_source_credibility(self, url: str) -> float:
        """Validate credibility of a source URL."""
        pass
    
    @abstractmethod
    async def extract_code_examples(self, content: str, technology: str) -> List[str]:
        """Extract relevant code examples from content."""
        pass


class IDynamicTemplateGenerator(ABC):
    """Interface for generating dynamic templates."""
    
    @abstractmethod
    async def generate_template(self, research: ResearchResult) -> str:
        """Generate template from research results."""
        pass
    
    @abstractmethod
    async def enhance_existing_template(self, template: str, research: ResearchResult) -> str:
        """Enhance existing template with new research."""
        pass
    
    @abstractmethod
    async def validate_template_quality(self, template: str) -> float:
        """Validate generated template quality."""
        pass


class ICircuitBreaker(ABC):
    """Interface for circuit breaker pattern."""
    
    @abstractmethod
    async def call(self, func, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        pass
    
    @abstractmethod
    def is_open(self) -> bool:
        """Check if circuit is open."""
        pass
    
    @abstractmethod
    async def reset(self) -> None:
        """Reset circuit breaker."""
        pass


class IWebResearcher(ABC):
    """Interface for web research orchestration."""
    
    @abstractmethod
    async def research_technology(
        self, 
        technology: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ResearchResult:
        """Research a single technology comprehensively."""
        pass
    
    @abstractmethod
    async def research_technologies_batch(
        self, 
        technologies: List[str],
        max_concurrent: int = 3
    ) -> Dict[str, ResearchResult]:
        """Research multiple technologies concurrently."""
        pass
    
    @abstractmethod
    async def get_research_suggestions(self, technology: str) -> List[str]:
        """Get suggested research queries for technology."""
        pass


class ITemplateCache(ABC):
    """Interface for template caching with versioning."""
    
    @abstractmethod
    async def store_template(
        self, 
        technology: str, 
        template: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Store generated template with version."""
        pass
    
    @abstractmethod
    async def get_template(
        self, 
        technology: str, 
        version: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve template by technology and version."""
        pass
    
    @abstractmethod
    async def list_template_versions(self, technology: str) -> List[str]:
        """List available template versions."""
        pass
    
    @abstractmethod
    async def invalidate_technology(self, technology: str) -> bool:
        """Invalidate all templates for technology."""
        pass


class IResearchOrchestrator(ABC):
    """Main orchestrator interface for the research workflow."""
    
    @abstractmethod
    async def process_unknown_technologies(
        self,
        technologies: List[str],
        user_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Main workflow: detect unknown technologies, research them,
        generate templates, and return results.
        """
        pass
    
    @abstractmethod
    async def get_research_progress(self, session_id: str) -> Dict[str, Any]:
        """Get progress of ongoing research session."""
        pass
    
    @abstractmethod
    async def approve_research_result(
        self, 
        technology: str, 
        approved: bool,
        feedback: Optional[str] = None
    ) -> bool:
        """Handle user approval/rejection of research results."""
        pass