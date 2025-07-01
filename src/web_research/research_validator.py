"""
Enterprise Research Validator with ML-based quality assessment and content validation.
"""

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from .config import WebResearchConfig
from .interfaces import IResearchValidator, ResearchQuality, ResearchResult, SearchResult


@dataclass
class ValidationResult:
    """Result of validation process."""

    is_valid: bool
    quality: ResearchQuality
    confidence: float
    issues: List[str]
    suggestions: List[str]
    metrics: Dict[str, float]


@dataclass
class SourceCredibilityMetrics:
    """Metrics for source credibility assessment."""

    domain_authority: float
    content_quality: float
    recency: float
    relevance: float
    technical_depth: float
    overall_score: float


class ResearchValidator(IResearchValidator):
    """
    Enterprise research validator with:
    - Content quality assessment
    - Source credibility validation
    - Code example extraction and validation
    - Bias detection
    - Completeness checking
    """

    def __init__(self, config: WebResearchConfig):
        self.config = config
        self._logger = logging.getLogger(__name__)

        # Quality thresholds
        self._min_search_results = 3
        self._min_quality_score = 0.6
        self._min_source_diversity = 2

        # Credible domains
        self._high_credibility_domains = self._load_credible_domains()
        self._low_credibility_domains = self._load_low_credibility_domains()

        # Content quality patterns
        self._quality_indicators = self._load_quality_indicators()
        self._spam_indicators = self._load_spam_indicators()

        # Code validation patterns
        self._code_patterns = self._load_code_patterns()

    def _load_credible_domains(self) -> Dict[str, float]:
        """Load high-credibility domains with scores."""
        return {
            # Official documentation
            "docs.python.org": 1.0,
            "kubernetes.io": 1.0,
            "docker.com": 1.0,
            "reactjs.org": 1.0,
            "postgresql.org": 1.0,
            "mongodb.com": 1.0,
            "redis.io": 1.0,
            "ansible.com": 1.0,
            "terraform.io": 1.0,
            "nginx.org": 1.0,
            # Major tech companies
            "github.com": 0.9,
            "stackoverflow.com": 0.85,
            "microsoft.com": 0.9,
            "aws.amazon.com": 0.95,
            "cloud.google.com": 0.95,
            "azure.microsoft.com": 0.95,
            # Technical communities
            "dev.to": 0.7,
            "medium.com": 0.6,
            "hackernoon.com": 0.65,
            "towardsdatascience.com": 0.75,
            # Academic and standards
            "ieee.org": 0.95,
            "w3.org": 0.95,
            "ietf.org": 0.95,
            "owasp.org": 0.9,
            # Enterprise blogs
            "blog.google": 0.8,
            "engineering.fb.com": 0.8,
            "netflixtechblog.com": 0.85,
            "eng.uber.com": 0.8,
        }

    def _load_low_credibility_domains(self) -> Set[str]:
        """Load domains with questionable credibility."""
        return {
            "contentfarms.com",
            "spamsite.org",
            "clickbait.net",
            # Add more as needed
        }

    def _load_quality_indicators(self) -> Dict[str, float]:
        """Load content quality indicators with weights."""
        return {
            # Positive indicators
            "code example": 0.3,
            "tutorial": 0.25,
            "documentation": 0.3,
            "best practice": 0.25,
            "production": 0.2,
            "enterprise": 0.2,
            "security": 0.15,
            "performance": 0.15,
            "testing": 0.1,
            "configuration": 0.1,
            "official": 0.3,
            "guide": 0.2,
            "how to": 0.15,
            "implementation": 0.2,
            "step by step": 0.15,
            "troubleshooting": 0.1,
            "comparison": 0.1,
            "benchmark": 0.15,
        }

    def _load_spam_indicators(self) -> Dict[str, float]:
        """Load spam/low-quality indicators with penalties."""
        return {
            "click here": -0.3,
            "amazing": -0.2,
            "incredible": -0.2,
            "ultimate": -0.15,
            "secret": -0.2,
            "hack": -0.15,
            "trick": -0.1,
            "guaranteed": -0.2,
            "instant": -0.15,
            "free download": -0.3,
            "limited time": -0.2,
            "act now": -0.2,
            "exclusive": -0.15,
        }

    def _load_code_patterns(self) -> Dict[str, List[str]]:
        """Load code validation patterns by language."""
        return {
            "python": [
                r"def\s+\w+\(",
                r"class\s+\w+",
                r"import\s+\w+",
                r"from\s+\w+\s+import",
                r'if\s+__name__\s*==\s*["\']__main__["\']',
            ],
            "javascript": [
                r"function\s+\w+\(",
                r"const\s+\w+\s*=",
                r"let\s+\w+\s*=",
                r"var\s+\w+\s*=",
                r"export\s+(default\s+)?",
                r'require\(["\'][^"\']+["\']\)',
            ],
            "yaml": [
                r"^\s*\w+:\s*$",
                r"^\s*-\s+\w+",
                r"apiVersion:\s*\w+",
                r"kind:\s*\w+",
                r"metadata:\s*$",
            ],
            "dockerfile": [
                r"^FROM\s+\w+",
                r"^RUN\s+",
                r"^COPY\s+",
                r"^ADD\s+",
                r"^EXPOSE\s+\d+",
                r"^CMD\s+",
                r"^ENTRYPOINT\s+",
            ],
            "sql": [
                r"\bSELECT\b",
                r"\bFROM\b",
                r"\bWHERE\b",
                r"\bINSERT\s+INTO\b",
                r"\bCREATE\s+TABLE\b",
                r"\bALTER\s+TABLE\b",
            ],
            "bash": [
                r"#!/bin/bash",
                r"\$\w+",
                r"if\s+\[.*\]",
                r"for\s+\w+\s+in",
                r"while\s+\[.*\]",
                r"echo\s+",
            ],
        }

    async def validate_research_result(self, result: ResearchResult) -> ResearchQuality:
        """Validate overall research quality."""
        validation = await self._comprehensive_validation(result)

        self._logger.info(
            f"Research validation for {result.technology}: "
            f"quality={validation.quality.value}, confidence={validation.confidence:.2f}"
        )

        return validation.quality

    async def _comprehensive_validation(self, result: ResearchResult) -> ValidationResult:
        """Perform comprehensive validation."""
        issues = []
        suggestions = []
        metrics = {}

        # 1. Quantity validation
        quantity_score = await self._validate_quantity(result, issues, suggestions)
        metrics["quantity"] = quantity_score

        # 2. Source diversity validation
        diversity_score = await self._validate_source_diversity(result, issues, suggestions)
        metrics["diversity"] = diversity_score

        # 3. Content quality validation
        content_score = await self._validate_content_quality(result, issues, suggestions)
        metrics["content_quality"] = content_score

        # 4. Source credibility validation
        credibility_score = await self._validate_source_credibility(result, issues, suggestions)
        metrics["credibility"] = credibility_score

        # 5. Technical depth validation
        depth_score = await self._validate_technical_depth(result, issues, suggestions)
        metrics["technical_depth"] = depth_score

        # 6. Recency validation
        recency_score = await self._validate_recency(result, issues, suggestions)
        metrics["recency"] = recency_score

        # 7. Bias detection
        bias_score = await self._detect_bias(result, issues, suggestions)
        metrics["bias_free"] = bias_score

        # Calculate overall score
        weights = {
            "quantity": 0.1,
            "diversity": 0.15,
            "content_quality": 0.25,
            "credibility": 0.2,
            "technical_depth": 0.15,
            "recency": 0.1,
            "bias_free": 0.05,
        }

        overall_score = sum(metrics[key] * weights[key] for key in weights)
        metrics["overall"] = overall_score

        # Determine quality level
        if overall_score >= 0.8:
            quality = ResearchQuality.EXCELLENT
        elif overall_score >= 0.7:
            quality = ResearchQuality.GOOD
        elif overall_score >= 0.6:
            quality = ResearchQuality.FAIR
        else:
            quality = ResearchQuality.POOR

        # Calculate confidence
        confidence = min(1.0, overall_score + 0.1)

        return ValidationResult(
            is_valid=overall_score >= self._min_quality_score,
            quality=quality,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics,
        )

    async def _validate_quantity(
        self, result: ResearchResult, issues: List[str], suggestions: List[str]
    ) -> float:
        """Validate quantity of search results."""
        count = len(result.search_results)

        if count < self._min_search_results:
            issues.append(f"Insufficient search results: {count} < {self._min_search_results}")
            suggestions.append("Broaden search queries or use additional search providers")

        # Score based on logarithmic scale
        import math

        score = min(1.0, math.log(count + 1) / math.log(11))  # Max at 10 results

        return score

    async def _validate_source_diversity(
        self, result: ResearchResult, issues: List[str], suggestions: List[str]
    ) -> float:
        """Validate diversity of information sources."""
        domains = set()
        source_types = set()

        for search_result in result.search_results:
            if search_result.url:
                domain = urlparse(search_result.url).netloc
                domains.add(domain)

                # Classify source type
                source_type = self._classify_source_type(search_result.url)
                source_types.add(source_type)

        domain_diversity = len(domains)
        type_diversity = len(source_types)

        if domain_diversity < self._min_source_diversity:
            issues.append(f"Low source diversity: {domain_diversity} unique domains")
            suggestions.append("Include sources from different domains and types")

        # Calculate diversity score
        max_domains = min(len(result.search_results), 8)  # Reasonable maximum
        max_types = 4  # official, community, tutorial, commercial

        # Avoid division by zero
        domain_score = min(1.0, domain_diversity / max_domains) if max_domains > 0 else 0.0
        type_score = min(1.0, type_diversity / max_types) if max_types > 0 else 0.0

        return (domain_score + type_score) / 2

    async def _validate_content_quality(
        self, result: ResearchResult, issues: List[str], suggestions: List[str]
    ) -> float:
        """Validate quality of content."""
        total_quality = 0.0

        for search_result in result.search_results:
            content = (search_result.title + " " + search_result.snippet).lower()

            # Calculate quality score for this result
            quality_score = 0.0

            # Positive indicators
            for indicator, weight in self._quality_indicators.items():
                if indicator in content:
                    quality_score += weight

            # Negative indicators (spam)
            for indicator, penalty in self._spam_indicators.items():
                if indicator in content:
                    quality_score += penalty

            # Content length bonus
            if len(search_result.snippet) > 100:
                quality_score += 0.1

            # Technical terms bonus
            technical_terms = self._count_technical_terms(content, result.technology)
            quality_score += min(0.2, technical_terms * 0.05)

            total_quality += max(0.0, min(1.0, quality_score))

        average_quality = (
            total_quality / len(result.search_results) if result.search_results else 0.0
        )

        if average_quality < 0.5:
            issues.append(f"Low content quality: {average_quality:.2f}")
            suggestions.append("Look for more technical and detailed sources")

        return average_quality

    async def _validate_source_credibility(
        self, result: ResearchResult, issues: List[str], suggestions: List[str]
    ) -> float:
        """Validate credibility of sources."""
        total_credibility = 0.0

        for search_result in result.search_results:
            credibility = await self.validate_source_credibility(search_result.url)
            total_credibility += credibility

        average_credibility = (
            total_credibility / len(result.search_results) if result.search_results else 0.0
        )

        if average_credibility < 0.6:
            issues.append(f"Low source credibility: {average_credibility:.2f}")
            suggestions.append("Include more authoritative and official sources")

        return average_credibility

    async def _validate_technical_depth(
        self, result: ResearchResult, issues: List[str], suggestions: List[str]
    ) -> float:
        """Validate technical depth of content."""
        code_examples = 0
        technical_discussions = 0
        implementation_details = 0

        for search_result in result.search_results:
            content = search_result.title + " " + search_result.snippet

            # Count code examples
            if "```" in content or "code" in content.lower():
                code_examples += 1

            # Count technical discussions
            technical_keywords = [
                "implement",
                "configure",
                "setup",
                "install",
                "deploy",
                "architecture",
            ]
            if any(keyword in content.lower() for keyword in technical_keywords):
                technical_discussions += 1

            # Count implementation details
            detail_keywords = ["parameter", "option", "setting", "variable", "function", "method"]
            if any(keyword in content.lower() for keyword in detail_keywords):
                implementation_details += 1

        total_results = len(result.search_results)
        if total_results == 0:
            return 0.0

        code_ratio = code_examples / total_results
        discussion_ratio = technical_discussions / total_results
        detail_ratio = implementation_details / total_results

        depth_score = code_ratio * 0.4 + discussion_ratio * 0.3 + detail_ratio * 0.3

        if depth_score < 0.3:
            issues.append(f"Low technical depth: {depth_score:.2f}")
            suggestions.append("Look for more detailed technical guides and code examples")

        return depth_score

    async def _validate_recency(
        self, result: ResearchResult, issues: List[str], suggestions: List[str]
    ) -> float:
        """Validate recency of information."""
        # Note: This is simplified as we don't have publication dates from search results
        # In a production system, you'd extract dates from content or metadata

        recent_indicators = ["2024", "2023", "latest", "new", "updated", "current"]
        outdated_indicators = ["2020", "2019", "2018", "deprecated", "legacy", "old"]

        recent_count = 0
        outdated_count = 0

        for search_result in result.search_results:
            content = (search_result.title + " " + search_result.snippet).lower()

            if any(indicator in content for indicator in recent_indicators):
                recent_count += 1

            if any(indicator in content for indicator in outdated_indicators):
                outdated_count += 1

        total_results = len(result.search_results)
        if total_results == 0:
            return 0.5  # Neutral score

        recent_ratio = recent_count / total_results
        outdated_ratio = outdated_count / total_results

        recency_score = max(0.0, min(1.0, recent_ratio - outdated_ratio + 0.5))

        if recency_score < 0.4:
            issues.append(f"Information may be outdated: {recency_score:.2f}")
            suggestions.append("Look for more recent sources and documentation")

        return recency_score

    async def _detect_bias(
        self, result: ResearchResult, issues: List[str], suggestions: List[str]
    ) -> float:
        """Detect potential bias in research results."""
        # Check for vendor bias
        vendor_domains = set()
        for search_result in result.search_results:
            if search_result.url:
                domain = urlparse(search_result.url).netloc
                # Check if it's a vendor/commercial domain
                if any(commercial in domain for commercial in [".com", "enterprise", "corp"]):
                    vendor_domains.add(domain)

        vendor_ratio = (
            len(vendor_domains) / len(result.search_results) if result.search_results else 0
        )

        # Check for promotional language
        promotional_terms = ["best", "top", "leading", "premier", "enterprise", "professional"]
        promotional_count = 0

        for search_result in result.search_results:
            content = (search_result.title + " " + search_result.snippet).lower()
            if any(term in content for term in promotional_terms):
                promotional_count += 1

        promotional_ratio = (
            promotional_count / len(result.search_results) if result.search_results else 0
        )

        # Calculate bias-free score (higher = less biased)
        bias_score = 1.0 - min(1.0, vendor_ratio * 0.5 + promotional_ratio * 0.3)

        if bias_score < 0.7:
            issues.append(f"Potential bias detected: {bias_score:.2f}")
            suggestions.append("Include more neutral and academic sources")

        return bias_score

    async def validate_source_credibility(self, url: str) -> float:
        """Validate credibility of a source URL."""
        if not url:
            return 0.3  # Low credibility for missing URL

        domain = urlparse(url).netloc.lower()

        # Check high-credibility domains
        for credible_domain, score in self._high_credibility_domains.items():
            if credible_domain in domain:
                return score

        # Check low-credibility domains
        if any(bad_domain in domain for bad_domain in self._low_credibility_domains):
            return 0.1

        # Basic heuristics for unknown domains
        credibility = 0.5  # Neutral starting point

        # HTTPS bonus
        if url.startswith("https://"):
            credibility += 0.1

        # Well-known TLDs
        if domain.endswith((".org", ".edu", ".gov")):
            credibility += 0.2
        elif domain.endswith(".io"):
            credibility += 0.1

        # Subdomain penalty (except for known good patterns)
        parts = domain.split(".")
        if len(parts) > 2 and not any(good in domain for good in ["docs.", "blog.", "www."]):
            credibility -= 0.1

        return max(0.1, min(1.0, credibility))

    async def extract_code_examples(self, content: str, technology: str) -> List[str]:
        """Extract relevant code examples from content."""
        code_examples = []

        # Extract markdown code blocks
        code_block_pattern = r"```(\w+)?\n(.*?)\n```"
        matches = re.finditer(code_block_pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2).strip()

            # Validate code quality
            if await self._is_valid_code_example(code, language, technology):
                code_examples.append(code)

        # Extract inline code
        inline_pattern = r"`([^`\n]+)`"
        inline_matches = re.findall(inline_pattern, content)

        for code in inline_matches:
            if len(code) > 20 and await self._is_valid_code_example(code, "text", technology):
                code_examples.append(code)

        return code_examples[:5]  # Return top 5 examples

    async def _is_valid_code_example(self, code: str, language: str, technology: str) -> bool:
        """Validate if code example is relevant and well-formed."""
        # Minimum length check
        if len(code.strip()) < 10:
            return False

        # Technology relevance check
        if technology.lower() not in code.lower():
            # Check for related terms
            related_terms = self._get_related_terms(technology)
            if not any(term in code.lower() for term in related_terms):
                return False

        # Language-specific validation
        if language in self._code_patterns:
            patterns = self._code_patterns[language]
            if not any(re.search(pattern, code, re.MULTILINE) for pattern in patterns):
                return False

        # Quality indicators
        quality_indicators = ["def ", "function", "class", "import", "const", "var"]
        if not any(indicator in code.lower() for indicator in quality_indicators):
            return False

        return True

    def _get_related_terms(self, technology: str) -> List[str]:
        """Get related terms for technology."""
        related_map = {
            "python": ["pip", "virtualenv", "django", "flask", "fastapi"],
            "javascript": ["npm", "node", "react", "vue", "angular"],
            "docker": ["container", "dockerfile", "image", "compose"],
            "kubernetes": ["k8s", "pod", "deployment", "service", "kubectl"],
            "postgresql": ["postgres", "pg", "sql", "database"],
            "ansible": ["playbook", "yaml", "task", "role"],
        }

        return related_map.get(technology.lower(), [])

    def _count_technical_terms(self, content: str, technology: str) -> int:
        """Count technical terms related to the technology."""
        related_terms = self._get_related_terms(technology)
        count = 0

        for term in related_terms:
            count += content.count(term)

        # Add general technical terms
        general_terms = ["api", "config", "deploy", "server", "client", "database", "service"]
        for term in general_terms:
            count += content.count(term)

        return count

    def _classify_source_type(self, url: str) -> str:
        """Classify source type based on URL patterns."""
        domain = urlparse(url).netloc.lower()

        if any(official in domain for official in ["docs.", ".org", "official"]):
            return "official"
        elif any(community in domain for community in ["stackoverflow", "reddit", "forum"]):
            return "community"
        elif any(tutorial in domain for tutorial in ["tutorial", "guide", "learn"]):
            return "tutorial"
        elif any(commercial in domain for commercial in [".com", "enterprise"]):
            return "commercial"
        else:
            return "unknown"

    async def get_validation_summary(self, result: ResearchResult) -> Dict[str, Any]:
        """Get comprehensive validation summary."""
        validation = await self._comprehensive_validation(result)

        return {
            "overall_quality": validation.quality.value,
            "confidence": validation.confidence,
            "is_valid": validation.is_valid,
            "metrics": validation.metrics,
            "issues_count": len(validation.issues),
            "suggestions_count": len(validation.suggestions),
            "issues": validation.issues,
            "suggestions": validation.suggestions,
            "validation_timestamp": datetime.now().isoformat(),
        }
