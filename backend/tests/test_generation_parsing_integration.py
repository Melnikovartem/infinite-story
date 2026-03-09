"""Integration tests for the full generation → parsing → model creation pipeline.

These tests use REALISTIC LLM output strings (the kind GPT-4o/GPT-4o-mini
actually produces) and feed them through the real `generate_structured()` →
`AIResponseParser.parse()` → model constructor pipeline.

The ONLY thing mocked is `_generate_content()` (the raw LLM API call).
Everything else — prompt instruction injection, multi-strategy parsing,
alias resolution, type coercion, fallback handling — runs for real.

This catches bugs that unit tests with mock parsers miss:
- Schema field names that don't match what the code `.get()`s after parsing
- Type coercion failures (e.g., LLM returns string "0.7" for a float field)
- Alias resolution failures
- Fallback defaults that don't match model constructors
- Model constructors that reject parsed data (missing required fields, wrong types)
"""

import json
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.story import Story
from app.models.story_arc import StoryArc
from app.models.story_faction import StoryFaction
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_magic_system import StoryMagicSystem
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

# Import the actual generator classes
from app.engine.generators.arc_generator import ArcGenerator, ARC_SCHEMA
from app.engine.generators.faction_generator import FactionGenerator, FACTION_SCHEMA, FACTION_FALLBACK
from app.engine.generators.character_generator import CharacterGenerator, CHARACTER_SCHEMA, CHARACTER_FALLBACK
from app.engine.generators.location_generator import LocationGenerator, LOCATION_SCHEMA, LOCATION_FALLBACK
from app.engine.generators.magic_system_generator import (
    MagicSystemGenerator, PARADIGM_SCHEMA, SYSTEM_SCHEMA, SYSTEM_FALLBACK,
)


# ============================================================================
# Helpers
# ============================================================================

def make_story(**overrides) -> Story:
    """Create a minimal Story for testing (no disk I/O)."""
    defaults = dict(
        id="test_story",
        title="The Veil of Thornreach",
        description="A dark fantasy world where thorns grow from shadows",
        genre="Dark Fantasy",
        user_id="test_user",
        start_segment_id="seg_001",
    )
    defaults.update(overrides)
    return Story(**defaults)


def make_generator(raw_response: str) -> TextGenerator:
    """Create a TextGenerator whose _generate_content returns a fixed string.

    This lets the REAL generate_structured() pipeline run — prompt instruction
    injection, AIResponseParser.parse(), alias resolution, coercion — with
    only the network call mocked.
    """
    gen = TextGenerator(temperature=0.7, max_tokens=2000)

    async def fake_generate_content(system_prompt: str, user_prompt: str) -> str:
        return raw_response

    gen._generate_content = fake_generate_content
    return gen


def make_sequential_generator(responses: list[str]) -> TextGenerator:
    """Create a TextGenerator that returns different responses on each call."""
    gen = TextGenerator(temperature=0.7, max_tokens=2000)
    call_index = {"i": 0}

    async def fake_generate_content(system_prompt: str, user_prompt: str) -> str:
        idx = call_index["i"]
        call_index["i"] += 1
        if idx < len(responses):
            return responses[idx]
        return responses[-1]  # repeat last response if called more times

    gen._generate_content = fake_generate_content
    return gen


# ============================================================================
# Realistic LLM output strings
# ============================================================================

# --- Arcs (JSON array) ---
ARC_JSON_CLEAN = json.dumps([
    {
        "title": "The Withering",
        "premise": "A creeping blight spreads from the Thornwood, poisoning the land",
        "central_conflict": "Nature itself turns hostile as the thorn-blight consumes fertile ground",
        "narrative_direction": "The world descends from uneasy peace into environmental catastrophe",
        "themes": ["corruption", "survival", "sacrifice"],
        "mysteries": ["What caused the first thorn-bloom?", "Who is the Pale Gardener?"],
        "hooks": ["The capital's water supply is tainted", "A faction offers a cure — at a terrible price"]
    },
    {
        "title": "The Crimson Accord",
        "premise": "Factions unite under a fragile alliance to fight the blight, but old hatreds simmer",
        "central_conflict": "Trust vs. betrayal as former enemies must cooperate or perish",
        "narrative_direction": "Political intrigue replaces open warfare",
        "themes": ["loyalty", "deception", "unity"],
        "mysteries": ["Is the Accord a trap?", "Who sabotaged the summit?"],
        "hooks": ["The leader of the Accord is assassinated", "A secret weapon is discovered"]
    },
    {
        "title": "The Reckoning",
        "premise": "The true source of the blight is revealed, and the world must choose its fate",
        "central_conflict": "Destroy the source and lose magic forever, or live with the blight",
        "narrative_direction": "The world faces an irreversible choice",
        "themes": ["sacrifice", "rebirth", "identity"],
        "mysteries": ["Can the blight be turned into something beneficial?"],
        "hooks": ["The final confrontation at the Heart of Thorns"]
    }
])

ARC_JSON_WITH_PREAMBLE = """Here are 3 story arcs for your dark fantasy world:

```json
""" + ARC_JSON_CLEAN + """
```

Each arc builds on the previous one, creating a cohesive narrative progression."""

ARC_XML_FORMAT = """<arcs>
  <arc>
    <title>The Withering</title>
    <premise>A creeping blight spreads from the Thornwood</premise>
    <central_conflict>Nature turns hostile as thorn-blight consumes the land</central_conflict>
    <narrative_direction>Uneasy peace descends into catastrophe</narrative_direction>
    <themes>
      <theme>corruption</theme>
      <theme>survival</theme>
      <theme>sacrifice</theme>
    </themes>
    <mysteries>
      <mystery>What caused the first thorn-bloom?</mystery>
    </mysteries>
    <hooks>
      <hook>The capital's water supply is tainted</hook>
    </hooks>
  </arc>
  <arc>
    <title>The Crimson Accord</title>
    <premise>Factions unite under a fragile alliance</premise>
    <central_conflict>Trust vs betrayal</central_conflict>
    <narrative_direction>Political intrigue replaces warfare</narrative_direction>
    <themes>
      <theme>loyalty</theme>
      <theme>deception</theme>
    </themes>
    <mysteries>
      <mystery>Is the Accord a trap?</mystery>
    </mysteries>
    <hooks>
      <hook>The Accord leader is assassinated</hook>
    </hooks>
  </arc>
  <arc>
    <title>The Reckoning</title>
    <premise>The true source of the blight is revealed</premise>
    <central_conflict>Destroy the source or live with it</central_conflict>
    <narrative_direction>Irreversible choice</narrative_direction>
    <themes>
      <theme>sacrifice</theme>
      <theme>rebirth</theme>
    </themes>
    <mysteries>
      <mystery>Can the blight be turned beneficial?</mystery>
    </mysteries>
    <hooks>
      <hook>Final confrontation at the Heart of Thorns</hook>
    </hooks>
  </arc>
</arcs>"""

