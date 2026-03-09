"""Tests for AIResponseParser — all formats (JSON, XML, hybrid) and prompt generators."""

import json
import pytest
from app.utils.ai_response_parser import (
    AIResponseParser,
    FieldSpec,
    OutputFormat,
    ResponseSchema,
)


# ---------------------------------------------------------------------------
# Shared test schemas
# ---------------------------------------------------------------------------

FACTION_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", required=True),
        FieldSpec("description"),
        FieldSpec("goals", type="list"),
        FieldSpec("leader"),
    ],
    expect_array=True,
    min_items=3,
    item_tag="faction",
    root_tag="factions",
)

MAGIC_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", required=True),
        FieldSpec("description"),
        FieldSpec("what_it_can_do", type="list", aliases=["capabilities"]),
        FieldSpec("limitations", type="list"),
        FieldSpec("costs_and_consequences", type="list", aliases=["costs"]),
    ],
    expect_array=False,
    item_tag="magic_system",
    root_tag="magic_systems",
)

CHARACTER_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", required=True),
        FieldSpec("age", type="str"),
        FieldSpec("role"),
        FieldSpec("backstory"),
        FieldSpec("traits", type="list"),
    ],
    expect_array=False,
    item_tag="character",
    root_tag="characters",
)


# ===================================================================
# A) XML Strategy Tests
# ===================================================================

class TestStrategyXML:
    """Test _strategy_xml parsing."""

    def test_basic_xml_factions(self):
        """Parse 3 factions from clean XML."""
        text = """
<factions>
  <faction>
    <name>The Iron Conclave</name>
    <description>A militaristic guild of blacksmiths and warriors</description>
    <goals>
      <goal>Control the northern mines</goal>
      <goal>Forge the legendary blade</goal>
    </goals>
    <leader>Commander Voss</leader>
  </faction>
  <faction>
    <name>The Silk Court</name>
    <description>An aristocratic trade consortium</description>
    <goals>
      <goal>Monopolize silk trade</goal>
      <goal>Infiltrate the royal council</goal>
    </goals>
    <leader>Duchess Meren</leader>
  </faction>
  <faction>
    <name>The Ashen Circle</name>
    <description>A secret society of pyromancers</description>
    <goals>
      <goal>Uncover ancient fire rituals</goal>
      <goal>Destroy the water temple</goal>
    </goals>
    <leader>The Ember Prophet</leader>
  </faction>
</factions>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"
        assert results[1]["name"] == "The Silk Court"
        assert results[2]["name"] == "The Ashen Circle"
        assert "Control the northern mines" in results[0]["goals"]
        assert results[0]["leader"] == "Commander Voss"

    def test_xml_without_root_wrapper(self):
        """Parse factions from XML with no root wrapper — just repeated tags."""
        text = """
<faction>
  <name>The Iron Conclave</name>
  <description>A militaristic guild</description>
  <leader>Commander Voss</leader>
</faction>
<faction>
  <name>The Silk Court</name>
  <description>An aristocratic trade consortium</description>
  <leader>Duchess Meren</leader>
</faction>
<faction>
  <name>The Ashen Circle</name>
  <description>A secret society</description>
  <leader>The Ember Prophet</leader>
</faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"
        assert results[2]["name"] == "The Ashen Circle"

    def test_xml_single_item(self):
        """Parse a single magic system from XML."""
        text = """
<magic_system>
  <name>Aether Weaving</name>
  <description>The art of manipulating ambient magical energy</description>
  <what_it_can_do>
    <capability>Telekinesis</capability>
    <capability>Elemental shaping</capability>
    <capability>Mind linking</capability>
  </what_it_can_do>
  <limitations>
    <limitation>Cannot create matter from nothing</limitation>
    <limitation>Requires concentration</limitation>
  </limitations>
  <costs_and_consequences>
    <cost>Physical exhaustion</cost>
    <cost>Memory loss with overuse</cost>
  </costs_and_consequences>
</magic_system>
"""
        results = AIResponseParser.parse(text, MAGIC_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 1
        assert results[0]["name"] == "Aether Weaving"
        assert len(results[0]["what_it_can_do"]) >= 2
        assert len(results[0]["limitations"]) >= 1
        assert len(results[0]["costs_and_consequences"]) >= 1

    def test_xml_with_preamble_text(self):
        """Parser should handle AI preamble before XML."""
        text = """Here are the three factions I've created for your world:

<faction>
  <name>The Iron Conclave</name>
  <description>Warriors</description>
</faction>
<faction>
  <name>The Silk Court</name>
  <description>Traders</description>
</faction>
<faction>
  <name>The Ashen Circle</name>
  <description>Mages</description>
</faction>

I hope these factions work well for your story!"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"

    def test_xml_with_attributes(self):
        """Tags with attributes like <faction id="1"> should still parse."""
        text = """
<faction id="1" type="military">
  <name>The Iron Conclave</name>
  <description>Warriors</description>
</faction>
<faction id="2" type="trade">
  <name>The Silk Court</name>
  <description>Traders</description>
</faction>
<faction id="3">
  <name>The Ashen Circle</name>
  <description>Mages</description>
</faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"

    def test_xml_comma_separated_list(self):
        """List field in XML with comma-separated text instead of child tags."""
        text = """
<magic_system>
  <name>Runecraft</name>
  <description>Ancient rune-based magic</description>
  <what_it_can_do>Enchanting weapons, Creating barriers, Divination</what_it_can_do>
  <limitations>Requires physical runes, Slow to cast</limitations>
  <costs_and_consequences>Rune degradation, Physical scarring</costs_and_consequences>
</magic_system>
"""
        results = AIResponseParser.parse(text, MAGIC_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 1
        assert len(results[0]["what_it_can_do"]) >= 2
        assert "Enchanting weapons" in results[0]["what_it_can_do"]


# ===================================================================
# B) XML+JSON Hybrid Strategy Tests
# ===================================================================

class TestStrategyXMLJsonHybrid:
    """Test _strategy_xml_json_hybrid parsing."""

    def test_basic_hybrid_factions(self):
        """Parse factions from XML-wrapped JSON."""
        text = """
<factions>
<faction>
{"name": "The Iron Conclave", "description": "A militaristic guild", "goals": ["Control mines", "Forge the blade"], "leader": "Commander Voss"}
</faction>
<faction>
{"name": "The Silk Court", "description": "An aristocratic consortium", "goals": ["Monopolize trade"], "leader": "Duchess Meren"}
</faction>
<faction>
{"name": "The Ashen Circle", "description": "Secret pyromancers", "goals": ["Fire rituals"], "leader": "The Ember Prophet"}
</faction>
</factions>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML_JSON)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"
        assert results[1]["name"] == "The Silk Court"
        assert results[0]["goals"] == ["Control mines", "Forge the blade"]
        assert results[0]["leader"] == "Commander Voss"

    def test_hybrid_without_root_wrapper(self):
        """Hybrid tags without outer root wrapper."""
        text = """
<faction>
{"name": "The Iron Conclave", "description": "Warriors"}
</faction>
<faction>
{"name": "The Silk Court", "description": "Traders"}
</faction>
<faction>
{"name": "The Ashen Circle", "description": "Mages"}
</faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML_JSON)
        assert len(results) == 3

    def test_hybrid_single_item(self):
        """Single item in hybrid format."""
        text = """
<magic_system>
{
  "name": "Aether Weaving",
  "description": "The art of manipulating ambient magical energy",
  "what_it_can_do": ["Telekinesis", "Elemental shaping", "Mind linking"],
  "limitations": ["Cannot create matter", "Requires concentration"],
  "costs_and_consequences": ["Physical exhaustion", "Memory loss"]
}
</magic_system>
"""
        results = AIResponseParser.parse(text, MAGIC_SCHEMA, preferred_format=OutputFormat.XML_JSON)
        assert len(results) == 1
        assert results[0]["name"] == "Aether Weaving"
        assert len(results[0]["what_it_can_do"]) == 3
        assert len(results[0]["limitations"]) == 2

    def test_hybrid_with_preamble(self):
        """AI preamble before hybrid tags."""
        text = """Sure! Here are the factions:

<faction>
{"name": "Alpha", "description": "First faction", "goals": ["Win"], "leader": "Boss A"}
</faction>

<faction>
{"name": "Beta", "description": "Second faction", "goals": ["Survive"], "leader": "Boss B"}
</faction>

<faction>
{"name": "Gamma", "description": "Third faction", "goals": ["Grow"], "leader": "Boss C"}
</faction>

Let me know if you'd like to modify any!"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML_JSON)
        assert len(results) == 3
        assert results[0]["name"] == "Alpha"
        assert results[2]["name"] == "Gamma"

    def test_hybrid_json_in_code_block_inside_xml(self):
        """JSON wrapped in markdown code block inside XML tags."""
        text = """
<faction>
```json
{"name": "The Iron Conclave", "description": "Warriors", "goals": ["Fight"], "leader": "Voss"}
```
</faction>
<faction>
```json
{"name": "The Silk Court", "description": "Traders", "goals": ["Trade"], "leader": "Meren"}
```
</faction>
<faction>
```json
{"name": "The Ashen Circle", "description": "Mages", "goals": ["Magic"], "leader": "Prophet"}
```
</faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML_JSON)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"

    def test_hybrid_with_trailing_commas_in_json(self):
        """Hybrid with slightly broken JSON (trailing commas) inside XML."""
        text = """
<faction>
{"name": "The Iron Conclave", "description": "Warriors", "goals": ["Fight",], "leader": "Voss",}
</faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML_JSON)
        assert len(results) >= 1
        assert results[0]["name"] == "The Iron Conclave"


# ===================================================================
# C) Format-Agnostic Parsing (any format should work without hint)
# ===================================================================

class TestFormatAgnosticParsing:
    """Verify that parse() works regardless of preferred_format hint."""

    def test_json_parsed_without_hint(self):
        """JSON response parsed correctly with no preferred_format."""
        text = json.dumps([
            {"name": "A", "description": "First", "goals": ["Win"], "leader": "L1"},
            {"name": "B", "description": "Second", "goals": ["Lose"], "leader": "L2"},
            {"name": "C", "description": "Third", "goals": ["Draw"], "leader": "L3"},
        ])
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        assert len(results) == 3
        assert results[0]["name"] == "A"

    def test_xml_parsed_without_hint(self):
        """XML response parsed correctly even when preferred_format is not set."""
        text = """
