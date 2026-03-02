"""Tests for EpisodeRecap and CharacterState models (E0-2)."""

import pytest
from datetime import datetime, UTC
from app.models.episode_recap import EpisodeRecap, CharacterState


class TestCharacterState:
    """Tests for CharacterState model."""
    
    def test_character_state_creation(self):
        """Create a character state with all fields."""
        char_state = CharacterState(
            id="char_1",
            name="Alice",
            status="alive",
            mood="hopeful",
            location="castle",
            loyalty=0.8
        )
        
        assert char_state.id == "char_1"
        assert char_state.name == "Alice"
        assert char_state.status == "alive"
        assert char_state.mood == "hopeful"
        assert char_state.location == "castle"
        assert char_state.loyalty == 0.8
    
    def test_character_state_defaults(self):
        """Character state with default values."""
        char_state = CharacterState(
            id="char_2",
            name="Bob",
            status="alive",
            mood="angry"
        )
        
        assert char_state.loyalty == 0.0
        assert char_state.location is None
        assert char_state.relationships == {}
        assert char_state.goals == []
        assert char_state.custom_data == {}
    
    def test_character_state_loyalty_bounds(self):
        """Loyalty field is constrained to -1.0 to 1.0."""
        # Valid bounds
        for loyalty in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            char_state = CharacterState(
                id="char_3",
                name="Test",
                status="alive",
                mood="neutral",
                loyalty=loyalty
            )
            assert char_state.loyalty == loyalty
    
    def test_character_state_with_relationships(self):
        """Character state with relationships and goals."""
        char_state = CharacterState(
            id="char_4",
            name="Charlie",
            status="alive",
            mood="determined",
            relationships={"char_1": "trusts", "char_2": "fears"},
            goals=["Find the artifact", "Survive the night"]
        )
        
        assert len(char_state.relationships) == 2
        assert char_state.relationships["char_1"] == "trusts"
        assert len(char_state.goals) == 2
    
    def test_character_state_with_custom_data(self):
        """Character state with custom metadata."""
        custom = {"wounds": 3, "inventory": ["sword", "shield"]}
        char_state = CharacterState(
            id="char_5",
            name="Diana",
            status="alive",
            mood="wounded",
            custom_data=custom
        )
        
        assert char_state.custom_data == custom


class TestEpisodeRecap:
    """Tests for EpisodeRecap model."""
    
    def test_episode_recap_creation(self):
        """Create an episode recap with basic fields."""
        recap = EpisodeRecap(
            id="recap_1",
            story_id="story_1",
            episode_number=1,
            title="The Beginning",
            summary="The hero starts their journey in a peaceful village.",
            tone="hopeful"
        )
        
        assert recap.id == "recap_1"
        assert recap.story_id == "story_1"
        assert recap.episode_number == 1
        assert recap.title == "The Beginning"
        assert recap.tone == "hopeful"
    
    def test_episode_recap_defaults(self):
        """Episode recap with default values."""
        recap = EpisodeRecap(
            id="recap_2",
            story_id="story_1",
            episode_number=2,
            title="The Challenge",
            summary="The hero faces their first real test.",
            tone="tense"
        )
        
        assert recap.arc_id is None
        assert recap.starting_character_states == {}
        assert recap.ending_character_states == {}
        assert recap.segment_ids == []
        assert recap.choice_ids == []
        assert recap.key_themes == []
        assert recap.generator_model == "gpt-4o-mini"
    
    def test_episode_recap_with_character_states(self):
        """Episode recap with character state snapshots."""
        alice_start = CharacterState(
            id="alice",
            name="Alice",
            status="alive",
            mood="hopeful",
            loyalty=0.0
        )
        alice_end = CharacterState(
            id="alice",
            name="Alice",
            status="alive",
            mood="determined",
            loyalty=0.5
        )
        
        recap = EpisodeRecap(
            id="recap_3",
            story_id="story_1",
            episode_number=1,
            title="The Beginning",
            summary="Alice begins her journey.",
            tone="hopeful",
            starting_character_states={"alice": alice_start},
            ending_character_states={"alice": alice_end}
        )
        
        assert len(recap.starting_character_states) == 1
        assert len(recap.ending_character_states) == 1
        assert recap.ending_character_states["alice"].mood == "determined"
        assert recap.ending_character_states["alice"].loyalty == 0.5
    
    def test_episode_recap_with_segments_and_choices(self):
        """Episode recap with segment and choice tracking."""
        recap = EpisodeRecap(
            id="recap_4",
            story_id="story_1",
            episode_number=1,
            title="The Beginning",
            summary="A short episode.",
            tone="neutral",
            segment_ids=["seg_1", "seg_2", "seg_3"],
            choice_ids=["choice_1", "choice_2"]
        )
        
        assert len(recap.segment_ids) == 3
        assert len(recap.choice_ids) == 2
    
    def test_episode_recap_with_themes(self):
        """Episode recap with key themes."""
        recap = EpisodeRecap(
            id="recap_5",
            story_id="story_1",
            episode_number=2,
            title="The Betrayal",
            summary="A dark turn of events.",
            tone="dark",
            key_themes=["betrayal", "loss", "redemption"]
        )
        
        assert len(recap.key_themes) == 3
        assert "betrayal" in recap.key_themes
    
    def test_episode_recap_with_arc(self):
        """Episode recap associated with a story arc."""
        recap = EpisodeRecap(
            id="recap_6",
            story_id="story_1",
            episode_number=1,
            arc_id="arc_001",
            title="Arc Beginning",
            summary="First episode of the arc.",
            tone="hopeful"
        )
        
        assert recap.arc_id == "arc_001"