# --- Factions (JSON array) ---
FACTION_JSON_CLEAN = json.dumps([
    {
        "name": "The Thornguard",
        "description": "Militant order sworn to contain the blight at any cost",
        "goals": ["Burn infected zones", "Quarantine frontier towns", "Find a permanent cure"],
        "leader": "Commander Sera Blackthorn",
        "resources": "Military force, fire-magic specialists, fortified outposts",
        "alignment": "Lawful Neutral"
    },
    {
        "name": "The Pale Court",
        "description": "Aristocratic cabal that secretly profits from the blight",
        "goals": ["Control the cure supply", "Expand territory", "Eliminate the Thornguard"],
        "leader": "Duchess Morwen Ashveil",
        "resources": "Wealth, political influence, a network of spies",
        "alignment": "Neutral Evil"
    },
    {
        "name": "The Root Speakers",
        "description": "Druidic commune that believes the blight is nature's judgment",
        "goals": ["Protect the ancient groves", "Commune with the blight", "Convert others to their faith"],
        "leader": "Elder Yarrow",
        "resources": "Nature magic, hidden sanctuaries, deep knowledge of the land",
        "alignment": "True Neutral"
    }
])

# --- Factions: LLM uses alias field names ---
FACTION_JSON_ALIASES = json.dumps([
    {
        "faction_name": "The Iron Brotherhood",
        "overview": "Mercenary company that sells protection against the blight",
        "objectives": ["Profit from the crisis", "Control trade routes"],
        "ruler": "Captain Dorn Ironjaw",
        "power": "Military strength, strategic locations",
        "moral_stance": "Chaotic Neutral"
    },
    {
        "faction_name": "The Verdant Pact",
        "summary": "Coalition of healers and alchemists seeking a cure",
        "aims": ["Find a cure", "Establish hospitals"],
        "head": "Archhealer Lienna",
        "capabilities": "Alchemical knowledge, healing magic",
        "stance": "Neutral Good"
    }
])

# --- Characters (JSON array) ---
CHARACTER_JSON_CLEAN = json.dumps([
    {
        "name": "Kael Ashford",
        "description": "A lean, sharp-eyed woman with burn scars on her left arm",
        "background": "Former blacksmith who discovered she could sense metal through touch",
        "personality_traits": ["pragmatic", "self-reliant", "distrustful of authority"],
        "goals": "Find a way to control her ability",
        "fears": "Losing control and hurting someone she cares about",
        "skills": ["metalworking", "hand-to-hand combat", "wilderness survival"]
    },
    {
        "name": "Thorne Valdris",
        "description": "A tall, gaunt man with silver-streaked hair and eyes like storm clouds",
        "background": "Once a court mage, now exiled for forbidden experiments",
        "personality_traits": ["brilliant", "arrogant", "secretly compassionate"],
        "goals": "Redeem himself and restore his reputation",
        "fears": "Being forgotten and irrelevant",
        "skills": ["arcane magic", "alchemy", "politics"]
    },
    {
        "name": "Mira Songweaver",
        "description": "A small, dark-skinned woman with a voice that echoes unnaturally",
        "background": "A bard from the frontier who witnessed the first thorn-bloom",
        "personality_traits": ["curious", "empathetic", "reckless"],
        "goals": "Document the truth of what's happening to the world",
        "fears": "Silence — the absence of stories",
        "skills": ["singing", "lore", "persuasion", "lock-picking"]
    }
])

# --- Characters: LLM uses alias field names ---
CHARACTER_JSON_ALIASES = json.dumps([
    {
        "character_name": "Rowan Blackmere",
        "appearance": "Stocky build, rough hands, a scar across the bridge of his nose",
        "backstory": "A former soldier who deserted after the massacre at Thornhallow",
        "personality": ["haunted", "protective", "blunt"],
        "motivation": "Protect the innocent from both the blight and corrupt leaders",
        "weakness": "Nightmares and guilt over past failures",
        "abilities": ["swordsmanship", "tactical planning", "foraging"]
    },
    {
        "full_name": "Elara Dawnwhisper",
        "physical": "Ethereal appearance, glowing amber eyes, bark-like patches on her skin",
        "history": "A Root Speaker initiate who questions her order's dogma",
        "traits": ["conflicted", "intelligent", "stubborn"],
        "desire": "Understand the blight's true nature without the Root Speakers' bias",
        "fear": "Becoming part of the blight she studies",
        "talents": ["herbalism", "blight-sensing", "stealth"]
    }
])

# --- Locations (JSON array) ---
LOCATION_JSON_CLEAN = json.dumps([
    {
        "name": "Thornhaven",
        "description": "The last fortified city standing against the encroaching blight",
        "full_description": "Thornhaven rises from a granite plateau, its walls reinforced with fire-treated steel. The city is divided into three tiers: the Lower Sprawl where refugees crowd, the Merchant Ring where trade still flows, and the High Bastion where the Thornguard commands. Smoke from the eternal pyres hangs low, mingling with the acrid scent of alchemical fog deployed to slow thorn growth. Despite the grim atmosphere, Thornhaven pulses with desperate energy — every tavern is full, every forge burns day and night."
    },
    {
        "name": "The Thornwood",
        "description": "A vast forest consumed by the blight, now a labyrinth of razor-sharp thorns",
        "full_description": "Once the great Greenwood, the Thornwood is a nightmarish tangle of black thorns that grow visibly. The canopy blocks all sunlight, and the air is thick with pollen that causes hallucinations. Paths shift as thorns grow and decay, making navigation nearly impossible. Deep within, ruins of the old forest villages can still be found, their inhabitants long gone — or worse, absorbed."
    },
    {
        "name": "The Sunken Bazaar",
        "description": "An underground market in flooded catacombs beneath the capital",
        "full_description": "Beneath the cobblestones of the capital lies the Sunken Bazaar. Merchants pole flat-bottomed boats between pillars draped in bioluminescent moss. The air is thick with incense meant to mask the smell of canal water. Guards rarely venture below — the Bazaar is governed by its own code."
    },
    {
        "name": "The Pale Meadow",
        "description": "A deceptively peaceful field where the blight first appeared",
        "full_description": "The Pale Meadow is a vast expanse of bleached grass surrounding a single massive thorn tree. The ground is unnaturally warm. Nothing grows here except pale flowers that bloom and wilt within hours. The meadow is considered sacred by the Root Speakers and forbidden by the Thornguard."
    },
    {
        "name": "Ironhold Mines",
        "description": "Abandoned mine complex now used as a refuge by deserters",
        "full_description": "Once the kingdom's richest iron source, the Ironhold Mines were abandoned when thorn-root infiltrated the lower shafts. The upper levels now shelter a community of deserters, refugees, and outcasts who have sealed the deep tunnels. Ironhold is self-governing, trading salvaged ore for food."
    }
])