<faction><name>Alpha</name><description>First</description></faction>
<faction><name>Beta</name><description>Second</description></faction>
<faction><name>Gamma</name><description>Third</description></faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        assert len(results) == 3
        assert results[0]["name"] == "Alpha"

    def test_hybrid_parsed_without_hint(self):
        """Hybrid response parsed correctly even without hint."""
        text = """
<faction>
{"name": "Alpha", "description": "First", "goals": [], "leader": "L1"}
</faction>
<faction>
{"name": "Beta", "description": "Second", "goals": [], "leader": "L2"}
</faction>
<faction>
{"name": "Gamma", "description": "Third", "goals": [], "leader": "L3"}
</faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        assert len(results) == 3

    def test_xml_response_with_json_hint_still_parses(self):
        """Even if we asked for JSON, XML response should still parse."""
        text = """
<faction><name>Alpha</name><description>First</description></faction>
<faction><name>Beta</name><description>Second</description></faction>
<faction><name>Gamma</name><description>Third</description></faction>
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.JSON)
        assert len(results) == 3
        assert results[0]["name"] == "Alpha"

    def test_json_response_with_xml_hint_still_parses(self):
        """Even if we asked for XML, JSON response should still parse."""
        text = json.dumps([
            {"name": "A", "description": "First", "goals": [], "leader": "L1"},
            {"name": "B", "description": "Second", "goals": [], "leader": "L2"},
            {"name": "C", "description": "Third", "goals": [], "leader": "L3"},
        ])
        results = AIResponseParser.parse(text, FACTION_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 3


# ===================================================================
# D) Prompt Instruction Generator Tests
# ===================================================================

class TestPromptInstructions:
    """Test all three prompt instruction generators."""

    def test_json_prompt_basic(self):
        """JSON prompt instruction has correct structure."""
        prompt = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA, fmt=OutputFormat.JSON)
        assert "JSON array" in prompt
        assert '"name"' in prompt
        assert '"description"' in prompt
        assert '"goals"' in prompt
        assert "(REQUIRED)" in prompt
        assert "Return ONLY valid JSON" in prompt

    def test_json_prompt_with_example(self):
        """JSON prompt instruction includes example."""
        example = {"name": "Example Faction", "description": "A test", "goals": ["Win"], "leader": "Boss"}
        prompt = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA, fmt=OutputFormat.JSON, example=example)
        assert "Example Faction" in prompt
        assert "```json" in prompt

    def test_xml_prompt_basic(self):
        """XML prompt instruction has correct structure."""
        prompt = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA, fmt=OutputFormat.XML)
        assert "<faction>" in prompt
        assert "<factions>" in prompt
        assert "<name>" in prompt
        assert "(REQUIRED)" in prompt
        assert "valid XML" in prompt

    def test_xml_prompt_with_example(self):
        """XML prompt includes an XML example."""
        example = {"name": "The Iron Conclave", "description": "Warriors", "goals": ["Fight", "Win"], "leader": "Voss"}
        prompt = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA, fmt=OutputFormat.XML, example=example)
        assert "```xml" in prompt
        assert "<name>The Iron Conclave</name>" in prompt
        assert "<goal>" in prompt  # list items should use singular child tags

    def test_xml_json_prompt_basic(self):
        """Hybrid prompt instruction has correct structure."""
        prompt = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA, fmt=OutputFormat.XML_JSON)
        assert "<faction>" in prompt
        assert "JSON object" in prompt
        assert '"name"' in prompt
        assert "(REQUIRED)" in prompt

    def test_xml_json_prompt_with_example(self):
        """Hybrid prompt includes example with XML wrapping JSON."""
        example = {"name": "Test", "description": "Desc", "goals": ["A"], "leader": "L"}
        prompt = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA, fmt=OutputFormat.XML_JSON, example=example)
        assert "```xml" in prompt
        assert "<faction>" in prompt
        assert '"name"' in prompt

    def test_single_item_json_prompt(self):
        """Single-item schema generates 'single object' prompt."""
        prompt = AIResponseParser.get_prompt_instruction(MAGIC_SCHEMA, fmt=OutputFormat.JSON)
        assert "single JSON object" in prompt
        assert "array" not in prompt.split("object")[0]  # "array" should not appear before "object"

    def test_single_item_xml_prompt(self):
        """Single-item schema generates single element XML prompt."""
        prompt = AIResponseParser.get_prompt_instruction(MAGIC_SCHEMA, fmt=OutputFormat.XML)
        assert "<magic_system>" in prompt
        assert "single" in prompt.lower()

    def test_dispatch_default_is_json(self):
        """Default format is JSON."""
        prompt_default = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA)
        prompt_json = AIResponseParser.get_prompt_instruction(FACTION_SCHEMA, fmt=OutputFormat.JSON)
        assert prompt_default == prompt_json

    def test_list_field_xml_shows_child_elements(self):
        """XML prompt for list fields mentions child elements."""
        prompt = AIResponseParser.get_prompt_instruction(MAGIC_SCHEMA, fmt=OutputFormat.XML)
        # Should mention that what_it_can_do contains child elements
        assert "what_it_can_do" in prompt
        assert "multiple" in prompt.lower() or "elements" in prompt.lower()


