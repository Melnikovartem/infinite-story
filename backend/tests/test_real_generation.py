"""Real API generation tests — calls actual LLM and validates full pipeline.

These tests call the real OpenRouter API with the configured model and validate
that:
1. The raw LLM output can be parsed by AIResponseParser
2. The parsed data creates valid model objects
3. All expected fields are populated with meaningful content

Run with: python -m pytest tests/test_real_generation.py -v -s --timeout=120

These tests are slow (~5-15s each) and require a valid API key.
"""

import json
import os
import sys
import pytest
import uuid
import logging

# Load .env before any imports that use config
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from app.models.story import Story
from app.models.story_arc import StoryArc
from app.models.story_faction import StoryFaction
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_magic_system import StoryMagicSystem
from app.engine.generator import TextGenerator
from app.engine.openrouter_generator import OpenRouterGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

from app.engine.generators.arc_generator import ArcGenerator, ARC_SCHEMA
from app.engine.generators.faction_generator import FactionGenerator, FACTION_SCHEMA, FACTION_FALLBACK
from app.engine.generators.character_generator import CharacterGenerator, CHARACTER_SCHEMA, CHARACTER_FALLBACK
from app.engine.generators.location_generator import LocationGenerator, LOCATION_SCHEMA, LOCATION_FALLBACK
from app.engine.generators.magic_system_generator import (
    MagicSystemGenerator, PARADIGM_SCHEMA, SYSTEM_SCHEMA, SYSTEM_FALLBACK,
)
from app.engine.character_state_updater import _ENHANCE_SCHEMA, _NEW_CHAR_SCHEMA

logger = logging.getLogger("test_real_generation")

# ============================================================================
# Skip if no API key
# ============================================================================

API_KEY = os.getenv("OPENROUTER_API_KEY")
SKIP_REASON = "OPENROUTER_API_KEY not set — skipping real API tests"

pytestmark = pytest.mark.skipif(not API_KEY, reason=SKIP_REASON)


# ============================================================================
# Helpers
# ============================================================================

def make_story(**overrides) -> Story:
    defaults = dict(
        id="real_test_story",
        title="The Veil of Thornreach",
        description="A dark fantasy world where thorns grow from shadows and ancient powers stir beneath the earth",
        genre="Dark Fantasy",
        user_id="test_user",
        start_segment_id="seg_001",
    )
    defaults.update(overrides)
    return Story(**defaults)


def make_real_generator() -> OpenRouterGenerator:
    """Create a real OpenRouter generator from .env config."""
    return OpenRouterGenerator(
        api_key=API_KEY,
        model=os.getenv("AI_MODEL", "deepseek-v3"),
        temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
        max_tokens=2000,
        site_url=os.getenv("OPENROUTER_SITE_URL"),
        site_name=os.getenv("OPENROUTER_SITE_NAME"),
        auto_fallback=True,
    )


def validate_non_empty_string(val, field_name, min_len=2):
    """Assert a string field is populated with real content."""
    assert isinstance(val, str), f"{field_name} should be str, got {type(val)}"
    assert len(val.strip()) >= min_len, f"{field_name} is too short or empty: {val!r}"


def validate_non_empty_list(val, field_name, min_len=1):
    """Assert a list field has items."""
    assert isinstance(val, list), f"{field_name} should be list, got {type(val)}"
    assert len(val) >= min_len, f"{field_name} has {len(val)} items, expected >= {min_len}"


# ============================================================================
# Tests
# ============================================================================

class TestRealFactionGeneration:
    """Generate factions with real LLM and validate parsing."""

    @pytest.mark.asyncio
    async def test_generate_factions(self):
        story = make_story()
        gen = make_real_generator()
        try:
            faction_gen = FactionGenerator(story, gen)
            factions = await faction_gen.generate_factions(
                count=3,
                world_description="A dark fantasy world plagued by thorn-blight. Ancient magic and political intrigue shape the fate of nations.",
                major_tensions=["The spreading blight threatens all", "Factions blame each other", "Resources are scarce"],
            )

            print(f"\n--- Generated {len(factions)} factions ---")
            assert len(factions) == 3, f"Expected 3 factions, got {len(factions)}"

            for i, f in enumerate(factions):
                print(f"\n[Faction {i+1}]")
                print(f"  name: {f.name!r}")
                print(f"  description: {f.description!r}")
                print(f"  goals: {f.goals!r}")
                print(f"  leader: {f.leader!r}")
                print(f"  resources: {f.resources!r}")
                print(f"  alignment: {f.alignment!r}")

                assert isinstance(f, StoryFaction)
                validate_non_empty_string(f.name, f"faction[{i}].name")
                validate_non_empty_string(f.description, f"faction[{i}].description")
                validate_non_empty_list(f.goals, f"faction[{i}].goals", min_len=1)
                validate_non_empty_string(f.leader, f"faction[{i}].leader")
                # resources and alignment can be short
                assert isinstance(f.resources, str)
                assert isinstance(f.alignment, str)
        finally:
            await gen.close()