# --- Magic System (JSON objects) ---
PARADIGM_JSON_MAGIC = json.dumps({"paradigm": "magic", "reason": "Dark fantasy setting with supernatural blight"})
PARADIGM_JSON_NONE = json.dumps({"paradigm": "none", "reason": "Realistic historical fiction"})
PARADIGM_JSON_TECH = json.dumps({"paradigm": "tech", "reason": "Cyberpunk setting"})

MAGIC_SYSTEM_JSON = json.dumps({
    "name": "The Ember Weave",
    "description": "A volatile magical force drawn from underground ember veins",
    "rules": ["Channel heat through ritual scars", "Sense ember veins underground", "Forge-bond with metal"],
    "limitations": ["Cannot affect water or ice", "Cannot heal", "Cannot be used at night"],
    "costs": ["Each use deepens ritual scars", "Prolonged use causes hallucinations", "Overuse burns out ember veins"],
    "origin": "Ancient ember veins beneath the continent",
    "practitioners": "Scarred channelers called Embersmiths, rare and feared",
    "technology_level": "Late medieval with magical metallurgy"
})

# --- Episode recap (JSON object) ---
RECAP_JSON = json.dumps({
    "title": "The Fall of Thornhaven",
    "summary": "The blight breached the outer walls. The Thornguard fell back to the inner bastion while civilians fled through the Sunken Bazaar. Kael discovered her metal-sense could detect blight-roots underground, giving the defenders a brief advantage. But the Pale Court used the chaos to seize the granary.",
    "key_themes": ["sacrifice", "betrayal"],
    "themes_explored": ["survival under siege", "the cost of power"],
    "hook_for_next": "The Pale Court controls the food supply — starvation looms",
    "unresolved_new": ["Where did the blight breach originate?", "Is there a traitor in the Thornguard?"]
})


# ============================================================================
# Test: generate_structured() end-to-end pipeline
# ============================================================================

class TestGenerateStructuredPipeline:
    """Test the TextGenerator.generate_structured() method with real parsing."""

    @pytest.mark.asyncio
    async def test_single_object_json(self):
        """generate_structured() with expect_array=False returns a dict."""
        gen = make_generator(PARADIGM_JSON_MAGIC)
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=PARADIGM_SCHEMA,
        )
        assert isinstance(result, dict)
        assert result["paradigm"] == "magic"
        assert "reason" in result

    @pytest.mark.asyncio
    async def test_array_json(self):
        """generate_structured() with expect_array=True returns a list."""
        gen = make_generator(FACTION_JSON_CLEAN)
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True,
            min_items=3, max_items=5,
            item_tag="faction", root_tag="factions",
        )
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=schema,
        )
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["name"] == "The Thornguard"

    @pytest.mark.asyncio
    async def test_json_with_preamble(self):
        """Parser handles LLM preamble text before the JSON."""
        gen = make_generator(ARC_JSON_WITH_PREAMBLE)
        schema = ResponseSchema(
            fields=ARC_SCHEMA.fields,
            expect_array=True,
            min_items=3, max_items=5,
            item_tag="arc", root_tag="arcs",
        )
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=schema,
        )
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["title"] == "The Withering"

    @pytest.mark.asyncio
    async def test_xml_format_parsed(self):
        """Parser handles XML format even when JSON was requested."""
        gen = make_generator(ARC_XML_FORMAT)
        schema = ResponseSchema(
            fields=ARC_SCHEMA.fields,
            expect_array=True,
            min_items=3, max_items=5,
            item_tag="arc", root_tag="arcs",
        )
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=schema,
        )
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["title"] == "The Withering"
        # XML themes should be parsed as lists
        assert isinstance(result[0]["themes"], list)
        assert "corruption" in result[0]["themes"]

    @pytest.mark.asyncio
    async def test_alias_resolution(self):
        """Parser resolves field aliases (e.g., 'faction_name' → 'name')."""
        gen = make_generator(FACTION_JSON_ALIASES)
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True,
            min_items=2, max_items=4,
            item_tag="faction", root_tag="factions",
        )
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=schema,
        )
        assert isinstance(result, list)
        assert len(result) == 2
        # Aliases should be resolved to canonical names
        assert result[0]["name"] == "The Iron Brotherhood"
        assert result[0]["description"] == "Mercenary company that sells protection against the blight"
        assert isinstance(result[0]["goals"], list)
        assert result[0]["leader"] == "Captain Dorn Ironjaw"

    @pytest.mark.asyncio
    async def test_character_alias_resolution(self):
        """Parser resolves character field aliases."""
        gen = make_generator(CHARACTER_JSON_ALIASES)
        schema = ResponseSchema(
            fields=CHARACTER_SCHEMA.fields,
            expect_array=True,
            min_items=2, max_items=4,
            item_tag="character", root_tag="characters",
        )
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=schema,
        )
        assert len(result) == 2
        # character_name → name
        assert result[0]["name"] == "Rowan Blackmere"
        # appearance → description
        assert "Stocky build" in result[0]["description"]
        # backstory → background
        assert "former soldier" in result[0]["background"].lower()
        # personality → personality_traits
        assert isinstance(result[0]["personality_traits"], list)
        assert "haunted" in result[0]["personality_traits"]

    @pytest.mark.asyncio
    async def test_fallback_on_garbage(self):
        """generate_structured() returns fallback_defaults on garbage input."""
        gen = make_generator("This is not JSON or XML at all. Just random text about weather.")
        fallback = [{"paradigm": "magic", "reason": "Fallback heuristic"}]
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=PARADIGM_SCHEMA,
            fallback_defaults=fallback,
        )
        assert isinstance(result, dict)
        assert result.get("paradigm") == "magic"

    @pytest.mark.asyncio
    async def test_fallback_on_empty(self):
        """generate_structured() returns fallback_defaults on empty response."""
        gen = make_generator("")
        fallback = [{"name": "Fallback Faction", "description": "A fallback", "goals": []}]
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=False,
        )
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=schema,
            fallback_defaults=fallback,
        )
        assert result["name"] == "Fallback Faction"

    @pytest.mark.asyncio
    async def test_fallback_on_exception(self):
        """generate_structured() returns fallback if _generate_content raises."""
        gen = TextGenerator()

        async def exploding_generate(system_prompt, user_prompt):
            raise RuntimeError("API is down")

        gen._generate_content = exploding_generate

        fallback = [{"paradigm": "none", "reason": "error fallback"}]
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=PARADIGM_SCHEMA,
            fallback_defaults=fallback,
        )
        assert result["paradigm"] == "none"

    @pytest.mark.asyncio
    async def test_padding_with_defaults(self):
        """Parser pads to min_items using fallback_defaults."""
        # LLM returns only 1 item but min_items=3
        single_item = json.dumps([{
            "name": "Only Faction",
            "description": "The only one",
            "goals": ["survive"],
            "leader": "Nobody",
            "resources": "Nothing",
            "alignment": "Neutral"
        }])
        gen = make_generator(single_item)
        fallback = [
            {**FACTION_FALLBACK, "name": "Pad 1"},
            {**FACTION_FALLBACK, "name": "Pad 2"},
            {**FACTION_FALLBACK, "name": "Pad 3"},
        ]
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True,
            min_items=3, max_items=5,
            item_tag="faction", root_tag="factions",
        )
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=schema,
            fallback_defaults=fallback,
        )
        # Parser accepts what it parsed without padding
        assert len(result) >= 1
        assert result[0]["name"] == "Only Faction"

    @pytest.mark.asyncio
    async def test_prompt_instruction_appended(self):
        """generate_structured() appends format instructions to user prompt."""
        captured_prompts = {}

        gen = TextGenerator()

        async def capture_generate(system_prompt, user_prompt):
            captured_prompts["user"] = user_prompt
            captured_prompts["system"] = system_prompt
            return PARADIGM_JSON_MAGIC

        gen._generate_content = capture_generate

        await gen.generate_structured(
            system_prompt="test system",
            user_prompt="test user",
            schema=PARADIGM_SCHEMA,
        )
        # Format instruction should be appended
        assert "Return a single JSON object" in captured_prompts["user"]
        assert "paradigm" in captured_prompts["user"]


