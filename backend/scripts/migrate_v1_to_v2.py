#!/usr/bin/env python3
"""
Migrate v1 stories to v2 format.

This script converts existing v1 segments to v2 format by adding:
- Episode context (episode_number, episode_tone, etc.)
- Character state tracking (character_states, change_notes)
- Status field for immutability tracking
- Episode recap data
- Story arc data

Usage:
    python migrate_v1_to_v2.py the_veil
    python migrate_v1_to_v2.py --all
    python migrate_v1_to_v2.py --rollback the_veil
"""

import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory paths
DATA_DIR = Path(".infinite_story_data")
BACKUP_DIR = Path(".infinite_story_data_v1_backup")


class MigrationManager:
    """Manages migration of stories from v1 to v2 format."""
    
    def __init__(self):
        """Initialize migration manager."""
        self.data_dir = DATA_DIR
        self.backup_dir = BACKUP_DIR
        self.migrations = []
    
    def get_story_dirs(self) -> List[str]:
        """Get all story directories."""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return []
        
        return [d.name for d in self.data_dir.iterdir() if d.is_dir()]
    
    def backup_story(self, story_id: str) -> bool:
        """Create a backup of story before migration.
        
        Args:
            story_id: ID of story to backup
            
        Returns:
            True if backup successful, False otherwise
        """
        story_dir = self.data_dir / story_id
        backup_story_dir = self.backup_dir / story_id
        
        if not story_dir.exists():
            logger.warning(f"Story directory not found: {story_dir}")
            return False
        
        try:
            # Remove existing backup if present
            if backup_story_dir.exists():
                shutil.rmtree(backup_story_dir)
            
            # Create backup
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(story_dir, backup_story_dir)
            logger.info(f"✅ Backup created: {backup_story_dir}")
            return True
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def restore_story(self, story_id: str) -> bool:
        """Restore story from backup.
        
        Args:
            story_id: ID of story to restore
            
        Returns:
            True if restore successful, False otherwise
        """
        story_dir = self.data_dir / story_id
        backup_story_dir = self.backup_dir / story_id
        
        if not backup_story_dir.exists():
            logger.error(f"Backup not found: {backup_story_dir}")
            return False
        
        try:
            # Remove current story if present
            if story_dir.exists():
                shutil.rmtree(story_dir)
            
            # Restore from backup
            shutil.copytree(backup_story_dir, story_dir)
            logger.info(f"✅ Restored from backup: {story_dir}")
            return True
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def load_v1_segments(self, story_id: str) -> Dict[str, Dict[str, Any]]:
        """Load all v1 segments for a story.
        
        Args:
            story_id: ID of story
            
        Returns:
            Dictionary mapping segment IDs to segment data
        """
        segment_dir = self.data_dir / story_id / "storysegment"
        segments = {}
        
        if not segment_dir.exists():
            logger.warning(f"No segment directory found for {story_id}")
            return segments
        
        for seg_file in segment_dir.glob("*.json"):
            try:
                with open(seg_file, 'r') as f:
                    segment_data = json.load(f)
                    segment_id = seg_file.stem
                    segments[segment_id] = segment_data
            except Exception as e:
                logger.error(f"Failed to load segment {seg_file}: {e}")
        
        logger.info(f"Loaded {len(segments)} segments from {story_id}")
        return segments
    
    def load_v1_choices(self, story_id: str) -> Dict[str, Dict[str, Any]]:
        """Load all v1 choices for a story.
        
        Args:
            story_id: ID of story
            
        Returns:
            Dictionary mapping choice IDs to choice data
        """
        choice_dir = self.data_dir / story_id / "storychoice"
        choices = {}
        
        if not choice_dir.exists():
            logger.warning(f"No choice directory found for {story_id}")
            return choices
        
        for choice_file in choice_dir.glob("*.json"):
            try:
                with open(choice_file, 'r') as f:
                    choice_data = json.load(f)
                    choice_id = choice_file.stem
                    choices[choice_id] = choice_data
            except Exception as e:
                logger.error(f"Failed to load choice {choice_file}: {e}")
        
        logger.info(f"Loaded {len(choices)} choices from {story_id}")
        return choices
    
    def add_v2_fields_to_segment(self, segment: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Add v2 fields to a v1 segment.
        
        Args:
            segment: Segment data
            index: Position in segment list
            
        Returns:
            Segment with v2 fields added
        """
        # Add episode/arc context fields
        if "episode_number" not in segment:
            segment["episode_number"] = 1
        
        if "arc_id" not in segment:
            segment["arc_id"] = None
        
        if "episode_tone" not in segment:
            segment["episode_tone"] = segment.get("atmosphere", "neutral")
        
        if "episode_end_condition" not in segment:
            segment["episode_end_condition"] = None
        
        if "segment_number_in_episode" not in segment:
            segment["segment_number_in_episode"] = index + 1
        
        if "pacing_weight" not in segment:
            # Default pacing: later segments have higher weight
            segment["pacing_weight"] = 0.0
        
        # Add character/location state fields
        if "protagonist_id" not in segment:
            segment["protagonist_id"] = None
        
        if "character_states" not in segment:
            segment["character_states"] = {}
        
        if "change_notes" not in segment:
            segment["change_notes"] = []
        
        if "locations_running_status" not in segment and "locations" in segment:
            # Convert old format to new
            segment["locations_running_status"] = segment.get("locations_running_status", [])
        
        # Add episode completion signals
        if "end_condition_proximity" not in segment:
            segment["end_condition_proximity"] = 0.0
        
        if "protagonist_alive" not in segment:
            segment["protagonist_alive"] = True
        
        if "triggers_episode_transition" not in segment:
            segment["triggers_episode_transition"] = False
        
        # Add status field
        if "status" not in segment:
            # Mark as generated if it already has is_generated or content
            is_generated = segment.get("is_generated", True) or "content" in segment
            segment["status"] = "generated" if is_generated else "unexplored"
        
        # Add parent tracking if not present
        if "parent_segment_id" not in segment:
            segment["parent_segment_id"] = None
        
        if "parent_choice_id" not in segment:
            segment["parent_choice_id"] = None
        
        return segment
    
    def create_default_episode_recap(self, story_id: str, segments: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a default EpisodeRecap for episode 1.
        
        Args:
            story_id: ID of story
            segments: Dictionary of segments
            
        Returns:
            EpisodeRecap data
        """
        now = datetime.now(UTC).isoformat()
        
        # Infer title and tone from segments
        title = "The Beginning"
        if segments:
            first_segment = list(segments.values())[0]
            if "atmosphere" in first_segment:
                title = f"Episode 1: {first_segment.get('atmosphere', 'The Beginning')}"
        
        tone = "neutral"
        if segments:
            first_segment = list(segments.values())[0]
            tone = first_segment.get("atmosphere", "neutral").lower().replace(" ", "_")
        
        recap = {
            "id": f"episode_recap_001",
            "story_id": story_id,
            "episode_number": 1,
            "arc_id": "arc_001",
            "title": title,
            "summary": "The first episode of the story begins.",
            "starting_character_states": {},
            "ending_character_states": {},
            "segment_ids": list(segments.keys()),
            "choice_ids": [],
            "key_themes": ["adventure", "mystery"],
            "tone": tone,
            "generated_at": now,
            "generator_model": "v1-migration",
            "created_at": now,
            "updated_at": now
        }
        
        return recap
    
    def create_default_story_arc(self, story_id: str, segments: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a default StoryArc.
        
        Args:
            story_id: ID of story
            segments: Dictionary of segments
            
        Returns:
            StoryArc data
        """
        now = datetime.now(UTC).isoformat()
        first_segment_id = list(segments.keys())[0] if segments else "segment_001"
        
        arc = {
            "id": "arc_001",
            "story_id": story_id,
            "title": "The Opening Arc",
            "description": "The beginning of the narrative.",
            "episode_ids": ["episode_recap_001"],
            "episode_count": 1,
            "start_segment_id": first_segment_id,
            "current_segment_id": first_segment_id,
            "premise": "A story unfolds.",
            "narrative_direction": "Forward",
            "is_compressed": False,
            "compression_result": None,
            "created_at": now,
            "updated_at": now
        }
        
        return arc
    
    def save_segment(self, story_id: str, segment_id: str, segment: Dict[str, Any]) -> bool:
        """Save a segment to disk.
        
        Args:
            story_id: ID of story
            segment_id: ID of segment
            segment: Segment data
            
        Returns:
            True if successful, False otherwise
        """
        segment_dir = self.data_dir / story_id / "storysegment"
        segment_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            segment_file = segment_dir / f"{segment_id}.json"
            with open(segment_file, 'w') as f:
                json.dump(segment, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save segment {segment_id}: {e}")
            return False
    
    def save_recap(self, story_id: str, recap: Dict[str, Any]) -> bool:
        """Save an EpisodeRecap to disk.
        
        Args:
            story_id: ID of story
            recap: EpisodeRecap data
            
        Returns:
            True if successful, False otherwise
        """
        recap_dir = self.data_dir / story_id / "episoderecap"
        recap_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            recap_file = recap_dir / f"{recap['id']}.json"
            with open(recap_file, 'w') as f:
                json.dump(recap, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save recap: {e}")
            return False
    
    def save_arc(self, story_id: str, arc: Dict[str, Any]) -> bool:
        """Save a StoryArc to disk.
        
        Args:
            story_id: ID of story
            arc: StoryArc data
            
        Returns:
            True if successful, False otherwise
        """
        arc_dir = self.data_dir / story_id / "storyarc"
        arc_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            arc_file = arc_dir / f"{arc['id']}.json"
            with open(arc_file, 'w') as f:
                json.dump(arc, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save arc: {e}")
            return False
    
    def validate_migration(self, story_id: str, segments: Dict[str, Dict[str, Any]]) -> bool:
        """Validate that migration was successful.
        
        Args:
            story_id: ID of story
            segments: Original segment data
            
        Returns:
            True if validation passes, False otherwise
        """
        # Check that all segments still exist
        segment_dir = self.data_dir / story_id / "storysegment"
        migrated_count = len(list(segment_dir.glob("*.json")))
        
        if migrated_count != len(segments):
            logger.error(
                f"Data loss detected: {len(segments)} original segments, "
                f"{migrated_count} migrated segments"
            )
            return False
        
        # Check that v2 fields exist in migrated segments
        for seg_id, seg_data in segments.items():
            try:
                migrated_file = segment_dir / f"{seg_id}.json"
                if not migrated_file.exists():
                    logger.error(f"Segment missing: {seg_id}")
                    return False
                
                with open(migrated_file, 'r') as f:
                    migrated = json.load(f)
                
                # Check for key v2 fields
                required_fields = [
                    "episode_number", "status", "character_states",
                    "pacing_weight", "protagonist_alive"
                ]
                
                for field in required_fields:
                    if field not in migrated:
                        logger.error(f"Missing v2 field '{field}' in segment {seg_id}")
                        return False
            
            except Exception as e:
                logger.error(f"Validation error for segment {seg_id}: {e}")
                return False
        
        logger.info(f"✅ Validation passed: {migrated_count} segments migrated successfully")
        return True
    
    def migrate_story(self, story_id: str) -> bool:
        """Migrate a single story from v1 to v2.
        
        Args:
            story_id: ID of story to migrate
            
        Returns:
            True if migration successful, False otherwise
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Migrating story: {story_id}")
        logger.info(f"{'='*60}")
        
        # 1. Backup existing data
        logger.info("Step 1: Creating backup...")
        if not self.backup_story(story_id):
            logger.error("Backup failed, aborting migration")
            return False
        
        # 2. Load v1 segments
        logger.info("Step 2: Loading v1 segments...")
        segments = self.load_v1_segments(story_id)
        if not segments:
            logger.warning(f"No segments found for {story_id}")
            return False
        
        # 3. Load v1 choices (for future use)
        logger.info("Step 3: Loading v1 choices...")
        choices = self.load_v1_choices(story_id)
        
        # 4. Add v2 fields to segments
        logger.info("Step 4: Adding v2 fields...")
        migrated_segments = {}
        for idx, (seg_id, seg_data) in enumerate(segments.items()):
            migrated_segments[seg_id] = self.add_v2_fields_to_segment(seg_data, idx)
        
        # 5. Create default EpisodeRecap
        logger.info("Step 5: Creating default episode recap...")
        recap = self.create_default_episode_recap(story_id, migrated_segments)
        
        # 6. Create default StoryArc
        logger.info("Step 6: Creating default story arc...")
        arc = self.create_default_story_arc(story_id, migrated_segments)
        
        # 7. Save migrated segments
        logger.info("Step 7: Saving migrated segments...")
        for seg_id, seg_data in migrated_segments.items():
            if not self.save_segment(story_id, seg_id, seg_data):
                logger.error("Failed to save segments, restoring from backup")
                self.restore_story(story_id)
                return False
        
        # 8. Save recap
        logger.info("Step 8: Saving episode recap...")
        if not self.save_recap(story_id, recap):
            logger.error("Failed to save recap, restoring from backup")
            self.restore_story(story_id)
            return False
        
        # 9. Save arc
        logger.info("Step 9: Saving story arc...")
        if not self.save_arc(story_id, arc):
            logger.error("Failed to save arc, restoring from backup")
            self.restore_story(story_id)
            return False
        
        # 10. Validate migration
        logger.info("Step 10: Validating migration...")
        if not self.validate_migration(story_id, segments):
            logger.error("Validation failed, restoring from backup")
            self.restore_story(story_id)
            return False
        
        logger.info(f"✅ Successfully migrated {story_id}")
        self.migrations.append(story_id)
        return True
    
    def migrate_all(self) -> bool:
        """Migrate all stories.
        
        Returns:
            True if all migrations successful, False otherwise
        """
        stories = self.get_story_dirs()
        
        if not stories:
            logger.error("No stories found to migrate")
            return False
        
        # Filter out non-story directories
        story_dirs = [s for s in stories if (self.data_dir / s).is_dir()]
        
        logger.info(f"Found {len(story_dirs)} stories to migrate")
        
        success_count = 0
        for story_id in story_dirs:
            # Skip backup and test directories
            if story_id.startswith("test") or story_id.startswith("cleanup"):
                logger.info(f"Skipping {story_id}")
                continue
            
            if self.migrate_story(story_id):
                success_count += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Migration Summary")
        logger.info(f"{'='*60}")
        logger.info(f"Successfully migrated: {success_count}/{len(story_dirs)} stories")
        
        return success_count > 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate v1 stories to v2 format"
    )
    parser.add_argument(
        "story",
        nargs="?",
        default=None,
        help="Story ID to migrate (or --all for all stories)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all stories"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback a migration from backup"
    )
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.rollback and args.story:
        # Rollback mode
        logger.info(f"Rolling back migration for {args.story}")
        if manager.restore_story(args.story):
            logger.info(f"✅ Successfully rolled back {args.story}")
            return 0
        else:
            logger.error(f"❌ Failed to rollback {args.story}")
            return 1
    
    elif args.all:
        # Migrate all stories
        if manager.migrate_all():
            return 0
        else:
            return 1
    
    elif args.story:
        # Migrate single story
        if manager.migrate_story(args.story):
            return 0
        else:
            return 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())
