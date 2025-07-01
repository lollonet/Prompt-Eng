"""
Enterprise Dynamic Template Generator following SOLID principles.

Business Context: Orchestrates template generation by delegating to
specialized engines and extracting research content for quality validation.
"""

import asyncio
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import hashlib
from pathlib import Path

from .interfaces import IDynamicTemplateGenerator, ResearchResult, SearchResult
from .config import WebResearchConfig, TemplateConfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..prompt_config import SpecificOptions


@dataclass
class TemplateSection:
    """Represents a section of a generated template."""
    name: str
    content: str
    priority: int
    confidence: float


@dataclass
class CodeExample:
    """Represents a code example extracted from research."""
    language: str
    code: str
    description: str
    source_url: str
    relevance_score: float


@dataclass
class BestPractice:
    """Represents a best practice extracted from research."""
    title: str
    description: str
    category: str
    source_url: str
    confidence: float


class DynamicTemplateGenerator(IDynamicTemplateGenerator):
    """
    Enterprise template generator following Single Responsibility Principle.
    
    Business Context: Orchestrates template generation by delegating to
    specialized engines, focusing only on research data extraction and
    quality validation.
    
    Why this approach: Composition over inheritance - uses specialized
    engines rather than implementing all template logic internally.
    """
    
    def __init__(self, config: WebResearchConfig):
        self.config = config
        self.template_config = config.template
        self._logger = logging.getLogger(__name__)
        
        # Template engine factory (dependency injection)
        from .template_engines.template_factory import get_template_factory
        self._template_factory = get_template_factory()
        
        # Content extractors (focused responsibility)
        self._code_extractors = self._initialize_code_extractors()
        self._practice_extractors = self._initialize_practice_extractors()
        
        # Quality thresholds (configuration)
        self._min_code_length = 20
        self._min_practice_length = 50
        self._relevance_threshold = 0.6
    
    def _initialize_code_extractors(self) -> Dict[str, Any]:
        """Initialize code extraction patterns (≤20 lines)."""
        return {
            "code_block_patterns": [
                r'```(\w+)?\n(.*?)\n```',  # Markdown code blocks
                r'<code[^>]*>(.*?)</code>',  # HTML code tags
                r'`([^`\n]+)`',  # Inline code
                r'^\s{4,}(.+)$',  # Indented code (multiline)
            ],
            "language_indicators": {
                'python': ['def ', 'import ', 'from ', 'class ', 'pip install'],
                'javascript': ['function', 'const ', 'let ', 'var ', 'npm install'],
                'yaml': ['---', 'apiVersion:', 'kind:', 'metadata:'],
                'dockerfile': ['FROM ', 'RUN ', 'COPY ', 'EXPOSE '],
                'bash': ['#!/bin/bash', '$ ', 'sudo ', 'apt-get'],
                'ansible': ['- name:', 'tasks:', 'playbook:', 'hosts:']
            }
        }
    
    def _initialize_practice_extractors(self) -> Dict[str, Any]:
        """Initialize best practice extraction patterns (≤20 lines)."""
        return {
            "practice_indicators": [
                r'best practice[s]?[:\-]?\s*(.+)',
                r'recommendation[s]?[:\-]?\s*(.+)',
                r'should\s+(always|never|use|avoid)\s+(.+)',
                r'important[:\-]?\s*(.+)',
            ],
            "categories": {
                'security': ['auth', 'encrypt', 'validate', 'sanitiz'],
                'performance': ['cache', 'optimize', 'fast', 'efficient'],
                'maintainability': ['clean', 'readable', 'document', 'test'],
                'reliability': ['error', 'exception', 'robust', 'fault']
            }
        }
    
    async def generate_template(
        self, 
        research: ResearchResult, 
        specific_options: Optional['SpecificOptions'] = None
    ) -> str:
        """
        Generate dynamic template using specialized engines.
        
        Business Context: Main entry point that orchestrates research analysis
        and delegates to appropriate template engines for generation.
        """
        self._logger.info(f"Generating template for technology: {research.technology}")
        
        # Try engine-based generation first (preferred path)
        if specific_options:
            engine_result = await self._try_engine_generation(research, specific_options)
            if engine_result and engine_result.is_high_quality():
                return engine_result.content
        
        # Fallback to legacy generation for unknown technologies
        return await self._generate_legacy_template(research, specific_options)
    
    async def _try_engine_generation(
        self, 
        research: ResearchResult, 
        specific_options: 'SpecificOptions'
    ) -> Optional['TemplateResult']:
        """
        Attempt template generation using specialized engines.
        
        Why this approach: Delegation to specialized engines following
        Single Responsibility Principle.
        """
        from .template_engines.base_engine import TemplateContext
        
        context = TemplateContext(
            technology=research.technology,
            task_description=research.technology + " implementation",
            specific_options=specific_options,
            research_data=research.__dict__
        )
        
        try:
            return await self._template_factory.generate_template(context)
        except Exception as e:
            self._logger.warning(f"Engine generation failed: {e}")
            return None
    
    async def _generate_legacy_template(
        self, 
        research: ResearchResult, 
        specific_options: Optional['SpecificOptions']
    ) -> str:
        """
        Legacy template generation for unsupported technologies.
        
        Business Context: Maintains backward compatibility while
        new engines are being developed.
        """
        # Extract content using existing methods
        code_examples = await self._extract_code_examples(research)
        best_practices = await self._extract_best_practices(research)
        
        # Simple template assembly
        return self._assemble_simple_template(research, code_examples, best_practices)
    
    def _assemble_simple_template(
        self,
        research: ResearchResult,
        code_examples: List[CodeExample],
        best_practices: List[BestPractice]
    ) -> str:
        """
        Assemble simple template from extracted content.
        
        Why this approach: Focused function with single responsibility
        and clear parameter list (≤3 parameters).
        """
        sections = [
            f"# {research.technology.title()} Implementation",
            "",
            "## TASK", 
            f"Implement: **{research.technology} functionality**",
            "",
            self._generate_simple_examples_section(code_examples),
            "",
            self._generate_simple_practices_section(best_practices),
            "",
            "## IMPLEMENTATION STEPS",
            "1. Setup environment following official documentation",
            "2. Implement core functionality with error handling", 
            "3. Add comprehensive testing and monitoring",
            "",
            "Please implement following best practices."
        ]
        
        return "\n".join(sections)
    
    def _generate_simple_examples_section(self, examples: List[CodeExample]) -> str:
        """Generate simple examples section (≤20 lines)."""
        if not examples:
            return "## EXPECTED OUTPUT\n```\n# Implementation examples will be provided\n```"
        
        best_example = examples[0]
        return f"""## EXPECTED OUTPUT
```{best_example.language}
{best_example.code[:500]}...
```"""
    
    def _generate_simple_practices_section(self, practices: List[BestPractice]) -> str:
        """Generate simple best practices section (≤20 lines)."""
        if not practices:
            return "## BEST PRACTICES\n- Follow official documentation\n- Write comprehensive tests"
        
        practice_items = []
        for practice in practices[:3]:  # Limit to top 3
            practice_items.append(f"- {practice.title}")
        
        return "## BEST PRACTICES\n" + "\n".join(practice_items)
    
    async def _extract_code_examples(self, research: ResearchResult) -> List[CodeExample]:
        """Extract relevant code examples from research results (≤20 lines)."""
        code_examples = []
        
        for search_result in research.search_results:
            content = search_result.snippet
            
            # Extract code blocks using patterns
            for pattern in self._code_extractors["code_block_patterns"]:
                matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
                
                for match in matches:
                    code = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    
                    if len(code.strip()) >= self._min_code_length:
                        code_examples.append(CodeExample(
                            language=self._detect_code_language(code),
                            code=code.strip(),
                            description=f"Example from {search_result.title[:50]}...",
                            source_url=search_result.url,
                            relevance_score=0.7
                        ))
        
        return code_examples[:5]  # Top 5 most relevant examples
    
    async def _extract_best_practices(self, research: ResearchResult) -> List[BestPractice]:
        """Extract best practices from research results (≤20 lines)."""
        best_practices = []
        
        for search_result in research.search_results:
            content = search_result.snippet + " " + search_result.title
            
            # Extract practices using patterns
            for pattern in self._practice_extractors["practice_indicators"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    practice_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    
                    if len(practice_text.strip()) >= self._min_practice_length:
                        best_practices.append(BestPractice(
                            title=practice_text[:60] + "..." if len(practice_text) > 60 else practice_text,
                            description=practice_text.strip(),
                            category=self._categorize_practice(practice_text),
                            source_url=search_result.url,
                            confidence=0.7
                        ))
        
        return best_practices[:8]  # Top 8 practices
    
    async def enhance_existing_template(self, template: str, research: ResearchResult) -> str:
        """Enhance existing template with new research (≤20 lines)."""
        self._logger.info(f"Enhancing template for {research.technology}")
        
        # Extract new content
        new_code_examples = await self._extract_code_examples(research)
        new_best_practices = await self._extract_best_practices(research)
        
        # Add missing code examples
        enhanced_template = template
        if new_code_examples and "```" not in template:
            best_example = new_code_examples[0]
            enhancement = f"\n## UPDATED EXAMPLE\n```{best_example.language}\n{best_example.code}\n```\n"
            enhanced_template += enhancement
        
        return enhanced_template
    
    async def validate_template_quality(self, template: str) -> float:
        """Validate generated template quality (≤20 lines)."""
        quality_score = 0.0
        
        # Length check
        if 500 <= len(template) <= 3000:
            quality_score += 0.3
        
        # Structure check
        required_sections = ["TASK", "EXPECTED OUTPUT", "IMPLEMENTATION"]
        section_count = sum(1 for section in required_sections if section in template)
        quality_score += (section_count / len(required_sections)) * 0.4
        
        # Code examples check
        if "```" in template:
            quality_score += 0.3
        
        return min(quality_score, 1.0)
    
    # Helper methods (≤10 lines each)
    def _detect_code_language(self, code: str) -> str:
        """Detect programming language of code snippet."""
        for language, indicators in self._code_extractors["language_indicators"].items():
            if any(indicator in code for indicator in indicators):
                return language
        return "text"
    
    def _categorize_practice(self, practice_text: str) -> str:
        """Categorize best practice by content."""
        text_lower = practice_text.lower()
        
        for category, keywords in self._practice_extractors["categories"].items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"