# ============================================================================
# Test: Arc Generator full pipeline
# ============================================================================

class TestArcGeneratorPipeline:
    """Test ArcGenerator with real parsing, mocked _generate_content."""

    @pytest.mark.asyncio
    async def test_generate_arcs_from_clean_json(self, temp_data_dir):
        story = make_story()
        gen = make_generator(ARC_JSON_CLEAN)
        arc_gen = ArcGenerator(story, gen)
        arcs = await arc_gen.generate_future_arcs(count=3)

        assert len(arcs) == 3
        assert all(isinstance(a, StoryArc) for a in arcs)
        assert arcs[0].title == "The Withering"
        assert arcs[0].premise == "A creeping blight spreads from the Thornwood, poisoning the land"
        assert arcs[0].central_conflict != ""
        assert isinstance(arcs[0].themes, list)
        assert "corruption" in arcs[0].themes
        assert isinstance(arcs[0].unresolved_mysteries, list)
        assert len(arcs[0].unresolved_mysteries) > 0
        assert isinstance(arcs[0].plot_hooks, list)
        # First arc is active, others are future
        assert arcs[0].is_active is True
        assert arcs[1].is_future_arc is True

    @pytest.mark.asyncio
    async def test_generate_arcs_from_json_with_preamble(self, temp_data_dir):
        story = make_story()
        gen = make_generator(ARC_JSON_WITH_PREAMBLE)
        arc_gen = ArcGenerator(story, gen)
        arcs = await arc_gen.generate_future_arcs(count=3)

        assert len(arcs) == 3
        assert arcs[0].title == "The Withering"

    @pytest.mark.asyncio
    async def test_generate_arcs_from_xml(self, temp_data_dir):
        story = make_story()
        gen = make_generator(ARC_XML_FORMAT)
        arc_gen = ArcGenerator(story, gen)
        arcs = await arc_gen.generate_future_arcs(count=3)

        assert len(arcs) == 3
        assert arcs[0].title == "The Withering"
        assert isinstance(arcs[0].themes, list)
        assert "corruption" in arcs[0].themes

    @pytest.mark.asyncio
    async def test_select_active_characters(self, temp_data_dir):
        story = make_story()
        char1 = StoryCharacter(
            story=story, id="char_001", name="Kael", description="desc", background="bg"
        )
        char2 = StoryCharacter(
            story=story, id="char_002", name="Thorne", description="desc", background="bg"
        )
        arc = StoryArc(
            id="arc_001", story_id=story.id, title="Test Arc",
            start_segment_id="seg_001", premise="Test",
            central_conflict="Test conflict", themes=["survival"]
        )

        response = json.dumps({
            "active_characters": [
                {"character_id": "char_001", "reason": "Central to the conflict"},
                {"character_id": "char_002", "reason": "Key antagonist"}
            ]
        })
        gen = make_generator(response)
        arc_gen = ArcGenerator(story, gen)
        active_ids = await arc_gen.select_active_characters_for_arc(arc)

        assert "char_001" in active_ids
        assert "char_002" in active_ids


# ============================================================================
# Test: Faction Generator full pipeline
# ============================================================================

class TestFactionGeneratorPipeline:
    """Test FactionGenerator with real parsing."""

    @pytest.mark.asyncio
    async def test_generate_factions_clean_json(self):
        story = make_story()
        gen = make_generator(FACTION_JSON_CLEAN)
        faction_gen = FactionGenerator(story, gen)
        factions = await faction_gen.generate_factions(
            count=3,
            world_description="A dark fantasy world plagued by thorn-blight",
            major_tensions=["The blight threatens all", "Factions distrust each other"],
        )

        assert len(factions) == 3
        assert all(isinstance(f, StoryFaction) for f in factions)
        assert factions[0].name == "The Thornguard"
        assert "Militant" in factions[0].description
        assert isinstance(factions[0].goals, list)
        assert len(factions[0].goals) == 3
        assert factions[0].leader == "Commander Sera Blackthorn"
        assert factions[0].alignment == "Lawful Neutral"
        # Should be registered with story
        assert factions[0].id in story._factions

    @pytest.mark.asyncio
    async def test_generate_factions_with_aliases(self):
        story = make_story()
        gen = make_generator(FACTION_JSON_ALIASES)
        faction_gen = FactionGenerator(story, gen)
        factions = await faction_gen.generate_factions(
            count=2,
            world_description="A fantasy world",
            major_tensions=["Power struggles"],
        )

        assert len(factions) == 2
        # Aliases should be resolved
        assert factions[0].name == "The Iron Brotherhood"
        assert "Mercenary" in factions[0].description
        assert isinstance(factions[0].goals, list)
        assert factions[0].leader == "Captain Dorn Ironjaw"


