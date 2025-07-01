"""
Enterprise Web Search Providers with multiple API support and failover.
"""

import asyncio
import aiohttp
import json
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from abc import ABC, abstractmethod

from .interfaces import ISearchProvider, SearchResult
from .config import SearchProviderConfig
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig


class SearchProviderFactory:
    """Factory for creating search provider instances."""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class):
        """Register a new search provider type."""
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def create_provider(
        cls, 
        config: SearchProviderConfig,
        circuit_breaker: Optional[CircuitBreaker] = None
    ) -> ISearchProvider:
        """Create search provider instance."""
        if config.provider_type not in cls._providers:
            raise ValueError(f"Unknown provider type: {config.provider_type}")
        
        provider_class = cls._providers[config.provider_type]
        return provider_class(config, circuit_breaker)


class BaseSearchProvider(ISearchProvider):
    """Base class for search providers with common functionality."""
    
    def __init__(self, config: SearchProviderConfig, circuit_breaker: Optional[CircuitBreaker] = None):
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.provider_name}")
        self._session: Optional[aiohttp.ClientSession] = None
        self._circuit_breaker = circuit_breaker
        
        # Rate limiting
        self._last_request_time = 0.0
        self._request_interval = 60.0 / config.rate_limit_per_minute
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': 'Prompt-Engineering-CLI/1.0'}
            )
        return self._session
    
    async def _rate_limit(self) -> None:
        """Apply rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._request_interval:
            sleep_time = self._request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Perform search with circuit breaker protection."""
        if not self.config.enabled:
            return []
        
        if self._circuit_breaker:
            return await self._circuit_breaker.call(
                self._search_internal, query, max_results
            )
        else:
            return await self._search_internal(query, max_results)
    
    @abstractmethod
    async def _search_internal(self, query: str, max_results: int) -> List[SearchResult]:
        """Internal search implementation."""
        pass
    
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            # Simple search with minimal query
            results = await self._search_internal("test", 1)
            return len(results) >= 0  # Even empty results indicate API is working
        except Exception as e:
            self._logger.warning(f"Health check failed for {self.provider_name}: {e}")
            return False
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _parse_search_result(self, item: Dict[str, Any]) -> Optional[SearchResult]:
        """Parse search result item. Override in subclasses."""
        return None
    
    def _calculate_relevance_score(self, title: str, snippet: str, query: str) -> float:
        """Calculate relevance score for search result."""
        query_lower = query.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        score = 0.0
        
        # Title matches (higher weight)
        if query_lower in title_lower:
            score += 0.5
        
        # Snippet matches
        if query_lower in snippet_lower:
            score += 0.3
        
        # Word matches
        query_words = query_lower.split()
        title_words = title_lower.split()
        snippet_words = snippet_lower.split()
        
        title_matches = sum(1 for word in query_words if word in title_words)
        snippet_matches = sum(1 for word in query_words if word in snippet_words)
        
        score += (title_matches / len(query_words)) * 0.3
        score += (snippet_matches / len(query_words)) * 0.2
        
        return min(score, 1.0)


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """DuckDuckGo search provider (no API key required)."""
    
    @property
    def provider_name(self) -> str:
        return "duckduckgo"
    
    async def _search_internal(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo Instant Answer API."""
        await self._rate_limit()
        
        # Use DuckDuckGo's instant answer API
        search_url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        session = await self._get_session()
        results = []
        
        try:
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse instant answer
                    if data.get('Abstract'):
                        results.append(SearchResult(
                            title=data.get('Heading', query),
                            url=data.get('AbstractURL', ''),
                            snippet=data.get('Abstract', ''),
                            score=self._calculate_relevance_score(
                                data.get('Heading', ''), 
                                data.get('Abstract', ''), 
                                query
                            ),
                            timestamp=datetime.now(),
                            source_credibility=0.8
                        ))
                    
                    # Parse related topics
                    for topic in data.get('RelatedTopics', [])[:max_results-1]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append(SearchResult(
                                title=topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                                url=topic.get('FirstURL', ''),
                                snippet=topic.get('Text', ''),
                                score=self._calculate_relevance_score(
                                    topic.get('Text', ''), 
                                    topic.get('Text', ''), 
                                    query
                                ),
                                timestamp=datetime.now(),
                                source_credibility=0.7
                            ))
        
        except Exception as e:
            self._logger.error(f"DuckDuckGo search failed: {e}")
            raise
        
        # Fallback: Try HTML scraping approach (more comprehensive)
        if len(results) < max_results:
            html_results = await self._search_html_fallback(query, max_results - len(results))
            results.extend(html_results)
        
        return results[:max_results]
    
    async def _search_html_fallback(self, query: str, max_results: int) -> List[SearchResult]:
        """Fallback HTML scraping approach."""
        search_url = "https://duckduckgo.com/html/"
        params = {'q': query}
        
        session = await self._get_session()
        results = []
        
        try:
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    html_content = await response.text()
                    results = self._parse_html_results(html_content, query, max_results)
        except Exception as e:
            self._logger.warning(f"HTML fallback failed: {e}")
        
        return results
    
    def _parse_html_results(self, html: str, query: str, max_results: int) -> List[SearchResult]:
        """Parse HTML search results."""
        results = []
        
        # Simple regex patterns for extracting results
        # Note: This is a simplified approach - in production, use proper HTML parsing
        title_pattern = r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<a[^>]+class="result__snippet"[^>]*>([^<]+)</a>'
        
        title_matches = re.findall(title_pattern, html)
        snippet_matches = re.findall(snippet_pattern, html)
        
        for i, (url, title) in enumerate(title_matches[:max_results]):
            snippet = snippet_matches[i] if i < len(snippet_matches) else ""
            
            # Clean up URL (DuckDuckGo uses redirect URLs)
            if url.startswith('/l/?uddg='):
                url = urllib.parse.unquote(url.split('uddg=')[1])
            
            results.append(SearchResult(
                title=title.strip(),
                url=url,
                snippet=snippet.strip(),
                score=self._calculate_relevance_score(title, snippet, query),
                timestamp=datetime.now(),
                source_credibility=0.7
            ))
        
        return results


class BingSearchProvider(BaseSearchProvider):
    """Bing search provider using Azure Cognitive Services."""
    
    @property
    def provider_name(self) -> str:
        return "bing"
    
    async def _search_internal(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Bing Web Search API."""
        if not self.config.api_key:
            raise ValueError("Bing API key is required")
        
        await self._rate_limit()
        
        search_url = "https://api.cognitive.microsoft.com/bing/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': self.config.api_key,
            'Content-Type': 'application/json'
        }
        params = {
            'q': query,
            'count': min(max_results, 50),  # Bing limit
            'responseFilter': 'Webpages',
            'textFormat': 'Raw'
        }
        
        session = await self._get_session()
        results = []
        
        try:
            async with session.get(search_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('webPages', {}).get('value', []):
                        result = self._parse_bing_result(item, query)
                        if result:
                            results.append(result)
                elif response.status == 429:
                    self._logger.warning("Bing API rate limit exceeded")
                    raise Exception("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    self._logger.error(f"Bing API error {response.status}: {error_text}")
                    raise Exception(f"Bing API error: {response.status}")
        
        except Exception as e:
            self._logger.error(f"Bing search failed: {e}")
            raise
        
        return results
    
    def _parse_bing_result(self, item: Dict[str, Any], query: str) -> Optional[SearchResult]:
        """Parse Bing search result."""
        try:
            return SearchResult(
                title=item.get('name', ''),
                url=item.get('url', ''),
                snippet=item.get('snippet', ''),
                score=self._calculate_relevance_score(
                    item.get('name', ''), 
                    item.get('snippet', ''), 
                    query
                ),
                timestamp=datetime.now(),
                source_credibility=0.9  # Bing generally has high quality results
            )
        except Exception as e:
            self._logger.warning(f"Failed to parse Bing result: {e}")
            return None


class CustomSearchProvider(BaseSearchProvider):
    """Custom search provider for specialized APIs."""
    
    def __init__(self, config: SearchProviderConfig, circuit_breaker: Optional[CircuitBreaker] = None):
        super().__init__(config, circuit_breaker)
        self._base_url = config.base_url or "https://api.example.com/search"
    
    @property
    def provider_name(self) -> str:
        return "custom"
    
    async def _search_internal(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using custom API."""
        await self._rate_limit()
        
        headers = {}
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        
        params = {
            'q': query,
            'limit': max_results
        }
        
        session = await self._get_session()
        results = []
        
        try:
            async with session.get(self._base_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('results', []):
                        result = self._parse_custom_result(item, query)
                        if result:
                            results.append(result)
                else:
                    error_text = await response.text()
                    self._logger.error(f"Custom API error {response.status}: {error_text}")
                    raise Exception(f"Custom API error: {response.status}")
        
        except Exception as e:
            self._logger.error(f"Custom search failed: {e}")
            raise
        
        return results
    
    def _parse_custom_result(self, item: Dict[str, Any], query: str) -> Optional[SearchResult]:
        """Parse custom API result."""
        try:
            return SearchResult(
                title=item.get('title', ''),
                url=item.get('url', ''),
                snippet=item.get('description', ''),
                score=item.get('relevance_score', self._calculate_relevance_score(
                    item.get('title', ''), 
                    item.get('description', ''), 
                    query
                )),
                timestamp=datetime.now(),
                source_credibility=item.get('credibility', 0.6)
            )
        except Exception as e:
            self._logger.warning(f"Failed to parse custom result: {e}")
            return None


class MultiProviderSearchOrchestrator:
    """Orchestrates multiple search providers with failover and result aggregation."""
    
    def __init__(self, providers: List[ISearchProvider]):
        self.providers = providers
        self._logger = logging.getLogger(__name__)
    
    async def search(
        self, 
        query: str, 
        max_results: int = 10,
        merge_results: bool = True
    ) -> List[SearchResult]:
        """Search using multiple providers with failover."""
        all_results = []
        
        # Try providers in order until we get results
        for provider in self.providers:
            try:
                if not provider.config.enabled:
                    continue
                
                self._logger.debug(f"Searching with provider: {provider.provider_name}")
                results = await provider.search(query, max_results)
                
                if results:
                    all_results.extend(results)
                    self._logger.info(
                        f"Provider {provider.provider_name} returned {len(results)} results"
                    )
                    
                    if not merge_results:
                        break  # Use only first successful provider
                
            except Exception as e:
                self._logger.warning(
                    f"Provider {provider.provider_name} failed: {e}"
                )
                continue
        
        if merge_results and all_results:
            # Deduplicate and merge results
            all_results = self._deduplicate_results(all_results)
            # Sort by relevance score
            all_results.sort(key=lambda x: x.score, reverse=True)
        
        return all_results[:max_results]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL similarity."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # Normalize URL for comparison
            normalized_url = self._normalize_url(result.url)
            
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)
        
        return unique_results
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        # Remove protocol and www
        normalized = re.sub(r'^https?://(www\.)?', '', url)
        # Remove trailing slash
        normalized = normalized.rstrip('/')
        # Remove query parameters and fragments
        normalized = normalized.split('?')[0].split('#')[0]
        return normalized.lower()
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        health_status = {}
        
        for provider in self.providers:
            try:
                is_healthy = await provider.health_check()
                health_status[provider.provider_name] = is_healthy
            except Exception as e:
                self._logger.error(f"Health check failed for {provider.provider_name}: {e}")
                health_status[provider.provider_name] = False
        
        return health_status
    
    async def close_all(self) -> None:
        """Close all provider sessions."""
        for provider in self.providers:
            try:
                if hasattr(provider, 'close'):
                    await provider.close()
            except Exception as e:
                self._logger.error(f"Failed to close provider {provider.provider_name}: {e}")


# Register providers with factory
SearchProviderFactory.register_provider("duckduckgo", DuckDuckGoSearchProvider)
SearchProviderFactory.register_provider("bing", BingSearchProvider)
SearchProviderFactory.register_provider("custom", CustomSearchProvider)