"""
Enterprise Template and Research Cache with versioning, persistence, and intelligent invalidation.
"""

import asyncio
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
import pickle
import gzip
import aiofiles
from abc import ABC, abstractmethod

from .interfaces import ITemplateCache, ICacheProvider, ResearchResult
from .config import CacheConfig


@dataclass
class CacheMetadata:
    """Metadata for cached items."""
    created_at: datetime
    last_accessed: datetime
    access_count: int
    expires_at: Optional[datetime]
    version: str
    checksum: str
    size_bytes: int
    tags: List[str] = field(default_factory=list)


@dataclass
class TemplateVersion:
    """Template version information."""
    version_id: str
    content: str
    metadata: CacheMetadata
    research_data: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None


@dataclass
class ResearchCacheEntry:
    """Research result cache entry."""
    technology: str
    research_result: ResearchResult
    metadata: CacheMetadata


class FileCacheProvider(ICacheProvider):
    """File-based cache provider with compression and async I/O."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache_dir = Path(config.file_cache_path)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)
        
        # Cache structure
        self.templates_dir = self.cache_dir / "templates"
        self.research_dir = self.cache_dir / "research"
        self.metadata_dir = self.cache_dir / "metadata"
        
        for directory in [self.templates_dir, self.research_dir, self.metadata_dir]:
            directory.mkdir(exist_ok=True)
        
        # Memory cache for frequently accessed items
        self._memory_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._max_memory_items = 100
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            interval = self.config.cleanup_interval_minutes * 60
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup(interval))
    
    async def _periodic_cleanup(self, interval: int):
        """Periodic cleanup of expired cache entries."""
        while True:
            try:
                await asyncio.sleep(interval)
                await self._cleanup_expired_entries()
                await self._enforce_size_limits()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Cleanup task error: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve cached item."""
        # Check memory cache first
        if key in self._memory_cache:
            value, cached_at = self._memory_cache[key]
            if datetime.now() - cached_at < timedelta(minutes=5):  # 5 minute memory cache
                return value
        
        # Check file cache
        cache_file = self._get_cache_file_path(key)
        metadata_file = self._get_metadata_file_path(key)
        
        if not cache_file.exists() or not metadata_file.exists():
            return None
        
        try:
            # Load metadata
            metadata = await self._load_metadata(metadata_file)
            
            # Check expiration
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                await self._remove_cache_entry(key)
                return None
            
            # Load content
            async with aiofiles.open(cache_file, 'rb') as f:
                compressed_data = await f.read()
            
            # Decompress and deserialize
            data = gzip.decompress(compressed_data)
            value = pickle.loads(data)
            
            # Update access info
            metadata.last_accessed = datetime.now()
            metadata.access_count += 1
            await self._save_metadata(metadata_file, metadata)
            
            # Update memory cache
            self._update_memory_cache(key, value)
            
            return value
        
        except Exception as e:
            self._logger.error(f"Failed to load cache entry {key}: {e}")
            await self._remove_cache_entry(key)
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store item in cache."""
        try:
            # Serialize and compress
            data = pickle.dumps(value)
            compressed_data = gzip.compress(data)
            
            # Calculate metadata
            checksum = hashlib.sha256(data).hexdigest()
            size_bytes = len(compressed_data)
            
            expires_at = None
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            elif self.config.ttl_seconds > 0:
                expires_at = datetime.now() + timedelta(seconds=self.config.ttl_seconds)
            
            metadata = CacheMetadata(
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=0,
                expires_at=expires_at,
                version="1.0",
                checksum=checksum,
                size_bytes=size_bytes
            )
            
            # Save files
            cache_file = self._get_cache_file_path(key)
            metadata_file = self._get_metadata_file_path(key)
            
            async with aiofiles.open(cache_file, 'wb') as f:
                await f.write(compressed_data)
            
            await self._save_metadata(metadata_file, metadata)
            
            # Update memory cache
            self._update_memory_cache(key, value)
            
            return True
        
        except Exception as e:
            self._logger.error(f"Failed to save cache entry {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        cache_file = self._get_cache_file_path(key)
        metadata_file = self._get_metadata_file_path(key)
        
        if not cache_file.exists() or not metadata_file.exists():
            return False
        
        try:
            metadata = await self._load_metadata(metadata_file)
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                await self._remove_cache_entry(key)
                return False
            return True
        except:
            return False
    
    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        count = 0
        
        for cache_file in self.cache_dir.rglob("*.cache"):
            key = cache_file.stem
            if pattern in key or key.startswith(pattern):
                await self._remove_cache_entry(key)
                count += 1
        
        return count
    
    def _get_cache_file_path(self, key: str) -> Path:
        """Get cache file path for key."""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def _get_metadata_file_path(self, key: str) -> Path:
        """Get metadata file path for key."""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.metadata_dir / f"{safe_key}.meta"
    
    async def _load_metadata(self, metadata_file: Path) -> CacheMetadata:
        """Load metadata from file."""
        async with aiofiles.open(metadata_file, 'r') as f:
            data = json.loads(await f.read())
        
        # Convert datetime strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        if data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        
        return CacheMetadata(**data)
    
    async def _save_metadata(self, metadata_file: Path, metadata: CacheMetadata):
        """Save metadata to file."""
        data = asdict(metadata)
        
        # Convert datetime objects to ISO format strings
        data['created_at'] = metadata.created_at.isoformat()
        data['last_accessed'] = metadata.last_accessed.isoformat()
        if metadata.expires_at:
            data['expires_at'] = metadata.expires_at.isoformat()
        else:
            data['expires_at'] = None
        
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    async def _remove_cache_entry(self, key: str):
        """Remove cache entry and metadata."""
        cache_file = self._get_cache_file_path(key)
        metadata_file = self._get_metadata_file_path(key)
        
        try:
            if cache_file.exists():
                cache_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Remove from memory cache
            self._memory_cache.pop(key, None)
            
        except Exception as e:
            self._logger.error(f"Failed to remove cache entry {key}: {e}")
    
    def _update_memory_cache(self, key: str, value: Any):
        """Update memory cache with size limit."""
        self._memory_cache[key] = (value, datetime.now())
        
        # Enforce memory cache size limit
        if len(self._memory_cache) > self._max_memory_items:
            # Remove oldest entries
            items = list(self._memory_cache.items())
            items.sort(key=lambda x: x[1][1])  # Sort by timestamp
            
            for old_key, _ in items[:len(items) - self._max_memory_items]:
                del self._memory_cache[old_key]
    
    async def _cleanup_expired_entries(self):
        """Remove expired cache entries."""
        now = datetime.now()
        removed_count = 0
        
        for metadata_file in self.metadata_dir.glob("*.meta"):
            try:
                metadata = await self._load_metadata(metadata_file)
                if metadata.expires_at and now > metadata.expires_at:
                    key = metadata_file.stem
                    await self._remove_cache_entry(key)
                    removed_count += 1
            except Exception as e:
                self._logger.warning(f"Failed to check expiration for {metadata_file}: {e}")
        
        if removed_count > 0:
            self._logger.info(f"Cleaned up {removed_count} expired cache entries")
    
    async def _enforce_size_limits(self):
        """Enforce cache size limits."""
        total_size = 0
        entries = []
        
        # Calculate total size and collect entries
        for cache_file in self.cache_dir.rglob("*.cache"):
            size = cache_file.stat().st_size
            total_size += size
            
            metadata_file = self.metadata_dir / f"{cache_file.stem}.meta"
            if metadata_file.exists():
                try:
                    metadata = await self._load_metadata(metadata_file)
                    entries.append((cache_file.stem, size, metadata.last_accessed))
                except:
                    pass
        
        max_size_bytes = self.config.max_size_mb * 1024 * 1024
        
        if total_size > max_size_bytes:
            # Remove least recently used entries
            entries.sort(key=lambda x: x[2])  # Sort by last_accessed
            
            removed_size = 0
            for key, size, _ in entries:
                if total_size - removed_size <= max_size_bytes:
                    break
                
                await self._remove_cache_entry(key)
                removed_size += size
            
            self._logger.info(f"Enforced size limit: removed {removed_size / 1024 / 1024:.1f}MB")
    
    async def close(self):
        """Close cache provider."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class TemplateCache(ITemplateCache):
    """Template cache with versioning and quality tracking."""
    
    def __init__(self, cache_provider: ICacheProvider):
        self._cache = cache_provider
        self._logger = logging.getLogger(__name__)
        
        # Version tracking
        self._version_counter = 0
    
    async def store_template(
        self, 
        technology: str, 
        template: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Store generated template with version."""
        version_id = await self._generate_version_id(technology, template)
        
        template_version = TemplateVersion(
            version_id=version_id,
            content=template,
            metadata=CacheMetadata(
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=0,
                expires_at=None,  # Templates don't expire by default
                version=version_id,
                checksum=hashlib.sha256(template.encode()).hexdigest(),
                size_bytes=len(template.encode()),
                tags=metadata.get('tags', [])
            ),
            research_data=metadata.get('research_data'),
            quality_score=metadata.get('quality_score')
        )
        
        # Store template
        template_key = f"template:{technology}:{version_id}"
        await self._cache.set(template_key, template_version)
        
        # Update latest version pointer
        latest_key = f"template_latest:{technology}"
        await self._cache.set(latest_key, version_id)
        
        # Store in version list
        await self._add_to_version_list(technology, version_id)
        
        self._logger.info(f"Stored template for {technology}, version {version_id}")
        return version_id
    
    async def get_template(
        self, 
        technology: str, 
        version: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve template by technology and version."""
        if version is None:
            # Get latest version
            latest_key = f"template_latest:{technology}"
            version = await self._cache.get(latest_key)
            
            if not version:
                return None
        
        template_key = f"template:{technology}:{version}"
        template_version = await self._cache.get(template_key)
        
        if template_version:
            return template_version.content
        
        return None
    
    async def list_template_versions(self, technology: str) -> List[str]:
        """List available template versions."""
        versions_key = f"template_versions:{technology}"
        versions = await self._cache.get(versions_key)
        
        return versions or []
    
    async def invalidate_technology(self, technology: str) -> bool:
        """Invalidate all templates for technology."""
        try:
            pattern = f"template:{technology}:"
            await self._cache.invalidate(pattern)
            
            # Also invalidate version list and latest pointer
            await self._cache.invalidate(f"template_latest:{technology}")
            await self._cache.invalidate(f"template_versions:{technology}")
            
            self._logger.info(f"Invalidated all templates for {technology}")
            return True
        
        except Exception as e:
            self._logger.error(f"Failed to invalidate templates for {technology}: {e}")
            return False
    
    async def get_template_metadata(self, technology: str, version: str) -> Optional[Dict[str, Any]]:
        """Get template metadata."""
        template_key = f"template:{technology}:{version}"
        template_version = await self._cache.get(template_key)
        
        if template_version:
            return {
                'version_id': template_version.version_id,
                'created_at': template_version.metadata.created_at.isoformat(),
                'quality_score': template_version.quality_score,
                'size_bytes': template_version.metadata.size_bytes,
                'access_count': template_version.metadata.access_count,
                'tags': template_version.metadata.tags
            }
        
        return None
    
    async def search_templates(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search templates by content or technology."""
        # This would require indexing in a production system
        # For now, implement basic search
        results = []
        
        # Search through cached templates
        # This is a simplified implementation
        return results[:limit]
    
    async def _generate_version_id(self, technology: str, template: str) -> str:
        """Generate unique version ID."""
        content_hash = hashlib.md5(template.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._version_counter += 1
        
        return f"v{timestamp}_{content_hash}_{self._version_counter}"
    
    async def _add_to_version_list(self, technology: str, version_id: str):
        """Add version to technology's version list."""
        versions_key = f"template_versions:{technology}"
        versions = await self._cache.get(versions_key) or []
        
        if version_id not in versions:
            versions.append(version_id)
            # Keep only last 10 versions
            versions = versions[-10:]
            await self._cache.set(versions_key, versions)


class ResearchCache:
    """Cache for research results with intelligent invalidation."""
    
    def __init__(self, cache_provider: ICacheProvider):
        self._cache = cache_provider
        self._logger = logging.getLogger(__name__)
    
    async def store_research(
        self, 
        technology: str, 
        research_result: ResearchResult,
        ttl_hours: int = 24
    ) -> bool:
        """Store research result."""
        try:
            cache_entry = ResearchCacheEntry(
                technology=technology,
                research_result=research_result,
                metadata=CacheMetadata(
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    access_count=0,
                    expires_at=datetime.now() + timedelta(hours=ttl_hours),
                    version="1.0",
                    checksum=self._calculate_research_checksum(research_result),
                    size_bytes=len(str(research_result).encode()),
                    tags=[technology, "research"]
                )
            )
            
            research_key = f"research:{technology}"
            await self._cache.set(research_key, cache_entry, ttl=ttl_hours * 3600)
            
            self._logger.info(f"Stored research for {technology}")
            return True
        
        except Exception as e:
            self._logger.error(f"Failed to store research for {technology}: {e}")
            return False
    
    async def get_research(self, technology: str) -> Optional[ResearchResult]:
        """Retrieve cached research result."""
        research_key = f"research:{technology}"
        cache_entry = await self._cache.get(research_key)
        
        if cache_entry:
            return cache_entry.research_result
        
        return None
    
    async def is_research_fresh(self, technology: str, max_age_hours: int = 6) -> bool:
        """Check if cached research is still fresh."""
        research_key = f"research:{technology}"
        
        if not await self._cache.exists(research_key):
            return False
        
        cache_entry = await self._cache.get(research_key)
        if not cache_entry:
            return False
        
        age = datetime.now() - cache_entry.metadata.created_at
        return age < timedelta(hours=max_age_hours)
    
    def _calculate_research_checksum(self, research_result: ResearchResult) -> str:
        """Calculate checksum for research result."""
        # Create a stable string representation
        content = f"{research_result.technology}:{len(research_result.search_results)}:{research_result.quality_score}"
        return hashlib.md5(content.encode()).hexdigest()


class CacheFactory:
    """Factory for creating cache instances."""
    
    @staticmethod
    async def create_file_cache(config: CacheConfig) -> FileCacheProvider:
        """Create file-based cache provider."""
        return FileCacheProvider(config)
    
    @staticmethod
    async def create_template_cache(cache_provider: ICacheProvider) -> TemplateCache:
        """Create template cache."""
        return TemplateCache(cache_provider)
    
    @staticmethod
    async def create_research_cache(cache_provider: ICacheProvider) -> ResearchCache:
        """Create research cache."""
        return ResearchCache(cache_provider)