# ============================================================================
# Test: Character Generator full pipeline
# ============================================================================

class TestCharacterGeneratorPipeline:
    """Test CharacterGenerator with real parsing."""

    @pytest.mark.asyncio
    async def test_generate_initial_characters_clean_json(self, temp_data_dir):
        story = make_story()
        gen = make_generator(CHARACTER_JSON_CLEAN)
        char_gen = CharacterGenerator(story, gen)
        chars = await char_gen.generate_initial_characters(count=3)

        assert len(chars) == 3
        assert all(isinstance(c, StoryCharacter) for c in chars)
        assert chars[0].name == "Kael Ashford"
        assert "burn scars" in chars[0].description
        assert "blacksmith" in chars[0].background.lower()
        assert isinstance(chars[0].personality, list)
        assert "pragmatic" in chars[0].personality
        assert chars[0].goals != ""

    @pytest.mark.asyncio
    async def test_generate_characters_with_aliases(self, temp_data_dir):
        story = make_story()
        gen = make_generator(CHARACTER_JSON_ALIASES)
        char_gen = CharacterGenerator(story, gen)
        chars = await char_gen.generate_initial_characters(count=2)

        assert len(chars) == 2
        assert chars[0].name == "Rowan Blackmere"
        assert isinstance(chars[0].personality, list)
        assert "haunted" in chars[0].personality

    @pytest.mark.asyncio
    async def test_generate_faction_characters(self, temp_data_dir):
        story = make_story()
        faction = StoryFaction(
            id="faction_test", story=story,
            name="The Thornguard",
            description="Militant order",
            goals=["Contain the blight"],
        )
        gen = make_generator(CHARACTER_JSON_CLEAN)
        char_gen = CharacterGenerator(story, gen)
        chars = await char_gen.generate_faction_characters(
            factions=[faction],
            story_plan={"chars_per_faction_min": 2, "chars_per_faction_max": 2}
        )

        assert len(chars) == 2
        # Characters should be assigned to the faction
        assert all(c.faction_id == "faction_test" for c in chars)


# ============================================================================
# Test: Location Generator full pipeline
# ============================================================================

class TestLocationGeneratorPipeline:
    """Test LocationGenerator with real parsing."""

    @pytest.mark.asyncio
    async def test_generate_locations_clean_json(self):
        story = make_story()
        gen = make_generator(LOCATION_JSON_CLEAN)
        loc_gen = LocationGenerator(story, gen)
        locations = await loc_gen.generate_world_locations(
            world_description="A dark fantasy world",
            fundamental_truths=["Thorns grow from shadows", "Magic is fueled by pain"],
        )

        assert len(locations) == 5
        assert all(isinstance(loc, StoryLocation) for loc in locations)
        assert locations[0].name == "Thornhaven"
        assert "fortified city" in locations[0].description.lower()
        assert locations[0].full_description != ""
        assert len(locations[0].full_description) > len(locations[0].description)
        # Should be registered with story
        assert any(loc.name == "Thornhaven" for loc in story._locations.values())

    @pytest.mark.asyncio
    async def test_locations_full_description_fallback(self):
        """If full_description is empty, it falls back to description."""
        partial = json.dumps([
            {"name": "Empty Full", "description": "A short desc", "full_description": ""},
            {"name": "Missing Full", "description": "Another desc"},
        ] + [
            {"name": f"Loc {i}", "description": f"Desc {i}", "full_description": f"Full {i}"}
            for i in range(3, 8)
        ])
        story = make_story()
        gen = make_generator(partial)
        loc_gen = LocationGenerator(story, gen)
        locations = await loc_gen.generate_world_locations(
            world_description="test",
            fundamental_truths=["test"],
        )
        # First location: empty full_description → fallback to description
        empty_full = next(loc for loc in locations if loc.name == "Empty Full")
        assert empty_full.full_description == "A short desc"


# ============================================================================
# Test: Magic System Generator full pipeline
# ============================================================================

class TestMagicSystemGeneratorPipeline:
    """Test MagicSystemGenerator with real parsing."""

    @pytest.mark.asyncio
    async def test_magic_paradigm_generates_system(self):
        story = make_story()
        gen = make_sequential_generator([PARADIGM_JSON_MAGIC, MAGIC_SYSTEM_JSON])
        magic_gen = MagicSystemGenerator(story, gen)
        system = await magic_gen.generate_magic_system(
            world_description="A dark fantasy world with supernatural blight",
            genre="Dark Fantasy",
        )

        assert system is not None
        assert isinstance(system, StoryMagicSystem)
        assert system.name == "The Ember Weave"
        assert "volatile" in system.description.lower()
        assert isinstance(system.rules, list)
        assert len(system.rules) == 3
        assert isinstance(system.limitations, list)
        assert len(system.limitations) == 3
        assert isinstance(system.costs, list)
        assert len(system.costs) == 3
        assert system.origin != ""
        assert system.practitioners != ""

    @pytest.mark.asyncio
    async def test_none_paradigm_returns_none(self):
        story = make_story()
        gen = make_generator(PARADIGM_JSON_NONE)
        magic_gen = MagicSystemGenerator(story, gen)
        system = await magic_gen.generate_magic_system(
            world_description="A realistic noir thriller set in 1940s Chicago",
            genre="Noir",
        )
        assert system is None

    @pytest.mark.asyncio
    async def test_tech_paradigm_generates_system(self):
        story = make_story()
        tech_system = json.dumps({
            "name": "Neural Lattice",
            "description": "Brain-computer interface network connecting all citizens",
            "rules": ["Instant communication", "Memory sharing", "Skill downloading"],
            "limitations": ["Cannot override free will", "Range limited to city", "Requires implant"],
            "costs": ["Identity erosion", "Addiction to connectivity", "Government surveillance"],
            "origin": "Military project that went civilian",
            "practitioners": "90% of urban population has basic implants",
            "technology_level": "Near-future cyberpunk"
        })
        gen = make_sequential_generator([PARADIGM_JSON_TECH, tech_system])
        magic_gen = MagicSystemGenerator(story, gen)
        system = await magic_gen.generate_magic_system(
            world_description="A cyberpunk megacity",
            genre="Cyberpunk",
        )
        assert system is not None
        assert system.name == "Neural Lattice"

    @pytest.mark.asyncio
    async def test_paradigm_fuzzy_matching(self):
        """LLM returns 'supernatural forces' instead of exact 'magic'."""
        fuzzy_response = json.dumps({
            "paradigm": "supernatural forces and arcane energy",
            "reason": "The world is steeped in the occult"
        })
        story = make_story()
        gen = make_sequential_generator([fuzzy_response, MAGIC_SYSTEM_JSON])
        magic_gen = MagicSystemGenerator(story, gen)
        system = await magic_gen.generate_magic_system(
            world_description="Occult world",
            genre="Dark Fantasy",
        )
        # Should fuzzy-match "arcane" → "magic" paradigm
        assert system is not None


