"""Tests for Character State Reconciliation (E2-3)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.story import Story
from app.models.story_episode import CharacterState
from app.engine.episode_recap_generator import EpisodeRecapGenerator


@pytest.fixture
def sample_story():
    """Create a test story."""
    return Story(
        id="test_story",
        title="Test Story",
        description="A test story"
    )


@pytest.fixture
def mock_generator():
    """Create a mock TextGenerator."""
    gen = AsyncMock()
    
    # Default response for generate
    async def mock_generate(system_prompt, user_prompt, context_type):
        response = MagicMock()
        response.error = None
        response.title = "Test Episode Title"
        response.summary = "A test episode summary"
        return response
    
    gen.generate = mock_generate
    return gen


@pytest.fixture
def sample_characters():
    """Create sample character states."""
    return {
        "char_1": CharacterState(
            id="char_1",
            name="Alice",
            status="alive",
            mood="hopeful"
        ),
        "char_2": CharacterState(
            id="char_2",
            name="Bob",
            status="alive",
            mood="angry"
        )
    }


class TestContradictionDetection:
    """Tests for detecting contradictions in change notes."""
    
    def test_detect_no_contradictions(self, sample_story, mock_generator):
        """Detect contradictions returns empty when no conflicts."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        changes = [
            "Alice becomes more confident",
            "Bob learns a secret",
            "The castle falls"
        ]
        
        contradictions = gen._detect_contradictions(changes)
        assert contradictions == []
    
    def test_detect_death_contradiction(self, sample_story, mock_generator):
        """Detect contradictions finds alive/dead conflicts."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        changes = [
            "Alice dies in battle",
            "Alice survives the encounter"
        ]
        
        contradictions = gen._detect_contradictions(changes)
        assert len(contradictions) == 1
        assert contradictions[0][0] == "Alice dies in battle"
        assert contradictions[0][1] == "Alice survives the encounter"
    
    def test_detect_mood_contradiction(self, sample_story, mock_generator):
        """Detect contradictions finds opposing mood changes."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        changes = [
            "Bob loses hope and becomes desperate",
            "Bob finds hope again and becomes optimistic"
        ]
        
        contradictions = gen._detect_contradictions(changes)
        assert len(contradictions) >= 1
    
    def test_are_contradictory_pairs(self, sample_story, mock_generator):
        """Test individual contradiction detection."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        # Test various contradictory pairs
        assert gen._are_contradictory("Alice dies", "Alice is alive") == True
        assert gen._are_contradictory("Bob trusts Charlie", "Bob betrays Charlie") == True
        assert gen._are_contradictory("Alice hates Bob", "Alice loves Bob") == True
        assert gen._are_contradictory("Charlie loses hope", "Charlie gains hope") == True
        
        # Test non-contradictory pairs
        assert gen._are_contradictory("Alice learns a secret", "Bob learns a secret") == False
        assert gen._are_contradictory("Castle burns", "Town burns") == False


class TestApplySingleChange:
    """Tests for applying single change notes."""
    
    def test_apply_mood_change(self, sample_story, mock_generator, sample_characters):
        """Apply mood change to character state."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        gen._apply_single_change(sample_characters, "Alice becomes angry")
        
        # Should update Alice's mood
        assert sample_characters["char_1"].mood == "angry"
    
    def test_apply_status_change(self, sample_story, mock_generator, sample_characters):
        """Apply status change to character state."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        gen._apply_single_change(sample_characters, "Bob dies in the confrontation")
        
        # Should update Bob's status
        assert sample_characters["char_2"].status == "dead"
    
    def test_apply_change_wrong_character_ignored(self, sample_story, mock_generator, sample_characters):
        """Apply change to non-existent character is ignored."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        original_alice_mood = sample_characters["char_1"].mood
        gen._apply_single_change(sample_characters, "Charlie becomes sad")
        
        # Should not affect Alice or Bob
        assert sample_characters["char_1"].mood == original_alice_mood
    
    def test_apply_multiple_mood_changes(self, sample_story, mock_generator, sample_characters):
        """Apply multiple mood changes."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        gen._apply_single_change(sample_characters, "Alice becomes determined")
        gen._apply_single_change(sample_characters, "Bob becomes desperate")
        
        assert sample_characters["char_1"].mood == "determined"
        assert sample_characters["char_2"].mood == "desperate"


@pytest.mark.asyncio
class TestReconcileWithAI:
    """Tests for AI-based reconciliation."""
    
    async def test_reconcile_no_contradictions(self, sample_story, mock_generator, sample_characters):
        """Reconcile with no contradictions applies changes directly."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        changes = [
            "Alice learns the truth",
            "Bob becomes more trusted"
        ]
        
        result = await gen.reconcile_character_states_with_ai(sample_characters, changes)
        
        # Should have updated states
        assert "char_1" in result
        assert "char_2" in result
    
    async def test_reconcile_with_contradictions_calls_ai(self, sample_story, mock_generator, sample_characters):
        """Reconcile with contradictions requests AI resolution."""
        # Mock generator with specific behavior
        ai_gen = AsyncMock()
        ai_called = False
        
        async def mock_generate_tracking(system_prompt, user_prompt, context_type):
            nonlocal ai_called
            if "Resolve character state" in user_prompt:
                ai_called = True
            response = MagicMock()
            response.error = None
            return response
        
        ai_gen.generate = mock_generate_tracking
        
        gen = EpisodeRecapGenerator(sample_story, ai_gen)
        
        changes = [
            "Alice dies in the explosion",
            "Alice survives and escapes"  # Contradiction!
        ]
        
        result = await gen.reconcile_character_states_with_ai(sample_characters, changes)
        
        # AI should have been called due to contradiction
        assert ai_called
    
    async def test_reconcile_ai_error_fallback(self, sample_story, mock_generator, sample_characters):
        """Reconcile handles AI errors gracefully."""
        # Mock generator that returns error
        error_gen = AsyncMock()
        
        async def mock_generate_with_error(system_prompt, user_prompt, context_type):
            response = MagicMock()
            response.error = "AI service unavailable"
            return response
        
        error_gen.generate = mock_generate_with_error
        
        gen = EpisodeRecapGenerator(sample_story, error_gen)
        
        changes = [
            "Alice dies",
            "Alice lives"  # Contradiction
        ]
        
        result = await gen.reconcile_character_states_with_ai(sample_characters, changes)
        
        # Should fall back to starting states on error
        assert result["char_1"].status == sample_characters["char_1"].status