class TestRealCharacterGeneration:
    """Generate characters with real LLM and validate parsing."""

    @pytest.mark.asyncio
    async def test_generate_characters(self, temp_data_dir):
        story = make_story()
        gen = make_real_generator()
        try:
            char_gen = CharacterGenerator(story, gen)
            chars = await char_gen.generate_initial_characters(count=3)

            print(f"\n--- Generated {len(chars)} characters ---")
            assert len(chars) == 3, f"Expected 3 characters, got {len(chars)}"

            for i, c in enumerate(chars):
                print(f"\n[Character {i+1}]")
                print(f"  name: {c.name!r}")
                print(f"  description: {c.description!r}")
                print(f"  background: {c.background!r}")
                print(f"  personality: {c.personality!r}")
                print(f"  goals: {c.goals!r}")

                assert isinstance(c, StoryCharacter)
                validate_non_empty_string(c.name, f"char[{i}].name")
                validate_non_empty_string(c.description, f"char[{i}].description")
                validate_non_empty_string(c.background, f"char[{i}].background")
                validate_non_empty_list(c.personality, f"char[{i}].personality", min_len=2)
                # goals is a str
                assert isinstance(c.goals, str)
                assert len(c.goals.strip()) > 3, f"char[{i}].goals too short: {c.goals!r}"
        finally:
            await gen.close()


class TestRealLocationGeneration:
    """Generate locations with real LLM and validate parsing."""

    @pytest.mark.asyncio
    async def test_generate_locations(self):
        story = make_story()
        gen = make_real_generator()
        try:
            loc_gen = LocationGenerator(story, gen)
            locations = await loc_gen.generate_world_locations(
                world_description="A dark fantasy world plagued by thorn-blight. Cities fortified against encroaching thorns. Underground markets thrive.",
                fundamental_truths=["Thorns grow from shadows", "Pain fuels ancient magic", "The land remembers"],
            )

            print(f"\n--- Generated {len(locations)} locations ---")
            assert len(locations) >= 5, f"Expected >= 5 locations, got {len(locations)}"

            for i, loc in enumerate(locations):
                print(f"\n[Location {i+1}]")
                print(f"  name: {loc.name!r}")
                print(f"  description: {loc.description!r}")
                print(f"  full_description: {loc.full_description[:100]!r}...")

                assert isinstance(loc, StoryLocation)
                validate_non_empty_string(loc.name, f"loc[{i}].name")
                validate_non_empty_string(loc.description, f"loc[{i}].description")
                validate_non_empty_string(loc.full_description, f"loc[{i}].full_description")
                # full_description should be longer than description
                assert len(loc.full_description) >= len(loc.description), \
                    f"loc[{i}].full_description ({len(loc.full_description)}) shorter than description ({len(loc.description)})"
        finally:
            await gen.close()


class TestRealArcGeneration:
    """Generate arcs with real LLM and validate parsing."""

    @pytest.mark.asyncio
    async def test_generate_arcs(self, temp_data_dir):
        story = make_story()
        gen = make_real_generator()
        try:
            arc_gen = ArcGenerator(story, gen)
            arcs = await arc_gen.generate_future_arcs(count=3)

            print(f"\n--- Generated {len(arcs)} arcs ---")
            assert len(arcs) == 3, f"Expected 3 arcs, got {len(arcs)}"

            for i, a in enumerate(arcs):
                print(f"\n[Arc {i+1}]")
                print(f"  title: {a.title!r}")
                print(f"  premise: {a.premise!r}")
                print(f"  central_conflict: {a.central_conflict!r}")
                print(f"  themes: {a.themes!r}")
                print(f"  mysteries: {a.unresolved_mysteries!r}")
                print(f"  hooks: {a.plot_hooks!r}")

                assert isinstance(a, StoryArc)
                validate_non_empty_string(a.title, f"arc[{i}].title")
                validate_non_empty_string(a.premise, f"arc[{i}].premise")
                validate_non_empty_string(a.central_conflict, f"arc[{i}].central_conflict")
                validate_non_empty_list(a.themes, f"arc[{i}].themes", min_len=2)
        finally:
            await gen.close()