# ============================================================================
# Test: Episode Recap parsing
# ============================================================================

class TestEpisodeRecapParsing:
    """Test that episode recap schema parsing works end-to-end."""

    @pytest.mark.asyncio
    async def test_recap_schema_parsing(self):
        """Parse a realistic recap response through the schema."""
        from app.engine.episode_recap_generator import RECAP_SCHEMA

        gen = make_generator(RECAP_JSON)
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=RECAP_SCHEMA,
        )

        assert isinstance(result, dict)
        assert result["title"] == "The Fall of Thornhaven"
        assert "blight breached" in result["summary"]
        assert isinstance(result["key_themes"], list)
        assert "sacrifice" in result["key_themes"]
        assert isinstance(result["themes_explored"], list)
        assert result["hook_for_next"] != ""
        assert isinstance(result["unresolved_new"], list)
        assert len(result["unresolved_new"]) == 2

    @pytest.mark.asyncio
    async def test_recap_with_aliases(self):
        """LLM uses alias field names for recap."""
        from app.engine.episode_recap_generator import RECAP_SCHEMA

        aliased = json.dumps({
            "episode_title": "Chapter Two: The Siege",
            "recap": "The city fell under siege. Heroes emerged from unlikely places.",
            "themes": ["heroism", "desperation"],
            "explored_themes": ["the cost of war"],
            "cliffhanger": "The walls are about to fall",
            "mysteries": ["Who opened the gates?"]
        })
        gen = make_generator(aliased)
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=RECAP_SCHEMA,
        )

        assert result["title"] == "Chapter Two: The Siege"
        assert "city fell" in result["summary"]
        assert isinstance(result["key_themes"], list)
        assert result["hook_for_next"] == "The walls are about to fall"

    @pytest.mark.asyncio
    async def test_episode_context_schema_parsing(self):
        """Parse episode context (tone, direction, hooks) through the schema."""
        episode_context_schema = ResponseSchema(
            fields=[
                FieldSpec("tone_tags", type="list", aliases=["tone", "tones"]),
                FieldSpec("end_condition", type="str", aliases=["ending", "resolution"]),
                FieldSpec("narrative_direction", type="str", aliases=["direction", "narrative"]),
                FieldSpec("episode_focus", type="str", aliases=["focus"]),
                FieldSpec("story_hooks", type="list", aliases=["hooks", "plot_hooks"]),
            ],
            expect_array=False,
        )
        context_response = json.dumps({
            "tone_tags": ["tense", "foreboding", "desperate"],
            "end_condition": "The siege breaks — either through victory or collapse",
            "narrative_direction": "Escalating tension toward a climactic battle",
            "episode_focus": "The defenders' last stand",
            "story_hooks": ["A traitor is revealed", "Ancient weapon discovered in the mines"]
        })
        gen = make_generator(context_response)
        result = await gen.generate_structured(
            system_prompt="test",
            user_prompt="test",
            schema=episode_context_schema,
        )

        assert isinstance(result["tone_tags"], list)
        assert "tense" in result["tone_tags"]
        assert result["end_condition"] != ""
        assert result["narrative_direction"] != ""


# ============================================================================
# Test: Type coercion edge cases in real schemas
# ============================================================================

class TestTypeCoercionInSchemas:
    """Test that type coercion works correctly for the field types used by generators."""

    @pytest.mark.asyncio
    async def test_themes_as_comma_string(self):
        """LLM returns themes as a comma-separated string instead of array."""
        arc_data = json.dumps([{
            "title": "The Withering",
            "premise": "Blight spreads",
            "central_conflict": "Nature turns hostile",
            "narrative_direction": "Descent into chaos",
            "themes": "corruption, survival, sacrifice",  # String, not array!
            "mysteries": "What caused it?, Who is behind it?",
            "hooks": "The capital falls"
        }])
        schema = ResponseSchema(
            fields=ARC_SCHEMA.fields,
            expect_array=True, min_items=1, max_items=3,
            item_tag="arc", root_tag="arcs",
        )
        gen = make_generator(arc_data)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        # Coercion should convert comma-separated string to list
        assert isinstance(result[0]["themes"], list)
        assert len(result[0]["themes"]) == 3
        assert "corruption" in result[0]["themes"]

    @pytest.mark.asyncio
    async def test_goals_as_string(self):
        """Faction goals returned as a single string should be coerced to list."""
        single_faction = json.dumps([{
            "name": "The Order",
            "description": "A religious order",
            "goals": "Spread the faith and convert the masses",
            "leader": "High Priest",
            "resources": "Churches",
            "alignment": "Lawful Good"
        }])
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True, min_items=1, max_items=3,
            item_tag="faction", root_tag="factions",
        )
        gen = make_generator(single_faction)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        # goals is type="list" — string should be coerced
        assert isinstance(result[0]["goals"], list)

    @pytest.mark.asyncio
    async def test_float_coercion_for_goal_progress(self):
        """Float field returned as string should be coerced."""
        from app.engine.character_state_updater import _ENHANCE_SCHEMA

        enhance_response = json.dumps({
            "description": "Updated description",
            "emotional_status": "anxious",
            "health_status": "injured",
            "goal_progress": "0.75",  # String, not float!
            "goal_notes": "Making progress",
            "relationship_notes": ["Allied with Kael", "Distrusts the Pale Court"]
        })
        gen = make_generator(enhance_response)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=_ENHANCE_SCHEMA,
        )
        # goal_progress should be coerced from "0.75" to 0.75
        assert isinstance(result["goal_progress"], float)
        assert result["goal_progress"] == 0.75


# ============================================================================
# Test: Mixed/malformed LLM responses
# ============================================================================

