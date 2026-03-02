#!/usr/bin/env python3
"""Monitor story engine health

Usage:
    python health-check.py [--verbose]
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.story import Story
from app.config import Config


def check_data_access():
    """Check if story data can be accessed"""
    try:
        # Try to create a test story
        test_story = Story(
            id="health_check_test",
            title="Health Check",
            description="System health check",
            genre="Test",
            user_id="system",
            start_segment_id="seg_001"
        )
        return True, "Story data accessible"
    except Exception as e:
        return False, f"Data access failed: {str(e)[:100]}"


def check_configuration():
    """Check if configuration is valid"""
    try:
        config = Config()
        # Check if any AI models are configured
        if not hasattr(config, 'OPENROUTER_API_KEY'):
            return True, "Config loaded (OpenRouter not configured)"
        
        if config.OPENROUTER_API_KEY:
            return True, "Config loaded with OpenRouter key"
        
        return True, "Config loaded"
    except Exception as e:
        return False, f"Config error: {str(e)[:100]}"


def check_models_import():
    """Check if core models can be imported"""
    try:
        from app.models.story_segment import StorySegment
        from app.models.story_character import StoryCharacter
        from app.models.story_location import StoryLocation
        from app.models.story_choice import StoryChoice
        from app.models.text_types import TextBlock, TextType
        from app.engine.generator import TextGenerator
        
        return True, "All models import successfully"
    except Exception as e:
        return False, f"Import error: {str(e)[:100]}"


def check_directory_permissions():
    """Check if data directory is accessible"""
    try:
        data_dir = Path(".infinite_story_data")
        
        # Try to create directory if it doesn't exist
        data_dir.mkdir(exist_ok=True)
        
        # Try to write a test file
        test_file = data_dir / ".health_check_test"
        test_file.touch()
        test_file.unlink()
        
        return True, "Data directory accessible and writable"
    except Exception as e:
        return False, f"Directory error: {str(e)[:100]}"


def main(verbose=False):
    """Run all health checks"""
    checks = {
        'imports': check_models_import,
        'configuration': check_configuration,
        'data_directory': check_directory_permissions,
        'data_access': check_data_access,
    }
    
    results = {}
    all_ok = True
    
    print("=" * 50)
    print("ISE v2 Health Check")
    print("=" * 50)
    print()
    
    for name, check_func in checks.items():
        try:
            passed, message = check_func()
            results[name] = {
                'status': 'ok' if passed else 'error',
                'message': message
            }
            
            status_icon = "✓" if passed else "✗"
            print(f"{status_icon} {name:20} {message}")
            
            if not passed:
                all_ok = False
                
        except Exception as e:
            results[name] = {
                'status': 'error',
                'message': str(e)[:100]
            }
            print(f"✗ {name:20} Exception: {str(e)[:50]}")
            all_ok = False
    
    print()
    print("=" * 50)
    
    if all_ok:
        print("✅ All health checks passed!")
        print("=" * 50)
        return 0
    else:
        print("❌ Some health checks failed")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    exit_code = main(verbose=verbose)
    sys.exit(exit_code)