# ===================================================================
# E) Edge Cases
# ===================================================================

class TestEdgeCases:
    """Edge cases and error handling."""

    def test_empty_text(self):
        """Empty text returns fallback defaults."""
        defaults = [{"name": "Default 1"}, {"name": "Default 2"}, {"name": "Default 3"}]
        results = AIResponseParser.parse("", FACTION_SCHEMA, fallback_defaults=defaults)
        assert results == defaults

    def test_garbage_text(self):
        """Completely unparseable text returns fallback defaults."""
        defaults = [{"name": "Fallback"}]
        results = AIResponseParser.parse(
            "lorem ipsum dolor sit amet, this is total nonsense with no structure at all",
            MAGIC_SCHEMA,
            fallback_defaults=defaults,
        )
        assert len(results) >= 1

    def test_mixed_xml_and_json_in_same_response(self):
        """Response that has both XML and JSON — parser should extract from both."""
        text = """
Here are two factions in XML and one in JSON:

<faction>
  <name>XML Faction 1</name>
  <description>First from XML</description>
</faction>
<faction>
  <name>XML Faction 2</name>
  <description>Second from XML</description>
</faction>

And here's the third:
```json
{"name": "JSON Faction", "description": "From JSON", "goals": [], "leader": "Boss"}
```
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        # Should get at least 2 from one strategy
        assert len(results) >= 2
        names = [r["name"] for r in results]
        # At least the XML ones should be found
        assert "XML Faction 1" in names or "JSON Faction" in names

    def test_xml_with_html_entities(self):
        """XML content with HTML entities like &amp; should parse."""
        text = """