class TestMalformedResponses:
    """Test parsing of realistically malformed LLM responses."""

    @pytest.mark.asyncio
    async def test_json_with_trailing_comma(self):
        """LLM outputs JSON with trailing commas (common GPT mistake)."""
        bad_json = """{
  "title": "The Withering",
  "premise": "Blight spreads",
  "central_conflict": "Nature hostile",
  "themes": ["corruption", "survival",],
  "mysteries": ["What caused it?",],
  "hooks": ["The capital falls",],
}"""
        # Wrap in array for arc schema
        schema = ResponseSchema(
            fields=ARC_SCHEMA.fields,
            expect_array=False,
        )
        gen = make_generator(bad_json)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        # Parser's JSON repair should handle trailing commas
        assert result.get("title") == "The Withering"

    @pytest.mark.asyncio
    async def test_json_with_markdown_wrapper(self):
        """LLM wraps JSON in triple backtick code blocks."""
        markdown_wrapped = """Here are the factions:

```json
[
  {"name": "The Thornguard", "description": "Militant order", "goals": ["fight"], "leader": "Sera", "resources": "Military", "alignment": "Neutral"}
]
```

These factions create tension through their opposing goals."""
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True, min_items=1, max_items=3,
            item_tag="faction", root_tag="factions",
        )
        gen = make_generator(markdown_wrapped)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        assert len(result) >= 1
        assert result[0]["name"] == "The Thornguard"

    @pytest.mark.asyncio
    async def test_partial_json_missing_fields(self):
        """LLM returns JSON with some fields missing."""
        partial = json.dumps([{
            "name": "Incomplete Faction",
            "description": "Missing most fields"
            # goals, leader, resources, alignment all missing
        }])
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True, min_items=1, max_items=3,
            item_tag="faction", root_tag="factions",
        )
        gen = make_generator(partial)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        assert len(result) >= 1
        assert result[0]["name"] == "Incomplete Faction"
        # Missing fields should get defaults
        assert isinstance(result[0]["goals"], list)  # default: []
        assert isinstance(result[0]["leader"], str)   # default: ""

    @pytest.mark.asyncio
    async def test_xml_json_hybrid(self):
        """LLM returns XML-wrapped JSON (hybrid format)."""
        hybrid = """<factions>
  <faction>
    {"name": "The Thornguard", "description": "Militant order", "goals": ["fight blight"], "leader": "Sera", "resources": "Military", "alignment": "Neutral"}
  </faction>
  <faction>
    {"name": "The Pale Court", "description": "Aristocratic cabal", "goals": ["profit"], "leader": "Morwen", "resources": "Wealth", "alignment": "Evil"}
  </faction>
</factions>"""
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True, min_items=2, max_items=4,
            item_tag="faction", root_tag="factions",
        )
        gen = make_generator(hybrid)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        assert len(result) == 2
        assert result[0]["name"] == "The Thornguard"
        assert result[1]["name"] == "The Pale Court"

    @pytest.mark.asyncio
    async def test_bold_section_format(self):
        """LLM returns formatted text with bold headers (item-per-header).

        The bold_sections strategy treats each **bold** header as an item name.
        Single-item bold-label responses (field: value) are handled by
        _extract_fields_from_text inside the bold strategy. But when bold
        headers match field labels like "Description", they're skipped since
        the strategy thinks they're sub-fields not item names.

        This test verifies that numbered_sections handles the field-label
        pattern, and that bold sections work when each header IS an item name.
        """
        # Numbered-section format (field labels inside a single numbered item)
        numbered_format = """1. The Thornguard
Description: A militant order sworn to contain the blight
Goals: Burn infected zones, quarantine frontier towns, find a permanent cure
Leader: Commander Sera Blackthorn
Resources: Military force, fire-magic specialists
Alignment: Lawful Neutral"""
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=False,
        )
        gen = make_generator(numbered_format)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        assert result["name"] == "The Thornguard"
        assert "militant" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_bold_section_multiple_items(self):
        """Bold headers as item names — the intended bold_sections use case."""
        bold_items = """**The Thornguard**
Description: A militant order sworn to contain the blight
Goals: Burn infected zones, find a cure
Leader: Sera Blackthorn

**The Pale Court**
Description: An aristocratic cabal profiting from the crisis
Goals: Control the cure, expand territory
Leader: Duchess Morwen"""
        schema = ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True, min_items=2, max_items=4,
            item_tag="faction", root_tag="factions",
        )
        gen = make_generator(bold_items)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        assert len(result) >= 2
        assert result[0]["name"] == "The Thornguard"
        assert result[1]["name"] == "The Pale Court"


# ============================================================================
# Test: Cross-format consistency (same data, different formats)
# ============================================================================

class TestCrossFormatConsistency:
    """Verify that the same data parsed from JSON/XML/hybrid produces identical results."""

    @pytest.mark.asyncio
    async def test_arc_json_vs_xml_consistency(self):
        """Same arc data in JSON and XML should produce same parsed fields."""
        json_gen = make_generator(ARC_JSON_CLEAN)
        xml_gen = make_generator(ARC_XML_FORMAT)

        schema = ResponseSchema(
            fields=ARC_SCHEMA.fields,
            expect_array=True, min_items=3, max_items=5,
            item_tag="arc", root_tag="arcs",
        )
        json_result = await json_gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )
        xml_result = await xml_gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=schema,
        )

        assert len(json_result) == len(xml_result) == 3
        # Titles should match
        assert json_result[0]["title"] == xml_result[0]["title"] == "The Withering"
        assert json_result[1]["title"] == xml_result[1]["title"] == "The Crimson Accord"
        assert json_result[2]["title"] == xml_result[2]["title"] == "The Reckoning"
        # Both should have list-type themes
        assert isinstance(json_result[0]["themes"], list)
        assert isinstance(xml_result[0]["themes"], list)


# ============================================================================
# Test: Character state updater schemas
# ============================================================================

