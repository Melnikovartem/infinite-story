#!/usr/bin/env python3
"""Async story generator runner with output logging."""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.cli import create_story_ai_async

# Setup logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('story_generation.log')
    ]
)

logger = logging.getLogger(__name__)


async def run_story_generator():
    """Run the story generator asynchronously."""
    logger.info("=" * 80)
    logger.info("STARTING STORY GENERATION")
    logger.info("=" * 80)
    
    try:
        story_id = await create_story_ai_async(
            story_id="the_last_city",
            title="The Last City",
            description="A world where mega-corporations rule from floating towers above a sprawling dystopian city",
            genre="Sci-Fi",
            world_input=""
        )
        
        logger.info("=" * 80)
        logger.info(f"STORY GENERATION COMPLETE!")
        logger.info(f"Story ID: {story_id}")
        logger.info("=" * 80)
        
        # List generated files
        data_dir = Path(".infinite_story_data") / story_id
        if data_dir.exists():
            logger.info(f"\nGenerated files in {data_dir}:")
            for f in sorted(data_dir.rglob("*")):
                if f.is_file():
                    size = f.stat().st_size
                    logger.info(f"  {f.relative_to(data_dir)} ({size} bytes)")
        
        return True
        
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        return False


async def main():
    """Main entry point."""
    logger.info("Starting async story generation...")
    
    # Run the generator
    success = await run_story_generator()
    
    # Keep running to allow exploration
    if success:
        logger.info("\nGeneration complete! Keeping process alive for exploration...")
        logger.info("Check .infinite_story_data/the_last_city/ for generated files")
        
        # Keep alive for 60 seconds so you can explore
        await asyncio.sleep(60)
        logger.info("Shutting down...")
    else:
        logger.error("Generation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
