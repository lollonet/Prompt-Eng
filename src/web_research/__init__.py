"""
Web Research Module for Dynamic Technology Discovery

This module provides automatic web research capabilities for unknown technologies,
generating dynamic templates based on real-time web research.
"""

from .research_cache import ResearchCache, TemplateCache
from .research_validator import ResearchValidator
from .technology_detector import TechnologyDetector
from .template_generator import DynamicTemplateGenerator
from .web_researcher import WebResearcher

__all__ = [
    "TechnologyDetector",
    "WebResearcher",
    "DynamicTemplateGenerator",
    "TemplateCache",
    "ResearchCache",
    "ResearchValidator",
]
