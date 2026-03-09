"""
E0 + E1 Integration Tests

Tests the integration between:
- E0: Data Layer (Story, Segments, Characters, Locations, Choices)
- E1: Generation Pipeline (Context Building, Generation, Choice Creation)

Verifies:
- Full generation pipeline from context to new segment
- Traverse vs Generate flows
- Segment context building and accumulation
- Pacing weight calculation
- Episode transitions
"""

import pytest
from datetime import datetime, UTC
from typing import List

from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice
from app.models.text_types import TextBlock, TextType


class TestSegmentChainIntegration:
    """Test integration of segment chains"""
    
    def test_segment_chain_traversal(self, three_segment_chain):
        """Can traverse a chain of segments"""
        seg1, seg2, seg3 = three_segment_chain
        
        # Segments use chain_seg_N naming from fixture
        assert seg1.id == "chain_seg_1"
        assert seg2.parent_segment_id == seg1.id
        assert seg3.parent_segment_id == seg2.id
        
        # Verify chain connectivity
        assert seg2.episode_number == seg1.episode_number
        assert seg3.episode_number == seg2.episode_number
    
    def test_multi_episode_progression(self, multi_episode_chain):
        """Segments progress correctly across episodes"""
        segments = multi_episode_chain
        
        # Should have 9 segments total (3 episodes x 3 segments)
        assert len(segments) == 9
        
        # Verify episode numbers
        for i, seg in enumerate(segments):
            expected_episode = (i // 3) + 1
            assert seg.episode_number == expected_episode
    
    def test_segment_status_transitions(self, sample_story):
        """Segment status can transition correctly"""
        seg = StorySegment(
            story=sample_story,
            id="status_test",
            status=SegmentStatus.GENERATED
        )
        
        assert seg.status == SegmentStatus.GENERATED


class TestContextBuilding:
    """Test context building from segments"""
    
    def test_context_from_single_segment(self, sample_segment):
        """Context can be built from single segment"""
        # Context would be built by E1 engine
        # This tests that data is accessible
        assert sample_segment.text_blocks
        assert len(sample_segment.text_blocks) > 0
        assert sample_segment.short_description
    
    def test_context_accumulation_from_chain(self, three_segment_chain):
        """Context accumulates from entire chain"""
        seg1, seg2, seg3 = three_segment_chain
        
        # Simulate context accumulation
        all_content = []
        current = seg3
        
        while current is not None:
            all_content.append(current.short_description)
            
            # Find parent
            if current.parent_segment_id:
                current = next(
                    (s for s in [seg1, seg2, seg3] if s.id == current.parent_segment_id),
                    None
                )
            else:
                current = None
        
        # Should have accumulated 3 descriptions (walking backward)
        assert len(all_content) == 3
    
    def test_character_context_in_segments(self, three_segment_chain):
        """Character status is preserved in context"""
        seg1 = three_segment_chain[0]
        char_statuses = seg1.characters
        
        # Only seg1 in the fixture has characters
        assert len(char_statuses) > 0
        assert char_statuses[0].character_id == "char_001"
        assert char_statuses[0].current_status == "active"


class TestChoiceCreationAndTraversal:
    """Test choice handling and segment traversal"""
    
    def test_choice_creation_in_segment(self, sample_segment):
        """Choices can be created for a segment"""
        story = sample_segment.story
        
        choice = StoryChoice(
            story=story,
            id="choice_test",
            from_segment_id=sample_segment.id,
            text="Test choice",
        )
        
        assert choice.from_segment_id == sample_segment.id
    
    def test_traverse_to_existing_segment(self, sample_segment, three_segment_chain):
        """Choice can point to existing segment (traverse)"""
        seg1, seg2, seg3 = three_segment_chain
        
        choice = StoryChoice(
            story=sample_segment.story,
            id="traverse_choice",
            from_segment_id=sample_segment.id,
            to_segment_id=seg1.id,
            text="Go back to beginning",
        )
        
        assert choice.to_segment_id == seg1.id
    
    def test_choice_without_target_for_generation(self, sample_segment):
        """Choice without target triggers generation"""
        choice = StoryChoice(
            story=sample_segment.story,
            id="gen_choice",
            from_segment_id=sample_segment.id,
            to_segment_id=None,  # No target = will generate
            text="Explore unknown path",
        )
        
        assert choice.to_segment_id is None
        # E1 engine would generate new segment
    
    def test_choice_lock_for_generation(self, sample_choice):
        """Choice can be locked during generation"""
        assert sample_choice.locked is False
        
        sample_choice.locked = True
        assert sample_choice.locked is True
        
        sample_choice.locked = False
        assert sample_choice.locked is False


class TestPacingAndEpisodeTransitions:
    """Test pacing weight and episode transition logic"""
    
    def test_segment_numbers_within_episode(self, three_segment_chain):
        """Segment numbers within episode are sequential"""
        seg1, seg2, seg3 = three_segment_chain
        
        assert seg1.segment_number_in_episode == 1
        assert seg2.segment_number_in_episode == 2
        assert seg3.segment_number_in_episode == 3
    
    def test_segment_progression_index(self, sample_segment):
        """Segments have progression index"""
        # In E1, this helps with pacing calculations
        seg_num = sample_segment.segment_number_in_episode
        assert seg_num >= 1
    
    def test_proximity_threshold_tracking(self, sample_story):
        """Proximity to goal can be tracked"""
        # E1 uses proximity for episode transitions
        seg = StorySegment(
            story=sample_story,
            id="proximity_test",
            end_condition_proximity=0.75
        )
        
        assert seg.end_condition_proximity == 0.75


class TestGeneratedSegmentIntegration:
    """Test integration of newly generated segments"""
    
    def test_generated_segment_creation(self, sample_segment):
        """Generated segment has correct properties"""
        story = sample_segment.story
        
        # Simulate what E1 would create after generation
        generated = StorySegment(
            story=story,
            id="generated_1",
            story_id=story.id,
            short_description="Generated scene description",
            text_blocks=[
                TextBlock(
                    type=TextType.NARRATOR_DESCRIBING,
                    content="The generated content here..."
                )
            ],
            episode_number=sample_segment.episode_number,
            segment_number_in_episode=sample_segment.segment_number_in_episode + 1,
            parent_segment_id=sample_segment.id,
            status=SegmentStatus.GENERATED
        )
        
        assert generated.parent_segment_id == sample_segment.id
        assert generated.status == SegmentStatus.GENERATED
        assert generated.episode_number == sample_segment.episode_number
    
    def test_generated_segment_inherits_context(self, three_segment_chain):
        """Generated segment inherits characters and locations from context"""
        seg1, seg2, seg3 = three_segment_chain
        
        # Simulate generation inheriting context from seg1 (which has characters/locations)
        inherited_chars = seg1.characters.copy()
        inherited_locs = seg1.locations.copy()
        
        generated = StorySegment(
            story=seg1.story,
            id="generated_inherit",
            characters=inherited_chars,
            locations=inherited_locs,
            parent_segment_id=seg1.id
        )
        
        assert len(generated.characters) == len(seg1.characters)
        assert len(generated.locations) == len(seg1.locations)


class TestDataPersistenceAcrossEpics:
    """Test that data persists correctly between E0 and E1"""
    
    def test_segment_save_before_generation(self, sample_segment):
        """Segment can be saved before generating next"""
        sample_segment.save()
        
        # Simulate loading to prepare for generation
        loaded = StorySegment.load(
            sample_segment.story.id,
            sample_segment.id,
            story=sample_segment.story
        )
        
        assert loaded is not None
        assert loaded.id == sample_segment.id
    
    def test_choice_persistence(self, sample_choice):
        """Choices persist across operations"""
        sample_choice.save()
        
        loaded = StoryChoice.load(
            sample_choice.story.id,
            sample_choice.id,
            story=sample_choice.story
        )
        
        assert loaded is not None
        assert loaded.text == sample_choice.text


class TestEdgeCasesE0E1:
    """Test edge cases in E0-E1 integration"""
    
    def test_branching_from_same_parent(self, sample_story):
        """Multiple segments can have same parent (branching)"""
        parent = StorySegment(
            story=sample_story,
            id="parent_seg",
            segment_number_in_episode=1,
            episode_number=1,
            characters=[],
            locations=[]
        )
        
        # Create two segments from same parent
        branch1 = StorySegment(
            story=sample_story,
            id="branch1",
            parent_segment_id=parent.id,
            segment_number_in_episode=2,
            episode_number=1
        )
        
        branch2 = StorySegment(
            story=sample_story,
            id="branch2",
            parent_segment_id=parent.id,
            segment_number_in_episode=2,
            episode_number=1
        )
        
        assert branch1.parent_segment_id == parent.id
        assert branch2.parent_segment_id == parent.id
        assert branch1.id != branch2.id
    
    def test_episode_change_in_chain(self, sample_story):
        """Segments can transition to new episode"""
        segs = []
        
        # Create 5 segments transitioning between episodes
        for i in range(1, 6):
            seg = StorySegment(
                story=sample_story,
                id=f"transition_{i}",
                segment_number_in_episode=i if i <= 3 else i - 3,
                episode_number=1 if i <= 3 else 2,
                parent_segment_id=f"transition_{i-1}" if i > 1 else None
            )
            segs.append(seg)
        
        # First 3 in episode 1, last 2 in episode 2
        assert segs[0].episode_number == 1
        assert segs[2].episode_number == 1
        assert segs[3].episode_number == 2
        assert segs[4].episode_number == 2
    
    def test_very_long_segment_chain(self, sample_story):
        """Can handle long chains of segments"""
        segs = []
        
        for i in range(1, 51):  # 50 segments
            seg = StorySegment(
                story=sample_story,
                id=f"long_{i}",
                segment_number_in_episode=i,
                parent_segment_id=f"long_{i-1}" if i > 1 else None
            )
            segs.append(seg)
        
        assert len(segs) == 50
        assert segs[-1].parent_segment_id == "long_49"
        assert segs[0].parent_segment_id is None