class TestEpisodeRecapMethods:
    """Tests for EpisodeRecap helper methods."""
    
    def test_get_short_overview(self):
        """Test short overview method."""
        recap = EpisodeRecap(
            id="recap_7",
            story_id="story_1",
            episode_number=3,
            title="The Revelation",
            summary="The secret is revealed.",
            tone="dramatic"
        )
        
        overview = recap.get_short_overview()
        assert "Episode 3" in overview
        assert "The Revelation" in overview
    
    def test_get_full_overview(self):
        """Test full overview method."""
        alice = CharacterState(
            id="alice",
            name="Alice",
            status="alive",
            mood="relieved",
            loyalty=0.7
        )
        
        recap = EpisodeRecap(
            id="recap_8",
            story_id="story_1",
            episode_number=2,
            title="The Triumph",
            summary="Alice achieves victory.",
            tone="triumphant",
            key_themes=["victory", "courage"],
            ending_character_states={"alice": alice}
        )
        
        overview = recap.get_full_overview()
        assert "Episode 2" in overview
        assert "The Triumph" in overview
        assert "triumphant" in overview
        assert "victory, courage" in overview
        assert "Alice" in overview
        assert "relieved" in overview
    
    def test_get_full_overview_empty_characters(self):
        """Test full overview with no character states."""
        recap = EpisodeRecap(
            id="recap_9",
            story_id="story_1",
            episode_number=1,
            title="Empty",
            summary="No characters.",
            tone="neutral"
        )
        
        overview = recap.get_full_overview()
        assert "No character states recorded" in overview


class TestEpisodeRecapSerialization:
    """Tests for EpisodeRecap save/load."""
    
    def test_episode_recap_save_and_load(self):
        """Save and load episode recap."""
        alice = CharacterState(
            id="alice",
            name="Alice",
            status="alive",
            mood="hopeful",
            loyalty=0.5
        )
        
        recap = EpisodeRecap(
            id="recap_10",
            story_id="test_story",
            episode_number=1,
            title="The Beginning",
            summary="Alice starts her journey.",
            tone="hopeful",
            key_themes=["hope", "adventure"],
            ending_character_states={"alice": alice},
            segment_ids=["seg_1", "seg_2"],
            choice_ids=["choice_1"]
        )
        
        # Save
        recap.save()
        
        # Load
        loaded = EpisodeRecap.load("test_story", "recap_10")
        
        assert loaded is not None
        assert loaded.episode_number == 1
        assert loaded.title == "The Beginning"
        assert loaded.tone == "hopeful"
        assert len(loaded.key_themes) == 2
        assert len(loaded.segment_ids) == 2
        assert "alice" in loaded.ending_character_states
        assert loaded.ending_character_states["alice"].mood == "hopeful"
    
    def test_episode_recap_with_multiple_characters(self):
        """Save and load recap with multiple characters."""
        alice = CharacterState(
            id="alice",
            name="Alice",
            status="alive",
            mood="determined",
            loyalty=0.8
        )
        bob = CharacterState(
            id="bob",
            name="Bob",
            status="alive",
            mood="cautious",
            loyalty=-0.3
        )
        
        recap = EpisodeRecap(
            id="recap_11",
            story_id="test_story",
            episode_number=2,
            title="The Alliance",
            summary="Alice and Bob meet.",
            tone="tense",
            ending_character_states={"alice": alice, "bob": bob}
        )
        
        recap.save()
        loaded = EpisodeRecap.load("test_story", "recap_11")
        
        assert len(loaded.ending_character_states) == 2
        assert loaded.ending_character_states["alice"].loyalty == 0.8
        assert loaded.ending_character_states["bob"].loyalty == -0.3
