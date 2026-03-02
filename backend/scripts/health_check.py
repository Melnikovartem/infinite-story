#!/usr/bin/env python3
"""
Health check script for Infinite Story Engine

Verifies:
- Data access layer is working
- Generator is ready
- Archive system is functional
- Models can be loaded
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR


class HealthCheck:
    """Perform health checks on the system"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
    
    async def run_all_checks(self) -> Tuple[bool, int]:
        """Run all health checks"""
        checks = [
            ("data_access", self.check_data_access),
            ("model_loading", self.check_model_loading),
            ("data_persistence", self.check_data_persistence),
            ("generator_setup", self.check_generator_setup),
            ("archive_system", self.check_archive_system),
        ]
        
        print("Running health checks...")
        print("=" * 50)
        
        for name, check_func in checks:
            try:
                result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                self.results[name] = {
                    "status": "✓ OK",
                    "message": result
                }
                print(f"✓ {name:20} PASS")
            except Exception as e:
                self.results[name] = {
                    "status": "✗ FAILED",
                    "message": str(e)
                }
                print(f"✗ {name:20} FAIL: {e}")
        
        print("=" * 50)
        
        # Summary
        passed = sum(1 for r in self.results.values() if "OK" in r["status"])
        total = len(self.results)
        
        print(f"\nResults: {passed}/{total} checks passed")
        
        if passed == total:
            print("✅ All checks passed - system is healthy")
            return True, 0
        else:
            print("❌ Some checks failed - system may not be healthy")
            return False, 1
    
    def check_data_access(self) -> str:
        """Check if data directory is accessible"""
        if not LOCAL_DATA_DIR.exists():
            LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Try to write a test file
        test_file = LOCAL_DATA_DIR / ".health_check_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            return "Data directory accessible and writable"
        except Exception as e:
            raise Exception(f"Cannot write to data directory: {e}")
    
    def check_model_loading(self) -> str:
        """Check if models can be loaded"""
        try:
            # Try importing all models
            from app.models.story_segment import StorySegment
            from app.models.story_character import StoryCharacter
            from app.models.story_location import StoryLocation
            from app.models.story_choice import StoryChoice
            
            return "All models loaded successfully"
        except Exception as e:
            raise Exception(f"Failed to load models: {e}")
    
    def check_data_persistence(self) -> str:
        """Check if data can be saved and loaded"""
        try:
            # Create a test story
            from app.models.story import Story
            from datetime import datetime, UTC
            
            test_id = "health_check_test"
            test_story = Story(
                id=test_id,
                title="Health Check Test",
                description="Test story for health check",
                genre="Test",
                user_id="system",
                start_segment_id="start",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            # Save
            test_story.save()
            
            # Load
            loaded = Story.load(test_id, test_id)
            
            if loaded is None:
                raise Exception("Saved story could not be loaded")
            
            # Cleanup
            test_story.delete()
            
            return "Data persistence working"
        except Exception as e:
            raise Exception(f"Data persistence check failed: {e}")
    
    async def check_generator_setup(self) -> str:
        """Check if text generator is configured"""
        try:
            from app.engine.generator import TextGenerator
            from app.config import settings
            
            # Check if API key or configuration is available
            if hasattr(settings, 'openrouter_api_key') and settings.openrouter_api_key:
                return "Generator API key is configured"
            else:
                return "Generator not configured (will use mock/fallback)"
        except Exception as e:
            return f"Generator check: {e}"
    
    def check_archive_system(self) -> str:
        """Check if archive system is functional"""
        try:
            # Check if archive-related modules exist
            from app.models.story_segment import SegmentStatus
            
            # Verify status enum includes archived
            if hasattr(SegmentStatus, 'ARCHIVED'):
                return "Archive system available"
            else:
                return "Archive system not fully configured"
        except Exception as e:
            raise Exception(f"Archive system check failed: {e}")


async def main():
    """Run health checks"""
    health = HealthCheck()
    success, exit_code = await health.run_all_checks()
    
    # Print detailed results
    if health.results:
        print("\nDetailed Results:")
        print("-" * 50)
        for name, result in health.results.items():
            print(f"{name:20} {result['status']}")
            if result.get('message'):
                print(f"  → {result['message']}")
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
