"""
Web Research Module for Dynamic Technology Discovery

This module provides automatic web research capabilities for unknown technologies,
generating dynamic templates based on real-time web research.
"""

from .technology_detector import TechnologyDetector
from .web_researcher import WebResearcher
from .template_generator import DynamicTemplateGenerator
from .research_cache import TemplateCache, ResearchCache
from .research_validator import ResearchValidator

__all__ = [
    'TechnologyDetector',
    'WebResearcher', 
    'DynamicTemplateGenerator',
    'TemplateCache',
    'ResearchCache',
    'ResearchValidator'
]