class TestRealMagicSystemGeneration:
    """Generate magic system with real LLM and validate parsing."""

    @pytest.mark.asyncio
    async def test_generate_magic_system(self):
        story = make_story()
        gen = make_real_generator()
        try:
            magic_gen = MagicSystemGenerator(story, gen)
            system = await magic_gen.generate_magic_system(
                world_description="A dark fantasy world where thorns grow from shadows and ancient powers stir beneath the earth. Pain and sacrifice fuel the old magic.",
                genre="Dark Fantasy",
            )

            print(f"\n--- Magic System ---")
            if system is None:
                print("  LLM decided: no magic system (this is valid for some worlds)")
                # For a dark fantasy world, we'd expect magic, but the LLM has freedom
                return

            print(f"  name: {system.name!r}")
            print(f"  description: {system.description!r}")
            print(f"  rules: {system.rules!r}")
            print(f"  limitations: {system.limitations!r}")
            print(f"  costs: {system.costs!r}")
            print(f"  origin: {system.origin!r}")
            print(f"  practitioners: {system.practitioners!r}")
            print(f"  technology_level: {system.technology_level!r}")

            assert isinstance(system, StoryMagicSystem)
            validate_non_empty_string(system.name, "magic.name")
            validate_non_empty_string(system.description, "magic.description")
            validate_non_empty_list(system.rules, "magic.rules", min_len=2)
            validate_non_empty_list(system.limitations, "magic.limitations", min_len=2)
            validate_non_empty_list(system.costs, "magic.costs", min_len=2)
        finally:
            await gen.close()

    @pytest.mark.asyncio
    async def test_no_magic_for_realistic_fiction(self):
        story = make_story(
            title="The Last Summer",
            description="A literary novel about a family reuniting at their childhood home",
            genre="Literary Fiction",
        )
        gen = make_real_generator()
        try:
            magic_gen = MagicSystemGenerator(story, gen)
            system = await magic_gen.generate_magic_system(
                world_description="A quiet coastal town in present-day New England. No supernatural elements.",
                genre="Literary Fiction",
            )
            print(f"\n--- Literary Fiction: magic system = {system!r}")
            # Should be None for literary fiction
            assert system is None, f"Expected None for literary fiction, got: {system.name if system else 'None'}"
        finally:
            await gen.close()


class TestRealGenerateStructured:
    """Test generate_structured() directly with real API calls."""

    @pytest.mark.asyncio
    async def test_recap_schema(self):
        """Generate an episode recap with real LLM."""
        from app.engine.episode_recap_generator import RECAP_SCHEMA

        gen = make_real_generator()
        try:
            result = await gen.generate_structured(
                system_prompt="You are a narrative editor creating episode recaps.",
                user_prompt="""Create a recap for Episode 3 of a dark fantasy story.
                
The episode featured:
- The protagonist Kael discovered her metal-sense could detect blight-roots
- The Thornguard fell back from the outer walls
- The Pale Court seized the granary during the chaos
- A mysterious figure called the Pale Gardener appeared briefly

Summarize the episode with a title, key themes, hooks, and unresolved questions.""",
                schema=RECAP_SCHEMA,
            )

            print(f"\n--- Recap ---")
            print(f"  title: {result.get('title')!r}")
            print(f"  summary: {result.get('summary')!r}")
            print(f"  key_themes: {result.get('key_themes')!r}")
            print(f"  themes_explored: {result.get('themes_explored')!r}")
            print(f"  hook_for_next: {result.get('hook_for_next')!r}")
            print(f"  unresolved_new: {result.get('unresolved_new')!r}")

            assert isinstance(result, dict)
            validate_non_empty_string(result.get("title", ""), "recap.title")
            validate_non_empty_string(result.get("summary", ""), "recap.summary")
            assert isinstance(result.get("key_themes", []), list)
        finally:
            await gen.close()

    @pytest.mark.asyncio
    async def test_character_enhance_schema(self):
        """Generate character enhancement with real LLM."""
        gen = make_real_generator()
        try:
            result = await gen.generate_structured(
                system_prompt="You are updating a character's state after a dramatic event.",
                user_prompt="""Character: Kael Ashford
Current: A lean, sharp-eyed woman with burn scars on her left arm.
Event: She was caught in a blight-root eruption while trying to save civilians. She succeeded but at great personal cost — new scars, exhaustion, and a deeper connection to her metal-sense ability.

Update her state:""",
                schema=_ENHANCE_SCHEMA,
            )

            print(f"\n--- Character Enhancement ---")
            for k, v in result.items():
                print(f"  {k}: {v!r}")

            assert isinstance(result, dict)
            # At minimum, description should be populated
            if result.get("description"):
                validate_non_empty_string(result["description"], "enhance.description")
            if result.get("goal_progress") is not None:
                assert isinstance(result["goal_progress"], (int, float)), \
                    f"goal_progress should be numeric, got {type(result['goal_progress'])}"
        finally:
            await gen.close()

    @pytest.mark.asyncio
    async def test_new_character_schema(self):
        """Generate a new character with real LLM."""
        gen = make_real_generator()
        try:
            result = await gen.generate_structured(
                system_prompt="You create characters for dark fantasy stories.",
                user_prompt="""Create a new minor character for a dark fantasy story.
Theme: survival and sacrifice
Hint: a healer who operates in the underground market""",
                schema=_NEW_CHAR_SCHEMA,
            )

            print(f"\n--- New Character ---")
            for k, v in result.items():
                print(f"  {k}: {v!r}")

            assert isinstance(result, dict)
            validate_non_empty_string(result.get("name", ""), "new_char.name")
            validate_non_empty_string(result.get("description", ""), "new_char.description")
            validate_non_empty_string(result.get("background", ""), "new_char.background")
            assert isinstance(result.get("personality_traits", []), list)
        finally:
            await gen.close()
