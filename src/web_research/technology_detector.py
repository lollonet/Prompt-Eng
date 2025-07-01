"""
Enterprise Technology Detection with ML-based similarity matching and fuzzy search.
"""

import asyncio
import difflib
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .config import WebResearchConfig
from .interfaces import ITechnologyDetector, TechnologyProfile


@dataclass
class TechnologyKnowledge:
    """Internal knowledge about technologies."""

    known_technologies: Set[str] = field(default_factory=set)
    technology_aliases: Dict[str, List[str]] = field(default_factory=dict)
    technology_categories: Dict[str, str] = field(default_factory=dict)
    technology_popularity: Dict[str, float] = field(default_factory=dict)
    technology_maturity: Dict[str, str] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class SimilarityResult:
    """Result of similarity analysis."""

    technology: str
    similarity_score: float
    match_type: str  # exact, alias, fuzzy, category
    confidence: float


class TechnologyDetector(ITechnologyDetector):
    """
    Enterprise technology detector with:
    - Fuzzy string matching
    - Alias resolution
    - Category-based grouping
    - ML-based similarity scoring
    - Continuous learning
    """

    def __init__(self, config: WebResearchConfig, knowledge_base_path: Optional[str] = None):
        self.config = config
        self._knowledge_base_path = knowledge_base_path or "knowledge_base"
        self._logger = logging.getLogger(__name__)

        # Knowledge storage
        self._knowledge = TechnologyKnowledge()
        self._similarity_cache: Dict[str, List[SimilarityResult]] = {}

        # Configuration
        self._similarity_threshold = 0.7
        self._cache_ttl_hours = 24

        # Initialize knowledge base
        asyncio.create_task(self._initialize_knowledge_base())

    async def _initialize_knowledge_base(self) -> None:
        """Initialize technology knowledge base."""
        try:
            await self._load_existing_knowledge()
            await self._load_technology_mappings()
            await self._populate_default_knowledge()

            self._logger.info(
                f"Technology detector initialized with {len(self._knowledge.known_technologies)} technologies"
            )
        except Exception as e:
            self._logger.error(f"Failed to initialize knowledge base: {e}")
            await self._populate_default_knowledge()

    async def _load_existing_knowledge(self) -> None:
        """Load existing technology knowledge from files."""
        knowledge_file = Path(self._knowledge_base_path) / "technology_knowledge.json"

        if knowledge_file.exists():
            try:
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._knowledge.known_technologies = set(data.get("known_technologies", []))
                self._knowledge.technology_aliases = data.get("technology_aliases", {})
                self._knowledge.technology_categories = data.get("technology_categories", {})
                self._knowledge.technology_popularity = data.get("technology_popularity", {})
                self._knowledge.technology_maturity = data.get("technology_maturity", {})

                self._logger.info(f"Loaded existing knowledge base from {knowledge_file}")
            except Exception as e:
                self._logger.warning(f"Failed to load existing knowledge: {e}")

    async def _load_technology_mappings(self) -> None:
        """Load technology mappings from config files."""
        mapping_file = Path("config/tech_stack_mapping.json")

        if mapping_file.exists():
            try:
                with open(mapping_file, "r", encoding="utf-8") as f:
                    mappings = json.load(f)

                for tech_name in mappings.keys():
                    self._knowledge.known_technologies.add(tech_name.lower())

                    # Infer category from context
                    if any(
                        keyword in tech_name.lower()
                        for keyword in ["python", "java", "javascript", "go", "rust"]
                    ):
                        self._knowledge.technology_categories[tech_name.lower()] = (
                            "programming_language"
                        )
                    elif any(
                        keyword in tech_name.lower()
                        for keyword in ["react", "vue", "angular", "express"]
                    ):
                        self._knowledge.technology_categories[tech_name.lower()] = "framework"
                    elif any(
                        keyword in tech_name.lower()
                        for keyword in ["postgresql", "mysql", "mongodb", "redis"]
                    ):
                        self._knowledge.technology_categories[tech_name.lower()] = "database"
                    elif any(
                        keyword in tech_name.lower()
                        for keyword in ["docker", "kubernetes", "ansible"]
                    ):
                        self._knowledge.technology_categories[tech_name.lower()] = "infrastructure"

                self._logger.info(f"Loaded {len(mappings)} technologies from tech stack mapping")
            except Exception as e:
                self._logger.warning(f"Failed to load tech stack mapping: {e}")

    async def _populate_default_knowledge(self) -> None:
        """Populate default technology knowledge."""
        default_technologies = {
            # Programming Languages
            "python": {
                "category": "programming_language",
                "popularity": 0.95,
                "maturity": "mature",
            },
            "javascript": {
                "category": "programming_language",
                "popularity": 0.98,
                "maturity": "mature",
            },
            "typescript": {
                "category": "programming_language",
                "popularity": 0.85,
                "maturity": "mature",
            },
            "java": {"category": "programming_language", "popularity": 0.90, "maturity": "mature"},
            "go": {"category": "programming_language", "popularity": 0.75, "maturity": "mature"},
            "rust": {"category": "programming_language", "popularity": 0.65, "maturity": "growing"},
            # Web Frameworks
            "react": {"category": "frontend_framework", "popularity": 0.92, "maturity": "mature"},
            "vue": {"category": "frontend_framework", "popularity": 0.80, "maturity": "mature"},
            "angular": {"category": "frontend_framework", "popularity": 0.75, "maturity": "mature"},
            "svelte": {"category": "frontend_framework", "popularity": 0.60, "maturity": "growing"},
            "nextjs": {"category": "fullstack_framework", "popularity": 0.85, "maturity": "mature"},
            "express": {"category": "backend_framework", "popularity": 0.88, "maturity": "mature"},
            "fastapi": {"category": "backend_framework", "popularity": 0.80, "maturity": "mature"},
            "django": {"category": "backend_framework", "popularity": 0.82, "maturity": "mature"},
            "flask": {"category": "backend_framework", "popularity": 0.75, "maturity": "mature"},
            # Databases
            "postgresql": {"category": "database", "popularity": 0.90, "maturity": "mature"},
            "mysql": {"category": "database", "popularity": 0.85, "maturity": "mature"},
            "mongodb": {"category": "database", "popularity": 0.80, "maturity": "mature"},
            "redis": {"category": "cache_database", "popularity": 0.85, "maturity": "mature"},
            "elasticsearch": {
                "category": "search_database",
                "popularity": 0.75,
                "maturity": "mature",
            },
            # Infrastructure
            "docker": {"category": "containerization", "popularity": 0.95, "maturity": "mature"},
            "kubernetes": {"category": "orchestration", "popularity": 0.88, "maturity": "mature"},
            "ansible": {
                "category": "configuration_management",
                "popularity": 0.80,
                "maturity": "mature",
            },
            "terraform": {
                "category": "infrastructure_as_code",
                "popularity": 0.85,
                "maturity": "mature",
            },
            "prometheus": {"category": "monitoring", "popularity": 0.82, "maturity": "mature"},
            "grafana": {"category": "visualization", "popularity": 0.85, "maturity": "mature"},
            # Cloud Providers
            "aws": {"category": "cloud_provider", "popularity": 0.95, "maturity": "mature"},
            "azure": {"category": "cloud_provider", "popularity": 0.85, "maturity": "mature"},
            "gcp": {"category": "cloud_provider", "popularity": 0.75, "maturity": "mature"},
            # Specialized
            "patroni": {
                "category": "database_clustering",
                "popularity": 0.60,
                "maturity": "mature",
            },
            "etcd": {"category": "distributed_storage", "popularity": 0.70, "maturity": "mature"},
            "nagios": {"category": "monitoring", "popularity": 0.65, "maturity": "mature"},
        }

        # Common aliases
        default_aliases = {
            "js": ["javascript"],
            "ts": ["typescript"],
            "k8s": ["kubernetes"],
            "pg": ["postgresql"],
            "mongo": ["mongodb"],
            "next": ["nextjs"],
            "react.js": ["react"],
            "vue.js": ["vue"],
            "node": ["nodejs"],
            "npm": ["nodejs"],
            "yarn": ["nodejs"],
            "pip": ["python"],
            "maven": ["java"],
            "gradle": ["java"],
        }

        # Update knowledge
        for tech, info in default_technologies.items():
            self._knowledge.known_technologies.add(tech)
            self._knowledge.technology_categories[tech] = info["category"]
            self._knowledge.technology_popularity[tech] = info["popularity"]
            self._knowledge.technology_maturity[tech] = info["maturity"]

        self._knowledge.technology_aliases.update(default_aliases)

        self._logger.info(
            f"Populated default knowledge with {len(default_technologies)} technologies"
        )

    async def detect_unknown_technologies(self, technologies: List[str]) -> List[str]:
        """Identify technologies not in knowledge base."""
        unknown_technologies = []

        for tech in technologies:
            tech_normalized = tech.lower().strip()

            # Check direct match
            if tech_normalized in self._knowledge.known_technologies:
                continue

            # Check aliases
            if await self._is_known_alias(tech_normalized):
                continue

            # Check fuzzy matches
            similarity_results = await self._find_similar_technologies(tech_normalized)
            best_match = (
                max(similarity_results, key=lambda x: x.similarity_score)
                if similarity_results
                else None
            )

            if not best_match or best_match.similarity_score < self._similarity_threshold:
                unknown_technologies.append(tech)
                self._logger.info(f"Unknown technology detected: {tech}")
            else:
                self._logger.info(
                    f"Technology '{tech}' matched to known '{best_match.technology}' "
                    f"(similarity: {best_match.similarity_score:.2f})"
                )

        return unknown_technologies

    async def get_technology_profile(self, technology: str) -> Optional[TechnologyProfile]:
        """Get detailed profile for a technology."""
        tech_normalized = technology.lower().strip()

        # Check if technology is known
        if tech_normalized not in self._knowledge.known_technologies:
            # Try to find similar technology
            similarity_results = await self._find_similar_technologies(tech_normalized)
            if similarity_results:
                best_match = max(similarity_results, key=lambda x: x.similarity_score)
                if best_match.similarity_score >= self._similarity_threshold:
                    tech_normalized = best_match.technology
                else:
                    return None
            else:
                return None

        # Build profile
        profile = TechnologyProfile(
            name=tech_normalized,
            category=self._knowledge.technology_categories.get(tech_normalized, "unknown"),
            maturity_level=self._knowledge.technology_maturity.get(tech_normalized, "unknown"),
            popularity_score=self._knowledge.technology_popularity.get(tech_normalized, 0.5),
        )

        # Add additional metadata based on category
        await self._enrich_technology_profile(profile)

        return profile

    async def suggest_similar_technologies(self, technology: str) -> List[str]:
        """Suggest similar known technologies."""
        tech_normalized = technology.lower().strip()

        # Find similar technologies
        similarity_results = await self._find_similar_technologies(tech_normalized)

        # Filter and sort by similarity
        suggestions = [
            result.technology
            for result in similarity_results
            if result.similarity_score >= 0.3  # Lower threshold for suggestions
        ]

        # Add category-based suggestions
        profile = await self.get_technology_profile(technology)
        if profile and profile.category != "unknown":
            category_suggestions = [
                tech
                for tech, cat in self._knowledge.technology_categories.items()
                if cat == profile.category and tech not in suggestions
            ]
            suggestions.extend(category_suggestions[:3])  # Add top 3 from same category

        return suggestions[:5]  # Return top 5 suggestions

    async def _is_known_alias(self, technology: str) -> bool:
        """Check if technology is a known alias."""
        for aliases in self._knowledge.technology_aliases.values():
            if technology in aliases:
                return True

        return technology in self._knowledge.technology_aliases

    async def _find_similar_technologies(self, technology: str) -> List[SimilarityResult]:
        """Find similar technologies using multiple matching strategies."""
        # Check cache first
        cache_key = hashlib.md5(technology.encode()).hexdigest()
        if cache_key in self._similarity_cache:
            cached_result = self._similarity_cache[cache_key]
            # Check cache age
            if len(cached_result) > 0:  # Simple cache validity check
                return cached_result

        results = []

        # 1. Exact substring matches
        for known_tech in self._knowledge.known_technologies:
            if technology in known_tech or known_tech in technology:
                results.append(
                    SimilarityResult(
                        technology=known_tech,
                        similarity_score=0.9,
                        match_type="substring",
                        confidence=0.95,
                    )
                )

        # 2. Fuzzy string matching
        fuzzy_matches = difflib.get_close_matches(
            technology, self._knowledge.known_technologies, n=10, cutoff=0.6
        )

        for match in fuzzy_matches:
            similarity_score = difflib.SequenceMatcher(None, technology, match).ratio()
            results.append(
                SimilarityResult(
                    technology=match,
                    similarity_score=similarity_score,
                    match_type="fuzzy",
                    confidence=0.8,
                )
            )

        # 3. Alias matching
        for alias, target_techs in self._knowledge.technology_aliases.items():
            if technology == alias:
                for target_tech in target_techs:
                    results.append(
                        SimilarityResult(
                            technology=target_tech,
                            similarity_score=1.0,
                            match_type="alias",
                            confidence=1.0,
                        )
                    )

        # 4. Pattern-based matching (e.g., version numbers, variants)
        results.extend(await self._pattern_based_matching(technology))

        # Remove duplicates and sort by similarity
        unique_results = {}
        for result in results:
            if (
                result.technology not in unique_results
                or result.similarity_score > unique_results[result.technology].similarity_score
            ):
                unique_results[result.technology] = result

        final_results = sorted(
            unique_results.values(), key=lambda x: x.similarity_score, reverse=True
        )

        # Cache results
        self._similarity_cache[cache_key] = final_results

        return final_results

    async def _pattern_based_matching(self, technology: str) -> List[SimilarityResult]:
        """Pattern-based matching for technology variants."""
        results = []

        # Remove version numbers and common suffixes
        clean_tech = re.sub(r"[\d\.\-_]+$", "", technology)
        clean_tech = re.sub(r"(js|ts|py)$", "", clean_tech)

        if clean_tech != technology and clean_tech in self._knowledge.known_technologies:
            results.append(
                SimilarityResult(
                    technology=clean_tech,
                    similarity_score=0.85,
                    match_type="pattern_version",
                    confidence=0.9,
                )
            )

        # Check for common patterns
        patterns = {
            r"(.+)\.js$": lambda m: m.group(1),  # react.js -> react
            r"(.+)-cli$": lambda m: m.group(1),  # vue-cli -> vue
            r"(.+)-server$": lambda m: m.group(1),  # express-server -> express
            r"node-(.+)$": lambda m: m.group(1),  # node-express -> express
        }

        for pattern, extractor in patterns.items():
            match = re.match(pattern, technology)
            if match:
                extracted = extractor(match)
                if extracted in self._knowledge.known_technologies:
                    results.append(
                        SimilarityResult(
                            technology=extracted,
                            similarity_score=0.8,
                            match_type="pattern_extraction",
                            confidence=0.85,
                        )
                    )

        return results

    async def _enrich_technology_profile(self, profile: TechnologyProfile) -> None:
        """Enrich technology profile with additional metadata."""
        # Add common URLs based on technology name
        common_docs = {
            "react": "https://reactjs.org/docs",
            "vue": "https://vuejs.org/guide/",
            "angular": "https://angular.io/docs",
            "python": "https://docs.python.org/",
            "javascript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
            "typescript": "https://www.typescriptlang.org/docs/",
            "docker": "https://docs.docker.com/",
            "kubernetes": "https://kubernetes.io/docs/",
            "postgresql": "https://www.postgresql.org/docs/",
            "mongodb": "https://docs.mongodb.com/",
            "redis": "https://redis.io/documentation",
            "ansible": "https://docs.ansible.com/",
            "terraform": "https://www.terraform.io/docs/",
        }

        profile.official_docs_url = common_docs.get(profile.name)

        # Add GitHub repositories for open source projects
        github_repos = {
            "react": "https://github.com/facebook/react",
            "vue": "https://github.com/vuejs/vue",
            "angular": "https://github.com/angular/angular",
            "docker": "https://github.com/docker/docker-ce",
            "kubernetes": "https://github.com/kubernetes/kubernetes",
            "postgresql": "https://github.com/postgres/postgres",
            "mongodb": "https://github.com/mongodb/mongo",
            "redis": "https://github.com/redis/redis",
            "ansible": "https://github.com/ansible/ansible",
            "terraform": "https://github.com/hashicorp/terraform",
        }

        profile.github_repo = github_repos.get(profile.name)

        # Add Stack Overflow tags
        profile.stack_overflow_tag = profile.name.replace("-", "_")

    async def learn_from_research(self, technology: str, research_data: Dict[str, Any]) -> None:
        """Learn about new technology from research data."""
        tech_normalized = technology.lower().strip()

        # Add to known technologies
        self._knowledge.known_technologies.add(tech_normalized)

        # Extract category from research data
        if "category" in research_data:
            self._knowledge.technology_categories[tech_normalized] = research_data["category"]

        # Extract popularity score
        if "popularity_score" in research_data:
            self._knowledge.technology_popularity[tech_normalized] = research_data[
                "popularity_score"
            ]

        # Extract maturity level
        if "maturity_level" in research_data:
            self._knowledge.technology_maturity[tech_normalized] = research_data["maturity_level"]

        # Extract aliases
        if "aliases" in research_data:
            self._knowledge.technology_aliases[tech_normalized] = research_data["aliases"]

        # Save updated knowledge
        await self._save_knowledge()

        self._logger.info(f"Learned about new technology: {technology}")

    async def _save_knowledge(self) -> None:
        """Save technology knowledge to file."""
        knowledge_file = Path(self._knowledge_base_path) / "technology_knowledge.json"
        knowledge_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "known_technologies": list(self._knowledge.known_technologies),
            "technology_aliases": self._knowledge.technology_aliases,
            "technology_categories": self._knowledge.technology_categories,
            "technology_popularity": self._knowledge.technology_popularity,
            "technology_maturity": self._knowledge.technology_maturity,
            "last_updated": self._knowledge.last_updated.isoformat(),
        }

        try:
            with open(knowledge_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._logger.debug(f"Saved technology knowledge to {knowledge_file}")
        except Exception as e:
            self._logger.error(f"Failed to save knowledge: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics."""
        return {
            "total_known_technologies": len(self._knowledge.known_technologies),
            "total_aliases": len(self._knowledge.technology_aliases),
            "categories": len(set(self._knowledge.technology_categories.values())),
            "cache_size": len(self._similarity_cache),
            "last_updated": self._knowledge.last_updated.isoformat(),
        }