<faction>
  <name>Smith &amp; Sons</name>
  <description>A guild of blacksmiths &amp; merchants</description>
</faction>
"""
        schema = ResponseSchema(
            fields=[FieldSpec("name", required=True), FieldSpec("description")],
            expect_array=False,
            item_tag="faction",
        )
        results = AIResponseParser.parse(text, schema, preferred_format=OutputFormat.XML)
        assert len(results) >= 1
        # The raw &amp; will be in the text (we don't do HTML entity decoding)
        assert "Smith" in results[0]["name"]

    def test_xml_item_tag_fallback_to_item(self):
        """Schema with default item_tag='item' should parse <item> tags."""
        text = """
<item>
  <name>Thing One</name>
  <description>First thing</description>
</item>
<item>
  <name>Thing Two</name>
  <description>Second thing</description>
</item>
"""
        schema = ResponseSchema(
            fields=[FieldSpec("name", required=True), FieldSpec("description")],
            expect_array=True,
            min_items=2,
        )
        results = AIResponseParser.parse(text, schema, preferred_format=OutputFormat.XML)
        assert len(results) == 2
        assert results[0]["name"] == "Thing One"

    def test_padding_with_defaults_xml(self):
        """If XML only produces 1 faction, parser accepts what it gets."""
        text = """
<faction>
  <name>The Only Faction</name>
  <description>Lonely</description>
</faction>
"""
        defaults = [
            {"name": "Default 1", "description": "d1", "goals": [], "leader": ""},
            {"name": "Default 2", "description": "d2", "goals": [], "leader": ""},
            {"name": "Default 3", "description": "d3", "goals": [], "leader": ""},
        ]
        results = AIResponseParser.parse(text, FACTION_SCHEMA, fallback_defaults=defaults, preferred_format=OutputFormat.XML)
        # Parser accepts what it parsed without padding
        assert len(results) >= 1
        assert results[0]["name"] == "The Only Faction"

    def test_xml_hyphenated_field_names(self):
        """Fields with underscores should match hyphenated XML tags too."""
        text = """
<magic_system>
  <name>Aether Weaving</name>
  <description>Magic stuff</description>
  <what-it-can-do>
    <capability>Telekinesis</capability>
    <capability>Elemental shaping</capability>
  </what-it-can-do>
  <limitations>
    <limitation>Cannot create matter</limitation>
  </limitations>
  <costs-and-consequences>
    <cost>Physical exhaustion</cost>
  </costs-and-consequences>
</magic_system>
"""
        results = AIResponseParser.parse(text, MAGIC_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 1
        assert results[0]["name"] == "Aether Weaving"
        assert len(results[0]["what_it_can_do"]) >= 1

    def test_character_schema_xml(self):
        """Character with age as string in XML."""
        text = """
<character>
  <name>Aldric Voss</name>
  <age>early 40s</age>
  <role>Blacksmith turned rebel leader</role>
  <backstory>Once a humble forge worker, Aldric rose to prominence after...</backstory>
  <traits>
    <trait>Determined</trait>
    <trait>Honorable</trait>
    <trait>Short-tempered</trait>
  </traits>
