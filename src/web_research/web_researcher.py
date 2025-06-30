"""
Enterprise Web Researcher - Main orchestrator for automatic technology research.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
from dataclasses import dataclass, field

from .interfaces import (
    IWebResearcher, IResearchOrchestrator, ResearchResult, SearchResult,
    ITechnologyDetector, IResearchValidator, IDynamicTemplateGenerator,
    ITemplateCache, ResearchQuality
)
from .config import WebResearchConfig
from .search_providers import MultiProviderSearchOrchestrator, SearchProviderFactory
from .technology_detector import TechnologyDetector
from .template_generator import DynamicTemplateGenerator
from .research_validator import ResearchValidator
from .research_cache import CacheFactory, ResearchCache
from .circuit_breaker import CircuitBreakerManager


@dataclass
class ResearchSession:
    """Tracks a research session."""
    session_id: str
    technologies: List[str]
    user_context: Dict[str, Any]
    progress: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, str] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    status: str = "in_progress"


@dataclass
class ResearchProgress:
    """Progress tracking for research operations."""
    total_technologies: int
    completed: int
    current_technology: Optional[str]
    stage: str  # detecting, researching, validating, generating, caching
    estimated_time_remaining: Optional[int] = None
    errors: List[str] = field(default_factory=list)


class WebResearcher(IWebResearcher):
    """
    Main web researcher implementation with full orchestration capabilities.
    """
    
    def __init__(
        self,
        config: WebResearchConfig,
        search_orchestrator: MultiProviderSearchOrchestrator,
        circuit_breaker_manager: CircuitBreakerManager
    ):
        self.config = config
        self._search_orchestrator = search_orchestrator
        self._circuit_breaker_manager = circuit_breaker_manager
        self._logger = logging.getLogger(__name__)
        
        # Progress tracking
        self._progress_callbacks: List[Callable[[str, ResearchProgress], None]] = []
        
    async def research_technology(
        self, 
        technology: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ResearchResult:
        """Research a single technology comprehensively."""
        self._logger.info(f"Starting research for technology: {technology}")
        
        try:
            # Generate research queries
            queries = await self.get_research_suggestions(technology)
            
            # Perform searches
            all_results = []
            for query in queries:
                search_results = await self._search_orchestrator.search(
                    query, 
                    max_results=self.config.research.max_search_results_per_query
                )
                all_results.extend(search_results)
            
            # Remove duplicates and filter by relevance
            unique_results = self._deduplicate_results(all_results)
            relevant_results = await self._filter_relevant_results(unique_results, technology)
            
            # Extract best practices and code examples
            best_practices = await self._extract_best_practices(relevant_results, technology)
            code_examples = await self._extract_code_examples(relevant_results, technology)
            documentation_urls = self._extract_documentation_urls(relevant_results)
            
            # Calculate quality score
            quality_score = await self._calculate_quality_score(
                relevant_results, best_practices, code_examples
            )
            
            # Create research result
            research_result = ResearchResult(
                technology=technology,
                search_results=relevant_results,
                best_practices=best_practices,
                code_examples=code_examples,
                documentation_urls=documentation_urls,
                quality_score=quality_score,
                research_timestamp=datetime.now(),
                confidence_level=min(1.0, quality_score + 0.1)
            )
            
            self._logger.info(
                f"Research completed for {technology}: "
                f"quality={quality_score:.2f}, results={len(relevant_results)}"
            )
            
            return research_result
        
        except Exception as e:
            self._logger.error(f"Research failed for {technology}: {e}")
            raise
    
    async def research_technologies_batch(
        self, 
        technologies: List[str],
        max_concurrent: int = 3
    ) -> Dict[str, ResearchResult]:
        """Research multiple technologies concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def research_with_semaphore(tech: str) -> tuple[str, ResearchResult]:
            async with semaphore:
                result = await self.research_technology(tech)
                return tech, result
        
        # Create tasks
        tasks = [research_with_semaphore(tech) for tech in technologies]
        
        # Execute with progress tracking
        results = {}
        completed = 0
        
        for coro in asyncio.as_completed(tasks):
            try:
                tech, result = await coro
                results[tech] = result
                completed += 1
                
                # Update progress
                progress = ResearchProgress(
                    total_technologies=len(technologies),
                    completed=completed,
                    current_technology=tech,
                    stage="completed"
                )
                await self._notify_progress("batch_research", progress)
                
            except Exception as e:
                self._logger.error(f"Failed to research technology in batch: {e}")
        
        return results
    
    async def get_research_suggestions(self, technology: str) -> List[str]:
        """Get suggested research queries for technology."""
        base_queries = [
            f"{technology} tutorial",
            f"{technology} best practices",
            f"{technology} documentation",
            f"{technology} examples",
            f"how to use {technology}",
        ]
        
        # Add context-specific queries
        context_queries = []
        
        # Detect technology type and add specific queries
        tech_lower = technology.lower()
        
        if any(keyword in tech_lower for keyword in ['database', 'db', 'postgres', 'mysql']):
            context_queries.extend([
                f"{technology} configuration",
                f"{technology} performance tuning",
                f"{technology} backup strategy"
            ])
        elif any(keyword in tech_lower for keyword in ['framework', 'library', 'api']):
            context_queries.extend([
                f"{technology} getting started",
                f"{technology} production setup",
                f"{technology} security"
            ])
        elif any(keyword in tech_lower for keyword in ['cluster', 'orchestration', 'deploy']):
            context_queries.extend([
                f"{technology} setup guide",
                f"{technology} monitoring",
                f"{technology} troubleshooting"
            ])
        
        all_queries = base_queries + context_queries
        return all_queries[:self.config.research.research_queries_per_technology]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate search results."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            normalized_url = self._normalize_url(result.url)
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)
        
        return unique_results
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        import re
        # Remove protocol and www
        normalized = re.sub(r'^https?://(www\.)?', '', url)
        # Remove trailing slash and query parameters
        normalized = normalized.split('?')[0].split('#')[0].rstrip('/')
        return normalized.lower()
    
    async def _filter_relevant_results(
        self, 
        results: List[SearchResult], 
        technology: str
    ) -> List[SearchResult]:
        """Filter search results by relevance to technology."""
        relevant_results = []
        
        for result in results:
            relevance_score = self._calculate_relevance_score(result, technology)
            
            if relevance_score >= 0.3:  # Minimum relevance threshold
                # Update the result's score
                result.score = relevance_score
                relevant_results.append(result)
        
        # Sort by relevance and return top results
        relevant_results.sort(key=lambda x: x.score, reverse=True)
        return relevant_results[:20]  # Top 20 most relevant
    
    def _calculate_relevance_score(self, result: SearchResult, technology: str) -> float:
        """Calculate relevance score for a search result."""
        score = 0.0
        tech_lower = technology.lower()
        title_lower = result.title.lower()
        snippet_lower = result.snippet.lower()
        
        # Exact technology match in title (high weight)
        if tech_lower in title_lower:
            score += 0.4
        
        # Exact technology match in snippet
        if tech_lower in snippet_lower:
            score += 0.3
        
        # Related terms
        related_terms = self._get_related_technology_terms(technology)
        for term in related_terms:
            if term in title_lower:
                score += 0.1
            if term in snippet_lower:
                score += 0.05
        
        # Quality indicators
        quality_terms = ['tutorial', 'guide', 'documentation', 'example', 'best practice']
        for term in quality_terms:
            if term in title_lower:
                score += 0.1
            if term in snippet_lower:
                score += 0.05
        
        return min(1.0, score)
    
    def _get_related_technology_terms(self, technology: str) -> List[str]:
        """Get related terms for a technology."""
        tech_lower = technology.lower()
        
        related_map = {
            'python': ['django', 'flask', 'fastapi', 'pip', 'virtualenv'],
            'javascript': ['node', 'npm', 'react', 'vue', 'angular'],
            'docker': ['container', 'image', 'compose', 'dockerfile'],
            'kubernetes': ['k8s', 'pod', 'deployment', 'service', 'kubectl'],
            'postgresql': ['postgres', 'pg', 'database', 'sql'],
            'ansible': ['playbook', 'yaml', 'role', 'inventory'],
            'prometheus': ['monitoring', 'metrics', 'alerting', 'grafana'],
            'patroni': ['postgres', 'cluster', 'ha', 'failover']
        }
        
        # Find the best match
        for key, terms in related_map.items():
            if key in tech_lower or tech_lower in key:
                return terms
        
        return []
    
    async def _extract_best_practices(
        self, 
        results: List[SearchResult], 
        technology: str
    ) -> List[str]:
        """Extract best practices from search results."""
        best_practices = []
        
        for result in results:
            content = result.title + " " + result.snippet
            
            # Look for best practices patterns
            practices = self._extract_practices_from_content(content, technology)
            best_practices.extend(practices)
        
        # Deduplicate and sort by quality
        unique_practices = list(set(best_practices))
        return unique_practices[:10]  # Top 10 practices
    
    def _extract_practices_from_content(self, content: str, technology: str) -> List[str]:
        """Extract best practices from content."""
        import re
        practices = []
        
        # Patterns for best practices
        patterns = [
            r'best practice[s]?[:\-]?\s*(.+)',
            r'recommendation[s]?[:\-]?\s*(.+)',
            r'should\s+(always|never|use|avoid)\s+(.+)',
            r'important[:\-]?\s*(.+)',
            r'tip[s]?[:\-]?\s*(.+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                practice = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if len(practice.strip()) > 20:  # Minimum length
                    practices.append(practice.strip())
        
        return practices
    
    async def _extract_code_examples(
        self, 
        results: List[SearchResult], 
        technology: str
    ) -> List[str]:
        """Extract code examples from search results."""
        code_examples = []
        
        for result in results:
            content = result.snippet
            
            # Extract code blocks
            examples = self._extract_code_from_content(content, technology)
            code_examples.extend(examples)
        
        return code_examples[:5]  # Top 5 examples
    
    def _extract_code_from_content(self, content: str, technology: str) -> List[str]:
        """Extract code examples from content."""
        import re
        examples = []
        
        # Code block patterns
        patterns = [
            r'```(\w+)?\n(.*?)\n```',  # Markdown code blocks
            r'<code[^>]*>(.*?)</code>',  # HTML code tags
            r'`([^`\n]{20,})`',  # Long inline code
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                code = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if code and len(code.strip()) > 10:
                    examples.append(code.strip())
        
        return examples
    
    def _extract_documentation_urls(self, results: List[SearchResult]) -> List[str]:
        """Extract official documentation URLs."""
        doc_urls = []
        
        official_indicators = ['docs.', 'documentation', 'official', 'guide']
        
        for result in results:
            url_lower = result.url.lower()
            title_lower = result.title.lower()
            
            if any(indicator in url_lower or indicator in title_lower 
                   for indicator in official_indicators):
                doc_urls.append(result.url)
        
        return doc_urls[:5]  # Top 5 documentation URLs
    
    async def _calculate_quality_score(
        self, 
        results: List[SearchResult], 
        best_practices: List[str], 
        code_examples: List[str]
    ) -> float:
        """Calculate overall quality score for research."""
        if not results:
            return 0.0
        
        # Base score from number of results
        result_score = min(1.0, len(results) / 10)
        
        # Score from content richness
        practice_score = min(1.0, len(best_practices) / 8)
        code_score = min(1.0, len(code_examples) / 3)
        
        # Score from result quality
        avg_result_score = sum(r.score for r in results) / len(results)
        
        # Score from source diversity
        unique_domains = len(set(self._normalize_url(r.url) for r in results))
        diversity_score = min(1.0, unique_domains / 5)
        
        # Weighted average
        quality_score = (
            result_score * 0.2 +
            practice_score * 0.25 +
            code_score * 0.25 +
            avg_result_score * 0.2 +
            diversity_score * 0.1
        )
        
        return quality_score
    
    async def _notify_progress(self, session_id: str, progress: ResearchProgress):
        """Notify progress callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(session_id, progress)
            except Exception as e:
                self._logger.warning(f"Progress callback failed: {e}")
    
    def add_progress_callback(self, callback: Callable[[str, ResearchProgress], None]):
        """Add progress tracking callback."""
        self._progress_callbacks.append(callback)


class ResearchOrchestrator(IResearchOrchestrator):
    """
    Main orchestrator for the complete web research workflow.
    """
    
    def __init__(self, config: WebResearchConfig):
        self.config = config
        self._logger = logging.getLogger(__name__)
        
        # Initialize components - removed async call from constructor
        self._initialized = False
        
        # Session tracking
        self._active_sessions: Dict[str, ResearchSession] = {}
        
    async def _initialize_components(self):
        """Initialize all research components."""
        # Circuit breaker manager
        self._circuit_breaker_manager = CircuitBreakerManager(self.config.circuit_breaker)
        
        # Search providers
        search_providers = []
        for name, provider_config in self.config.search_providers.items():
            if provider_config.enabled:
                circuit_breaker = self._circuit_breaker_manager.get_breaker(f"search_{name}")
                provider = SearchProviderFactory.create_provider(provider_config, circuit_breaker)
                search_providers.append(provider)
        
        self._search_orchestrator = MultiProviderSearchOrchestrator(search_providers)
        
        # Core components
        self._technology_detector = TechnologyDetector(self.config)
        self._web_researcher = WebResearcher(
            self.config, 
            self._search_orchestrator, 
            self._circuit_breaker_manager
        )
        self._template_generator = DynamicTemplateGenerator(self.config)
        self._research_validator = ResearchValidator(self.config)
        
        # Cache components
        cache_provider = await CacheFactory.create_file_cache(self.config.cache)
        self._template_cache = await CacheFactory.create_template_cache(cache_provider)
        self._research_cache = await CacheFactory.create_research_cache(cache_provider)
        
        self._logger.info("Research orchestrator initialized successfully")
    
    async def process_unknown_technologies(
        self,
        technologies: List[str],
        user_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Main workflow: detect, research, validate, generate templates."""
        # Ensure initialization
        if not self._initialized:
            await self._initialize_components()
            self._initialized = True
            
        session_id = str(uuid.uuid4())
        session = ResearchSession(
            session_id=session_id,
            technologies=technologies,
            user_context=user_context
        )
        self._active_sessions[session_id] = session
        
        try:
            results = {}
            
            # 1. Detect unknown technologies
            self._logger.info(f"Session {session_id}: Detecting unknown technologies")
            unknown_technologies = await self._technology_detector.detect_unknown_technologies(technologies)
            
            if not unknown_technologies:
                self._logger.info("All technologies are known, using existing templates")
                # Use existing templates for known technologies
                for tech in technologies:
                    template = await self._template_cache.get_template(tech)
                    if template:
                        results[tech] = template
                    else:
                        # Generate from existing knowledge
                        results[tech] = await self._generate_basic_template(tech, user_context)
                return results
            
            # 2. Research unknown technologies
            self._logger.info(f"Session {session_id}: Researching {len(unknown_technologies)} technologies")
            research_results = {}
            
            for i, technology in enumerate(unknown_technologies):
                # Check cache first
                cached_research = await self._research_cache.get_research(technology)
                if cached_research and await self._research_cache.is_research_fresh(technology):
                    self._logger.info(f"Using cached research for {technology}")
                    research_results[technology] = cached_research
                else:
                    # Perform new research
                    self._logger.info(f"Researching {technology} ({i+1}/{len(unknown_technologies)})")
                    research_result = await self._web_researcher.research_technology(
                        technology, user_context
                    )
                    
                    # Validate research quality
                    quality = await self._research_validator.validate_research_result(research_result)
                    
                    if quality in [ResearchQuality.EXCELLENT, ResearchQuality.GOOD]:
                        research_results[technology] = research_result
                        # Cache research result
                        await self._research_cache.store_research(technology, research_result)
                    else:
                        self._logger.warning(f"Research quality for {technology} is {quality.value}")
                        # Could retry with different search strategy here
                        research_results[technology] = research_result  # Use anyway but mark as low quality
            
            # 3. Generate templates
            self._logger.info(f"Session {session_id}: Generating templates")
            # Extract specific options from user context
            specific_options = user_context.get('specific_options')
            
            for technology, research_result in research_results.items():
                try:
                    template = await self._template_generator.generate_template(
                        research_result, 
                        specific_options
                    )
                    
                    # Validate template quality
                    template_quality = await self._template_generator.validate_template_quality(template)
                    
                    if template_quality >= self.config.research.min_quality_threshold:
                        # Store in cache
                        await self._template_cache.store_template(
                            technology, 
                            template,
                            {
                                'research_data': research_result.__dict__,
                                'quality_score': template_quality,
                                'tags': ['generated', 'web_research']
                            }
                        )
                        
                        results[technology] = template
                        
                        # Learn about new technology
                        await self._technology_detector.learn_from_research(
                            technology, 
                            {'category': self._infer_technology_category(research_result)}
                        )
                        
                    else:
                        self._logger.warning(f"Generated template quality for {technology} too low: {template_quality}")
                        results[technology] = await self._generate_fallback_template(technology, research_result)
                
                except Exception as e:
                    self._logger.error(f"Template generation failed for {technology}: {e}")
                    results[technology] = await self._generate_fallback_template(technology, None)
            
            # 4. Update session
            session.results = results
            session.status = "completed"
            
            self._logger.info(f"Session {session_id}: Completed successfully with {len(results)} templates")
            return results
        
        except Exception as e:
            self._logger.error(f"Session {session_id}: Failed with error: {e}")
            session.status = "failed"
            raise
        
        finally:
            # Cleanup session after some time
            asyncio.create_task(self._cleanup_session(session_id, delay=300))  # 5 minutes
    
    async def get_research_progress(self, session_id: str) -> Dict[str, Any]:
        """Get progress of ongoing research session."""
        if session_id not in self._active_sessions:
            return {"error": "Session not found"}
        
        session = self._active_sessions[session_id]
        return {
            "session_id": session_id,
            "status": session.status,
            "technologies": session.technologies,
            "progress": session.progress,
            "results_count": len(session.results),
            "start_time": session.start_time.isoformat(),
            "elapsed_time": (datetime.now() - session.start_time).total_seconds()
        }
    
    async def approve_research_result(
        self, 
        technology: str, 
        approved: bool,
        feedback: Optional[str] = None
    ) -> bool:
        """Handle user approval/rejection of research results."""
        try:
            if approved:
                self._logger.info(f"Research result for {technology} approved by user")
                if feedback:
                    self._logger.info(f"User feedback: {feedback}")
                return True
            else:
                self._logger.info(f"Research result for {technology} rejected by user")
                if feedback:
                    self._logger.info(f"User feedback: {feedback}")
                
                # Invalidate cached research and template
                await self._research_cache._cache.invalidate(f"research:{technology}")
                await self._template_cache.invalidate_technology(technology)
                
                return False
        
        except Exception as e:
            self._logger.error(f"Failed to process approval for {technology}: {e}")
            return False
    
    async def _generate_basic_template(self, technology: str, context: Dict[str, Any]) -> str:
        """Generate basic template for known technology."""
        task_type = context.get('task_type', 'implementation')
        
        return f"""# {technology.title()} {task_type.title()}

## TASK
Implement: **{technology} {task_type}**

## EXPECTED OUTPUT EXAMPLE
```
# {technology} implementation example
# Specific implementation details will be provided
```

## REQUIREMENTS
Follow best practices and write clean, maintainable code

## IMPLEMENTATION STEPS
1. **Setup {technology} environment** following official documentation
2. **Implement core functionality** with proper error handling
3. **Add configuration management** for different environments
4. **Include comprehensive testing** (unit, integration)
5. **Setup monitoring and logging** for production readiness

## QUALITY CHECKLIST
After implementation, verify:
- [ ] {technology} implementation follows official guidelines
- [ ] Code is well-documented with clear comments
- [ ] Error handling is comprehensive and user-friendly
- [ ] Tests cover critical functionality and edge cases
- [ ] Configuration is externalized and environment-specific

Please implement step by step, explaining your choices for {technology} architecture and best practices."""
    
    async def _generate_fallback_template(self, technology: str, research_result: Optional[ResearchResult]) -> str:
        """Generate fallback template when main generation fails."""
        return await self._generate_basic_template(technology, {'task_type': 'development'})
    
    def _infer_technology_category(self, research_result: ResearchResult) -> str:
        """Infer technology category from research result."""
        technology = research_result.technology.lower()
        
        # Simple category inference
        if any(keyword in technology for keyword in ['database', 'postgres', 'mysql', 'mongo']):
            return 'database'
        elif any(keyword in technology for keyword in ['framework', 'library', 'react', 'vue', 'django']):
            return 'framework'
        elif any(keyword in technology for keyword in ['language', 'python', 'javascript', 'java']):
            return 'programming_language'
        elif any(keyword in technology for keyword in ['tool', 'deploy', 'docker', 'kubernetes']):
            return 'infrastructure'
        else:
            return 'unknown'
    
    async def _cleanup_session(self, session_id: str, delay: int = 300):
        """Cleanup session after delay."""
        await asyncio.sleep(delay)
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            self._logger.debug(f"Cleaned up session {session_id}")
    
    async def close(self):
        """Close orchestrator and cleanup resources."""
        if hasattr(self, '_search_orchestrator'):
            await self._search_orchestrator.close_all()
        
        self._logger.info("Research orchestrator closed")