class TestReconciliationIntegration:
    """Integration tests for character reconciliation."""
    
    def test_simple_reconciliation_flow(self, sample_story, mock_generator):
        """Test simple reconciliation without AI."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        starting_states = {
            "char_1": CharacterState(
                id="char_1",
                name="Alice",
                status="alive",
                mood="hopeful"
            )
        }
        
        changes = ["Alice becomes determined"]
        
        result = gen._reconcile_character_states(starting_states, changes)
        
        assert "char_1" in result
        assert result["char_1"].name == "Alice"
        # State should be a copy, not the original
        assert result["char_1"] is not starting_states["char_1"]
    
    def test_multiple_character_reconciliation(self, sample_story, mock_generator):
        """Test reconciliation with multiple characters."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        starting_states = {
            "alice": CharacterState(
                id="alice",
                name="Alice",
                status="alive",
                mood="hopeful"
            ),
            "bob": CharacterState(
                id="bob",
                name="Bob",
                status="alive",
                mood="neutral"
            )
        }
        
        changes = [
            "Alice learns the truth",
            "Bob becomes angry"
        ]
        
        result = gen._reconcile_character_states(starting_states, changes)
        
        assert len(result) == 2
        assert "alice" in result
        assert "bob" in result
    
    def test_reconciliation_preserves_untouched_fields(self, sample_story, mock_generator):
        """Test that reconciliation preserves fields not mentioned in changes."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        starting_states = {
            "alice": CharacterState(
                id="alice",
                name="Alice",
                status="alive",
                mood="hopeful",
                location="castle",
                relationships={"bob": "friend"},
                goals=["Save the kingdom"],
                custom_data={"wounds": 0}
            )
        }
        
        changes = []  # No changes
        
        result = gen._reconcile_character_states(starting_states, changes)
        
        alice = result["alice"]
        assert alice.location == "castle"
        assert alice.relationships == {"bob": "friend"}
        assert alice.goals == ["Save the kingdom"]
        assert alice.custom_data == {"wounds": 0}


@pytest.mark.asyncio
class TestReconciliationErrors:
    """Tests for error handling in reconciliation."""
    
    async def test_reconcile_empty_states(self, sample_story, mock_generator):
        """Reconcile handles empty starting states."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        result = await gen.reconcile_character_states_with_ai({}, [])
        
        assert result == {}
    
    async def test_reconcile_empty_changes(self, sample_story, mock_generator, sample_characters):
        """Reconcile handles empty change list."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        result = await gen.reconcile_character_states_with_ai(sample_characters, [])
        
        assert len(result) == len(sample_characters)
