#!/usr/bin/env python3
"""
Test script for MySQL/MariaDB template engine.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.web_research.template_engines.mysql_engine import MySQLTemplateEngine
from src.web_research.template_engines.base_engine import TemplateContext
from src.prompt_config import SpecificOptions

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_mysql_galera_cluster():
    """Test MySQL/MariaDB Galera cluster generation."""
    print("🔍 Testing MySQL/MariaDB Galera Cluster Template Engine")
    print("=" * 60)
    
    engine = MySQLTemplateEngine()
    
    # Test Galera cluster context
    context = TemplateContext(
        technology=["mariadb", "galera", "proxysql"],
        task_description="Deploy 3-node MariaDB Galera cluster with ProxySQL load balancer for high availability",
        specific_options=SpecificOptions(cluster_size=3),
        research_data={}
    )
    
    # Check if engine can handle this context
    can_handle = engine.can_handle(context)
    print(f"Can handle context: {can_handle}")
    
    if can_handle:
        # Generate template
        result = await engine.generate_template(context)
        
        print(f"Template generated successfully!")
        print(f"Confidence score: {result.confidence_score}")
        print(f"Metadata: {result.metadata}")
        print("\n" + "=" * 60)
        print("Generated Template:")
        print("=" * 60)
        print(result.content[:2000] + "..." if len(result.content) > 2000 else result.content)
    else:
        print("❌ Engine cannot handle this context")

async def test_mysql_basic():
    """Test basic MySQL setup."""
    print("\n🔍 Testing Basic MySQL Setup")
    print("=" * 60)
    
    engine = MySQLTemplateEngine()
    
    context = TemplateContext(
        technology=["mysql"],
        task_description="Set up MySQL database for web application",
        specific_options=SpecificOptions(),
        research_data={}
    )
    
    can_handle = engine.can_handle(context)
    print(f"Can handle context: {can_handle}")
    
    if can_handle:
        result = await engine.generate_template(context)
        print(f"Template generated successfully!")
        print(f"Confidence score: {result.confidence_score}")
        print(f"Template length: {len(result.content)} characters")

async def main():
    """Run all tests."""
    try:
        await test_mysql_galera_cluster()
        await test_mysql_basic()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())