</character>
"""
        results = AIResponseParser.parse(text, CHARACTER_SCHEMA, preferred_format=OutputFormat.XML)
        assert len(results) == 1
        assert results[0]["name"] == "Aldric Voss"
        assert results[0]["age"] == "early 40s"
        assert len(results[0]["traits"]) == 3


# ===================================================================
# F) JSON Strategy Regression Tests (existing behavior preserved)
# ===================================================================

class TestJsonStrategyRegression:
    """Ensure existing JSON parsing still works after adding XML strategies."""

    def test_json_array_in_code_block(self):
        """JSON array in markdown code block."""
        text = """```json
[
  {"name": "F1", "description": "First", "goals": ["A"], "leader": "L1"},
  {"name": "F2", "description": "Second", "goals": ["B"], "leader": "L2"},
  {"name": "F3", "description": "Third", "goals": ["C"], "leader": "L3"}
]
```"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        assert len(results) == 3
        assert results[0]["name"] == "F1"

    def test_json_object_with_nested_array(self):
        """JSON object containing a 'factions' array."""
        data = {
            "world": "TestWorld",
            "factions": [
                {"name": "F1", "description": "First", "goals": [], "leader": "L1"},
                {"name": "F2", "description": "Second", "goals": [], "leader": "L2"},
                {"name": "F3", "description": "Third", "goals": [], "leader": "L3"},
            ]
        }
        text = json.dumps(data, indent=2)
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        assert len(results) == 3
        assert results[0]["name"] == "F1"

    def test_bold_sections_still_work(self):
        """Bold section strategy still works after XML additions."""
        text = """
**The Iron Conclave**
- Description: A militaristic guild
- Leader: Commander Voss
- Goals: Control mines, Forge weapons

**The Silk Court**
- Description: A trade consortium
- Leader: Duchess Meren
- Goals: Monopolize trade

**The Ashen Circle**
- Description: Secret pyromancers
- Leader: Ember Prophet
- Goals: Uncover rituals
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"

    def test_numbered_sections_still_work(self):
        """Numbered section strategy still works after XML additions."""
        text = """
1. The Iron Conclave
   Description: A militaristic guild
   Leader: Commander Voss

2. The Silk Court
   Description: A trade consortium
   Leader: Duchess Meren

3. The Ashen Circle
   Description: Secret pyromancers
   Leader: Ember Prophet
"""
        results = AIResponseParser.parse(text, FACTION_SCHEMA)
        assert len(results) == 3
        assert results[0]["name"] == "The Iron Conclave"


# ===================================================================
# G) _extract_xml_blocks unit tests
# ===================================================================

class TestExtractXmlBlocks:
    """Low-level tests for _extract_xml_blocks."""

    def test_simple_block(self):
        blocks = AIResponseParser._extract_xml_blocks("<item>hello</item>", "item")
        assert blocks == ["hello"]

    def test_multiple_blocks(self):
        text = "<item>one</item>\n<item>two</item>\n<item>three</item>"
        blocks = AIResponseParser._extract_xml_blocks(text, "item")
        assert len(blocks) == 3
        assert blocks[0] == "one"
        assert blocks[2] == "three"

    def test_blocks_with_attributes(self):
        text = '<item id="1">one</item><item id="2">two</item>'
        blocks = AIResponseParser._extract_xml_blocks(text, "item")
        assert len(blocks) == 2

    def test_no_blocks(self):
        blocks = AIResponseParser._extract_xml_blocks("no xml here", "item")
        assert blocks == []

    def test_case_insensitive(self):
        blocks = AIResponseParser._extract_xml_blocks("<Item>hello</Item>", "item")
        assert len(blocks) == 1
        assert blocks[0] == "hello"

    def test_multiline_content(self):
        text = """<item>
  line 1
  line 2
  line 3
</item>"""
        blocks = AIResponseParser._extract_xml_blocks(text, "item")
        assert len(blocks) == 1
        assert "line 1" in blocks[0]
        assert "line 3" in blocks[0]


# ===================================================================
# H) OutputFormat enum tests
# ===================================================================

class TestOutputFormat:
    """Basic enum tests."""

    def test_enum_values(self):
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.XML.value == "xml"
        assert OutputFormat.XML_JSON.value == "xml_json"

    def test_enum_from_string(self):
        assert OutputFormat("json") == OutputFormat.JSON
        assert OutputFormat("xml") == OutputFormat.XML
        assert OutputFormat("xml_json") == OutputFormat.XML_JSON