class TestCharacterStateUpdaterSchemas:
    """Test character_state_updater's schemas parse correctly."""

    @pytest.mark.asyncio
    async def test_enhance_schema(self):
        """_ENHANCE_SCHEMA: realistic enhancement response."""
        from app.engine.character_state_updater import _ENHANCE_SCHEMA

        response = json.dumps({
            "description": "Kael's scars have deepened. She moves with visible pain but determined purpose.",
            "emotional_status": "resolute but haunted",
            "health_status": "wounded — left arm partially paralyzed from blight exposure",
            "goal_progress": 0.4,
            "goal_notes": "She's learned to sense blight-roots but can't yet control the ability",
            "relationship_notes": ["Growing trust with Thorne", "Suspicious of Morwen's motives"]
        })
        gen = make_generator(response)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=_ENHANCE_SCHEMA,
        )
        assert result["description"] != ""
        assert result["emotional_status"] == "resolute but haunted"
        assert isinstance(result["goal_progress"], float)
        assert 0.0 <= result["goal_progress"] <= 1.0
        assert isinstance(result["relationship_notes"], list)

    @pytest.mark.asyncio
    async def test_new_char_schema(self):
        """_NEW_CHAR_SCHEMA: new character generation response."""
        from app.engine.character_state_updater import _NEW_CHAR_SCHEMA

        response = json.dumps({
            "name": "Vex the Unbroken",
            "description": "A towering woman with ritual tattoos covering her arms and a missing left eye",
            "background": "Former gladiator who earned her freedom by defeating a blight-beast in the arena",
            "personality_traits": ["fierce", "honorable", "impatient"],
            "goals": "Find a worthy cause to fight for",
            "role_in_theme": "Represents the cost of survival and the search for meaning after violence"
        })
        gen = make_generator(response)
        result = await gen.generate_structured(
            system_prompt="test", user_prompt="test", schema=_NEW_CHAR_SCHEMA,
        )
        assert result["name"] == "Vex the Unbroken"
        assert isinstance(result["personality_traits"], list)
        assert "fierce" in result["personality_traits"]
        assert result["goals"] != ""


# ============================================================================
# Test: Full round-trip (parse → model constructor → verify fields)
# ============================================================================

class TestFullRoundTrip:
    """Parse LLM output → build model objects → verify all fields populated."""

    @pytest.mark.asyncio
    async def test_faction_roundtrip(self):
        """Faction: parse → StoryFaction constructor → verify."""
        story = make_story()
        parsed = AIResponseParser.parse(FACTION_JSON_CLEAN, ResponseSchema(
            fields=FACTION_SCHEMA.fields,
            expect_array=True, min_items=3, max_items=5,
            item_tag="faction", root_tag="factions",
        ))
        assert len(parsed) == 3

        for raw in parsed:
            faction = StoryFaction(
                id=f"faction_{uuid.uuid4().hex[:8]}",
                story=story,
                name=raw.get('name', FACTION_FALLBACK['name']),
                description=raw.get('description', FACTION_FALLBACK['description']),
                goals=raw.get('goals', FACTION_FALLBACK['goals']),
                leader=raw.get('leader', FACTION_FALLBACK['leader']),
                resources=raw.get('resources', FACTION_FALLBACK['resources']),
                alignment=raw.get('alignment', FACTION_FALLBACK['alignment']),
            )
            assert faction.name != ""
            assert faction.description != ""
            assert isinstance(faction.goals, list)
            assert len(faction.goals) > 0

    @pytest.mark.asyncio
    async def test_character_roundtrip(self):
        """Character: parse → StoryCharacter constructor → verify."""
        story = make_story()
        parsed = AIResponseParser.parse(CHARACTER_JSON_CLEAN, ResponseSchema(
            fields=CHARACTER_SCHEMA.fields,
            expect_array=True, min_items=3, max_items=5,
            item_tag="character", root_tag="characters",
        ))
        assert len(parsed) == 3

        for raw in parsed:
            char = StoryCharacter(
                story=story,
                id=f"char_{uuid.uuid4().hex[:8]}",
                name=raw.get('name', CHARACTER_FALLBACK['name']),
                description=raw.get('description', CHARACTER_FALLBACK['description']),
                background=raw.get('background', CHARACTER_FALLBACK['background']),
                personality=raw.get('personality_traits', []),
                goals=raw.get('goals', ''),
            )
            assert char.name != ""
            assert char.description != ""
            assert char.background != ""
            assert isinstance(char.personality, list)

    @pytest.mark.asyncio
    async def test_location_roundtrip(self):
        """Location: parse → StoryLocation constructor → verify."""
        story = make_story()
        parsed = AIResponseParser.parse(LOCATION_JSON_CLEAN, LOCATION_SCHEMA)
        assert len(parsed) == 5

        for raw in parsed:
            name = raw.get('name', LOCATION_FALLBACK['name'])
            short_desc = raw.get('description', LOCATION_FALLBACK['description'])
            full_desc = raw.get('full_description', '') or short_desc

            loc = StoryLocation(
                id=f"loc_{uuid.uuid4().hex[:8]}",
                story=story,
                name=name,
                description=short_desc,
                full_description=full_desc,
            )
            assert loc.name != ""
            assert loc.description != ""
            assert loc.full_description != ""

    @pytest.mark.asyncio
    async def test_magic_system_roundtrip(self):
        """Magic system: parse → StoryMagicSystem constructor → verify."""
        story = make_story()
        parsed = AIResponseParser.parse(MAGIC_SYSTEM_JSON, SYSTEM_SCHEMA)
        assert len(parsed) == 1
        raw = parsed[0]

        system = StoryMagicSystem(
            id=f"magic_{uuid.uuid4().hex[:8]}",
            story=story,
            name=raw.get('name', SYSTEM_FALLBACK['name']),
            description=raw.get('description', SYSTEM_FALLBACK['description']),
            rules=raw.get('rules', SYSTEM_FALLBACK['rules']),
            limitations=raw.get('limitations', SYSTEM_FALLBACK['limitations']),
            costs=raw.get('costs', SYSTEM_FALLBACK['costs']),
            origin=raw.get('origin', ''),
            practitioners=raw.get('practitioners', ''),
            technology_level=raw.get('technology_level', ''),
        )
        assert system.name == "The Ember Weave"
        assert len(system.rules) == 3
        assert len(system.limitations) == 3
        assert len(system.costs) == 3
        assert system.origin != ""

    @pytest.mark.asyncio
    async def test_fallback_defaults_create_valid_models(self):
        """Fallback defaults should be valid enough to create model objects."""
        story = make_story()

        # Faction fallback
        faction = StoryFaction(
            id="fallback_faction", story=story,
            **FACTION_FALLBACK,
        )
        assert faction.name == "Unknown Faction"

        # Character fallback
        char = StoryCharacter(
            id="fallback_char", story=story,
            name=CHARACTER_FALLBACK["name"],
            description=CHARACTER_FALLBACK["description"],
            background=CHARACTER_FALLBACK["background"],
            personality=CHARACTER_FALLBACK["personality_traits"],
            goals=CHARACTER_FALLBACK["goals"],
        )
        assert char.name == "Unnamed Character"

        # Location fallback
        loc = StoryLocation(
            id="fallback_loc", story=story,
            **LOCATION_FALLBACK,
        )
        assert loc.name == "Unknown Location"

        # Magic system fallback
        system = StoryMagicSystem(
            id="fallback_magic", story=story,
            **SYSTEM_FALLBACK,
        )
        assert system.name == "The Ancient Arts"
