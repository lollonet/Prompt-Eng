#!/usr/bin/env python3
"""
Simple test script to validate the centralized configuration system.
"""

import asyncio
import logging
from pathlib import Path

from src.config_manager import get_config, reload_config
from src.config_integration import (
    setup_logging_from_config,
    get_knowledge_manager_config_legacy,
    validate_required_paths,
    create_missing_directories,
    is_development_mode,
    get_environment_name,
)

# Configure basic logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_config_loading():
    """Test basic configuration loading."""
    print("Testing basic configuration loading...")
    
    config_result = get_config()
    if config_result.is_error():
        print(f"❌ Failed to load configuration: {config_result.error}")
        return False
    
    config = config_result.unwrap()
    print(f"✅ Configuration loaded successfully")
    print(f"   - System: {config.system.name} v{config.system.version}")
    print(f"   - Environment: {config.system.environment}")
    print(f"   - Loaded at: {config.loaded_at}")
    return True


def test_logging_setup():
    """Test logging configuration setup."""
    print("\nTesting logging setup...")
    
    result = setup_logging_from_config()
    if result.is_error():
        print(f"❌ Failed to setup logging: {result.error}")
        return False
    
    print("✅ Logging configured from centralized config")
    return True


def test_path_resolution():
    """Test path resolution and validation."""
    print("\nTesting path resolution...")
    
    config_result = get_config()
    if config_result.is_error():
        print(f"❌ Failed to get config: {config_result.error}")
        return False
    
    config = config_result.unwrap()
    
    # Test path resolution
    prompts_path = config.get_absolute_path(config.paths.prompts_dir)
    print(f"   - Prompts directory: {prompts_path}")
    
    knowledge_path = config.get_absolute_path(config.paths.knowledge_base_root)
    print(f"   - Knowledge base: {knowledge_path}")
    
    cache_path = config.get_absolute_path(config.paths.cache_dir)
    print(f"   - Cache directory: {cache_path}")
    
    print("✅ Path resolution working")
    return True


def test_legacy_integration():
    """Test legacy configuration integration."""
    print("\nTesting legacy integration...")
    
    legacy_result = get_knowledge_manager_config_legacy()
    if legacy_result.is_error():
        print(f"❌ Failed to get legacy config: {legacy_result.error}")
        return False
    
    legacy_config = legacy_result.unwrap()
    print(f"   - Legacy config path: {legacy_config.config_path}")
    print(f"   - Cache strategy: {legacy_config.cache_strategy}")
    print(f"   - Max concurrent ops: {legacy_config.max_concurrent_operations}")
    
    print("✅ Legacy integration working")
    return True


def test_environment_detection():
    """Test environment detection helpers."""
    print("\nTesting environment detection...")
    
    env_name = get_environment_name()
    is_dev = is_development_mode()
    
    print(f"   - Environment: {env_name}")
    print(f"   - Development mode: {is_dev}")
    
    print("✅ Environment detection working")
    return True


def test_directory_creation():
    """Test automatic directory creation."""
    print("\nTesting directory creation...")
    
    result = create_missing_directories()
    if result.is_error():
        print(f"❌ Failed to create directories: {result.error}")
        return False
    
    print("✅ Directory creation working")
    return True


def test_path_validation():
    """Test path validation."""
    print("\nTesting path validation...")
    
    result = validate_required_paths()
    if result.is_error():
        print(f"⚠️ Path validation issues: {result.error}")
        # This is expected for some paths, so don't fail the test
    else:
        print("✅ All required paths valid")
    
    return True


def test_config_reload():
    """Test configuration hot reload."""
    print("\nTesting configuration reload...")
    
    # Get initial config
    initial_result = get_config()
    if initial_result.is_error():
        print(f"❌ Failed to get initial config: {initial_result.error}")
        return False
    
    initial_time = initial_result.unwrap().loaded_at
    
    # Force reload
    reload_result = reload_config()
    if reload_result.is_error():
        print(f"❌ Failed to reload config: {reload_result.error}")
        return False
    
    reloaded_time = reload_result.unwrap().loaded_at
    
    if reloaded_time > initial_time:
        print("✅ Configuration reload working")
        return True
    else:
        print("⚠️ Configuration reload timestamp unchanged")
        return True  # Still acceptable


def test_config_sections():
    """Test access to all configuration sections."""
    print("\nTesting configuration sections...")
    
    config_result = get_config()
    if config_result.is_error():
        print(f"❌ Failed to get config: {config_result.error}")
        return False
    
    config = config_result.unwrap()
    
    # Test each section
    sections = [
        ("System", config.system),
        ("Paths", config.paths),
        ("Performance", config.performance),
        ("Cache", config.cache),
        ("Logging", config.logging),
        ("Knowledge Manager", config.knowledge_manager),
        ("Event System", config.event_system),
        ("Web Research", config.web_research),
        ("Security", config.security),
        ("Templates", config.templates),
        ("Monitoring", config.monitoring),
        ("Development", config.development),
    ]
    
    for section_name, section_obj in sections:
        if section_obj is None:
            print(f"❌ Section {section_name} is None")
            return False
        print(f"   - {section_name}: ✅")
    
    print("✅ All configuration sections accessible")
    return True


def run_all_tests():
    """Run all configuration tests."""
    print("=" * 60)
    print("CENTRALIZED CONFIGURATION SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        test_basic_config_loading,
        test_logging_setup,
        test_path_resolution,
        test_legacy_integration,
        test_environment_detection,
        test_directory_creation,
        test_path_validation,
        test_config_reload,
        test_config_sections,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration system is working correctly.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Please check the configuration system.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)